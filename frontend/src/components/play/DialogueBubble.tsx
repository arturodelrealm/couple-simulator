export type DialogueSpeaker = "partner_a" | "partner_b" | "both";

export type DialogueBubbleProps = {
  speaker: DialogueSpeaker;
  text: string;
  partnerAName: string;
  partnerBName: string;
};

const SPEAKER_STYLES: Record<
  DialogueSpeaker,
  { color: string; background: string }
> = {
  partner_a: { color: "#EC4899", background: "#FDF2F8" },
  partner_b: { color: "#6366F1", background: "#EEF2FF" },
  both: { color: "#A78BFA", background: "#F5F3FF" },
};

export function DialogueBubble({
  speaker,
  text,
  partnerAName,
  partnerBName,
}: DialogueBubbleProps) {
  const isPartnerB = speaker === "partner_b";
  const styles = SPEAKER_STYLES[speaker];
  const name =
    speaker === "partner_a"
      ? partnerAName
      : speaker === "partner_b"
        ? partnerBName
        : `${partnerAName} · ${partnerBName}`;
  const initial = name.trim().charAt(0) || "?";

  return (
    <div
      className={`flex items-end gap-2 ${isPartnerB ? "flex-row-reverse" : ""}`}
    >
      <div
        className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white"
        style={{ background: styles.color }}
        title={name}
      >
        {initial}
      </div>
      <div
        className={`relative max-w-sm rounded-2xl px-4 py-2.5 text-sm italic leading-snug ${
          isPartnerB ? "rounded-br-sm" : "rounded-bl-sm"
        }`}
        style={{ background: styles.background, color: styles.color }}
      >
        {text}
        <span
          className={`absolute bottom-0 h-2.5 w-2.5 ${
            isPartnerB ? "-right-1" : "-left-1"
          }`}
          style={{
            background: styles.background,
            clipPath: isPartnerB
              ? "polygon(0 0, 100% 0, 0 100%)"
              : "polygon(100% 0, 0 0, 100% 100%)",
          }}
        />
      </div>
    </div>
  );
}
