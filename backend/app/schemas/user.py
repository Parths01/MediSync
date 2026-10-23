from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


Gender = Literal["Male", "Female", "Other"]
BloodGroup = Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
UserRole = Literal["patient", "admin"]


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    dob: date
    gender: Gender
    contact: str = Field(min_length=1, max_length=15)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    blood_group: BloodGroup | None = None

    @field_validator("name", "contact")
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("This field cannot be blank")
        return normalized

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("dob")
    @classmethod
    def validate_birth_date(cls, value: date) -> date:
        today = date.today()
        if value >= today:
            raise ValueError("Date of birth must be in the past")
        if today.year - value.year > 120:
            raise ValueError("Date of birth is outside the supported age range")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    name: str
    dob: date
    gender: Gender
    contact: str
    email: EmailStr
    blood_group: BloodGroup | None
    role: UserRole
    registration_date: datetime | None


class AuthResponse(BaseModel):
    user: UserResponse
    csrf_token: str
