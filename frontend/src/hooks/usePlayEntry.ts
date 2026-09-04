import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { ApiClientError } from "../services/apiClient";
import { getGame } from "../services/gameService";
import {
  listSimulationRuns,
  startSimulationRun,
} from "../services/simulationService";
import { toErrorMessage } from "../shared/errors";
import {
  getConfirmPath,
  getPartnerAQuestionnairePath,
  getPlayPath,
  getPlayerBSetupPath,
  isGameReadyToPlay,
  isPlayerBSetupComplete,
  parsePlayPlayerRole,
} from "../shared/gameNavigation";
import {
  clearCurrentGame,
  saveCurrentGameFromGame,
  saveCurrentRunId,
} from "../shared/gameStorage";

export function usePlayEntry() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { gameId } = useParams<{ gameId: string }>();
  const [searchParams] = useSearchParams();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorCode, setErrorCode] = useState<string | null>(null);
  const playerRole = parsePlayPlayerRole(searchParams.get("role"));

  useEffect(() => {
    if (!gameId) {
      setError(t("errors.gameNotFound"));
      setIsLoading(false);
      return;
    }

    if (playerRole === null) {
      navigate(getConfirmPath(gameId), { replace: true });
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

        if (playerRole === "partner_a") {
          navigate(getPartnerAQuestionnairePath(gameId), { replace: true });
          return;
        }

        if (playerRole === "partner_b" && !isPlayerBSetupComplete(game)) {
          navigate(getPlayerBSetupPath(gameId), { replace: true });
          return;
        }

        if (!isGameReadyToPlay(game)) {
          navigate(`/games/${gameId}/player-a`, { replace: true });
          return;
        }
        saveCurrentGameFromGame(game);

        const listed = await listSimulationRuns(gameId, {
          status: "ACTIVE",
          player_role: playerRole,
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

        const created = await startSimulationRun(gameId, {
          player_role: playerRole,
        });
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
  }, [gameId, navigate, playerRole, t]);

  return { gameId, isLoading, error, errorCode, playerRole };
}
