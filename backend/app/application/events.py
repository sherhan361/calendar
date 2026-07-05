from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.db.models import Booking

logger = logging.getLogger("calendar.booking_events")

BOOKING_CREATED = "created"
BOOKING_CONFIRMED = "confirmed"
BOOKING_DECLINED = "declined"
BOOKING_CANCELLED = "cancelled"


@dataclass(frozen=True)
class BookingEvent:
    """Minimal, provider-agnostic payload for a booking lifecycle change.

    Carries just enough for a future notifier (email, calendar, webhook) to
    build a message without loading the ORM again.
    """

    type: str
    booking_uid: str
    event_type_id: str
    event_type_title: str
    host_username: str
    host_email: str
    attendee_name: str
    attendee_email: str
    start: datetime
    end: datetime
    status: str
    reason: str | None = None


class BookingNotifier(Protocol):
    def notify(self, event: BookingEvent) -> None: ...


class LoggingBookingNotifier:
    """Default local/dev notifier. Never sends anything external; it only logs."""

    def notify(self, event: BookingEvent) -> None:
        logger.info(
            "booking_event type=%s uid=%s status=%s attendee=%s",
            event.type,
            event.booking_uid,
            event.status,
            event.attendee_email,
        )


_notifier: BookingNotifier = LoggingBookingNotifier()


def get_booking_notifier() -> BookingNotifier:
    return _notifier


def set_booking_notifier(notifier: BookingNotifier) -> None:
    global _notifier
    _notifier = notifier


def emit_booking_event(booking: Booking, kind: str) -> None:
    event = _build_event(booking, kind)
    try:
        get_booking_notifier().notify(event)
    except Exception:  # noqa: BLE001 - a notifier must never break the booking flow
        logger.exception("booking notifier failed for uid=%s kind=%s", booking.uid, kind)


def _build_event(booking: Booking, kind: str) -> BookingEvent:
    reason = booking.cancellation_reason or booking.rejection_reason
    return BookingEvent(
        type=kind,
        booking_uid=booking.uid,
        event_type_id=booking.event_type_id,
        event_type_title=booking.title,
        host_username=booking.owner.username,
        host_email=booking.owner.email,
        attendee_name=booking.attendee_name,
        attendee_email=booking.attendee_email,
        start=booking.start,
        end=booking.end,
        status=booking.status,
        reason=reason,
    )
