import type { ReactNode } from "react";
import { Field } from "@base-ui-components/react/field";

type TextFieldProps = {
  label: ReactNode;
  value: string;
  onChange: (value: string) => void;
  type?: "text" | "email" | "password" | "time" | "date";
  placeholder?: string;
  required?: boolean;
  multiline?: boolean;
  rows?: number;
  hint?: ReactNode;
};

export function TextField({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
  required,
  multiline,
  rows = 4,
  hint,
}: TextFieldProps) {
  return (
    <Field.Root className="field">
      <Field.Label className="field-label">{label}</Field.Label>
      {multiline ? (
        <Field.Control
          render={<textarea rows={rows} />}
          className="input textarea"
          value={value}
          required={required}
          placeholder={placeholder}
          onChange={(event) => onChange(event.target.value)}
        />
      ) : (
        <Field.Control
          className="input"
          type={type}
          value={value}
          required={required}
          placeholder={placeholder}
          onChange={(event) => onChange(event.target.value)}
        />
      )}
      {hint ? <Field.Description className="field-hint">{hint}</Field.Description> : null}
    </Field.Root>
  );
}
