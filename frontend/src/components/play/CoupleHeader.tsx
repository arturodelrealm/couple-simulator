import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

import type { AvatarConfig } from "../../shared/avatar/avataaarsVariants";
import {
  isLifeStageId,
  LIFE_STAGE_CONFIG,
} from "../../shared/play/lifeStageConfig";
import { ChildrenIcon } from "../../shared/play/statIcons";
import { theme } from "../../shared/ui/theme";
import { PlayAvatar } from "./PlayAvatar";
import { PlayHeartIcon } from "./playIcons";

export type CoupleHeaderProps = {
  partnerAName: string;
  partnerAAvatar: AvatarConfig;
  partnerASeed: string;
  partnerBAvatar: AvatarConfig;
  partnerBSeed: string;
  partnerBName?: string;
  lifeStage: string;
  age: number;
  partnerBDisplayAge?: number;
  childrenCount: number;
};

function PartnerColumn({
  name,
  ageLabel,
  avatar,
  reversed,
}: {
  name: string;
  ageLabel: string;
  avatar: ReactNode;
  reversed: boolean;
}) {
  return (
    <div
      className={`flex items-center gap-4 ${reversed ? "flex-row-reverse" : ""}`}
    >
      {avatar}
      <div className={reversed ? "text-right" : undefined}>
        <p className="font-display text-xl font-extrabold text-slate-800">
          {name}
        </p>
        <p className="text-sm text-slate-500">{ageLabel}</p>
      </div>
    </div>
  );
}

export function CoupleHeader({
  partnerAName,
  partnerAAvatar,
  partnerASeed,
  partnerBAvatar,
  partnerBSeed,
  partnerBName,
  lifeStage,
  age,
  partnerBDisplayAge,
  childrenCount,
}: CoupleHeaderProps) {
  const { t } = useTranslation();
  const partnerBLabel = partnerBName ?? t("game.play.partnerB");
  const partnerBAge = partnerBDisplayAge ?? age;
  const stage = isLifeStageId(lifeStage) ? LIFE_STAGE_CONFIG[lifeStage] : null;
  const extraChildren = Math.max(0, childrenCount - 5);
  const childIcons = Math.min(childrenCount, 5);

  return (
    <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div
        className="px-8 py-6"
        style={{
          background: theme.headerGradient,
        }}
      >
        <div className="flex flex-col items-center justify-between gap-6 sm:flex-row">
          <PartnerColumn
            name={partnerAName}
            ageLabel={t("game.play.age", { age })}
            reversed={false}
            avatar={
              <PlayAvatar
                config={partnerAAvatar}
                seed={partnerASeed}
                age={age}
                background={theme.partnerA.background}
                badgeColor={theme.partnerA.color}
                badgeAlign="right"
              />
            }
          />

          <div className="text-center">
            {stage && (
              <div
                className="mb-3 inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-xs font-semibold"
                style={{
                  background: `${stage.color}22`,
                  color: stage.color,
                }}
              >
                <span
                  className="inline-block h-1.5 w-1.5 rounded-full"
                  style={{ background: stage.color }}
                />
                {t(stage.labelKey)}
              </div>
            )}
            <div className="flex justify-center">
              <PlayHeartIcon
                className="h-7 w-7"
                style={{ color: theme.heart }}
              />
            </div>
            {childrenCount > 0 && (
              <div className="mt-2 flex items-center justify-center gap-1">
                {Array.from({ length: childIcons }, (_, index) => (
                  <ChildrenIcon
                    key={index}
                    className="h-3.5 w-3.5"
                    style={{ color: theme.primary }}
                  />
                ))}
                {extraChildren > 0 && (
                  <span className="text-xs font-semibold text-blue-400">
                    {t("game.play.childrenOverflow", { count: extraChildren })}
                  </span>
                )}
              </div>
            )}
          </div>

          <PartnerColumn
            name={partnerBLabel}
            ageLabel={t("game.play.age", { age: partnerBAge })}
            reversed
            avatar={
              <PlayAvatar
                config={partnerBAvatar}
                seed={partnerBSeed}
                age={partnerBAge}
                background={theme.partnerB.background}
                badgeColor={theme.partnerB.color}
                badgeAlign="left"
              />
            }
          />
        </div>
      </div>
    </section>
  );
}
