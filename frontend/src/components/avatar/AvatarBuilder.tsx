import type { ReactNode } from "react";

import type { AvatarConfig } from "../../shared/avatar/avataaarsVariants";
import {
  AVATAR_SECTIONS,
  getSectionOptions,
} from "../../shared/avatar/avataaarsVariants";
import { AvatarPreview } from "../../shared/ui/AvatarPreview";
import { AvatarOptionSection } from "./AvatarOptionSection";

type AvatarBuilderProps = {
  config: AvatarConfig;
  seed: string;
  onChange: (config: AvatarConfig) => void;
  footer?: ReactNode;
};

export function AvatarBuilder({
  config,
  seed,
  onChange,
  footer,
}: AvatarBuilderProps) {
  const handleSelect = (
    sectionKey: (typeof AVATAR_SECTIONS)[number],
    value: string,
    enabled: boolean,
  ) => {
    const next: AvatarConfig = { ...config, [sectionKey.key]: value };
    if (sectionKey.probabilityKey) {
      next[sectionKey.probabilityKey] = enabled ? 100 : 0;
    }
    onChange(next);
  };

  return (
    <div className="space-y-6">
      <AvatarPreview config={config} seed={seed} size={180} />
      {AVATAR_SECTIONS.map((section) => (
        <AvatarOptionSection
          key={section.key}
          titleKey={section.titleKey}
          optionKey={section.key}
          options={getSectionOptions(section.key)}
          value={config[section.key]}
          probabilityKey={section.probabilityKey}
          probabilityValue={
            section.probabilityKey ? config[section.probabilityKey] : undefined
          }
          config={config}
          onSelect={(value, enabled) => handleSelect(section, value, enabled)}
        />
      ))}
      {footer}
    </div>
  );
}
