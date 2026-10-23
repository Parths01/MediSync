import argparse
import asyncio
from datetime import date
from getpass import getpass

from email_validator import validate_email
from sqlalchemy import func, select, text

from app.database import AsyncSessionLocal, engine
from app.models import User
from app.security import hash_password


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create the first MediSync administrator in the configured PostgreSQL database."
    )
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--dob", required=True, help="Date of birth in YYYY-MM-DD format")
    parser.add_argument("--gender", required=True, choices=("Male", "Female", "Other"))
    parser.add_argument("--contact", required=True)
    return parser.parse_args()


async def _create_first_admin(
    *,
    name: str,
    email: str,
    dob: date,
    gender: str,
    contact: str,
    password: str,
) -> int:
    async with AsyncSessionLocal.begin() as session:
        await session.execute(text("SELECT pg_advisory_xact_lock(1297303379)"))
        admin_count = await session.scalar(
            select(func.count()).select_from(User).where(User.role == "admin")
        )
        if admin_count:
            raise ValueError("An administrator already exists; this command only creates the first one.")

        existing_user_id = await session.scalar(
            select(User.user_id).where(func.lower(User.email) == email.lower())
        )
        if existing_user_id is not None:
            raise ValueError("That email already belongs to an account. No role changes were made.")

        user = User(
            name=name,
            dob=dob,
            gender=gender,
            contact=contact,
            email=email,
            password_hash=hash_password(password),
            blood_group=None,
            role="admin",
        )
        session.add(user)
        await session.flush()
        return user.user_id


async def _run() -> None:
    args = _parse_args()
    name = args.name.strip()
    contact = args.contact.strip()
    if not name or len(name) > 255:
        raise ValueError("Name must contain 1 to 255 characters.")
    if not contact or len(contact) > 15:
        raise ValueError("Contact must contain 1 to 15 characters.")

    try:
        dob = date.fromisoformat(args.dob)
    except ValueError as error:
        raise ValueError("Date of birth must use YYYY-MM-DD format.") from error
    if dob > date.today():
        raise ValueError("Date of birth cannot be in the future.")

    email = validate_email(args.email.strip(), check_deliverability=False).normalized
    password = getpass("Admin password (minimum 14 characters): ")
    confirmation = getpass("Confirm admin password: ")
    if len(password) < 14:
        raise ValueError("Admin password must be at least 14 characters.")
    if password != confirmation:
        raise ValueError("The password confirmation does not match.")

    user_id = await _create_first_admin(
        name=name,
        email=email,
        dob=dob,
        gender=args.gender,
        contact=contact,
        password=password,
    )
    print(f"Created the first administrator account (user ID {user_id}).")


def main() -> None:
    try:
        asyncio.run(_run())
    finally:
        asyncio.run(engine.dispose())


if __name__ == "__main__":
    main()
