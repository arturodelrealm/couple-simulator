import { useTranslation } from "react-i18next";

export type EventContinueButtonProps = {
  onClick: () => void;
  disabled?: boolean;
};

export function EventContinueButton({
  onClick,
  disabled = false,
}: EventContinueButtonProps) {
  const { t } = useTranslation();

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="w-full rounded-2xl px-5 py-3 font-display text-base font-bold text-white transition-all hover:opacity-90 active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
      style={{
        background: "linear-gradient(135deg, #a78bfa, #f472b6)",
      }}
    >
      {t("game.play.continueNextEvent")}
    </button>
  );
}
