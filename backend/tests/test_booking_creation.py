from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.application import bookings as booking_use_cases
from app.db.models import Base, Booking, EventType, Schedule, User
from app.db.session import get_db
from app.main import app
from app.services.calendar import booking_url, dumps_json, prepare_availability


SLOT_START = "2099-01-05T09:00:00Z"


@pytest.fixture()
def context() -> Iterator[tuple[TestClient, sessionmaker[Session], EventType]]:
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
        event_type = _seed_public_event_type(db)
    with TestClient(app) as test_client:
        yield test_client, testing_session, event_type
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(engine)


def _payload(idempotency_key: str | None = None, email: str = "guest@example.com") -> dict[str, object]:
    body: dict[str, object] = {
        "username": "hostuser",
        "eventTypeSlug": "discovery-call",
        "start": SLOT_START,
        "durationMinutes": 30,
        "attendee": {"name": "Guest", "email": email, "timeZone": "UTC"},
    }
    if idempotency_key is not None:
        body["idempotencyKey"] = idempotency_key
    return body


def test_create_booking_succeeds(context: tuple[TestClient, sessionmaker[Session], EventType]) -> None:
    client, _, _ = context

    response = client.post("/bookings", json=_payload())

    assert response.status_code == 201
    assert response.json()["data"]["status"] == "confirmed"


def test_duplicate_submit_with_same_key_returns_same_booking(
    context: tuple[TestClient, sessionmaker[Session], EventType],
) -> None:
    client, testing_session, _ = context

    first = client.post("/bookings", json=_payload("retry-key-123"))
    second = client.post("/bookings", json=_payload("retry-key-123"))

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["data"]["uid"] == second.json()["data"]["uid"]

    with testing_session() as db:
        bookings = db.scalars(select(Booking)).all()
    assert len(bookings) == 1


def test_second_booking_for_taken_slot_conflicts(
    context: tuple[TestClient, sessionmaker[Session], EventType],
) -> None:
    client, testing_session, _ = context

    first = client.post("/bookings", json=_payload("slot-key-a", email="a@example.com"))
    second = client.post("/bookings", json=_payload("slot-key-b", email="b@example.com"))

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "conflict"

    with testing_session() as db:
        active = db.scalars(
            select(Booking).where(Booking.status.in_(["pending_host", "pending_attendee", "confirmed"]))
        ).all()
    assert len(active) == 1


def test_race_on_same_slot_returns_conflict_via_integrity_error(
    context: tuple[TestClient, sessionmaker[Session], EventType],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, testing_session, event_type = context
    start = datetime(2099, 1, 5, 9, tzinfo=timezone.utc)

    with testing_session() as db:
        db.add(_booking(event_type, "booking_winner", "confirmed", start, "winner"))
        db.commit()

    monkeypatch.setattr(booking_use_cases, "event_type_slot_is_available", lambda *args, **kwargs: True)
    response = client.post("/bookings", json=_payload("late-key-123", email="late@example.com"))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"

    with testing_session() as db:
        active = db.scalars(
            select(Booking).where(Booking.status.in_(["pending_host", "pending_attendee", "confirmed"]))
        ).all()
    assert len(active) == 1


def test_active_slot_unique_index_blocks_concurrent_duplicate(
    context: tuple[TestClient, sessionmaker[Session], EventType],
) -> None:
    _, testing_session, event_type = context
    start = datetime(2099, 1, 5, 9, tzinfo=timezone.utc)

    with testing_session() as db:
        db.add(_booking(event_type, "booking_one", "confirmed", start, "one"))
        db.commit()

    with testing_session() as db:
        db.add(_booking(event_type, "booking_two", "confirmed", start, "two"))
        with pytest.raises(IntegrityError):
            db.commit()


def test_cancelled_slot_can_be_rebooked(
    context: tuple[TestClient, sessionmaker[Session], EventType],
) -> None:
    _, testing_session, event_type = context
    start = datetime(2099, 1, 5, 9, tzinfo=timezone.utc)

    with testing_session() as db:
        db.add(_booking(event_type, "booking_cancelled", "cancelled", start, "cancelled"))
        db.commit()
        db.add(_booking(event_type, "booking_new", "confirmed", start, "new"))
        db.commit()
        active = db.scalars(select(Booking).where(Booking.status == "confirmed")).all()
    assert len(active) == 1


def test_success_response_exposes_status_title_and_time(
    context: tuple[TestClient, sessionmaker[Session], EventType],
) -> None:
    client, _, _ = context

    response = client.post("/bookings", json=_payload())

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["title"] == "Discovery call"
    assert data["status"] == "confirmed"
    assert data["start"].startswith("2099-01-05T09:00:00")
    assert data["durationMinutes"] == 30


def test_blank_attendee_name_is_rejected(
    context: tuple[TestClient, sessionmaker[Session], EventType],
) -> None:
    client, testing_session, _ = context
    body = _payload()
    body["attendee"] = {"name": "   ", "email": "guest@example.com", "timeZone": "UTC"}

    response = client.post("/bookings", json=body)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"
    with testing_session() as db:
        assert db.scalars(select(Booking)).all() == []


def test_invalid_attendee_email_is_rejected(
    context: tuple[TestClient, sessionmaker[Session], EventType],
) -> None:
    client, _, _ = context
    body = _payload()
    body["attendee"] = {"name": "Guest", "email": "not-an-email", "timeZone": "UTC"}

    response = client.post("/bookings", json=body)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


def test_attendee_name_is_trimmed(
    context: tuple[TestClient, sessionmaker[Session], EventType],
) -> None:
    client, _, _ = context
    body = _payload()
    body["attendee"] = {"name": "  Ada Lovelace  ", "email": "ada@example.com", "timeZone": "UTC"}

    response = client.post("/bookings", json=body)

    assert response.status_code == 201
    assert response.json()["data"]["attendee"]["name"] == "Ada Lovelace"


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


def _booking(event_type: EventType, uid: str, status: str, start: datetime, suffix: str) -> Booking:
    return Booking(
        uid=uid,
        event_type_id=event_type.id,
        owner_id=event_type.owner_id,
        title=event_type.title,
        description=None,
        status=status,
        start=start,
        end=start + timedelta(minutes=30),
        duration_minutes=30,
        attendee_name="Attendee",
        attendee_email=f"attendee-{suffix}@example.com",
        attendee_time_zone="UTC",
        attendee_token=f"token_{uid}",
    )
