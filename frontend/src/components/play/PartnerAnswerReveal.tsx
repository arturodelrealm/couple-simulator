import { useTranslation } from "react-i18next";

type PartnerAnswerRevealProps = {
  phase: "hidden" | "waiting" | "revealed";
  missing: boolean;
  partnerName: string;
};

export function PartnerAnswerReveal({
  phase,
  missing,
  partnerName,
}: PartnerAnswerRevealProps) {
  const { t } = useTranslation();

  if (phase === "waiting") {
    return (
      <p className="text-sm font-medium italic text-slate-600">
        {t("game.play.partnerReveal.waiting")}
      </p>
    );
  }

  if (phase === "revealed" && missing) {
    return (
      <p className="text-sm font-medium text-slate-600">
        {t("game.play.partnerReveal.missing", { name: partnerName })}
      </p>
    );
  }

  return null;
}
