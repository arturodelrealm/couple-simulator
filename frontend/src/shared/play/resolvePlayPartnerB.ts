import type { Game } from "../../services/gameService";
import type { AvatarConfig } from "../avatar/avataaarsVariants";
import { getOrCreatePartnerBPreferences } from "./partnerBPreferences";

export type PlayPartnerBIdentity = {
  nameFromApi: string | null;
  avatarConfig: AvatarConfig;
  seed: string;
  displayAge: number;
};

export function resolvePlayPartnerB(
  game: Game,
  simulationAge: number,
): PlayPartnerBIdentity {
  const partnerB = game.partner_b;
  if (partnerB) {
    const name = partnerB.name?.trim() ? partnerB.name : null;
    return {
      nameFromApi: name,
      avatarConfig: partnerB.avatar_config ?? {},
      seed: name ?? game.id,
      displayAge: simulationAge,
    };
  }

  const fallback = getOrCreatePartnerBPreferences(game.id, simulationAge);
  return {
    nameFromApi: null,
    avatarConfig: fallback.avatar_config,
    seed: `${game.id}-partner-b`,
    displayAge: fallback.display_age,
  };
}
