import { useTranslation } from "react-i18next";

import { useCreateGame } from "../hooks/useCreateGame";
import { GameLayout } from "../shared/ui/GameLayout";
import { PrimaryButton } from "../shared/ui/PrimaryButton";
import { ErrorMessage } from "../shared/ui/ErrorMessage";

export function CreateGamePage() {
  const { t } = useTranslation();
  const { name, setName, onSubmit, isSubmitting, error } = useCreateGame();

  return (
    <GameLayout>
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900">
          {t("game.create.title")}
        </h1>
        <p className="text-slate-600">{t("game.create.description")}</p>
        <label className="block space-y-2">
          <span className="text-sm font-medium text-slate-700">
            {t("game.create.nameLabel")}
          </span>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            placeholder={t("game.create.namePlaceholder")}
            maxLength={255}
          />
        </label>
        {error && <ErrorMessage message={error} />}
        <PrimaryButton onClick={onSubmit} disabled={isSubmitting}>
          {t("game.create.submit")}
        </PrimaryButton>
      </div>
    </GameLayout>
  );
}
