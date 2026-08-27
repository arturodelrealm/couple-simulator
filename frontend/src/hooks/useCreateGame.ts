import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { createGame } from "../services/gameService";
import { saveGameId } from "../shared/gameStorage";
import { toErrorMessage } from "../shared/errors";

export function useCreateGame() {
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
      const game = await createGame({ partner_a_name: trimmed });
      saveGameId(game.id);
      navigate(`/games/${game.id}/avatar`);
    } catch (err) {
      setError(toErrorMessage(err, t));
    } finally {
      setIsSubmitting(false);
    }
  }, [name, navigate, t]);

  return { name, setName, onSubmit, isSubmitting, error };
}
