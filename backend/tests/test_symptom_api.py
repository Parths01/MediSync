from datetime import date

import httpx
import pytest

from app.database import get_db
from app.main import app
from app.models import Doctor, User
from app.security import get_current_user


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
                ),
                Doctor(
                    doctor_id=2,
                    name="Zoya Rao",
                    specialization="Neurologist",
                    experience=8,
                    contact_details="9000000002",
                ),
                Doctor(
                    doctor_id=3,
                    name="Meera Iyer",
                    specialization="Cardiologist",
                    experience=10,
                    contact_details="9000000003",
                ),
            ]
        )


def patient_user() -> User:
    return User(
        user_id=1,
        name="Test Patient",
        dob=date(1990, 1, 1),
        gender="Other",
        contact="9000010000",
        email="patient@example.test",
        password_hash="unused",
        role="patient",
    )


@pytest.mark.asyncio
async def test_symptom_recommendations_require_authentication() -> None:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        client.cookies.set("medisync_csrf", "test-csrf")
        response = await client.post(
            "/api/v1/patient/symptom-check",
            headers={
                "Origin": "http://localhost:3000",
                "X-CSRF-Token": "test-csrf",
            },
            json={"symptoms": "throbbing headache with sensitivity to light"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_symptom_recommendations_return_specialty_matched_doctors() -> None:
    app.dependency_overrides[get_db] = lambda: FakeSession()
    app.dependency_overrides[get_current_user] = patient_user
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            client.cookies.set("medisync_csrf", "test-csrf")
            response = await client.post(
                "/api/v1/patient/symptom-check",
                headers={
                    "Origin": "http://localhost:3000",
                    "X-CSRF-Token": "test-csrf",
                },
                json={"symptoms": "throbbing headache with sensitivity to light"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["recommendations"][0]["specialty"] == "Neurologist"
    assert "synthetic examples" in payload["disclaimer"]
    assert "not medical advice" in payload["disclaimer"]
    specialty_order = {
        recommendation["specialty"]: index
        for index, recommendation in enumerate(payload["recommendations"])
    }
    doctor_order = [
        (specialty_order[doctor["specialization"]], doctor["name"])
        for doctor in payload["doctors"]
    ]
    assert doctor_order == sorted(doctor_order)


@pytest.mark.asyncio
async def test_symptom_recommendations_reject_blank_text() -> None:
    app.dependency_overrides[get_current_user] = patient_user
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            client.cookies.set("medisync_csrf", "test-csrf")
            response = await client.post(
                "/api/v1/patient/symptom-check",
                headers={
                    "Origin": "http://localhost:3000",
                    "X-CSRF-Token": "test-csrf",
                },
                json={"symptoms": "   "},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
