import { useTranslation } from "react-i18next";

export type NextQuestionButtonProps = {
  onClick: () => void;
  disabled?: boolean;
  label?: string;
};

export function NextQuestionButton({
  onClick,
  disabled = false,
  label,
}: NextQuestionButtonProps) {
  const { t } = useTranslation();

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="w-full rounded-2xl border-2 border-purple-200 bg-white px-5 py-3 font-display text-base font-bold text-purple-700 transition-all hover:bg-purple-50 disabled:cursor-not-allowed disabled:opacity-50"
    >
      {label ?? t("game.play.nextQuestion")}
    </button>
  );
}
