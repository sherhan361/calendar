from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.application import bookings as booking_use_cases
from app.db.models import Booking, EventType
from tests.factories import create_booking

SLOT_START = "2099-01-05T09:00:00Z"


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


def test_create_booking_succeeds(client: TestClient, public_event_type: EventType) -> None:
    response = client.post("/bookings", json=_payload())

    assert response.status_code == 201
    assert response.json()["data"]["status"] == "confirmed"


def test_duplicate_submit_with_same_key_returns_same_booking(
    client: TestClient,
    session_factory: sessionmaker[Session],
    public_event_type: EventType,
) -> None:
    first = client.post("/bookings", json=_payload("retry-key-123"))
    second = client.post("/bookings", json=_payload("retry-key-123"))

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["data"]["uid"] == second.json()["data"]["uid"]

    with session_factory() as db:
        bookings = db.scalars(select(Booking)).all()
    assert len(bookings) == 1


def test_second_booking_for_taken_slot_conflicts(
    client: TestClient,
    session_factory: sessionmaker[Session],
    public_event_type: EventType,
) -> None:
    first = client.post("/bookings", json=_payload("slot-key-a", email="a@example.com"))
    second = client.post("/bookings", json=_payload("slot-key-b", email="b@example.com"))

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "conflict"

    with session_factory() as db:
        active = db.scalars(
            select(Booking).where(Booking.status.in_(["pending_host", "pending_attendee", "confirmed"]))
        ).all()
    assert len(active) == 1


def test_race_on_same_slot_returns_conflict_via_integrity_error(
    client: TestClient,
    session_factory: sessionmaker[Session],
    public_event_type: EventType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    start = datetime(2099, 1, 5, 9, tzinfo=timezone.utc)

    with session_factory() as db:
        create_booking(db, public_event_type, uid="booking_winner", status="confirmed", start=start)

    monkeypatch.setattr(booking_use_cases, "event_type_slot_is_available", lambda *args, **kwargs: True)
    response = client.post("/bookings", json=_payload("late-key-123", email="late@example.com"))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"

    with session_factory() as db:
        active = db.scalars(
            select(Booking).where(Booking.status.in_(["pending_host", "pending_attendee", "confirmed"]))
        ).all()
    assert len(active) == 1


def test_active_slot_unique_index_blocks_concurrent_duplicate(
    session_factory: sessionmaker[Session],
    public_event_type: EventType,
) -> None:
    start = datetime(2099, 1, 5, 9, tzinfo=timezone.utc)

    with session_factory() as db:
        create_booking(db, public_event_type, uid="booking_one", status="confirmed", start=start)

    with session_factory() as db:
        create_booking(db, public_event_type, uid="booking_two", status="confirmed", start=start, commit=False)
        with pytest.raises(IntegrityError):
            db.commit()


def test_cancelled_slot_can_be_rebooked(
    session_factory: sessionmaker[Session],
    public_event_type: EventType,
) -> None:
    start = datetime(2099, 1, 5, 9, tzinfo=timezone.utc)

    with session_factory() as db:
        create_booking(db, public_event_type, uid="booking_cancelled", status="cancelled", start=start)
        create_booking(db, public_event_type, uid="booking_new", status="confirmed", start=start)
        active = db.scalars(select(Booking).where(Booking.status == "confirmed")).all()
    assert len(active) == 1


def test_success_response_exposes_status_title_and_time(
    client: TestClient,
    public_event_type: EventType,
) -> None:
    response = client.post("/bookings", json=_payload())

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["title"] == "Discovery call"
    assert data["status"] == "confirmed"
    assert data["start"].startswith("2099-01-05T09:00:00")
    assert data["durationMinutes"] == 30


def test_blank_attendee_name_is_rejected(
    client: TestClient,
    session_factory: sessionmaker[Session],
    public_event_type: EventType,
) -> None:
    body = _payload()
    body["attendee"] = {"name": "   ", "email": "guest@example.com", "timeZone": "UTC"}

    response = client.post("/bookings", json=body)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"
    with session_factory() as db:
        assert db.scalars(select(Booking)).all() == []


def test_invalid_attendee_email_is_rejected(
    client: TestClient,
    public_event_type: EventType,
) -> None:
    body = _payload()
    body["attendee"] = {"name": "Guest", "email": "not-an-email", "timeZone": "UTC"}

    response = client.post("/bookings", json=body)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


def test_attendee_name_is_trimmed(
    client: TestClient,
    public_event_type: EventType,
) -> None:
    body = _payload()
    body["attendee"] = {"name": "  Ada Lovelace  ", "email": "ada@example.com", "timeZone": "UTC"}

    response = client.post("/bookings", json=body)

    assert response.status_code == 201
    assert response.json()["data"]["attendee"]["name"] == "Ada Lovelace"
