import { useEffect, useState } from "react";
import { Checkbox } from "@base-ui-components/react/checkbox";
import { Switch } from "@base-ui-components/react/switch";
import { Tabs } from "@base-ui-components/react/tabs";
import { Button } from "../../components/ui/Button";
import { Modal, DialogClose } from "../../components/ui/Modal";
import { TextField } from "../../components/ui/TextField";
import { SelectField } from "../../components/ui/SelectField";
import { IconGlobe, IconMore } from "../../components/ui/icons";
import { api } from "../../lib/api";
import { asErrorMessage, cx } from "../../lib/utils";
import { browserTimeZone, timeZoneOptions } from "../../lib/datetime";
import { useToast } from "../../components/ui/toast";
import { formatAvailabilitySummary, t } from "../../lib/i18n";
import type { AvailabilityOverride, AvailabilityRule, Schedule, Weekday } from "../../lib/types";

const weekdays: Weekday[] = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];
const weekdayLabels: Record<Weekday, string> = {
  monday: "Пн",
  tuesday: "Вт",
  wednesday: "Ср",
  thursday: "Чт",
  friday: "Пт",
  saturday: "Сб",
  sunday: "Вс",
};

const tzOptions = timeZoneOptions().map((zone) => ({ value: zone, label: zone.replace(/_/g, " ") }));

type AvailabilityEditorProps = {
  token: string;
  schedules: Schedule[];
  onChanged: () => void;
};

export function AvailabilityEditor({ token, schedules, onChanged }: AvailabilityEditorProps) {
  const toast = useToast();
  const [editingId, setEditingId] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  async function createSchedule() {
    setCreating(true);
    try {
      const created = await api.createSchedule(token, {
        name: t.availability.workingHours,
        timeZone: browserTimeZone(),
        availability: [
          { days: ["monday", "tuesday", "wednesday", "thursday", "friday"], startTime: "09:00", endTime: "17:00" },
        ],
        overrides: [],
      });
      toast.success(t.availability.scheduleCreated, created.name);
      onChanged();
      setEditingId(created.id);
    } catch (error) {
      toast.error(t.availability.createError, asErrorMessage(error));
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="stack lg">
      <Tabs.Root defaultValue="mine" className="availability-tabs">
        <div className="availability-toolbar">
          <Tabs.List className="segmented">
            <Tabs.Tab value="mine" className="segmented-item">
              {t.availability.myAvailability}
            </Tabs.Tab>
            <Tabs.Tab value="team" className="segmented-item" disabled>
              {t.availability.teamAvailability}
            </Tabs.Tab>
          </Tabs.List>
          <Button variant="primary" disabled={creating} onClick={() => void createSchedule()}>
            + {t.availability.createSchedule}
          </Button>
        </div>

        <Tabs.Panel value="mine">
          {schedules.length === 0 ? (
            <div className="empty-state">{t.availability.empty}</div>
          ) : (
            <div className="schedule-list">
              {schedules.map((schedule) => (
                <ScheduleCard
                  key={schedule.id}
                  token={token}
                  schedule={schedule}
                  editing={editingId === schedule.id}
                  onEdit={() => setEditingId(editingId === schedule.id ? null : schedule.id)}
                  onChanged={onChanged}
                />
              ))}
            </div>
          )}

          {editingId && schedules.some((item) => item.id === editingId) ? (
            <ScheduleEditor
              token={token}
              schedule={schedules.find((item) => item.id === editingId)!}
              onSaved={() => {
                onChanged();
                setEditingId(null);
              }}
              onCancel={() => setEditingId(null)}
            />
          ) : null}
        </Tabs.Panel>
      </Tabs.Root>
    </div>
  );
}

function ScheduleCard({
  token,
  schedule,
  editing,
  onEdit,
  onChanged,
}: {
  token: string;
  schedule: Schedule;
  editing: boolean;
  onEdit: () => void;
  onChanged: () => void;
}) {
  const toast = useToast();
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  async function removeSchedule() {
    setBusy(true);
    try {
      await api.deleteSchedule(token, schedule.id);
      toast.success(t.availability.deleted, schedule.name);
      setDeleteOpen(false);
      onChanged();
    } catch (error) {
      toast.error(t.availability.deleteError, asErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className={cx("schedule-card", editing && "is-editing")}>
      <div className="schedule-card-head">
        <div>
          <div className="schedule-card-title">
            <h3>{schedule.name || t.availability.workingHours}</h3>
            {schedule.isDefault ? <span className="badge badge-default">{t.common.default}</span> : null}
          </div>
          <div className="schedule-intervals">
            {schedule.availability.map((rule, index) => (
              <p key={index}>{formatAvailabilitySummary(rule.days, rule.startTime, rule.endTime)}</p>
            ))}
          </div>
          <p className="schedule-timezone">
            <IconGlobe />
            {schedule.timeZone}
          </p>
        </div>
        <div className="button-row">
          <button type="button" className="icon-btn" title={t.availability.edit} onClick={onEdit}>
            <IconMore />
          </button>
          <Button variant="ghost" size="sm" disabled={busy} onClick={() => setDeleteOpen(true)}>
            {t.availability.deleteSchedule}
          </Button>
        </div>
      </div>

      <Modal
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        title={t.availability.deleteTitle}
        description={schedule.name}
        footer={
          <>
            <DialogClose className="btn btn-ghost">{t.common.cancel}</DialogClose>
            <Button variant="danger" disabled={busy} onClick={() => void removeSchedule()}>
              {busy ? t.common.syncing : t.availability.deleteSchedule}
            </Button>
          </>
        }
      >
        <p className="muted">{t.availability.deleteConfirm}</p>
      </Modal>
    </article>
  );
}

function ScheduleEditor({
  token,
  schedule,
  onSaved,
  onCancel,
}: {
  token: string;
  schedule: Schedule;
  onSaved: () => void;
  onCancel: () => void;
}) {
  const toast = useToast();
  const [name, setName] = useState(schedule.name);
  const [timeZone, setTimeZone] = useState(schedule.timeZone);
  const [isDefault, setIsDefault] = useState(schedule.isDefault);
  const [rules, setRules] = useState<AvailabilityRule[]>(schedule.availability);
  const [overrides, setOverrides] = useState<AvailabilityOverride[]>(schedule.overrides);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setName(schedule.name);
    setTimeZone(schedule.timeZone);
    setIsDefault(schedule.isDefault);
    setRules(schedule.availability);
    setOverrides(schedule.overrides);
  }, [schedule.id]);

  function updateRule(index: number, patch: Partial<AvailabilityRule>) {
    setRules((current) => current.map((rule, ruleIndex) => (ruleIndex === index ? { ...rule, ...patch } : rule)));
  }

  function toggleDay(index: number, day: Weekday, checked: boolean) {
    const rule = rules[index];
    const days = checked ? [...rule.days, day] : rule.days.filter((item) => item !== day);
    updateRule(index, { days });
  }

  function updateOverride(index: number, patch: Partial<AvailabilityOverride>) {
    setOverrides((current) => current.map((item, i) => (i === index ? { ...item, ...patch } : item)));
  }

  async function save() {
    setBusy(true);
    try {
      await api.updateSchedule(token, schedule.id, {
        name: name.trim() || t.availability.workingHours,
        timeZone,
        isDefault,
        availability: rules,
        overrides,
      });
      toast.success(t.availability.saved);
      onSaved();
    } catch (error) {
      toast.error(t.availability.saveError, asErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="cal-panel schedule-editor">
      <div className="section-heading">
        <h2>{t.availability.edit}: {schedule.name}</h2>
        <div className="button-row">
          <Button variant="ghost" onClick={onCancel}>
            {t.common.cancel}
          </Button>
          <Button variant="primary" onClick={() => void save()} disabled={busy}>
            {busy ? t.availability.saving : t.availability.save}
          </Button>
        </div>
      </div>

      <div className="stack">
        <TextField label={t.availability.fieldName} value={name} onChange={setName} />
        <div className="field">
          <span className="field-label">{t.availability.fieldTimeZone}</span>
          <SelectField value={timeZone} onValueChange={setTimeZone} options={tzOptions} />
        </div>
        <label className="switch-field">
          <Switch.Root checked={isDefault} onCheckedChange={(checked) => setIsDefault(checked === true)} className="switch">
            <Switch.Thumb className="switch-thumb" />
          </Switch.Root>
          <span>{t.availability.setDefault}</span>
        </label>
      </div>

      <div className="availability-list">
        {rules.map((rule, index) => (
          <div className="availability-row" key={`rule-${index}`}>
            <div className="weekday-list">
              {weekdays.map((day) => {
                const checked = rule.days.includes(day);
                return (
                  <Checkbox.Root
                    key={day}
                    checked={checked}
                    onCheckedChange={(value) => toggleDay(index, day, value === true)}
                    className={cx("weekday-chip", checked && "checked")}
                    nativeButton
                    render={<button type="button" />}
                  >
                    {weekdayLabels[day]}
                  </Checkbox.Root>
                );
              })}
            </div>
            <input
              className="input"
              value={rule.startTime}
              type="time"
              onChange={(event) => updateRule(index, { startTime: event.target.value })}
            />
            <input
              className="input"
              value={rule.endTime}
              type="time"
              onChange={(event) => updateRule(index, { endTime: event.target.value })}
            />
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setRules((current) => current.filter((_, ruleIndex) => ruleIndex !== index))}
            >
              {t.availability.remove}
            </Button>
          </div>
        ))}
      </div>

      <Button
        onClick={() =>
          setRules((current) => [
            ...current,
            { days: ["monday", "tuesday", "wednesday", "thursday", "friday"], startTime: "10:00", endTime: "11:00" },
          ])
        }
      >
        {t.availability.addInterval}
      </Button>

      <div className="section-heading">
        <h3>{t.availability.overridesTitle}</h3>
      </div>
      <div className="availability-list">
        {overrides.length === 0 ? <p className="muted">{t.availability.noOverrides}</p> : null}
        {overrides.map((override, index) => (
          <div className="availability-row" key={`override-${index}`}>
            <input
              className="input"
              type="date"
              value={override.date}
              onChange={(event) => updateOverride(index, { date: event.target.value })}
            />
            <label className="switch-field">
              <Switch.Root
                checked={override.unavailable}
                onCheckedChange={(checked) => updateOverride(index, { unavailable: checked === true })}
                className="switch"
              >
                <Switch.Thumb className="switch-thumb" />
              </Switch.Root>
              <span>{t.availability.overrideAway}</span>
            </label>
            {!override.unavailable ? (
              <>
                <input
                  className="input"
                  type="time"
                  value={override.startTime ?? "09:00"}
                  onChange={(event) => updateOverride(index, { startTime: event.target.value })}
                />
                <input
                  className="input"
                  type="time"
                  value={override.endTime ?? "17:00"}
                  onChange={(event) => updateOverride(index, { endTime: event.target.value })}
                />
              </>
            ) : null}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setOverrides((current) => current.filter((_, i) => i !== index))}
            >
              {t.availability.removeOverride}
            </Button>
          </div>
        ))}
      </div>

      <Button
        onClick={() =>
          setOverrides((current) => [
            ...current,
            { date: new Date().toISOString().slice(0, 10), unavailable: true },
          ])
        }
      >
        {t.availability.addOverride}
      </Button>
    </section>
  );
}
