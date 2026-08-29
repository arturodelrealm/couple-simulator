const MATCH_NAME_PATTERN = /^[a-z0-9_-]{3,32}$/;

export function normalizeMatchName(value: string): string {
  return value.trim().toLowerCase();
}

export function isValidMatchName(value: string): boolean {
  return MATCH_NAME_PATTERN.test(normalizeMatchName(value));
}
