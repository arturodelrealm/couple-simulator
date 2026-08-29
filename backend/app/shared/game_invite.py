def build_invite_path(match_name: str) -> str:
    return f"/games/join/{match_name}"


def build_invite_url(
    invite_path: str,
    frontend_public_url: str | None,
) -> str | None:
    if not frontend_public_url:
        return None
    return f"{frontend_public_url.rstrip('/')}{invite_path}"
