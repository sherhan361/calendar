const LOCALE = "ru-RU";

export function formatDateTime(value: string, timeZone?: string) {
  return new Intl.DateTimeFormat(LOCALE, {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone,
  }).format(new Date(value));
}

export function formatTime(value: string, timeZone?: string) {
  return new Intl.DateTimeFormat(LOCALE, {
    hour: "2-digit",
    minute: "2-digit",
    timeZone,
  }).format(new Date(value));
}

export function formatDayLong(value: string, timeZone?: string) {
  return new Intl.DateTimeFormat(LOCALE, {
    weekday: "long",
    month: "long",
    day: "numeric",
    timeZone,
  }).format(new Date(value));
}

/** Returns the calendar day (YYYY-MM-DD) of an instant, evaluated in a timezone. */
export function zonedDayKey(value: string, timeZone?: string) {
  return new Intl.DateTimeFormat("en-CA", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    timeZone,
  }).format(new Date(value));
}

/** YYYY-MM-DD for a local calendar day, independent of timezone. */
export function dayKey(year: number, month: number, day: number) {
  return `${year.toString().padStart(4, "0")}-${(month + 1).toString().padStart(2, "0")}-${day
    .toString()
    .padStart(2, "0")}`;
}

export function localDateString(date: Date) {
  return dayKey(date.getFullYear(), date.getMonth(), date.getDate());
}

export function addDays(date: Date, days: number) {
  const next = new Date(date);
  next.setDate(next.getDate() + days);
  return next;
}

export type CalendarDay = {
  key: string;
  date: Date;
  day: number;
  inMonth: boolean;
  isToday: boolean;
};

/** A Monday-first 6x7 grid of days covering the given month. */
export function buildMonthGrid(year: number, month: number): CalendarDay[] {
  const first = new Date(year, month, 1);
  const offset = (first.getDay() + 6) % 7;
  const start = new Date(year, month, 1 - offset);
  const todayKey = localDateString(new Date());
  const cells: CalendarDay[] = [];
  for (let i = 0; i < 42; i += 1) {
    const date = new Date(start.getFullYear(), start.getMonth(), start.getDate() + i);
    const key = localDateString(date);
    cells.push({
      key,
      date,
      day: date.getDate(),
      inMonth: date.getMonth() === month,
      isToday: key === todayKey,
    });
  }
  return cells;
}

export const monthTitle = (year: number, month: number) =>
  new Intl.DateTimeFormat(LOCALE, { month: "long", year: "numeric" }).format(new Date(year, month, 1));

export function browserTimeZone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  } catch {
    return "UTC";
  }
}

const CURATED_TIME_ZONES = [
  "Europe/Moscow",
  "Europe/London",
  "Europe/Berlin",
  "Europe/Lisbon",
  "America/New_York",
  "America/Los_Angeles",
  "Asia/Dubai",
  "Asia/Almaty",
  "Asia/Tokyo",
  "Australia/Sydney",
  "UTC",
];

export function timeZoneOptions() {
  const detected = browserTimeZone();
  return Array.from(new Set([detected, ...CURATED_TIME_ZONES]));
}
