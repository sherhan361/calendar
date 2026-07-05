import { useEffect, useState } from "react";
import { buttonClass } from "../../components/ui/Button";
import { IconClock } from "../../components/ui/icons";
import { api } from "../../lib/api";
import { asErrorMessage, initials } from "../../lib/utils";
import { t } from "../../lib/i18n";
import type { AppRoute } from "../../app/router";
import type { PublicUserPage } from "../../lib/types";

type ProfileRoute = Extract<AppRoute, { kind: "public-profile" }>;

export function PublicProfilePage({ route }: { route: ProfileRoute }) {
  const [page, setPage] = useState<PublicUserPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const nextPage = await api.getPublicUserPage(route.username);
        if (!cancelled) setPage(nextPage);
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
  }, [route.username]);

  return (
    <main className="public-page">
      <a className="brand" href="#">
        {t.brand}
      </a>

      <section className="booking-shell profile-shell">
        <div className="booking-picker">
          {loading ? <p className="muted">{t.public.profileLoading}</p> : null}
          {error ? <div className="banner error">{error}</div> : null}
          {page ? (
            <div className="profile">
              <div className="profile-head">
                <div className="avatar large-avatar">{initials(page.user.name)}</div>
                <p className="eyebrow">{t.public.profileEyebrow}</p>
                <h1>{page.user.name}</h1>
                <p className="muted">@{page.user.username}</p>
              </div>

              {page.eventTypes.length === 0 ? (
                <p className="muted">{t.public.profileEmpty}</p>
              ) : (
                <div className="profile-event-list">
                  {page.eventTypes.map((eventType) => (
                    <article className="profile-event" key={eventType.id}>
                      <div>
                        <h3>{eventType.title}</h3>
                        {eventType.description ? <p className="muted">{eventType.description}</p> : null}
                        <span className="event-row-duration">
                          <IconClock />
                          {eventType.durationMinutes} {t.public.minutes}
                        </span>
                      </div>
                      <a className={buttonClass("primary")} href={`#/book/${page.user.username}/${eventType.slug}`}>
                        {t.public.book}
                      </a>
                    </article>
                  ))}
                </div>
              )}
            </div>
          ) : null}
        </div>
      </section>
    </main>
  );
}
