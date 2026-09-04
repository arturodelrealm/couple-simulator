import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { PlayLayout } from "../components/play/PlayLayout";
import { usePlayEntry } from "../hooks/usePlayEntry";
import { getPlayerBSetupPath } from "../shared/gameNavigation";
import { ErrorMessage } from "../shared/ui/ErrorMessage";
import { LoadingState } from "../shared/ui/LoadingState";

export function PlayEntryPage() {
  const { t } = useTranslation();
  const { gameId, isLoading, error, errorCode } = usePlayEntry();

  if (isLoading) {
    return (
      <PlayLayout>
        <LoadingState message={t("common.loading")} />
      </PlayLayout>
    );
  }

  const showPartnerBSetupLink =
    errorCode === "PARTNER_B_NOT_READY" && gameId !== undefined;
  const showSetupLink = errorCode === "GAME_NOT_READY" && gameId !== undefined;

  return (
    <PlayLayout>
      <div className="space-y-4">
        <ErrorMessage message={error ?? t("errors.generic")} />
        {showPartnerBSetupLink ? (
          <Link
            to={getPlayerBSetupPath(gameId)}
            className="text-sm font-medium text-sky-700 hover:text-sky-800"
          >
            {t("game.play.errors.goToPartnerBSetup")}
          </Link>
        ) : showSetupLink ? (
          <Link
            to={`/games/${gameId}/player-a`}
            className="text-sm font-medium text-sky-700 hover:text-sky-800"
          >
            {t("game.play.errors.goToSetup")}
          </Link>
        ) : (
          <Link
            to="/lobby"
            className="text-sm font-medium text-sky-700 hover:text-sky-800"
          >
            {t("game.nav.backToLobby")}
          </Link>
        )}
      </div>
    </PlayLayout>
  );
}
