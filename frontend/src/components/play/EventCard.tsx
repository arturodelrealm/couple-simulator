import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

export type EventCardProps = {
  title: string;
  description: string | null;
  children?: ReactNode;
};

const EVENT_BACKGROUND = "#EFF6FF";
const EVENT_ACCENT = "#3B82F6";

export function EventCard({ title, description, children }: EventCardProps) {
  const { t } = useTranslation();

  return (
    <div
      className="overflow-hidden rounded-3xl border border-purple-50 shadow-sm"
      style={{ background: EVENT_BACKGROUND }}
    >
      <div className="px-8 py-6">
        <span
          className="mb-3 inline-block rounded-full px-2.5 py-1 text-xs font-semibold"
          style={{
            color: EVENT_ACCENT,
            background: `${EVENT_ACCENT}18`,
          }}
        >
          {t("game.play.lifeEvent")}
        </span>
        <h2 className="mb-2 font-display text-2xl font-extrabold leading-tight text-slate-800">
          {title}
        </h2>
        {description ? (
          <p className="text-sm leading-relaxed text-slate-600">
            {description}
          </p>
        ) : null}
        {children ? (
          <div className="mt-5 space-y-3 border-t border-black/5 pt-5">
            {children}
          </div>
        ) : null}
      </div>
    </div>
  );
}
