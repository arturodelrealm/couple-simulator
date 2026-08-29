import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { AvatarBuilder } from "../components/avatar/AvatarBuilder";
import { usePlayerASetup } from "../hooks/usePlayerASetup";
import type { PlayerSex } from "../services/gameService";
import { GameLayout } from "../shared/ui/GameLayout";
import { PrimaryButton } from "../shared/ui/PrimaryButton";
import { LoadingState } from "../shared/ui/LoadingState";
import { ErrorMessage } from "../shared/ui/ErrorMessage";

const SEX_OPTIONS: PlayerSex[] = ["male", "female", "prefer_not_to_say"];

const SEX_LABEL_KEYS: Record<PlayerSex, string> = {
  male: "game.playerA.sex.male",
  female: "game.playerA.sex.female",
  prefer_not_to_say: "game.playerA.sex.preferNotToSay",
};

export function PlayerASetupPage() {
  const { t } = useTranslation();
  const {
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
  } = usePlayerASetup();

  if (isLoading) {
    return (
      <GameLayout>
        <LoadingState message={t("common.loading")} />
      </GameLayout>
    );
  }

  if (!gameId) {
    return (
      <GameLayout>
        <ErrorMessage message={t("errors.gameNotFound")} />
      </GameLayout>
    );
  }

  return (
    <GameLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between gap-4">
          <h1 className="text-2xl font-bold text-slate-900">
            {t(isEditing ? "game.playerA.editTitle" : "game.playerA.title")}
          </h1>
          <Link
            to="/lobby"
            className="text-sm font-medium text-indigo-600 hover:text-indigo-700"
          >
            {t("game.nav.backToLobby")}
          </Link>
        </div>

        <label className="block space-y-2">
          <span className="text-sm font-medium text-slate-700">
            {t("game.playerA.nameLabel")}
          </span>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            placeholder={t("game.playerA.namePlaceholder")}
            maxLength={255}
          />
        </label>

        <fieldset className="space-y-2">
          <legend className="text-sm font-medium text-slate-700">
            {t("game.playerA.sexLabel")}
          </legend>
          <div className="flex flex-wrap gap-4">
            {SEX_OPTIONS.map((option) => (
              <label
                key={option}
                className="flex cursor-pointer items-center gap-2 text-sm text-slate-700"
              >
                <input
                  type="radio"
                  name="player-a-sex"
                  value={option}
                  checked={sex === option}
                  onChange={() => setSex(option)}
                  className="text-indigo-600 focus:ring-indigo-500"
                />
                {t(SEX_LABEL_KEYS[option])}
              </label>
            ))}
          </div>
        </fieldset>

        {error && <ErrorMessage message={error} />}
        <AvatarBuilder
          config={config}
          seed={gameId}
          onChange={setConfig}
          footer={
            <PrimaryButton onClick={onSave} disabled={isSaving}>
              {t("game.playerA.save")}
            </PrimaryButton>
          }
        />
      </div>
    </GameLayout>
  );
}
