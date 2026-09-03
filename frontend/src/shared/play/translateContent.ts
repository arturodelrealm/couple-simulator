import type { TOptions } from "i18next";

import i18n from "../../i18n";

/**
 * Resolve engine-sourced copy: i18n keys look up the active locale;
 * legacy English literals (not in the catalog) pass through unchanged.
 */
export function translateContent(
  keyOrText: string,
  params?: Record<string, unknown>,
): string {
  if (params === undefined) {
    return String(i18n.t(keyOrText));
  }
  return String(i18n.t(keyOrText, params as TOptions));
}
