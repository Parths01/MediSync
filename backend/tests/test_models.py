from sqlalchemy import CheckConstraint

from app.database import Base
from app.models import (
    AIFeedback,
    AIConversation,
    AIMessage,
    Appointment,
    ContactMessage,
    Doctor,
    Feedback,
    MedicalHistory,
    OperatorAuditEvent,
    User,
    UserSession,
)


def test_all_legacy_workflow_entities_have_postgres_models() -> None:
    assert set(Base.metadata.tables) == {
        "ai_conversations",
        "ai_feedback",
        "ai_messages",
        "ai_rate_limits",
        "ai_usage_events",
        "appointments",
        "contact_messages",
        "doctors",
        "feedback",
        "medical_history",
        "operator_audit_events",
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
    assert next(iter(AIConversation.__table__.c.user_id.foreign_keys)).ondelete == "CASCADE"
    assert next(iter(AIMessage.__table__.c.conversation_id.foreign_keys)).ondelete == "CASCADE"
    assert next(iter(AIFeedback.__table__.c.message_id.foreign_keys)).ondelete == "CASCADE"
    assert next(iter(Doctor.__table__.primary_key.columns)).name == "doctor_id"


def test_ai_conversations_have_indexed_expiry_and_feedback_follows_message_cascade() -> None:
    assert not AIConversation.__table__.c.expires_at.nullable
    assert any(index.name == "ix_ai_conversations_expires_at" for index in AIConversation.__table__.indexes)


def test_operator_audit_records_only_template_action_and_nulls_deleted_actor() -> None:
    assert next(iter(OperatorAuditEvent.__table__.c.actor_user_id.foreign_keys)).ondelete == "SET NULL"
    assert OperatorAuditEvent.__table__.c.action.type.length == 256
    assert {index.name for index in OperatorAuditEvent.__table__.indexes} >= {
        "ix_operator_audit_created_at",
        "ix_operator_audit_actor_created",
    }
