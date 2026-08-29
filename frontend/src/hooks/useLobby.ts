import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { ApiClientError } from "../services/apiClient";
import { getGame } from "../services/gameService";
import {
  clearCurrentGame,
  getCurrentGame,
  saveCurrentGameFromGame,
  type StoredCurrentGame,
} from "../shared/gameStorage";
import { toErrorMessage } from "../shared/errors";
import { getGameStepPath } from "../shared/gameNavigation";

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
