import variantsJson from "./avataaarsVariants.json";

export type AvatarStyleKey =
  | "topVariant"
  | "eyesVariant"
  | "eyebrowsVariant"
  | "mouthVariant"
  | "facialHairVariant"
  | "clothesVariant"
  | "accessoriesVariant";

export type AvatarColorKey =
  "skinColor" | "hairColor" | "facialHairColor" | "clothesColor";

export type AvatarVariantKey = AvatarStyleKey | AvatarColorKey;

export type AvatarConfig = Partial<
  Record<AvatarVariantKey, string> & {
    accessoriesProbability: number;
    facialHairProbability: number;
  }
>;

export const AVATAR_VARIANTS = variantsJson as Record<
  AvatarVariantKey,
  string[]
>;

export const AVATAR_COLOR_KEYS: AvatarColorKey[] = [
  "skinColor",
  "hairColor",
  "facialHairColor",
  "clothesColor",
];

export const AVATAR_COLOR_LABEL_KEYS: Record<AvatarColorKey, string> = {
  skinColor: "avatar.section.skin",
  hairColor: "avatar.section.hairColor",
  facialHairColor: "avatar.section.facialHairColor",
  clothesColor: "avatar.section.clothesColor",
};

export type AvatarSection = {
  key: AvatarStyleKey;
  titleKey: string;
  probabilityKey?: "accessoriesProbability" | "facialHairProbability";
};

export const AVATAR_SECTIONS: AvatarSection[] = [
  { key: "topVariant", titleKey: "avatar.section.hair" },
  { key: "eyesVariant", titleKey: "avatar.section.eyes" },
  { key: "eyebrowsVariant", titleKey: "avatar.section.eyebrows" },
  { key: "mouthVariant", titleKey: "avatar.section.mouth" },
  {
    key: "facialHairVariant",
    titleKey: "avatar.section.facialHair",
    probabilityKey: "facialHairProbability",
  },
  { key: "clothesVariant", titleKey: "avatar.section.clothes" },
  {
    key: "accessoriesVariant",
    titleKey: "avatar.section.accessories",
    probabilityKey: "accessoriesProbability",
  },
];

export type AvatarColorSection = {
  key: AvatarColorKey;
  titleKey: string;
};

export const AVATAR_COLOR_SECTIONS: AvatarColorSection[] = [
  { key: "hairColor", titleKey: "avatar.section.hairColor" },
  { key: "skinColor", titleKey: "avatar.section.skin" },
  { key: "facialHairColor", titleKey: "avatar.section.facialHairColor" },
  { key: "clothesColor", titleKey: "avatar.section.clothesColor" },
];

export type AvatarTab =
  | { kind: "style"; section: AvatarSection }
  | { kind: "color"; section: AvatarColorSection };

function styleTab(key: AvatarStyleKey): AvatarTab {
  const section = AVATAR_SECTIONS.find((item) => item.key === key);
  if (!section) {
    throw new Error(`Missing avatar style section: ${key}`);
  }
  return { kind: "style", section };
}

function colorTab(key: AvatarColorKey): AvatarTab {
  const section = AVATAR_COLOR_SECTIONS.find((item) => item.key === key);
  if (!section) {
    throw new Error(`Missing avatar color section: ${key}`);
  }
  return { kind: "color", section };
}

export const AVATAR_TABS: AvatarTab[] = [
  styleTab("topVariant"),
  colorTab("hairColor"),
  colorTab("skinColor"),
  styleTab("eyesVariant"),
  styleTab("eyebrowsVariant"),
  styleTab("mouthVariant"),
  styleTab("facialHairVariant"),
  colorTab("facialHairColor"),
  styleTab("clothesVariant"),
  colorTab("clothesColor"),
  styleTab("accessoriesVariant"),
];

export function getSectionOptions(optionKey: AvatarVariantKey): string[] {
  return AVATAR_VARIANTS[optionKey];
}
