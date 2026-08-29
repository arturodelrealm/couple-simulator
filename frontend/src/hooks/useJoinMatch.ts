import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { ApiClientError } from "../services/apiClient";
import { getGameByMatchName } from "../services/gameService";
import { saveCurrentGameFromGame } from "../shared/gameStorage";
import { toErrorMessage } from "../shared/errors";
import { getGameStepPath } from "../shared/gameNavigation";
import {
  isValidMatchName,
  normalizeMatchName,
} from "../shared/matchNameValidation";

export function useJoinMatch() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [matchName, setMatchName] = useState("");
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
      const game = await getGameByMatchName(normalizeMatchName(trimmed));
      saveCurrentGameFromGame(game);
      navigate(getGameStepPath(game));
    } catch (err) {
      if (err instanceof ApiClientError && err.code === "GAME_NOT_FOUND") {
        setError(t("game.join.notFound"));
      } else {
        setError(toErrorMessage(err, t));
      }
    } finally {
      setIsSubmitting(false);
    }
  }, [matchName, navigate, t]);

  return { matchName, setMatchName, onSubmit, isSubmitting, error };
}
