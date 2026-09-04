import type { ComponentType } from "react";

import {
  ChildrenIcon,
  CompatibilityIcon,
  FinancesIcon,
  QualityOfLifeIcon,
  WellnessIcon,
  type StatIconProps,
} from "./statIcons";

export type SimulationStatKey =
  "compatibility" | "finances" | "children" | "quality_of_life" | "wellness";

export type StatDisplayConfig = {
  key: SimulationStatKey;
  labelKey: string;
  color: string;
  background: string;
  isCount: boolean;
  Icon: ComponentType<StatIconProps>;
};

export const STAT_CONFIG: readonly StatDisplayConfig[] = [
  {
    key: "compatibility",
    labelKey: "game.play.stats.compatibility",
    color: "#F43F5E",
    background: "#FFF1F2",
    isCount: false,
    Icon: CompatibilityIcon,
  },
  {
    key: "finances",
    labelKey: "game.play.stats.finances",
    color: "#D97706",
    background: "#FFFBEB",
    isCount: false,
    Icon: FinancesIcon,
  },
  {
    key: "children",
    labelKey: "game.play.stats.children",
    color: "#0284C7",
    background: "#F0F9FF",
    isCount: true,
    Icon: ChildrenIcon,
  },
  {
    key: "quality_of_life",
    labelKey: "game.play.stats.qualityOfLife",
    color: "#7C3AED",
    background: "#F5F3FF",
    isCount: false,
    Icon: QualityOfLifeIcon,
  },
  {
    key: "wellness",
    labelKey: "game.play.stats.wellness",
    color: "#059669",
    background: "#ECFDF5",
    isCount: false,
    Icon: WellnessIcon,
  },
];
