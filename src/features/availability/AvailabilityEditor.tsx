import { useEffect, useState } from "react";
import { Checkbox } from "@base-ui-components/react/checkbox";
import { Tabs } from "@base-ui-components/react/tabs";
import { Button } from "../../components/ui/Button";
import { IconGlobe, IconMore } from "../../components/ui/icons";
import { api } from "../../lib/api";
import { asErrorMessage, cx } from "../../lib/utils";
import { useToast } from "../../components/ui/toast";
import { formatAvailabilitySummary, t } from "../../lib/i18n";
import type { AvailabilityRule, Schedule, Weekday } from "../../lib/types";

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

type AvailabilityEditorProps = {
  token: string;
  schedules: Schedule[];
  onChanged: () => void;
};

export function AvailabilityEditor({ token, schedules, onChanged }: AvailabilityEditorProps) {
  const [editingId, setEditingId] = useState<string | null>(null);

  if (schedules.length === 0) {
    return <div className="empty-state">{t.availability.empty}</div>;
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
        </div>

        <Tabs.Panel value="mine">
          <div className="schedule-list">
            {schedules.map((schedule) => (
              <ScheduleCard
                key={schedule.id}
                schedule={schedule}
                editing={editingId === schedule.id}
                onEdit={() => setEditingId(editingId === schedule.id ? null : schedule.id)}
              />
            ))}
          </div>

          {editingId ? (
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

          <p className="away-hint">
            {t.availability.awayHint}{" "}
            <button type="button" className="link-btn">
              {t.availability.awayAction}
            </button>
          </p>
        </Tabs.Panel>
      </Tabs.Root>
    </div>
  );
}

function ScheduleCard({
  schedule,
  editing,
  onEdit,
}: {
  schedule: Schedule;
  editing: boolean;
  onEdit: () => void;
}) {
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
        <button type="button" className="icon-btn" title={t.availability.edit} onClick={onEdit}>
          <IconMore />
        </button>
      </div>
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
  const [rules, setRules] = useState<AvailabilityRule[]>(schedule.availability);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setRules(schedule.availability);
  }, [schedule.id]);

  function updateRule(index: number, patch: Partial<AvailabilityRule>) {
    setRules((current) => current.map((rule, ruleIndex) => (ruleIndex === index ? { ...rule, ...patch } : rule)));
  }

  function toggleDay(index: number, day: Weekday, checked: boolean) {
    const rule = rules[index];
    const days = checked ? [...rule.days, day] : rule.days.filter((item) => item !== day);
    updateRule(index, { days });
  }

  async function save() {
    setBusy(true);
    try {
      await api.updateSchedule(token, schedule.id, { availability: rules });
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
    </section>
  );
}
