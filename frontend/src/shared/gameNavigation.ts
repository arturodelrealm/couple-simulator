import type { Game } from "../services/gameService";
import type { SimulationPlayerRole } from "../services/simulationService";

export type PlayPlayerRole = SimulationPlayerRole;

export function parsePlayPlayerRole(
  value: string | null | undefined,
): PlayPlayerRole | null {
  if (value === "partner_a" || value === "partner_b") {
    return value;
  }
  return null;
}

export function getConfirmPath(gameId: string): string {
  return `/games/${gameId}/confirm`;
}

export function getPlayEntryPath(gameId: string, role: PlayPlayerRole): string {
  return `/games/${gameId}/play?role=${role}`;
}

export function isPlayerASetupComplete(game: Game): boolean {
  const { name, sex, avatar_config } = game.partner_a;
  return Boolean(name?.trim() && sex && avatar_config);
}

export function isPlayerBSetupComplete(game: Game): boolean {
  const partnerB = game.partner_b;
  if (!partnerB) {
    return false;
  }
  const { name, sex, avatar_config } = partnerB;
  return Boolean(name?.trim() && sex && avatar_config);
}

export function getPlayerBSetupPath(gameId: string): string {
  return `/games/${gameId}/player-b`;
}

export function isGameReadyToPlay(game: Game): boolean {
  return (
    (game.status === "PLAYER_A_READY" || game.status === "PLAYER_B_PLAYING") &&
    isPlayerASetupComplete(game)
  );
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

export function getPartnerAQuestionnairePath(gameId: string): string {
  return `/games/${gameId}/partner-a/questions`;
}
