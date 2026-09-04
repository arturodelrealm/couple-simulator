import { useTranslation } from "react-i18next";

import {
  STAT_CONFIG,
  type SimulationStatKey,
} from "../../shared/play/statConfig";

export type StatsBarValues = Record<SimulationStatKey, number>;

export type StatsBarProps = {
  values: StatsBarValues;
  orientation?: "horizontal" | "vertical";
};

function StatMeter({
  label,
  value,
  color,
  background,
  isCount,
  Icon,
}: {
  label: string;
  value: number;
  color: string;
  background: string;
  isCount: boolean;
  Icon: (typeof STAT_CONFIG)[number]["Icon"];
}) {
  const barWidth = Math.min(100, Math.max(0, value));
  const chipCount = Math.max(4, value + 1);

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Icon className="h-3.5 w-3.5" style={{ color }} />
          <span className="text-xs font-medium text-slate-500">{label}</span>
        </div>
        <span className="font-display text-sm font-bold" style={{ color }}>
          {value}
          {!isCount && (
            <span className="ml-0.5 text-xs font-medium text-slate-400">
              /100
            </span>
          )}
        </span>
      </div>
      {isCount ? (
        <div className="flex gap-1">
          {Array.from({ length: chipCount }, (_, index) => (
            <div
              key={index}
              className="h-2 flex-1 rounded-full transition-all duration-500"
              style={{ background: index < value ? color : background }}
            />
          ))}
        </div>
      ) : (
        <div
          className="h-2 w-full overflow-hidden rounded-full"
          style={{ background }}
        >
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{ width: `${barWidth}%`, background: color }}
          />
        </div>
      )}
    </div>
  );
}

export function StatsBar({
  values,
  orientation = "horizontal",
}: StatsBarProps) {
  const { t } = useTranslation();
  const isVertical = orientation === "vertical";

  return (
    <aside
      className={`rounded-3xl border border-slate-200 bg-white shadow-sm ${
        isVertical ? "p-5" : "px-8 py-5"
      }`}
    >
      <div
        className={
          isVertical
            ? "flex flex-col gap-5"
            : "grid grid-cols-2 gap-6 lg:grid-cols-5"
        }
      >
        {STAT_CONFIG.map((stat) => (
          <StatMeter
            key={stat.key}
            label={t(stat.labelKey)}
            value={values[stat.key]}
            color={stat.color}
            background={stat.background}
            isCount={stat.isCount}
            Icon={stat.Icon}
          />
        ))}
      </div>
    </aside>
  );
}
