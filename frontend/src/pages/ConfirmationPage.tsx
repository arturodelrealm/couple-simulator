import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { useConfirmation } from "../hooks/useConfirmation";
import { AvatarPreview } from "../shared/ui/AvatarPreview";
import { GameLayout } from "../shared/ui/GameLayout";
import { LoadingState } from "../shared/ui/LoadingState";
import { ErrorMessage } from "../shared/ui/ErrorMessage";

export function ConfirmationPage() {
  const { t } = useTranslation();
  const { game, gameId, isLoading, error } = useConfirmation();

  if (isLoading) {
    return (
      <GameLayout>
        <LoadingState message={t("common.loading")} />
      </GameLayout>
    );
  }

  if (error || !game || !gameId) {
    return (
      <GameLayout>
        <div className="space-y-4">
          <ErrorMessage message={error ?? t("errors.gameNotFound")} />
          <Link
            to="/create"
            className="text-sm font-medium text-indigo-600 hover:text-indigo-700"
          >
            {t("game.confirm.backToCreate")}
          </Link>
        </div>
      </GameLayout>
    );
  }

  const avatarConfig = game.partner_a.avatar_config ?? {};

  return (
    <GameLayout>
      <div className="space-y-6 text-center">
        <h1 className="text-2xl font-bold text-slate-900">
          {t("game.confirm.title")}
        </h1>
        <p className="text-lg font-medium text-slate-800">
          {game.partner_a.name}
        </p>
        <AvatarPreview config={avatarConfig} seed={gameId} size={180} />
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <p className="text-sm text-slate-600">
            {t("game.confirm.gameIdLabel")}
          </p>
          <p className="mt-1 font-mono text-sm text-slate-900">{game.id}</p>
        </div>
        <p className="text-sm text-slate-600">{t("game.confirm.hint")}</p>
      </div>
    </GameLayout>
  );
}
