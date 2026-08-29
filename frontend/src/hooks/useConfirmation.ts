import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { getGame, type Game } from "../services/gameService";
import {
  clearCurrentGame,
  saveCurrentGameFromGame,
  touchCurrentGame,
} from "../shared/gameStorage";
import { toErrorMessage } from "../shared/errors";
import { isPlayerASetupComplete } from "../shared/gameNavigation";

export function useConfirmation() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { gameId } = useParams<{ gameId: string }>();
  const [game, setGame] = useState<Game | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!gameId) {
      setError(t("errors.gameNotFound"));
      setIsLoading(false);
      return;
    }

    getGame(gameId)
      .then((loaded) => {
        saveCurrentGameFromGame(loaded);
        touchCurrentGame();
        if (!isPlayerASetupComplete(loaded)) {
          navigate(`/games/${gameId}/player-a`, { replace: true });
          return;
        }
        setGame(loaded);
      })
      .catch((err) => {
        clearCurrentGame();
        setError(toErrorMessage(err, t));
      })
      .finally(() => setIsLoading(false));
  }, [gameId, navigate, t]);

  return { game, gameId, isLoading, error };
}
