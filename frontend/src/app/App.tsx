import { useState } from "react";
import { Tabs } from "@base-ui-components/react/tabs";
import { ToastProvider } from "../components/ui/toast";
import { useHashRoute } from "./router";
import { useWorkspace } from "./useWorkspace";
import { LoginScreen } from "../features/auth/LoginScreen";
import { EventTypesView } from "../features/event-types/EventTypesView";
import { AvailabilityEditor } from "../features/availability/AvailabilityEditor";
import { BookingsQueue } from "../features/bookings/BookingsQueue";
import { PublicBookingPage } from "../features/public-booking/PublicBookingPage";
import { CancelBookingPage } from "../features/public-booking/CancelBookingPage";
import { Button } from "../components/ui/Button";
import { IconAvailability, IconBookings, IconEventTypes } from "../components/ui/icons";
import { initials } from "../lib/utils";
import { t } from "../lib/i18n";

type View = "events" | "availability" | "bookings";

export default function App() {
  const route = useHashRoute();
  return (
    <ToastProvider>
      {route.kind === "public-booking" ? (
        <PublicBookingPage route={route} />
      ) : route.kind === "public-cancel" ? (
        <CancelBookingPage route={route} />
      ) : (
        <PrivateApp />
      )}
    </ToastProvider>
  );
}

function PrivateApp() {
  const workspace = useWorkspace();
  const [view, setView] = useState<View>("events");

  if (!workspace.token || !workspace.user) {
    return <LoginScreen loading={workspace.loading} error={workspace.error} onLogin={workspace.login} />;
  }

  const { user, token, schedules, eventTypes, bookings } = workspace;
  const pendingCount = bookings.filter((item) => item.status === "pending_host").length;

  return (
    <div className="app-shell">
      <Tabs.Root value={view} onValueChange={(value) => setView(value as View)} className="tabs-root">
        <aside className="sidebar">
          <div className="sidebar-top">
            <a className="brand" href="#">
              {t.brand}
            </a>
            <div className="avatar avatar-sm">{initials(user.name)}</div>
          </div>

          <Tabs.List className="nav-list">
            <Tabs.Tab value="events" className="nav-tab">
              <IconEventTypes className="nav-icon" />
              {t.nav.eventTypes}
            </Tabs.Tab>
            <Tabs.Tab value="bookings" className="nav-tab">
              <IconBookings className="nav-icon" />
              {t.nav.bookings}
              {pendingCount > 0 ? <span className="nav-badge">{pendingCount}</span> : null}
            </Tabs.Tab>
            <Tabs.Tab value="availability" className="nav-tab">
              <IconAvailability className="nav-icon" />
              {t.nav.availability}
            </Tabs.Tab>
          </Tabs.List>

          <div className="sidebar-footer">
            <div className="avatar">{initials(user.name)}</div>
            <div>
              <strong>{user.name}</strong>
              <span>{user.email}</span>
            </div>
          </div>
        </aside>

        <main className="workspace">
          <header className="page-header">
            <div>
              <h1>{pageTitle(view)}</h1>
              {pageSubtitle(view) ? <p className="page-subtitle">{pageSubtitle(view)}</p> : null}
            </div>
            <div className="topbar-actions">
              {workspace.loading ? <span className="muted">{t.common.syncing}</span> : null}
              <Button variant="ghost" size="sm" onClick={() => void workspace.refresh()}>
                {t.common.refresh}
              </Button>
              <Button variant="ghost" size="sm" onClick={workspace.logout}>
                {t.common.logout}
              </Button>
            </div>
          </header>

          {workspace.error ? <div className="banner error">{workspace.error}</div> : null}

          <div className="page-content">
            <Tabs.Panel value="events">
              <EventTypesView
                token={token}
                user={user}
                schedules={schedules}
                eventTypes={eventTypes}
                onChanged={() => void workspace.refresh()}
              />
            </Tabs.Panel>
            <Tabs.Panel value="availability">
              <AvailabilityEditor token={token} schedules={schedules} onChanged={() => void workspace.refresh()} />
            </Tabs.Panel>
            <Tabs.Panel value="bookings">
              <BookingsQueue token={token} bookings={bookings} onChanged={() => void workspace.refresh()} />
            </Tabs.Panel>
          </div>
        </main>
      </Tabs.Root>
    </div>
  );
}

function pageTitle(view: View) {
  if (view === "availability") return t.availability.title;
  if (view === "bookings") return t.bookings.title;
  return t.eventTypes.title;
}

function pageSubtitle(view: View) {
  if (view === "availability") return t.availability.subtitle;
  if (view === "bookings") return "";
  return t.eventTypes.subtitle;
}
