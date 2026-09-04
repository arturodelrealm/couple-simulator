import { Avatar, Style } from "@dicebear/core";
import avataaarsDefinition from "@dicebear/styles/avataaars.json";

import type { AvatarConfig } from "./avataaarsVariants";

const style = new Style(avataaarsDefinition);

const PROBABILITY_KEYS = new Set([
  "accessoriesProbability",
  "facialHairProbability",
]);

function toProbability(value: unknown): number | undefined {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }
  return undefined;
}

function toDiceBearOptions(
  config: AvatarConfig,
): Record<string, string | number> {
  const options: Record<string, string | number> = {};
  for (const [key, value] of Object.entries(config)) {
    if (value === undefined) {
      continue;
    }
    if (PROBABILITY_KEYS.has(key)) {
      const probability = toProbability(value);
      if (probability !== undefined) {
        options[key] = probability;
      }
      continue;
    }
    options[key] = String(value);
  }
  return options;
}

export function createAvatarDataUri(
  config: AvatarConfig,
  seed: string,
  size = 128,
): string {
  try {
    const avatar = new Avatar(style, {
      ...toDiceBearOptions(config),
      seed,
      size,
    });
    return avatar.toDataUri();
  } catch {
    return "";
  }
}
