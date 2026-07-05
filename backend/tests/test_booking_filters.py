from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import create_access_token
from tests.factories import create_booking, create_event_type, create_schedule, create_user
from tests.support import AuthenticatedClient


@pytest.fixture()
def owner_with_bookings(
    client: TestClient, session_factory: sessionmaker[Session]
) -> AuthenticatedClient:
    with session_factory() as db:
        owner = create_user(db)
        other_owner = create_user(db, email="other@example.com", username="otherhost", name="Other Host")
        event_type = create_event_type(db, owner, create_schedule(db, owner))
        other_event_type = create_event_type(
            db,
            other_owner,
            create_schedule(db, other_owner),
            title="Other call",
            slug="other-call",
        )

        create_booking(
            db, event_type, uid="booking_confirmed", status="confirmed",
            start=datetime(2026, 7, 5, 9, tzinfo=timezone.utc), commit=False,
        )
        create_booking(
            db, event_type, uid="booking_pending", status="pending_host",
            start=datetime(2026, 7, 6, 9, tzinfo=timezone.utc), commit=False,
        )
        create_booking(
            db, event_type, uid="booking_cancelled", status="cancelled",
            start=datetime(2026, 7, 7, 9, tzinfo=timezone.utc), commit=False,
        )
        create_booking(
            db, other_event_type, uid="booking_other_owner", status="confirmed",
            start=datetime(2026, 7, 6, 10, tzinfo=timezone.utc), commit=False,
        )
        db.commit()
        token = create_access_token(owner.id)
    return AuthenticatedClient(client, token)


def test_list_bookings_filters_by_status(owner_with_bookings: AuthenticatedClient) -> None:
    auth = owner_with_bookings

    response = auth.client.get("/bookings?status=pending_host", headers=auth.headers)

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert [item["uid"] for item in items] == ["booking_pending"]


def test_list_bookings_returns_all_owner_bookings_in_start_order(
    owner_with_bookings: AuthenticatedClient,
) -> None:
    auth = owner_with_bookings

    response = auth.client.get("/bookings", headers=auth.headers)

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert [item["uid"] for item in items] == ["booking_confirmed", "booking_pending", "booking_cancelled"]


def test_list_bookings_filters_by_inclusive_date_window(
    owner_with_bookings: AuthenticatedClient,
) -> None:
    auth = owner_with_bookings

    response = auth.client.get("/bookings?from=2026-07-06&to=2026-07-06", headers=auth.headers)

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert [item["uid"] for item in items] == ["booking_pending"]


def test_list_bookings_filters_by_from_date_only(
    owner_with_bookings: AuthenticatedClient,
) -> None:
    auth = owner_with_bookings

    response = auth.client.get("/bookings?from=2026-07-06", headers=auth.headers)

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert [item["uid"] for item in items] == ["booking_pending", "booking_cancelled"]


def test_list_bookings_filters_by_to_date_only(
    owner_with_bookings: AuthenticatedClient,
) -> None:
    auth = owner_with_bookings

    response = auth.client.get("/bookings?to=2026-07-06", headers=auth.headers)

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert [item["uid"] for item in items] == ["booking_confirmed", "booking_pending"]


def test_list_bookings_empty_date_window_returns_empty_list(
    owner_with_bookings: AuthenticatedClient,
) -> None:
    auth = owner_with_bookings

    response = auth.client.get("/bookings?from=2026-07-08&to=2026-07-08", headers=auth.headers)

    assert response.status_code == 200
    assert response.json()["data"]["items"] == []


def test_list_bookings_rejects_invalid_date_filter(
    owner_with_bookings: AuthenticatedClient,
) -> None:
    auth = owner_with_bookings

    response = auth.client.get("/bookings?from=2026-13-01", headers=auth.headers)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"
