from sqlalchemy import CheckConstraint

from app.database import Base
from app.models import (
    Appointment,
    ContactMessage,
    Doctor,
    Feedback,
    MedicalHistory,
    User,
    UserSession,
)


def test_all_legacy_workflow_entities_have_postgres_models() -> None:
    assert set(Base.metadata.tables) == {
        "appointments",
        "contact_messages",
        "doctors",
        "feedback",
        "medical_history",
        "users",
        "user_sessions",
    }


def test_patient_identity_and_auth_fields_are_in_postgres_model() -> None:
    user_columns = User.__table__.columns

    assert "dob" in user_columns
    assert "password_hash" in user_columns
    assert "password" not in user_columns
    assert any(
        index.name == "uq_users_email_normalized" and index.unique
        for index in User.__table__.indexes
    )


def test_appointment_slot_has_a_database_level_concurrency_guard() -> None:
    slot_index = next(
        index
        for index in Appointment.__table__.indexes
        if index.name == "uq_appointments_active_doctor_slot"
    )

    assert slot_index.unique
    assert "status IN ('pending','confirmed')" in str(
        slot_index.dialect_options["postgresql"]["where"]
    )


def test_status_and_role_values_are_constrained() -> None:
    constraints = [
        constraint
        for model in (User, Appointment, ContactMessage)
        for constraint in model.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    ]

    assert {constraint.name for constraint in constraints} >= {
        "ck_users_role",
        "ck_appointments_status",
        "ck_contact_messages_status",
    }


def test_workflow_foreign_keys_restrict_accidental_patient_or_doctor_deletion() -> None:
    assert next(iter(Appointment.__table__.c.user_id.foreign_keys)).ondelete == "RESTRICT"
    assert next(iter(Appointment.__table__.c.doctor_id.foreign_keys)).ondelete == "RESTRICT"
    assert next(iter(MedicalHistory.__table__.c.user_id.foreign_keys)).ondelete == "RESTRICT"
    assert next(iter(Feedback.__table__.c.user_id.foreign_keys)).ondelete == "RESTRICT"
    assert next(iter(UserSession.__table__.c.user_id.foreign_keys)).ondelete == "RESTRICT"
    assert next(iter(Doctor.__table__.primary_key.columns)).name == "doctor_id"
