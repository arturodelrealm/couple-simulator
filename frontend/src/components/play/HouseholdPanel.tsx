import { useTranslation } from "react-i18next";

import type {
  SimulationHousing,
  SimulationMascot,
} from "../../services/simulationService";

export type HouseholdPanelProps = {
  housing: SimulationHousing;
  mascot: SimulationMascot | null;
};

export function HouseholdPanel({ housing, mascot }: HouseholdPanelProps) {
  const { t } = useTranslation();
  const typeLabel = t(`game.play.housingType.${housing.type}`, {
    defaultValue: housing.type,
  });
  const qualityLabel = t(`game.play.housingQuality.${housing.quality}`, {
    defaultValue: housing.quality,
  });

  return (
    <section className="rounded-3xl border border-purple-50 bg-white px-8 py-4 shadow-sm">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <p className="text-xs font-medium text-slate-500">
            {t("game.play.household.house")}
          </p>
          <p className="mt-1 font-display text-sm font-bold text-slate-800">
            {housing.place}
          </p>
          <p className="text-sm text-slate-500">
            {typeLabel} · {qualityLabel}
          </p>
        </div>
        <div>
          <p className="text-xs font-medium text-slate-500">
            {t("game.play.household.mascot")}
          </p>
          {mascot === null ? (
            <p className="mt-1 text-sm text-slate-500">
              {t("game.play.household.noMascot")}
            </p>
          ) : (
            <p className="mt-1 font-display text-sm font-bold text-slate-800">
              {mascot.name}
              <span className="ml-2 font-sans text-sm font-medium text-slate-500">
                {mascot.species}
              </span>
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
