import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import type { TimelineEntry } from "../../services/simulationService";
import { STAT_CONFIG } from "../../shared/play/statConfig";
import { translateContent } from "../../shared/play/translateContent";
import { ErrorMessage } from "../../shared/ui/ErrorMessage";
import type { StatsBarValues } from "./StatsBar";
import { PlayRefreshIcon } from "./playIcons";

export type GameOverScreenProps = {
  partnerAName: string;
  partnerBName: string;
  partnerAAge: number;
  partnerBAge: number;
  stats: StatsBarValues;
  timeline: TimelineEntry[];
  matches: number;
  compared: number;
  onPlayAgain: () => void;
  playAgainDisabled?: boolean;
  errorMessage?: string | null;
};

export function GameOverScreen({
  partnerAName,
  partnerBName,
  partnerAAge,
  partnerBAge,
  stats,
  timeline,
  matches,
  compared,
  onPlayAgain,
  playAgainDisabled = false,
  errorMessage = null,
}: GameOverScreenProps) {
  const { t } = useTranslation();

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f5f0ff] p-8">
      <div className="w-full max-w-lg rounded-3xl bg-white p-10 text-center shadow-xl">
        <h1 className="mb-2 font-display text-3xl font-extrabold text-slate-800">
          {t("game.play.gameOver.title")}
        </h1>
        <p className="mb-6 text-slate-500">
          {t("game.play.gameOver.ages", {
            partnerAName,
            partnerAAge,
            partnerBName,
            partnerBAge,
          })}
        </p>
        <p className="mb-6 text-sm font-medium text-slate-600">
          {t("game.play.gameOver.agreements", {
            matches,
            compared,
          })}
        </p>
        <div className="mb-8 grid grid-cols-2 gap-3 sm:grid-cols-3">
          {STAT_CONFIG.map((stat) => (
            <div
              key={stat.key}
              className="rounded-xl p-3"
              style={{ background: stat.background }}
            >
              <div className="mb-1 flex justify-center">
                <stat.Icon
                  className="h-[18px] w-[18px]"
                  style={{ color: stat.color }}
                />
              </div>
              <div
                className="font-display text-lg font-bold"
                style={{ color: stat.color }}
              >
                {stats[stat.key]}
              </div>
              <div className="text-xs text-slate-500">{t(stat.labelKey)}</div>
            </div>
          ))}
        </div>
        <div className="mb-6 max-h-40 overflow-y-auto rounded-2xl bg-slate-50 p-4 text-left">
          <p className="mb-2 font-display text-sm font-bold text-slate-700">
            {t("game.play.gameOver.yourStory")}
          </p>
          {timeline.length === 0 ? (
            <p className="text-xs text-slate-400">
              {t("game.play.timeline.empty")}
            </p>
          ) : (
            timeline.map((entry, index) => (
              <p
                key={`${entry.title}-${entry.age}-${index}`}
                className="border-b border-slate-100 py-1 text-xs text-slate-500 last:border-0"
              >
                {t("game.play.eventYear", { year: entry.age })} —{" "}
                {translateContent(entry.title)}
              </p>
            ))
          )}
        </div>
        {errorMessage ? (
          <div className="mb-4">
            <ErrorMessage message={errorMessage} />
          </div>
        ) : null}
        <div className="flex flex-col gap-3">
          <button
            type="button"
            onClick={onPlayAgain}
            disabled={playAgainDisabled}
            className="flex w-full items-center justify-center gap-2 rounded-2xl py-3 font-display text-base font-bold text-white transition-all hover:opacity-90 active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
            style={{ background: "linear-gradient(135deg, #a78bfa, #f472b6)" }}
          >
            <PlayRefreshIcon className="h-4 w-4" />
            {t("game.play.gameOver.playAgain")}
          </button>
          <Link
            to="/lobby"
            className="block w-full rounded-2xl border-2 border-purple-100 bg-white px-5 py-3 text-center font-display text-base font-bold text-slate-700 transition-all hover:border-purple-300 hover:bg-purple-50"
          >
            {t("game.nav.backToLobby")}
          </Link>
        </div>
      </div>
    </div>
  );
}
