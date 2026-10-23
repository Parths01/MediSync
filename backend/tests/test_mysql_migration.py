from datetime import datetime, timezone
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

import bcrypt

from app.migrate_mysql import (
    _assert_source_integrity,
    _legacy_datetime,
    _password_hash,
    _same_appointment,
    _timestamp,
)
from app.security import verify_password_and_update


def test_unsupported_password_hash_format_stops_migration() -> None:
    with pytest.raises(ValueError, match="unsupported hash format"):
        _password_hash("$unknown$not-supported")


def test_legacy_plaintext_password_is_rehashed_for_modern_login() -> None:
    password = "legacy-test-password"
    migrated_hash = _password_hash(password)

    assert migrated_hash.startswith("$argon2")
    assert verify_password_and_update(password, migrated_hash)[0]


def test_supported_bcrypt_hash_is_preserved_for_login_upgrade() -> None:
    password = b"legacy-test-password"
    legacy_hash = bcrypt.hashpw(password, bcrypt.gensalt()).decode()

    migrated_hash = _password_hash(legacy_hash)

    assert migrated_hash == legacy_hash
    assert verify_password_and_update(password.decode(), migrated_hash)[0]


def test_datetime_conversion_preserves_legacy_local_time_and_utc_timestamps() -> None:
    source_datetime = datetime(2025, 2, 11, 9, 30)
    source_timestamp = datetime(2025, 2, 11, 4, 0)

    assert _legacy_datetime(source_datetime, ZoneInfo("Asia/Kolkata")).isoformat() == (
        "2025-02-11T09:30:00+05:30"
    )
    assert _timestamp(source_timestamp) == datetime(2025, 2, 11, 4, 0, tzinfo=timezone.utc)


def test_appointment_comparison_preserves_timezone_aware_postgresql_values() -> None:
    local_timezone = ZoneInfo("Asia/Kolkata")
    source_date = datetime(2025, 2, 11, 9, 30)
    source = {
        "status": "completed",
        "description": "follow-up",
        "assigned_by": None,
    }
    existing = SimpleNamespace(
        user_id=2,
        doctor_id=1,
        appointment_date=datetime(2025, 2, 11, 4, 0, tzinfo=timezone.utc),
        status="completed",
        description="follow-up",
        assigned_by=None,
    )

    assert _same_appointment(
        existing,
        source,
        2,
        1,
        _legacy_datetime(source_date, local_timezone),
        local_timezone,
    )


def _source_fixture(appointments: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    return {
        "users": [
            {
                "user_id": 1,
                "email": "patient@example.test",
                "password_hash": "legacy-pass",
            }
        ],
        "doctors": [{"doctor_id": 1, "photo": None}],
        "appointments": appointments,
        "medical_history": [],
        "contact_messages": [],
        "feedback": [],
    }


def test_source_integrity_allows_duplicate_completed_historical_slots() -> None:
    appointment_date = datetime(2025, 2, 11, 9, 30)
    appointments = [
        {
            "user_id": 1,
            "doctor_id": 1,
            "appointment_date": appointment_date,
            "status": "completed",
        },
        {
            "user_id": 1,
            "doctor_id": 1,
            "appointment_date": appointment_date,
            "status": "completed",
        },
    ]

    _assert_source_integrity(_source_fixture(appointments))


def test_source_integrity_rejects_duplicate_active_slots() -> None:
    appointment_date = datetime(2025, 2, 11, 9, 30)
    appointments = [
        {
            "user_id": 1,
            "doctor_id": 1,
            "appointment_date": appointment_date,
            "status": "pending",
        },
        {
            "user_id": 1,
            "doctor_id": 1,
            "appointment_date": appointment_date,
            "status": "confirmed",
        },
    ]

    with pytest.raises(ValueError, match="conflicting pending or confirmed"):
        _assert_source_integrity(_source_fixture(appointments))
