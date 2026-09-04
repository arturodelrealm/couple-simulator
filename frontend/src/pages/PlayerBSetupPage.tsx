import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { AvatarBuilder } from "../components/avatar/AvatarBuilder";
import { usePlayerBSetup } from "../hooks/usePlayerBSetup";
import type { PlayerSex } from "../services/gameService";
import { GameLayout } from "../shared/ui/GameLayout";
import { PrimaryButton } from "../shared/ui/PrimaryButton";
import { LoadingState } from "../shared/ui/LoadingState";
import { ErrorMessage } from "../shared/ui/ErrorMessage";

const SEX_OPTIONS: PlayerSex[] = ["male", "female", "prefer_not_to_say"];

const SEX_LABEL_KEYS: Record<PlayerSex, string> = {
  male: "game.playerB.sex.male",
  female: "game.playerB.sex.female",
  prefer_not_to_say: "game.playerB.sex.preferNotToSay",
};

export function PlayerBSetupPage() {
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
  } = usePlayerBSetup();

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
            {t(isEditing ? "game.playerB.editTitle" : "game.playerB.title")}
          </h1>
          <Link
            to="/lobby"
            className="text-sm font-medium text-sky-700 hover:text-sky-800"
          >
            {t("game.nav.backToLobby")}
          </Link>
        </div>

        <label className="block space-y-2">
          <span className="text-sm font-medium text-slate-700">
            {t("game.playerB.nameLabel")}
          </span>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            placeholder={t("game.playerB.namePlaceholder")}
            maxLength={255}
          />
        </label>

        <fieldset className="space-y-2">
          <legend className="text-sm font-medium text-slate-700">
            {t("game.playerB.sexLabel")}
          </legend>
          <div className="flex flex-wrap gap-4">
            {SEX_OPTIONS.map((option) => (
              <label
                key={option}
                className="flex cursor-pointer items-center gap-2 text-sm text-slate-700"
              >
                <input
                  type="radio"
                  name="player-b-sex"
                  value={option}
                  checked={sex === option}
                  onChange={() => setSex(option)}
                  className="text-sky-600 focus:ring-sky-500"
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
              {t("game.playerB.save")}
            </PrimaryButton>
          }
        />
      </div>
    </GameLayout>
  );
}
