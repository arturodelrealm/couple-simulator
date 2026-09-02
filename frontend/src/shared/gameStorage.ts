import { ApiClientError } from "../services/apiClient";
import { getGame } from "../services/gameService";

export const CURRENT_GAME_STORAGE_KEY = "couple_simulator_current_game";
export const LEGACY_GAME_ID_STORAGE_KEY = "couple_simulator_game_id";

export type StoredCurrentGame = {
  game_id: string;
  match_name: string;
  last_visited_at: string;
  run_id?: string;
};

function isStoredCurrentGame(value: unknown): value is StoredCurrentGame {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const record = value as Record<string, unknown>;
  if (
    typeof record.game_id !== "string" ||
    typeof record.match_name !== "string" ||
    typeof record.last_visited_at !== "string"
  ) {
    return false;
  }
  if (record.run_id !== undefined && typeof record.run_id !== "string") {
    return false;
  }
  return true;
}

export function saveCurrentGame(game: StoredCurrentGame): void {
  localStorage.setItem(CURRENT_GAME_STORAGE_KEY, JSON.stringify(game));
}

export function getCurrentGame(): StoredCurrentGame | null {
  const raw = localStorage.getItem(CURRENT_GAME_STORAGE_KEY);
  if (!raw) {
    return null;
  }
  try {
    const parsed: unknown = JSON.parse(raw);
    if (!isStoredCurrentGame(parsed)) {
      return null;
    }
    return parsed;
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
  const existing = getCurrentGame();
  saveCurrentGame({
    game_id: game.id,
    match_name: game.match_name,
    run_id: existing?.game_id === game.id ? existing.run_id : undefined,
    last_visited_at: new Date().toISOString(),
  });
}

export function saveCurrentRunId(runId: string): void {
  const current = getCurrentGame();
  if (!current) {
    return;
  }
  saveCurrentGame({
    ...current,
    run_id: runId,
    last_visited_at: new Date().toISOString(),
  });
}

export function getCurrentRunId(): string | null {
  return getCurrentGame()?.run_id ?? null;
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
