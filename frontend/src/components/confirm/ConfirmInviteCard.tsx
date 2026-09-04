import { useTranslation } from "react-i18next";

import { ErrorMessage } from "../../shared/ui/ErrorMessage";
import { ConfirmCheckIcon, ConfirmCopyIcon } from "./confirmIcons";

export type ConfirmInviteCardProps = {
  inviteUrl: string;
  onCopy: () => void;
  copied: boolean;
  copyError: string | null;
};

export function ConfirmInviteCard({
  inviteUrl,
  onCopy,
  copied,
  copyError,
}: ConfirmInviteCardProps) {
  const { t } = useTranslation();

  return (
    <div className="space-y-3 overflow-hidden rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="font-display text-lg font-extrabold text-slate-800">
        {t("game.confirm.inviteLabel")}
      </p>
      <p className="text-sm leading-relaxed text-slate-600">
        {t("game.confirm.inviteHint")}
      </p>
      <input
        type="text"
        readOnly
        value={inviteUrl}
        className="w-full rounded-2xl border border-slate-200 bg-sky-50/50 px-4 py-2.5 font-mono text-sm text-slate-700 focus:outline-none"
      />
      <button
        type="button"
        onClick={onCopy}
        className="flex w-full items-center justify-center gap-2 rounded-2xl border-2 border-slate-200 bg-white px-5 py-3 font-display text-base font-bold text-slate-700 transition-all hover:border-sky-300 hover:bg-sky-50"
      >
        {copied ? (
          <ConfirmCheckIcon className="h-4 w-4 text-sky-600" />
        ) : (
          <ConfirmCopyIcon className="h-4 w-4" />
        )}
        {copied
          ? t("game.confirm.inviteCopied")
          : t("game.confirm.copyInviteLink")}
      </button>
      {copyError ? <ErrorMessage message={copyError} /> : null}
    </div>
  );
}
