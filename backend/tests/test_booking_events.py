from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.application.events import BookingEvent, LoggingBookingNotifier, set_booking_notifier
from app.core.security import create_access_token
from tests.factories import create_event_type, create_schedule, create_user
from tests.support import AuthenticatedClient


class RecordingNotifier:
    def __init__(self) -> None:
        self.events: list[BookingEvent] = []

    def notify(self, event: BookingEvent) -> None:
        self.events.append(event)

    def types(self) -> list[str]:
        return [event.type for event in self.events]


@pytest.fixture()
def recording_notifier() -> Iterator[RecordingNotifier]:
    recorder = RecordingNotifier()
    set_booking_notifier(recorder)
    yield recorder
    set_booking_notifier(LoggingBookingNotifier())


@pytest.fixture()
def host_auth(client: TestClient, session_factory: sessionmaker[Session]) -> AuthenticatedClient:
    with session_factory() as db:
        user = create_user(db)
        schedule = create_schedule(db, user)
        create_event_type(db, user, schedule, confirmation_policy_type="host")
        db.commit()
        token = create_access_token(user.id)
    return AuthenticatedClient(client, token)


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


def test_create_emits_created_event(
    host_auth: AuthenticatedClient, recording_notifier: RecordingNotifier
) -> None:
    data = _create(host_auth.client)

    assert recording_notifier.types() == ["created"]
    event = recording_notifier.events[0]
    assert event.booking_uid == data["uid"]
    assert event.host_username == "hostuser"
    assert event.attendee_email == "guest@example.com"
    assert event.status == "pending_host"


def test_idempotent_create_emits_created_once(
    host_auth: AuthenticatedClient, recording_notifier: RecordingNotifier
) -> None:
    _create(host_auth.client, idempotency_key="repeat-key-1")
    _create(host_auth.client, idempotency_key="repeat-key-1")

    assert recording_notifier.types() == ["created"]


def test_confirm_emits_confirmed_event(
    host_auth: AuthenticatedClient, recording_notifier: RecordingNotifier
) -> None:
    data = _create(host_auth.client)

    response = host_auth.client.post(f"/bookings/{data['uid']}/confirm", headers=host_auth.headers)
    assert response.status_code == 200

    assert recording_notifier.types() == ["created", "confirmed"]
    assert recording_notifier.events[-1].status == "confirmed"


def test_decline_emits_declined_event(
    host_auth: AuthenticatedClient, recording_notifier: RecordingNotifier
) -> None:
    data = _create(host_auth.client)

    response = host_auth.client.post(
        f"/bookings/{data['uid']}/decline", headers=host_auth.headers, json={"reason": "busy"}
    )
    assert response.status_code == 200

    declined = [event for event in recording_notifier.events if event.type == "declined"]
    assert len(declined) == 1
    assert declined[0].reason == "busy"


def test_host_cancel_emits_cancelled(
    host_auth: AuthenticatedClient, recording_notifier: RecordingNotifier
) -> None:
    data = _create(host_auth.client)

    response = host_auth.client.post(
        f"/bookings/{data['uid']}/cancel", headers=host_auth.headers, json={"reason": "host cancel"}
    )
    assert response.status_code == 200

    cancelled = [event for event in recording_notifier.events if event.type == "cancelled"]
    assert len(cancelled) == 1
    assert cancelled[0].reason == "host cancel"


def test_attendee_cancel_emits_once(
    host_auth: AuthenticatedClient, recording_notifier: RecordingNotifier
) -> None:
    data = _create(host_auth.client)
    token = data["manageToken"]

    first = host_auth.client.post(
        f"/public/bookings/{data['uid']}/cancel?token={token}", json={"reason": "cannot attend"}
    )
    second = host_auth.client.post(
        f"/public/bookings/{data['uid']}/cancel?token={token}", json={"reason": "again"}
    )

    assert first.status_code == 200
    assert second.status_code == 409
    cancelled = [event for event in recording_notifier.events if event.type == "cancelled"]
    assert len(cancelled) == 1
