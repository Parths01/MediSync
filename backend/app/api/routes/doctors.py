from io import BytesIO
import logging
from pathlib import Path
import re
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
from PIL import Image, UnidentifiedImageError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Doctor
from app.schemas import DoctorCreate, DoctorResponse, DoctorUpdate
from app.security import get_admin_user, require_csrf

router = APIRouter()
logger = logging.getLogger(__name__)
DOCTOR_PHOTO_DIR = Path(__file__).resolve().parents[4] / "uploads" / "doctors"
MAX_PHOTO_BYTES = 5 * 1024 * 1024
MAX_PHOTO_PIXELS = 40_000_000
PHOTO_FORMATS = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}
PHOTO_FILENAME_PATTERN = re.compile(r"doctor_[a-f0-9]{8,32}\.(?:jpg|png|webp)\Z")


@router.get("/photos/{filename}", response_class=FileResponse)
async def get_doctor_photo(filename: str) -> FileResponse:
    if not PHOTO_FILENAME_PATTERN.fullmatch(filename):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")

    photo_path = DOCTOR_PHOTO_DIR / filename
    if not photo_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")

    media_type = {
        "jpg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
    }[photo_path.suffix[1:]]
    return FileResponse(photo_path, media_type=media_type)


@router.get("", response_model=list[DoctorResponse])
async def list_doctors(db: AsyncSession = Depends(get_db)) -> list[Doctor]:
    result = await db.execute(select(Doctor).order_by(Doctor.name))
    return list(result.scalars().all())


@router.get("/{doctor_id}", response_model=DoctorResponse)
async def get_doctor(doctor_id: int, db: AsyncSession = Depends(get_db)) -> Doctor:
    doctor = await db.get(Doctor, doctor_id)
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    return doctor


@router.post(
    "",
    response_model=DoctorResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
async def create_doctor(
    payload: DoctorCreate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_admin_user),
) -> Doctor:
    doctor = Doctor(**payload.model_dump())
    db.add(doctor)
    await db.commit()
    await db.refresh(doctor)
    return doctor


@router.post(
    "/{doctor_id}/photo",
    response_model=DoctorResponse,
    dependencies=[Depends(require_csrf)],
)
async def upload_doctor_photo(
    doctor_id: int,
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_admin_user),
) -> Doctor:
    doctor = await db.get(Doctor, doctor_id)
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    content = await image.read(MAX_PHOTO_BYTES + 1)
    if len(content) > MAX_PHOTO_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Photo exceeds the 5 MB limit")

    try:
        with Image.open(BytesIO(content)) as decoded:
            image_format = decoded.format
            width, height = decoded.size
            if image_format not in PHOTO_FORMATS:
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail="Upload a JPEG, PNG, or WebP image",
                )
            if width < 1 or height < 1 or width * height > MAX_PHOTO_PIXELS:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Photo dimensions exceed the supported limit",
                )
            decoded.verify()
    except Image.DecompressionBombError as error:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Photo dimensions exceed the supported limit",
        ) from error
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="The uploaded file is not a valid supported image",
        ) from error

    filename = f"doctor_{uuid4().hex}.{PHOTO_FORMATS[image_format]}"
    photo_path = DOCTOR_PHOTO_DIR / filename
    DOCTOR_PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    photo_path.write_bytes(content)
    doctor.photo = f"/api/v1/doctors/photos/{filename}"

    try:
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()
        try:
            photo_path.unlink(missing_ok=True)
        except OSError:
            logger.exception("Unable to remove an uncommitted doctor photo: %s", photo_path.name)
        raise

    await db.refresh(doctor)
    return doctor


@router.put(
    "/{doctor_id}",
    response_model=DoctorResponse,
    dependencies=[Depends(require_csrf)],
)
async def update_doctor(
    doctor_id: int,
    payload: DoctorUpdate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_admin_user),
) -> Doctor:
    doctor = await db.get(Doctor, doctor_id)
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    for field, value in payload.model_dump().items():
        setattr(doctor, field, value)
    await db.commit()
    await db.refresh(doctor)
    return doctor


@router.delete(
    "/{doctor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_csrf)],
)
async def delete_doctor(
    doctor_id: int,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(get_admin_user),
) -> Response:
    doctor = await db.get(Doctor, doctor_id)
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    await db.delete(doctor)
    try:
        await db.commit()
    except IntegrityError as error:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Doctor has appointment records and cannot be deleted",
        ) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
