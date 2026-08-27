import type { ReactNode } from "react";

type OptionCardProps = {
  selected: boolean;
  onSelect: () => void;
  children: ReactNode;
  label: string;
};

export function OptionCard({
  selected,
  onSelect,
  children,
  label,
}: OptionCardProps) {
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-label={label}
      aria-pressed={selected}
      className={`flex flex-col items-center rounded-lg border-2 p-2 transition-colors ${
        selected
          ? "border-indigo-600 bg-indigo-50"
          : "border-slate-200 bg-white hover:border-slate-300"
      }`}
    >
      {children}
    </button>
  );
}
