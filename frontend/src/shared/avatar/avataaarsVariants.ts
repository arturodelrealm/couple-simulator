import variantsJson from "./avataaarsVariants.json";

export type AvatarVariantKey =
  | "topVariant"
  | "eyesVariant"
  | "eyebrowsVariant"
  | "mouthVariant"
  | "facialHairVariant"
  | "clothesVariant"
  | "accessoriesVariant";

export type AvatarConfig = Partial<
  Record<AvatarVariantKey, string> & {
    accessoriesProbability: number;
    facialHairProbability: number;
  }
>;

export const AVATAR_VARIANTS = variantsJson as Record<AvatarVariantKey, string[]>;

export type AvatarSection = {
  key: AvatarVariantKey;
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
