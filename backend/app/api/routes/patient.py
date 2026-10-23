from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    Appointment,
    ContactMessage,
    Doctor,
    Feedback,
    MedicalHistory,
    User,
    UserSession,
)
from app.schemas import UserResponse
from app.schemas.patient import (
    AppointmentCreate,
    AppointmentView,
    FeedbackCreate,
    MedicalHistoryCreate,
    MedicalHistoryView,
    MessageCreate,
    ProfileUpdate,
    SpecialtyRecommendation,
    SymptomRecommendationRequest,
    SymptomRecommendationResponse,
)
from app.security import (
    create_session,
    get_current_user,
    hash_password,
    require_csrf,
    verify_password_and_update,
)
from app.services.symptom_recommender import recommend_specialties

router = APIRouter(dependencies=[Depends(require_csrf)])


def _appointment_view(appointment: Appointment, doctor: Doctor) -> AppointmentView:
    return AppointmentView(
        appointment_id=appointment.appointment_id,
        user_id=appointment.user_id,
        doctor_id=appointment.doctor_id,
        appointment_date=appointment.appointment_date,
        description=appointment.description,
        status=appointment.status,
        assigned_by=appointment.assigned_by,
        created_at=appointment.created_at,
        doctor_name=doctor.name,
        specialization=doctor.specialization,
        doctor_contact=doctor.contact_details,
    )


@router.patch("/profile", response_model=UserResponse)
async def update_profile(
    payload: ProfileUpdate,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UserResponse:
    if payload.new_password is not None:
        is_valid, _replacement_hash = verify_password_and_update(
            payload.current_password or "",
            user.password_hash,
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )
        user.password_hash = hash_password(payload.new_password)
        await db.execute(delete(UserSession).where(UserSession.user_id == user.user_id))

    user.name = payload.name
    user.dob = payload.dob
    user.gender = payload.gender
    user.contact = payload.contact
    user.blood_group = payload.blood_group

    if payload.new_password is not None:
        await create_session(db, user, response)

    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.get("/appointments", response_model=list[AppointmentView])
async def list_appointments(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[AppointmentView]:
    result = await db.execute(
        select(Appointment, Doctor)
        .join(Doctor, Doctor.doctor_id == Appointment.doctor_id)
        .where(Appointment.user_id == user.user_id)
        .order_by(Appointment.appointment_date.desc())
        .limit(limit)
        .offset(offset)
    )
    return [_appointment_view(appointment, doctor) for appointment, doctor in result.all()]


@router.post(
    "/appointments",
    response_model=AppointmentView,
    status_code=status.HTTP_201_CREATED,
)
async def book_appointment(
    payload: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AppointmentView:
    doctor = await db.get(Doctor, payload.doctor_id)
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    appointment = Appointment(
        user_id=user.user_id,
        doctor_id=doctor.doctor_id,
        appointment_date=payload.appointment_date,
        description=payload.description,
        status="pending",
        assigned_by="user",
    )
    db.add(appointment)
    try:
        await db.commit()
    except IntegrityError as error:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That appointment time is unavailable. Choose another time.",
        ) from error

    await db.refresh(appointment)
    return _appointment_view(appointment, doctor)


@router.post("/appointments/{appointment_id}/cancel", response_model=AppointmentView)
async def cancel_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AppointmentView:
    result = await db.execute(
        select(Appointment, Doctor)
        .join(Doctor, Doctor.doctor_id == Appointment.doctor_id)
        .where(
            Appointment.appointment_id == appointment_id,
            Appointment.user_id == user.user_id,
        )
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    appointment, doctor = row
    if appointment.status not in {"pending", "confirmed"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This appointment can no longer be cancelled",
        )
    appointment.status = "cancelled"
    await db.commit()
    await db.refresh(appointment)
    return _appointment_view(appointment, doctor)


@router.get("/history", response_model=list[MedicalHistoryView])
async def list_medical_history(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[MedicalHistory]:
    result = await db.execute(
        select(MedicalHistory)
        .where(MedicalHistory.user_id == user.user_id)
        .order_by(MedicalHistory.recorded_at.desc(), MedicalHistory.history_id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


@router.post(
    "/history",
    response_model=MedicalHistoryView,
    status_code=status.HTTP_201_CREATED,
)
async def create_medical_history(
    payload: MedicalHistoryCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MedicalHistory:
    history = MedicalHistory(user_id=user.user_id, **payload.model_dump())
    db.add(history)
    await db.commit()
    await db.refresh(history)
    return history


@router.post("/contact", status_code=status.HTTP_201_CREATED)
async def send_contact_message(
    payload: MessageCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    message = ContactMessage(user_id=user.user_id, message=payload.message, status="open")
    db.add(message)
    await db.commit()
    return {"status": "sent"}


@router.post("/feedback", status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    payload: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    feedback = Feedback(user_id=user.user_id, message=payload.message)
    db.add(feedback)
    await db.commit()
    return {"status": "received"}


@router.post("/symptom-check", response_model=SymptomRecommendationResponse)
async def recommend_doctors(
    payload: SymptomRecommendationRequest,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> SymptomRecommendationResponse:
    recommendations = recommend_specialties(payload.symptoms)
    specialty_order = {
        str(item["specialty"]): position
        for position, item in enumerate(recommendations)
    }
    doctors: list[Doctor] = []
    if specialty_order:
        result = await db.execute(
            select(Doctor).where(Doctor.specialization.in_(specialty_order))
        )
        doctors = sorted(
            result.scalars().all(),
            key=lambda doctor: (
                specialty_order[doctor.specialization],
                doctor.name.casefold(),
            ),
        )

    return SymptomRecommendationResponse(
        recommendations=[
            SpecialtyRecommendation.model_validate(item) for item in recommendations
        ],
        doctors=doctors,
        disclaimer=(
            "This demo model was trained on synthetic examples and is not clinically "
            "validated. Its rankings are not medical advice or a diagnosis. Do not use "
            "them to make care decisions. If you may be experiencing an emergency, "
            "contact local emergency services."
        ),
    )
