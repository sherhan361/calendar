from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import create_access_token
from app.db.models import Schedule
from tests.factories import create_event_type, create_schedule, create_user
from tests.support import AuthenticatedClient

MONDAY = "2099-01-05"
TUESDAY = "2099-01-06"


@pytest.fixture()
def owner(
    client: TestClient, session_factory: sessionmaker[Session]
) -> tuple[AuthenticatedClient, Schedule]:
    with session_factory() as db:
        user = create_user(db)
        schedule = create_schedule(db, user)
        create_event_type(db, user, schedule)
        db.commit()
        db.refresh(schedule)
        token = create_access_token(schedule.owner_id)
    return AuthenticatedClient(client, token), schedule


def _slots(client: TestClient, day: str) -> list[dict[str, object]]:
    response = client.get(
        "/public/slots",
        params={
            "username": "hostuser",
            "eventTypeSlug": "discovery-call",
            "start": day,
            "end": day,
            "timeZone": "UTC",
            "durationMinutes": 30,
        },
    )
    assert response.status_code == 200
    return response.json()["data"]["days"][0]["slots"]


def test_weekly_availability_change_reflected_in_slots(
    owner: tuple[AuthenticatedClient, Schedule],
) -> None:
    auth, schedule = owner
    assert _slots(auth.client, MONDAY) != []
    assert _slots(auth.client, TUESDAY) == []

    patch = auth.client.patch(
        f"/schedules/{schedule.id}",
        headers=auth.headers,
        json={"availability": [{"days": ["tuesday"], "startTime": "09:00", "endTime": "17:00"}]},
    )
    assert patch.status_code == 200

    assert _slots(auth.client, MONDAY) == []
    assert _slots(auth.client, TUESDAY) != []


def test_override_away_day_removes_slots(owner: tuple[AuthenticatedClient, Schedule]) -> None:
    auth, schedule = owner
    assert _slots(auth.client, MONDAY) != []

    patch = auth.client.patch(
        f"/schedules/{schedule.id}",
        headers=auth.headers,
        json={"overrides": [{"date": MONDAY, "unavailable": True}]},
    )
    assert patch.status_code == 200

    assert _slots(auth.client, MONDAY) == []


def test_available_override_adds_slots_on_off_day(
    owner: tuple[AuthenticatedClient, Schedule],
) -> None:
    auth, schedule = owner
    saturday = "2099-01-10"
    assert _slots(auth.client, saturday) == []

    patch = auth.client.patch(
        f"/schedules/{schedule.id}",
        headers=auth.headers,
        json={"overrides": [{"date": saturday, "unavailable": False, "startTime": "09:00", "endTime": "11:00"}]},
    )
    assert patch.status_code == 200

    assert _slots(auth.client, saturday) != []


def test_timezone_change_shifts_slots(owner: tuple[AuthenticatedClient, Schedule]) -> None:
    auth, schedule = owner
    before = _slots(auth.client, MONDAY)
    assert "T09:00" in str(before[0]["start"])

    patch = auth.client.patch(
        f"/schedules/{schedule.id}",
        headers=auth.headers,
        json={"timeZone": "Europe/Moscow"},
    )
    assert patch.status_code == 200

    after = _slots(auth.client, MONDAY)
    assert "T06:00" in str(after[0]["start"])


def test_create_schedule_as_default_updates_default(
    owner: tuple[AuthenticatedClient, Schedule],
) -> None:
    auth, _ = owner

    created = auth.client.post(
        "/schedules",
        headers=auth.headers,
        json={
            "name": "Evenings",
            "timeZone": "UTC",
            "isDefault": True,
            "availability": [{"days": ["wednesday"], "startTime": "18:00", "endTime": "20:00"}],
        },
    )
    assert created.status_code == 201
    new_id = created.json()["data"]["id"]

    default = auth.client.get("/schedules/default", headers=auth.headers)
    assert default.status_code == 200
    assert default.json()["data"]["id"] == new_id
