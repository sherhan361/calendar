from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.main import app
from app.services.rate_limit import SlidingWindowRateLimiter, get_booking_rate_limiter
from tests.factories import create_public_event_type


@pytest.fixture()
def client_with_limit(
    client: TestClient, session_factory: sessionmaker[Session]
) -> Iterator[tuple[TestClient, dict[str, float]]]:
    with session_factory() as db:
        create_public_event_type(db)

    clock = {"t": 0.0}
    limiter = SlidingWindowRateLimiter(max_events=1, window_seconds=60.0, clock=lambda: clock["t"])
    app.dependency_overrides[get_booking_rate_limiter] = lambda: limiter
    yield client, clock
    app.dependency_overrides.pop(get_booking_rate_limiter, None)


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
