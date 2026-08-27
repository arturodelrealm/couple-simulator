export const GAME_ID_STORAGE_KEY = "couple_simulator_game_id";

export function saveGameId(gameId: string): void {
  localStorage.setItem(GAME_ID_STORAGE_KEY, gameId);
}

export function getStoredGameId(): string | null {
  return localStorage.getItem(GAME_ID_STORAGE_KEY);
}

export function clearStoredGameId(): void {
  localStorage.removeItem(GAME_ID_STORAGE_KEY);
}
