import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { useCreateMatch } from "../hooks/useCreateMatch";
import { GameLayout } from "../shared/ui/GameLayout";
import { PrimaryButton } from "../shared/ui/PrimaryButton";
import { ErrorMessage } from "../shared/ui/ErrorMessage";

export function CreateMatchPage() {
  const { t } = useTranslation();
  const { matchName, setMatchName, gameMode, onSubmit, isSubmitting, error } =
    useCreateMatch();

  return (
    <GameLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between gap-4">
          <h1 className="text-2xl font-bold text-slate-900">
            {t("game.create.title")}
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
            {t("game.create.matchNameLabel")}
          </span>
          <input
            type="text"
            value={matchName}
            onChange={(e) => setMatchName(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            placeholder={t("game.create.matchNamePlaceholder")}
            maxLength={32}
            autoComplete="off"
          />
          <p className="text-sm text-slate-500">
            {t("game.create.matchNameHint")}
          </p>
        </label>

        <label className="block space-y-2">
          <span className="text-sm font-medium text-slate-700">
            {t("game.create.gameModeLabel")}
          </span>
          <select
            value={gameMode}
            disabled
            className="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-slate-700"
          >
            <option value="couple">{t("game.create.gameMode.couple")}</option>
          </select>
        </label>

        {error && <ErrorMessage message={error} />}
        <PrimaryButton onClick={onSubmit} disabled={isSubmitting}>
          {t("game.create.submit")}
        </PrimaryButton>
      </div>
    </GameLayout>
  );
}
