import type { SVGProps } from "react";

type ConfirmIconProps = SVGProps<SVGSVGElement>;

const strokeDefaults = {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true as const,
};

export function ConfirmCopyIcon(props: ConfirmIconProps) {
  return (
    <svg {...strokeDefaults} {...props}>
      <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
      <path d="M4 16c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2h8c1.1 0 2 .9 2 2" />
    </svg>
  );
}

export function ConfirmCheckIcon(props: ConfirmIconProps) {
  return (
    <svg {...strokeDefaults} {...props}>
      <path d="M20 6 9 17l-5-5" />
    </svg>
  );
}
