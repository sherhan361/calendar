from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.db.models import Booking, EventType, Schedule, ShareLink, User
from app.services.calendar import booking_url, dumps_json, prepare_availability

DEFAULT_AVAILABILITY: list[dict[str, str | list[str]]] = [
    {"days": ["monday"], "startTime": "09:00", "endTime": "17:00"}
]


def create_user(
    db: Session,
    *,
    email: str = "host@example.com",
    username: str = "hostuser",
    name: str = "Host User",
    time_zone: str = "UTC",
) -> User:
    user = User(
        email=email,
        username=username,
        name=name,
        time_zone=time_zone,
        password_hash="pbkdf2_sha256$1$salt$digest",
    )
    db.add(user)
    db.flush()
    return user


def create_schedule(
    db: Session,
    owner: User,
    *,
    name: str = "Working hours",
    time_zone: str = "UTC",
    is_default: bool = True,
    availability: list[dict[str, object]] | None = None,
    make_default: bool = True,
) -> Schedule:
    schedule = Schedule(
        owner_id=owner.id,
        name=name,
        time_zone=time_zone,
        is_default=is_default,
        availability_json=dumps_json(
            prepare_availability(availability if availability is not None else DEFAULT_AVAILABILITY)
        ),
        overrides_json="[]",
    )
    db.add(schedule)
    db.flush()
    if make_default:
        owner.default_schedule_id = schedule.id
    return schedule


def create_event_type(
    db: Session,
    owner: User,
    schedule: Schedule,
    *,
    title: str = "Discovery call",
    slug: str = "discovery-call",
    description: str | None = None,
    duration_minutes: int = 30,
    slot_interval_minutes: int | None = 30,
    confirmation_policy_type: str = "automatic",
    block_slot_before_confirmation: bool = False,
    hidden: bool = False,
) -> EventType:
    event_type = EventType(
        owner_id=owner.id,
        schedule_id=schedule.id,
        title=title,
        slug=slug,
        description=description,
        duration_minutes=duration_minutes,
        slot_interval_minutes=slot_interval_minutes,
        minimum_booking_notice_minutes=None,
        before_event_buffer_minutes=None,
        after_event_buffer_minutes=None,
        booking_window_json=None,
        confirmation_policy_type=confirmation_policy_type,
        block_slot_before_confirmation=block_slot_before_confirmation,
        hidden=hidden,
        booking_url=booking_url(owner.username, slug),
    )
    db.add(event_type)
    db.flush()
    return event_type


def create_public_event_type(
    db: Session,
    *,
    duration_minutes: int = 30,
    slot_interval_minutes: int | None = 30,
    confirmation_policy_type: str = "automatic",
) -> EventType:
    """Собрать owner + schedule + видимый event type — самый частый seed для публичных сценариев."""
    owner = create_user(db)
    schedule = create_schedule(db, owner)
    event_type = create_event_type(
        db,
        owner,
        schedule,
        duration_minutes=duration_minutes,
        slot_interval_minutes=slot_interval_minutes,
        confirmation_policy_type=confirmation_policy_type,
    )
    db.commit()
    db.refresh(event_type)
    return event_type


def create_booking(
    db: Session,
    event_type: EventType,
    *,
    uid: str,
    status: str = "confirmed",
    start: datetime | None = None,
    duration_minutes: int | None = None,
    attendee_email: str = "attendee@example.com",
    attendee_token: str | None = None,
    commit: bool = True,
) -> Booking:
    start = start or datetime(2099, 1, 5, 9, tzinfo=timezone.utc)
    minutes = duration_minutes if duration_minutes is not None else event_type.duration_minutes
    booking = Booking(
        uid=uid,
        event_type_id=event_type.id,
        owner_id=event_type.owner_id,
        title=event_type.title,
        description=None,
        status=status,
        start=start,
        end=start + timedelta(minutes=minutes),
        duration_minutes=minutes,
        attendee_name="Attendee",
        attendee_email=attendee_email,
        attendee_time_zone="UTC",
        attendee_token=attendee_token or f"token_{uid}",
    )
    db.add(booking)
    if commit:
        db.commit()
    return booking


def create_share_link(
    db: Session,
    event_type: EventType,
    owner: User,
    *,
    token: str,
    expires_at: datetime | None = None,
    max_usage_count: int | None = 5,
    commit: bool = True,
) -> ShareLink:
    share_link = ShareLink(
        event_type_id=event_type.id,
        token=token,
        booking_url=booking_url(owner.username, event_type.slug, token),
        recipient_email=None,
        expires_at=expires_at or datetime(2099, 1, 1, tzinfo=timezone.utc),
        max_usage_count=max_usage_count,
        usage_count=0,
    )
    db.add(share_link)
    if commit:
        db.commit()
    return share_link
