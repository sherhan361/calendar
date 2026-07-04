import type { ReactNode } from "react";
import { NumberField } from "@base-ui-components/react/number-field";

type NumberInputProps = {
  label: ReactNode;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  hint?: ReactNode;
};

export function NumberInput({ label, value, onChange, min, max, step = 1, hint }: NumberInputProps) {
  return (
    <NumberField.Root
      className="field"
      value={value}
      min={min}
      max={max}
      step={step}
      onValueChange={(next) => onChange(next ?? min ?? 0)}
    >
      <NumberField.ScrubArea className="field-label">
        <label>{label}</label>
      </NumberField.ScrubArea>
      <NumberField.Group className="number-field">
        <NumberField.Decrement className="number-btn">−</NumberField.Decrement>
        <NumberField.Input className="input number-input" />
        <NumberField.Increment className="number-btn">+</NumberField.Increment>
      </NumberField.Group>
      {hint ? <p className="field-hint">{hint}</p> : null}
    </NumberField.Root>
  );
}
