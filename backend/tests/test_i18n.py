from app.shared.i18n import parse_accept_language, set_request_locale
from app.shared.i18n import translate as _


def test_parse_accept_language_prefers_supported_locale():
    assert parse_accept_language("es-ES,es;q=0.9,en;q=0.8") == "es"
    assert parse_accept_language("en-US,en;q=0.9") == "en"
    assert parse_accept_language(None) == "en"
    assert parse_accept_language("fr-FR,fr;q=0.9") == "en"


def test_translate_spanish_match_name_taken():
    set_request_locale("es")
    assert (
        _(
            "Match name is already taken",
        )
        == "Ese nombre de partida ya está en uso. Elige otro."
    )


def test_translate_english_is_msgid():
    set_request_locale("en")
    assert _("Match name is already taken") == "Match name is already taken"
