from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, EmailStr, Field


Uuid = Annotated[str, Field(pattern=r"^[0-9a-fA-F-]{36}$")]
LocalDate = Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")]
LocalTime = Annotated[str, Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")]
Slug = Annotated[str, Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]
PublicToken = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{16,128}$")]
IdempotencyKey = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{8,128}$")]
Username = Annotated[str, Field(pattern=r"^[A-Za-z][A-Za-z0-9_-]{2,31}$")]
TimeZone = str

T = TypeVar("T")


class ApiSuccess(BaseModel, Generic[T]):
    status: str = "success"
    data: T


class ApiList(BaseModel, Generic[T]):
    items: list[T]


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str


class ApiErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] | None = None


class ApiError(BaseModel):
    status: str = "error"
    error: ApiErrorBody


class Weekday(StrEnum):
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    sunday = "sunday"


class ConfirmationPolicyType(StrEnum):
    automatic = "automatic"
    host = "host"
    attendee = "attendee"


class BookingStatus(StrEnum):
    pending_host = "pending_host"
    pending_attendee = "pending_attendee"
    confirmed = "confirmed"
    declined = "declined"
    cancelled = "cancelled"


class User(BaseModel):
    id: Uuid
    email: EmailStr
    username: Username
    name: str
    avatarUrl: str | None = None
    timeZone: TimeZone
    defaultScheduleId: Uuid | None = None
    createdAt: datetime
    updatedAt: datetime


class PublicUser(BaseModel):
    id: Uuid
    username: Username
    name: str
    avatarUrl: str | None = None
    timeZone: TimeZone


class RegisterRequest(BaseModel):
    email: EmailStr
    username: Username
    name: str
    password: str
    timeZone: TimeZone


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthSession(BaseModel):
    accessToken: str
    tokenType: str = "Bearer"
    user: User


class UpdateMeRequest(BaseModel):
    email: EmailStr | None = None
    username: Username | None = None
    name: str | None = None
    avatarUrl: str | None = None
    timeZone: TimeZone | None = None


class AvailabilityRule(BaseModel):
    id: Uuid
    days: list[Weekday]
    startTime: LocalTime
    endTime: LocalTime


class AvailabilityRuleInput(BaseModel):
    days: list[Weekday]
    startTime: LocalTime
    endTime: LocalTime


class AvailabilityOverride(BaseModel):
    id: Uuid
    date: LocalDate
    startTime: LocalTime | None = None
    endTime: LocalTime | None = None
    unavailable: bool


class AvailabilityOverrideInput(BaseModel):
    date: LocalDate
    startTime: LocalTime | None = None
    endTime: LocalTime | None = None
    unavailable: bool | None = None


class Schedule(BaseModel):
    id: Uuid
    ownerId: Uuid
    name: str
    timeZone: TimeZone
    isDefault: bool
    availability: list[AvailabilityRule]
    overrides: list[AvailabilityOverride]
    createdAt: datetime
    updatedAt: datetime


class CreateScheduleRequest(BaseModel):
    name: str
    timeZone: TimeZone
    isDefault: bool | None = None
    availability: list[AvailabilityRuleInput]
    overrides: list[AvailabilityOverrideInput] | None = None


class UpdateScheduleRequest(BaseModel):
    name: str | None = None
    timeZone: TimeZone | None = None
    isDefault: bool | None = None
    availability: list[AvailabilityRuleInput] | None = None
    overrides: list[AvailabilityOverrideInput] | None = None


class ConfirmationPolicy(BaseModel):
    type: ConfirmationPolicyType
    blockSlotBeforeConfirmation: bool | None = None


class BookingWindow(BaseModel):
    rollingDays: int | None = None
    dateFrom: LocalDate | None = None
    dateTo: LocalDate | None = None


class EventType(BaseModel):
    id: Uuid
    ownerId: Uuid
    title: str
    slug: Slug
    description: str | None = None
    durationMinutes: int
    scheduleId: Uuid
    slotIntervalMinutes: int | None = None
    minimumBookingNoticeMinutes: int | None = None
    beforeEventBufferMinutes: int | None = None
    afterEventBufferMinutes: int | None = None
    bookingWindow: BookingWindow | None = None
    confirmationPolicy: ConfirmationPolicy
    hidden: bool
    bookingUrl: str
    createdAt: datetime
    updatedAt: datetime


class PublicEventType(BaseModel):
    id: Uuid
    owner: PublicUser
    title: str
    slug: Slug
    description: str | None = None
    durationMinutes: int
    slotIntervalMinutes: int | None = None
    minimumBookingNoticeMinutes: int | None = None
    confirmationPolicy: ConfirmationPolicy
    bookingUrl: str


class CreateEventTypeRequest(BaseModel):
    title: str
    slug: Slug
    description: str | None = None
    durationMinutes: int
    scheduleId: Uuid | None = None
    slotIntervalMinutes: int | None = None
    minimumBookingNoticeMinutes: int | None = None
    beforeEventBufferMinutes: int | None = None
    afterEventBufferMinutes: int | None = None
    bookingWindow: BookingWindow | None = None
    confirmationPolicy: ConfirmationPolicy | None = None
    hidden: bool | None = None


class UpdateEventTypeRequest(BaseModel):
    title: str | None = None
    slug: Slug | None = None
    description: str | None = None
    durationMinutes: int | None = None
    scheduleId: Uuid | None = None
    slotIntervalMinutes: int | None = None
    minimumBookingNoticeMinutes: int | None = None
    beforeEventBufferMinutes: int | None = None
    afterEventBufferMinutes: int | None = None
    bookingWindow: BookingWindow | None = None
    confirmationPolicy: ConfirmationPolicy | None = None
    hidden: bool | None = None


class ShareLink(BaseModel):
    id: Uuid
    eventTypeId: Uuid
    token: PublicToken
    bookingUrl: str
    recipientEmail: EmailStr | None = None
    expiresAt: datetime | None = None
    maxUsageCount: int | None = None
    usageCount: int
    isExpired: bool
    createdAt: datetime


class CreateShareLinkRequest(BaseModel):
    recipientEmail: EmailStr | None = None
    expiresAt: datetime | None = None
    maxUsageCount: int | None = None


class PublicShareLink(BaseModel):
    token: PublicToken
    eventType: PublicEventType
    isExpired: bool
    expiresAt: datetime | None = None
    remainingUsageCount: int | None = None


class Slot(BaseModel):
    start: datetime
    end: datetime
    available: bool


class SlotsByDate(BaseModel):
    date: LocalDate
    slots: list[Slot]


class SlotsResponse(BaseModel):
    timeZone: TimeZone
    days: list[SlotsByDate]


class BookingAttendeeInput(BaseModel):
    name: str
    email: EmailStr
    timeZone: TimeZone


class BookingAttendee(BaseModel):
    name: str
    email: EmailStr
    timeZone: TimeZone
    confirmedAt: datetime | None = None


class Booking(BaseModel):
    id: Uuid
    uid: str
    eventTypeId: Uuid
    owner: PublicUser
    title: str
    description: str | None = None
    status: BookingStatus
    start: datetime
    end: datetime
    durationMinutes: int
    attendee: BookingAttendee
    shareToken: PublicToken | None = None
    meetingUrl: str | None = None
    cancellationReason: str | None = None
    rejectionReason: str | None = None
    createdAt: datetime
    updatedAt: datetime


class CreateBookingRequest(BaseModel):
    eventTypeId: Uuid | None = None
    username: Username | None = None
    eventTypeSlug: Slug | None = None
    shareToken: PublicToken | None = None
    start: datetime
    durationMinutes: int | None = None
    idempotencyKey: IdempotencyKey | None = None
    attendee: BookingAttendeeInput


class BookingActionRequest(BaseModel):
    reason: str | None = None
