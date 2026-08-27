import type { AvatarConfig } from "../avatar/avataaarsVariants";
import { createAvatarDataUri } from "../avatar/createAvatarSvg";

type AvatarPreviewProps = {
  config: AvatarConfig;
  seed: string;
  size?: number;
};

export function AvatarPreview({
  config,
  seed,
  size = 160,
}: AvatarPreviewProps) {
  const dataUri = createAvatarDataUri(config, seed, size);

  return (
    <div className="flex justify-center">
      <img
        src={dataUri}
        alt=""
        width={size}
        height={size}
        className="rounded-full bg-white shadow-md"
      />
    </div>
  );
}
