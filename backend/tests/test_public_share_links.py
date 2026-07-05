from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base, EventType, Schedule, ShareLink, User
from app.db.session import get_db
from app.main import app
from app.services.calendar import booking_url, dumps_json, prepare_availability


SHARE_TOKEN = "hidden-share-token-123"


@pytest.fixture()
def client() -> Iterator[TestClient]:
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
        _seed_hidden_event_type_with_share_link(db)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(engine)


def test_hidden_event_type_stays_private_without_share_token(client: TestClient) -> None:
    event_type_response = client.get("/public/users/hostuser/event-types/secret-call")
    slots_response = client.get(
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
    booking_response = client.post(
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


def test_share_link_grants_access_to_hidden_event_type(client: TestClient) -> None:
    event_type_response = client.get(
        f"/public/users/hostuser/event-types/secret-call?shareToken={SHARE_TOKEN}"
    )
    slots_response = client.get(
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
    booking_response = client.post(
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


def _seed_hidden_event_type_with_share_link(db: Session) -> None:
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
            prepare_availability([{"days": ["monday"], "startTime": "09:00", "endTime": "10:00"}])
        ),
        overrides_json="[]",
    )
    db.add(schedule)
    db.flush()
    user.default_schedule_id = schedule.id

    event_type = EventType(
        owner_id=user.id,
        schedule_id=schedule.id,
        title="Secret call",
        slug="secret-call",
        description=None,
        duration_minutes=30,
        slot_interval_minutes=30,
        minimum_booking_notice_minutes=None,
        before_event_buffer_minutes=None,
        after_event_buffer_minutes=None,
        booking_window_json=None,
        confirmation_policy_type="automatic",
        block_slot_before_confirmation=False,
        hidden=True,
        booking_url=booking_url(user.username, "secret-call"),
    )
    db.add(event_type)
    db.flush()

    db.add(
        ShareLink(
            event_type_id=event_type.id,
            token=SHARE_TOKEN,
            booking_url=booking_url(user.username, event_type.slug, SHARE_TOKEN),
            recipient_email=None,
            expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
            max_usage_count=5,
            usage_count=0,
        )
    )
    db.commit()
