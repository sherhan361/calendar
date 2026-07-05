from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends

from app.api.deps import current_user
from app.api.responses import ApiException, success
from app.application import event_types as event_type_use_cases
from app.application.slots import DomainRuleError, build_slots_response
from app.db.models import EventType, User
from app.db.session import get_db
from app.services.calendar import parse_local_date


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
    event_type = event_type_use_cases.get_public_event_type(db, username, eventTypeSlug, shareToken)
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
