from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from tests.factories import create_event_type, create_schedule, create_share_link, create_user

SHARE_TOKEN = "hidden-share-token-1234"


@pytest.fixture()
def page_client(client: TestClient, session_factory: sessionmaker[Session]) -> TestClient:
    with session_factory() as db:
        user = create_user(db)
        schedule = create_schedule(db, user)
        create_event_type(db, user, schedule, title="Discovery call", slug="discovery-call")
        create_event_type(db, user, schedule, title="Strategy", slug="strategy")
        secret = create_event_type(db, user, schedule, title="Secret call", slug="secret-call", hidden=True)
        create_share_link(db, secret, user, token=SHARE_TOKEN)
    return client


def test_public_user_page_lists_visible_event_types(page_client: TestClient) -> None:
    response = page_client.get("/public/users/hostuser")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["user"]["username"] == "hostuser"
    slugs = {event_type["slug"] for event_type in data["eventTypes"]}
    assert slugs == {"discovery-call", "strategy"}


def test_public_user_page_excludes_hidden_event_types(page_client: TestClient) -> None:
    response = page_client.get("/public/users/hostuser")

    slugs = [event_type["slug"] for event_type in response.json()["data"]["eventTypes"]]
    assert "secret-call" not in slugs


def test_hidden_event_type_still_reachable_via_share_link(page_client: TestClient) -> None:
    listed = page_client.get("/public/users/hostuser")
    assert "secret-call" not in [et["slug"] for et in listed.json()["data"]["eventTypes"]]

    shared = page_client.get(f"/public/users/hostuser/event-types/secret-call?shareToken={SHARE_TOKEN}")
    assert shared.status_code == 200
    assert shared.json()["data"]["slug"] == "secret-call"


def test_public_user_page_unknown_user_returns_404(page_client: TestClient) -> None:
    response = page_client.get("/public/users/nobody")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
