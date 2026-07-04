import { useState } from "react";
import type { FormEvent } from "react";
import { Form } from "@base-ui-components/react/form";
import { Modal, DialogClose } from "../../components/ui/Modal";
import { Button } from "../../components/ui/Button";
import { TextField } from "../../components/ui/TextField";
import { NumberInput } from "../../components/ui/NumberInput";
import { SelectField } from "../../components/ui/SelectField";
import { api } from "../../lib/api";
import { asErrorMessage, slugify } from "../../lib/utils";
import { useToast } from "../../components/ui/toast";
import { policyOptions, t } from "../../lib/i18n";
import type { ConfirmationPolicyType, Schedule } from "../../lib/types";

type CreateEventTypeDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  token: string;
  schedules: Schedule[];
  onCreated: () => void;
};

export function CreateEventTypeDialog({ open, onOpenChange, token, schedules, onCreated }: CreateEventTypeDialogProps) {
  const toast = useToast();
  const [title, setTitle] = useState("Консультация");
  const [slug, setSlug] = useState("consultation");
  const [duration, setDuration] = useState(30);
  const [policy, setPolicy] = useState<ConfirmationPolicyType>("host");
  const [description, setDescription] = useState("Обсудим цели, объём работ и следующие шаги.");
  const [busy, setBusy] = useState(false);

  async function createEventType() {
    setBusy(true);
    try {
      await api.createEventType(token, {
        title,
        slug,
        description,
        durationMinutes: duration,
        scheduleId: schedules[0]?.id,
        slotIntervalMinutes: 15,
        afterEventBufferMinutes: 15,
        confirmationPolicy: {
          type: policy,
          blockSlotBeforeConfirmation: policy !== "automatic",
        },
      });
      toast.success(t.eventTypes.created, title);
      onCreated();
      onOpenChange(false);
    } catch (error) {
      toast.error(t.eventTypes.createError, asErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    await createEventType();
  }

  return (
    <Modal
      open={open}
      onOpenChange={onOpenChange}
      title={t.eventTypes.createTitle}
      description={t.eventTypes.createSubtitle}
      footer={
        <>
          <DialogClose className="btn btn-ghost">{t.common.cancel}</DialogClose>
          <Button
            variant="primary"
            type="button"
            onClick={() => void createEventType()}
            disabled={busy || schedules.length === 0}
          >
            {busy ? t.eventTypes.creating : t.eventTypes.createSubmit}
          </Button>
        </>
      }
    >
      <Form id="create-event-type" className="stack" onSubmit={submit}>
        <TextField label={t.eventTypes.fieldTitle} value={title} onChange={setTitle} required />
        <TextField label={t.eventTypes.fieldSlug} value={slug} onChange={(value) => setSlug(slugify(value))} required />
        <NumberInput label={t.eventTypes.fieldDuration} value={duration} onChange={setDuration} min={15} step={15} />
        <div className="field">
          <span className="field-label">{t.eventTypes.fieldConfirmation}</span>
          <SelectField value={policy} onValueChange={setPolicy} options={policyOptions} />
        </div>
        <TextField label={t.eventTypes.fieldDescription} value={description} onChange={setDescription} multiline />
      </Form>
    </Modal>
  );
}
