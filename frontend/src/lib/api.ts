import type {
  ApiError,
  ApiSuccess,
  AvailabilityRule,
  Booking,
  BookingStatus,
  ConfirmationPolicyType,
  EventType,
  ListResponse,
  PublicEventType,
  PublicShareLink,
  Schedule,
  ShareLink,
  SlotsResponse,
  User,
} from "./types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export type LoginResponse = {
  accessToken: string;
  tokenType: "Bearer";
  user: User;
};

export type RegisterInput = {
  email: string;
  username: string;
  name: string;
  password: string;
  timeZone: string;
};

export type EventTypeInput = {
  title: string;
  slug: string;
  description?: string;
  durationMinutes: number;
  scheduleId?: string;
  slotIntervalMinutes?: number;
  minimumBookingNoticeMinutes?: number;
  beforeEventBufferMinutes?: number;
  afterEventBufferMinutes?: number;
  bookingWindow?: {
    rollingDays?: number;
    dateFrom?: string;
    dateTo?: string;
  };
  confirmationPolicy?: {
    type: ConfirmationPolicyType;
    blockSlotBeforeConfirmation?: boolean;
  };
  hidden?: boolean;
};

export type CreateBookingInput = {
  username: string;
  eventTypeSlug: string;
  shareToken?: string;
  start: string;
  durationMinutes: number;
  attendee: {
    name: string;
    email: string;
    timeZone: string;
  };
};

export const api = {
  register: (payload: RegisterInput) =>
    request<LoginResponse>("/auth/register", {
      method: "POST",
      body: payload,
    }),

  login: (email: string, password: string) =>
    request<LoginResponse>("/auth/login", {
      method: "POST",
      body: { email, password },
    }),

  logout: (token: string) =>
    request<void>("/auth/logout", {
      method: "POST",
      token,
    }),

  me: (token: string) => request<User>("/me", { token }),

  listSchedules: (token: string) => request<ListResponse<Schedule>>("/schedules", { token }),

  updateSchedule: (token: string, scheduleId: string, payload: { availability: AvailabilityRule[] }) =>
    request<Schedule>(`/schedules/${scheduleId}`, {
      method: "PATCH",
      token,
      body: payload,
    }),

  listEventTypes: (token: string) => request<ListResponse<EventType>>("/event-types?includeHidden=true", { token }),

  createEventType: (token: string, payload: EventTypeInput) =>
    request<EventType>("/event-types", {
      method: "POST",
      token,
      body: payload,
    }),

  updateEventType: (token: string, eventTypeId: string, payload: Partial<EventTypeInput & { hidden?: boolean }>) =>
    request<EventType>(`/event-types/${eventTypeId}`, {
      method: "PATCH",
      token,
      body: payload,
    }),

  createShareLink: (token: string, eventTypeId: string, recipientEmail?: string) =>
    request<ShareLink>(`/event-types/${eventTypeId}/share-links`, {
      method: "POST",
      token,
      body: { recipientEmail, maxUsageCount: 5 },
    }),

  listShareLinks: (token: string, eventTypeId: string) =>
    request<ListResponse<ShareLink>>(`/event-types/${eventTypeId}/share-links`, { token }),

  getPublicShareLink: (token: string) => request<PublicShareLink>(`/public/share-links/${token}`),

  listBookings: (token: string, status?: BookingStatus) => {
    const query = status ? `?status=${status}` : "";
    return request<ListResponse<Booking>>(`/bookings${query}`, { token });
  },

  confirmBooking: (token: string, uid: string) =>
    request<Booking>(`/bookings/${uid}/confirm`, {
      method: "POST",
      token,
    }),

  declineBooking: (token: string, uid: string, reason?: string) =>
    request<Booking>(`/bookings/${uid}/decline`, {
      method: "POST",
      token,
      body: { reason },
    }),

  cancelBooking: (token: string, uid: string, reason?: string) =>
    request<Booking>(`/bookings/${uid}/cancel`, {
      method: "POST",
      token,
      body: { reason },
    }),

  getPublicEventType: (username: string, slug: string, shareToken?: string) => {
    const query = shareToken ? `?shareToken=${shareToken}` : "";
    return request<PublicEventType>(`/public/users/${username}/event-types/${slug}${query}`);
  },

  getPublicSlots: (params: {
    username: string;
    eventTypeSlug: string;
    start: string;
    end: string;
    timeZone: string;
    durationMinutes: number;
    shareToken?: string;
  }) => {
    const search = new URLSearchParams({
      username: params.username,
      eventTypeSlug: params.eventTypeSlug,
      start: params.start,
      end: params.end,
      timeZone: params.timeZone,
      durationMinutes: String(params.durationMinutes),
    });
    if (params.shareToken) search.set("shareToken", params.shareToken);
    return request<SlotsResponse>(`/public/slots?${search.toString()}`);
  },

  createBooking: (payload: CreateBookingInput) =>
    request<Booking>("/bookings", {
      method: "POST",
      body: payload,
    }),
};

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  token?: string;
  body?: unknown;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    method: options.method ?? "GET",
    headers: {
      "content-type": "application/json",
      ...(options.token ? { authorization: `Bearer ${options.token}` } : {}),
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (response.status === 204) return undefined as T;

  const payload = (await response.json()) as ApiSuccess<T> | ApiError;
  if (!response.ok || payload.status === "error") {
    throw new Error(payload.status === "error" ? payload.error.message : "Request failed");
  }

  return payload.data;
}
