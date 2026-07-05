from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.domain.calendar import ACTIVE_BOOKING_STATUSES

ACTIVE_BOOKING_SLOT_PREDICATE = "status IN ({})".format(
    ", ".join(f"'{status}'" for status in sorted(ACTIVE_BOOKING_STATUSES))
)


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(2048))
    time_zone: Mapped[str] = mapped_column(String(128), default="Europe/Moscow", nullable=False)
    default_schedule_id: Mapped[str | None] = mapped_column(String(36))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    schedules: Mapped[list["Schedule"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    event_types: Mapped[list["EventType"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    owner_bookings: Mapped[list["Booking"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class Schedule(TimestampMixin, Base):
    __tablename__ = "schedules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    time_zone: Mapped[str] = mapped_column(String(128), default="Europe/Moscow", nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    availability_json: Mapped[str] = mapped_column(Text, nullable=False)
    overrides_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)

    owner: Mapped[User] = relationship(back_populates="schedules")
    event_types: Mapped[list["EventType"]] = relationship(back_populates="schedule")

    __table_args__ = (Index("ix_schedules_owner_id", "owner_id"),)


class EventType(TimestampMixin, Base):
    __tablename__ = "event_types"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    schedule_id: Mapped[str] = mapped_column(ForeignKey("schedules.id", ondelete="RESTRICT"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    slot_interval_minutes: Mapped[int | None] = mapped_column(Integer)
    minimum_booking_notice_minutes: Mapped[int | None] = mapped_column(Integer)
    before_event_buffer_minutes: Mapped[int | None] = mapped_column(Integer)
    after_event_buffer_minutes: Mapped[int | None] = mapped_column(Integer)
    booking_window_json: Mapped[str | None] = mapped_column(Text)
    confirmation_policy_type: Mapped[str] = mapped_column(String(32), default="automatic", nullable=False)
    block_slot_before_confirmation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    booking_url: Mapped[str] = mapped_column(String(512), nullable=False)

    owner: Mapped[User] = relationship(back_populates="event_types")
    schedule: Mapped[Schedule] = relationship(back_populates="event_types")
    share_links: Mapped[list["ShareLink"]] = relationship(back_populates="event_type", cascade="all, delete-orphan")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="event_type", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("owner_id", "slug", name="uq_event_types_owner_slug"),
        CheckConstraint("duration_minutes > 0", name="ck_event_types_duration_positive"),
        CheckConstraint(
            "slot_interval_minutes IS NULL OR slot_interval_minutes > 0",
            name="ck_event_types_slot_interval_positive",
        ),
        CheckConstraint(
            "minimum_booking_notice_minutes IS NULL OR minimum_booking_notice_minutes >= 0",
            name="ck_event_types_minimum_notice_non_negative",
        ),
        CheckConstraint(
            "before_event_buffer_minutes IS NULL OR before_event_buffer_minutes >= 0",
            name="ck_event_types_before_buffer_non_negative",
        ),
        CheckConstraint(
            "after_event_buffer_minutes IS NULL OR after_event_buffer_minutes >= 0",
            name="ck_event_types_after_buffer_non_negative",
        ),
        CheckConstraint(
            "confirmation_policy_type IN ('automatic', 'host', 'attendee')",
            name="ck_event_types_confirmation_policy",
        ),
        Index("ix_event_types_schedule_id", "schedule_id"),
    )


class ShareLink(Base):
    __tablename__ = "share_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    event_type_id: Mapped[str] = mapped_column(ForeignKey("event_types.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    booking_url: Mapped[str] = mapped_column(String(512), nullable=False)
    recipient_email: Mapped[str | None] = mapped_column(String(320))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    max_usage_count: Mapped[int | None] = mapped_column(Integer)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    event_type: Mapped[EventType] = relationship(back_populates="share_links")

    __table_args__ = (
        CheckConstraint("max_usage_count IS NULL OR max_usage_count > 0", name="ck_share_links_max_usage_positive"),
        CheckConstraint("usage_count >= 0", name="ck_share_links_usage_non_negative"),
        Index("ix_share_links_event_type_id", "event_type_id"),
    )


class Booking(TimestampMixin, Base):
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    uid: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    event_type_id: Mapped[str] = mapped_column(ForeignKey("event_types.id", ondelete="CASCADE"), nullable=False)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    attendee_name: Mapped[str] = mapped_column(String(255), nullable=False)
    attendee_email: Mapped[str] = mapped_column(String(320), nullable=False)
    attendee_time_zone: Mapped[str] = mapped_column(String(128), nullable=False)
    attendee_token: Mapped[str] = mapped_column(String(128), nullable=False)
    attendee_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    idempotency_key: Mapped[str | None] = mapped_column(String(128))
    share_token: Mapped[str | None] = mapped_column(String(128))
    meeting_url: Mapped[str | None] = mapped_column(String(2048))
    cancellation_reason: Mapped[str | None] = mapped_column(Text)
    rejection_reason: Mapped[str | None] = mapped_column(Text)

    event_type: Mapped[EventType] = relationship(back_populates="bookings")
    owner: Mapped[User] = relationship(back_populates="owner_bookings")

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending_host', 'pending_attendee', 'confirmed', 'declined', 'cancelled')",
            name="ck_bookings_status",
        ),
        CheckConstraint("duration_minutes > 0", name="ck_bookings_duration_positive"),
        Index("ix_bookings_owner_status", "owner_id", "status"),
        Index("ix_bookings_event_type_start", "event_type_id", "start"),
        Index("uq_bookings_event_type_idempotency_key", "event_type_id", "idempotency_key", unique=True),
        Index(
            "uq_bookings_active_slot",
            "event_type_id",
            "start",
            unique=True,
            sqlite_where=text(ACTIVE_BOOKING_SLOT_PREDICATE),
            postgresql_where=text(ACTIVE_BOOKING_SLOT_PREDICATE),
        ),
    )
