"""
tests/test_combat_engine_contract.py
═══════════════════════════════════════════════════════════════════════
Faz 2 — CombatEngine İzolasyon Güvenlik Ağı

Bu dosya Faz 2 implementasyonu ÖNCESINDE yazılmıştır.
Başlangıçta tüm testler FAIL eder (CombatEngine henüz yok).
Implementasyon sonrasında tümü GREEN olmalıdır.
Faz 3–4 süresince DEĞİŞTİRİLMEZ; kırılırsa refactor durur.

Kapsam:
  A. CombatEngine bağımsız örneklenebilmeli (game.py gerekmez)
  B. run_combat() → mevcut last_combat_results formatıyla birebir uyumlu
  C. _return_cards_to_pool() → kartlar pool'a geri döner, board/hand temizlenir
  D. game.combat_phase() artık inline değil, CombatEngine'e delegate eder
  E. game.last_combat_results CombatEngine çıktısıyla güncellenir
═══════════════════════════════════════════════════════════════════════
"""

import random
import pytest

from engine_core.board import Board, combat_phase as board_combat_phase
from engine_core.card import Card, get_card_pool
from engine_core.game import Game
from engine_core.passive_trigger import trigger_passive
from engine_core.player import Player


# ── Yardımcılar ──────────────────────────────────────────────────────────────

REQUIRED_RESULT_KEYS = {
    "pid_a", "pid_b", "pts_a", "pts_b",
    "kill_a", "kill_b", "combo_a", "combo_b",
    "synergy_a", "synergy_b", "draws",
    "winner_pid", "dmg",
    "hp_before_a", "hp_before_b", "hp_after_a", "hp_after_b",
}


def _make_card(name: str, power: int = 1) -> Card:
    stats = {
        "Power": power, "Durability": power, "Size": power, "Speed": power,
        "Meaning": power, "Secret": power,
    }
    return Card(name, "Fixture", "1", stats)


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


def _build_minimal_combat_engine(game: Game):
    """
    CombatEngine'i game.py'den bağımsız kurar.
    Import burada yapılır; sınıf henüz yoksa ImportError → test FAIL (beklenen).
    """
    from engine_core.combat_engine import CombatEngine  # noqa: beklenen import
    return CombatEngine(
        players=game.players,
        market=game.market,
        rng=game.rng,
        trigger_passive_fn=trigger_passive,
        combat_phase_fn=board_combat_phase,
        next_card_uid_fn=game.next_card_uid,
        verbose=False,
    )


# ══════════════════════════════════════════════════════════════════════════════
# A. CombatEngine Bağımsız Örneklenme
# ══════════════════════════════════════════════════════════════════════════════

class TestCombatEngineInstantiation:
    """CombatEngine, game.py import etmeden oluşturulabilmeli."""

    def test_combat_engine_importable(self):
        """engine_core.combat_engine modülü import edilebilmeli."""
        from engine_core import combat_engine  # noqa
        assert hasattr(combat_engine, "CombatEngine")

    def test_combat_engine_instantiates_without_game(self):
        """CombatEngine, Game nesnesi inject edilmeden oluşturulabilmeli."""
        game = _build_game(seed=1)
        ce = _build_minimal_combat_engine(game)
        assert ce is not None

    def test_combat_engine_has_run_combat(self):
        game = _build_game(seed=2)
        ce = _build_minimal_combat_engine(game)
        assert callable(getattr(ce, "run_combat", None))

    def test_combat_engine_has_return_cards_to_pool(self):
        game = _build_game(seed=3)
        ce = _build_minimal_combat_engine(game)
        assert callable(getattr(ce, "_return_cards_to_pool", None))


# ══════════════════════════════════════════════════════════════════════════════
# B. run_combat() Çıktı Formatı
# ══════════════════════════════════════════════════════════════════════════════

class TestRunCombatOutputFormat:
    """run_combat() last_combat_results ile birebir uyumlu dict listesi döndürmeli."""

    def _pairs_and_engine(self, seed: int):
        game = _build_game(seed=seed)
        game.start_turn()
        game.finish_turn()
        pairs = game.swiss_pairs()
        ce = _build_minimal_combat_engine(game)
        return game, ce, pairs

    def test_run_combat_returns_list(self):
        game, ce, pairs = self._pairs_and_engine(seed=10)
        result = ce.run_combat(pairs)
        assert isinstance(result, list)

    def test_run_combat_result_count_matches_pair_count(self):
        game, ce, pairs = self._pairs_and_engine(seed=11)
        result = ce.run_combat(pairs)
        assert len(result) == len(pairs)

    def test_run_combat_each_result_has_required_keys(self):
        game, ce, pairs = self._pairs_and_engine(seed=12)
        results = ce.run_combat(pairs)
        for r in results:
            missing = REQUIRED_RESULT_KEYS - set(r.keys())
            assert not missing, f"Eksik anahtarlar: {missing}"

    def test_run_combat_score_decomposition_invariant(self):
        """pts_x == kill_x + combo_x + synergy_x her zaman doğru olmalı."""
        game, ce, pairs = self._pairs_and_engine(seed=13)
        results = ce.run_combat(pairs)
        for r in results:
            assert r["pts_a"] == r["kill_a"] + r["combo_a"] + r["synergy_a"]
            assert r["pts_b"] == r["kill_b"] + r["combo_b"] + r["synergy_b"]

    def test_run_combat_winner_pid_is_valid(self):
        game, ce, pairs = self._pairs_and_engine(seed=14)
        results = ce.run_combat(pairs)
        for r in results:
            assert r["winner_pid"] in {-1, r["pid_a"], r["pid_b"]}

    def test_run_combat_hp_snapshots_consistent_with_winner(self):
        """Kazananın HP'si değişmemeli, kaybedenin HP'si tam dmg kadar düşmeli."""
        game, ce, pairs = self._pairs_and_engine(seed=15)
        results = ce.run_combat(pairs)
        for r in results:
            if r["winner_pid"] == -1:
                assert r["dmg"] == 0
            elif r["winner_pid"] == r["pid_a"]:
                assert r["hp_after_a"] == r["hp_before_a"]
                assert r["hp_after_b"] == r["hp_before_b"] - r["dmg"]
            else:
                assert r["hp_after_b"] == r["hp_before_b"]
                assert r["hp_after_a"] == r["hp_before_a"] - r["dmg"]

    def test_run_combat_empty_pairs_returns_empty_list(self):
        game = _build_game(seed=16)
        ce = _build_minimal_combat_engine(game)
        assert ce.run_combat([]) == []


# ══════════════════════════════════════════════════════════════════════════════
# C. _return_cards_to_pool()
# ══════════════════════════════════════════════════════════════════════════════

class TestReturnCardsToPool:
    """_return_cards_to_pool board/hand temizlenmeli, kartlar pool'a dönmeli."""

    def _setup(self, seed: int = 50):
        game = _build_game(seed=seed, n=2)
        game.start_turn()
        ce = _build_minimal_combat_engine(game)
        return game, ce

    def test_board_cleared_after_return(self):
        game, ce = self._setup(seed=50)
        player = game.players[0]
        card = _make_card("Cannon", power=3)
        card.uid = game.next_card_uid()
        player.board.place((0, 0), card)
        assert len(player.board.grid) > 0

        ce._return_cards_to_pool(player)
        assert player.board.grid == {}

    def test_hand_cleared_after_return(self):
        game, ce = self._setup(seed=51)
        player = game.players[0]
        card = _make_card("Sword", power=2)
        card.uid = game.next_card_uid()
        player.hand.append(card)

        ce._return_cards_to_pool(player)
        assert player.hand == []

    def test_copies_cleared_after_return(self):
        game, ce = self._setup(seed=52)
        player = game.players[0]
        player.copies["TestCard"] = 2

        ce._return_cards_to_pool(player)
        assert player.copies == {}

    def test_pool_copy_count_nonnegative_after_return(self):
        game, ce = self._setup(seed=53)
        player = game.players[0]
        card = _make_card("Dragon", power=5)
        card.uid = game.next_card_uid()
        game.market.pool_copies["Dragon"] = 0
        player.board.place((0, 0), card)

        ce._return_cards_to_pool(player)
        assert game.market.pool_copies.get("Dragon", 0) >= 0

    def test_pool_count_increases_after_return(self):
        """Board'a konan bilinen bir kart pool'a dönünce count artmalı."""
        pool = get_card_pool()
        if not pool:
            pytest.skip("Boş card pool")
        game, ce = self._setup(seed=54)
        player = game.players[0]
        # Pool'da var olan bir kartı al
        real_card = pool[0]
        game.market.pool_copies[real_card.name] = 0
        cloned = real_card.clone()
        cloned.uid = game.next_card_uid()
        player.board.grid.clear()
        player.board.place((0, 0), cloned)

        ce._return_cards_to_pool(player)
        assert game.market.pool_copies[real_card.name] >= 1


# ══════════════════════════════════════════════════════════════════════════════
# D. game.combat_phase() Delegation
# ══════════════════════════════════════════════════════════════════════════════

class TestGameDelegatesToCombatEngine:
    """
    game.combat_phase() artık inline logic içermemeli;
    CombatEngine.run_combat()'a delegate etmeli.
    """

    def test_game_has_combat_engine_attribute(self):
        """Faz 2 sonrası game._combat_engine attribute'u olmalı."""
        game = _build_game(seed=20)
        assert hasattr(game, "_combat_engine"), (
            "game._combat_engine attribute yok — game_factory veya __init__ güncellenmedi"
        )

    def test_game_combat_engine_is_combat_engine_instance(self):
        from engine_core.combat_engine import CombatEngine
        game = _build_game(seed=21)
        assert isinstance(game._combat_engine, CombatEngine)

    def test_combat_phase_calls_run_combat(self):
        """
        game.combat_phase() çağrıldığında CombatEngine.run_combat()'ın
        gerçekten tetiklendiğini doğrula (call count üstünden).
        """
        game = _build_game(seed=22)
        game.start_turn()
        game.finish_turn()

        call_count = {"n": 0}
        original_run = game._combat_engine.run_combat

        def spy_run_combat(pairs):
            call_count["n"] += 1
            return original_run(pairs)

        game._combat_engine.run_combat = spy_run_combat
        game.combat_phase()
        assert call_count["n"] == 1, (
            "combat_phase(), run_combat()'ı çağırmadı — delegation eksik"
        )

    def test_combat_phase_without_inline_logic(self):
        """
        game.combat_phase() source'unda inline HP/damage hesabı bulunmamalı.
        (run_combat mock'lanırsa game.py HP'lere dokunmamalı.)
        """
        game = _build_game(seed=23)
        game.start_turn()
        game.finish_turn()

        # run_combat'ı boş liste döndüren mock ile değiştir
        game._combat_engine.run_combat = lambda pairs: []

        hp_before = {p.pid: p.hp for p in game.players}
        game.combat_phase()
        hp_after = {p.pid: p.hp for p in game.players}

        # HP hiç değişmemeli — damage logic artık game.py içinde değil
        assert hp_before == hp_after, (
            "game.combat_phase() hala inline damage uyguluyor — CombatEngine'e tam delegate edilmedi"
        )


# ══════════════════════════════════════════════════════════════════════════════
# E. game.last_combat_results CombatEngine çıktısıyla güncellenir
# ══════════════════════════════════════════════════════════════════════════════

class TestLastCombatResultsSync:
    """game.last_combat_results, CombatEngine.run_combat() döndürdüğü listeyle set edilmeli."""

    def test_last_combat_results_set_from_run_combat(self):
        game = _build_game(seed=30)
        game.start_turn()
        game.finish_turn()

        sentinel = [{"pid_a": 99, "pid_b": 88, "sentinel": True}]
        game._combat_engine.run_combat = lambda pairs: sentinel

        game.combat_phase()
        assert game.last_combat_results is sentinel, (
            "game.last_combat_results run_combat() dönüş değeriyle set edilmedi"
        )

    def test_last_combat_results_reset_each_call(self):
        game = _build_game(seed=31)
        game.start_turn()
        game.finish_turn()
        game.combat_phase()
        ref = game.last_combat_results

        game.start_turn()
        game.finish_turn()
        game.combat_phase()

        assert game.last_combat_results is not ref, (
            "last_combat_results nesnesi yenilenmedi — eski referans hala geçerli"
        )

    def test_full_cycle_last_results_have_correct_format(self):
        """Gerçek CombatEngine inject edildiğinde tam format beklenir."""
        game = _build_game(seed=32)
        game.start_turn()
        game.finish_turn()
        game.combat_phase()
        for r in game.last_combat_results:
            missing = REQUIRED_RESULT_KEYS - set(r.keys())
            assert not missing, f"Eksik anahtarlar: {missing}"
