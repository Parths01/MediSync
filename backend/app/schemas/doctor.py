from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DoctorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    doctor_id: int
    name: str
    specialization: str
    experience: int
    contact_details: str
    photo: str | None = None
    created_at: datetime | None = None


class DoctorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    specialization: str = Field(min_length=1, max_length=255)
    experience: int = Field(ge=0, le=100)
    contact_details: str = Field(min_length=1, max_length=255)

    @field_validator("name", "specialization", "contact_details")
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("This field cannot be blank")
        return normalized


class DoctorUpdate(DoctorCreate):
    pass
