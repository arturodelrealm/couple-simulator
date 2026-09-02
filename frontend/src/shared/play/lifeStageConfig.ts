export type LifeStageId = "youth" | "adult" | "elderly";

export type LifeStageDisplayConfig = {
  color: string;
  labelKey: string;
};

export const LIFE_STAGE_CONFIG: Record<LifeStageId, LifeStageDisplayConfig> = {
  youth: {
    color: "#F472B6",
    labelKey: "game.play.lifeStage.youth",
  },
  adult: {
    color: "#A78BFA",
    labelKey: "game.play.lifeStage.adult",
  },
  elderly: {
    color: "#FBBF24",
    labelKey: "game.play.lifeStage.elderly",
  },
};

export function isLifeStageId(value: string): value is LifeStageId {
  return value === "youth" || value === "adult" || value === "elderly";
}
