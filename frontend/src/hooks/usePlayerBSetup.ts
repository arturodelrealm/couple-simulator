import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { getGame, updateGame, type PlayerSex } from "../services/gameService";
import type { AvatarConfig } from "../shared/avatar/avataaarsVariants";
import { DEFAULT_AVATAR_CONFIG } from "../shared/avatar/defaultAvatarConfig";
import {
  clearCurrentGame,
  saveCurrentGameFromGame,
  touchCurrentGame,
} from "../shared/gameStorage";
import { toErrorMessage } from "../shared/errors";
import { isPlayerBSetupComplete } from "../shared/gameNavigation";

export function usePlayerBSetup() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { gameId } = useParams<{ gameId: string }>();
  const [name, setName] = useState("");
  const [sex, setSex] = useState<PlayerSex | null>(null);
  const [config, setConfig] = useState<AvatarConfig>(DEFAULT_AVATAR_CONFIG);
  const [isEditing, setIsEditing] = useState(false);
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
        touchCurrentGame();
        setIsEditing(isPlayerBSetupComplete(game));
        const partnerB = game.partner_b;
        if (partnerB?.name) {
          setName(partnerB.name);
        }
        if (partnerB?.sex) {
          setSex(partnerB.sex);
        }
        if (partnerB?.avatar_config) {
          setConfig(partnerB.avatar_config);
        }
      })
      .catch((err) => {
        clearCurrentGame();
        setError(toErrorMessage(err, t));
      })
      .finally(() => setIsLoading(false));
  }, [gameId, t]);

  const onSave = useCallback(async () => {
    if (!gameId) {
      return;
    }

    const trimmedName = name.trim();
    if (!trimmedName) {
      setError(t("errors.nameRequired"));
      return;
    }
    if (!sex) {
      setError(t("errors.sexRequired"));
      return;
    }

    setIsSaving(true);
    setError(null);
    try {
      const game = await updateGame(gameId, {
        partner_b_name: trimmedName,
        partner_b_sex: sex,
        partner_b_avatar_config: config,
      });
      saveCurrentGameFromGame(game);
      touchCurrentGame();
      navigate(`/games/${gameId}/confirm`);
    } catch (err) {
      setError(toErrorMessage(err, t));
    } finally {
      setIsSaving(false);
    }
  }, [config, gameId, name, navigate, sex, t]);

  return {
    gameId,
    name,
    setName,
    sex,
    setSex,
    config,
    setConfig,
    isEditing,
    isLoading,
    isSaving,
    error,
    onSave,
  };
}
