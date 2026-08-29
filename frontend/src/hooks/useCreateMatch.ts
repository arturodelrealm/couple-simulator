import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { createGame, type GameMode } from "../services/gameService";
import { saveCurrentGameFromGame } from "../shared/gameStorage";
import { toErrorMessage } from "../shared/errors";
import {
  isValidMatchName,
  normalizeMatchName,
} from "../shared/matchNameValidation";

export function useCreateMatch() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [matchName, setMatchName] = useState("");
  const [gameMode] = useState<GameMode>("couple");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = useCallback(async () => {
    const trimmed = matchName.trim();
    if (!trimmed) {
      setError(t("errors.matchNameRequired"));
      return;
    }
    if (!isValidMatchName(trimmed)) {
      setError(t("errors.matchNameInvalid"));
      return;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      const game = await createGame({
        match_name: normalizeMatchName(trimmed),
        game_mode: gameMode,
      });
      saveCurrentGameFromGame(game);
      navigate(`/games/${game.id}/player-a`);
    } catch (err) {
      setError(toErrorMessage(err, t));
    } finally {
      setIsSubmitting(false);
    }
  }, [gameMode, matchName, navigate, t]);

  return { matchName, setMatchName, gameMode, onSubmit, isSubmitting, error };
}
