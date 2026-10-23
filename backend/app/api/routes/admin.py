from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Appointment, ContactMessage, Doctor, Feedback, User
from app.schemas.admin import (
    AdminDashboardResponse,
    AdminInsightsResponse,
    AppointmentFollowUpView,
    ContactStatusUpdate,
    FeedbackInsightView,
    MonthlyCount,
)
from app.schemas.patient import (
    AppointmentStatusUpdate,
    AppointmentView,
    ContactMessageView,
    FeedbackView,
)
from app.security import get_admin_user, require_csrf
from app.services.heuristics import appointment_follow_up_indicator, classify_feedback

router = APIRouter(dependencies=[Depends(require_csrf)])

APPOINTMENT_STATUSES = ("pending", "confirmed", "completed", "rejected", "cancelled")
REPORTING_TIMEZONE = ZoneInfo("Asia/Kolkata")


def _month_start(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=REPORTING_TIMEZONE)
    else:
        value = value.astimezone(REPORTING_TIMEZONE)
    return value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _month_range_start(value: datetime) -> datetime:
    month_index = value.year * 12 + value.month - 1 - 5
    return value.replace(
        year=month_index // 12,
        month=month_index % 12 + 1,
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )


def _next_month_start(value: datetime) -> datetime:
    month_index = value.year * 12 + value.month
    return value.replace(
        year=month_index // 12,
        month=month_index % 12 + 1,
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )


async def _monthly_counts(
    db: AsyncSession,
    model: type[Appointment] | type[User],
    date_column: object,
    anchor: datetime | None,
) -> list[MonthlyCount]:
    month_anchor = _month_start(anchor or datetime.now(REPORTING_TIMEZONE))
    start = _month_range_start(month_anchor)
    month_column = func.to_char(
        func.date_trunc("month", date_column, "Asia/Kolkata"),
        "YYYY-MM",
    ).label("month")
    statement = (
        select(month_column, func.count())
        .select_from(model)
        .where(date_column >= start, date_column < _next_month_start(month_anchor))
        .group_by(text("1"))
        .order_by(text("1"))
    )
    if model is User:
        statement = statement.where(User.role == "patient")
    result = await db.execute(statement)
    counts = dict(result.all())
    months: list[MonthlyCount] = []
    for offset in range(6):
        month_index = start.year * 12 + start.month - 1 + offset
        month = start.replace(
            year=month_index // 12,
            month=month_index % 12 + 1,
        )
        month_label = month.strftime("%Y-%m")
        months.append(MonthlyCount(month=month_label, count=counts.get(month_label, 0)))
    return months


def _appointment_view(
    appointment: Appointment,
    doctor: Doctor,
    patient: User,
) -> AppointmentView:
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
        patient_name=patient.name,
    )


@router.get("/dashboard", response_model=AdminDashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
) -> AdminDashboardResponse:
    now = datetime.now(timezone.utc)
    total_users = await db.scalar(
        select(func.count()).select_from(User).where(User.role == "patient")
    ) or 0
    total_doctors = await db.scalar(select(func.count()).select_from(Doctor)) or 0
    total_appointments = await db.scalar(select(func.count()).select_from(Appointment)) or 0
    new_users = await db.scalar(
        select(func.count())
        .select_from(User)
        .where(User.role == "patient", User.registration_date >= now - timedelta(days=30))
    ) or 0
    pending_appointments = await db.scalar(
        select(func.count())
        .select_from(Appointment)
        .where(Appointment.status == "pending")
    ) or 0

    status_result = await db.execute(
        select(Appointment.status, func.count()).group_by(Appointment.status)
    )
    appointment_status_counts = {status: 0 for status in APPOINTMENT_STATUSES}
    appointment_status_counts.update(dict(status_result.all()))

    latest_appointment = await db.scalar(select(func.max(Appointment.appointment_date)))
    latest_registration = await db.scalar(
        select(func.max(User.registration_date)).where(User.role == "patient")
    )
    monthly_appointments = await _monthly_counts(
        db,
        Appointment,
        Appointment.appointment_date,
        latest_appointment,
    )
    monthly_registrations = await _monthly_counts(
        db,
        User,
        User.registration_date,
        latest_registration,
    )

    result = await db.execute(
        select(Appointment, Doctor, User)
        .join(Doctor, Doctor.doctor_id == Appointment.doctor_id)
        .join(User, User.user_id == Appointment.user_id)
        .order_by(Appointment.appointment_date.desc())
        .limit(10)
    )
    recent = [
        _appointment_view(appointment, doctor, patient)
        for appointment, doctor, patient in result.all()
    ]
    return AdminDashboardResponse(
        total_users=total_users,
        total_doctors=total_doctors,
        total_appointments=total_appointments,
        new_users_30d=new_users,
        pending_appointments=pending_appointments,
        appointment_status_counts=appointment_status_counts,
        monthly_appointments=monthly_appointments,
        monthly_registrations=monthly_registrations,
        recent_appointments=recent,
    )


@router.get("/appointments", response_model=list[AppointmentView])
async def list_appointments(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
) -> list[AppointmentView]:
    result = await db.execute(
        select(Appointment, Doctor, User)
        .join(Doctor, Doctor.doctor_id == Appointment.doctor_id)
        .join(User, User.user_id == Appointment.user_id)
        .order_by(Appointment.appointment_date.desc())
        .limit(limit)
        .offset(offset)
    )
    return [
        _appointment_view(appointment, doctor, patient)
        for appointment, doctor, patient in result.all()
    ]


@router.patch(
    "/appointments/{appointment_id}",
    response_model=AppointmentView,
)
async def update_appointment_status(
    appointment_id: int,
    payload: AppointmentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
) -> AppointmentView:
    result = await db.execute(
        select(Appointment, Doctor, User)
        .join(Doctor, Doctor.doctor_id == Appointment.doctor_id)
        .join(User, User.user_id == Appointment.user_id)
        .where(Appointment.appointment_id == appointment_id)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    appointment, doctor, patient = row
    appointment.status = payload.status
    try:
        await db.commit()
    except IntegrityError as error:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That appointment slot is already occupied",
        ) from error
    await db.refresh(appointment)
    return _appointment_view(appointment, doctor, patient)


@router.get("/reports", response_model=list[ContactMessageView])
async def list_reports(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
) -> list[ContactMessageView]:
    result = await db.execute(
        select(ContactMessage, User)
        .join(User, User.user_id == ContactMessage.user_id)
        .order_by(ContactMessage.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [
        ContactMessageView(
            contact_id=message.contact_id,
            message=message.message,
            status=message.status,
            created_at=message.created_at,
            user_name=user.name,
        )
        for message, user in result.all()
    ]


@router.patch("/reports/{contact_id}", response_model=ContactMessageView)
async def update_report_status(
    contact_id: int,
    payload: ContactStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
) -> ContactMessageView:
    result = await db.execute(
        select(ContactMessage, User)
        .join(User, User.user_id == ContactMessage.user_id)
        .where(ContactMessage.contact_id == contact_id)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    message, user = row
    message.status = payload.status
    await db.commit()
    await db.refresh(message)
    return ContactMessageView(
        contact_id=message.contact_id,
        message=message.message,
        status=message.status,
        created_at=message.created_at,
        user_name=user.name,
    )


@router.get("/feedback", response_model=list[FeedbackView])
async def list_feedback(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
) -> list[FeedbackView]:
    result = await db.execute(
        select(Feedback, User)
        .join(User, User.user_id == Feedback.user_id)
        .order_by(Feedback.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [
        FeedbackView(
            feedback_id=feedback.feedback_id,
            message=feedback.message,
            created_at=feedback.created_at,
            user_name=user.name,
        )
        for feedback, user in result.all()
    ]


@router.get("/insights", response_model=AdminInsightsResponse)
async def get_admin_insights(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_admin_user),
) -> AdminInsightsResponse:
    now = datetime.now(timezone.utc)
    past_appointments = (
        select(
            Appointment.user_id.label("user_id"),
            func.count(Appointment.appointment_id).label("past_total"),
            func.sum(
                case(
                    (Appointment.status.in_(("cancelled", "rejected")), 1),
                    else_=0,
                )
            ).label("past_cancelled_or_rejected"),
        )
        .where(Appointment.appointment_date < now)
        .group_by(Appointment.user_id)
        .subquery()
    )
    upcoming_result = await db.execute(
        select(
            Appointment,
            Doctor,
            User,
            past_appointments.c.past_total,
            past_appointments.c.past_cancelled_or_rejected,
        )
        .join(Doctor, Doctor.doctor_id == Appointment.doctor_id)
        .join(User, User.user_id == Appointment.user_id)
        .outerjoin(past_appointments, past_appointments.c.user_id == Appointment.user_id)
        .where(
            Appointment.appointment_date >= now,
            Appointment.status.in_(("pending", "confirmed")),
        )
        .order_by(Appointment.appointment_date.asc())
        .limit(50)
    )
    indicators: list[AppointmentFollowUpView] = []
    for appointment, doctor, patient, past_total, past_cancelled in upcoming_result.all():
        indicator = appointment_follow_up_indicator(
            appointment.appointment_date,
            appointment.created_at,
            past_total or 0,
            past_cancelled or 0,
        )
        indicators.append(
            AppointmentFollowUpView(
                appointment=_appointment_view(appointment, doctor, patient),
                indicator_score=float(indicator["score"]),
                indicator_label=str(indicator["label"]),
                factors=list(indicator["factors"]),
                suggestion=str(indicator["suggestion"]),
            )
        )
    label_order = {"High": 0, "Medium": 1, "Low": 2}
    indicators.sort(
        key=lambda indicator: (
            label_order[indicator.indicator_label],
            indicator.appointment.appointment_date,
        )
    )

    total_feedback = await db.scalar(select(func.count()).select_from(Feedback)) or 0
    feedback_result = await db.execute(
        select(Feedback, User)
        .join(User, User.user_id == Feedback.user_id)
        .order_by(Feedback.created_at.desc())
        .limit(200)
    )
    feedback = []
    counts = {"positive": 0, "neutral": 0, "negative": 0}
    for item, user in feedback_result.all():
        sentiment = str(classify_feedback(item.message)["sentiment"])
        counts[sentiment] += 1
        if sentiment == "negative":
            feedback.append(
                FeedbackInsightView(
                    feedback_id=item.feedback_id,
                    message=item.message,
                    created_at=item.created_at,
                    user_name=user.name,
                    sentiment=sentiment,
                )
            )

    analyzed_feedback = sum(counts.values())
    return AdminInsightsResponse(
        follow_up_indicators=indicators,
        feedback_total=total_feedback,
        feedback_analyzed=analyzed_feedback,
        sentiment_counts=counts,
        negative_feedback=feedback,
        disclaimer=(
            "These are unvalidated keyword and scheduling heuristics, not AI, medical advice, "
            "or reliable predictions. Do not use them to deny, delay, or prioritize patient care. "
            "Appointment indicators may be used only to consider routine staff-reviewed reminders."
        ),
    )
