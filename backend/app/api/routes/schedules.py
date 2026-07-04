from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, Response

from app.api.deps import current_user
from app.api.responses import ApiException, success
from app.application import schedules as schedule_use_cases
from app.db.models import Schedule, User
from app.db.session import get_db
from app.schemas.contracts import CreateScheduleRequest, UpdateScheduleRequest
from app.services.mappers import map_schedule


router = APIRouter(prefix="/schedules", tags=["Schedules"])


@router.post("", status_code=201)
def create_schedule(
    body: CreateScheduleRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return success(map_schedule(schedule_use_cases.create_schedule(db, user, body)))


@router.get("")
def list_schedules(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    schedules = db.scalars(
        select(Schedule).where(Schedule.owner_id == user.id).order_by(Schedule.created_at.asc())
    ).all()
    return success({"items": [map_schedule(schedule) for schedule in schedules]})


@router.get("/default")
def get_default_schedule(user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    schedule = db.scalar(select(Schedule).where(Schedule.owner_id == user.id, Schedule.is_default.is_(True)))
    if schedule is None:
        raise ApiException(404, "not_found", "Default schedule not found.")
    return success(map_schedule(schedule))


@router.get("/{schedule_id}")
def get_schedule(
    schedule_id: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    schedule = schedule_use_cases.get_owned_schedule(db, user.id, schedule_id)
    return success(map_schedule(schedule))


@router.patch("/{schedule_id}")
def update_schedule(
    schedule_id: str,
    body: UpdateScheduleRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return success(map_schedule(schedule_use_cases.update_schedule(db, user, schedule_id, body)))


@router.delete("/{schedule_id}", status_code=204)
def delete_schedule(
    schedule_id: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> Response:
    schedule_use_cases.delete_schedule(db, user, schedule_id)
    return Response(status_code=204)
