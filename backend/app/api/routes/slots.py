from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends

from app.api.deps import current_user
from app.api.responses import ApiException, success
from app.application.slots import DomainRuleError, build_slots_response
from app.db.models import EventType, ShareLink, User
from app.db.session import get_db
from app.services.calendar import is_share_link_expired, parse_local_date


router = APIRouter(tags=["Slots"])


@router.get("/slots")
def get_slots(
    eventTypeId: str,
    start: str,
    end: str,
    timeZone: str | None = None,
    durationMinutes: int | None = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _validate_dates(start, end)
    event_type = db.scalar(select(EventType).where(EventType.id == eventTypeId, EventType.owner_id == user.id))
    if event_type is None:
        raise ApiException(404, "not_found", "Event type not found.")
    try:
        return success(build_slots_response(event_type, start, end, timeZone, durationMinutes))
    except DomainRuleError as exc:
        raise ApiException(exc.status_code, exc.code, exc.message) from exc


@router.get("/public/slots", tags=["Public Slots"])
def get_public_slots(
    username: str,
    eventTypeSlug: str,
    start: str,
    end: str,
    timeZone: str | None = None,
    durationMinutes: int | None = None,
    shareToken: str | None = None,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    _validate_dates(start, end)
    event_type = db.scalar(
        select(EventType)
        .join(EventType.owner)
        .where(User.username == username, EventType.slug == eventTypeSlug, EventType.hidden.is_(False))
    )
    if event_type is None:
        raise ApiException(404, "not_found", "Event type not found.")
    if shareToken:
        link = db.scalar(select(ShareLink).where(ShareLink.token == shareToken))
        if link is None or link.event_type_id != event_type.id:
            raise ApiException(404, "not_found", "Share link not found.")
        if is_share_link_expired(link):
            raise ApiException(410, "link_expired", "Share link is expired.")
    try:
        return success(build_slots_response(event_type, start, end, timeZone, durationMinutes))
    except DomainRuleError as exc:
        raise ApiException(exc.status_code, exc.code, exc.message) from exc


def _validate_dates(start: str, end: str) -> None:
    try:
        parse_local_date(start)
        parse_local_date(end)
    except ValueError as exc:
        raise ApiException(400, "validation_error", "start and end must be local dates.") from exc
