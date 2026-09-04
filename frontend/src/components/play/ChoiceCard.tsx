type ChoiceCardProps = {
  index: number;
  text: string;
  onSelect: () => void;
  disabled?: boolean;
  selected?: boolean;
  partnerPicked?: boolean;
  partnerLabel?: string;
};

function choiceLetter(index: number): string {
  if (index >= 0 && index < 26) {
    return String.fromCharCode(65 + index);
  }
  return String(index + 1);
}

export function ChoiceCard({
  index,
  text,
  onSelect,
  disabled = false,
  selected = false,
  partnerPicked = false,
  partnerLabel,
}: ChoiceCardProps) {
  const matched = selected && partnerPicked;
  const borderClass = matched
    ? "border-emerald-400 bg-emerald-50"
    : partnerPicked
      ? "border-amber-400 bg-amber-50"
      : selected
        ? "border-purple-400 bg-purple-50"
        : "border-purple-100";

  return (
    <button
      type="button"
      onClick={onSelect}
      disabled={disabled}
      aria-pressed={selected}
      className={`group w-full rounded-2xl border-2 bg-white px-5 py-4 text-left transition-all duration-200 hover:border-purple-300 hover:bg-purple-50 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-purple-300 disabled:cursor-not-allowed disabled:pointer-events-none ${borderClass}`}
    >
      <div className="flex items-center gap-4">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-purple-100 transition-colors group-hover:bg-purple-200">
          <span className="font-display text-sm font-extrabold text-purple-700">
            {choiceLetter(index)}
          </span>
        </div>
        <p className="min-w-0 flex-1 font-display text-sm font-bold leading-snug text-slate-800">
          {text}
        </p>
        {partnerPicked && partnerLabel ? (
          <span className="shrink-0 rounded-full bg-amber-200 px-2 py-0.5 text-xs font-semibold text-amber-900">
            {partnerLabel}
          </span>
        ) : null}
      </div>
    </button>
  );
}
