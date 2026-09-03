import { useTranslation } from "react-i18next";

import type { PlayerSex } from "../../services/gameService";
import type { AvatarConfig } from "../../shared/avatar/avataaarsVariants";
import { AvatarPreview } from "../../shared/ui/AvatarPreview";

const SEX_LABEL_KEYS: Record<PlayerSex, string> = {
  male: "game.playerB.sex.male",
  female: "game.playerB.sex.female",
  prefer_not_to_say: "game.playerB.sex.preferNotToSay",
};

export type ConfirmPartnerBProps = {
  name: string | null;
  sex: PlayerSex | null;
  avatarConfig: AvatarConfig;
  seed: string;
};

export function ConfirmPartnerB({
  name,
  sex,
  avatarConfig,
  seed,
}: ConfirmPartnerBProps) {
  const { t } = useTranslation();

  return (
    <section className="rounded-3xl border border-purple-50 bg-white px-6 py-6 text-center shadow-sm sm:px-8">
      <span className="inline-block rounded-full bg-indigo-50 px-2.5 py-1 text-xs font-semibold text-indigo-500">
        {t("game.confirm.partnerBHeading")}
      </span>
      <div className="mt-4">
        <AvatarPreview config={avatarConfig} seed={seed} size={120} />
      </div>
      {name ? (
        <p className="mt-3 font-display text-xl font-extrabold text-slate-800">
          {name}
        </p>
      ) : null}
      {sex ? (
        <p className="mt-1 text-sm text-slate-500">{t(SEX_LABEL_KEYS[sex])}</p>
      ) : null}
    </section>
  );
}
