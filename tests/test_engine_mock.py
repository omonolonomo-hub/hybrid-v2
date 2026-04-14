import pytest
from v2.mock.engine_mock import MockGame

def test_mockgame_initial_state_contract():
    """Motor başlatıldığında deterministik varsayılan (default) kuralları garanti etmelidir."""
    game = MockGame()

    # 1. Tur 1'den başlamalı
    assert game.turn == 1

    # 2. Oyun başlarken oyun durumu SHOP olmalı
    assert game.state == "SHOP"

    # 3. İçinde sahte oyuncuların listesi olmalı (8 kişilik boş dizi veya varsayılanlar)
    assert isinstance(game.players, list)

def test_mockgame_deterministic_player_fixture_exists():
    game = MockGame()
    game.initialize_deterministic_fixture() # Sabit statlar yükle

    assert len(game.players) == 8
    # Ana oyuncumuz (Human) Player1 (veya Player 0) olmalı ve başlangıç statları can = 100 olmalı.
    assert game.players[0].hp == 150
    assert game.players[0].gold == 10


# ── Phase 3c item 28: MockPlayer yeni alanlar ─────────────────────────────

def test_mockplayer_has_win_streak():
    from v2.mock.engine_mock import MockPlayer
    p = MockPlayer()
    assert hasattr(p, "win_streak")
    assert p.win_streak == 0

def test_mockplayer_has_alive_field():
    from v2.mock.engine_mock import MockPlayer
    p = MockPlayer()
    assert hasattr(p, "alive")
    assert p.alive is True

def test_mockplayer_has_copies_dict():
    from v2.mock.engine_mock import MockPlayer
    p = MockPlayer()
    assert hasattr(p, "copies")
    assert isinstance(p.copies, dict)

def test_mockplayer_has_stats_dict_with_required_keys():
    from v2.mock.engine_mock import MockPlayer
    p = MockPlayer()
    required = {"wins", "losses", "draws", "market_rolls", "evolutions", "win_streak_max"}
    assert required.issubset(set(p.stats.keys()))

def test_mockplayer_has_passive_buff_log():
    from v2.mock.engine_mock import MockPlayer
    p = MockPlayer()
    assert hasattr(p, "passive_buff_log")
    assert isinstance(p.passive_buff_log, list)

# ── Phase 3c item 29: MockGame yeni alanlar ──────────────────────────────

def test_mockgame_has_last_combat_results():
    game = MockGame()
    assert hasattr(game, "last_combat_results")
    assert isinstance(game.last_combat_results, list)

def test_buy_card_updates_copies():
    game = MockGame()
    game.initialize_deterministic_fixture()
    # Önce shop'u belirleyelim
    shop = game.get_shop_window(0)
    card_name = next((c for c in shop if c is not None), None)
    if card_name is None:
        pytest.skip("Dükkan boş — fixture sorunu")
    slot = shop.index(card_name)
    # Player'ın gold'unu yeterli yap
    game.players[0].gold = 50
    before = game.players[0].copies.get(card_name, 0)
    result = game.buy_card_from_slot(0, slot)
    assert result is True
    after = game.players[0].copies.get(card_name, 0)
    assert after == before + 1

def test_reroll_updates_market_rolls():
    game = MockGame()
    game.initialize_deterministic_fixture()
    before = game.players[0].stats.get("market_rolls", 0)
    game.reroll_market(0)
    after = game.players[0].stats.get("market_rolls", 0)
    assert after == before + 1
