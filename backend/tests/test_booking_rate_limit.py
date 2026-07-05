from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base, EventType, Schedule, User
from app.db.session import get_db
from app.main import app
from app.services.calendar import booking_url, dumps_json, prepare_availability
from app.services.rate_limit import SlidingWindowRateLimiter, get_booking_rate_limiter


@pytest.fixture()
def client_with_limit() -> Iterator[tuple[TestClient, dict[str, float]]]:
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

    clock = {"t": 0.0}
    limiter = SlidingWindowRateLimiter(max_events=1, window_seconds=60.0, clock=lambda: clock["t"])

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_booking_rate_limiter] = lambda: limiter
    with testing_session() as db:
        _seed_public_event_type(db)
    with TestClient(app) as test_client:
        yield test_client, clock
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_booking_rate_limiter, None)
    Base.metadata.drop_all(engine)


def _payload(start: str = "2099-01-05T09:00:00Z") -> dict[str, object]:
    return {
        "username": "hostuser",
        "eventTypeSlug": "discovery-call",
        "start": start,
        "durationMinutes": 30,
        "attendee": {"name": "Guest", "email": "guest@example.com", "timeZone": "UTC"},
    }


def test_booking_within_limit_succeeds(client_with_limit: tuple[TestClient, dict[str, float]]) -> None:
    client, _ = client_with_limit

    response = client.post("/bookings", json=_payload())

    assert response.status_code == 201


def test_booking_over_limit_returns_429(client_with_limit: tuple[TestClient, dict[str, float]]) -> None:
    client, _ = client_with_limit

    first = client.post("/bookings", json=_payload("2099-01-05T09:00:00Z"))
    second = client.post("/bookings", json=_payload("2099-01-05T09:30:00Z"))

    assert first.status_code == 201
    assert second.status_code == 429
    assert second.json()["error"]["code"] == "rate_limited"


def test_booking_allowed_again_after_window(client_with_limit: tuple[TestClient, dict[str, float]]) -> None:
    client, clock = client_with_limit

    assert client.post("/bookings", json=_payload("2099-01-05T09:00:00Z")).status_code == 201
    assert client.post("/bookings", json=_payload("2099-01-05T09:30:00Z")).status_code == 429

    clock["t"] += 61.0
    recovered = client.post("/bookings", json=_payload("2099-01-05T09:30:00Z"))

    assert recovered.status_code == 201


def test_validation_error_does_not_consume_limit(client_with_limit: tuple[TestClient, dict[str, float]]) -> None:
    client, _ = client_with_limit

    invalid = _payload()
    del invalid["attendee"]
    rejected = client.post("/bookings", json=invalid)
    accepted = client.post("/bookings", json=_payload())

    assert rejected.status_code == 400
    assert rejected.json()["error"]["code"] == "validation_error"
    assert accepted.status_code == 201


def _seed_public_event_type(db: Session) -> EventType:
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
    db.refresh(event_type)
    return event_type
