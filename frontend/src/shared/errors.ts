import { ApiClientError } from "../services/apiClient";

const API_ERROR_I18N_KEYS: Record<string, string> = {
  GAME_NOT_FOUND: "errors.gameNotFound",
  GAME_NOT_READY: "game.play.errors.gameNotReady",
  RUN_NOT_FOUND: "game.play.errors.runNotFound",
  RUN_FINISHED: "game.play.errors.runFinished",
  NO_ELIGIBLE_EVENTS: "game.play.errors.noEligibleEvents",
  EVENT_MISMATCH: "game.play.errors.eventMismatch",
  EVENT_NOT_FOUND: "game.play.errors.eventNotFound",
  INVALID_ANSWERS: "game.play.errors.invalidAnswers",
};

export function toErrorMessage(
  error: unknown,
  t: (key: string) => string,
): string {
  if (error instanceof ApiClientError) {
    const key = API_ERROR_I18N_KEYS[error.code];
    if (key) {
      return t(key);
    }
    return error.message;
  }
  return t("errors.generic");
}
