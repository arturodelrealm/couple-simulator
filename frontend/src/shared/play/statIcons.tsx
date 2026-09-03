import type { SVGProps } from "react";

export type StatIconProps = SVGProps<SVGSVGElement>;

const svgDefaults = {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true as const,
};

export function CompatibilityIcon(props: StatIconProps) {
  return (
    <svg {...svgDefaults} {...props}>
      <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
    </svg>
  );
}

export function FinancesIcon(props: StatIconProps) {
  return (
    <svg {...svgDefaults} {...props}>
      <circle cx="8" cy="8" r="6" />
      <path d="M18.09 10.37A6 6 0 1 1 10.34 18" />
      <path d="M7 6h1v4" />
    </svg>
  );
}

export function ChildrenIcon(props: StatIconProps) {
  return (
    <svg {...svgDefaults} {...props}>
      <circle cx="12" cy="8" r="4" />
      <path d="M8 21v-2a4 4 0 0 1 8 0v2" />
      <path d="M10 8h.01" />
      <path d="M14 8h.01" />
    </svg>
  );
}

export function QualityOfLifeIcon(props: StatIconProps) {
  return (
    <svg {...svgDefaults} {...props}>
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
  );
}
