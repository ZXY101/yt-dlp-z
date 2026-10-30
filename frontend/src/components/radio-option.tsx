interface RadioOptionProps {
  name: string;
  label: string;
  checked: boolean;
  onSelect: () => void;
}

export function RadioOption({ name, label, checked, onSelect }: RadioOptionProps) {
  return (
    <label className="flex min-h-10 cursor-pointer items-center gap-3 text-sm">
      <input
        type="radio"
        name={name}
        className="size-5 cursor-pointer accent-primary"
        checked={checked}
        onChange={onSelect}
      />
      {label}
    </label>
  );
}
