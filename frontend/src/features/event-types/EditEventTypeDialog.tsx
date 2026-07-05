import { useState } from "react";
import type { FormEvent } from "react";
import { Form } from "@base-ui-components/react/form";
import { Switch } from "@base-ui-components/react/switch";
import { Modal, DialogClose } from "../../components/ui/Modal";
import { Button } from "../../components/ui/Button";
import { TextField } from "../../components/ui/TextField";
import { NumberInput } from "../../components/ui/NumberInput";
import { SelectField } from "../../components/ui/SelectField";
import { api } from "../../lib/api";
import { asErrorMessage, slugify } from "../../lib/utils";
import { useToast } from "../../components/ui/toast";
import { policyOptions, t } from "../../lib/i18n";
import type { ConfirmationPolicyType, EventType } from "../../lib/types";

type EditEventTypeDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  token: string;
  eventType: EventType;
  onUpdated: () => void;
};

export function EditEventTypeDialog({ open, onOpenChange, token, eventType, onUpdated }: EditEventTypeDialogProps) {
  const toast = useToast();
  const [title, setTitle] = useState(eventType.title);
  const [slug, setSlug] = useState(eventType.slug);
  const [description, setDescription] = useState(eventType.description ?? "");
  const [duration, setDuration] = useState(eventType.durationMinutes);
  const [slotInterval, setSlotInterval] = useState(eventType.slotIntervalMinutes ?? eventType.durationMinutes);
  const [minNotice, setMinNotice] = useState(eventType.minimumBookingNoticeMinutes ?? 0);
  const [beforeBuffer, setBeforeBuffer] = useState(eventType.beforeEventBufferMinutes ?? 0);
  const [afterBuffer, setAfterBuffer] = useState(eventType.afterEventBufferMinutes ?? 0);
  const [rollingDays, setRollingDays] = useState(eventType.bookingWindow?.rollingDays ?? 0);
  const [policy, setPolicy] = useState<ConfirmationPolicyType>(eventType.confirmationPolicy.type);
  const [blockSlot, setBlockSlot] = useState(Boolean(eventType.confirmationPolicy.blockSlotBeforeConfirmation));
  const [hidden, setHidden] = useState(eventType.hidden);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function save() {
    const trimmedSlug = slugify(slug);
    if (!trimmedSlug) {
      setError(t.eventTypes.invalidSlug);
      return;
    }
    if (duration <= 0) {
      setError(t.eventTypes.invalidDuration);
      return;
    }
    setBusy(true);
    setError("");
    try {
      await api.updateEventType(token, eventType.id, {
        title: title.trim(),
        slug: trimmedSlug,
        description: description.trim() || undefined,
        durationMinutes: duration,
        slotIntervalMinutes: slotInterval,
        minimumBookingNoticeMinutes: minNotice,
        beforeEventBufferMinutes: beforeBuffer,
        afterEventBufferMinutes: afterBuffer,
        bookingWindow: rollingDays > 0 ? { rollingDays } : null,
        confirmationPolicy: { type: policy, blockSlotBeforeConfirmation: blockSlot },
        hidden,
      });
      toast.success(t.eventTypes.updated, title);
      onUpdated();
      onOpenChange(false);
    } catch (requestError) {
      setError(asErrorMessage(requestError));
    } finally {
      setBusy(false);
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    await save();
  }

  return (
    <Modal
      open={open}
      onOpenChange={onOpenChange}
      title={t.eventTypes.editTitle}
      description={t.eventTypes.editSubtitle}
      footer={
        <>
          <DialogClose className="btn btn-ghost">{t.common.cancel}</DialogClose>
          <Button variant="primary" type="button" onClick={() => void save()} disabled={busy}>
            {busy ? t.eventTypes.saving : t.eventTypes.editSubmit}
          </Button>
        </>
      }
    >
      <Form className="stack" onSubmit={submit}>
        {error ? <div className="banner error">{error}</div> : null}
        <TextField label={t.eventTypes.fieldTitle} value={title} onChange={setTitle} required />
        <TextField label={t.eventTypes.fieldSlug} value={slug} onChange={(value) => setSlug(slugify(value))} required />
        <TextField label={t.eventTypes.fieldDescription} value={description} onChange={setDescription} multiline />
        <NumberInput label={t.eventTypes.fieldDuration} value={duration} onChange={setDuration} min={5} step={5} />
        <NumberInput label={t.eventTypes.fieldSlotInterval} value={slotInterval} onChange={setSlotInterval} min={5} step={5} />
        <NumberInput label={t.eventTypes.fieldMinNotice} value={minNotice} onChange={setMinNotice} min={0} step={15} />
        <NumberInput label={t.eventTypes.fieldBeforeBuffer} value={beforeBuffer} onChange={setBeforeBuffer} min={0} step={5} />
        <NumberInput label={t.eventTypes.fieldAfterBuffer} value={afterBuffer} onChange={setAfterBuffer} min={0} step={5} />
        <NumberInput label={t.eventTypes.fieldRollingDays} value={rollingDays} onChange={setRollingDays} min={0} step={1} />
        <div className="field">
          <span className="field-label">{t.eventTypes.fieldConfirmation}</span>
          <SelectField value={policy} onValueChange={setPolicy} options={policyOptions} />
        </div>
        <label className="switch-field">
          <Switch.Root checked={blockSlot} onCheckedChange={(checked) => setBlockSlot(checked === true)} className="switch">
            <Switch.Thumb className="switch-thumb" />
          </Switch.Root>
          <span>{t.eventTypes.fieldBlockSlot}</span>
        </label>
        <label className="switch-field">
          <Switch.Root checked={hidden} onCheckedChange={(checked) => setHidden(checked === true)} className="switch">
            <Switch.Thumb className="switch-thumb" />
          </Switch.Root>
          <span>{t.eventTypes.fieldHidden}</span>
        </label>
      </Form>
    </Modal>
  );
}
