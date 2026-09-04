import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

import type {
  SimulationHousing,
  SimulationMascot,
} from "../../services/simulationService";
import type { AvatarConfig } from "../../shared/avatar/avataaarsVariants";
import {
  CatMascotIcon,
  DogMascotIcon,
  GenericMascotIcon,
  HamsterMascotIcon,
} from "./playIcons";
import { PlayAvatar } from "./PlayAvatar";

export type HouseholdPartner = {
  name: string;
  avatar: AvatarConfig;
  seed: string;
  age: number;
  background: string;
  badgeColor: string;
};

export type HouseholdPanelProps = {
  housing: SimulationHousing;
  mascot: SimulationMascot | null;
  partnerA: HouseholdPartner;
  partnerB: HouseholdPartner;
};

function PartnerChip({
  partner,
  ageLabel,
  reversed,
  badgeAlign,
}: {
  partner: HouseholdPartner;
  ageLabel: string;
  reversed: boolean;
  badgeAlign: "left" | "right";
}) {
  return (
    <div
      className={`flex min-w-0 items-center gap-3 ${reversed ? "flex-row-reverse sm:text-right" : ""}`}
    >
      <PlayAvatar
        config={partner.avatar}
        seed={partner.seed}
        age={partner.age}
        size={64}
        background={partner.background}
        badgeColor={partner.badgeColor}
        badgeAlign={badgeAlign}
      />
      <div className="min-w-0">
        <p className="truncate font-display text-base font-bold text-slate-800">
          {partner.name}
        </p>
        <p className="text-xs text-slate-500">{ageLabel}</p>
      </div>
    </div>
  );
}

function MascotSpeciesIcon({
  species,
  label,
}: {
  species: string;
  label: string;
}) {
  const normalized = species.trim().toLowerCase();
  const Icon =
    normalized === "cat"
      ? CatMascotIcon
      : normalized === "dog"
        ? DogMascotIcon
        : normalized === "hamster"
          ? HamsterMascotIcon
          : GenericMascotIcon;

  return (
    <Icon
      className="h-5 w-5 shrink-0"
      style={{ color: "#D97706" }}
      aria-hidden={false}
      aria-label={label}
      role="img"
    />
  );
}

function HouseholdFact({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="min-w-0">
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <div className="mt-0.5">{children}</div>
    </div>
  );
}

export function HouseholdPanel({
  housing,
  mascot,
  partnerA,
  partnerB,
}: HouseholdPanelProps) {
  const { t } = useTranslation();
  const typeLabel = t(`game.play.housingType.${housing.type}`, {
    defaultValue: housing.type,
  });
  const qualityLabel = t(`game.play.housingQuality.${housing.quality}`, {
    defaultValue: housing.quality,
  });

  return (
    <section className="rounded-3xl border border-purple-50 bg-white/95 px-5 py-3 shadow-sm sm:px-6 lg:sticky lg:top-14 lg:z-[9] lg:backdrop-blur-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:gap-6">
        <PartnerChip
          partner={partnerA}
          ageLabel={t("game.play.age", { age: partnerA.age })}
          reversed={false}
          badgeAlign="right"
        />

        <div className="grid min-w-0 flex-1 grid-cols-1 gap-4 sm:grid-cols-2 sm:items-center">
          <HouseholdFact label={t("game.play.household.house")}>
            <p className="font-display text-sm font-bold text-slate-800">
              {housing.place}
            </p>
            <p className="text-xs text-slate-500">
              {typeLabel} · {qualityLabel}
            </p>
          </HouseholdFact>

          <HouseholdFact label={t("game.play.household.mascot")}>
            {mascot === null ? (
              <p className="text-sm text-slate-500">
                {t("game.play.household.noMascot")}
              </p>
            ) : (
              <div className="flex items-center gap-2">
                <MascotSpeciesIcon
                  species={mascot.species}
                  label={t(
                    `game.play.household.species.${mascot.species.trim().toLowerCase()}`,
                    { defaultValue: mascot.species },
                  )}
                />
                <p className="font-display text-sm font-bold text-slate-800">
                  {mascot.name}
                </p>
              </div>
            )}
          </HouseholdFact>
        </div>

        <PartnerChip
          partner={partnerB}
          ageLabel={t("game.play.age", { age: partnerB.age })}
          reversed
          badgeAlign="left"
        />
      </div>
    </section>
  );
}
