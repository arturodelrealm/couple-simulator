import type { AvatarConfig } from "../shared/avatar/avataaarsVariants";
import { apiRequest } from "./apiClient";

export type PlayerSex = "male" | "female" | "prefer_not_to_say";
export type GameMode = "couple";
export type GameStatus =
  "CREATED" | "PLAYER_A_READY" | "PLAYER_B_PLAYING" | "FINISHED";

export type PartnerA = {
  name: string | null;
  sex: PlayerSex | null;
  avatar_config: AvatarConfig | null;
};

export type Game = {
  id: string;
  match_name: string;
  game_mode: GameMode;
  status: GameStatus;
  partner_a: PartnerA;
};

export type CreateGamePayload = {
  match_name: string;
  game_mode?: GameMode;
  partner_a_name?: string;
  partner_a_sex?: PlayerSex;
  avatar_config?: AvatarConfig;
};

export type UpdateGamePayload = {
  partner_a_name?: string;
  partner_a_sex?: PlayerSex;
  avatar_config?: AvatarConfig;
};

export type GameInvite = {
  game_id: string;
  match_name: string;
  invite_path: string;
  invite_url: string | null;
};

export function createGame(payload: CreateGamePayload): Promise<Game> {
  return apiRequest<Game>("/api/games", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getGame(gameId: string): Promise<Game> {
  return apiRequest<Game>(`/api/games/${gameId}`);
}

export function getGameInvite(gameId: string): Promise<GameInvite> {
  return apiRequest<GameInvite>(`/api/games/${gameId}/invite`);
}

export function getGameByMatchName(matchName: string): Promise<Game> {
  return apiRequest<Game>(
    `/api/games/by-match-name/${encodeURIComponent(matchName)}`,
  );
}

export function updateGame(
  gameId: string,
  payload: UpdateGamePayload,
): Promise<Game> {
  return apiRequest<Game>(`/api/games/${gameId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
