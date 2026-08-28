import { ApiClientError } from "../services/apiClient";
import { getGame } from "../services/gameService";

export const CURRENT_GAME_STORAGE_KEY = "couple_simulator_current_game";
export const LEGACY_GAME_ID_STORAGE_KEY = "couple_simulator_game_id";

export type StoredCurrentGame = {
  game_id: string;
  match_name: string;
  last_visited_at: string;
};

export function saveCurrentGame(game: StoredCurrentGame): void {
  localStorage.setItem(CURRENT_GAME_STORAGE_KEY, JSON.stringify(game));
}

export function getCurrentGame(): StoredCurrentGame | null {
  const raw = localStorage.getItem(CURRENT_GAME_STORAGE_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as StoredCurrentGame;
  } catch {
    return null;
  }
}

export function clearCurrentGame(): void {
  localStorage.removeItem(CURRENT_GAME_STORAGE_KEY);
  localStorage.removeItem(LEGACY_GAME_ID_STORAGE_KEY);
}

export function touchCurrentGame(): void {
  const current = getCurrentGame();
  if (!current) {
    return;
  }
  saveCurrentGame({
    ...current,
    last_visited_at: new Date().toISOString(),
  });
}

export function getLegacyGameId(): string | null {
  return localStorage.getItem(LEGACY_GAME_ID_STORAGE_KEY);
}

function clearLegacyGameId(): void {
  localStorage.removeItem(LEGACY_GAME_ID_STORAGE_KEY);
}

export function saveCurrentGameFromGame(game: {
  id: string;
  match_name: string;
}): void {
  saveCurrentGame({
    game_id: game.id,
    match_name: game.match_name,
    last_visited_at: new Date().toISOString(),
  });
}

export async function migrateLegacyGameStorage(): Promise<StoredCurrentGame | null> {
  const existing = getCurrentGame();
  if (existing) {
    return existing;
  }

  const legacyId = getLegacyGameId();
  if (!legacyId) {
    return null;
  }

  try {
    const game = await getGame(legacyId);
    const stored: StoredCurrentGame = {
      game_id: game.id,
      match_name: game.match_name,
      last_visited_at: new Date().toISOString(),
    };
    saveCurrentGame(stored);
    clearLegacyGameId();
    return stored;
  } catch (error) {
    if (error instanceof ApiClientError && error.code === "GAME_NOT_FOUND") {
      clearCurrentGame();
      return null;
    }
    throw error;
  }
}
