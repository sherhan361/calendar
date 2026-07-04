import { Select } from "@base-ui-components/react/select";

export type SelectOption<T extends string> = {
  value: T;
  label: string;
};

type SelectFieldProps<T extends string> = {
  value: T;
  onValueChange: (value: T) => void;
  options: ReadonlyArray<SelectOption<T>>;
  id?: string;
};

export function SelectField<T extends string>({ value, onValueChange, options, id }: SelectFieldProps<T>) {
  return (
    <Select.Root
      id={id}
      value={value}
      items={options as Array<{ value: T; label: string }>}
      onValueChange={(next) => onValueChange(next as T)}
    >
      <Select.Trigger className="select-trigger">
        <Select.Value />
        <Select.Icon className="select-icon">▾</Select.Icon>
      </Select.Trigger>
      <Select.Portal>
        <Select.Positioner className="select-positioner" sideOffset={6}>
          <Select.Popup className="select-popup">
            {options.map((option) => (
              <Select.Item key={option.value} value={option.value} className="select-item">
                <Select.ItemText>{option.label}</Select.ItemText>
                <Select.ItemIndicator className="select-indicator">✓</Select.ItemIndicator>
              </Select.Item>
            ))}
          </Select.Popup>
        </Select.Positioner>
      </Select.Portal>
    </Select.Root>
  );
}
