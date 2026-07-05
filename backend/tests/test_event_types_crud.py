from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import create_access_token
from app.db.models import Booking, EventType
from tests.factories import create_booking, create_event_type, create_schedule, create_user
from tests.support import AuthenticatedClient


@pytest.fixture()
def owner_event_type(
    client: TestClient, session_factory: sessionmaker[Session]
) -> tuple[AuthenticatedClient, EventType]:
    with session_factory() as db:
        user = create_user(db)
        schedule = create_schedule(db, user)
        event_type = create_event_type(
            db, user, schedule, duration_minutes=60, slot_interval_minutes=60
        )
        db.commit()
        db.refresh(event_type)
        token = create_access_token(user.id)
    return AuthenticatedClient(client, token), event_type


def test_create_event_type(owner_event_type: tuple[AuthenticatedClient, EventType]) -> None:
    auth, _ = owner_event_type

    response = auth.client.post(
        "/event-types",
        headers=auth.headers,
        json={"title": "Intro", "slug": "intro", "durationMinutes": 45, "description": "Quick chat"},
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["slug"] == "intro"
    assert data["durationMinutes"] == 45


def test_create_event_type_duplicate_slug_conflicts(
    owner_event_type: tuple[AuthenticatedClient, EventType],
) -> None:
    auth, event_type = owner_event_type

    response = auth.client.post(
        "/event-types",
        headers=auth.headers,
        json={"title": "Dup", "slug": event_type.slug, "durationMinutes": 30},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_update_event_type_duration(
    owner_event_type: tuple[AuthenticatedClient, EventType],
) -> None:
    auth, event_type = owner_event_type

    response = auth.client.patch(
        f"/event-types/{event_type.id}",
        headers=auth.headers,
        json={"durationMinutes": 90},
    )

    assert response.status_code == 200
    assert response.json()["data"]["durationMinutes"] == 90


def test_delete_event_type_without_bookings(
    owner_event_type: tuple[AuthenticatedClient, EventType],
    session_factory: sessionmaker[Session],
) -> None:
    auth, event_type = owner_event_type

    response = auth.client.delete(f"/event-types/{event_type.id}", headers=auth.headers)

    assert response.status_code == 204
    with session_factory() as db:
        assert db.get(EventType, event_type.id) is None


def test_delete_event_type_with_bookings_is_blocked(
    owner_event_type: tuple[AuthenticatedClient, EventType],
    session_factory: sessionmaker[Session],
) -> None:
    auth, event_type = owner_event_type
    with session_factory() as db:
        create_booking(
            db,
            event_type,
            uid="booking_et_crud",
            status="confirmed",
            start=datetime(2099, 1, 5, 9, tzinfo=timezone.utc),
        )

    response = auth.client.delete(f"/event-types/{event_type.id}", headers=auth.headers)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"
    with session_factory() as db:
        assert db.get(EventType, event_type.id) is not None
        assert db.scalars(select(Booking)).all() != []


def test_update_rejects_conflicting_settings(
    owner_event_type: tuple[AuthenticatedClient, EventType],
) -> None:
    auth, event_type = owner_event_type

    response = auth.client.patch(
        f"/event-types/{event_type.id}",
        headers=auth.headers,
        json={"confirmationPolicy": {"type": "automatic", "blockSlotBeforeConfirmation": True}},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


def test_slot_interval_change_affects_available_slots(
    owner_event_type: tuple[AuthenticatedClient, EventType],
) -> None:
    auth, event_type = owner_event_type
    params = {
        "username": "hostuser",
        "eventTypeSlug": "discovery-call",
        "start": "2099-01-05",
        "end": "2099-01-05",
        "timeZone": "UTC",
    }

    before = auth.client.get("/public/slots", params={**params, "durationMinutes": 60})
    assert before.status_code == 200
    before_count = len(before.json()["data"]["days"][0]["slots"])

    patch = auth.client.patch(
        f"/event-types/{event_type.id}",
        headers=auth.headers,
        json={"slotIntervalMinutes": 30},
    )
    assert patch.status_code == 200

    after = auth.client.get("/public/slots", params={**params, "durationMinutes": 60})
    after_count = len(after.json()["data"]["days"][0]["slots"])
    assert after_count > before_count
