from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token
from app.db.models import Base, Booking, EventType, Schedule, User
from app.db.session import get_db
from app.main import app
from app.services.calendar import booking_url, dumps_json, prepare_availability


@pytest.fixture()
def client_with_bookings() -> Iterator[tuple[TestClient, str]]:
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
        user = _seed_bookings(db)
        token = create_access_token(user.id)

    with TestClient(app) as test_client:
        yield test_client, token

    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(engine)


def test_list_bookings_filters_by_status(client_with_bookings: tuple[TestClient, str]) -> None:
    client, token = client_with_bookings

    response = client.get("/bookings?status=pending_host", headers=_auth_headers(token))

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert [item["uid"] for item in items] == ["booking_pending"]


def test_list_bookings_returns_all_owner_bookings_in_start_order(
    client_with_bookings: tuple[TestClient, str],
) -> None:
    client, token = client_with_bookings

    response = client.get("/bookings", headers=_auth_headers(token))

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert [item["uid"] for item in items] == ["booking_confirmed", "booking_pending", "booking_cancelled"]


def test_list_bookings_filters_by_inclusive_date_window(client_with_bookings: tuple[TestClient, str]) -> None:
    client, token = client_with_bookings

    response = client.get("/bookings?from=2026-07-06&to=2026-07-06", headers=_auth_headers(token))

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert [item["uid"] for item in items] == ["booking_pending"]


def test_list_bookings_filters_by_from_date_only(client_with_bookings: tuple[TestClient, str]) -> None:
    client, token = client_with_bookings

    response = client.get("/bookings?from=2026-07-06", headers=_auth_headers(token))

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert [item["uid"] for item in items] == ["booking_pending", "booking_cancelled"]


def test_list_bookings_filters_by_to_date_only(client_with_bookings: tuple[TestClient, str]) -> None:
    client, token = client_with_bookings

    response = client.get("/bookings?to=2026-07-06", headers=_auth_headers(token))

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert [item["uid"] for item in items] == ["booking_confirmed", "booking_pending"]


def test_list_bookings_empty_date_window_returns_empty_list(client_with_bookings: tuple[TestClient, str]) -> None:
    client, token = client_with_bookings

    response = client.get("/bookings?from=2026-07-08&to=2026-07-08", headers=_auth_headers(token))

    assert response.status_code == 200
    assert response.json()["data"]["items"] == []


def test_list_bookings_rejects_invalid_date_filter(client_with_bookings: tuple[TestClient, str]) -> None:
    client, token = client_with_bookings

    response = client.get("/bookings?from=2026-13-01", headers=_auth_headers(token))

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


def _seed_bookings(db: Session) -> User:
    owner = _add_user(db, "host@example.com", "hostuser", "Host User")
    other_owner = _add_user(db, "other@example.com", "otherhost", "Other Host")
    event_type = _add_event_type(db, owner, "Discovery call", "discovery-call")
    other_event_type = _add_event_type(db, other_owner, "Other call", "other-call")

    db.add_all(
        [
            _booking(
                owner,
                event_type,
                "booking_confirmed",
                "confirmed",
                datetime(2026, 7, 5, 9, tzinfo=timezone.utc),
            ),
            _booking(
                owner,
                event_type,
                "booking_pending",
                "pending_host",
                datetime(2026, 7, 6, 9, tzinfo=timezone.utc),
            ),
            _booking(
                owner,
                event_type,
                "booking_cancelled",
                "cancelled",
                datetime(2026, 7, 7, 9, tzinfo=timezone.utc),
            ),
            _booking(
                other_owner,
                other_event_type,
                "booking_other_owner",
                "confirmed",
                datetime(2026, 7, 6, 10, tzinfo=timezone.utc),
            ),
        ]
    )
    db.commit()
    return owner


def _add_user(db: Session, email: str, username: str, name: str) -> User:
    user = User(
        email=email,
        username=username,
        name=name,
        time_zone="UTC",
        password_hash="pbkdf2_sha256$1$salt$digest",
    )
    db.add(user)
    db.flush()
    return user


def _add_event_type(db: Session, owner: User, title: str, slug: str) -> EventType:
    schedule = Schedule(
        owner_id=owner.id,
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
    owner.default_schedule_id = schedule.id

    event_type = EventType(
        owner_id=owner.id,
        schedule_id=schedule.id,
        title=title,
        slug=slug,
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
        booking_url=booking_url(owner.username, slug),
    )
    db.add(event_type)
    db.flush()
    return event_type


def _booking(owner: User, event_type: EventType, uid: str, status: str, start: datetime) -> Booking:
    return Booking(
        uid=uid,
        event_type_id=event_type.id,
        owner_id=owner.id,
        title=event_type.title,
        description=None,
        status=status,
        start=start,
        end=start + timedelta(minutes=30),
        duration_minutes=30,
        attendee_name="Attendee",
        attendee_email="attendee@example.com",
        attendee_time_zone="UTC",
        attendee_token=f"token_{uid}",
    )


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
