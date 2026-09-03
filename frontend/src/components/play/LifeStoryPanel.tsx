import { useTranslation } from "react-i18next";

import type { TimelineEntry } from "../../services/simulationService";
import { STAT_CONFIG } from "../../shared/play/statConfig";
import { translateContent } from "../../shared/play/translateContent";
import type { StatsBarValues } from "./StatsBar";
import { PlayBookIcon } from "./playIcons";

export type LifeStoryPanelProps = {
  timeline: TimelineEntry[];
  stats: StatsBarValues;
};

export function LifeStoryPanel({ timeline, stats }: LifeStoryPanelProps) {
  const { t } = useTranslation();
  const glanceStats = STAT_CONFIG.filter((stat) => !stat.isCount).slice(0, 4);
  // GET run timeline is oldest-first (sort_index ascending); highlight the last item as newest.
  const newestIndex = timeline.length > 0 ? timeline.length - 1 : -1;

  return (
    <aside className="flex flex-col rounded-3xl border border-purple-50 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center gap-2">
        <PlayBookIcon className="h-4 w-4" style={{ color: "#A78BFA" }} />
        <h3 className="font-display text-sm font-bold text-slate-700">
          {t("game.play.lifeStory")}
        </h3>
      </div>

      <div className="max-h-80 flex-1 space-y-2 overflow-y-auto">
        {timeline.length === 0 ? (
          <p className="px-1 text-xs text-slate-400">
            {t("game.play.timeline.empty")}
          </p>
        ) : (
          timeline.map((entry, index) => {
            const isNewest = index === newestIndex;
            return (
              <div
                key={`${entry.title}-${entry.age}-${index}`}
                className={`flex items-start gap-3 rounded-xl p-3 ${
                  isNewest
                    ? "border border-purple-100 bg-purple-50"
                    : "bg-slate-50"
                }`}
              >
                <div
                  className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full"
                  style={{
                    background: isNewest ? "#a78bfa" : "#cbd5e1",
                  }}
                />
                <div>
                  <p
                    className={`text-xs font-semibold ${
                      isNewest ? "text-purple-700" : "text-slate-600"
                    }`}
                  >
                    {translateContent(entry.title)}
                  </p>
                  <p className="mt-0.5 text-xs text-slate-400">
                    {t("game.play.age", { age: entry.age })}
                  </p>
                  {entry.description ? (
                    <p className="mt-1 text-xs text-slate-500">
                      {translateContent(entry.description)}
                    </p>
                  ) : null}
                </div>
              </div>
            );
          })
        )}
      </div>

      <div className="mt-4 border-t border-slate-100 pt-4">
        <p className="mb-3 font-display text-xs font-bold uppercase tracking-widest text-slate-400">
          {t("game.play.atAGlance")}
        </p>
        <div className="grid grid-cols-2 gap-2">
          {glanceStats.map((stat) => (
            <div
              key={stat.key}
              className="rounded-xl p-2.5 text-center"
              style={{ background: stat.background }}
            >
              <div className="mb-1 flex justify-center">
                <stat.Icon className="h-4 w-4" style={{ color: stat.color }} />
              </div>
              <div
                className="font-display text-sm font-extrabold"
                style={{ color: stat.color }}
              >
                {stats[stat.key]}
              </div>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}
