import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { useLobby } from "../hooks/useLobby";
import { GameLayout } from "../shared/ui/GameLayout";
import { PrimaryButton } from "../shared/ui/PrimaryButton";
import { ErrorMessage } from "../shared/ui/ErrorMessage";

export function LobbyPage() {
  const { t } = useTranslation();
  const { currentGame, onContinue, isContinuing, error } = useLobby();

  return (
    <GameLayout>
      <div className="space-y-8">
        <h1 className="text-2xl font-bold text-slate-900">
          {t("game.lobby.title")}
        </h1>

        <div className="space-y-3">
          <Link to="/games/new" className="block">
            <PrimaryButton className="w-full">
              {t("game.lobby.createButton")}
            </PrimaryButton>
          </Link>
          <Link to="/games/join" className="block">
            <PrimaryButton className="w-full bg-white text-indigo-600 ring-1 ring-indigo-600 hover:bg-indigo-50">
              {t("game.lobby.joinButton")}
            </PrimaryButton>
          </Link>
        </div>

        {currentGame && (
          <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-3">
            <p className="text-sm text-slate-600">
              {t("game.lobby.currentMatchLabel")}
            </p>
            <p className="font-mono text-lg font-medium text-slate-900">
              {currentGame.match_name}
            </p>
            <PrimaryButton
              onClick={onContinue}
              disabled={isContinuing}
              className="w-full"
            >
              {t("game.lobby.continueCurrent")}
            </PrimaryButton>
          </div>
        )}

        {error && <ErrorMessage message={error} />}
      </div>
    </GameLayout>
  );
}
