from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.responses import ApiException
from app.application.event_types import get_owned_event_type
from app.db.models import ShareLink, User
from app.schemas.contracts import CreateShareLinkRequest
from app.services.calendar import booking_url, random_token


def create_share_link(db: Session, user: User, event_type_id: str, body: CreateShareLinkRequest) -> ShareLink:
    event_type = get_owned_event_type(db, user.id, event_type_id)
    token = random_token()
    link = ShareLink(
        event_type_id=event_type.id,
        token=token,
        booking_url=booking_url(user.username, event_type.slug, token),
        recipient_email=str(body.recipientEmail) if body.recipientEmail else None,
        expires_at=body.expiresAt,
        max_usage_count=body.maxUsageCount,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def delete_share_link(db: Session, owner_id: str, event_type_id: str, share_link_id: str) -> None:
    get_owned_event_type(db, owner_id, event_type_id)
    link = db.scalar(select(ShareLink).where(ShareLink.id == share_link_id, ShareLink.event_type_id == event_type_id))
    if link is None:
        raise ApiException(404, "not_found", "Share link not found.")
    db.delete(link)
    db.commit()
