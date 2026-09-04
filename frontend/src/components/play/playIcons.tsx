import type { SVGProps } from "react";

type PlayIconProps = SVGProps<SVGSVGElement>;

const strokeDefaults = {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true as const,
};

export function PlayHeartIcon(props: PlayIconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" {...props}>
      <path
        fill="currentColor"
        d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"
      />
    </svg>
  );
}

export function PlayBookIcon(props: PlayIconProps) {
  return (
    <svg {...strokeDefaults} {...props}>
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z" />
    </svg>
  );
}

export function PlayRefreshIcon(props: PlayIconProps) {
  return (
    <svg {...strokeDefaults} {...props}>
      <path d="M3 12a9 9 0 0 1 15.5-6.36L21 8" />
      <path d="M21 3v5h-5" />
      <path d="M21 12a9 9 0 0 1-15.5 6.36L3 16" />
      <path d="M8 16H3v5" />
    </svg>
  );
}

export function CatMascotIcon(props: PlayIconProps) {
  return (
    <svg {...strokeDefaults} {...props}>
      <path d="M12 5c.67 0 1.35.09 2 .26 1.78-2 5.03-2.84 6.42-2.26 1.4.58-.42 7-.42 7 .57 1.07 1 2.24 1 3.44C21 17.9 16.97 21 12 21s-9-3.1-9-7.56c0-1.21.43-2.38 1-3.44 0 0-1.81-6.42-.42-7 1.39-.58 4.64.26 6.42 2.26.65-.17 1.33-.26 2-.26Z" />
      <path d="M8 14v.5" />
      <path d="M16 14v.5" />
      <path d="M11.25 16.25h1.5L12 17l-.75-.75Z" />
    </svg>
  );
}

export function DogMascotIcon(props: PlayIconProps) {
  return (
    <svg {...strokeDefaults} {...props}>
      <path d="M10 5.172C10 3.782 8.423 2.679 6.5 3c-2.823.47-4.113 6.006-4 7 .08.703 1.725 1.722 3.656 1 1.261-.472 1.96-1.45 2.344-2.5" />
      <path d="M14.267 5.172c0-1.39 1.577-2.493 3.5-2.172 2.823.47 4.113 6.006 4 7-.08.703-1.725 1.722-3.656 1-1.261-.472-1.96-1.45-2.344-2.5" />
      <path d="M8 14v.5" />
      <path d="M16 14v.5" />
      <path d="M11.25 16.25h1.5L12 17l-.75-.75Z" />
      <path d="M4.42 11.247A13.152 13.152 0 0 0 4 14.556C4 18.728 7.582 21 12 21s8-2.272 8-6.444c0-1.061-.162-2.2-.493-3.309m-9.243-6.082A8.801 8.801 0 0 1 12 5c.78 0 1.5.108 2.161.306" />
    </svg>
  );
}

export function HamsterMascotIcon(props: PlayIconProps) {
  return (
    <svg {...strokeDefaults} {...props}>
      <circle cx="12" cy="13" r="7" />
      <path d="M8 8.5c-1.5-2.5-4-2-4 .5 0 1.5 1.2 2.2 2.5 2.4" />
      <path d="M16 8.5c1.5-2.5 4-2 4 .5 0 1.5-1.2 2.2-2.5 2.4" />
      <path d="M9 13h.01" />
      <path d="M15 13h.01" />
      <path d="M10.5 16c.8.6 2.2.6 3 0" />
    </svg>
  );
}

export function GenericMascotIcon(props: PlayIconProps) {
  return (
    <svg {...strokeDefaults} {...props}>
      <circle cx="11" cy="4" r="2" />
      <circle cx="18" cy="8" r="2" />
      <circle cx="20" cy="16" r="2" />
      <path d="M9 10a5 5 0 0 1 5 5v3.5a3.5 3.5 0 0 1-7 0" />
      <path d="M8 14.05A6 6 0 0 1 18.2 8.8" />
      <path d="M11.5 13.5A6 6 0 0 1 20 18.2" />
    </svg>
  );
}
