from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token
from app.db.models import Base, EventType, Schedule, User
from app.db.session import get_db
from app.main import app
from app.services.calendar import booking_url, dumps_json, prepare_availability


MONDAY = "2099-01-05"
TUESDAY = "2099-01-06"


@pytest.fixture()
def owner() -> Iterator[tuple[TestClient, str, Schedule]]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    testing_session = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )
    Base.metadata.create_all(engine)

    def override_get_db() -> Iterator[Session]:
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with testing_session() as db:
        schedule = _seed(db)
        token = create_access_token(schedule.owner_id)
    with TestClient(app) as test_client:
        yield test_client, token, schedule
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(engine)


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _slots(client: TestClient, day: str) -> list[dict[str, object]]:
    response = client.get(
        "/public/slots",
        params={
            "username": "hostuser",
            "eventTypeSlug": "discovery-call",
            "start": day,
            "end": day,
            "timeZone": "UTC",
            "durationMinutes": 30,
        },
    )
    assert response.status_code == 200
    return response.json()["data"]["days"][0]["slots"]


def test_weekly_availability_change_reflected_in_slots(owner: tuple[TestClient, str, Schedule]) -> None:
    client, token, schedule = owner
    assert _slots(client, MONDAY) != []
    assert _slots(client, TUESDAY) == []

    patch = client.patch(
        f"/schedules/{schedule.id}",
        headers=_auth(token),
        json={"availability": [{"days": ["tuesday"], "startTime": "09:00", "endTime": "17:00"}]},
    )
    assert patch.status_code == 200

    assert _slots(client, MONDAY) == []
    assert _slots(client, TUESDAY) != []


def test_override_away_day_removes_slots(owner: tuple[TestClient, str, Schedule]) -> None:
    client, token, schedule = owner
    assert _slots(client, MONDAY) != []

    patch = client.patch(
        f"/schedules/{schedule.id}",
        headers=_auth(token),
        json={"overrides": [{"date": MONDAY, "unavailable": True}]},
    )
    assert patch.status_code == 200

    assert _slots(client, MONDAY) == []


def test_available_override_adds_slots_on_off_day(owner: tuple[TestClient, str, Schedule]) -> None:
    client, token, schedule = owner
    saturday = "2099-01-10"
    assert _slots(client, saturday) == []

    patch = client.patch(
        f"/schedules/{schedule.id}",
        headers=_auth(token),
        json={"overrides": [{"date": saturday, "unavailable": False, "startTime": "09:00", "endTime": "11:00"}]},
    )
    assert patch.status_code == 200

    assert _slots(client, saturday) != []


def test_timezone_change_shifts_slots(owner: tuple[TestClient, str, Schedule]) -> None:
    client, token, schedule = owner
    before = _slots(client, MONDAY)
    assert "T09:00" in str(before[0]["start"])

    patch = client.patch(
        f"/schedules/{schedule.id}",
        headers=_auth(token),
        json={"timeZone": "Europe/Moscow"},
    )
    assert patch.status_code == 200

    after = _slots(client, MONDAY)
    assert "T06:00" in str(after[0]["start"])


def test_create_schedule_as_default_updates_default(owner: tuple[TestClient, str, Schedule]) -> None:
    client, token, _ = owner

    created = client.post(
        "/schedules",
        headers=_auth(token),
        json={
            "name": "Evenings",
            "timeZone": "UTC",
            "isDefault": True,
            "availability": [{"days": ["wednesday"], "startTime": "18:00", "endTime": "20:00"}],
        },
    )
    assert created.status_code == 201
    new_id = created.json()["data"]["id"]

    default = client.get("/schedules/default", headers=_auth(token))
    assert default.status_code == 200
    assert default.json()["data"]["id"] == new_id


def _seed(db: Session) -> Schedule:
    user = User(
        email="host@example.com",
        username="hostuser",
        name="Host User",
        time_zone="UTC",
        password_hash="pbkdf2_sha256$1$salt$digest",
    )
    db.add(user)
    db.flush()

    schedule = Schedule(
        owner_id=user.id,
        name="Working hours",
        time_zone="UTC",
        is_default=True,
        availability_json=dumps_json(
            prepare_availability([{"days": ["monday"], "startTime": "09:00", "endTime": "17:00"}])
        ),
        overrides_json="[]",
    )
    db.add(schedule)
    db.flush()
    user.default_schedule_id = schedule.id

    event_type = EventType(
        owner_id=user.id,
        schedule_id=schedule.id,
        title="Discovery call",
        slug="discovery-call",
        description=None,
        duration_minutes=30,
        slot_interval_minutes=30,
        minimum_booking_notice_minutes=None,
        before_event_buffer_minutes=None,
        after_event_buffer_minutes=None,
        booking_window_json=None,
        confirmation_policy_type="automatic",
        block_slot_before_confirmation=False,
        hidden=False,
        booking_url=booking_url(user.username, "discovery-call"),
    )
    db.add(event_type)
    db.commit()
    db.refresh(schedule)
    return schedule
