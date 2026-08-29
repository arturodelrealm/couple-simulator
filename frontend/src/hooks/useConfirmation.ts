import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";

import {
  getGame,
  getGameInvite,
  type Game,
  type GameInvite,
} from "../services/gameService";
import {
  clearCurrentGame,
  saveCurrentGameFromGame,
  touchCurrentGame,
} from "../shared/gameStorage";
import { toErrorMessage } from "../shared/errors";
import { isPlayerASetupComplete } from "../shared/gameNavigation";
import { copyInviteUrl, resolveInviteUrl } from "../shared/invite";

export function useConfirmation() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { gameId } = useParams<{ gameId: string }>();
  const [game, setGame] = useState<Game | null>(null);
  const [invite, setInvite] = useState<GameInvite | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [inviteCopied, setInviteCopied] = useState(false);
  const [inviteCopyError, setInviteCopyError] = useState<string | null>(null);

  useEffect(() => {
    if (!gameId) {
      setError(t("errors.gameNotFound"));
      setIsLoading(false);
      return;
    }

    Promise.all([getGame(gameId), getGameInvite(gameId)])
      .then(([loaded, loadedInvite]) => {
        saveCurrentGameFromGame(loaded);
        touchCurrentGame();
        if (!isPlayerASetupComplete(loaded)) {
          navigate(`/games/${gameId}/player-a`, { replace: true });
          return;
        }
        setGame(loaded);
        setInvite(loadedInvite);
      })
      .catch((err) => {
        clearCurrentGame();
        setError(toErrorMessage(err, t));
      })
      .finally(() => setIsLoading(false));
  }, [gameId, navigate, t]);

  const inviteUrl =
    invite !== null
      ? resolveInviteUrl(invite.invite_path, invite.invite_url)
      : null;

  const onCopyInvite = useCallback(async () => {
    if (!inviteUrl) {
      return;
    }
    setInviteCopyError(null);
    try {
      await copyInviteUrl(inviteUrl);
      setInviteCopied(true);
      window.setTimeout(() => setInviteCopied(false), 2000);
    } catch {
      setInviteCopyError(t("errors.inviteCopyFailed"));
    }
  }, [inviteUrl, t]);

  return {
    game,
    gameId,
    inviteUrl,
    isLoading,
    error,
    onCopyInvite,
    inviteCopied,
    inviteCopyError,
  };
}
