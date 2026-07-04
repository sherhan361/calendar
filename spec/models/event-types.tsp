namespace Calendar;

enum ConfirmationPolicyType {
  automatic: "automatic",
  host: "host",
  attendee: "attendee",
}

model ConfirmationPolicy {
  type: ConfirmationPolicyType;
  blockSlotBeforeConfirmation?: boolean;
}

model BookingWindow {
  rollingDays?: int32;
  dateFrom?: LocalDate;
  dateTo?: LocalDate;
}

model EventType {
  id: Uuid;
  ownerId: Uuid;
  title: string;
  slug: Slug;
  description?: string;
  durationMinutes: int32;
  scheduleId: Uuid;
  slotIntervalMinutes?: int32;
  minimumBookingNoticeMinutes?: int32;
  beforeEventBufferMinutes?: int32;
  afterEventBufferMinutes?: int32;
  bookingWindow?: BookingWindow;
  confirmationPolicy: ConfirmationPolicy;
  hidden: boolean;
  bookingUrl: string;
  createdAt: utcDateTime;
  updatedAt: utcDateTime;
}

model PublicEventType {
  id: Uuid;
  owner: PublicUser;
  title: string;
  slug: Slug;
  description?: string;
  durationMinutes: int32;
  slotIntervalMinutes?: int32;
  minimumBookingNoticeMinutes?: int32;
  confirmationPolicy: ConfirmationPolicy;
  bookingUrl: string;
}

model CreateEventTypeRequest {
  title: string;
  slug: Slug;
  description?: string;
  durationMinutes: int32;
  scheduleId?: Uuid;
  slotIntervalMinutes?: int32;
  minimumBookingNoticeMinutes?: int32;
  beforeEventBufferMinutes?: int32;
  afterEventBufferMinutes?: int32;
  bookingWindow?: BookingWindow;
  confirmationPolicy?: ConfirmationPolicy;
  hidden?: boolean;
}

model UpdateEventTypeRequest {
  title?: string;
  slug?: Slug;
  description?: string;
  durationMinutes?: int32;
  scheduleId?: Uuid;
  slotIntervalMinutes?: int32;
  minimumBookingNoticeMinutes?: int32;
  beforeEventBufferMinutes?: int32;
  afterEventBufferMinutes?: int32;
  bookingWindow?: BookingWindow;
  confirmationPolicy?: ConfirmationPolicy;
  hidden?: boolean;
}
