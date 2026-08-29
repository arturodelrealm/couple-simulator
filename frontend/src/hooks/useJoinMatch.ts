import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
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
  const { matchName: matchNameParam } = useParams<{ matchName?: string }>();
  const [matchName, setMatchName] = useState(() => matchNameParam ?? "");
  const [isSubmitting, setIsSubmitting] = useState(Boolean(matchNameParam));
  const [error, setError] = useState<string | null>(null);

  const joinByMatchName = useCallback(
    async (rawName: string) => {
      const trimmed = rawName.trim();
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
    },
    [navigate, t],
  );

  useEffect(() => {
    if (!matchNameParam) {
      return;
    }
    setMatchName(matchNameParam);
    void joinByMatchName(matchNameParam);
  }, [joinByMatchName, matchNameParam]);

  const onSubmit = useCallback(() => {
    void joinByMatchName(matchName);
  }, [joinByMatchName, matchName]);

  return {
    matchName,
    setMatchName,
    onSubmit,
    isSubmitting,
    isAutoJoining: Boolean(matchNameParam) && isSubmitting,
    error,
  };
}
