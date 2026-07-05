import { useState } from "react";
import type { FormEvent } from "react";
import { Form } from "@base-ui-components/react/form";
import { Button, buttonClass } from "../../components/ui/Button";
import { TextField } from "../../components/ui/TextField";
import { api } from "../../lib/api";
import { asErrorMessage } from "../../lib/utils";
import { t } from "../../lib/i18n";
import type { AppRoute } from "../../app/router";
import type { Booking } from "../../lib/types";

type CancelRoute = Extract<AppRoute, { kind: "public-cancel" }>;

export function CancelBookingPage({ route }: { route: CancelRoute }) {
  const [reason, setReason] = useState("");
  const [cancelledBooking, setCancelledBooking] = useState<Booking | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const invalidLink = !route.uid || !route.token;

  async function submitCancel(event: FormEvent) {
    event.preventDefault();
    if (busy || invalidLink) return;
    setBusy(true);
    setError("");
    try {
      const cancelled = await api.cancelBookingPublic(route.uid, route.token, reason.trim() || undefined);
      setCancelledBooking(cancelled);
    } catch (requestError) {
      setError(asErrorMessage(requestError));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="public-page">
      <a className="brand" href="#">
        {t.brand}
      </a>

      <section className="booking-shell cancel-shell">
        <div className="booking-picker">
          {cancelledBooking ? (
            <div className="success-state">
              <div className="success-badge">✓</div>
              <h2>{t.public.cancel.success}</h2>
              <p className="success-event">{cancelledBooking.title}</p>
              <p className="muted">{t.public.cancel.successHint}</p>
              <a className={buttonClass("secondary")} href="#">
                {t.public.backHome}
              </a>
            </div>
          ) : invalidLink ? (
            <div className="banner error">{t.public.cancel.invalidLink}</div>
          ) : (
            <Form className="stack booking-form" onSubmit={submitCancel}>
              <h2>{t.public.cancel.title}</h2>
              <p className="muted">{t.public.cancel.intro}</p>
              {error ? <div className="banner error">{error}</div> : null}
              <TextField
                label={t.public.cancel.reasonLabel}
                value={reason}
                onChange={setReason}
                multiline
                rows={3}
                placeholder={t.public.cancel.reasonPlaceholder}
              />
              <div className="button-row">
                <a className={buttonClass("ghost")} href="#">
                  {t.common.back}
                </a>
                <Button variant="danger" type="submit" disabled={busy}>
                  {busy ? t.public.cancel.submitting : t.public.cancel.submit}
                </Button>
              </div>
            </Form>
          )}
        </div>
      </section>
    </main>
  );
}
