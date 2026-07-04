from __future__ import annotations

import json
import secrets
from uuid import uuid4

from app.db.models import ShareLink
from app.domain.calendar import ensure_utc, parse_local_date, utc_now


def default_availability() -> list[dict[str, object]]:
    return [
        {
            "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
            "startTime": "09:00",
            "endTime": "12:00",
        },
        {
            "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
            "startTime": "13:00",
            "endTime": "18:00",
        },
    ]


def prepare_availability(rules: list[object]) -> list[dict[str, object]]:
    prepared = []
    for rule in rules:
        payload = _model_or_dict(rule)
        prepared.append(
            {
                "id": payload.get("id") or str(uuid4()),
                "days": [str(day) for day in payload.get("days", [])],
                "startTime": payload["startTime"],
                "endTime": payload["endTime"],
            }
        )
    return prepared


def prepare_overrides(overrides: list[object] | None) -> list[dict[str, object]]:
    prepared = []
    for override in overrides or []:
        payload = _model_or_dict(override)
        prepared.append(
            {
                "id": payload.get("id") or str(uuid4()),
                "date": payload["date"],
                "startTime": payload.get("startTime"),
                "endTime": payload.get("endTime"),
                "unavailable": bool(payload.get("unavailable", False)),
            }
        )
    return prepared


def random_token() -> str:
    return secrets.token_urlsafe(24)


def booking_url(username: str, slug: str, token: str | None = None) -> str:
    url = f"/#/book/{username}/{slug}"
    if token:
        return f"{url}?shareToken={token}"
    return url


def is_share_link_expired(link: ShareLink) -> bool:
    if link.expires_at and ensure_utc(link.expires_at) < utc_now():
        return True
    if link.max_usage_count is not None and link.usage_count >= link.max_usage_count:
        return True
    return False


def load_json(value: str | None, fallback: object) -> object:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def dumps_json(value: object) -> str:
    return json.dumps(value, separators=(",", ":"))


def _model_or_dict(value: object) -> dict[str, object]:
    if hasattr(value, "model_dump"):
        return value.model_dump(exclude_none=True)
    return dict(value)  # type: ignore[arg-type]
