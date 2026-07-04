import { useMemo, useState } from "react";
import { Tabs } from "@base-ui-components/react/tabs";
import { Button } from "../../components/ui/Button";
import { Modal, DialogClose } from "../../components/ui/Modal";
import { TextField } from "../../components/ui/TextField";
import { IconCalendar } from "../../components/ui/icons";
import { useToast } from "../../components/ui/toast";
import { api } from "../../lib/api";
import { asErrorMessage } from "../../lib/utils";
import { bookingStatusLabel, t } from "../../lib/i18n";
import { formatDateTime } from "../../lib/datetime";
import type { Booking } from "../../lib/types";

type BookingTab = "upcoming" | "unconfirmed" | "past" | "cancelled";

type ReasonAction = { uid: string; title: string; type: "decline" | "cancel" };

type BookingsQueueProps = {
  token: string;
  bookings: Booking[];
  onChanged: () => void;
};

export function BookingsQueue({ token, bookings, onChanged }: BookingsQueueProps) {
  const toast = useToast();
  const [tab, setTab] = useState<BookingTab>("upcoming");
  const [reasonAction, setReasonAction] = useState<ReasonAction | null>(null);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);

  const now = Date.now();

  const filtered = useMemo(() => {
    return bookings.filter((booking) => {
      const start = new Date(booking.start).getTime();
      switch (tab) {
        case "upcoming":
          return start >= now && ["confirmed", "pending_host", "pending_attendee"].includes(booking.status);
        case "unconfirmed":
          return ["pending_host", "pending_attendee"].includes(booking.status);
        case "past":
          return start < now && booking.status === "confirmed";
        case "cancelled":
          return ["cancelled", "declined"].includes(booking.status);
        default: {
          const _exhaustive: never = tab;
          return _exhaustive;
        }
      }
    });
  }, [bookings, tab, now]);

  async function confirm(uid: string) {
    setBusy(true);
    try {
      await api.confirmBooking(token, uid);
      toast.success(t.bookings.confirmed);
      onChanged();
    } catch (error) {
      toast.error(t.bookings.confirmError, asErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  function openReason(action: ReasonAction) {
    setReason("");
    setReasonAction(action);
  }

  async function submitReason() {
    if (!reasonAction) return;
    setBusy(true);
    try {
      if (reasonAction.type === "decline") {
        await api.declineBooking(token, reasonAction.uid, reason || undefined);
        toast.success(t.bookings.declined);
      } else {
        await api.cancelBooking(token, reasonAction.uid, reason || undefined);
        toast.success(t.bookings.cancelled);
      }
      setReasonAction(null);
      onChanged();
    } catch (error) {
      toast.error(t.bookings.actionError, asErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  const empty = emptyStateForTab(tab);

  return (
    <div className="cal-panel">
      <Tabs.Root value={tab} onValueChange={(value) => setTab(value as BookingTab)}>
        <div className="bookings-toolbar">
          <Tabs.List className="bookings-tabs">
            <Tabs.Tab value="upcoming" className="bookings-tab">
              {t.bookings.tabs.upcoming}
            </Tabs.Tab>
            <Tabs.Tab value="unconfirmed" className="bookings-tab">
              {t.bookings.tabs.unconfirmed}
            </Tabs.Tab>
            <Tabs.Tab value="past" className="bookings-tab">
              {t.bookings.tabs.past}
            </Tabs.Tab>
            <Tabs.Tab value="cancelled" className="bookings-tab">
              {t.bookings.tabs.cancelled}
            </Tabs.Tab>
          </Tabs.List>
          <Button variant="secondary" size="sm">
            {t.common.filter}
          </Button>
        </div>

        {["upcoming", "unconfirmed", "past", "cancelled"].map((value) => (
          <Tabs.Panel key={value} value={value}>
            {filtered.length === 0 ? (
              <div className="bookings-empty">
                <div className="bookings-empty-icon">
                  <IconCalendar />
                </div>
                <h3>{empty.title}</h3>
                <p className="muted">{empty.hint}</p>
              </div>
            ) : (
              <div className="booking-list">
                {filtered.map((booking) => (
                  <article className="booking-item" key={booking.id}>
                    <div className="booking-info">
                      <div className="event-card-header">
                        <h3>{booking.title}</h3>
                        <span className="status-pill" data-status={booking.status}>
                          {bookingStatusLabel(booking.status)}
                        </span>
                      </div>
                      <p className="muted">
                        {formatDateTime(booking.start, booking.attendee.timeZone)} · {booking.attendee.name} (
                        {booking.attendee.email})
                      </p>
                    </div>
                    <div className="button-row">
                      {booking.status === "pending_host" ? (
                        <>
                          <Button variant="primary" size="sm" disabled={busy} onClick={() => void confirm(booking.uid)}>
                            {t.bookings.confirm}
                          </Button>
                          <Button
                            variant="secondary"
                            size="sm"
                            disabled={busy}
                            onClick={() => openReason({ uid: booking.uid, title: booking.title, type: "decline" })}
                          >
                            {t.bookings.decline}
                          </Button>
                        </>
                      ) : null}
                      {!["cancelled", "declined"].includes(booking.status) ? (
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={busy}
                          onClick={() => openReason({ uid: booking.uid, title: booking.title, type: "cancel" })}
                        >
                          {t.bookings.cancelBooking}
                        </Button>
                      ) : null}
                    </div>
                  </article>
                ))}
              </div>
            )}
          </Tabs.Panel>
        ))}
      </Tabs.Root>

      <Modal
        open={reasonAction !== null}
        onOpenChange={(open) => !open && setReasonAction(null)}
        title={reasonAction?.type === "decline" ? t.bookings.declineTitle : t.bookings.cancelTitle}
        description={reasonAction ? reasonAction.title : undefined}
        footer={
          <>
            <DialogClose className="btn btn-ghost">{t.bookings.keepBooking}</DialogClose>
            <Button variant="danger" disabled={busy} onClick={() => void submitReason()}>
              {busy
                ? t.common.syncing
                : reasonAction?.type === "decline"
                  ? t.bookings.decline
                  : t.bookings.cancelBooking}
            </Button>
          </>
        }
      >
        <TextField
          label={t.bookings.reasonLabel}
          value={reason}
          onChange={setReason}
          multiline
          rows={3}
          placeholder={t.bookings.reasonPlaceholder}
        />
      </Modal>
    </div>
  );
}

function emptyStateForTab(tab: BookingTab) {
  switch (tab) {
    case "upcoming":
      return { title: t.bookings.emptyUpcoming, hint: t.bookings.emptyUpcomingHint };
    case "unconfirmed":
      return { title: t.bookings.emptyUnconfirmed, hint: t.bookings.emptyUnconfirmedHint };
    case "past":
      return { title: t.bookings.emptyPast, hint: t.bookings.emptyPastHint };
    case "cancelled":
      return { title: t.bookings.emptyCancelled, hint: t.bookings.emptyCancelledHint };
    default: {
      const _exhaustive: never = tab;
      return _exhaustive;
    }
  }
}
