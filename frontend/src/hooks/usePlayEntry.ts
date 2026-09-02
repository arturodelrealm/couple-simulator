import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { ApiClientError } from "../services/apiClient";
import { getGame } from "../services/gameService";
import {
  listSimulationRuns,
  startSimulationRun,
} from "../services/simulationService";
import { toErrorMessage } from "../shared/errors";
import { getPlayPath, isGameReadyToPlay } from "../shared/gameNavigation";
import {
  clearCurrentGame,
  saveCurrentGameFromGame,
  saveCurrentRunId,
} from "../shared/gameStorage";

export function usePlayEntry() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { gameId } = useParams<{ gameId: string }>();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorCode, setErrorCode] = useState<string | null>(null);

  useEffect(() => {
    if (!gameId) {
      setError(t("errors.gameNotFound"));
      setIsLoading(false);
      return;
    }

    let cancelled = false;

    void (async () => {
      setIsLoading(true);
      setError(null);
      setErrorCode(null);
      try {
        const game = await getGame(gameId);
        if (cancelled) {
          return;
        }
        if (!isGameReadyToPlay(game)) {
          navigate(`/games/${gameId}/player-a`, { replace: true });
          return;
        }
        saveCurrentGameFromGame(game);

        const listed = await listSimulationRuns(gameId, {
          status: "ACTIVE",
          page: 1,
          per_page: 1,
        });
        if (cancelled) {
          return;
        }
        const activeRun = listed.items[0];
        if (activeRun) {
          saveCurrentRunId(activeRun.run_id);
          navigate(getPlayPath(gameId, activeRun.run_id), {
            replace: true,
          });
          return;
        }

        const created = await startSimulationRun(gameId);
        if (cancelled) {
          return;
        }
        saveCurrentRunId(created.run_id);
        navigate(getPlayPath(gameId, created.run_id), { replace: true });
      } catch (err) {
        if (cancelled) {
          return;
        }
        if (err instanceof ApiClientError && err.code === "GAME_NOT_FOUND") {
          clearCurrentGame();
        }
        if (err instanceof ApiClientError) {
          setErrorCode(err.code);
        }
        setError(toErrorMessage(err, t));
        setIsLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [gameId, navigate, t]);

  return { gameId, isLoading, error, errorCode };
}
