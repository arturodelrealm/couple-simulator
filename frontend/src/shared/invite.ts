export function resolveInviteUrl(
  invitePath: string,
  inviteUrl: string | null,
): string {
  if (inviteUrl) {
    return inviteUrl;
  }
  return `${window.location.origin}${invitePath}`;
}

export async function copyInviteUrl(url: string): Promise<void> {
  await navigator.clipboard.writeText(url);
}
