"""Partner A questionnaire event listing (eligibility ignored)."""

from couple_simulator_engine.content.catalog import (
    load_catalog,
    package_events_directory,
)
from couple_simulator_engine.engine import GameEngine
from couple_simulator_engine.enums import PlayerRole, PlayerSex
from couple_simulator_engine.questionnaire import (
    list_partner_a_questionnaire_events,
    present_partner_a_questionnaire_events,
)


def _packaged_catalog():
    return load_catalog(package_events_directory())


def test_lists_all_packaged_events_except_work_party_crush() -> None:
    catalog = _packaged_catalog()
    events = list_partner_a_questionnaire_events(catalog)
    ids = [event.id for event in events]
    packaged_ids = {event.id for event in catalog.all_events()}

    assert "work_party_crush" in packaged_ids
    assert "work_party_crush" not in ids
    assert set(ids) == packaged_ids - {"work_party_crush"}
    assert len(events) == 21


def test_includes_events_with_eligibility_gates() -> None:
    catalog = _packaged_catalog()
    events = list_partner_a_questionnaire_events(catalog)
    gated = [event for event in events if event.eligibility is not None]
    assert any(event.id == "couples_therapy_suggestion" for event in gated)
    assert gated


def test_order_is_lexicographic_event_id() -> None:
    catalog = _packaged_catalog()
    ids = [event.id for event in list_partner_a_questionnaire_events(catalog)]
    assert ids == sorted(ids)


def test_does_not_require_session_or_mutate_catalog() -> None:
    catalog = _packaged_catalog()
    before = catalog.all_events()
    list_partner_a_questionnaire_events(catalog)
    assert catalog.all_events() == before


def test_present_wrapper_uses_present_event_for_partner_a() -> None:
    catalog = _packaged_catalog()
    engine = GameEngine(catalog)
    events = list_partner_a_questionnaire_events(catalog)
    presentations = present_partner_a_questionnaire_events(
        engine, catalog, player_sex=PlayerSex.FEMALE
    )
    assert len(presentations) == len(events)
    for event, presentation in zip(events, presentations, strict=True):
        expected = engine.present_event(
            event,
            player_role=PlayerRole.PARTNER_A,
            player_sex=PlayerSex.FEMALE,
        )
        assert presentation == expected
