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

  return (
    <div className="relative shrink-0">
      <div
        className="overflow-hidden rounded-full border-4 border-white shadow-md"
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
        className={`absolute flex h-7 w-7 items-center justify-center rounded-full bg-white font-display text-xs font-extrabold shadow ${badgeSideClass}`}
        style={{ color: badgeColor }}
      >
        {age}
      </div>
    </div>
  );
}
