"""Request-scoped translations for user-facing API messages.

We use JSON locale catalogs (``backend/locales/<lang>.json``) instead of GNU
gettext ``.po`` / ``.mo`` files. English strings in code act as the message
keys; non-default locales map those keys to translated text.

Why JSON and not gettext?

- The standard flow is ``.po`` → ``msgfmt`` → ``.mo`` → ``gettext.translation()``.
- That requires ``msgfmt`` at build/dev time and a correct binary ``.mo`` file.
- For a small, fixed set of API error messages, JSON is easier to edit, avoids a
  compilation step, and handles UTF-8 without tooling issues.

Call sites should import the translator as the conventional alias::

    from app.shared.i18n import translate as _

Locale is set per request by ``LocaleMiddleware`` from the ``Accept-Language``
header. Add or update entries in ``backend/locales/es.json`` when introducing
new translatable strings.
"""

import json
from contextvars import ContextVar
from pathlib import Path

LOCALES_DIR = Path(__file__).resolve().parents[2] / "locales"
SUPPORTED_LOCALES = frozenset({"en", "es"})
DEFAULT_LOCALE = "en"

_locale: ContextVar[str] = ContextVar("locale", default=DEFAULT_LOCALE)
_translations: dict[str, dict[str, str]] = {}


def _init_translations() -> None:
    for locale in SUPPORTED_LOCALES:
        if locale == DEFAULT_LOCALE:
            continue
        catalog_path = LOCALES_DIR / f"{locale}.json"
        if catalog_path.is_file():
            _translations[locale] = json.loads(
                catalog_path.read_text(encoding="utf-8"),
            )


_init_translations()


def parse_accept_language(header: str | None) -> str:
    if not header:
        return DEFAULT_LOCALE

    for part in header.split(","):
        token = part.strip().split(";")[0].lower()
        if not token:
            continue
        primary = token.split("-")[0]
        if primary in SUPPORTED_LOCALES:
            return primary

    return DEFAULT_LOCALE


def set_request_locale(accept_language: str | None) -> None:
    _locale.set(parse_accept_language(accept_language))


def get_locale() -> str:
    return _locale.get()


def translate(message: str) -> str:
    """Return *message* translated for the current request locale."""
    locale = get_locale()
    if locale == DEFAULT_LOCALE:
        return message

    return _translations.get(locale, {}).get(message, message)
