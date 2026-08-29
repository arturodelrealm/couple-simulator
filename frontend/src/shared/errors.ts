import { ApiClientError } from "../services/apiClient";

export function toErrorMessage(
  error: unknown,
  t: (key: string) => string,
): string {
  if (error instanceof ApiClientError) {
    return error.message;
  }
  return t("errors.generic");
}
