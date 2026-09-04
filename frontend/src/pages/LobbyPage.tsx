import { useTranslation } from "react-i18next";

import { LobbyActionCard } from "../components/lobby/LobbyActionCard";
import { LobbyCurrentMatch } from "../components/lobby/LobbyCurrentMatch";
import { LobbyJoinIcon, LobbyPlusIcon } from "../components/lobby/lobbyIcons";
import { PlayLayout } from "../components/play/PlayLayout";
import { PlayHeartIcon } from "../components/play/playIcons";
import { useLobby } from "../hooks/useLobby";
import { getPlayerBSetupPath } from "../shared/gameNavigation";
import { ErrorMessage } from "../shared/ui/ErrorMessage";
import { theme } from "../shared/ui/theme";

export function LobbyPage() {
  const { t } = useTranslation();
  const { currentGame, onContinue, isContinuing, error } = useLobby();

  return (
    <PlayLayout
      showBackToLobby={false}
      contentClassName="mx-auto max-w-3xl space-y-6 px-6 py-8"
    >
      <section
        className="rounded-3xl border border-slate-200 px-6 py-10 text-center shadow-sm sm:px-10"
        style={{
          background: theme.headerGradient,
        }}
      >
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-white/80 shadow-sm">
          <PlayHeartIcon className="h-6 w-6" style={{ color: theme.heart }} />
        </div>
        <h1 className="font-display text-3xl font-extrabold text-slate-800 sm:text-4xl">
          {t("game.lobby.title")}
        </h1>
        <p className="mx-auto mt-3 max-w-md text-sm leading-relaxed text-slate-600">
          {t("game.lobby.subtitle")}
        </p>
      </section>

      <div className="grid gap-4 sm:grid-cols-2">
        <LobbyActionCard
          to="/games/new"
          title={t("game.lobby.createButton")}
          description={t("game.lobby.createHint")}
          icon={<LobbyPlusIcon className="h-6 w-6" />}
        />
        <LobbyActionCard
          to="/games/join"
          title={t("game.lobby.joinButton")}
          description={t("game.lobby.joinHint")}
          icon={<LobbyJoinIcon className="h-6 w-6" />}
        />
      </div>

      {currentGame ? (
        <LobbyCurrentMatch
          matchName={currentGame.match_name}
          partnerBHref={getPlayerBSetupPath(currentGame.game_id)}
          onContinue={onContinue}
          isContinuing={isContinuing}
        />
      ) : null}

      {error ? <ErrorMessage message={error} /> : null}
    </PlayLayout>
  );
}
