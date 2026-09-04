import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import {
  getPartnerAQuestionnairePath,
  getPlayEntryPath,
  getPlayerBSetupPath,
} from "../../shared/gameNavigation";

export type ConfirmActionsProps = {
  gameId: string;
  canPlay: boolean;
  continueQuestionnaire: boolean;
  questionnaireProgressLabel: string | null;
  hasActiveRunB: boolean;
  partnerBComplete: boolean;
};

const gradientCta =
  "block w-full rounded-2xl px-5 py-3 text-center font-display text-base font-bold text-white transition-all hover:opacity-90 active:scale-95";

const secondaryCta =
  "block w-full rounded-2xl border-2 border-purple-100 bg-white px-5 py-3 text-center font-display text-base font-bold text-slate-700 transition-all hover:border-purple-300 hover:bg-purple-50";

const disabledCta =
  "block w-full cursor-not-allowed rounded-2xl px-5 py-3 text-center font-display text-base font-bold text-white opacity-50";

export function ConfirmActions({
  gameId,
  canPlay,
  continueQuestionnaire,
  questionnaireProgressLabel,
  hasActiveRunB,
  partnerBComplete,
}: ConfirmActionsProps) {
  const { t } = useTranslation();
  const canPlayAsB = canPlay && partnerBComplete;

  return (
    <div className="flex flex-col gap-3">
      {canPlay ? (
        <div className="space-y-2">
          <Link
            to={getPartnerAQuestionnairePath(gameId)}
            className={gradientCta}
            style={{
              background: "linear-gradient(135deg, #a78bfa, #f472b6)",
            }}
          >
            {t(
              continueQuestionnaire
                ? "game.questionnaire.continueCta"
                : "game.questionnaire.startCta",
            )}
          </Link>
          {questionnaireProgressLabel ? (
            <p className="text-center text-sm text-slate-500">
              {questionnaireProgressLabel}
            </p>
          ) : null}
        </div>
      ) : null}
      {canPlayAsB ? (
        <Link
          to={getPlayEntryPath(gameId, "partner_b")}
          className={gradientCta}
          style={{
            background: "linear-gradient(135deg, #a78bfa, #f472b6)",
          }}
        >
          {t(
            hasActiveRunB
              ? "game.play.continueAsPartnerB"
              : "game.play.startAsPartnerB",
          )}
        </Link>
      ) : canPlay ? (
        <div className="space-y-2">
          <button
            type="button"
            disabled
            className={disabledCta}
            style={{
              background: "linear-gradient(135deg, #a78bfa, #f472b6)",
            }}
          >
            {t("game.play.startAsPartnerB")}
          </button>
          <p className="text-center text-sm text-slate-500">
            {t("game.play.completePartnerBFirst")}
          </p>
        </div>
      ) : null}
      <Link to={`/games/${gameId}/player-a`} className={secondaryCta}>
        {t("game.confirm.editPlayerA")}
      </Link>
      <Link to={getPlayerBSetupPath(gameId)} className={secondaryCta}>
        {t(
          partnerBComplete
            ? "game.confirm.editPlayerB"
            : "game.confirm.iamPartnerB",
        )}
      </Link>
    </div>
  );
}
