from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, Response

from app.api.deps import current_user
from app.api.responses import ApiException, success
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import Schedule, User
from app.db.session import get_db
from app.schemas.contracts import LoginRequest, RegisterRequest
from app.services.calendar import default_availability, dumps_json, prepare_availability
from app.services.mappers import map_user


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    existing = db.scalar(select(User).where(or_(User.email == body.email, User.username == body.username)))
    if existing is not None:
        raise ApiException(409, "conflict", "User already exists.")

    user = User(
        email=str(body.email),
        username=body.username,
        name=body.name,
        time_zone=body.timeZone,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.flush()

    schedule = Schedule(
        owner_id=user.id,
        name="Working hours",
        time_zone=user.time_zone,
        is_default=True,
        availability_json=dumps_json(prepare_availability(default_availability())),
        overrides_json="[]",
    )
    db.add(schedule)
    db.flush()
    user.default_schedule_id = schedule.id
    db.commit()
    db.refresh(user)

    return success({"accessToken": create_access_token(user.id), "tokenType": "Bearer", "user": map_user(user)})


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    user = db.scalar(select(User).where(User.email == str(body.email)))
    if user is None or not verify_password(body.password, user.password_hash):
        raise ApiException(401, "unauthorized", "Invalid email or password.")
    return success({"accessToken": create_access_token(user.id), "tokenType": "Bearer", "user": map_user(user)})


@router.post("/logout", status_code=204)
def logout(_: User = Depends(current_user)) -> Response:
    return Response(status_code=204)
