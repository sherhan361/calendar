from __future__ import annotations

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends

from app.api.deps import current_user
from app.api.responses import ApiException, success
from app.db.models import User
from app.db.session import get_db
from app.schemas.contracts import UpdateMeRequest
from app.services.mappers import map_user


router = APIRouter(prefix="/me", tags=["Me"])


@router.get("")
def get_me(user: User = Depends(current_user)) -> dict[str, object]:
    return success(map_user(user))


@router.patch("")
def update_me(
    body: UpdateMeRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if "email" in body.model_fields_set and body.email is not None and str(body.email) != user.email:
        existing = db.scalar(select(User).where(and_(User.email == str(body.email), User.id != user.id)))
        if existing is not None:
            raise ApiException(409, "conflict", "Email is already used.")
        user.email = str(body.email)

    username_changed = "username" in body.model_fields_set and body.username is not None and body.username != user.username
    if username_changed:
        existing = db.scalar(select(User).where(and_(User.username == body.username, User.id != user.id)))
        if existing is not None:
            raise ApiException(409, "conflict", "Username is already used.")
        user.username = body.username

    if "name" in body.model_fields_set and body.name is not None:
        user.name = body.name
    if "avatarUrl" in body.model_fields_set:
        user.avatar_url = body.avatarUrl
    if "timeZone" in body.model_fields_set and body.timeZone is not None:
        user.time_zone = body.timeZone

    db.commit()
    db.refresh(user)
    return success(map_user(user))
