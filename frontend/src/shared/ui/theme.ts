export const theme = {
  page: "#F8FAFC",
  card: "#FFFFFF",
  primary: "#0284C7",
  primaryBright: "#0EA5E9",
  primaryLight: "#F0F9FF",
  heart: "#F43F5E",
  border: "#E2E8F0",
  headerGradient: "linear-gradient(90deg, #F0F9FF, #F8FAFC, #FFF7ED)",
  ctaGradient: "linear-gradient(135deg, #0284C7, #0EA5E9)",
  progressGradient: "linear-gradient(90deg, #0284C7, #0EA5E9)",
  partnerA: { color: "#0284C7", background: "#F0F9FF" },
  partnerB: { color: "#E11D48", background: "#FFF1F2" },
  both: { color: "#7C3AED", background: "#F5F3FF" },
  eventAccents: [
    "#0284C7",
    "#16A34A",
    "#EA580C",
    "#7C3AED",
    "#E11D48",
    "#059669",
  ],
} as const;

export function eventAccentForId(eventId: string): string {
  let hash = 0;
  for (let i = 0; i < eventId.length; i += 1) {
    hash = (hash * 31 + eventId.charCodeAt(i)) >>> 0;
  }
  return theme.eventAccents[hash % theme.eventAccents.length];
}
