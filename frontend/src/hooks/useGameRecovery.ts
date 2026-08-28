import { useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { getGame } from "../services/gameService";
import {
  clearCurrentGame,
  migrateLegacyGameStorage,
} from "../shared/gameStorage";

export function useGameRecovery() {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const isRecoveryRoute =
      location.pathname === "/" || location.pathname === "/create";
    if (!isRecoveryRoute) return;

    void migrateLegacyGameStorage()
      .then((stored) => {
        if (!stored) return;

        return getGame(stored.game_id).then((game) => {
          if (game.partner_a.avatar_config) {
            navigate(`/games/${stored.game_id}/confirm`, { replace: true });
          } else {
            navigate(`/games/${stored.game_id}/avatar`, { replace: true });
          }
        });
      })
      .catch(() => {
        clearCurrentGame();
      });
  }, [location.pathname, navigate]);
}
