import type {
  AvatarConfig,
  AvatarVariantKey,
} from "../avatar/avataaarsVariants";
import {
  AVATAR_COLOR_KEYS,
  AVATAR_SECTIONS,
  AVATAR_VARIANTS,
} from "../avatar/avataaarsVariants";

export const PARTNER_B_PREFS_STORAGE_PREFIX =
  "couple_simulator_partner_b_prefs:";

export type PartnerBPreferences = {
  avatar_config: AvatarConfig;
  display_age: number;
};

function storageKey(gameId: string): string {
  return `${PARTNER_B_PREFS_STORAGE_PREFIX}${gameId}`;
}

function randomIndex(length: number): number {
  return Math.floor(Math.random() * length);
}

function pickControlledVariant(optionKey: AvatarVariantKey): string {
  const options = AVATAR_VARIANTS[optionKey];
  return options[randomIndex(options.length)] ?? options[0];
}

function isControlledVariant(
  optionKey: AvatarVariantKey,
  value: string,
): boolean {
  return AVATAR_VARIANTS[optionKey].includes(value);
}

function isAvatarConfig(value: unknown): value is AvatarConfig {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const record = value as Record<string, unknown>;
  for (const key of Object.keys(AVATAR_VARIANTS) as AvatarVariantKey[]) {
    const variant = record[key];
    if (variant === undefined) {
      continue;
    }
    if (typeof variant !== "string" || !isControlledVariant(key, variant)) {
      return false;
    }
  }
  if (
    record.accessoriesProbability !== undefined &&
    typeof record.accessoriesProbability !== "number"
  ) {
    return false;
  }
  if (
    record.facialHairProbability !== undefined &&
    typeof record.facialHairProbability !== "number"
  ) {
    return false;
  }
  return true;
}

export function isPartnerBPreferences(
  value: unknown,
): value is PartnerBPreferences {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const record = value as Record<string, unknown>;
  return (
    isAvatarConfig(record.avatar_config) &&
    typeof record.display_age === "number" &&
    Number.isFinite(record.display_age)
  );
}

export function generatePartnerBPreferences(
  displayAge: number,
): PartnerBPreferences {
  const avatar_config: AvatarConfig = {};
  for (const section of AVATAR_SECTIONS) {
    avatar_config[section.key] = pickControlledVariant(section.key);
    if (section.probabilityKey) {
      avatar_config[section.probabilityKey] = randomIndex(2) * 100;
    }
  }
  for (const colorKey of AVATAR_COLOR_KEYS) {
    avatar_config[colorKey] = pickControlledVariant(colorKey);
  }
  return {
    avatar_config,
    display_age: displayAge,
  };
}

export function savePartnerBPreferences(
  gameId: string,
  preferences: PartnerBPreferences,
): void {
  localStorage.setItem(storageKey(gameId), JSON.stringify(preferences));
}

export function loadPartnerBPreferences(
  gameId: string,
): PartnerBPreferences | null {
  const raw = localStorage.getItem(storageKey(gameId));
  if (!raw) {
    return null;
  }
  try {
    const parsed: unknown = JSON.parse(raw);
    if (!isPartnerBPreferences(parsed)) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

/** @deprecated Prefer lobby `game.partner_b` on the play screen. Only used when API Partner B is null. */
export function getOrCreatePartnerBPreferences(
  gameId: string,
  displayAge: number,
): PartnerBPreferences {
  const existing = loadPartnerBPreferences(gameId);
  if (existing) {
    return existing;
  }
  const generated = generatePartnerBPreferences(displayAge);
  savePartnerBPreferences(gameId, generated);
  return generated;
}
