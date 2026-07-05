from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from tests.factories import create_booking, create_public_event_type

ATTENDEE_TOKEN = "attendee-token-abc"
BOOKING_UID = "booking_public_cancel"


@pytest.fixture()
def cancel_client(client: TestClient, session_factory: sessionmaker[Session]) -> TestClient:
    with session_factory() as db:
        event_type = create_public_event_type(db)
        create_booking(
            db,
            event_type,
            uid=BOOKING_UID,
            status="confirmed",
            start=datetime(2099, 1, 5, 9, tzinfo=timezone.utc),
            attendee_token=ATTENDEE_TOKEN,
        )
    return client


def _cancel(client: TestClient, token: str, reason: str | None = None) -> object:
    body = {"reason": reason} if reason is not None else {}
    return client.post(f"/public/bookings/{BOOKING_UID}/cancel?token={token}", json=body)


def test_public_cancel_marks_booking_cancelled_with_reason(cancel_client: TestClient) -> None:
    response = _cancel(cancel_client, ATTENDEE_TOKEN, reason="Не смогу прийти")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "cancelled"
    assert data["cancellationReason"] == "Не смогу прийти"


def test_public_cancel_without_reason_leaves_reason_empty(cancel_client: TestClient) -> None:
    response = _cancel(cancel_client, ATTENDEE_TOKEN)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "cancelled"
    assert "cancellationReason" not in data


def test_public_cancel_twice_returns_conflict(cancel_client: TestClient) -> None:
    first = _cancel(cancel_client, ATTENDEE_TOKEN, reason="first")
    second = _cancel(cancel_client, ATTENDEE_TOKEN, reason="second")

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "conflict"


def test_public_cancel_with_invalid_token_is_rejected(cancel_client: TestClient) -> None:
    response = _cancel(cancel_client, "wrong-token", reason="nope")

    assert response.status_code == 410
    assert response.json()["error"]["code"] == "link_expired"


def test_public_cancel_unknown_booking_returns_not_found(cancel_client: TestClient) -> None:
    response = cancel_client.post(f"/public/bookings/booking_missing/cancel?token={ATTENDEE_TOKEN}", json={})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
