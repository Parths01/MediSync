import argparse
import asyncio
import getpass
import os
import re
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pymysql
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, engine
from app.models import Appointment, ContactMessage, Doctor, Feedback, MedicalHistory, User
from app.security import hash_password

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DOCTOR_PHOTO_DIR = REPOSITORY_ROOT / "uploads" / "doctors"
PHOTO_FILENAME_PATTERN = re.compile(r"doctor_[a-f0-9]{8,32}\.(?:jpg|png|webp)\Z")
SERIAL_TABLES = {
    "users": "user_id",
    "doctors": "doctor_id",
    "appointments": "appointment_id",
    "medical_history": "history_id",
    "contact_messages": "contact_id",
    "feedback": "feedback_id",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy legacy MySQL MediSync records into the configured PostgreSQL database."
    )
    parser.add_argument("--source-host", default=os.getenv("MYSQL_HOST", "127.0.0.1"))
    parser.add_argument("--source-port", type=int, default=int(os.getenv("MYSQL_PORT", "3306")))
    parser.add_argument("--source-database", required=True)
    parser.add_argument("--source-user", default=os.getenv("MYSQL_USER", "root"))
    parser.add_argument(
        "--datetime-timezone",
        default="Asia/Kolkata",
        help="IANA timezone for legacy MySQL DATETIME values (default: Asia/Kolkata)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the verified import in one PostgreSQL transaction; otherwise only preview.",
    )
    return parser.parse_args()


def _load_source(args: argparse.Namespace, password: str) -> dict[str, list[dict[str, Any]]]:
    connection = pymysql.connect(
        host=args.source_host,
        port=args.source_port,
        user=args.source_user,
        password=password,
        database=args.source_database,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET time_zone = '+00:00'")
            cursor.execute(
                "SELECT user_id, name, dob, gender, contact, email, `password` AS password_hash, "
                "blood_group, role, registration_date FROM users ORDER BY user_id"
            )
            users = cursor.fetchall()
            cursor.execute(
                "SELECT doctor_id, name, specialization, experience, contact_details, photo, created_at "
                "FROM doctors ORDER BY doctor_id"
            )
            doctors = cursor.fetchall()
            cursor.execute(
                "SELECT appointment_id, user_id, doctor_id, appointment_date, `description`, "
                "status, assigned_by, created_at FROM appointments ORDER BY appointment_id"
            )
            appointments = cursor.fetchall()
            cursor.execute(
                "SELECT history_id, user_id, diagnosis, treatment, notes, recorded_at, created_at "
                "FROM medical_history ORDER BY history_id"
            )
            medical_history = cursor.fetchall()
            cursor.execute(
                "SELECT contact_id, user_id, message, status, created_at "
                "FROM contact_messages ORDER BY contact_id"
            )
            contact_messages = cursor.fetchall()
            cursor.execute(
                "SELECT feedback_id, user_id, message, created_at FROM feedback ORDER BY feedback_id"
            )
            feedback = cursor.fetchall()
        connection.commit()
        return {
            "users": users,
            "doctors": doctors,
            "appointments": appointments,
            "medical_history": medical_history,
            "contact_messages": contact_messages,
            "feedback": feedback,
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _timestamp(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _legacy_datetime(value: datetime, local_timezone: ZoneInfo) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=local_timezone)
    return value.astimezone(local_timezone)


def _doctor_photo(photo: str | None) -> str | None:
    if not photo:
        return None
    filename = PurePosixPath(photo.replace("\\", "/")).name
    if not PHOTO_FILENAME_PATTERN.fullmatch(filename):
        raise ValueError("A legacy doctor photo reference has an unsupported filename.")
    if not (DOCTOR_PHOTO_DIR / filename).is_file():
        raise ValueError("A referenced legacy doctor photo is missing from uploads/doctors.")
    return f"/api/v1/doctors/photos/{filename}"


def _password_hash(value: str) -> str:
    _validate_password(value)
    if value.startswith(("$2a$", "$2b$", "$2y$", "$argon2")):
        return value
    return hash_password(value)


def _validate_password(value: str) -> None:
    if value.startswith(("$2a$", "$2b$", "$2y$", "$argon2")):
        return
    if value.startswith("$"):
        raise ValueError("A legacy password uses an unsupported hash format; import stopped.")
    if not value:
        raise ValueError("A legacy user has an empty password; import stopped.")


def _same_user(existing: User, source: dict[str, Any]) -> bool:
    return existing.role == source["role"]


def _same_doctor(existing: Doctor, source: dict[str, Any], photo: str | None) -> bool:
    return (
        existing.name == source["name"]
        and existing.specialization == source["specialization"]
        and existing.experience == source["experience"]
        and existing.contact_details == source["contact_details"]
        and existing.photo == photo
    )


def _same_appointment(
    existing: Appointment,
    source: dict[str, Any],
    user_id: int,
    doctor_id: int,
    appointment_date: datetime,
    local_timezone: ZoneInfo,
) -> bool:
    return (
        existing.user_id == user_id
        and existing.doctor_id == doctor_id
        and _legacy_datetime(existing.appointment_date, local_timezone) == appointment_date
        and existing.status == source["status"]
        and existing.description == source["description"]
        and existing.assigned_by == source["assigned_by"]
    )


def _same_user_record(
    table_name: str,
    existing: Any,
    source: dict[str, Any],
    mapped_user_id: int,
) -> bool:
    if existing.user_id != mapped_user_id:
        return False
    if table_name == "medical_history":
        return (
            existing.diagnosis == source["diagnosis"]
            and existing.treatment == source["treatment"]
            and existing.notes == source["notes"]
            and existing.recorded_at == source["recorded_at"]
            and existing.created_at == _timestamp(source["created_at"])
        )
    if table_name == "contact_messages":
        return (
            existing.message == source["message"]
            and existing.status == source["status"]
            and existing.created_at == _timestamp(source["created_at"])
        )
    return (
        existing.message == source["message"]
        and existing.created_at == _timestamp(source["created_at"])
    )


def _assert_source_integrity(source: dict[str, list[dict[str, Any]]]) -> None:
    users = source["users"]
    doctors = source["doctors"]
    user_ids = {row["user_id"] for row in users}
    doctor_ids = {row["doctor_id"] for row in doctors}
    normalized_emails = [row["email"].casefold() for row in users]
    if len(normalized_emails) != len(set(normalized_emails)):
        raise ValueError("Source contains duplicate case-insensitive user emails.")

    for row in source["appointments"]:
        if row["user_id"] not in user_ids or row["doctor_id"] not in doctor_ids:
            raise ValueError("A source appointment has an unresolved user or doctor reference.")
    for table_name in ("medical_history", "contact_messages", "feedback"):
        for row in source[table_name]:
            if row["user_id"] not in user_ids:
                raise ValueError(f"A source {table_name} record has an unresolved user reference.")

    active_slots = Counter(
        (row["doctor_id"], row["appointment_date"])
        for row in source["appointments"]
        if row["status"] in {"pending", "confirmed"}
    )
    if any(count > 1 for count in active_slots.values()):
        raise ValueError("Source has conflicting pending or confirmed appointment slots.")

    for row in doctors:
        _doctor_photo(row["photo"])
    for row in users:
        _validate_password(row["password_hash"])


async def _import(
    source: dict[str, list[dict[str, Any]]],
    local_timezone: ZoneInfo,
    apply: bool,
) -> dict[str, int]:
    counts = {table: len(rows) for table, rows in source.items()}
    password_rehash_count = sum(
        not row["password_hash"].startswith(("$2a$", "$2b$", "$2y$", "$argon2"))
        for row in source["users"]
    )
    result = {
        **{f"source_{table}": count for table, count in counts.items()},
        "users_reused_by_email": 0,
        "legacy_passwords_rehashed": password_rehash_count,
    }

    async with AsyncSessionLocal() as session:
        async with session.begin():
            target_users = list((await session.scalars(select(User).with_for_update())).all())
            target_doctors = list((await session.scalars(select(Doctor))).all())
            target_appointments = list((await session.scalars(select(Appointment))).all())
            target_history = list((await session.scalars(select(MedicalHistory))).all())
            target_contacts = list((await session.scalars(select(ContactMessage))).all())
            target_feedback = list((await session.scalars(select(Feedback))).all())

            users_by_email = {row.email.casefold(): row for row in target_users}
            doctors_by_id = {row.doctor_id: row for row in target_doctors}
            appointments_by_id = {row.appointment_id: row for row in target_appointments}
            history_by_id = {row.history_id: row for row in target_history}
            contacts_by_id = {row.contact_id: row for row in target_contacts}
            feedback_by_id = {row.feedback_id: row for row in target_feedback}

            user_map: dict[int, int] = {}
            next_user_id = max((row.user_id for row in target_users), default=0) + 1
            for row in source["users"]:
                existing = users_by_email.get(row["email"].casefold())
                if existing is not None:
                    if not _same_user(existing, row):
                        raise ValueError(
                            "A source email already exists in PostgreSQL with a different account role."
                        )
                    user_map[row["user_id"]] = existing.user_id
                    result["users_reused_by_email"] += 1
                    continue
                if not apply:
                    user_map[row["user_id"]] = next_user_id
                    next_user_id += 1
                    continue

                user = User(
                    name=row["name"],
                    dob=row["dob"],
                    gender=row["gender"],
                    contact=row["contact"],
                    email=row["email"],
                    password_hash=_password_hash(row["password_hash"]),
                    blood_group=row["blood_group"],
                    role=row["role"],
                    registration_date=_timestamp(row["registration_date"]),
                )
                session.add(user)
                await session.flush()
                user_map[row["user_id"]] = user.user_id

            doctor_map: dict[int, int] = {}
            for row in source["doctors"]:
                photo = _doctor_photo(row["photo"])
                existing = doctors_by_id.get(row["doctor_id"])
                if existing is not None:
                    if not _same_doctor(existing, row, photo):
                        raise ValueError(
                            "A source doctor ID already exists in PostgreSQL with different details."
                        )
                    doctor_map[row["doctor_id"]] = existing.doctor_id
                    continue
                doctor_map[row["doctor_id"]] = row["doctor_id"]
                if apply:
                    session.add(
                        Doctor(
                            doctor_id=row["doctor_id"],
                            name=row["name"],
                            specialization=row["specialization"],
                            experience=row["experience"],
                            contact_details=row["contact_details"],
                            photo=photo,
                            created_at=_timestamp(row["created_at"]),
                        )
                    )
            if apply:
                await session.flush()

            result["new_doctors"] = sum(
                row["doctor_id"] not in doctors_by_id for row in source["doctors"]
            )
            result["new_users"] = counts["users"] - result["users_reused_by_email"]

            for row in source["appointments"]:
                mapped_user_id = user_map[row["user_id"]]
                mapped_doctor_id = doctor_map[row["doctor_id"]]
                appointment_date = _legacy_datetime(row["appointment_date"], local_timezone)
                existing = appointments_by_id.get(row["appointment_id"])
                if existing is not None:
                    if not _same_appointment(
                        existing,
                        row,
                        mapped_user_id,
                        mapped_doctor_id,
                        appointment_date,
                        local_timezone,
                    ):
                        raise ValueError(
                            "A source appointment ID already exists in PostgreSQL with different details."
                        )
                    continue
                if apply:
                    session.add(
                        Appointment(
                            appointment_id=row["appointment_id"],
                            user_id=mapped_user_id,
                            doctor_id=mapped_doctor_id,
                            appointment_date=appointment_date,
                            description=row["description"],
                            status=row["status"],
                            assigned_by=row["assigned_by"],
                            created_at=_timestamp(row["created_at"]),
                        )
                    )

            result["new_appointments"] = sum(
                row["appointment_id"] not in appointments_by_id
                for row in source["appointments"]
            )
            await _import_user_records(
                session,
                "medical_history",
                source["medical_history"],
                history_by_id,
                user_map,
                apply,
            )
            await _import_user_records(
                session,
                "contact_messages",
                source["contact_messages"],
                contacts_by_id,
                user_map,
                apply,
            )
            await _import_user_records(
                session,
                "feedback",
                source["feedback"],
                feedback_by_id,
                user_map,
                apply,
            )

            result["new_medical_history"] = counts["medical_history"] - sum(
                row["history_id"] in history_by_id for row in source["medical_history"]
            )
            result["new_contact_messages"] = counts["contact_messages"] - sum(
                row["contact_id"] in contacts_by_id for row in source["contact_messages"]
            )
            result["new_feedback"] = counts["feedback"] - sum(
                row["feedback_id"] in feedback_by_id for row in source["feedback"]
            )
            if apply:
                await session.flush()
                for table_name, id_column in SERIAL_TABLES.items():
                    await session.execute(
                        text(
                            f"SELECT setval(pg_get_serial_sequence('public.{table_name}', "
                            f"'{id_column}'), COALESCE(MAX({id_column}), 1), "
                            f"COUNT(*) > 0) FROM public.{table_name}"
                        )
                    )

    return result


async def _import_user_records(
    session: AsyncSession,
    table_name: str,
    rows: list[dict[str, Any]],
    existing_by_id: dict[int, Any],
    user_map: dict[int, int],
    apply: bool,
) -> None:
    id_column = {
        "medical_history": "history_id",
        "contact_messages": "contact_id",
        "feedback": "feedback_id",
    }[table_name]
    model = {
        "medical_history": MedicalHistory,
        "contact_messages": ContactMessage,
        "feedback": Feedback,
    }[table_name]
    for row in rows:
        record_id = row[id_column]
        mapped_user_id = user_map[row["user_id"]]
        existing = existing_by_id.get(record_id)
        if existing is not None:
            if not _same_user_record(
                table_name,
                existing,
                row,
                mapped_user_id,
            ):
                raise ValueError(
                    f"A source {table_name} ID already exists in PostgreSQL with different details."
                )
            continue
        if not apply:
            continue
        values = {key: value for key, value in row.items() if key not in {id_column, "user_id"}}
        values["created_at"] = _timestamp(values.get("created_at"))
        values["user_id"] = mapped_user_id
        if table_name == "medical_history":
            values["recorded_at"] = row["recorded_at"]
        session.add(model(**{id_column: record_id, **values}))


async def _run() -> None:
    args = _parse_args()
    try:
        local_timezone = ZoneInfo(args.datetime_timezone)
    except ZoneInfoNotFoundError as error:
        raise ValueError("The supplied DATETIME timezone is not a valid IANA timezone.") from error

    password = os.getenv("MYSQL_PASSWORD") or getpass.getpass("MySQL source password: ")
    if not password:
        raise ValueError("The MySQL source password cannot be empty.")

    source = _load_source(args, password)
    _assert_source_integrity(source)
    engine.echo = False
    result = await _import(source, local_timezone, args.apply)
    print("Source rows:", {key.removeprefix("source_"): value for key, value in result.items() if key.startswith("source_")})
    print(
        "Planned inserts:",
        {
            key.removeprefix("new_"): value
            for key, value in result.items()
            if key.startswith("new_")
        },
    )
    print(
        "Accounts reusing an existing PostgreSQL account by email:",
        result["users_reused_by_email"],
    )
    print("Legacy plaintext passwords re-hashed using Argon2:", result["legacy_passwords_rehashed"])
    print("Age values were not copied; the modern schema derives age from date of birth.")
    print("Migration mode:", "APPLIED" if args.apply else "DRY RUN (no PostgreSQL records written)")


def main() -> None:
    async def run_and_dispose() -> None:
        try:
            await _run()
        finally:
            await engine.dispose()

    try:
        asyncio.run(run_and_dispose())
    except KeyboardInterrupt:
        raise SystemExit("MySQL migration interrupted; any PostgreSQL transaction was rolled back.")


if __name__ == "__main__":
    main()
