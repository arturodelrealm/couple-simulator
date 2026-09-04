import type { AvatarConfig } from "../../shared/avatar/avataaarsVariants";
import { createAvatarDataUri } from "../../shared/avatar/createAvatarSvg";

export type PlayAvatarProps = {
  config: AvatarConfig;
  seed: string;
  age: number;
  size?: number;
  background: string;
  badgeColor: string;
  badgeAlign: "left" | "right";
};

export function PlayAvatar({
  config,
  seed,
  age,
  size = 80,
  background,
  badgeColor,
  badgeAlign,
}: PlayAvatarProps) {
  const dataUri = createAvatarDataUri(config, seed, size);
  const badgeSideClass =
    badgeAlign === "right" ? "-bottom-1 -right-1" : "-bottom-1 -left-1";
  const compact = size <= 56;
  const badgeSizeClass = compact ? "h-5 w-5 text-[10px]" : "h-7 w-7 text-xs";
  const borderClass = compact ? "border-[3px]" : "border-4";

  return (
    <div className="relative shrink-0">
      <div
        className={`overflow-hidden rounded-full border-white shadow-md ${borderClass}`}
        style={{ width: size, height: size, background }}
      >
        <img
          src={dataUri}
          alt=""
          width={size}
          height={size}
          className="h-full w-full object-cover"
        />
      </div>
      <div
        className={`absolute flex items-center justify-center rounded-full bg-white font-display font-extrabold shadow ${badgeSizeClass} ${badgeSideClass}`}
        style={{ color: badgeColor }}
      >
        {age}
      </div>
    </div>
  );
}
