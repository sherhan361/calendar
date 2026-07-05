from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from tests.factories import create_event_type, create_schedule, create_share_link, create_user

SHARE_TOKEN = "hidden-share-token-123"


@pytest.fixture()
def share_client(client: TestClient, session_factory: sessionmaker[Session]) -> TestClient:
    with session_factory() as db:
        user = create_user(db)
        schedule = create_schedule(
            db,
            user,
            availability=[{"days": ["monday"], "startTime": "09:00", "endTime": "10:00"}],
        )
        event_type = create_event_type(
            db, user, schedule, title="Secret call", slug="secret-call", hidden=True
        )
        create_share_link(db, event_type, user, token=SHARE_TOKEN)
    return client


def test_hidden_event_type_stays_private_without_share_token(share_client: TestClient) -> None:
    event_type_response = share_client.get("/public/users/hostuser/event-types/secret-call")
    slots_response = share_client.get(
        "/public/slots",
        params={
            "username": "hostuser",
            "eventTypeSlug": "secret-call",
            "start": "2099-01-05",
            "end": "2099-01-05",
            "timeZone": "UTC",
            "durationMinutes": 30,
        },
    )
    booking_response = share_client.post(
        "/bookings",
        json={
            "username": "hostuser",
            "eventTypeSlug": "secret-call",
            "start": "2099-01-05T09:00:00Z",
            "durationMinutes": 30,
            "attendee": {"name": "Attendee", "email": "attendee@example.com", "timeZone": "UTC"},
        },
    )

    assert event_type_response.status_code == 404
    assert slots_response.status_code == 404
    assert booking_response.status_code == 404


def test_share_link_grants_access_to_hidden_event_type(share_client: TestClient) -> None:
    event_type_response = share_client.get(
        f"/public/users/hostuser/event-types/secret-call?shareToken={SHARE_TOKEN}"
    )
    slots_response = share_client.get(
        "/public/slots",
        params={
            "username": "hostuser",
            "eventTypeSlug": "secret-call",
            "start": "2099-01-05",
            "end": "2099-01-05",
            "timeZone": "UTC",
            "durationMinutes": 30,
            "shareToken": SHARE_TOKEN,
        },
    )
    booking_response = share_client.post(
        "/bookings",
        json={
            "username": "hostuser",
            "eventTypeSlug": "secret-call",
            "shareToken": SHARE_TOKEN,
            "start": "2099-01-05T09:00:00Z",
            "durationMinutes": 30,
            "attendee": {"name": "Attendee", "email": "attendee@example.com", "timeZone": "UTC"},
        },
    )

    assert event_type_response.status_code == 200
    assert event_type_response.json()["data"]["title"] == "Secret call"

    assert slots_response.status_code == 200
    slots = slots_response.json()["data"]["days"][0]["slots"]
    assert slots
    assert slots[0]["available"] is True

    assert booking_response.status_code == 201
    assert booking_response.json()["data"]["shareToken"] == SHARE_TOKEN
