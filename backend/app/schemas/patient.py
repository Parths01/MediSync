from datetime import date, datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.doctor import DoctorResponse


AppointmentStatus = Literal["pending", "confirmed", "completed", "rejected", "cancelled"]
ContactStatus = Literal["open", "closed"]


class AppointmentCreate(BaseModel):
    doctor_id: int = Field(gt=0)
    appointment_date: datetime
    description: str = Field(min_length=1, max_length=10000)

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Please describe your symptoms")
        return normalized

    @model_validator(mode="after")
    def validate_appointment_date(self) -> "AppointmentCreate":
        if self.appointment_date.tzinfo is None or self.appointment_date.utcoffset() is None:
            raise ValueError("Appointment date must include a timezone")
        if self.appointment_date.astimezone(timezone.utc) <= datetime.now(timezone.utc):
            raise ValueError("Appointment date must be in the future")
        return self


class AppointmentView(BaseModel):
    appointment_id: int
    user_id: int
    doctor_id: int
    appointment_date: datetime
    description: str | None
    status: AppointmentStatus
    assigned_by: Literal["user", "admin"]
    created_at: datetime | None
    doctor_name: str
    specialization: str
    doctor_contact: str
    patient_name: str | None = None


class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus


class ProfileUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    dob: date
    gender: Literal["Male", "Female", "Other"]
    contact: str = Field(min_length=1, max_length=15)
    blood_group: Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"] | None
    current_password: str | None = Field(default=None, max_length=128)
    new_password: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("name", "contact")
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("This field cannot be blank")
        return normalized

    @field_validator("dob")
    @classmethod
    def validate_birth_date(cls, value: date) -> date:
        if value >= date.today():
            raise ValueError("Date of birth must be in the past")
        if date.today().year - value.year > 120:
            raise ValueError("Date of birth is outside the supported age range")
        return value

    @model_validator(mode="after")
    def validate_password_change(self) -> "ProfileUpdate":
        if (self.current_password is None) != (self.new_password is None):
            raise ValueError("Both current and new passwords are required to change a password")
        return self


class MedicalHistoryCreate(BaseModel):
    diagnosis: str = Field(min_length=1, max_length=255)
    treatment: str | None = Field(default=None, max_length=10000)
    notes: str | None = Field(default=None, max_length=10000)
    recorded_at: date

    @field_validator("diagnosis")
    @classmethod
    def normalize_diagnosis(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Diagnosis is required")
        return normalized

    @field_validator("recorded_at")
    @classmethod
    def validate_record_date(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Record date cannot be in the future")
        return value


class MedicalHistoryView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    history_id: int
    diagnosis: str
    treatment: str | None
    notes: str | None
    recorded_at: date
    created_at: datetime | None


class MessageCreate(BaseModel):
    message: str = Field(min_length=10, max_length=10000)

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 10:
            raise ValueError("Message must be at least 10 characters")
        return normalized


class FeedbackCreate(BaseModel):
    message: str = Field(min_length=1, max_length=10000)

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Feedback message is required")
        return normalized


class SymptomRecommendationRequest(BaseModel):
    symptoms: str = Field(min_length=1, max_length=2000)

    @field_validator("symptoms")
    @classmethod
    def normalize_symptoms(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Please describe your symptoms")
        return normalized


class SpecialtyRecommendation(BaseModel):
    specialty: str
    score: float


class SymptomRecommendationResponse(BaseModel):
    recommendations: list[SpecialtyRecommendation]
    doctors: list[DoctorResponse]
    disclaimer: str


class ContactMessageView(BaseModel):
    contact_id: int
    message: str
    status: ContactStatus
    created_at: datetime | None
    user_name: str


class FeedbackView(BaseModel):
    feedback_id: int
    message: str
    created_at: datetime | None
    user_name: str
