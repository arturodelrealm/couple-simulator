import type { AvatarConfig } from "../shared/avatar/avataaarsVariants";
import { apiRequest } from "./apiClient";

export type PartnerA = {
  name: string | null;
  avatar_config: AvatarConfig | null;
};

export type Game = {
  id: string;
  status: string;
  partner_a: PartnerA;
};

export type CreateGamePayload = {
  partner_a_name: string;
};

export type UpdateGamePayload = {
  partner_a_name?: string;
  avatar_config?: AvatarConfig;
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

export function updateGame(
  gameId: string,
  payload: UpdateGamePayload,
): Promise<Game> {
  return apiRequest<Game>(`/api/games/${gameId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
