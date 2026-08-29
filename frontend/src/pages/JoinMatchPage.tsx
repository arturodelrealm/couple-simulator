import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { useJoinMatch } from "../hooks/useJoinMatch";
import { GameLayout } from "../shared/ui/GameLayout";
import { PrimaryButton } from "../shared/ui/PrimaryButton";
import { ErrorMessage } from "../shared/ui/ErrorMessage";

export function JoinMatchPage() {
  const { t } = useTranslation();
  const { matchName, setMatchName, onSubmit, isSubmitting, error } =
    useJoinMatch();

  return (
    <GameLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between gap-4">
          <h1 className="text-2xl font-bold text-slate-900">
            {t("game.join.title")}
          </h1>
          <Link
            to="/lobby"
            className="text-sm font-medium text-indigo-600 hover:text-indigo-700"
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
            className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            placeholder={t("game.join.matchNamePlaceholder")}
            maxLength={32}
            autoComplete="off"
          />
        </label>

        {error && <ErrorMessage message={error} />}
        <PrimaryButton onClick={onSubmit} disabled={isSubmitting}>
          {t("game.join.submit")}
        </PrimaryButton>
      </div>
    </GameLayout>
  );
}
