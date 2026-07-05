from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token
from app.db.models import Base, Booking, EventType, Schedule, User
from app.db.session import get_db
from app.main import app
from app.services.calendar import booking_url, dumps_json, prepare_availability


@pytest.fixture()
def client_with_owner() -> Iterator[tuple[TestClient, sessionmaker[Session], str, EventType]]:
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
        user, event_type = _seed_owner(db)
        token = create_access_token(user.id)
    with TestClient(app) as test_client:
        yield test_client, testing_session, token, event_type
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(engine)


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_create_event_type(client_with_owner: tuple[TestClient, sessionmaker[Session], str, EventType]) -> None:
    client, _, token, _ = client_with_owner

    response = client.post(
        "/event-types",
        headers=_auth(token),
        json={"title": "Intro", "slug": "intro", "durationMinutes": 45, "description": "Quick chat"},
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["slug"] == "intro"
    assert data["durationMinutes"] == 45


def test_create_event_type_duplicate_slug_conflicts(
    client_with_owner: tuple[TestClient, sessionmaker[Session], str, EventType],
) -> None:
    client, _, token, event_type = client_with_owner

    response = client.post(
        "/event-types",
        headers=_auth(token),
        json={"title": "Dup", "slug": event_type.slug, "durationMinutes": 30},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_update_event_type_duration(
    client_with_owner: tuple[TestClient, sessionmaker[Session], str, EventType],
) -> None:
    client, _, token, event_type = client_with_owner

    response = client.patch(
        f"/event-types/{event_type.id}",
        headers=_auth(token),
        json={"durationMinutes": 90},
    )

    assert response.status_code == 200
    assert response.json()["data"]["durationMinutes"] == 90


def test_delete_event_type_without_bookings(
    client_with_owner: tuple[TestClient, sessionmaker[Session], str, EventType],
) -> None:
    client, testing_session, token, event_type = client_with_owner

    response = client.delete(f"/event-types/{event_type.id}", headers=_auth(token))

    assert response.status_code == 204
    with testing_session() as db:
        assert db.get(EventType, event_type.id) is None


def test_delete_event_type_with_bookings_is_blocked(
    client_with_owner: tuple[TestClient, sessionmaker[Session], str, EventType],
) -> None:
    client, testing_session, token, event_type = client_with_owner
    with testing_session() as db:
        _add_booking(db, event_type)

    response = client.delete(f"/event-types/{event_type.id}", headers=_auth(token))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"
    with testing_session() as db:
        assert db.get(EventType, event_type.id) is not None
        assert db.scalars(select(Booking)).all() != []


def test_update_rejects_conflicting_settings(
    client_with_owner: tuple[TestClient, sessionmaker[Session], str, EventType],
) -> None:
    client, _, token, event_type = client_with_owner

    response = client.patch(
        f"/event-types/{event_type.id}",
        headers=_auth(token),
        json={"confirmationPolicy": {"type": "automatic", "blockSlotBeforeConfirmation": True}},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"


def test_slot_interval_change_affects_available_slots(
    client_with_owner: tuple[TestClient, sessionmaker[Session], str, EventType],
) -> None:
    client, _, token, event_type = client_with_owner
    params = {
        "username": "hostuser",
        "eventTypeSlug": "discovery-call",
        "start": "2099-01-05",
        "end": "2099-01-05",
        "timeZone": "UTC",
    }

    before = client.get("/public/slots", params={**params, "durationMinutes": 60})
    assert before.status_code == 200
    before_count = len(before.json()["data"]["days"][0]["slots"])

    patch = client.patch(
        f"/event-types/{event_type.id}",
        headers=_auth(token),
        json={"slotIntervalMinutes": 30},
    )
    assert patch.status_code == 200

    after = client.get("/public/slots", params={**params, "durationMinutes": 60})
    after_count = len(after.json()["data"]["days"][0]["slots"])
    assert after_count > before_count


def _seed_owner(db: Session) -> tuple[User, EventType]:
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
        duration_minutes=60,
        slot_interval_minutes=60,
        minimum_booking_notice_minutes=None,
        before_event_buffer_minutes=None,
        after_event_buffer_minutes=None,
        booking_window_json=None,
        confirmation_policy_type="automatic",
        block_slot_before_confirmation=False,
        hidden=False,
        booking_url=booking_url(user.username, "discovery-call"),
    )
    db.add(event_type)
    db.commit()
    db.refresh(event_type)
    return user, event_type


def _add_booking(db: Session, event_type: EventType) -> None:
    start = datetime(2099, 1, 5, 9, tzinfo=timezone.utc)
    db.add(
        Booking(
            uid="booking_et_crud",
            event_type_id=event_type.id,
            owner_id=event_type.owner_id,
            title=event_type.title,
            description=None,
            status="confirmed",
            start=start,
            end=start + timedelta(minutes=60),
            duration_minutes=60,
            attendee_name="Attendee",
            attendee_email="attendee@example.com",
            attendee_time_zone="UTC",
            attendee_token="token_et_crud",
        )
    )
    db.commit()
