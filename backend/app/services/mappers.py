from __future__ import annotations

from app.db.models import Booking, EventType, Schedule, ShareLink, User
from datetime import datetime

from app.services.calendar import booking_url, ensure_utc, is_share_link_expired, load_json


def drop_none(payload: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in payload.items() if value is not None}


def map_datetime(value: datetime | None) -> datetime | None:
    return ensure_utc(value) if value is not None else None


def map_user(user: User) -> dict[str, object]:
    return drop_none(
        {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "name": user.name,
            "avatarUrl": user.avatar_url,
            "timeZone": user.time_zone,
            "defaultScheduleId": user.default_schedule_id,
            "createdAt": map_datetime(user.created_at),
            "updatedAt": map_datetime(user.updated_at),
        }
    )


def map_public_user(user: User) -> dict[str, object]:
    return drop_none(
        {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "avatarUrl": user.avatar_url,
            "timeZone": user.time_zone,
        }
    )


def map_schedule(schedule: Schedule) -> dict[str, object]:
    return {
        "id": schedule.id,
        "ownerId": schedule.owner_id,
        "name": schedule.name,
        "timeZone": schedule.time_zone,
        "isDefault": schedule.is_default,
        "availability": load_json(schedule.availability_json, []),
        "overrides": load_json(schedule.overrides_json, []),
        "createdAt": map_datetime(schedule.created_at),
        "updatedAt": map_datetime(schedule.updated_at),
    }


def map_event_type(event_type: EventType) -> dict[str, object]:
    return drop_none(
        {
            "id": event_type.id,
            "ownerId": event_type.owner_id,
            "title": event_type.title,
            "slug": event_type.slug,
            "description": event_type.description,
            "durationMinutes": event_type.duration_minutes,
            "scheduleId": event_type.schedule_id,
            "slotIntervalMinutes": event_type.slot_interval_minutes,
            "minimumBookingNoticeMinutes": event_type.minimum_booking_notice_minutes,
            "beforeEventBufferMinutes": event_type.before_event_buffer_minutes,
            "afterEventBufferMinutes": event_type.after_event_buffer_minutes,
            "bookingWindow": load_json(event_type.booking_window_json, None),
            "confirmationPolicy": {
                "type": event_type.confirmation_policy_type,
                "blockSlotBeforeConfirmation": event_type.block_slot_before_confirmation,
            },
            "hidden": event_type.hidden,
            "bookingUrl": booking_url(event_type.owner.username, event_type.slug),
            "createdAt": map_datetime(event_type.created_at),
            "updatedAt": map_datetime(event_type.updated_at),
        }
    )


def map_public_event_type(event_type: EventType) -> dict[str, object]:
    return drop_none(
        {
            "id": event_type.id,
            "owner": map_public_user(event_type.owner),
            "title": event_type.title,
            "slug": event_type.slug,
            "description": event_type.description,
            "durationMinutes": event_type.duration_minutes,
            "slotIntervalMinutes": event_type.slot_interval_minutes,
            "minimumBookingNoticeMinutes": event_type.minimum_booking_notice_minutes,
            "confirmationPolicy": {
                "type": event_type.confirmation_policy_type,
                "blockSlotBeforeConfirmation": event_type.block_slot_before_confirmation,
            },
            "bookingUrl": booking_url(event_type.owner.username, event_type.slug),
        }
    )


def map_share_link(link: ShareLink) -> dict[str, object]:
    return drop_none(
        {
            "id": link.id,
            "eventTypeId": link.event_type_id,
            "token": link.token,
            "bookingUrl": booking_url(link.event_type.owner.username, link.event_type.slug, link.token),
            "recipientEmail": link.recipient_email,
            "expiresAt": map_datetime(link.expires_at),
            "maxUsageCount": link.max_usage_count,
            "usageCount": link.usage_count,
            "isExpired": is_share_link_expired(link),
            "createdAt": map_datetime(link.created_at),
        }
    )


def map_public_share_link(link: ShareLink) -> dict[str, object]:
    remaining_usage_count = None
    if link.max_usage_count is not None:
        remaining_usage_count = max(link.max_usage_count - link.usage_count, 0)
    return drop_none(
        {
            "token": link.token,
            "eventType": map_public_event_type(link.event_type),
            "isExpired": is_share_link_expired(link),
            "expiresAt": map_datetime(link.expires_at),
            "remainingUsageCount": remaining_usage_count,
        }
    )


def map_booking(booking: Booking) -> dict[str, object]:
    return drop_none(
        {
            "id": booking.id,
            "uid": booking.uid,
            "eventTypeId": booking.event_type_id,
            "owner": map_public_user(booking.owner),
            "title": booking.title,
            "description": booking.description,
            "status": booking.status,
            "start": map_datetime(booking.start),
            "end": map_datetime(booking.end),
            "durationMinutes": booking.duration_minutes,
            "attendee": drop_none(
                {
                    "name": booking.attendee_name,
                    "email": booking.attendee_email,
                    "timeZone": booking.attendee_time_zone,
                    "confirmedAt": map_datetime(booking.attendee_confirmed_at),
                }
            ),
            "shareToken": booking.share_token,
            "meetingUrl": booking.meeting_url,
            "cancellationReason": booking.cancellation_reason,
            "rejectionReason": booking.rejection_reason,
            "createdAt": map_datetime(booking.created_at),
            "updatedAt": map_datetime(booking.updated_at),
        }
    )


def map_booking_with_manage_token(booking: Booking) -> dict[str, object]:
    return {**map_booking(booking), "manageToken": booking.attendee_token}
