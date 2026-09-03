import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

export type LobbyCurrentMatchProps = {
  matchName: string;
  partnerBHref: string;
  onContinue: () => void;
  isContinuing: boolean;
};

export function LobbyCurrentMatch({
  matchName,
  partnerBHref,
  onContinue,
  isContinuing,
}: LobbyCurrentMatchProps) {
  const { t } = useTranslation();

  return (
    <div className="overflow-hidden rounded-3xl border border-purple-50 bg-white p-6 shadow-sm sm:p-8">
      <span className="inline-block rounded-full bg-pink-50 px-2.5 py-1 text-xs font-semibold text-pink-500">
        {t("game.lobby.currentMatchLabel")}
      </span>
      <p className="mt-3 font-display text-2xl font-extrabold tracking-tight text-slate-800">
        {matchName}
      </p>
      <p className="mt-2 text-sm leading-relaxed text-slate-600">
        {t("game.lobby.continueHint")}
      </p>
      <button
        type="button"
        onClick={onContinue}
        disabled={isContinuing}
        className="mt-5 w-full rounded-2xl px-5 py-3 font-display text-base font-bold text-white transition-all hover:opacity-90 active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
        style={{
          background: "linear-gradient(135deg, #a78bfa, #f472b6)",
        }}
      >
        {t("game.lobby.continueCurrent")}
      </button>
      <Link
        to={partnerBHref}
        className="mt-3 block w-full rounded-2xl border-2 border-purple-100 bg-white px-5 py-3 text-center font-display text-base font-bold text-slate-700 transition-all hover:border-purple-300 hover:bg-purple-50"
      >
        {t("game.lobby.iamPartnerB")}
      </Link>
    </div>
  );
}
