"""
Hafta 3 Faz 2 Testleri — H3-3: combat_resolver.py tek kaynak doğrulama.

combat_phase kodu artık engine_core/combat_resolver.py'de tek kaynak.
board.py ve combat_engine.py bu modüle delegate ediyor.
"""

import pytest
from unittest.mock import MagicMock, patch

from engine_core.board import Board
from engine_core.card import Card
from engine_core.combat_resolver import resolve_combat_phase


def _make_card(name: str, rarity: str = "1", edges=None):
    """Test için Card oluştur."""
    card = Card(
        name=name,
        category="Test",
        rarity=rarity,
        stats={"Power": 5, "Durability": 5, "Size": 5, "Speed": 5,
               "Meaning": 5, "Secret": 5, "Intelligence": 5, "Trace": 5,
               "Gravity": 5, "Harmony": 5, "Spread": 5, "Prestige": 5},
    )
    if edges is not None:
        card._edges = edges
    return card


class TestCombatResolverSingleSource:
    """combat_resolver.resolve_combat_phase() tek yetkili implementasyon."""

    def test_empty_boards_return_zero(self):
        board_a = Board()
        board_b = Board()
        result = resolve_combat_phase(board_a, board_b, {}, {})
        assert result == (0, 0, 0)

    def test_no_shared_coords_return_zero(self):
        board_a = Board()
        board_b = Board()
        card_a = _make_card("CardA")
        card_b = _make_card("CardB")
        board_a.place((0, 0), card_a)
        board_b.place((1, -1), card_b)
        result = resolve_combat_phase(board_a, board_b, {}, {})
        assert result == (0, 0, 0)

    def test_shared_coord_produces_combat(self):
        board_a = Board()
        board_b = Board()
        card_a = _make_card("CardA")
        card_b = _make_card("CardB")
        board_a.place((0, 0), card_a)
        board_b.place((0, 0), card_b)
        kill_a, kill_b, draws = resolve_combat_phase(board_a, board_b, {}, {})
        # İki kart da aynı stats'e sahip → berabere
        assert draws == 1
        assert kill_a == 0
        assert kill_b == 0

    def test_trigger_passive_fn_default_import(self):
        """trigger_passive_fn=None → combat_resolver kendi import eder."""
        board_a = Board()
        board_b = Board()
        result = resolve_combat_phase(board_a, board_b, {}, {}, trigger_passive_fn=None)
        assert result == (0, 0, 0)

    def test_trigger_passive_fn_custom(self):
        """Özel trigger_passive_fn kullanılıyor."""
        board_a = Board()
        board_b = Board()
        card_a = _make_card("CardA")
        card_b = _make_card("CardB")
        board_a.place((0, 0), card_a)
        board_b.place((0, 0), card_b)

        custom_trigger = MagicMock(return_value=0)
        resolve_combat_phase(
            board_a, board_b, {}, {},
            trigger_passive_fn=custom_trigger,
        )
        # Aynı stats → berabere, trigger çağrılmaz
        custom_trigger.assert_not_called()

    def test_board_combat_phase_delegates_to_resolver(self):
        """board.combat_phase() → combat_resolver.resolve_combat_phase() delegate."""
        from engine_core.board import combat_phase as board_combat_phase
        board_a = Board()
        board_b = Board()
        result = board_combat_phase(board_a, board_b, {}, {})
        assert result == (0, 0, 0)

    def test_combat_engine_resolve_delegates_to_resolver(self):
        """CombatEngine._resolve_combat_phase() → combat_resolver.resolve_combat_phase() delegate."""
        from engine_core.combat_engine import CombatEngine
        engine = CombatEngine(
            players=[], market=MagicMock(), rng=MagicMock(),
            trigger_passive_fn=MagicMock(return_value=0),
            combat_phase_fn=None,
        )
        board_a = Board()
        board_b = Board()
        result = engine._resolve_combat_phase(board_a, board_b, {}, {})
        assert result == (0, 0, 0)

    def test_ctx_defaults_to_empty_dict(self):
        """ctx=None → {} olarak başlatılır."""
        board_a = Board()
        board_b = Board()
        # Herhangi bir hata olmadan çalışmalı
        result = resolve_combat_phase(board_a, board_b, {}, {}, ctx=None)
        assert result == (0, 0, 0)


class TestCombatResolverElimination:
    """Kart eliminasyonu combat_resolver üzerinden doğru çalışıyor mu?"""

    def test_elimination_delegates_correctly(self):
        """Eliminasyon combat_resolver üzerinden CombatEngine'e doğru delege olur."""
        # Full game simülasyonu ile doğrula — combat_engine testlerinde zaten kapsanıyor.
        # Burada sadece combat_resolver import'unun çalıştığını doğrula.
        from engine_core.combat_resolver import resolve_combat_phase as fn
        assert callable(fn)

    def test_board_combat_phase_import_works(self):
        """board.combat_phase import hala çalışıyor."""
        from engine_core.board import combat_phase
        assert callable(combat_phase)

    def test_combat_engine_still_runs_full_combat(self):
        """CombatEngine.run_combat() combat_resolver üzerinden çalışıyor."""
        from engine_core.game import Game
        from engine_core.player import Player

        # 2 oyunculu minimal oyun
        p1 = Player(pid=0, strategy="random")
        p2 = Player(pid=1, strategy="random")
        game = Game(players=[p1, p2])
        game.start_turn()
        # CombatEngine.run_combat() combat_resolver üzerinden çalışır
        pairs = game.swiss_pairs()
        results = game.combat_phase(pairs)
        # Hiçbir hata fırlatılmadı → delegasyon çalışıyor
        assert True
