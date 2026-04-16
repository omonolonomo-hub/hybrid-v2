"""
TDD — CardDatabase
"""
import os
import pytest
from engine_core.card import get_card_pool
from v2.core.card_database import CardDatabase, CardData

JSON_PATH = os.path.join(
    os.path.dirname(__file__), "..", "assets", "data", "cards.json"
)

@pytest.fixture(autouse=True)
def reset():
    CardDatabase.reset()
    yield
    CardDatabase.reset()


def test_raises_before_initialize():
    with pytest.raises(RuntimeError):
        CardDatabase.get()


def test_initialize_loads_cards():
    CardDatabase.initialize(JSON_PATH)
    db = CardDatabase.get()
    assert db.card_count > 50, "En az 50 kart yüklenmeli."


def test_lookup_known_card():
    CardDatabase.initialize(JSON_PATH)
    card = CardDatabase.get().lookup("Fibonacci Sequence")
    assert card is not None
    assert isinstance(card, CardData)
    assert card.name == "Fibonacci Sequence"


def test_lookup_returns_none_for_unknown():
    CardDatabase.initialize(JSON_PATH)
    result = CardDatabase.get().lookup("BU_KART_YOK")
    assert result is None


def test_card_has_passive_effect():
    CardDatabase.initialize(JSON_PATH)
    card = CardDatabase.get().lookup("Odin")
    assert card.passive_effect != ""
    assert len(card.passive_effect) > 10


def test_card_has_stats():
    CardDatabase.initialize(JSON_PATH)
    card = CardDatabase.get().lookup("Odin")
    assert isinstance(card.stats, dict)
    assert len(card.stats) >= 4


def test_card_rarity_level():
    CardDatabase.initialize(JSON_PATH)
    card = CardDatabase.get().lookup("Yggdrasil")  # ◆◆◆◆◆
    assert card.rarity_level == 5
    card2 = CardDatabase.get().lookup("Odin")  # ◆◆◆◆
    assert card2.rarity_level == 4


def test_card_rarity_color_is_tuple():
    CardDatabase.initialize(JSON_PATH)
    card = CardDatabase.get().lookup("Valhalla")
    color = card.rarity_color
    assert isinstance(color, tuple)
    assert len(color) == 3
    assert all(0 <= c <= 255 for c in color)


def test_card_passive_label_translated():
    CardDatabase.initialize(JSON_PATH)
    card = CardDatabase.get().lookup("Odin")   # passive_type: synergy_field
    assert card.passive_label == "SYNERGY FIELD"


def test_card_synergy_group_inferred():
    CardDatabase.initialize(JSON_PATH)
    card = CardDatabase.get().lookup("Isaac Newton")  # Science → MIND
    assert card.synergy_group == "MIND"


def test_rarity_level_with_engine_ascii_format():
    """engine_core '3' gibi ASCII rakam formatını da desteklemeli."""
    from v2.core.card_database import CardData
    # Simüle edilmiş engine_core runtime formatı: "3" (ASCII rakam)
    fake = CardData(
        name="FakeCard", category="Science", rarity="3",
        stats={}, passive_type="none", passive_effect="", synergy_group="MIND"
    )
    assert fake.rarity_level == 3, "engine_core '3' formatı rarity_level=3 vermeli"

def test_rarity_level_engine_format_all_tiers():
    """1..5 ve E tüm engine_core formatları doğru seviyeyi vermeli."""
    from v2.core.card_database import CardData
    for rarity_str, expected in [("1", 1), ("2", 2), ("3", 3), ("4", 4), ("5", 5)]:
        fake = CardData(
            name="X", category="Science", rarity=rarity_str,
            stats={}, passive_type="none", passive_effect="", synergy_group="MIND"
        )
        assert fake.rarity_level == expected, f"rarity='{rarity_str}' → beklenen {expected}"

def test_rarity_level_diamond_format_still_works():
    """Mevcut diamond format (◆◆◆) etkilenmemiş olmalı (regresyon testi)."""
    from v2.core.card_database import CardData
    fake = CardData(
        name="Y", category="Science", rarity="◆◆◆",
        stats={}, passive_type="none", passive_effect="", synergy_group="MIND"
    )
    assert fake.rarity_level == 3

def test_engine_pool_rarity_ids_are_supported_by_card_database_bridge():
    """Real engine pool rarity ids should map cleanly to DB rarity levels."""
    CardDatabase.initialize(JSON_PATH)
    db = CardDatabase.get()

    for engine_card in get_card_pool():
        data = db.lookup(engine_card.name)
        assert data is not None, f"DB lookup missing: {engine_card.name}"
        assert engine_card.rarity in {"1", "2", "3", "4", "5"}
        assert data.rarity_level == int(engine_card.rarity), (
            f"{engine_card.name}: engine rarity={engine_card.rarity}, "
            f"db rarity={data.rarity}, rarity_level={data.rarity_level}"
        )


def test_evolved_rarity_preserves_ui_badge_contract():
    """UI evolved badge detection relies on rarity='E' and rarity_level='E'."""
    fake = CardData(
        name="Evolved Fake",
        category="Science",
        rarity="E",
        stats={},
        passive_type="none",
        passive_effect="",
        synergy_group="MIND",
    )

    assert fake.rarity == "E"
    assert fake.rarity_level == "E"
    assert isinstance(fake.rarity_color, tuple)
    assert len(fake.rarity_color) == 3


def test_double_initialize_is_safe():
    """İki kez initialize() çağrısı ikinci kez yükleme yapmaz, hata atmaz."""
    CardDatabase.initialize(JSON_PATH)
    CardDatabase.initialize(JSON_PATH)   # İkinci çağrı
    assert CardDatabase.get().card_count > 0


def test_invalid_path_raises_error():
    with pytest.raises(FileNotFoundError):
        CardDatabase.initialize("/YOK/DIZI/cards.json")
