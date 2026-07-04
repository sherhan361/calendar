from __future__ import annotations

from datetime import date, datetime

from app.domain.calendar import (
    BusyBooking,
    DaySlots,
    DomainRuleError,
    build_slot_days,
    ensure_utc,
    parse_local_date,
    require_zone,
)
from app.db.models import EventType
from app.services.calendar import load_json


def build_slots_response(
    event_type: EventType,
    start: str,
    end: str,
    time_zone: str | None = None,
    duration_minutes: int | None = None,
    now: datetime | None = None,
) -> dict[str, object]:
    start_day = parse_local_date(start)
    end_day = parse_local_date(end)
    response_time_zone = time_zone or event_type.schedule.time_zone
    require_zone(response_time_zone)
    days = _build_day_slots(event_type, start_day, end_day, duration_minutes, now)
    return {
        "timeZone": response_time_zone,
        "days": [
            {
                "date": day_slots.day.isoformat(),
                "slots": [
                    {"start": slot.start, "end": slot.end, "available": slot.available}
                    for slot in day_slots.slots
                ],
            }
            for day_slots in days
        ],
    }


def event_type_slot_is_available(
    event_type: EventType,
    start: datetime,
    end: datetime,
    duration_minutes: int,
    now: datetime | None = None,
) -> bool:
    start_utc = ensure_utc(start)
    end_utc = ensure_utc(end)
    schedule_zone = require_zone(event_type.schedule.time_zone)
    local_day = start_utc.astimezone(schedule_zone).date()
    day_slots = _build_day_slots(event_type, local_day, local_day, duration_minutes, now)
    for day in day_slots:
        for slot in day.slots:
            if slot.start == start_utc and slot.end == end_utc:
                return slot.available
    return False


def _build_day_slots(
    event_type: EventType,
    start_day: date,
    end_day: date,
    duration_minutes: int | None,
    now: datetime | None,
) -> list[DaySlots]:
    return build_slot_days(
        schedule_time_zone=event_type.schedule.time_zone,
        availability_payload=load_json(event_type.schedule.availability_json, []),
        overrides_payload=load_json(event_type.schedule.overrides_json, []),
        booking_window_payload=load_json(event_type.booking_window_json, None),
        bookings=[
            BusyBooking(start=ensure_utc(booking.start), end=ensure_utc(booking.end), status=booking.status)
            for booking in event_type.bookings
        ],
        start_day=start_day,
        end_day=end_day,
        duration_minutes=duration_minutes or event_type.duration_minutes,
        slot_interval_minutes=event_type.slot_interval_minutes,
        minimum_booking_notice_minutes=event_type.minimum_booking_notice_minutes,
        before_event_buffer_minutes=event_type.before_event_buffer_minutes,
        after_event_buffer_minutes=event_type.after_event_buffer_minutes,
        block_slot_before_confirmation=event_type.block_slot_before_confirmation,
        now=now,
    )


__all__ = ["DomainRuleError", "build_slots_response", "event_type_slot_is_available"]
