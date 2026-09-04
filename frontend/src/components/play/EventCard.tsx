import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { eventAccentForId, theme } from "../../shared/ui/theme";

export type EventCardProps = {
  title: string;
  description: string | null;
  year?: number;
  eventId?: string;
  children?: ReactNode;
};

export function EventCard({
  title,
  description,
  year,
  eventId,
  children,
}: EventCardProps) {
  const { t } = useTranslation();
  const accent = eventId ? eventAccentForId(eventId) : theme.primary;

  return (
    <div
      className="overflow-hidden rounded-3xl border border-slate-200 shadow-sm"
      style={{ background: theme.primaryLight }}
    >
      <div className="px-6 py-5 sm:px-8 sm:py-6">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <span
            className="inline-block rounded-full px-2.5 py-1 text-xs font-semibold"
            style={{
              color: accent,
              background: `${accent}18`,
            }}
          >
            {t("game.play.lifeEvent")}
          </span>
          {year !== undefined ? (
            <span className="inline-block rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">
              {t("game.play.eventYear", { year })}
            </span>
          ) : null}
        </div>
        <h2 className="mb-2 font-display text-2xl font-extrabold leading-tight text-slate-800">
          {title}
        </h2>
        {description ? (
          <p className="text-sm leading-relaxed text-slate-600">
            {description}
          </p>
        ) : null}
        {children ? (
          <div className="mt-5 space-y-3 border-t border-slate-200 pt-5">
            {children}
          </div>
        ) : null}
      </div>
    </div>
  );
}
