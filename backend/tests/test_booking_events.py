from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.application.events import BookingEvent, LoggingBookingNotifier, set_booking_notifier
from app.core.security import create_access_token
from app.db.models import Base, EventType, Schedule, User
from app.db.session import get_db
from app.main import app
from app.services.calendar import booking_url, dumps_json, prepare_availability


class RecordingNotifier:
    def __init__(self) -> None:
        self.events: list[BookingEvent] = []

    def notify(self, event: BookingEvent) -> None:
        self.events.append(event)

    def types(self) -> list[str]:
        return [event.type for event in self.events]


@pytest.fixture()
def context() -> Iterator[tuple[TestClient, str, RecordingNotifier]]:
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

    recorder = RecordingNotifier()
    set_booking_notifier(recorder)
    app.dependency_overrides[get_db] = override_get_db
    with testing_session() as db:
        user = _seed(db)
        token = create_access_token(user.id)
    with TestClient(app) as test_client:
        yield test_client, token, recorder
    app.dependency_overrides.pop(get_db, None)
    set_booking_notifier(LoggingBookingNotifier())
    Base.metadata.drop_all(engine)


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create(client: TestClient, idempotency_key: str | None = None) -> dict[str, object]:
    body: dict[str, object] = {
        "username": "hostuser",
        "eventTypeSlug": "discovery-call",
        "start": "2099-01-05T09:00:00Z",
        "durationMinutes": 30,
        "attendee": {"name": "Guest", "email": "guest@example.com", "timeZone": "UTC"},
    }
    if idempotency_key is not None:
        body["idempotencyKey"] = idempotency_key
    response = client.post("/bookings", json=body)
    assert response.status_code == 201
    return response.json()["data"]


def test_create_emits_created_event(context: tuple[TestClient, str, RecordingNotifier]) -> None:
    client, _, recorder = context

    data = _create(client)

    assert recorder.types() == ["created"]
    event = recorder.events[0]
    assert event.booking_uid == data["uid"]
    assert event.host_username == "hostuser"
    assert event.attendee_email == "guest@example.com"
    assert event.status == "pending_host"


def test_idempotent_create_emits_created_once(context: tuple[TestClient, str, RecordingNotifier]) -> None:
    client, _, recorder = context

    _create(client, idempotency_key="repeat-key-1")
    _create(client, idempotency_key="repeat-key-1")

    assert recorder.types() == ["created"]


def test_confirm_emits_confirmed_event(context: tuple[TestClient, str, RecordingNotifier]) -> None:
    client, token, recorder = context
    data = _create(client)

    response = client.post(f"/bookings/{data['uid']}/confirm", headers=_auth(token))
    assert response.status_code == 200

    assert recorder.types() == ["created", "confirmed"]
    assert recorder.events[-1].status == "confirmed"


def test_decline_emits_declined_event(context: tuple[TestClient, str, RecordingNotifier]) -> None:
    client, token, recorder = context
    data = _create(client)

    response = client.post(f"/bookings/{data['uid']}/decline", headers=_auth(token), json={"reason": "busy"})
    assert response.status_code == 200

    declined = [event for event in recorder.events if event.type == "declined"]
    assert len(declined) == 1
    assert declined[0].reason == "busy"


def test_host_cancel_emits_cancelled(context: tuple[TestClient, str, RecordingNotifier]) -> None:
    client, token, recorder = context
    data = _create(client)

    response = client.post(f"/bookings/{data['uid']}/cancel", headers=_auth(token), json={"reason": "host cancel"})
    assert response.status_code == 200

    cancelled = [event for event in recorder.events if event.type == "cancelled"]
    assert len(cancelled) == 1
    assert cancelled[0].reason == "host cancel"


def test_attendee_cancel_emits_once(context: tuple[TestClient, str, RecordingNotifier]) -> None:
    client, _, recorder = context
    data = _create(client)
    token = data["manageToken"]

    first = client.post(f"/public/bookings/{data['uid']}/cancel?token={token}", json={"reason": "cannot attend"})
    second = client.post(f"/public/bookings/{data['uid']}/cancel?token={token}", json={"reason": "again"})

    assert first.status_code == 200
    assert second.status_code == 409
    cancelled = [event for event in recorder.events if event.type == "cancelled"]
    assert len(cancelled) == 1


def _seed(db: Session) -> User:
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
        confirmation_policy_type="host",
        block_slot_before_confirmation=False,
        hidden=False,
        booking_url=booking_url(user.username, "discovery-call"),
    )
    db.add(event_type)
    db.commit()
    return user
