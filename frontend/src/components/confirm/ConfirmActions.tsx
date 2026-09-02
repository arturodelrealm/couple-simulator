import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

export type ConfirmActionsProps = {
  gameId: string;
  canPlay: boolean;
  hasActiveRun: boolean;
};

const gradientCta =
  "block w-full rounded-2xl px-5 py-3 text-center font-display text-base font-bold text-white transition-all hover:opacity-90 active:scale-95";

const secondaryCta =
  "block w-full rounded-2xl border-2 border-purple-100 bg-white px-5 py-3 text-center font-display text-base font-bold text-slate-700 transition-all hover:border-purple-300 hover:bg-purple-50";

export function ConfirmActions({
  gameId,
  canPlay,
  hasActiveRun,
}: ConfirmActionsProps) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-3">
      {canPlay ? (
        <Link
          to={`/games/${gameId}/play`}
          className={gradientCta}
          style={{
            background: "linear-gradient(135deg, #a78bfa, #f472b6)",
          }}
        >
          {t(hasActiveRun ? "game.play.continue" : "game.play.start")}
        </Link>
      ) : null}
      <Link to={`/games/${gameId}/player-a`} className={secondaryCta}>
        {t("game.confirm.editPlayerA")}
      </Link>
    </div>
  );
}
