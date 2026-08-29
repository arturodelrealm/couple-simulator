import type { Game } from "../services/gameService";

export function isPlayerASetupComplete(game: Game): boolean {
  const { name, sex, avatar_config } = game.partner_a;
  return Boolean(name?.trim() && sex && avatar_config);
}

export function getGameStepPath(game: Game): string {
  if (isPlayerASetupComplete(game)) {
    return `/games/${game.id}/confirm`;
  }
  return `/games/${game.id}/player-a`;
}
