from __future__ import annotations

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.api.responses import ApiException
from app.db.models import Booking, EventType, Schedule, ShareLink, User
from app.schemas.contracts import CreateEventTypeRequest, UpdateEventTypeRequest
from app.services.calendar import booking_url, dumps_json, is_share_link_expired


def create_event_type(db: Session, user: User, body: CreateEventTypeRequest) -> EventType:
    schedule_id = body.scheduleId or user.default_schedule_id
    if schedule_id is None:
        raise ApiException(400, "validation_error", "scheduleId is required.")
    get_owned_schedule(db, user.id, schedule_id)
    ensure_slug_available(db, user.id, body.slug)

    policy = body.confirmationPolicy
    _validate_settings(
        body.durationMinutes,
        body.slotIntervalMinutes,
        policy.type.value if policy else "automatic",
        bool(policy.blockSlotBeforeConfirmation) if policy else False,
    )
    event_type = EventType(
        owner_id=user.id,
        schedule_id=schedule_id,
        title=body.title,
        slug=body.slug,
        description=body.description,
        duration_minutes=body.durationMinutes,
        slot_interval_minutes=body.slotIntervalMinutes,
        minimum_booking_notice_minutes=body.minimumBookingNoticeMinutes,
        before_event_buffer_minutes=body.beforeEventBufferMinutes,
        after_event_buffer_minutes=body.afterEventBufferMinutes,
        booking_window_json=dumps_json(body.bookingWindow.model_dump(exclude_none=True)) if body.bookingWindow else None,
        confirmation_policy_type=policy.type.value if policy else "automatic",
        block_slot_before_confirmation=bool(policy.blockSlotBeforeConfirmation) if policy else False,
        hidden=bool(body.hidden),
        booking_url=booking_url(user.username, body.slug),
    )
    db.add(event_type)
    db.commit()
    db.refresh(event_type)
    return event_type


def update_event_type(db: Session, user: User, event_type_id: str, body: UpdateEventTypeRequest) -> EventType:
    event_type = get_owned_event_type(db, user.id, event_type_id)

    if "scheduleId" in body.model_fields_set and body.scheduleId is not None:
        get_owned_schedule(db, user.id, body.scheduleId)
        event_type.schedule_id = body.scheduleId
    if "slug" in body.model_fields_set and body.slug is not None and body.slug != event_type.slug:
        ensure_slug_available(db, user.id, body.slug, exclude_event_type_id=event_type.id)
        event_type.slug = body.slug
        event_type.booking_url = booking_url(user.username, body.slug)
    if "title" in body.model_fields_set and body.title is not None:
        event_type.title = body.title
    if "description" in body.model_fields_set:
        event_type.description = body.description
    if "durationMinutes" in body.model_fields_set and body.durationMinutes is not None:
        event_type.duration_minutes = body.durationMinutes
    if "slotIntervalMinutes" in body.model_fields_set:
        event_type.slot_interval_minutes = body.slotIntervalMinutes
    if "minimumBookingNoticeMinutes" in body.model_fields_set:
        event_type.minimum_booking_notice_minutes = body.minimumBookingNoticeMinutes
    if "beforeEventBufferMinutes" in body.model_fields_set:
        event_type.before_event_buffer_minutes = body.beforeEventBufferMinutes
    if "afterEventBufferMinutes" in body.model_fields_set:
        event_type.after_event_buffer_minutes = body.afterEventBufferMinutes
    if "bookingWindow" in body.model_fields_set:
        event_type.booking_window_json = (
            dumps_json(body.bookingWindow.model_dump(exclude_none=True)) if body.bookingWindow else None
        )
    if "confirmationPolicy" in body.model_fields_set and body.confirmationPolicy is not None:
        event_type.confirmation_policy_type = body.confirmationPolicy.type.value
        event_type.block_slot_before_confirmation = bool(body.confirmationPolicy.blockSlotBeforeConfirmation)
    if "hidden" in body.model_fields_set and body.hidden is not None:
        event_type.hidden = body.hidden

    _validate_settings(
        event_type.duration_minutes,
        event_type.slot_interval_minutes,
        event_type.confirmation_policy_type,
        event_type.block_slot_before_confirmation,
    )
    db.commit()
    db.refresh(event_type)
    return event_type


def _validate_settings(
    duration_minutes: int,
    slot_interval_minutes: int | None,
    confirmation_policy_type: str,
    block_slot_before_confirmation: bool,
) -> None:
    if duration_minutes <= 0:
        raise ApiException(400, "validation_error", "durationMinutes must be positive.")
    if slot_interval_minutes is not None and slot_interval_minutes <= 0:
        raise ApiException(400, "validation_error", "slotIntervalMinutes must be positive.")
    if confirmation_policy_type == "automatic" and block_slot_before_confirmation:
        raise ApiException(
            400,
            "validation_error",
            "Automatic confirmation cannot block slots before confirmation.",
        )


def delete_event_type(db: Session, owner_id: str, event_type_id: str) -> None:
    event_type = get_owned_event_type(db, owner_id, event_type_id)
    has_bookings = db.scalar(select(Booking.id).where(Booking.event_type_id == event_type.id).limit(1))
    if has_bookings is not None:
        raise ApiException(
            409,
            "conflict",
            "Event type has bookings and cannot be deleted. Hide it instead.",
        )
    db.delete(event_type)
    db.commit()


def get_public_event_type(db: Session, username: str, slug: str, share_token: str | None) -> EventType:
    filters = [User.username == username, EventType.slug == slug]
    if share_token is None:
        filters.append(EventType.hidden.is_(False))

    event_type = db.scalar(select(EventType).join(EventType.owner).where(*filters))
    if event_type is None:
        raise ApiException(404, "not_found", "Event type not found.")
    if share_token:
        validate_share_token(db, event_type.id, share_token)
    return event_type


def get_owned_schedule(db: Session, owner_id: str, schedule_id: str) -> Schedule:
    schedule = db.scalar(select(Schedule).where(Schedule.id == schedule_id, Schedule.owner_id == owner_id))
    if schedule is None:
        raise ApiException(404, "not_found", "Schedule not found.")
    return schedule


def get_owned_event_type(db: Session, owner_id: str, event_type_id: str) -> EventType:
    event_type = db.scalar(select(EventType).where(EventType.id == event_type_id, EventType.owner_id == owner_id))
    if event_type is None:
        raise ApiException(404, "not_found", "Event type not found.")
    return event_type


def ensure_slug_available(
    db: Session,
    owner_id: str,
    slug: str,
    exclude_event_type_id: str | None = None,
) -> None:
    filters = [EventType.owner_id == owner_id, EventType.slug == slug]
    if exclude_event_type_id:
        filters.append(EventType.id != exclude_event_type_id)
    existing = db.scalar(select(EventType).where(and_(*filters)))
    if existing is not None:
        raise ApiException(409, "conflict", "Event type slug already exists.")


def validate_share_token(db: Session, event_type_id: str, token: str) -> ShareLink:
    link = db.scalar(select(ShareLink).where(ShareLink.token == token))
    if link is None or link.event_type_id != event_type_id:
        raise ApiException(404, "not_found", "Share link not found.")
    if is_share_link_expired(link):
        raise ApiException(410, "link_expired", "Share link is expired.")
    return link
