import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import { api } from "./api";
import type {
  AvailabilityRule,
  Booking,
  BookingStatus,
  EventType,
  PublicEventType,
  Schedule,
  Slot,
  User,
  Weekday,
} from "./types";

const weekdays: Weekday[] = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];
const weekdayLabels: Record<Weekday, string> = {
  monday: "Mon",
  tuesday: "Tue",
  wednesday: "Wed",
  thursday: "Thu",
  friday: "Fri",
  saturday: "Sat",
  sunday: "Sun",
};

type AppRoute =
  | { kind: "app" }
  | {
      kind: "public-booking";
      username: string;
      slug: string;
      shareToken?: string;
    };

export default function App() {
  const [route, setRoute] = useState<AppRoute>(() => parseRoute());

  useEffect(() => {
    const onHashChange = () => setRoute(parseRoute());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  if (route.kind === "public-booking") {
    return <PublicBookingPage route={route} />;
  }

  return <PrivateApp />;
}

function PrivateApp() {
  const [token, setToken] = useState(() => localStorage.getItem("calendar:token") ?? "");
  const [user, setUser] = useState<User | null>(null);
  const [view, setView] = useState<"dashboard" | "availability" | "bookings">("dashboard");
  const [eventTypes, setEventTypes] = useState<EventType[]>([]);
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    void refreshWorkspace(token);
  }, [token]);

  async function refreshWorkspace(activeToken = token) {
    setLoading(true);
    setError("");
    try {
      const [nextUser, nextSchedules, nextEventTypes, nextBookings] = await Promise.all([
        api.me(activeToken),
        api.listSchedules(activeToken),
        api.listEventTypes(activeToken),
        api.listBookings(activeToken),
      ]);
      setUser(nextUser);
      setSchedules(nextSchedules.items);
      setEventTypes(nextEventTypes.items);
      setBookings(nextBookings.items);
    } catch (requestError) {
      setError(asErrorMessage(requestError));
      localStorage.removeItem("calendar:token");
      setToken("");
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  async function handleLogin(email: string, password: string) {
    setLoading(true);
    setError("");
    try {
      const session = await api.login(email, password);
      localStorage.setItem("calendar:token", session.accessToken);
      setToken(session.accessToken);
      setUser(session.user);
      await refreshWorkspace(session.accessToken);
    } catch (requestError) {
      setError(asErrorMessage(requestError));
    } finally {
      setLoading(false);
    }
  }

  function handleLogout() {
    localStorage.removeItem("calendar:token");
    setToken("");
    setUser(null);
    setEventTypes([]);
    setSchedules([]);
    setBookings([]);
  }

  if (!token || !user) {
    return <LoginScreen loading={loading} error={error} onLogin={handleLogin} />;
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#">
          <span className="brand-mark">C</span>
          <span>Calendar</span>
        </a>
        <nav className="nav-list">
          <button className={view === "dashboard" ? "active" : ""} onClick={() => setView("dashboard")}>
            Event types
          </button>
          <button className={view === "availability" ? "active" : ""} onClick={() => setView("availability")}>
            Availability
          </button>
          <button className={view === "bookings" ? "active" : ""} onClick={() => setView("bookings")}>
            Bookings
          </button>
        </nav>
        <div className="sidebar-footer">
          <div className="avatar">{initials(user.name)}</div>
          <div>
            <strong>{user.name}</strong>
            <span>{user.email}</span>
          </div>
        </div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Mock workspace</p>
            <h1>{viewTitle(view)}</h1>
          </div>
          <div className="topbar-actions">
            {loading ? <span className="muted">Syncing...</span> : null}
            <button className="ghost-button" onClick={() => void refreshWorkspace()}>
              Refresh
            </button>
            <button className="ghost-button" onClick={handleLogout}>
              Logout
            </button>
          </div>
        </header>

        {error ? <div className="banner error">{error}</div> : null}

        {view === "dashboard" ? (
          <Dashboard
            token={token}
            user={user}
            schedules={schedules}
            eventTypes={eventTypes}
            bookings={bookings}
            onChanged={() => void refreshWorkspace()}
          />
        ) : null}

        {view === "availability" ? (
          <AvailabilityEditor token={token} schedules={schedules} onChanged={() => void refreshWorkspace()} />
        ) : null}

        {view === "bookings" ? (
          <BookingsQueue token={token} bookings={bookings} onChanged={() => void refreshWorkspace()} />
        ) : null}
      </main>
    </div>
  );
}

function LoginScreen({
  loading,
  error,
  onLogin,
}: {
  loading: boolean;
  error: string;
  onLogin: (email: string, password: string) => Promise<void>;
}) {
  const [email, setEmail] = useState("demo@example.com");
  const [password, setPassword] = useState("demo");

  async function submit(event: FormEvent) {
    event.preventDefault();
    await onLogin(email, password);
  }

  return (
    <main className="login-page">
      <section className="login-panel">
        <div className="brand large">
          <span className="brand-mark">C</span>
          <span>Calendar</span>
        </div>
        <div>
          <p className="eyebrow">Prisma mock backend</p>
          <h1>Sign in to manage your booking links</h1>
          <p className="muted">Demo user is prefilled from the seeded SQLite database.</p>
        </div>
        {error ? <div className="banner error">{error}</div> : null}
        <form className="stack" onSubmit={submit}>
          <label>
            Email
            <input value={email} onChange={(event) => setEmail(event.target.value)} />
          </label>
          <label>
            Password
            <input value={password} type="password" onChange={(event) => setPassword(event.target.value)} />
          </label>
          <button className="primary-button" disabled={loading}>
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}

function Dashboard({
  token,
  user,
  schedules,
  eventTypes,
  bookings,
  onChanged,
}: {
  token: string;
  user: User;
  schedules: Schedule[];
  eventTypes: EventType[];
  bookings: Booking[];
  onChanged: () => void;
}) {
  const pendingCount = bookings.filter((booking) => booking.status === "pending_host").length;
  const confirmedCount = bookings.filter((booking) => booking.status === "confirmed").length;

  return (
    <div className="content-grid">
      <section className="main-column">
        <div className="metric-row">
          <Metric label="Event types" value={eventTypes.length} />
          <Metric label="Pending" value={pendingCount} />
          <Metric label="Confirmed" value={confirmedCount} />
        </div>

        <section className="section-block">
          <div className="section-heading">
            <div>
              <h2>Event types</h2>
              <p className="muted">Share booking links backed by the local Prisma mock API.</p>
            </div>
          </div>
          <div className="event-grid">
            {eventTypes.map((eventType) => (
              <EventTypeCard key={eventType.id} token={token} user={user} eventType={eventType} onChanged={onChanged} />
            ))}
          </div>
        </section>
      </section>

      <aside className="side-panel">
        <CreateEventTypeForm token={token} schedules={schedules} onCreated={onChanged} />
      </aside>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function EventTypeCard({
  token,
  user,
  eventType,
  onChanged,
}: {
  token: string;
  user: User;
  eventType: EventType;
  onChanged: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const publicPath = `#/book/${user.username}/${eventType.slug}`;
  const publicUrl = `${window.location.origin}/${publicPath}`;

  async function createLink() {
    setBusy(true);
    try {
      const link = await api.createShareLink(token, eventType.id);
      const url = `${window.location.origin}/#/book/${user.username}/${eventType.slug}?shareToken=${link.token}`;
      await copyText(url);
      onChanged();
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="event-card">
      <div>
        <div className="event-card-header">
          <h3>{eventType.title}</h3>
          <span className="status-pill">{eventType.confirmationPolicy.type}</span>
        </div>
        <p>{eventType.description || "No description"}</p>
      </div>
      <div className="event-meta">
        <span>{eventType.durationMinutes} min</span>
        <span>{eventType.slug}</span>
      </div>
      <div className="button-row">
        <a className="secondary-button" href={publicPath}>
          Open page
        </a>
        <button className="secondary-button" onClick={() => void copyText(publicUrl)}>
          Copy URL
        </button>
        <button className="secondary-button" onClick={() => void createLink()} disabled={busy}>
          {busy ? "Creating..." : "Private link"}
        </button>
      </div>
    </article>
  );
}

function CreateEventTypeForm({
  token,
  schedules,
  onCreated,
}: {
  token: string;
  schedules: Schedule[];
  onCreated: () => void;
}) {
  const [title, setTitle] = useState("Backend consultation");
  const [slug, setSlug] = useState("backend-consultation");
  const [duration, setDuration] = useState(45);
  const [policy, setPolicy] = useState<"automatic" | "host" | "attendee">("host");
  const [description, setDescription] = useState("Discuss architecture, API contracts, and delivery risks.");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      await api.createEventType(token, {
        title,
        slug,
        description,
        durationMinutes: duration,
        scheduleId: schedules[0]?.id,
        slotIntervalMinutes: 15,
        afterEventBufferMinutes: 15,
        confirmationPolicy: {
          type: policy,
          blockSlotBeforeConfirmation: policy !== "automatic",
        },
      });
      onCreated();
      setTitle("New consultation");
      setSlug(`new-consultation-${Date.now().toString().slice(-4)}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel">
      <h2>Create event type</h2>
      <form className="stack" onSubmit={submit}>
        <label>
          Title
          <input value={title} onChange={(event) => setTitle(event.target.value)} />
        </label>
        <label>
          Slug
          <input value={slug} onChange={(event) => setSlug(slugify(event.target.value))} />
        </label>
        <label>
          Duration, min
          <input value={duration} type="number" min={15} step={15} onChange={(event) => setDuration(Number(event.target.value))} />
        </label>
        <label>
          Confirmation
          <select value={policy} onChange={(event) => setPolicy(event.target.value as "automatic" | "host" | "attendee")}>
            <option value="automatic">Automatic</option>
            <option value="host">Host approval</option>
            <option value="attendee">Attendee approval</option>
          </select>
        </label>
        <label>
          Description
          <textarea value={description} rows={4} onChange={(event) => setDescription(event.target.value)} />
        </label>
        <button className="primary-button" disabled={busy || schedules.length === 0}>
          {busy ? "Creating..." : "Create event"}
        </button>
      </form>
    </section>
  );
}

function AvailabilityEditor({
  token,
  schedules,
  onChanged,
}: {
  token: string;
  schedules: Schedule[];
  onChanged: () => void;
}) {
  const schedule = schedules.find((item) => item.isDefault) ?? schedules[0];
  const [rules, setRules] = useState<AvailabilityRule[]>(schedule?.availability ?? []);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setRules(schedule?.availability ?? []);
  }, [schedule?.id]);

  if (!schedule) {
    return <div className="empty-state">No schedule found. Seed or create a schedule first.</div>;
  }

  function updateRule(index: number, patch: Partial<AvailabilityRule>) {
    setRules((current) => current.map((rule, ruleIndex) => (ruleIndex === index ? { ...rule, ...patch } : rule)));
  }

  function toggleDay(index: number, day: Weekday) {
    const rule = rules[index];
    const days = rule.days.includes(day) ? rule.days.filter((item) => item !== day) : [...rule.days, day];
    updateRule(index, { days });
  }

  async function save() {
    setBusy(true);
    try {
      await api.updateSchedule(token, schedule.id, { availability: rules });
      onChanged();
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="section-block">
      <div className="section-heading">
        <div>
          <h2>{schedule.name}</h2>
          <p className="muted">These rules are used by mock slots generation.</p>
        </div>
        <button className="primary-button" onClick={() => void save()} disabled={busy}>
          {busy ? "Saving..." : "Save availability"}
        </button>
      </div>

      <div className="availability-list">
        {rules.map((rule, index) => (
          <div className="availability-row" key={`${rule.startTime}-${rule.endTime}-${index}`}>
            <div className="weekday-list">
              {weekdays.map((day) => (
                <label className="weekday-check" key={day}>
                  <input checked={rule.days.includes(day)} type="checkbox" onChange={() => toggleDay(index, day)} />
                  <span>{weekdayLabels[day]}</span>
                </label>
              ))}
            </div>
            <input value={rule.startTime} type="time" onChange={(event) => updateRule(index, { startTime: event.target.value })} />
            <input value={rule.endTime} type="time" onChange={(event) => updateRule(index, { endTime: event.target.value })} />
            <button className="ghost-button" onClick={() => setRules((current) => current.filter((_, ruleIndex) => ruleIndex !== index))}>
              Remove
            </button>
          </div>
        ))}
      </div>

      <button
        className="secondary-button"
        onClick={() =>
          setRules((current) => [
            ...current,
            { days: ["monday", "tuesday", "wednesday", "thursday", "friday"], startTime: "10:00", endTime: "11:00" },
          ])
        }
      >
        Add interval
      </button>
    </section>
  );
}

function BookingsQueue({
  token,
  bookings,
  onChanged,
}: {
  token: string;
  bookings: Booking[];
  onChanged: () => void;
}) {
  const [filter, setFilter] = useState<BookingStatus | "all">("all");
  const visibleBookings = filter === "all" ? bookings : bookings.filter((booking) => booking.status === filter);

  async function action(uid: string, type: "confirm" | "decline" | "cancel") {
    if (type === "confirm") await api.confirmBooking(token, uid);
    if (type === "decline") await api.declineBooking(token, uid);
    if (type === "cancel") await api.cancelBooking(token, uid);
    onChanged();
  }

  return (
    <section className="section-block">
      <div className="section-heading">
        <div>
          <h2>Bookings</h2>
          <p className="muted">Host queue from the Prisma mock database.</p>
        </div>
        <select value={filter} onChange={(event) => setFilter(event.target.value as BookingStatus | "all")}>
          <option value="all">All</option>
          <option value="pending_host">Pending host</option>
          <option value="confirmed">Confirmed</option>
          <option value="declined">Declined</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      <div className="booking-list">
        {visibleBookings.length === 0 ? <div className="empty-state">No bookings in this state.</div> : null}
        {visibleBookings.map((booking) => (
          <article className="booking-item" key={booking.id}>
            <div>
              <div className="event-card-header">
                <h3>{booking.title}</h3>
                <span className="status-pill">{booking.status.replace("_", " ")}</span>
              </div>
              <p className="muted">
                {formatDateTime(booking.start)} with {booking.attendee.name} ({booking.attendee.email})
              </p>
            </div>
            <div className="button-row">
              {booking.status === "pending_host" ? (
                <>
                  <button className="primary-button" onClick={() => void action(booking.uid, "confirm")}>
                    Confirm
                  </button>
                  <button className="secondary-button" onClick={() => void action(booking.uid, "decline")}>
                    Decline
                  </button>
                </>
              ) : null}
              {!["cancelled", "declined"].includes(booking.status) ? (
                <button className="ghost-button" onClick={() => void action(booking.uid, "cancel")}>
                  Cancel
                </button>
              ) : null}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function PublicBookingPage({ route }: { route: Extract<AppRoute, { kind: "public-booking" }> }) {
  const [eventType, setEventType] = useState<PublicEventType | null>(null);
  const [slots, setSlots] = useState<Slot[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<Slot | null>(null);
  const [name, setName] = useState("Guest User");
  const [email, setEmail] = useState("guest@example.com");
  const [createdBooking, setCreatedBooking] = useState<Booking | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const nextEvent = await api.getPublicEventType(route.username, route.slug, route.shareToken);
        const today = localDate(new Date());
        const nextWeek = localDate(addDays(new Date(), 6));
        const nextSlots = await api.getPublicSlots({
          username: route.username,
          eventTypeSlug: route.slug,
          start: today,
          end: nextWeek,
          timeZone: "Europe/Moscow",
          durationMinutes: nextEvent.durationMinutes,
          shareToken: route.shareToken,
        });
        setEventType(nextEvent);
        setSlots(nextSlots.days.flatMap((day) => day.slots).filter((slot) => slot.available).slice(0, 18));
      } catch (requestError) {
        setError(asErrorMessage(requestError));
      } finally {
        setLoading(false);
      }
    }

    void load();
  }, [route.username, route.slug, route.shareToken]);

  async function book(event: FormEvent) {
    event.preventDefault();
    if (!eventType || !selectedSlot) return;
    setLoading(true);
    setError("");
    try {
      const booking = await api.createBooking({
        username: route.username,
        eventTypeSlug: route.slug,
        shareToken: route.shareToken,
        start: selectedSlot.start,
        durationMinutes: eventType.durationMinutes,
        attendee: {
          name,
          email,
          timeZone: "Europe/Moscow",
        },
      });
      setCreatedBooking(booking);
    } catch (requestError) {
      setError(asErrorMessage(requestError));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="public-page">
      <a className="brand" href="#">
        <span className="brand-mark">C</span>
        <span>Calendar</span>
      </a>
      <section className="booking-shell">
        <div className="booking-profile">
          {loading && !eventType ? <p className="muted">Loading booking page...</p> : null}
          {error ? <div className="banner error">{error}</div> : null}
          {eventType ? (
            <>
              <div className="avatar large-avatar">{initials(eventType.owner.name)}</div>
              <p className="eyebrow">{eventType.owner.name}</p>
              <h1>{eventType.title}</h1>
              <p>{eventType.description}</p>
              <div className="event-meta vertical">
                <span>{eventType.durationMinutes} minutes</span>
                <span>{eventType.confirmationPolicy.type} confirmation</span>
                <span>Europe/Moscow</span>
              </div>
            </>
          ) : null}
        </div>

        <div className="booking-picker">
          {createdBooking ? (
            <div className="success-state">
              <p className="eyebrow">Booking requested</p>
              <h2>{createdBooking.status === "confirmed" ? "Your meeting is confirmed" : "Waiting for confirmation"}</h2>
              <p className="muted">{formatDateTime(createdBooking.start)}</p>
              <a className="secondary-button" href="#">
                Back to dashboard
              </a>
            </div>
          ) : (
            <>
              <h2>Select a time</h2>
              <div className="slot-grid">
                {slots.map((slot) => (
                  <button
                    className={selectedSlot?.start === slot.start ? "slot-button selected" : "slot-button"}
                    key={slot.start}
                    onClick={() => setSelectedSlot(slot)}
                  >
                    <span>{formatDay(slot.start)}</span>
                    <strong>{formatTime(slot.start)}</strong>
                  </button>
                ))}
              </div>
              <form className="stack booking-form" onSubmit={book}>
                <label>
                  Name
                  <input value={name} onChange={(event) => setName(event.target.value)} />
                </label>
                <label>
                  Email
                  <input value={email} type="email" onChange={(event) => setEmail(event.target.value)} />
                </label>
                <button className="primary-button" disabled={!selectedSlot || loading}>
                  {loading ? "Booking..." : "Book meeting"}
                </button>
              </form>
            </>
          )}
        </div>
      </section>
    </main>
  );
}

function parseRoute(): AppRoute {
  const hash = window.location.hash || "#";
  const [path, query = ""] = hash.slice(1).split("?");
  const parts = path.split("/").filter(Boolean);
  if (parts[0] === "book" && parts[1] && parts[2]) {
    return {
      kind: "public-booking",
      username: parts[1],
      slug: parts[2],
      shareToken: new URLSearchParams(query).get("shareToken") ?? undefined,
    };
  }
  return { kind: "app" };
}

function viewTitle(view: "dashboard" | "availability" | "bookings") {
  if (view === "availability") return "Availability";
  if (view === "bookings") return "Bookings";
  return "Event types";
}

function initials(name: string) {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function slugify(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

async function copyText(value: string) {
  if (navigator.clipboard) {
    await navigator.clipboard.writeText(value);
  }
}

function asErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Unexpected error";
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatDay(value: string) {
  return new Intl.DateTimeFormat("en", {
    weekday: "short",
    month: "short",
    day: "numeric",
  }).format(new Date(value));
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat("en", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function localDate(date: Date) {
  return date.toISOString().slice(0, 10);
}

function addDays(date: Date, days: number) {
  const next = new Date(date);
  next.setDate(next.getDate() + days);
  return next;
}
