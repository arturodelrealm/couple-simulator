import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";

import {
  getGame,
  getGameInvite,
  type Game,
  type GameInvite,
} from "../services/gameService";
import { getPartnerAQuestionnaire } from "../services/partnerAQuestionnaireService";
import {
  listSimulationRuns,
  type SimulationRunList,
} from "../services/simulationService";
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
  const [continueQuestionnaire, setContinueQuestionnaire] = useState(false);
  const [questionnaireProgress, setQuestionnaireProgress] = useState<{
    current: number;
    total: number;
  } | null>(null);
  const [hasActiveRunB, setHasActiveRunB] = useState(false);

  useEffect(() => {
    if (!gameId) {
      setError(t("errors.gameNotFound"));
      setIsLoading(false);
      return;
    }

    const emptyRunList: SimulationRunList = {
      items: [],
      pagination: { page: 1, per_page: 1, total: 0 },
    };

    Promise.all([
      getGame(gameId),
      getGameInvite(gameId),
      getPartnerAQuestionnaire(gameId).catch(() => null),
      listSimulationRuns(gameId, {
        status: "ACTIVE",
        player_role: "partner_b",
        page: 1,
        per_page: 1,
      }).catch(() => emptyRunList),
    ])
      .then(([loaded, loadedInvite, questionnaire, runsB]) => {
        saveCurrentGameFromGame(loaded);
        touchCurrentGame();
        if (!isPlayerASetupComplete(loaded)) {
          navigate(`/games/${gameId}/player-a`, { replace: true });
          return;
        }
        setGame(loaded);
        setInvite(loadedInvite);
        if (questionnaire) {
          const done =
            questionnaire.progress.answered + questionnaire.progress.skipped;
          setContinueQuestionnaire(done > 0);
          setQuestionnaireProgress({
            current: done,
            total: questionnaire.progress.total,
          });
        }
        setHasActiveRunB(runsB.items.length > 0);
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
    hasActiveRunB,
    continueQuestionnaire,
    questionnaireProgress,
    onCopyInvite,
    inviteCopied,
    inviteCopyError,
  };
}
