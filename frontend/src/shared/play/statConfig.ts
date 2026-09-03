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
    color: "#F472B6",
    background: "#FDF2F8",
    isCount: false,
    Icon: CompatibilityIcon,
  },
  {
    key: "finances",
    labelKey: "game.play.stats.finances",
    color: "#FBBF24",
    background: "#FFFBEB",
    isCount: false,
    Icon: FinancesIcon,
  },
  {
    key: "children",
    labelKey: "game.play.stats.children",
    color: "#60A5FA",
    background: "#EFF6FF",
    isCount: true,
    Icon: ChildrenIcon,
  },
  {
    key: "quality_of_life",
    labelKey: "game.play.stats.qualityOfLife",
    color: "#FB923C",
    background: "#FFF7ED",
    isCount: false,
    Icon: QualityOfLifeIcon,
  },
  {
    key: "wellness",
    labelKey: "game.play.stats.wellness",
    color: "#34D399",
    background: "#ECFDF5",
    isCount: false,
    Icon: WellnessIcon,
  },
];
