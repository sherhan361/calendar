import { useMemo, useState } from "react";
import { Switch } from "@base-ui-components/react/switch";
import { Button } from "../../components/ui/Button";
import { Modal, DialogClose } from "../../components/ui/Modal";
import { IconClock, IconExternal, IconEyeOff, IconLink } from "../../components/ui/icons";
import { CreateEventTypeDialog } from "./CreateEventTypeDialog";
import { EditEventTypeDialog } from "./EditEventTypeDialog";
import { api } from "../../lib/api";
import { asErrorMessage, copyText, cx } from "../../lib/utils";
import { useToast } from "../../components/ui/toast";
import { t } from "../../lib/i18n";
import type { EventType, Schedule, User } from "../../lib/types";

type EventTypesViewProps = {
  token: string;
  user: User;
  schedules: Schedule[];
  eventTypes: EventType[];
  onChanged: () => void;
};

export function EventTypesView({ token, user, schedules, eventTypes, onChanged }: EventTypesViewProps) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return eventTypes;
    return eventTypes.filter(
      (item) => item.title.toLowerCase().includes(q) || item.slug.toLowerCase().includes(q),
    );
  }, [eventTypes, query]);

  return (
    <div className="cal-panel">
      <div className="panel-toolbar">
        <input
          className="search-input"
          placeholder={t.common.search}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <Button variant="primary" onClick={() => setDialogOpen(true)} disabled={schedules.length === 0}>
          + {t.common.create}
        </Button>
      </div>

      {filtered.length === 0 ? (
        <div className="empty-state">{t.eventTypes.empty}</div>
      ) : (
        <div className="event-list">
          {filtered.map((eventType) => (
            <EventTypeRow key={eventType.id} token={token} user={user} eventType={eventType} onChanged={onChanged} />
          ))}
        </div>
      )}

      <CreateEventTypeDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        token={token}
        schedules={schedules}
        onCreated={onChanged}
      />
    </div>
  );
}

function EventTypeRow({
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
  const toast = useToast();
  const [busy, setBusy] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const publicPath = `#/book/${user.username}/${eventType.slug}`;
  const publicUrl = `${window.location.origin}/${publicPath}`;

  async function removeEventType() {
    setBusy(true);
    try {
      await api.deleteEventType(token, eventType.id);
      toast.success(t.eventTypes.deleted, eventType.title);
      setDeleteOpen(false);
      onChanged();
    } catch (error) {
      toast.error(t.eventTypes.deleteError, asErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function toggleHidden(checked: boolean) {
    setBusy(true);
    try {
      await api.updateEventType(token, eventType.id, { hidden: !checked });
      onChanged();
    } catch (error) {
      toast.error(t.eventTypes.toggleError, asErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function createLink() {
    setBusy(true);
    try {
      const link = await api.createShareLink(token, eventType.id);
      const url = `${window.location.origin}/#/book/${user.username}/${eventType.slug}?shareToken=${link.token}`;
      await copyText(url);
      toast.success(t.eventTypes.privateLinkCopied);
      onChanged();
    } catch (error) {
      toast.error(t.eventTypes.linkError, asErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function copyPublic() {
    await copyText(publicUrl);
    toast.success(t.eventTypes.linkCopied);
  }

  return (
    <article className={cx("event-row", eventType.hidden && "is-hidden")}>
      <div className="event-row-main">
        <div className="event-row-title">
          <h3>{eventType.title}</h3>
          {eventType.hidden ? (
            <span className="badge badge-hidden">
              <IconEyeOff />
              {t.common.hidden}
            </span>
          ) : null}
        </div>
        <p className="event-row-slug">/{user.username}/{eventType.slug}</p>
        <span className="event-row-duration">
          <IconClock />
          {eventType.durationMinutes}m
        </span>
      </div>

      <div className="event-row-actions">
        <Switch.Root
          checked={!eventType.hidden}
          disabled={busy}
          onCheckedChange={(checked) => void toggleHidden(checked === true)}
          className="switch"
        >
          <Switch.Thumb className="switch-thumb" />
        </Switch.Root>
        <a className="icon-btn" href={publicPath} target="_blank" rel="noreferrer" title={t.common.openPage}>
          <IconExternal />
        </a>
        <button type="button" className="icon-btn" title={t.common.copyLink} onClick={() => void copyPublic()}>
          <IconLink />
        </button>
        <button type="button" className="icon-btn" title={t.common.privateLink} disabled={busy} onClick={() => void createLink()}>
          <span className="icon-btn-label">⋯</span>
        </button>
        <Button variant="secondary" size="sm" onClick={() => setEditOpen(true)}>
          {t.eventTypes.edit}
        </Button>
        <Button variant="ghost" size="sm" disabled={busy} onClick={() => setDeleteOpen(true)}>
          {t.eventTypes.deleteAction}
        </Button>
      </div>

      <EditEventTypeDialog
        open={editOpen}
        onOpenChange={setEditOpen}
        token={token}
        eventType={eventType}
        onUpdated={onChanged}
      />

      <Modal
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        title={t.eventTypes.deleteTitle}
        description={eventType.title}
        footer={
          <>
            <DialogClose className="btn btn-ghost">{t.common.cancel}</DialogClose>
            <Button variant="danger" disabled={busy} onClick={() => void removeEventType()}>
              {busy ? t.common.syncing : t.eventTypes.deleteAction}
            </Button>
          </>
        }
      >
        <p className="muted">{t.eventTypes.deleteConfirm}</p>
      </Modal>
    </article>
  );
}
