export type LifeStageId = "youth" | "adult" | "elderly";

export type LifeStageDisplayConfig = {
  color: string;
  labelKey: string;
};

export const LIFE_STAGE_CONFIG: Record<LifeStageId, LifeStageDisplayConfig> = {
  youth: {
    color: "#0284C7",
    labelKey: "game.play.lifeStage.youth",
  },
  adult: {
    color: "#7C3AED",
    labelKey: "game.play.lifeStage.adult",
  },
  elderly: {
    color: "#D97706",
    labelKey: "game.play.lifeStage.elderly",
  },
};

export function isLifeStageId(value: string): value is LifeStageId {
  return value === "youth" || value === "adult" || value === "elderly";
}
