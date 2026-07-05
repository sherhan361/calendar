from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


WEEKDAY_BY_INDEX = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
CONFIRMATION_POLICY_TYPES = {"automatic", "host", "attendee"}
BOOKING_STATUSES = {"pending_host", "pending_attendee", "confirmed", "declined", "cancelled"}
PENDING_BOOKING_STATUSES = {"pending_host", "pending_attendee"}
NON_BLOCKING_BOOKING_STATUSES = {"cancelled", "declined"}
ACTIVE_BOOKING_STATUSES = BOOKING_STATUSES - NON_BLOCKING_BOOKING_STATUSES


class DomainRuleError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 409) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class TimeRange:
    start: datetime
    end: datetime

    def overlaps(self, other: "TimeRange") -> bool:
        return self.start < other.end and self.end > other.start


@dataclass(frozen=True)
class AvailabilityRule:
    days: frozenset[str]
    start_time: time
    end_time: time


@dataclass(frozen=True)
class AvailabilityOverride:
    day: date
    start_time: time | None
    end_time: time | None
    unavailable: bool

    @property
    def is_whole_day(self) -> bool:
        return self.start_time is None and self.end_time is None


@dataclass(frozen=True)
class BookingWindow:
    rolling_days: int | None = None
    date_from: date | None = None
    date_to: date | None = None


@dataclass(frozen=True)
class BusyBooking:
    start: datetime
    end: datetime
    status: str


@dataclass(frozen=True)
class SlotAvailability:
    start: datetime
    end: datetime
    available: bool


@dataclass(frozen=True)
class DaySlots:
    day: date
    slots: tuple[SlotAvailability, ...]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def parse_local_date(value: str) -> date:
    return date.fromisoformat(value)


def require_zone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise DomainRuleError("validation_error", f"Unknown time zone: {name}", status_code=400) from exc


def parse_availability_rules(payload: object) -> list[AvailabilityRule]:
    if not isinstance(payload, list):
        return []
    rules: list[AvailabilityRule] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        start_time = _parse_time_or_none(item.get("startTime"))
        end_time = _parse_time_or_none(item.get("endTime"))
        if start_time is None or end_time is None or start_time >= end_time:
            continue
        rules.append(
            AvailabilityRule(
                days=frozenset(str(day) for day in item.get("days", []) if str(day) in WEEKDAY_BY_INDEX),
                start_time=start_time,
                end_time=end_time,
            )
        )
    return rules


def parse_availability_overrides(payload: object) -> list[AvailabilityOverride]:
    if not isinstance(payload, list):
        return []
    overrides: list[AvailabilityOverride] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        raw_date = item.get("date")
        if not isinstance(raw_date, str):
            continue
        try:
            override_day = parse_local_date(raw_date)
        except ValueError:
            continue
        overrides.append(
            AvailabilityOverride(
                day=override_day,
                start_time=_parse_time_or_none(item.get("startTime")),
                end_time=_parse_time_or_none(item.get("endTime")),
                unavailable=bool(item.get("unavailable", False)),
            )
        )
    return overrides


def parse_booking_window(payload: object) -> BookingWindow | None:
    if not isinstance(payload, dict):
        return None
    return BookingWindow(
        rolling_days=_positive_int_or_none(payload.get("rollingDays")),
        date_from=_date_or_none(payload.get("dateFrom")),
        date_to=_date_or_none(payload.get("dateTo")),
    )


def build_slot_days(
    *,
    schedule_time_zone: str,
    availability_payload: object,
    overrides_payload: object,
    booking_window_payload: object,
    bookings: list[BusyBooking],
    start_day: date,
    end_day: date,
    duration_minutes: int,
    slot_interval_minutes: int | None,
    minimum_booking_notice_minutes: int | None,
    before_event_buffer_minutes: int | None,
    after_event_buffer_minutes: int | None,
    block_slot_before_confirmation: bool,
    now: datetime | None = None,
) -> list[DaySlots]:
    if duration_minutes <= 0:
        raise DomainRuleError("validation_error", "durationMinutes must be positive.", status_code=400)
    if end_day < start_day:
        end_day = start_day

    schedule_zone = require_zone(schedule_time_zone)
    rules = parse_availability_rules(availability_payload)
    overrides = parse_availability_overrides(overrides_payload)
    booking_window = parse_booking_window(booking_window_payload)
    interval_minutes = slot_interval_minutes if slot_interval_minutes and slot_interval_minutes > 0 else duration_minutes
    now_utc = ensure_utc(now or utc_now())

    days: list[DaySlots] = []
    cursor = start_day
    while cursor <= end_day:
        intervals = available_intervals_for_day(cursor, schedule_zone, rules, overrides)
        slots: list[SlotAvailability] = []
        for interval in intervals:
            slot_start = interval.start
            while slot_start + timedelta(minutes=duration_minutes) <= interval.end:
                slot_end = slot_start + timedelta(minutes=duration_minutes)
                start_utc = slot_start.astimezone(timezone.utc)
                end_utc = slot_end.astimezone(timezone.utc)
                slots.append(
                    SlotAvailability(
                        start=start_utc,
                        end=end_utc,
                        available=is_slot_available(
                            start_utc=start_utc,
                            end_utc=end_utc,
                            schedule_zone=schedule_zone,
                            booking_window=booking_window,
                            bookings=bookings,
                            minimum_booking_notice_minutes=minimum_booking_notice_minutes,
                            before_event_buffer_minutes=before_event_buffer_minutes,
                            after_event_buffer_minutes=after_event_buffer_minutes,
                            block_slot_before_confirmation=block_slot_before_confirmation,
                            now=now_utc,
                        ),
                    )
                )
                slot_start += timedelta(minutes=interval_minutes)
        days.append(DaySlots(day=cursor, slots=tuple(slots)))
        cursor += timedelta(days=1)
    return days


def is_slot_available(
    *,
    start_utc: datetime,
    end_utc: datetime,
    schedule_zone: ZoneInfo,
    booking_window: BookingWindow | None,
    bookings: list[BusyBooking],
    minimum_booking_notice_minutes: int | None,
    before_event_buffer_minutes: int | None,
    after_event_buffer_minutes: int | None,
    block_slot_before_confirmation: bool,
    now: datetime,
) -> bool:
    start_utc = ensure_utc(start_utc)
    end_utc = ensure_utc(end_utc)
    now = ensure_utc(now)
    if end_utc <= start_utc:
        return False
    if start_utc < now:
        return False
    if minimum_booking_notice_minutes and start_utc < now + timedelta(minutes=minimum_booking_notice_minutes):
        return False
    if not _within_booking_window(start_utc, schedule_zone, booking_window, now):
        return False

    candidate = _buffered_range(
        start_utc,
        end_utc,
        before_event_buffer_minutes,
        after_event_buffer_minutes,
    )
    for booking in bookings:
        if not booking_blocks_slot(booking.status, block_slot_before_confirmation):
            continue
        busy = _buffered_range(
            ensure_utc(booking.start),
            ensure_utc(booking.end),
            before_event_buffer_minutes,
            after_event_buffer_minutes,
        )
        if candidate.overlaps(busy):
            return False
    return True


def available_intervals_for_day(
    day: date,
    schedule_zone: ZoneInfo,
    rules: list[AvailabilityRule],
    overrides: list[AvailabilityOverride],
) -> list[TimeRange]:
    weekday = WEEKDAY_BY_INDEX[day.weekday()]
    day_overrides = [override for override in overrides if override.day == day]
    if any(override.unavailable and override.is_whole_day for override in day_overrides):
        return []

    intervals = [
        _local_range(day, rule.start_time, rule.end_time, schedule_zone)
        for rule in rules
        if weekday in rule.days
    ]
    for override in day_overrides:
        if override.is_whole_day or override.start_time is None or override.end_time is None:
            continue
        override_range = _local_range(day, override.start_time, override.end_time, schedule_zone)
        if override_range.end <= override_range.start:
            continue
        if override.unavailable:
            intervals = _subtract_range(intervals, override_range)
        else:
            intervals.append(override_range)
    return _merge_ranges(intervals)


def booking_blocks_slot(status: str, block_pending: bool) -> bool:
    if status in NON_BLOCKING_BOOKING_STATUSES:
        return False
    if status == "confirmed":
        return True
    if status in PENDING_BOOKING_STATUSES:
        return block_pending
    return True


def initial_booking_status(confirmation_policy_type: str) -> str:
    if confirmation_policy_type == "automatic":
        return "confirmed"
    if confirmation_policy_type in {"host", "attendee"}:
        return f"pending_{confirmation_policy_type}"
    raise DomainRuleError("validation_error", "Unknown confirmation policy.", status_code=400)


def host_confirm_status(current_status: str) -> str:
    if current_status == "pending_host":
        return "confirmed"
    raise DomainRuleError("conflict", "Booking cannot be confirmed.")


def attendee_confirm_status(current_status: str) -> str:
    if current_status == "pending_attendee":
        return "confirmed"
    raise DomainRuleError("conflict", "Booking cannot be confirmed.")


def host_decline_status(current_status: str) -> str:
    if current_status in PENDING_BOOKING_STATUSES:
        return "declined"
    raise DomainRuleError("conflict", "Booking cannot be declined.")


def host_cancel_status(current_status: str) -> str:
    if current_status in {"cancelled", "declined"}:
        raise DomainRuleError("conflict", "Booking cannot be cancelled.")
    return "cancelled"


def _within_booking_window(
    start_utc: datetime,
    schedule_zone: ZoneInfo,
    booking_window: BookingWindow | None,
    now: datetime,
) -> bool:
    if booking_window is None:
        return True
    local_day = start_utc.astimezone(schedule_zone).date()
    today = now.astimezone(schedule_zone).date()
    if booking_window.rolling_days is not None and local_day > today + timedelta(days=booking_window.rolling_days):
        return False
    if booking_window.date_from is not None and local_day < booking_window.date_from:
        return False
    if booking_window.date_to is not None and local_day > booking_window.date_to:
        return False
    return True


def _buffered_range(
    start_utc: datetime,
    end_utc: datetime,
    before_event_buffer_minutes: int | None,
    after_event_buffer_minutes: int | None,
) -> TimeRange:
    return TimeRange(
        start=start_utc - timedelta(minutes=before_event_buffer_minutes or 0),
        end=end_utc + timedelta(minutes=after_event_buffer_minutes or 0),
    )


def _local_range(day: date, start_time: time, end_time: time, schedule_zone: ZoneInfo) -> TimeRange:
    return TimeRange(
        start=datetime.combine(day, start_time, tzinfo=schedule_zone),
        end=datetime.combine(day, end_time, tzinfo=schedule_zone),
    )


def _subtract_range(intervals: list[TimeRange], blocked: TimeRange) -> list[TimeRange]:
    next_intervals: list[TimeRange] = []
    for interval in intervals:
        if not interval.overlaps(blocked):
            next_intervals.append(interval)
            continue
        if interval.start < blocked.start:
            next_intervals.append(TimeRange(start=interval.start, end=min(blocked.start, interval.end)))
        if blocked.end < interval.end:
            next_intervals.append(TimeRange(start=max(blocked.end, interval.start), end=interval.end))
    return [interval for interval in next_intervals if interval.start < interval.end]


def _merge_ranges(intervals: list[TimeRange]) -> list[TimeRange]:
    ordered = sorted((interval for interval in intervals if interval.start < interval.end), key=lambda item: item.start)
    if not ordered:
        return []
    merged = [ordered[0]]
    for interval in ordered[1:]:
        previous = merged[-1]
        if interval.start <= previous.end:
            merged[-1] = TimeRange(start=previous.start, end=max(previous.end, interval.end))
        else:
            merged.append(interval)
    return merged


def _parse_time_or_none(value: object) -> time | None:
    if not isinstance(value, str):
        return None
    try:
        hour, minute = [int(part) for part in value.split(":", 1)]
        return time(hour, minute)
    except (TypeError, ValueError):
        return None


def _date_or_none(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return parse_local_date(value)
    except ValueError:
        return None


def _positive_int_or_none(value: object) -> int | None:
    if not isinstance(value, int) or value < 0:
        return None
    return value
