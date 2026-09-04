import { useTranslation } from "react-i18next";

import type { QuestionnaireItem } from "../../services/partnerAQuestionnaireService";

type QuestionnaireEventNavProps = {
  items: QuestionnaireItem[];
  currentEventId: string | null;
  onSelect: (eventId: string) => void;
};

export function QuestionnaireEventNav({
  items,
  currentEventId,
  onSelect,
}: QuestionnaireEventNavProps) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item, index) => {
        const selected = item.event_id === currentEventId;
        return (
          <button
            key={item.event_id}
            type="button"
            onClick={() => onSelect(item.event_id)}
            className={`rounded-full px-3 py-1 text-xs font-semibold ${
              selected
                ? "bg-purple-600 text-white"
                : "bg-white text-slate-600 ring-1 ring-purple-100"
            }`}
          >
            {index + 1} · {t(`game.questionnaire.status.${item.status}`)}
          </button>
        );
      })}
    </div>
  );
}
