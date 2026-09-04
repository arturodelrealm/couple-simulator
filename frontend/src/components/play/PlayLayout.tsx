import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { theme } from "../../shared/ui/theme";
import { PlayHeartIcon } from "./playIcons";

export type PlayLayoutProps = {
  children: ReactNode;
  /** Visual fill 0–100 from events played; no max/total label (decision #11). */
  progressFillPercent?: number;
  showBackToLobby?: boolean;
  contentClassName?: string;
};

export function PlayLayout({
  children,
  progressFillPercent,
  showBackToLobby = true,
  contentClassName = "mx-auto max-w-7xl space-y-5 px-6 py-6",
}: PlayLayoutProps) {
  const { t } = useTranslation();
  const showProgress = progressFillPercent !== undefined;
  const clampedFill = Math.min(100, Math.max(0, progressFillPercent ?? 0));
  const showTrailing = showProgress || showBackToLobby;

  return (
    <div className="min-h-screen" style={{ background: theme.page }}>
      <nav className="sticky top-0 z-20 border-b border-slate-200 bg-white/80 px-6 py-3 backdrop-blur-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <PlayHeartIcon
              className="h-[18px] w-[18px]"
              style={{ color: theme.heart }}
            />
            <span className="font-display text-lg font-extrabold text-slate-800">
              {t("game.play.title")}
            </span>
          </div>
          {showTrailing ? (
            <div className="flex items-center gap-4">
              {showProgress && (
                <div className="h-2 w-32 rounded-full bg-sky-100">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${clampedFill}%`,
                      background: theme.progressGradient,
                    }}
                  />
                </div>
              )}
              {showBackToLobby ? (
                <Link
                  to="/lobby"
                  className="text-sm font-medium text-slate-500 hover:text-slate-800"
                >
                  {t("game.nav.backToLobby")}
                </Link>
              ) : null}
            </div>
          ) : null}
        </div>
      </nav>
      <main className={contentClassName}>{children}</main>
    </div>
  );
}
