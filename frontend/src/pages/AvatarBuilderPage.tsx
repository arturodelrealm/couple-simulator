import { useTranslation } from "react-i18next";

import { AvatarBuilder } from "../components/avatar/AvatarBuilder";
import { useAvatarBuilder } from "../hooks/useAvatarBuilder";
import { GameLayout } from "../shared/ui/GameLayout";
import { PrimaryButton } from "../shared/ui/PrimaryButton";
import { LoadingState } from "../shared/ui/LoadingState";
import { ErrorMessage } from "../shared/ui/ErrorMessage";

export function AvatarBuilderPage() {
  const { t } = useTranslation();
  const {
    gameId,
    config,
    setConfig,
    partnerName,
    isLoading,
    isSaving,
    error,
    onSave,
  } = useAvatarBuilder();

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
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            {t("avatar.builder.title")}
          </h1>
          {partnerName && (
            <p className="mt-1 text-slate-600">
              {t("avatar.builder.forPartner", { name: partnerName })}
            </p>
          )}
        </div>
        {error && <ErrorMessage message={error} />}
        <AvatarBuilder
          config={config}
          seed={gameId}
          onChange={setConfig}
          footer={
            <PrimaryButton onClick={onSave} disabled={isSaving}>
              {t("avatar.builder.save")}
            </PrimaryButton>
          }
        />
      </div>
    </GameLayout>
  );
}
