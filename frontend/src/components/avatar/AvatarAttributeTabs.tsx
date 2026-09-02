import { useTranslation } from "react-i18next";

import type { AvatarTab } from "../../shared/avatar/avataaarsVariants";

export type AvatarAttributeTabsProps = {
  tabs: AvatarTab[];
  activeIndex: number;
  onChange: (index: number) => void;
};

export function AvatarAttributeTabs({
  tabs,
  activeIndex,
  onChange,
}: AvatarAttributeTabsProps) {
  const { t } = useTranslation();

  return (
    <div className="relative">
      <div
        role="tablist"
        aria-label={t("avatar.builder.attributes")}
        className="flex gap-1 overflow-x-auto border-b border-purple-100 pb-px"
      >
        {tabs.map((tab, index) => {
          const selected = index === activeIndex;
          return (
            <button
              key={tab.section.key}
              type="button"
              role="tab"
              id={`avatar-tab-${tab.section.key}`}
              aria-selected={selected}
              aria-controls={`avatar-panel-${tab.section.key}`}
              tabIndex={selected ? 0 : -1}
              onClick={() => onChange(index)}
              className={`shrink-0 whitespace-nowrap px-3 py-2 font-display text-sm font-bold transition-colors ${
                selected
                  ? "border-b-2 border-purple-500 text-purple-700"
                  : "border-b-2 border-transparent text-slate-500 hover:text-slate-800"
              }`}
            >
              {t(tab.section.titleKey)}
            </button>
          );
        })}
      </div>
    </div>
  );
}
