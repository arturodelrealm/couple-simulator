import { useState, type ReactNode } from "react";

import type {
  AvatarConfig,
  AvatarSection,
} from "../../shared/avatar/avataaarsVariants";
import {
  AVATAR_TABS,
  getSectionOptions,
} from "../../shared/avatar/avataaarsVariants";
import { AvatarPreview } from "../../shared/ui/AvatarPreview";
import { AvatarAttributeTabs } from "./AvatarAttributeTabs";
import { AvatarColorSwatches } from "./AvatarColorSwatches";
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
  const [activeTabIndex, setActiveTabIndex] = useState(0);
  const activeTab = AVATAR_TABS[activeTabIndex] ?? AVATAR_TABS[0];
  if (!activeTab) {
    return null;
  }

  const handleStyleSelect = (
    section: AvatarSection,
    value: string,
    enabled: boolean,
  ) => {
    const next: AvatarConfig = { ...config, [section.key]: value };
    if (section.probabilityKey) {
      next[section.probabilityKey] = enabled ? 100 : 0;
    }
    onChange(next);
  };

  return (
    <div className="space-y-5">
      <AvatarPreview config={config} seed={seed} size={180} />
      <AvatarAttributeTabs
        tabs={AVATAR_TABS}
        activeIndex={activeTabIndex}
        onChange={setActiveTabIndex}
      />
      {activeTab.kind === "style" ? (
        <div
          role="tabpanel"
          id={`avatar-panel-${activeTab.section.key}`}
          aria-labelledby={`avatar-tab-${activeTab.section.key}`}
        >
          <AvatarOptionSection
            optionKey={activeTab.section.key}
            options={getSectionOptions(activeTab.section.key)}
            value={config[activeTab.section.key]}
            probabilityKey={activeTab.section.probabilityKey}
            probabilityValue={
              activeTab.section.probabilityKey
                ? config[activeTab.section.probabilityKey]
                : undefined
            }
            config={config}
            onSelect={(value, enabled) =>
              handleStyleSelect(activeTab.section, value, enabled)
            }
          />
        </div>
      ) : (
        <div
          role="tabpanel"
          id={`avatar-panel-${activeTab.section.key}`}
          aria-labelledby={`avatar-tab-${activeTab.section.key}`}
        >
          <AvatarColorSwatches
            colorKey={activeTab.section.key}
            options={getSectionOptions(activeTab.section.key)}
            value={config[activeTab.section.key]}
            onSelect={(value) =>
              onChange({ ...config, [activeTab.section.key]: value })
            }
          />
        </div>
      )}
      {footer}
    </div>
  );
}
