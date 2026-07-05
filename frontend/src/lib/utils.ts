export function cx(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

export function initials(name: string) {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export function slugify(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

export async function copyText(value: string) {
  if (navigator.clipboard) {
    await navigator.clipboard.writeText(value);
  }
}

export function asErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Unexpected error";
}

export function newIdempotencyKey() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 12)}`;
}

const STATUS_LABELS: Record<string, string> = {
  pending_host: "Pending approval",
  pending_attendee: "Awaiting attendee",
  confirmed: "Confirmed",
  declined: "Declined",
  cancelled: "Cancelled",
};

export function statusLabel(status: string) {
  return STATUS_LABELS[status] ?? status.replace(/_/g, " ");
}
