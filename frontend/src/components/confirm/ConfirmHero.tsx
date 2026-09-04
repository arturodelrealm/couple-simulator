import { useTranslation } from "react-i18next";

import type { PlayerSex } from "../../services/gameService";
import type { AvatarConfig } from "../../shared/avatar/avataaarsVariants";
import { AvatarPreview } from "../../shared/ui/AvatarPreview";
import { theme } from "../../shared/ui/theme";

const SEX_LABEL_KEYS: Record<PlayerSex, string> = {
  male: "game.playerA.sex.male",
  female: "game.playerA.sex.female",
  prefer_not_to_say: "game.playerA.sex.preferNotToSay",
};

export type ConfirmHeroProps = {
  matchName: string;
  gameMode: string;
  partnerName: string | null;
  sex: PlayerSex | null;
  avatarConfig: AvatarConfig;
  seed: string;
};

export function ConfirmHero({
  matchName,
  gameMode,
  partnerName,
  sex,
  avatarConfig,
  seed,
}: ConfirmHeroProps) {
  const { t } = useTranslation();

  return (
    <section
      className="rounded-3xl border border-slate-200 px-6 py-8 text-center shadow-sm sm:px-10"
      style={{
        background: theme.headerGradient,
      }}
    >
      <span className="inline-block rounded-full bg-sky-50 px-2.5 py-1 text-xs font-semibold text-sky-700">
        {t("game.confirm.title")}
      </span>
      <h1 className="mt-3 font-display text-3xl font-extrabold tracking-tight text-slate-800 sm:text-4xl">
        {matchName}
      </h1>
      <p className="mt-2 text-sm text-slate-600">
        {t(`game.create.gameMode.${gameMode}`)}
      </p>
      <div className="mt-6">
        <AvatarPreview config={avatarConfig} seed={seed} size={180} />
      </div>
      {partnerName ? (
        <p className="mt-4 font-display text-xl font-extrabold text-slate-800">
          {partnerName}
        </p>
      ) : null}
      {sex ? (
        <p className="mt-1 text-sm text-slate-500">{t(SEX_LABEL_KEYS[sex])}</p>
      ) : null}
      <p className="mx-auto mt-4 max-w-md text-sm leading-relaxed text-slate-600">
        {t("game.confirm.subtitle")}
      </p>
    </section>
  );
}
