import { useTranslation } from "react-i18next";

import { useGameRecovery } from "../hooks/useGameRecovery";
import { GameLayout } from "../shared/ui/GameLayout";
import { LoadingState } from "../shared/ui/LoadingState";

export function EntryPage() {
  const { t } = useTranslation();
  useGameRecovery();

  return (
    <GameLayout>
      <LoadingState message={t("common.loading")} />
    </GameLayout>
  );
}
