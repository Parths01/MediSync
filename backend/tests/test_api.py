from io import BytesIO
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest
from PIL import Image

from app.database import get_db
from app.api.routes import doctors as doctors_route
from app.main import app
from app.models import Doctor, User
from app.security import get_admin_user


class FakeResult:
    def __init__(self, rows: list[Doctor]) -> None:
        self.rows = rows

    def scalars(self) -> "FakeResult":
        return self

    def all(self) -> list[Doctor]:
        return self.rows


class FakeSession:
    async def execute(self, _statement: object) -> FakeResult:
        return FakeResult(
            [
                Doctor(
                    doctor_id=1,
                    name="Aarav Mehta",
                    specialization="Neurologist",
                    experience=12,
                    contact_details="9000000001",
                    photo=None,
                    created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
                )
            ]
        )


class FakeDoctorWriteSession:
    def __init__(self) -> None:
        self.doctor = Doctor(
            doctor_id=1,
            name="Aarav Mehta",
            specialization="Neurologist",
            experience=12,
            contact_details="9000000001",
            photo=None,
            created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )

    async def get(self, _model: object, doctor_id: int) -> Doctor | None:
        return self.doctor if doctor_id == self.doctor.doctor_id else None

    async def commit(self) -> None:
        return None

    async def refresh(self, _doctor: Doctor) -> None:
        return None

    async def rollback(self) -> None:
        return None


@pytest.mark.asyncio
async def test_health_check() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_cors_allows_credentialed_api_requests_from_frontend() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,x-csrf-token",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "POST" in response.headers["access-control-allow-methods"]
    assert "x-csrf-token" in response.headers["access-control-allow-headers"].lower()


@pytest.mark.asyncio
async def test_list_doctors_returns_serialized_doctors() -> None:
    app.dependency_overrides[get_db] = lambda: FakeSession()
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/v1/doctors")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [
        {
            "doctor_id": 1,
            "name": "Aarav Mehta",
            "specialization": "Neurologist",
            "experience": 12,
            "contact_details": "9000000001",
            "photo": None,
            "created_at": "2025-01-01T00:00:00Z",
        }
    ]


@pytest.mark.asyncio
async def test_csrf_endpoint_sets_matching_readable_cookie() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/auth/csrf")

    assert response.status_code == 200
    token = response.json()["csrf_token"]
    assert token
    assert response.cookies.get("medisync_csrf") == token


@pytest.mark.asyncio
async def test_registration_rejects_missing_csrf_token() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/auth/register",
            headers={"Origin": "http://localhost:3000"},
            json={
                "name": "Test Patient",
                "dob": "1990-01-01",
                "gender": "Other",
                "contact": "1234567890",
                "email": "test@example.com",
                "password": "long-enough-password",
                "blood_group": "O+",
            },
        )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_current_user_requires_a_session_cookie() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_patient_and_admin_routes_require_authentication() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        patient_response = await client.get("/api/v1/patient/appointments")
        admin_response = await client.get("/api/v1/admin/dashboard")
        insights_response = await client.get("/api/v1/admin/insights")

    assert patient_response.status_code == 401
    assert admin_response.status_code == 401
    assert insights_response.status_code == 401


@pytest.mark.asyncio
async def test_admin_can_upload_and_retrieve_valid_doctor_photo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    photo_bytes = BytesIO()
    Image.new("RGB", (2, 2), color="teal").save(photo_bytes, format="PNG")
    contents = photo_bytes.getvalue()
    session = FakeDoctorWriteSession()
    monkeypatch.setattr(doctors_route, "DOCTOR_PHOTO_DIR", tmp_path)
    app.dependency_overrides[get_db] = lambda: session
    app.dependency_overrides[get_admin_user] = lambda: User(
        user_id=1,
        name="Admin",
        dob=datetime(1990, 1, 1, tzinfo=timezone.utc).date(),
        gender="Other",
        contact="0000000000",
        email="admin@example.test",
        password_hash="unused",
        role="admin",
    )
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            client.cookies.set("medisync_csrf", "test-csrf")
            response = await client.post(
                "/api/v1/doctors/1/photo",
                headers={
                    "Origin": "http://localhost:3000",
                    "X-CSRF-Token": "test-csrf",
                },
                files={"image": ("doctor.png", contents, "image/png")},
            )
            photo_response = await client.get(response.json()["photo"])
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["photo"].startswith("/api/v1/doctors/photos/doctor_")
    assert photo_response.status_code == 200
    assert photo_response.headers["content-type"] == "image/png"
    assert photo_response.content == contents


@pytest.mark.asyncio
async def test_doctor_photo_upload_rejects_non_image_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeDoctorWriteSession()
    monkeypatch.setattr(doctors_route, "DOCTOR_PHOTO_DIR", tmp_path)
    app.dependency_overrides[get_db] = lambda: session
    app.dependency_overrides[get_admin_user] = lambda: User(
        user_id=1,
        name="Admin",
        dob=datetime(1990, 1, 1, tzinfo=timezone.utc).date(),
        gender="Other",
        contact="0000000000",
        email="admin@example.test",
        password_hash="unused",
        role="admin",
    )
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            client.cookies.set("medisync_csrf", "test-csrf")
            response = await client.post(
                "/api/v1/doctors/1/photo",
                headers={
                    "Origin": "http://localhost:3000",
                    "X-CSRF-Token": "test-csrf",
                },
                files={"image": ("fake.png", b"not an image", "image/png")},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 415
    assert list(tmp_path.iterdir()) == []
