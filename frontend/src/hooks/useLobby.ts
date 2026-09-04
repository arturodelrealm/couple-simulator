import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { ApiClientError } from "../services/apiClient";
import { getGame } from "../services/gameService";
import { getPartnerAQuestionnaire } from "../services/partnerAQuestionnaireService";
import { listSimulationRuns } from "../services/simulationService";
import {
  clearCurrentGame,
  getCurrentGame,
  saveCurrentGameFromGame,
  saveCurrentRunId,
  type StoredCurrentGame,
} from "../shared/gameStorage";
import { toErrorMessage } from "../shared/errors";
import {
  getGameStepPath,
  getPartnerAQuestionnairePath,
  getPlayPath,
} from "../shared/gameNavigation";

export function useLobby() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [currentGame] = useState<StoredCurrentGame | null>(() =>
    getCurrentGame(),
  );
  const [isContinuing, setIsContinuing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onContinue = useCallback(async () => {
    if (!currentGame) {
      return;
    }

    setIsContinuing(true);
    setError(null);
    try {
      const game = await getGame(currentGame.game_id);
      saveCurrentGameFromGame(game);
      try {
        const questionnaire = await getPartnerAQuestionnaire(game.id);
        if (!questionnaire.progress.complete) {
          navigate(getPartnerAQuestionnairePath(game.id));
          return;
        }
      } catch (err) {
        if (!(err instanceof ApiClientError && err.code === "GAME_NOT_READY")) {
          throw err;
        }
      }
      const listed = await listSimulationRuns(game.id, {
        status: "ACTIVE",
        player_role: "partner_b",
        page: 1,
        per_page: 1,
      });
      const activeRun = listed.items[0];
      if (activeRun) {
        saveCurrentRunId(activeRun.run_id);
        navigate(getPlayPath(game.id, activeRun.run_id));
        return;
      }
      navigate(getGameStepPath(game));
    } catch (err) {
      if (err instanceof ApiClientError && err.code === "GAME_NOT_FOUND") {
        clearCurrentGame();
      }
      setError(toErrorMessage(err, t));
    } finally {
      setIsContinuing(false);
    }
  }, [currentGame, navigate, t]);

  return { currentGame, onContinue, isContinuing, error };
}
