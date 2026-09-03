import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { ConfirmActions } from "../components/confirm/ConfirmActions";
import { ConfirmHero } from "../components/confirm/ConfirmHero";
import { ConfirmInviteCard } from "../components/confirm/ConfirmInviteCard";
import { ConfirmPartnerB } from "../components/confirm/ConfirmPartnerB";
import { PlayLayout } from "../components/play/PlayLayout";
import { useConfirmation } from "../hooks/useConfirmation";
import { ErrorMessage } from "../shared/ui/ErrorMessage";
import { LoadingState } from "../shared/ui/LoadingState";
import {
  isGameReadyToPlay,
  isPlayerBSetupComplete,
} from "../shared/gameNavigation";

export function ConfirmationPage() {
  const { t } = useTranslation();
  const {
    game,
    gameId,
    inviteUrl,
    isLoading,
    error,
    hasActiveRunA,
    hasActiveRunB,
    onCopyInvite,
    inviteCopied,
    inviteCopyError,
  } = useConfirmation();

  if (isLoading) {
    return (
      <PlayLayout contentClassName="mx-auto max-w-3xl px-6 py-8">
        <LoadingState message={t("common.loading")} />
      </PlayLayout>
    );
  }

  if (error || !game || !gameId) {
    return (
      <PlayLayout contentClassName="mx-auto max-w-3xl space-y-4 px-6 py-8">
        <ErrorMessage message={error ?? t("errors.gameNotFound")} />
        <Link
          to="/lobby"
          className="inline-block text-sm font-medium text-slate-500 hover:text-slate-800"
        >
          {t("game.confirm.backToLobby")}
        </Link>
      </PlayLayout>
    );
  }

  return (
    <PlayLayout contentClassName="mx-auto max-w-3xl space-y-6 px-6 py-8">
      <ConfirmHero
        matchName={game.match_name}
        gameMode={game.game_mode}
        partnerName={game.partner_a.name}
        sex={game.partner_a.sex}
        avatarConfig={game.partner_a.avatar_config ?? {}}
        seed={gameId}
      />
      {game.partner_b ? (
        <ConfirmPartnerB
          name={game.partner_b.name}
          sex={game.partner_b.sex}
          avatarConfig={game.partner_b.avatar_config ?? {}}
          seed={gameId}
        />
      ) : null}
      <ConfirmActions
        gameId={gameId}
        canPlay={isGameReadyToPlay(game)}
        hasActiveRunA={hasActiveRunA}
        hasActiveRunB={hasActiveRunB}
        partnerBComplete={isPlayerBSetupComplete(game)}
      />
      {inviteUrl ? (
        <ConfirmInviteCard
          inviteUrl={inviteUrl}
          onCopy={onCopyInvite}
          copied={inviteCopied}
          copyError={inviteCopyError}
        />
      ) : null}
      <p className="text-center text-sm leading-relaxed text-slate-500">
        {t("game.confirm.hint")}
      </p>
    </PlayLayout>
  );
}
