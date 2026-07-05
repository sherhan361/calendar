from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.responses import ApiException
from app.application.events import (
    BOOKING_CANCELLED,
    BOOKING_CONFIRMED,
    BOOKING_CREATED,
    BOOKING_DECLINED,
    emit_booking_event,
)
from app.application.slots import event_type_slot_is_available
from app.db.models import Booking, EventType, ShareLink, User
from app.domain.calendar import (
    ACTIVE_BOOKING_STATUSES,
    DomainRuleError,
    attendee_confirm_status,
    cancel_status,
    ensure_utc,
    host_confirm_status,
    host_decline_status,
    initial_booking_status,
)
from app.schemas.contracts import BookingActionRequest, CreateBookingRequest
from app.services.calendar import is_share_link_expired, random_token


def create_booking(db: Session, body: CreateBookingRequest) -> Booking:
    event_type = _resolve_event_type_for_booking(db, body)
    if event_type is None:
        raise ApiException(404, "not_found", "Event type not found.")

    if body.idempotencyKey is not None:
        existing = _find_by_idempotency_key(db, event_type.id, body.idempotencyKey)
        if existing is not None:
            return existing

    link = _resolve_share_link(db, event_type, body.shareToken)
    start = ensure_utc(body.start)
    duration_minutes = body.durationMinutes or event_type.duration_minutes
    end = start + timedelta(minutes=duration_minutes)

    try:
        slot_available = event_type_slot_is_available(event_type, start, end, duration_minutes)
        status = initial_booking_status(event_type.confirmation_policy_type)
    except DomainRuleError as exc:
        raise _api_error(exc) from exc
    if not slot_available:
        raise ApiException(409, "conflict", "Slot is not available.")

    booking = Booking(
        uid=f"booking_{uuid4().hex[:12]}",
        event_type_id=event_type.id,
        owner_id=event_type.owner_id,
        title=event_type.title,
        description=event_type.description,
        status=status,
        start=start,
        end=end,
        duration_minutes=duration_minutes,
        attendee_name=body.attendee.name,
        attendee_email=str(body.attendee.email),
        attendee_time_zone=body.attendee.timeZone,
        attendee_token=random_token(),
        idempotency_key=body.idempotencyKey,
        share_token=body.shareToken,
    )
    if link is not None:
        link.usage_count += 1
    db.add(booking)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        return _resolve_booking_conflict(db, body, event_type.id, start, exc)
    db.refresh(booking)
    emit_booking_event(booking, BOOKING_CREATED)
    return booking


def _resolve_booking_conflict(
    db: Session,
    body: CreateBookingRequest,
    event_type_id: str,
    start: datetime,
    exc: IntegrityError,
) -> Booking:
    if body.idempotencyKey is not None:
        existing = _find_by_idempotency_key(db, event_type_id, body.idempotencyKey)
        if existing is not None:
            return existing
    if _active_slot_taken(db, event_type_id, start):
        raise ApiException(409, "conflict", "Slot is not available.") from exc
    raise ApiException(409, "conflict", "Booking could not be created.") from exc


def _find_by_idempotency_key(db: Session, event_type_id: str, idempotency_key: str) -> Booking | None:
    return db.scalar(
        select(Booking).where(
            Booking.event_type_id == event_type_id,
            Booking.idempotency_key == idempotency_key,
        )
    )


def _active_slot_taken(db: Session, event_type_id: str, start: datetime) -> bool:
    active = db.scalar(
        select(Booking).where(
            Booking.event_type_id == event_type_id,
            Booking.start == start,
            Booking.status.in_(ACTIVE_BOOKING_STATUSES),
        )
    )
    return active is not None


def confirm_booking(db: Session, owner_id: str, booking_uid: str) -> Booking:
    booking = get_owned_booking(db, owner_id, booking_uid)
    try:
        booking.status = host_confirm_status(booking.status)
    except DomainRuleError as exc:
        raise _api_error(exc) from exc
    db.commit()
    db.refresh(booking)
    emit_booking_event(booking, BOOKING_CONFIRMED)
    return booking


def decline_booking(db: Session, owner_id: str, booking_uid: str, body: BookingActionRequest) -> Booking:
    booking = get_owned_booking(db, owner_id, booking_uid)
    try:
        booking.status = host_decline_status(booking.status)
    except DomainRuleError as exc:
        raise _api_error(exc) from exc
    booking.rejection_reason = body.reason or "Declined by host"
    db.commit()
    db.refresh(booking)
    emit_booking_event(booking, BOOKING_DECLINED)
    return booking


def cancel_booking(db: Session, owner_id: str, booking_uid: str, body: BookingActionRequest) -> Booking:
    booking = get_owned_booking(db, owner_id, booking_uid)
    try:
        booking.status = cancel_status(booking.status)
    except DomainRuleError as exc:
        raise _api_error(exc) from exc
    booking.cancellation_reason = body.reason or "Cancelled by host"
    db.commit()
    db.refresh(booking)
    emit_booking_event(booking, BOOKING_CANCELLED)
    return booking


def confirm_attendee(db: Session, booking_uid: str, token: str) -> Booking:
    booking = _get_booking_for_token(db, booking_uid, token)
    try:
        booking.status = attendee_confirm_status(booking.status)
    except DomainRuleError as exc:
        raise _api_error(exc) from exc
    booking.attendee_confirmed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(booking)
    emit_booking_event(booking, BOOKING_CONFIRMED)
    return booking


def cancel_attendee(db: Session, booking_uid: str, token: str, body: BookingActionRequest) -> Booking:
    booking = _get_booking_for_token(db, booking_uid, token)
    try:
        booking.status = cancel_status(booking.status)
    except DomainRuleError as exc:
        raise _api_error(exc) from exc
    reason = (body.reason or "").strip()
    booking.cancellation_reason = reason or None
    db.commit()
    db.refresh(booking)
    emit_booking_event(booking, BOOKING_CANCELLED)
    return booking


def _get_booking_for_token(db: Session, booking_uid: str, token: str) -> Booking:
    booking = db.scalar(select(Booking).where(Booking.uid == booking_uid))
    if booking is None:
        raise ApiException(404, "not_found", "Booking not found.")
    if booking.attendee_token != token:
        raise ApiException(410, "link_expired", "Invalid attendee token.")
    return booking


def get_owned_booking(db: Session, owner_id: str, booking_uid: str) -> Booking:
    booking = db.scalar(select(Booking).where(Booking.uid == booking_uid, Booking.owner_id == owner_id))
    if booking is None:
        raise ApiException(404, "not_found", "Booking not found.")
    return booking


def _resolve_event_type_for_booking(db: Session, body: CreateBookingRequest) -> EventType | None:
    if body.shareToken:
        link = db.scalar(select(ShareLink).where(ShareLink.token == body.shareToken))
        if link is None:
            return None
        if is_share_link_expired(link):
            raise ApiException(410, "link_expired", "Share link is expired.")

        statement = select(EventType).where(EventType.id == link.event_type_id)
        if body.eventTypeId:
            statement = statement.where(EventType.id == body.eventTypeId)
        if body.username or body.eventTypeSlug:
            statement = statement.join(EventType.owner)
            if body.username:
                statement = statement.where(User.username == body.username)
            if body.eventTypeSlug:
                statement = statement.where(EventType.slug == body.eventTypeSlug)
        return db.scalar(statement)

    if body.eventTypeId:
        return db.scalar(select(EventType).where(EventType.id == body.eventTypeId, EventType.hidden.is_(False)))
    if body.username and body.eventTypeSlug:
        return db.scalar(
            select(EventType)
            .join(EventType.owner)
            .where(User.username == body.username, EventType.slug == body.eventTypeSlug, EventType.hidden.is_(False))
        )
    return None


def _resolve_share_link(db: Session, event_type: EventType, token: str | None) -> ShareLink | None:
    if not token:
        return None
    link = db.scalar(select(ShareLink).where(ShareLink.token == token))
    if link is None or link.event_type_id != event_type.id:
        raise ApiException(404, "not_found", "Share link not found.")
    if is_share_link_expired(link):
        raise ApiException(410, "link_expired", "Share link is expired.")
    return link


def _api_error(exc: DomainRuleError) -> ApiException:
    return ApiException(exc.status_code, exc.code, exc.message)
