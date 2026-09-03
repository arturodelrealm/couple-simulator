import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { getGameByMatchName } from "../services/gameService";
import { saveCurrentGameFromGame } from "../shared/gameStorage";
import { toErrorMessage } from "../shared/errors";
import { getGameStepPath, getPlayerBSetupPath } from "../shared/gameNavigation";
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
    async (rawName: string, asPartnerB = false) => {
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
        navigate(
          asPartnerB ? getPlayerBSetupPath(game.id) : getGameStepPath(game),
        );
      } catch (err) {
        setError(toErrorMessage(err, t));
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

  const onJoinAsPartnerB = useCallback(() => {
    void joinByMatchName(matchName, true);
  }, [joinByMatchName, matchName]);

  return {
    matchName,
    setMatchName,
    onSubmit,
    onJoinAsPartnerB,
    isSubmitting,
    isAutoJoining: Boolean(matchNameParam) && isSubmitting,
    error,
  };
}
