import { ApiClientError } from "../services/apiClient";

export function getErrorI18nKey(code: string): string {
  const map: Record<string, string> = {
    GAME_NOT_FOUND: "errors.gameNotFound",
    INVALID_AVATAR_CONFIG: "errors.invalidAvatarConfig",
    VALIDATION_ERROR: "errors.validationError",
    BAD_REQUEST: "errors.badRequest",
    UNKNOWN_ERROR: "errors.generic",
  };
  return map[code] ?? "errors.generic";
}

export function toErrorMessage(
  error: unknown,
  t: (key: string) => string,
): string {
  if (error instanceof ApiClientError) {
    return t(getErrorI18nKey(error.code));
  }
  return t("errors.generic");
}
