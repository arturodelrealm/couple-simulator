import type { SVGProps } from "react";

type LobbyIconProps = SVGProps<SVGSVGElement>;

const strokeDefaults = {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true as const,
};

export function LobbyPlusIcon(props: LobbyIconProps) {
  return (
    <svg {...strokeDefaults} {...props}>
      <path d="M5 12h14" />
      <path d="M12 5v14" />
    </svg>
  );
}

export function LobbyJoinIcon(props: LobbyIconProps) {
  return (
    <svg {...strokeDefaults} {...props}>
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M19 8v6" />
      <path d="M22 11h-6" />
    </svg>
  );
}
