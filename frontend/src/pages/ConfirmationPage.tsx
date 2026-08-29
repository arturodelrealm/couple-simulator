import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { useConfirmation } from "../hooks/useConfirmation";
import type { PlayerSex } from "../services/gameService";
import { AvatarPreview } from "../shared/ui/AvatarPreview";
import { GameLayout } from "../shared/ui/GameLayout";
import { LoadingState } from "../shared/ui/LoadingState";
import { ErrorMessage } from "../shared/ui/ErrorMessage";
import { PrimaryButton } from "../shared/ui/PrimaryButton";

const SEX_LABEL_KEYS: Record<PlayerSex, string> = {
  male: "game.playerA.sex.male",
  female: "game.playerA.sex.female",
  prefer_not_to_say: "game.playerA.sex.preferNotToSay",
};

export function ConfirmationPage() {
  const { t } = useTranslation();
  const {
    game,
    gameId,
    inviteUrl,
    isLoading,
    error,
    onCopyInvite,
    inviteCopied,
    inviteCopyError,
  } = useConfirmation();

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
            to="/lobby"
            className="text-sm font-medium text-indigo-600 hover:text-indigo-700"
          >
            {t("game.confirm.backToLobby")}
          </Link>
        </div>
      </GameLayout>
    );
  }

  const avatarConfig = game.partner_a.avatar_config ?? {};
  const sex = game.partner_a.sex;

  return (
    <GameLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between gap-4">
          <h1 className="text-2xl font-bold text-slate-900">
            {t("game.confirm.title")}
          </h1>
          <Link
            to="/lobby"
            className="text-sm font-medium text-indigo-600 hover:text-indigo-700"
          >
            {t("game.nav.backToLobby")}
          </Link>
        </div>

        <dl className="space-y-4 rounded-lg border border-slate-200 bg-white p-4 text-left">
          <div>
            <dt className="text-sm text-slate-600">
              {t("game.confirm.matchName")}
            </dt>
            <dd className="mt-1 font-mono font-medium text-slate-900">
              {game.match_name}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-slate-600">
              {t("game.confirm.gameMode")}
            </dt>
            <dd className="mt-1 text-slate-900">
              {t(`game.create.gameMode.${game.game_mode}`)}
            </dd>
          </div>
        </dl>

        {inviteUrl && (
          <div className="space-y-2 rounded-lg border border-slate-200 bg-white p-4">
            <p className="text-sm font-medium text-slate-700">
              {t("game.confirm.inviteLabel")}
            </p>
            <p className="text-sm text-slate-600">
              {t("game.confirm.inviteHint")}
            </p>
            <input
              type="text"
              readOnly
              value={inviteUrl}
              className="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 font-mono text-sm text-slate-700"
            />
            <PrimaryButton onClick={onCopyInvite} className="w-full">
              {inviteCopied
                ? t("game.confirm.inviteCopied")
                : t("game.confirm.copyInviteLink")}
            </PrimaryButton>
            {inviteCopyError && <ErrorMessage message={inviteCopyError} />}
          </div>
        )}

        <div className="space-y-4 text-center">
          <p className="text-lg font-medium text-slate-800">
            {game.partner_a.name}
          </p>
          {sex && (
            <p className="text-sm text-slate-600">
              {t("game.confirm.sexLabel")}: {t(SEX_LABEL_KEYS[sex])}
            </p>
          )}
          <AvatarPreview config={avatarConfig} seed={gameId} size={180} />
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <Link to={`/games/${gameId}/player-a`} className="flex-1">
            <PrimaryButton className="w-full">
              {t("game.confirm.editPlayerA")}
            </PrimaryButton>
          </Link>
          <Link to="/lobby" className="flex-1">
            <PrimaryButton className="w-full bg-white text-indigo-600 ring-1 ring-indigo-600 hover:bg-indigo-50">
              {t("game.confirm.backToLobby")}
            </PrimaryButton>
          </Link>
        </div>

        <p className="text-center text-sm text-slate-600">
          {t("game.confirm.hint")}
        </p>
      </div>
    </GameLayout>
  );
}
