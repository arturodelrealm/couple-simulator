import type { Game } from "../services/gameService";

export function isPlayerASetupComplete(game: Game): boolean {
  const { name, sex, avatar_config } = game.partner_a;
  return Boolean(name?.trim() && sex && avatar_config);
}

export function isGameReadyToPlay(game: Game): boolean {
  return game.status === "PLAYER_A_READY" && isPlayerASetupComplete(game);
}

export function getGameStepPath(game: Game): string {
  if (isPlayerASetupComplete(game)) {
    return `/games/${game.id}/confirm`;
  }
  return `/games/${game.id}/player-a`;
}

export function getPlayPath(gameId: string, runId: string): string {
  return `/games/${gameId}/play/${runId}`;
}
