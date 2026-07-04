from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, Response

from app.api.deps import current_user
from app.api.responses import ApiException, success
from app.application import event_types as event_type_use_cases
from app.application import share_links as share_link_use_cases
from app.db.models import ShareLink, User
from app.db.session import get_db
from app.schemas.contracts import CreateShareLinkRequest
from app.services.calendar import is_share_link_expired
from app.services.mappers import map_public_share_link, map_share_link


router = APIRouter(tags=["Share Links"])


@router.post("/event-types/{event_type_id}/share-links", status_code=201)
def create_share_link(
    event_type_id: str,
    body: CreateShareLinkRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return success(map_share_link(share_link_use_cases.create_share_link(db, user, event_type_id, body)))


@router.get("/event-types/{event_type_id}/share-links")
def list_share_links(
    event_type_id: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    event_type_use_cases.get_owned_event_type(db, user.id, event_type_id)
    links = db.scalars(
        select(ShareLink).where(ShareLink.event_type_id == event_type_id).order_by(ShareLink.created_at.desc())
    ).all()
    return success({"items": [map_share_link(link) for link in links]})


@router.delete("/event-types/{event_type_id}/share-links/{share_link_id}", status_code=204)
def delete_share_link(
    event_type_id: str,
    share_link_id: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> Response:
    share_link_use_cases.delete_share_link(db, user.id, event_type_id, share_link_id)
    return Response(status_code=204)


@router.get("/public/share-links/{token}", tags=["Public Share Links"])
def get_public_share_link(token: str, db: Session = Depends(get_db)) -> dict[str, object]:
    link = db.scalar(select(ShareLink).where(ShareLink.token == token))
    if link is None:
        raise ApiException(404, "not_found", "Share link not found.")
    if is_share_link_expired(link):
        raise ApiException(410, "link_expired", "Share link is expired.")
    return success(map_public_share_link(link))
