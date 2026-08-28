import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { createGame, type GameMode } from "../services/gameService";
import { saveCurrentGameFromGame } from "../shared/gameStorage";
import { toErrorMessage } from "../shared/errors";

export type UseCreateGameOptions = {
  matchName?: string;
  gameMode?: GameMode;
};

export function useCreateGame(options: UseCreateGameOptions = {}) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = useCallback(async () => {
    const trimmed = name.trim();
    if (!trimmed) {
      setError(t("errors.nameRequired"));
      return;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      // TODO(phase-3): match_name comes from CreateMatchPage form instead of fallback.
      const matchName = options.matchName?.trim() || `mvp0-${Date.now()}`;
      const game = await createGame({
        match_name: matchName,
        game_mode: options.gameMode,
        partner_a_name: trimmed,
      });
      saveCurrentGameFromGame(game);
      navigate(`/games/${game.id}/avatar`);
    } catch (err) {
      setError(toErrorMessage(err, t));
    } finally {
      setIsSubmitting(false);
    }
  }, [name, navigate, options.gameMode, options.matchName, t]);

  return { name, setName, onSubmit, isSubmitting, error };
}
