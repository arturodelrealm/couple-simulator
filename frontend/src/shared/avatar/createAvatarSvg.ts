import { Avatar, Style } from "@dicebear/core";
import avataaarsDefinition from "@dicebear/styles/avataaars.json";

import type { AvatarConfig } from "./avataaarsVariants";

const style = new Style(avataaarsDefinition);

function toDiceBearOptions(config: AvatarConfig): Record<string, string | number> {
  const options: Record<string, string | number> = {};
  for (const [key, value] of Object.entries(config)) {
    if (value !== undefined) {
      options[key] = value;
    }
  }
  return options;
}

export function createAvatarDataUri(
  config: AvatarConfig,
  seed: string,
  size = 128,
): string {
  const avatar = new Avatar(style, {
    ...toDiceBearOptions(config),
    seed,
    size,
  });
  return avatar.toDataUri();
}
