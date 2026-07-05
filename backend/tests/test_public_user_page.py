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


SHARE_TOKEN = "hidden-share-token-1234"


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
        _seed(db)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(engine)


def test_public_user_page_lists_visible_event_types(client: TestClient) -> None:
    response = client.get("/public/users/hostuser")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["user"]["username"] == "hostuser"
    slugs = {event_type["slug"] for event_type in data["eventTypes"]}
    assert slugs == {"discovery-call", "strategy"}


def test_public_user_page_excludes_hidden_event_types(client: TestClient) -> None:
    response = client.get("/public/users/hostuser")

    slugs = [event_type["slug"] for event_type in response.json()["data"]["eventTypes"]]
    assert "secret-call" not in slugs


def test_hidden_event_type_still_reachable_via_share_link(client: TestClient) -> None:
    listed = client.get("/public/users/hostuser")
    assert "secret-call" not in [et["slug"] for et in listed.json()["data"]["eventTypes"]]

    shared = client.get(f"/public/users/hostuser/event-types/secret-call?shareToken={SHARE_TOKEN}")
    assert shared.status_code == 200
    assert shared.json()["data"]["slug"] == "secret-call"


def test_public_user_page_unknown_user_returns_404(client: TestClient) -> None:
    response = client.get("/public/users/nobody")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def _seed(db: Session) -> None:
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

    db.add(_event_type(user, schedule, "Discovery call", "discovery-call", hidden=False))
    db.add(_event_type(user, schedule, "Strategy", "strategy", hidden=False))
    secret = _event_type(user, schedule, "Secret call", "secret-call", hidden=True)
    db.add(secret)
    db.flush()

    db.add(
        ShareLink(
            event_type_id=secret.id,
            token=SHARE_TOKEN,
            booking_url=booking_url(user.username, "secret-call", SHARE_TOKEN),
            recipient_email=None,
            expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
            max_usage_count=5,
            usage_count=0,
        )
    )
    db.commit()


def _event_type(user: User, schedule: Schedule, title: str, slug: str, hidden: bool) -> EventType:
    return EventType(
        owner_id=user.id,
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
        hidden=hidden,
        booking_url=booking_url(user.username, slug),
    )
