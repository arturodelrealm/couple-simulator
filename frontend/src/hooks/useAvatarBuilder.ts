import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { getGame, updateGame } from "../services/gameService";
import type { AvatarConfig } from "../shared/avatar/avataaarsVariants";
import { DEFAULT_AVATAR_CONFIG } from "../shared/avatar/defaultAvatarConfig";
import {
  clearCurrentGame,
  saveCurrentGameFromGame,
  touchCurrentGame,
} from "../shared/gameStorage";
import { toErrorMessage } from "../shared/errors";

export function useAvatarBuilder() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { gameId } = useParams<{ gameId: string }>();
  const [config, setConfig] = useState<AvatarConfig>(DEFAULT_AVATAR_CONFIG);
  const [partnerName, setPartnerName] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!gameId) {
      setError(t("errors.gameNotFound"));
      setIsLoading(false);
      return;
    }

    getGame(gameId)
      .then((game) => {
        saveCurrentGameFromGame(game);
        if (game.partner_a.avatar_config) {
          navigate(`/games/${gameId}/confirm`, { replace: true });
          return;
        }
        setPartnerName(game.partner_a.name);
      })
      .catch((err) => {
        clearCurrentGame();
        setError(toErrorMessage(err, t));
      })
      .finally(() => setIsLoading(false));
  }, [gameId, navigate, t]);

  const onSave = useCallback(async () => {
    if (!gameId) return;

    setIsSaving(true);
    setError(null);
    try {
      const game = await updateGame(gameId, { avatar_config: config });
      saveCurrentGameFromGame(game);
      touchCurrentGame();
      navigate(`/games/${gameId}/confirm`);
    } catch (err) {
      setError(toErrorMessage(err, t));
    } finally {
      setIsSaving(false);
    }
  }, [config, gameId, navigate, t]);

  return {
    gameId,
    config,
    setConfig,
    partnerName,
    isLoading,
    isSaving,
    error,
    onSave,
  };
}
