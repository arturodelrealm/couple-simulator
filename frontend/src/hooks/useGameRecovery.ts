import { useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { ApiClientError } from "../services/apiClient";
import { getGame } from "../services/gameService";
import {
  clearCurrentGame,
  migrateLegacyGameStorage,
} from "../shared/gameStorage";
import { getGameStepPath } from "../shared/gameNavigation";

export function useGameRecovery() {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (location.pathname !== "/") {
      return;
    }

    void migrateLegacyGameStorage()
      .then((stored) => {
        if (!stored) {
          navigate("/lobby", { replace: true });
          return;
        }

        return getGame(stored.game_id)
          .then((game) => {
            navigate(getGameStepPath(game), { replace: true });
          })
          .catch((error) => {
            if (
              error instanceof ApiClientError &&
              error.code === "GAME_NOT_FOUND"
            ) {
              clearCurrentGame();
            }
            navigate("/lobby", { replace: true });
          });
      })
      .catch(() => {
        clearCurrentGame();
        navigate("/lobby", { replace: true });
      });
  }, [location.pathname, navigate]);
}
