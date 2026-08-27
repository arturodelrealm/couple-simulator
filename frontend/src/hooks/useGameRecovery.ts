import { useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { getGame } from "../services/gameService";
import { clearStoredGameId, getStoredGameId } from "../shared/gameStorage";

export function useGameRecovery() {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const isRecoveryRoute =
      location.pathname === "/" || location.pathname === "/create";
    if (!isRecoveryRoute) return;

    const storedId = getStoredGameId();
    if (!storedId) return;

    getGame(storedId)
      .then((game) => {
        if (game.partner_a.avatar_config) {
          navigate(`/games/${storedId}/confirm`, { replace: true });
        } else {
          navigate(`/games/${storedId}/avatar`, { replace: true });
        }
      })
      .catch(() => {
        clearStoredGameId();
      });
  }, [location.pathname, navigate]);
}
