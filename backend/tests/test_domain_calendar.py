from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from app.domain.calendar import (
    BusyBooking,
    DomainRuleError,
    attendee_confirm_status,
    build_slot_days,
    host_confirm_status,
)


def test_slots_are_built_in_schedule_timezone() -> None:
    days = build_slot_days(
        schedule_time_zone="Europe/Moscow",
        availability_payload=[{"days": ["monday"], "startTime": "09:00", "endTime": "10:00"}],
        overrides_payload=[],
        booking_window_payload=None,
        bookings=[],
        start_day=date(2026, 7, 6),
        end_day=date(2026, 7, 6),
        duration_minutes=30,
        slot_interval_minutes=30,
        minimum_booking_notice_minutes=None,
        before_event_buffer_minutes=None,
        after_event_buffer_minutes=None,
        block_slot_before_confirmation=True,
        now=datetime(2026, 7, 4, tzinfo=timezone.utc),
    )

    assert days[0].slots[0].start == datetime(2026, 7, 6, 6, 0, tzinfo=timezone.utc)
    assert days[0].slots[0].end == datetime(2026, 7, 6, 6, 30, tzinfo=timezone.utc)


def test_partial_unavailable_override_removes_only_that_interval() -> None:
    days = build_slot_days(
        schedule_time_zone="UTC",
        availability_payload=[{"days": ["monday"], "startTime": "09:00", "endTime": "11:00"}],
        overrides_payload=[
            {"date": "2026-07-06", "startTime": "09:30", "endTime": "10:00", "unavailable": True}
        ],
        booking_window_payload=None,
        bookings=[],
        start_day=date(2026, 7, 6),
        end_day=date(2026, 7, 6),
        duration_minutes=30,
        slot_interval_minutes=30,
        minimum_booking_notice_minutes=None,
        before_event_buffer_minutes=None,
        after_event_buffer_minutes=None,
        block_slot_before_confirmation=True,
        now=datetime(2026, 7, 4, tzinfo=timezone.utc),
    )

    assert [slot.start.hour for slot in days[0].slots] == [9, 10, 10]
    assert [slot.start.minute for slot in days[0].slots] == [0, 0, 30]


def test_pending_bookings_block_slots_only_when_policy_requires_it() -> None:
    base_kwargs = {
        "schedule_time_zone": "UTC",
        "availability_payload": [{"days": ["monday"], "startTime": "09:00", "endTime": "10:00"}],
        "overrides_payload": [],
        "booking_window_payload": None,
        "bookings": [
            BusyBooking(
                start=datetime(2026, 7, 6, 9, 0, tzinfo=timezone.utc),
                end=datetime(2026, 7, 6, 9, 30, tzinfo=timezone.utc),
                status="pending_host",
            )
        ],
        "start_day": date(2026, 7, 6),
        "end_day": date(2026, 7, 6),
        "duration_minutes": 30,
        "slot_interval_minutes": 30,
        "minimum_booking_notice_minutes": None,
        "before_event_buffer_minutes": None,
        "after_event_buffer_minutes": None,
        "now": datetime(2026, 7, 4, tzinfo=timezone.utc),
    }

    blocking_days = build_slot_days(**base_kwargs, block_slot_before_confirmation=True)
    non_blocking_days = build_slot_days(**base_kwargs, block_slot_before_confirmation=False)

    assert blocking_days[0].slots[0].available is False
    assert non_blocking_days[0].slots[0].available is True


def test_after_buffer_blocks_adjacent_slot() -> None:
    days = build_slot_days(
        schedule_time_zone="UTC",
        availability_payload=[{"days": ["monday"], "startTime": "09:00", "endTime": "10:00"}],
        overrides_payload=[],
        booking_window_payload=None,
        bookings=[
            BusyBooking(
                start=datetime(2026, 7, 6, 9, 0, tzinfo=timezone.utc),
                end=datetime(2026, 7, 6, 9, 15, tzinfo=timezone.utc),
                status="confirmed",
            )
        ],
        start_day=date(2026, 7, 6),
        end_day=date(2026, 7, 6),
        duration_minutes=15,
        slot_interval_minutes=15,
        minimum_booking_notice_minutes=None,
        before_event_buffer_minutes=None,
        after_event_buffer_minutes=15,
        block_slot_before_confirmation=True,
        now=datetime(2026, 7, 4, tzinfo=timezone.utc),
    )

    assert [slot.available for slot in days[0].slots[:3]] == [False, False, True]


def test_booking_window_marks_slots_outside_window_unavailable() -> None:
    days = build_slot_days(
        schedule_time_zone="UTC",
        availability_payload=[{"days": ["monday"], "startTime": "09:00", "endTime": "10:00"}],
        overrides_payload=[],
        booking_window_payload={"rollingDays": 1},
        bookings=[],
        start_day=date(2026, 7, 6),
        end_day=date(2026, 7, 6),
        duration_minutes=30,
        slot_interval_minutes=30,
        minimum_booking_notice_minutes=None,
        before_event_buffer_minutes=None,
        after_event_buffer_minutes=None,
        block_slot_before_confirmation=True,
        now=datetime(2026, 7, 4, tzinfo=timezone.utc),
    )

    assert days[0].slots
    assert all(slot.available is False for slot in days[0].slots)


def test_booking_confirmation_transitions_are_role_specific() -> None:
    assert host_confirm_status("pending_host") == "confirmed"
    assert attendee_confirm_status("pending_attendee") == "confirmed"

    with pytest.raises(DomainRuleError):
        host_confirm_status("pending_attendee")

    with pytest.raises(DomainRuleError):
        attendee_confirm_status("pending_host")
