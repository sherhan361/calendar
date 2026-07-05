import { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";
import { Form } from "@base-ui-components/react/form";
import { Calendar } from "./Calendar";
import { Button, buttonClass } from "../../components/ui/Button";
import { TextField } from "../../components/ui/TextField";
import { SelectField } from "../../components/ui/SelectField";
import { IconClock } from "../../components/ui/icons";
import { api, ApiRequestError } from "../../lib/api";
import { asErrorMessage, initials, cx, newIdempotencyKey } from "../../lib/utils";
import {
  addDays,
  browserTimeZone,
  formatDateTime,
  formatDayLong,
  formatTime,
  localDateString,
  timeZoneOptions,
  zonedDayKey,
} from "../../lib/datetime";
import { confirmationPolicyLabel, t } from "../../lib/i18n";
import type { AppRoute } from "../../app/router";
import type { Booking, PublicEventType, Slot } from "../../lib/types";

const tzOptions = timeZoneOptions().map((zone) => ({ value: zone, label: zone.replace(/_/g, " ") }));

type PublicRoute = Extract<AppRoute, { kind: "public-booking" }>;

async function fetchAvailableSlots(route: PublicRoute, durationMinutes: number, timeZone: string): Promise<Slot[]> {
  const start = localDateString(new Date());
  const end = localDateString(addDays(new Date(), 30));
  const response = await api.getPublicSlots({
    username: route.username,
    eventTypeSlug: route.slug,
    start,
    end,
    timeZone,
    durationMinutes,
    shareToken: route.shareToken,
  });
  return response.days.flatMap((day) => day.slots).filter((slot) => slot.available);
}

export function PublicBookingPage({ route }: { route: PublicRoute }) {
  const [eventType, setEventType] = useState<PublicEventType | null>(null);
  const [slots, setSlots] = useState<Slot[]>([]);
  const [timeZone, setTimeZone] = useState(browserTimeZone());
  const [selectedDay, setSelectedDay] = useState<string | null>(null);
  const [selectedSlot, setSelectedSlot] = useState<Slot | null>(null);
  const [month, setMonth] = useState(() => {
    const now = new Date();
    return { year: now.getFullYear(), month: now.getMonth() };
  });
  const [name, setName] = useState("Гость");
  const [email, setEmail] = useState("guest@example.com");
  const [createdBooking, setCreatedBooking] = useState<Booking | null>(null);
  const [loading, setLoading] = useState(true);
  const [booking, setBooking] = useState(false);
  const [error, setError] = useState("");
  const idempotencyKeyRef = useRef<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const nextEvent = await api.getPublicEventType(route.username, route.slug, route.shareToken);
        const nextSlots = await fetchAvailableSlots(route, nextEvent.durationMinutes, timeZone);
        if (cancelled) return;
        setEventType(nextEvent);
        setSlots(nextSlots);
      } catch (requestError) {
        if (!cancelled) setError(asErrorMessage(requestError));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [route.username, route.slug, route.shareToken, timeZone]);

  const slotsByDay = useMemo(() => {
    const grouped = new Map<string, Slot[]>();
    for (const slot of slots) {
      const key = zonedDayKey(slot.start, timeZone);
      const list = grouped.get(key) ?? [];
      list.push(slot);
      grouped.set(key, list);
    }
    return grouped;
  }, [slots, timeZone]);

  const availableDays = useMemo(() => new Set(slotsByDay.keys()), [slotsByDay]);

  useEffect(() => {
    if (selectedDay && availableDays.has(selectedDay)) return;
    const first = [...availableDays].sort()[0];
    if (first) {
      setSelectedDay(first);
      const [y, m] = first.split("-").map(Number);
      setMonth({ year: y, month: m - 1 });
    } else {
      setSelectedDay(null);
    }
    setSelectedSlot(null);
  }, [availableDays, selectedDay]);

  const daySlots = selectedDay ? slotsByDay.get(selectedDay) ?? [] : [];

  function chooseSlot(slot: Slot | null) {
    idempotencyKeyRef.current = null;
    setSelectedSlot(slot);
  }

  async function submitBooking(event: FormEvent) {
    event.preventDefault();
    if (!eventType || !selectedSlot || booking) return;
    if (idempotencyKeyRef.current === null) {
      idempotencyKeyRef.current = newIdempotencyKey();
    }
    setBooking(true);
    setError("");
    try {
      const created = await api.createBooking({
        username: route.username,
        eventTypeSlug: route.slug,
        shareToken: route.shareToken,
        start: selectedSlot.start,
        durationMinutes: eventType.durationMinutes,
        idempotencyKey: idempotencyKeyRef.current,
        attendee: { name, email, timeZone },
      });
      idempotencyKeyRef.current = null;
      setCreatedBooking(created);
    } catch (requestError) {
      if (requestError instanceof ApiRequestError && requestError.code === "conflict") {
        idempotencyKeyRef.current = null;
        setError(t.public.slotTaken);
        try {
          setSlots(await fetchAvailableSlots(route, eventType.durationMinutes, timeZone));
        } catch {
          // keep the current slot list if refresh fails
        }
        setSelectedSlot(null);
      } else {
        setError(asErrorMessage(requestError));
      }
    } finally {
      setBooking(false);
    }
  }

  return (
    <main className="public-page">
      <a className="brand" href="#">
        {t.brand}
      </a>

      <section className="booking-shell">
        <aside className="booking-profile">
          {loading && !eventType ? <p className="muted">{t.public.loading}</p> : null}
          {error && !eventType ? <div className="banner error">{error}</div> : null}
          {eventType ? (
            <>
              <div className="avatar large-avatar">{initials(eventType.owner.name)}</div>
              <p className="eyebrow">{eventType.owner.name}</p>
              <h1>{eventType.title}</h1>
              <p className="muted">{eventType.description}</p>
              <div className="event-meta vertical">
                <span>
                  <IconClock /> {eventType.durationMinutes} {t.public.minutes}
                </span>
                <span>{confirmationPolicyLabel(eventType.confirmationPolicy.type)}</span>
              </div>
              <div className="field tz-field">
                <span className="field-label">{t.public.timeZone}</span>
                <SelectField value={timeZone} onValueChange={setTimeZone} options={tzOptions} />
              </div>
            </>
          ) : null}
        </aside>

        <div className="booking-picker">
          {createdBooking ? (
            <div className="success-state">
              <div className="success-badge">✓</div>
              <h2>{createdBooking.status === "confirmed" ? t.public.confirmed : t.public.requestSent}</h2>
              <p className="muted">
                {formatDateTime(createdBooking.start, timeZone)} ({timeZone})
              </p>
              {createdBooking.status !== "confirmed" ? <p className="muted">{t.public.pendingHint}</p> : null}
              <a className={buttonClass("secondary")} href="#">
                {t.public.backHome}
              </a>
            </div>
          ) : eventType ? (
            <div className="picker-grid">
              <div>
                <h2>{t.public.selectDay}</h2>
                <Calendar
                  year={month.year}
                  month={month.month}
                  selectedKey={selectedDay}
                  availableDays={availableDays}
                  onMonthChange={(year, m) => setMonth({ year, month: m })}
                  onSelect={(key) => {
                    setSelectedDay(key);
                    chooseSlot(null);
                  }}
                />
              </div>
              <div className="slots-column">
                <h2>{selectedDay ? formatDayLong(`${selectedDay}T00:00:00`) : t.public.pickTime}</h2>
                {error ? <div className="banner error">{error}</div> : null}
                {selectedSlot ? (
                  <Form className="stack booking-form" onSubmit={submitBooking}>
                    <p className="muted">
                      {formatTime(selectedSlot.start, timeZone)} – {formatTime(selectedSlot.end, timeZone)}
                    </p>
                    <TextField label={t.public.name} value={name} onChange={setName} required />
                    <TextField label={t.public.email} type="email" value={email} onChange={setEmail} required />
                    <div className="button-row">
                      <Button variant="ghost" onClick={() => chooseSlot(null)}>
                        {t.common.back}
                      </Button>
                      <Button variant="primary" type="submit" disabled={booking}>
                        {booking ? t.public.booking : t.public.confirmBooking}
                      </Button>
                    </div>
                  </Form>
                ) : (
                  <div className="slot-list">
                    {daySlots.length === 0 ? (
                      <p className="muted">{t.public.noSlots}</p>
                    ) : (
                      daySlots.map((slot) => (
                        <button
                          key={slot.start}
                          type="button"
                          className={cx("slot-button", selectedSlot === slot && "selected")}
                          onClick={() => chooseSlot(slot)}
                        >
                          {formatTime(slot.start, timeZone)}
                        </button>
                      ))
                    )}
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </div>
      </section>
    </main>
  );
}
