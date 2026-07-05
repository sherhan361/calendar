namespace Calendar;

enum BookingStatus {
  pendingHost: "pending_host",
  pendingAttendee: "pending_attendee",
  confirmed: "confirmed",
  declined: "declined",
  cancelled: "cancelled",
}

model BookingAttendeeInput {
  @minLength(1)
  @maxLength(255)
  name: string;

  email: Email;
  timeZone: TimeZone;
}

model BookingAttendee {
  name: string;
  email: Email;
  timeZone: TimeZone;
  confirmedAt?: utcDateTime;
}

model Booking {
  id: Uuid;
  uid: string;
  eventTypeId: Uuid;
  owner: PublicUser;
  title: string;
  description?: string;
  status: BookingStatus;
  start: utcDateTime;
  end: utcDateTime;
  durationMinutes: int32;
  attendee: BookingAttendee;
  shareToken?: PublicToken;
  meetingUrl?: string;
  cancellationReason?: string;
  rejectionReason?: string;
  createdAt: utcDateTime;
  updatedAt: utcDateTime;
}

model CreateBookingRequest {
  eventTypeId?: Uuid;
  username?: Username;
  eventTypeSlug?: Slug;
  shareToken?: PublicToken;
  start: utcDateTime;
  durationMinutes?: int32;
  idempotencyKey?: IdempotencyKey;
  attendee: BookingAttendeeInput;
}

model BookingActionRequest {
  reason?: string;
}
