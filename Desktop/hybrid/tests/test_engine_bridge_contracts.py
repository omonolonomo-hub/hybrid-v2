"""
tests/test_engine_bridge_contracts.py
═══════════════════════════════════════════════════════════════════════
Faz 3 — Game ↔ TurnManager Köprü Sözleşmesi

Bu dosya Faz 3 implementasyonu ÖNCESINDE yazılmıştır.
Başlangıçta tüm testler FAIL eder (_turn_manager henüz yok).
Implementasyon sonrasında tümü GREEN olmalıdır.
Faz 4 süresince DEĞİŞTİRİLMEZ; kırılırsa refactor durur.

Kapsam:
  A. Game, _turn_manager attribute'una sahip olmalı
  B. Game.start_turn()  → TurnManager.start_turn()'e delegate etmeli
  C. Game.finish_turn() → TurnManager.finish_turn()'e delegate etmeli
  D. Game.combat_phase() → swiss_pairs() TurnManager'dan alınmalı
  E. Game._turn_manager.turn ile game.turn senkronize olmalı
  F. game_factory.py, TurnManager inject etmeli (opsiyonel smoke)
═══════════════════════════════════════════════════════════════════════
"""

import random
import pytest

from engine_core.board import combat_phase as board_combat_phase
from engine_core.card import get_card_pool
from engine_core.game import Game
from engine_core.passive_trigger import trigger_passive
from engine_core.player import Player


# ── Yardımcılar ──────────────────────────────────────────────────────────────

def _build_game(seed: int = 42, n: int = 4) -> Game:
    strategies = ["random", "warrior", "economist", "builder"][:n]
    rng = random.Random(seed)
    players = [Player(pid=i, strategy=s) for i, s in enumerate(strategies)]
    return Game(
        players, verbose=False, rng=rng,
        trigger_passive_fn=trigger_passive,
        combat_phase_fn=board_combat_phase,
        card_pool=get_card_pool(),
    )


# ══════════════════════════════════════════════════════════════════════════════
# A. Game._turn_manager Varlığı
# ══════════════════════════════════════════════════════════════════════════════

class TestGameHasTurnManager:
    """Faz 3 sonrası game._turn_manager attribute'u olmalı."""

    def test_game_has_turn_manager_attribute(self):
        game = _build_game(seed=1)
        assert hasattr(game, "_turn_manager"), (
            "game._turn_manager attribute yok — "
            "Game.__init__ veya game_factory güncellenmedi"
        )

    def test_game_turn_manager_is_correct_type(self):
        from engine_core.turn_manager import TurnManager
        game = _build_game(seed=2)
        assert isinstance(game._turn_manager, TurnManager), (
            f"game._turn_manager TurnManager değil: {type(game._turn_manager)}"
        )

    def test_game_still_has_combat_engine_attribute(self):
        """_turn_manager eklenmesi _combat_engine'i kaldırmamalı."""
        from engine_core.combat_engine import CombatEngine
        game = _build_game(seed=3)
        assert hasattr(game, "_combat_engine")
        assert isinstance(game._combat_engine, CombatEngine)

    def test_turn_manager_players_shared_with_game(self):
        """TurnManager ve Game aynı players listesini paylaşmalı."""
        game = _build_game(seed=4)
        assert game._turn_manager._players is game.players, (
            "TurnManager kendi players kopyasını kullanıyor; "
            "game.players ile aynı nesne olmalı"
        )

    def test_turn_manager_market_shared_with_game(self):
        """TurnManager ve Game aynı market nesnesini paylaşmalı."""
        game = _build_game(seed=5)
        assert game._turn_manager._market is game.market, (
            "TurnManager ayrı market kullanıyor; game.market ile aynı olmalı"
        )


# ══════════════════════════════════════════════════════════════════════════════
# B. Game.start_turn() Delegation
# ══════════════════════════════════════════════════════════════════════════════

class TestStartTurnDelegation:
    """Game.start_turn() artık TurnManager.start_turn()'e delegate etmeli."""

    def test_game_start_turn_calls_turn_manager_start_turn(self):
        """
        game.start_turn() çağrıldığında TurnManager.start_turn()'ün
        tetiklendiğini spy ile doğrula.
        """
        game = _build_game(seed=10)
        call_count = {"n": 0}
        original = game._turn_manager.start_turn

        def spy_start():
            call_count["n"] += 1
            return original()

        game._turn_manager.start_turn = spy_start
        game.start_turn()
        assert call_count["n"] == 1, (
            "game.start_turn() TurnManager.start_turn()'ı çağırmadı"
        )

    def test_game_turn_counter_after_start_turn_via_turn_manager(self):
        """game.start_turn() sonrası game.turn TurnManager'dan senkronize olmalı."""
        game = _build_game(seed=11)
        game.start_turn()
        # game.turn ile turn_manager.turn tutarlı olmalı
        assert game.turn == game._turn_manager.turn == 1

    def test_game_start_turn_no_inline_turn_increment(self):
        """
        game.start_turn() kendi turn artışını yapmamalı;
        TurnManager bunu yönetmeli.
        Spy turn_manager.start_turn'ü no-op'a çevirdiğimizde turn artmamalı.
        """
        game = _build_game(seed=12)
        game._turn_manager.start_turn = lambda: None  # no-op
        turn_before = game.turn
        game.start_turn()
        # turn_manager no-op → game.turn değişmemeli
        assert game.turn == turn_before, (
            "game.start_turn() TurnManager'ı bypass ederek turn artırıyor — "
            "inline logic taşınmadı"
        )

    def test_game_income_distributed_via_start_turn(self):
        """game.start_turn() sonrası oyuncuların altınları artmış olmalı."""
        game = _build_game(seed=13)
        gold_before = {p.pid: p.gold for p in game.players}
        game.start_turn()
        for p in game.players:
            assert p.gold >= gold_before[p.pid]


# ══════════════════════════════════════════════════════════════════════════════
# C. Game.finish_turn() Delegation
# ══════════════════════════════════════════════════════════════════════════════

class TestFinishTurnDelegation:
    """Game.finish_turn() artık TurnManager.finish_turn()'e delegate etmeli."""

    def test_game_finish_turn_calls_turn_manager_finish_turn(self):
        game = _build_game(seed=20)
        call_count = {"n": 0}
        original = game._turn_manager.finish_turn

        def spy_finish():
            call_count["n"] += 1
            return original()

        game._turn_manager.finish_turn = spy_finish
        game.start_turn()
        game.finish_turn()
        assert call_count["n"] == 1, (
            "game.finish_turn() TurnManager.finish_turn()'ı çağırmadı"
        )

    def test_game_finish_turn_no_inline_ai_logic(self):
        """
        game.finish_turn(), TurnManager no-op olduğunda oyuncuların
        durumuna dokunmamalı (AI çağrısı inline kalmadıysa).
        """
        game = _build_game(seed=21)
        game.start_turn()
        game._turn_manager.finish_turn = lambda: None  # no-op

        hand_sizes_before = {p.pid: len(p.hand) for p in game.players}
        board_sizes_before = {p.pid: len(p.board.grid) for p in game.players}

        game.finish_turn()

        hand_sizes_after = {p.pid: len(p.hand) for p in game.players}
        board_sizes_after = {p.pid: len(p.board.grid) for p in game.players}

        assert hand_sizes_before == hand_sizes_after, (
            "game.finish_turn() TurnManager'ı bypass ederek AI çalıştırıyor"
        )
        assert board_sizes_before == board_sizes_after, (
            "game.finish_turn() TurnManager'ı bypass ederek board değiştiriyor"
        )

    def test_human_gold_unchanged_after_game_finish_turn(self):
        """game.finish_turn() delegasyon sonrası human altını korunmalı."""
        strategies = ["human", "random"]
        rng = random.Random(22)
        players = [Player(pid=i, strategy=s) for i, s in enumerate(strategies)]
        game = Game(
            players, verbose=False, rng=rng,
            trigger_passive_fn=trigger_passive,
            combat_phase_fn=board_combat_phase,
            card_pool=get_card_pool(),
        )
        game.start_turn()
        human_gold = game.players[0].gold
        game.finish_turn()
        assert game.players[0].gold == human_gold


# ══════════════════════════════════════════════════════════════════════════════
# D. Game.combat_phase() → swiss_pairs() TurnManager'dan
# ══════════════════════════════════════════════════════════════════════════════

class TestCombatPhasePairsFromTurnManager:
    """
    game.combat_phase() pairs=None çağrıldığında swiss_pairs()
    TurnManager'dan alınmalı (game.swiss_pairs() veya inline çağrı değil).
    """

    def test_combat_phase_calls_turn_manager_swiss_pairs(self):
        game = _build_game(seed=30)
        game.start_turn()
        game.finish_turn()

        call_count = {"n": 0}
        original = game._turn_manager.swiss_pairs

        def spy_swiss_pairs():
            call_count["n"] += 1
            return original()

        game._turn_manager.swiss_pairs = spy_swiss_pairs
        game.combat_phase()
        assert call_count["n"] == 1, (
            "game.combat_phase() TurnManager.swiss_pairs()'ı çağırmadı"
        )

    def test_combat_phase_respects_explicit_pairs(self):
        """pairs= argümanı verildiğinde TurnManager.swiss_pairs() çağrılmamalı."""
        game = _build_game(seed=31)
        game.start_turn()
        game.finish_turn()

        call_count = {"n": 0}

        def spy_swiss_pairs():
            call_count["n"] += 1
            return []

        game._turn_manager.swiss_pairs = spy_swiss_pairs
        # Açık çift ver — swiss_pairs atlanmalı
        game.combat_phase(pairs=[(game.players[0], game.players[1])])
        assert call_count["n"] == 0, (
            "Açık pairs verildiğinde TurnManager.swiss_pairs() çağrılmamalı"
        )

    def test_combat_phase_still_delegates_to_combat_engine(self):
        """swiss_pairs TurnManager'dan gelse de run_combat hala CombatEngine'de."""
        game = _build_game(seed=32)
        game.start_turn()
        game.finish_turn()

        engine_call_count = {"n": 0}
        original_run = game._combat_engine.run_combat

        def spy_run_combat(pairs):
            engine_call_count["n"] += 1
            return original_run(pairs)

        game._combat_engine.run_combat = spy_run_combat
        game.combat_phase()
        assert engine_call_count["n"] == 1, (
            "game.combat_phase() CombatEngine.run_combat()'ı çağırmadı"
        )

    def test_game_swiss_pairs_method_removed_or_delegates(self):
        """
        Faz 3 sonrası game.swiss_pairs() ya kaldırılmış ya da
        TurnManager'a delegate ediyor olmalı.
        Eğer hala game'de varsa TurnManager'ı çağırmalı.
        """
        game = _build_game(seed=33)
        if not hasattr(game, "swiss_pairs"):
            # Kaldırıldı — kabul edilebilir
            return

        # Hala varsa TurnManager'a delegate etmeli
        call_count = {"n": 0}
        original = game._turn_manager.swiss_pairs

        def spy():
            call_count["n"] += 1
            return original()

        game._turn_manager.swiss_pairs = spy
        game.swiss_pairs()
        assert call_count["n"] == 1, (
            "game.swiss_pairs() TurnManager'a delegate etmiyor"
        )


# ══════════════════════════════════════════════════════════════════════════════
# E. game.turn ↔ TurnManager.turn Senkronizasyonu
# ══════════════════════════════════════════════════════════════════════════════

class TestTurnCounterSync:
    """
    game.turn ile game._turn_manager.turn her zaman tutarlı olmalı.
    Bu iki sayaç tek bir kaynak tarafından yönetilmeli.
    """

    def test_turn_sync_after_one_start_turn(self):
        game = _build_game(seed=40)
        game.start_turn()
        assert game.turn == game._turn_manager.turn

    def test_turn_sync_after_full_cycle(self):
        game = _build_game(seed=41)
        game.start_turn()
        game.finish_turn()
        game.combat_phase()
        assert game.turn == game._turn_manager.turn

    def test_turn_sync_after_two_full_cycles(self):
        game = _build_game(seed=42)
        for _ in range(2):
            game.start_turn()
            game.finish_turn()
            game.combat_phase()
        assert game.turn == game._turn_manager.turn == 2

    def test_turn_is_single_source_of_truth(self):
        """
        Faz 3 sonrası game.turn, TurnManager.turn'ün bir alias'ı ya da
        TurnManager üstünden yönetilen tek değer olmalı.
        Her iki yerden erişim aynı sayıyı vermeli.
        """
        game = _build_game(seed=43)
        game.start_turn()
        game.start_turn()
        tm_turn = game._turn_manager.turn
        game_turn = game.turn
        assert tm_turn == game_turn == 2, (
            f"Tur sayacı uyuşmazlığı: game.turn={game_turn}, "
            f"turn_manager.turn={tm_turn}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# F. game_factory.py Smoke Testi
# ══════════════════════════════════════════════════════════════════════════════

class TestGameFactoryInjectsTurnManager:
    """
    game_factory.build_game() üretilen Game nesnesine _turn_manager inject etmeli.
    """

    def test_build_game_produces_game_with_turn_manager(self):
        try:
            from engine_core.game_factory import build_game
        except ImportError:
            pytest.skip("game_factory.py bulunamadı — opsiyonel smoke testi")

        from engine_core.turn_manager import TurnManager
        game = build_game()
        assert hasattr(game, "_turn_manager"), (
            "build_game() üretilen game._turn_manager yok"
        )
        assert isinstance(game._turn_manager, TurnManager)

    def test_build_game_turn_manager_and_combat_engine_share_players(self):
        """
        game_factory üretilen game'de TurnManager ve CombatEngine
        aynı players listesini paylaşmalı.
        """
        try:
            from engine_core.game_factory import build_game
        except ImportError:
            pytest.skip("game_factory.py bulunamadı — opsiyonel smoke testi")

        game = build_game()
        if not hasattr(game, "_turn_manager"):
            pytest.skip("_turn_manager henüz inject edilmedi")

        assert game._turn_manager._players is game._combat_engine._players, (
            "TurnManager ve CombatEngine farklı players listeleri kullanıyor"
        )

    def test_full_cycle_via_factory_game(self):
        """build_game() ile üretilen game tam bir tur döngüsünü tamamlamalı."""
        try:
            from engine_core.game_factory import build_game
        except ImportError:
            pytest.skip("game_factory.py bulunamadı")

        game = build_game()
        game.start_turn()
        game.finish_turn()
        game.combat_phase()
        assert game.turn == 1
        assert isinstance(game.last_combat_results, list)
