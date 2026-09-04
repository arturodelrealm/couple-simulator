import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { useJoinMatch } from "../hooks/useJoinMatch";
import { GameLayout } from "../shared/ui/GameLayout";
import { PrimaryButton } from "../shared/ui/PrimaryButton";
import { LoadingState } from "../shared/ui/LoadingState";
import { ErrorMessage } from "../shared/ui/ErrorMessage";

export function JoinMatchPage() {
  const { t } = useTranslation();
  const {
    matchName,
    setMatchName,
    onSubmit,
    onJoinAsPartnerB,
    isSubmitting,
    isAutoJoining,
    error,
  } = useJoinMatch();

  if (isAutoJoining) {
    return (
      <GameLayout>
        <LoadingState message={t("game.join.joining")} />
      </GameLayout>
    );
  }

  return (
    <GameLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between gap-4">
          <h1 className="text-2xl font-bold text-slate-900">
            {t("game.join.title")}
          </h1>
          <Link
            to="/lobby"
            className="text-sm font-medium text-sky-700 hover:text-sky-800"
          >
            {t("game.nav.backToLobby")}
          </Link>
        </div>

        <label className="block space-y-2">
          <span className="text-sm font-medium text-slate-700">
            {t("game.join.matchNameLabel")}
          </span>
          <input
            type="text"
            value={matchName}
            onChange={(e) => setMatchName(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            placeholder={t("game.join.matchNamePlaceholder")}
            maxLength={32}
            autoComplete="off"
          />
        </label>

        {error && <ErrorMessage message={error} />}
        <PrimaryButton onClick={onSubmit} disabled={isSubmitting}>
          {t("game.join.submit")}
        </PrimaryButton>
        <button
          type="button"
          onClick={onJoinAsPartnerB}
          disabled={isSubmitting}
          className="w-full rounded-2xl border-2 border-slate-200 bg-white px-5 py-3 text-center font-display text-base font-bold text-slate-700 transition-all hover:border-sky-300 hover:bg-sky-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {t("game.join.iamPartnerB")}
        </button>
      </div>
    </GameLayout>
  );
}
