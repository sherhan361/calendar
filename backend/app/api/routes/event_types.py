from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, Response

from app.api.deps import current_user
from app.api.responses import success
from app.application import event_types as event_type_use_cases
from app.db.models import EventType, User
from app.db.session import get_db
from app.schemas.contracts import CreateEventTypeRequest, UpdateEventTypeRequest
from app.services.mappers import map_event_type, map_public_event_type


router = APIRouter(tags=["Event Types"])


@router.post("/event-types", status_code=201)
def create_event_type(
    body: CreateEventTypeRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return success(map_event_type(event_type_use_cases.create_event_type(db, user, body)))


@router.get("/event-types")
def list_event_types(
    includeHidden: bool = False,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    filters = [EventType.owner_id == user.id]
    if not includeHidden:
        filters.append(EventType.hidden.is_(False))
    event_types = db.scalars(select(EventType).where(*filters).order_by(EventType.created_at.asc())).all()
    return success({"items": [map_event_type(event_type) for event_type in event_types]})


@router.get("/event-types/{event_type_id}")
def get_event_type(
    event_type_id: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    event_type = event_type_use_cases.get_owned_event_type(db, user.id, event_type_id)
    return success(map_event_type(event_type))


@router.patch("/event-types/{event_type_id}")
def update_event_type(
    event_type_id: str,
    body: UpdateEventTypeRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return success(map_event_type(event_type_use_cases.update_event_type(db, user, event_type_id, body)))


@router.delete("/event-types/{event_type_id}", status_code=204)
def delete_event_type(
    event_type_id: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> Response:
    event_type_use_cases.delete_event_type(db, user.id, event_type_id)
    return Response(status_code=204)


@router.get("/public/users/{username}/event-types/{slug}", tags=["Public Event Types"])
def get_public_event_type(
    username: str,
    slug: str,
    shareToken: str | None = None,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    event_type = event_type_use_cases.get_public_event_type(db, username, slug, shareToken)
    return success(map_public_event_type(event_type))
