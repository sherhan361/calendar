export type ApiSuccess<T> = {
  status: "success";
  data: T;
};

export type ApiError = {
  status: "error";
  error: {
    code: string;
    message: string;
  };
};

export type User = {
  id: string;
  email: string;
  username: string;
  name: string;
  avatarUrl?: string | null;
  timeZone: string;
  defaultScheduleId?: string | null;
};

export type PublicUser = Pick<User, "id" | "username" | "name" | "avatarUrl" | "timeZone">;

export type Weekday =
  | "monday"
  | "tuesday"
  | "wednesday"
  | "thursday"
  | "friday"
  | "saturday"
  | "sunday";

export type AvailabilityRule = {
  id?: string;
  days: Weekday[];
  startTime: string;
  endTime: string;
};

export type Schedule = {
  id: string;
  ownerId: string;
  name: string;
  timeZone: string;
  isDefault: boolean;
  availability: AvailabilityRule[];
};

export type ConfirmationPolicyType = "automatic" | "host" | "attendee";

export type ConfirmationPolicy = {
  type: ConfirmationPolicyType;
  blockSlotBeforeConfirmation?: boolean;
};

export type EventType = {
  id: string;
  ownerId: string;
  title: string;
  slug: string;
  description?: string | null;
  durationMinutes: number;
  scheduleId: string;
  slotIntervalMinutes?: number | null;
  minimumBookingNoticeMinutes?: number | null;
  afterEventBufferMinutes?: number | null;
  confirmationPolicy: ConfirmationPolicy;
  hidden: boolean;
  bookingUrl: string;
};

export type PublicEventType = {
  id: string;
  owner: PublicUser;
  title: string;
  slug: string;
  description?: string | null;
  durationMinutes: number;
  slotIntervalMinutes?: number | null;
  minimumBookingNoticeMinutes?: number | null;
  confirmationPolicy: ConfirmationPolicy;
  bookingUrl: string;
};

export type ShareLink = {
  id: string;
  eventTypeId: string;
  token: string;
  bookingUrl: string;
  recipientEmail?: string | null;
  expiresAt?: string | null;
  maxUsageCount?: number | null;
  usageCount: number;
  isExpired: boolean;
};

export type Slot = {
  start: string;
  end: string;
  available: boolean;
};

export type SlotsResponse = {
  timeZone: string;
  days: Array<{
    date: string;
    slots: Slot[];
  }>;
};

export type BookingStatus = "pending_host" | "pending_attendee" | "confirmed" | "declined" | "cancelled";

export type Booking = {
  id: string;
  uid: string;
  eventTypeId: string;
  owner: PublicUser;
  title: string;
  description?: string | null;
  status: BookingStatus;
  start: string;
  end: string;
  durationMinutes: number;
  attendee: {
    name: string;
    email: string;
    timeZone: string;
    confirmedAt?: string | null;
  };
};

export type ListResponse<T> = {
  items: T[];
};
