import { useTranslation } from "react-i18next";

import type {
  AvatarConfig,
  AvatarVariantKey,
} from "../../shared/avatar/avataaarsVariants";
import { createAvatarDataUri } from "../../shared/avatar/createAvatarSvg";
import { AvatarOptionGrid } from "../../shared/ui/AvatarOptionGrid";
import { OptionCard } from "../../shared/ui/OptionCard";

type AvatarOptionSectionProps = {
  titleKey: string;
  optionKey: AvatarVariantKey;
  options: string[];
  value: string | undefined;
  probabilityKey?: "accessoriesProbability" | "facialHairProbability";
  probabilityValue?: number;
  config: AvatarConfig;
  onSelect: (value: string, enabled: boolean) => void;
};

const THUMB_SIZE = 48;

export function AvatarOptionSection({
  titleKey,
  optionKey,
  options,
  value,
  probabilityKey,
  probabilityValue,
  config,
  onSelect,
}: AvatarOptionSectionProps) {
  const { t } = useTranslation();
  const hasProbability = probabilityKey !== undefined;
  const isNoneSelected = hasProbability && probabilityValue === 0;

  return (
    <section className="space-y-3">
      <h3 className="text-sm font-semibold text-slate-700">{t(titleKey)}</h3>
      <AvatarOptionGrid>
        {hasProbability && (
          <OptionCard
            selected={isNoneSelected}
            onSelect={() => onSelect(options[0], false)}
            label={t("avatar.option.none")}
          >
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-xs text-slate-500">
              {t("avatar.option.none")}
            </div>
          </OptionCard>
        )}
        {options.map((option) => {
          const thumbConfig: AvatarConfig = {
            ...config,
            [optionKey]: option,
          };
          if (probabilityKey) {
            thumbConfig[probabilityKey] = 100;
          }
          const thumbUri = createAvatarDataUri(
            thumbConfig,
            "thumb",
            THUMB_SIZE,
          );
          const selected = !isNoneSelected && value === option;

          return (
            <OptionCard
              key={option}
              selected={selected}
              onSelect={() => onSelect(option, true)}
              label={option}
            >
              <img
                src={thumbUri}
                alt=""
                width={THUMB_SIZE}
                height={THUMB_SIZE}
                className="rounded-full bg-slate-50"
              />
            </OptionCard>
          );
        })}
      </AvatarOptionGrid>
    </section>
  );
}
