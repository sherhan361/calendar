from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base, Booking, EventType, Schedule, User
from app.db.session import get_db
from app.main import app
from app.services.calendar import booking_url, dumps_json, prepare_availability


ATTENDEE_TOKEN = "attendee-token-abc"
BOOKING_UID = "booking_public_cancel"


@pytest.fixture()
def client() -> Iterator[TestClient]:
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
        _seed_booking(db)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(engine)


def _cancel(client: TestClient, token: str, reason: str | None = None) -> object:
    body = {"reason": reason} if reason is not None else {}
    return client.post(f"/public/bookings/{BOOKING_UID}/cancel?token={token}", json=body)


def test_public_cancel_marks_booking_cancelled_with_reason(client: TestClient) -> None:
    response = _cancel(client, ATTENDEE_TOKEN, reason="Не смогу прийти")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "cancelled"
    assert data["cancellationReason"] == "Не смогу прийти"


def test_public_cancel_without_reason_leaves_reason_empty(client: TestClient) -> None:
    response = _cancel(client, ATTENDEE_TOKEN)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "cancelled"
    assert "cancellationReason" not in data


def test_public_cancel_twice_returns_conflict(client: TestClient) -> None:
    first = _cancel(client, ATTENDEE_TOKEN, reason="first")
    second = _cancel(client, ATTENDEE_TOKEN, reason="second")

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "conflict"


def test_public_cancel_with_invalid_token_is_rejected(client: TestClient) -> None:
    response = _cancel(client, "wrong-token", reason="nope")

    assert response.status_code == 410
    assert response.json()["error"]["code"] == "link_expired"


def test_public_cancel_unknown_booking_returns_not_found(client: TestClient) -> None:
    response = client.post(f"/public/bookings/booking_missing/cancel?token={ATTENDEE_TOKEN}", json={})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def _seed_booking(db: Session) -> None:
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
    db.flush()

    start = datetime(2099, 1, 5, 9, tzinfo=timezone.utc)
    db.add(
        Booking(
            uid=BOOKING_UID,
            event_type_id=event_type.id,
            owner_id=user.id,
            title=event_type.title,
            description=None,
            status="confirmed",
            start=start,
            end=start + timedelta(minutes=30),
            duration_minutes=30,
            attendee_name="Attendee",
            attendee_email="attendee@example.com",
            attendee_time_zone="UTC",
            attendee_token=ATTENDEE_TOKEN,
        )
    )
    db.commit()
