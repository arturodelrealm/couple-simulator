import { useTranslation } from "react-i18next";

import type { AvatarColorKey } from "../../shared/avatar/avataaarsVariants";
import { AVATAR_COLOR_LABEL_KEYS } from "../../shared/avatar/avataaarsVariants";

export type AvatarColorSwatchesProps = {
  colorKey: AvatarColorKey;
  options: string[];
  value: string | undefined;
  onSelect: (value: string) => void;
};

function toCssHex(hex: string): string {
  return hex.startsWith("#") ? hex : `#${hex}`;
}

export function AvatarColorSwatches({
  colorKey,
  options,
  value,
  onSelect,
}: AvatarColorSwatchesProps) {
  const { t } = useTranslation();
  const attributeLabel = t(AVATAR_COLOR_LABEL_KEYS[colorKey]);

  return (
    <div className="flex flex-wrap gap-3">
      {options.map((hex) => {
        const selected = value === hex;
        return (
          <button
            key={hex}
            type="button"
            aria-label={t("avatar.color.swatch", {
              color: hex,
              attribute: attributeLabel,
            })}
            aria-pressed={selected}
            onClick={() => onSelect(hex)}
            className={`h-10 w-10 rounded-full border border-slate-200 shadow-sm transition-transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-sky-300 ${
              selected ? "ring-2 ring-sky-500 ring-offset-2" : ""
            }`}
            style={{ backgroundColor: toCssHex(hex) }}
          />
        );
      })}
    </div>
  );
}
