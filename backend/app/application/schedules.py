from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.responses import ApiException
from app.db.models import EventType, Schedule, User
from app.schemas.contracts import CreateScheduleRequest, UpdateScheduleRequest
from app.services.calendar import dumps_json, prepare_availability, prepare_overrides


def create_schedule(db: Session, user: User, body: CreateScheduleRequest) -> Schedule:
    is_default = bool(body.isDefault)
    if is_default:
        clear_default_schedules(db, user.id)
    schedule = Schedule(
        owner_id=user.id,
        name=body.name,
        time_zone=body.timeZone,
        is_default=is_default,
        availability_json=dumps_json(prepare_availability(body.availability)),
        overrides_json=dumps_json(prepare_overrides(body.overrides)),
    )
    db.add(schedule)
    db.flush()
    if is_default or user.default_schedule_id is None:
        schedule.is_default = True
        user.default_schedule_id = schedule.id
    db.commit()
    db.refresh(schedule)
    return schedule


def update_schedule(db: Session, user: User, schedule_id: str, body: UpdateScheduleRequest) -> Schedule:
    schedule = get_owned_schedule(db, user.id, schedule_id)
    if body.isDefault is True:
        clear_default_schedules(db, user.id)
        schedule.is_default = True
        user.default_schedule_id = schedule.id
    elif body.isDefault is False:
        schedule.is_default = False
        if user.default_schedule_id == schedule.id:
            user.default_schedule_id = None

    if "name" in body.model_fields_set and body.name is not None:
        schedule.name = body.name
    if "timeZone" in body.model_fields_set and body.timeZone is not None:
        schedule.time_zone = body.timeZone
    if "availability" in body.model_fields_set and body.availability is not None:
        schedule.availability_json = dumps_json(prepare_availability(body.availability))
    if "overrides" in body.model_fields_set:
        schedule.overrides_json = dumps_json(prepare_overrides(body.overrides))

    db.commit()
    db.refresh(schedule)
    return schedule


def delete_schedule(db: Session, user: User, schedule_id: str) -> None:
    schedule = get_owned_schedule(db, user.id, schedule_id)
    attached = db.scalar(select(func.count(EventType.id)).where(EventType.schedule_id == schedule_id))
    if attached:
        raise ApiException(409, "conflict", "Schedule is used by event types.")
    if user.default_schedule_id == schedule.id:
        user.default_schedule_id = None
    db.delete(schedule)
    db.commit()


def get_owned_schedule(db: Session, owner_id: str, schedule_id: str) -> Schedule:
    schedule = db.scalar(select(Schedule).where(Schedule.id == schedule_id, Schedule.owner_id == owner_id))
    if schedule is None:
        raise ApiException(404, "not_found", "Schedule not found.")
    return schedule


def clear_default_schedules(db: Session, owner_id: str) -> None:
    schedules = db.scalars(select(Schedule).where(Schedule.owner_id == owner_id, Schedule.is_default.is_(True))).all()
    for schedule in schedules:
        schedule.is_default = False
