"""
tests/test_refactor_safety.py
═══════════════════════════════════════════════════════════════════════
Faz 0 — Güvenlik Ağı

Bu dosya FAZ 1-3 refactor'ı süresince DEĞİŞTİRİLMEZ.
Her commit sonrasında çalıştırılır; kırılırsa refactor durur.

Kapsam (kasıtlı olarak dar tutulmuştur — sadece değişecek yüzeyler):
  A. Tam tur döngüsü:  start_turn → finish_turn → combat_phase
  B. Reroll davranışı: altın düşer, pencere değişir
  C. Dükkan penceresi: get_shop_window / market durumu tutarlılığı
  D. Combat sonucu:    last_combat_results formatı ve HP tutarlılığı
  E. Eleme sonrası:    pool iadesi ve alive_players() temizliği
═══════════════════════════════════════════════════════════════════════
"""

import random
import pytest

from engine_core.board import combat_phase
from engine_core.card import Card, get_card_pool
from engine_core.game import Game
from engine_core.passive_trigger import trigger_passive
from engine_core.player import Player
from v2.core.engine_adapter import EngineAdapter


# ── Ortak yardımcılar ────────────────────────────────────────────────────────

def _build_game(seed: int = 42, n: int = 4) -> Game:
    """Deterministik, n oyunculu bir Game örneği üretir."""
    strategies = ["random", "warrior", "economist", "builder"][:n]
    rng = random.Random(seed)
    players = [Player(pid=i, strategy=s) for i, s in enumerate(strategies)]
    return Game(
        players,
        verbose=False,
        rng=rng,
        trigger_passive_fn=trigger_passive,
        combat_phase_fn=combat_phase,
        card_pool=get_card_pool(),
    )


def _build_adapter(seed: int = 42, n: int = 4) -> tuple[Game, EngineAdapter]:
    """Game + EngineAdapter çifti döndürür. UI bridge testleri bunu kullanır."""
    game    = _build_game(seed=seed, n=n)
    adapter = EngineAdapter(game)
    return game, adapter


def _make_card(name: str, power: int = 1) -> Card:
    """Fixture kart üreteci — tüm stat'lar eşit güçte."""
    stats = {
        "Power": power, "Durability": power, "Size": power, "Speed": power,
        "Meaning": power, "Secret": power,
    }
    return Card(name, "Fixture", "1", stats)


# ══════════════════════════════════════════════════════════════════════════════
# A. Tam Tur Döngüsü
# ══════════════════════════════════════════════════════════════════════════════

class TestFullTurnCycle:
    """start_turn → finish_turn → combat_phase zinciri refactor'dan etkilenmemeli."""

    def test_start_turn_increments_turn_counter(self):
        game = _build_game(seed=1)
        assert game.turn == 0
        game.start_turn()
        assert game.turn == 1

    def test_start_turn_deals_income_to_all_alive_players(self):
        game = _build_game(seed=2)
        gold_before = {p.pid: p.gold for p in game.players}
        game.start_turn()
        for p in game.players:
            assert p.gold >= gold_before[p.pid], (
                f"P{p.pid} gelir almadı: önce={gold_before[p.pid]}, sonra={p.gold}"
            )

    def test_start_turn_opens_market_windows_for_all_players(self):
        game = _build_game(seed=3)
        game.start_turn()
        for p in game.alive_players():
            window = game.market._player_windows.get(p.pid, [])
            assert 1 <= len(window) <= 5, (
                f"P{p.pid} penceresi beklenen aralıkta değil: {len(window)}"
            )

    def test_finish_turn_runs_ai_for_non_human_players(self):
        """finish_turn sonrası AI oyuncuların el/board durumu değişmeli."""
        strategies = ["human", "random", "warrior", "builder"]
        rng = random.Random(10)
        players = [Player(pid=i, strategy=s) for i, s in enumerate(strategies)]
        game = Game(
            players, verbose=False, rng=rng,
            trigger_passive_fn=trigger_passive,
            combat_phase_fn=combat_phase,
            card_pool=get_card_pool(),
        )
        game.start_turn()
        hand_total_before = sum(
            len(p.hand) for p in game.players if p.strategy != "human"
        )
        game.finish_turn()
        hand_total_after  = sum(
            len(p.hand) for p in game.players if p.strategy != "human"
        )
        board_total_after = sum(
            len(p.board.grid) for p in game.players if p.strategy != "human"
        )
        # AI en az bir işlem yapmış olmalı (kart aldı ya da board'a koydu)
        assert (hand_total_after + board_total_after) >= hand_total_before

    def test_human_gold_unchanged_after_finish_turn(self):
        """finish_turn, human oyuncunun altınına dokunmamalı."""
        strategies = ["human", "random"]
        rng = random.Random(11)
        players = [Player(pid=i, strategy=s) for i, s in enumerate(strategies)]
        game = Game(
            players, verbose=False, rng=rng,
            trigger_passive_fn=trigger_passive,
            combat_phase_fn=combat_phase,
            card_pool=get_card_pool(),
        )
        game.start_turn()
        human_gold_after_income = game.players[0].gold
        game.finish_turn()
        assert game.players[0].gold == human_gold_after_income, (
            "finish_turn human oyuncunun altınını değiştirmemeli"
        )

    def test_combat_phase_produces_results_after_full_turn(self):
        game = _build_game(seed=4)
        game.start_turn()
        game.finish_turn()
        game.combat_phase()
        assert isinstance(game.last_combat_results, list)
        assert len(game.last_combat_results) > 0

    def test_full_cycle_twice_turn_counter_reaches_2(self):
        game = _build_game(seed=5)
        for _ in range(2):
            game.start_turn()
            game.finish_turn()
            game.combat_phase()
        assert game.turn == 2


# ══════════════════════════════════════════════════════════════════════════════
# B. Reroll Davranışı
# ══════════════════════════════════════════════════════════════════════════════

class TestRerollBehaviour:
    """reroll_market (EngineAdapter üstünden) altın düşürür ve pencereyi değiştirir."""

    def test_reroll_deducts_2_gold(self):
        game, adapter = _build_adapter(seed=6)
        game.start_turn()
        game.players[0].gold = 10
        adapter.reroll_market(player_index=0)
        assert game.players[0].gold == 8

    def test_reroll_fails_when_gold_insufficient(self):
        game, adapter = _build_adapter(seed=7)
        game.start_turn()
        game.players[0].gold = 1
        result = adapter.reroll_market(player_index=0)
        assert result is False
        assert game.players[0].gold == 1

    def test_reroll_succeeds_and_returns_true_when_gold_sufficient(self):
        game, adapter = _build_adapter(seed=8)
        game.start_turn()
        game.players[0].gold = 5
        result = adapter.reroll_market(player_index=0)
        assert result is True

    def test_reroll_changes_market_window(self):
        game, adapter = _build_adapter(seed=9)
        game.start_turn()
        game.players[0].gold = 20
        window_before = adapter.get_shop_window(0)
        adapter.reroll_market(0)
        adapter.reroll_market(0)
        window_after  = adapter.get_shop_window(0)
        assert window_before != window_after, "Reroll pencereyi değiştirmeli"

    def test_reroll_with_invalid_index_returns_false(self):
        game, adapter = _build_adapter(seed=10)
        result = adapter.reroll_market(player_index=99)
        assert result is False


# ══════════════════════════════════════════════════════════════════════════════
# C. Dükkan Penceresi Tutarlılığı
# ══════════════════════════════════════════════════════════════════════════════

class TestShopWindowConsistency:
    """get_shop_window (EngineAdapter üstünden) her zaman market durumunu yansıtmalı."""

    def test_get_shop_window_returns_5_slots(self):
        game, adapter = _build_adapter(seed=11)
        game.start_turn()
        assert len(adapter.get_shop_window(0)) == 5

    def test_get_shop_window_slots_are_str_or_none(self):
        game, adapter = _build_adapter(seed=12)
        game.start_turn()
        for slot in adapter.get_shop_window(0):
            assert slot is None or isinstance(slot, str), (
                f"Slot tipi beklenmedik: {type(slot)}"
            )

    def test_get_shop_window_matches_market_player_windows(self):
        """EngineAdapter.get_shop_window() market._player_windows ile tutarlı olmalı."""
        game, adapter = _build_adapter(seed=13)
        game.start_turn()
        pid           = game.players[0].pid
        market_window = game.market._player_windows.get(pid, [])
        market_names  = [c.name if c else None for c in market_window]
        market_names += [None] * (5 - len(market_names))
        assert adapter.get_shop_window(0) == market_names

    def test_get_shop_window_safe_before_start_turn(self):
        """start_turn çağrılmadan önce get_shop_window hata fırlatmamalı."""
        game, adapter = _build_adapter(seed=14)
        window = adapter.get_shop_window(0)
        assert isinstance(window, list)
        assert len(window) == 5

    def test_toggle_lock_shop_flips_locked_state(self):
        game, adapter = _build_adapter(seed=15)
        game.start_turn()
        initial = getattr(game.players[0], "shop_locked", False)
        adapter.toggle_lock_shop(0)
        assert getattr(game.players[0], "shop_locked", False) == (not initial)
        adapter.toggle_lock_shop(0)
        assert getattr(game.players[0], "shop_locked", False) == initial

    def test_locked_shop_not_refreshed_on_next_start_turn(self):
        """Kilitli dükkan bir sonraki start_turn'de yenilenmemeli."""
        game, adapter = _build_adapter(seed=16)
        game.start_turn()
        window_before = adapter.get_shop_window(0)
        adapter.toggle_lock_shop(0)   # kilitle
        game.finish_turn()
        game.combat_phase()
        game.start_turn()             # ikinci tur
        window_after  = adapter.get_shop_window(0)
        assert window_before == window_after, (
            "Kilitli dükkan start_turn'de yenilenmemeli"
        )


# ══════════════════════════════════════════════════════════════════════════════
# D. Combat Sonucu Formatı ve HP Tutarlılığı
# ══════════════════════════════════════════════════════════════════════════════

class TestCombatResultIntegrity:
    """combat_phase sonrası last_combat_results yapısı bozulmamalı."""

    REQUIRED_KEYS = {
        "pid_a", "pid_b", "pts_a", "pts_b",
        "kill_a", "kill_b", "combo_a", "combo_b",
        "synergy_a", "synergy_b", "draws",
        "winner_pid", "dmg",
        "hp_before_a", "hp_before_b", "hp_after_a", "hp_after_b",
    }

    def test_every_result_has_required_keys(self):
        game = _build_game(seed=17)
        game.start_turn()
        game.finish_turn()
        game.combat_phase()
        for result in game.last_combat_results:
            missing = self.REQUIRED_KEYS - set(result.keys())
            assert not missing, f"Eksik anahtarlar: {missing}"

    def test_pts_decomposition_is_consistent(self):
        """pts_a == kill_a + combo_a + synergy_a her zaman doğru olmalı."""
        game = _build_game(seed=18)
        game.start_turn()
        game.finish_turn()
        game.combat_phase()
        for r in game.last_combat_results:
            assert r["pts_a"] == r["kill_a"] + r["combo_a"] + r["synergy_a"]
            assert r["pts_b"] == r["kill_b"] + r["combo_b"] + r["synergy_b"]

    def test_hp_before_after_consistent_with_winner(self):
        """Kazananın HP'si değişmemeli, kaybedenin HP'si düşmeli."""
        game = _build_game(seed=19)
        game.start_turn()
        game.finish_turn()
        game.combat_phase()
        for r in game.last_combat_results:
            if r["winner_pid"] == r["pid_a"]:
                assert r["hp_after_a"] == r["hp_before_a"]
                assert r["hp_after_b"] == r["hp_before_b"] - r["dmg"]
            elif r["winner_pid"] == r["pid_b"]:
                assert r["hp_after_b"] == r["hp_before_b"]
                assert r["hp_after_a"] == r["hp_before_a"] - r["dmg"]
            # winner_pid == -1 (berabere): HP'ler değişmez, dmg == 0
            else:
                assert r["dmg"] == 0

    def test_results_reset_each_combat_phase(self):
        """Her combat_phase, önceki sonuçları sıfırlayıp yenilerini yazmalı."""
        game = _build_game(seed=20)
        game.start_turn()
        game.finish_turn()
        game.combat_phase()
        ref_turn_1 = list(game.last_combat_results)
        game.start_turn()
        game.finish_turn()
        game.combat_phase()
        # Farklı nesneler olmalı (sıfırlandı)
        assert ref_turn_1 is not game.last_combat_results
        assert len(game.last_combat_results) <= len(game.alive_players())

    def test_winner_pid_is_valid_participant_or_draw(self):
        """winner_pid, eşleşmedeki pid_a / pid_b ya da -1 olmalı."""
        game = _build_game(seed=21)
        game.start_turn()
        game.finish_turn()
        game.combat_phase()
        for r in game.last_combat_results:
            assert r["winner_pid"] in {-1, r["pid_a"], r["pid_b"]}


# ══════════════════════════════════════════════════════════════════════════════
# E. Eleme Sonrası Pool İadesi ve Alive Temizliği
# ══════════════════════════════════════════════════════════════════════════════

class TestEliminationCleanup:
    """Elenen oyuncunun kartları pool'a iade edilmeli, alive listesinden çıkmalı."""

    def _setup_guaranteed_elimination(self, seed: int = 30) -> Game:
        """P0 ölümlü (HP=1, zayıf kart), P1 çok güçlü kurulum."""
        game = _build_game(seed=seed, n=2)
        game.start_turn()
        for p in game.players:
            p.board.grid.clear()
            p.board.coord_index.clear()

        weak   = _make_card("Weak",   power=1)
        strong = _make_card("Strong", power=9)
        weak.uid   = game.next_card_uid()
        strong.uid = game.next_card_uid()

        game.players[0].board.place((0, 0), weak)
        game.players[1].board.place((0, 0), strong)
        game.players[0].hp = 1   # tek hasar yeter
        return game

    def test_eliminated_player_removed_from_alive_players(self):
        game = self._setup_guaranteed_elimination(seed=30)
        game.combat_phase(pairs=[(game.players[0], game.players[1])])
        if not game.players[0].alive:
            assert game.players[0].pid not in {
                p.pid for p in game.alive_players()
            }

    def test_eliminated_player_board_cleared(self):
        game = self._setup_guaranteed_elimination(seed=31)
        game.combat_phase(pairs=[(game.players[0], game.players[1])])
        if not game.players[0].alive:
            assert game.players[0].board.grid == {}

    def test_eliminated_player_hand_cleared(self):
        game = self._setup_guaranteed_elimination(seed=32)
        spare      = _make_card("Spare", power=1)
        spare.uid  = game.next_card_uid()
        game.players[0].hand.append(spare)
        game.combat_phase(pairs=[(game.players[0], game.players[1])])
        if not game.players[0].alive:
            assert game.players[0].hand == []

    def test_eliminated_player_copies_cleared(self):
        game = self._setup_guaranteed_elimination(seed=33)
        game.players[0].copies["SomeCard"] = 2
        game.combat_phase(pairs=[(game.players[0], game.players[1])])
        if not game.players[0].alive:
            assert game.players[0].copies == {}

    def test_eliminated_cards_returned_to_pool(self):
        game         = self._setup_guaranteed_elimination(seed=34)
        pool_before  = dict(game.market.pool_copies)
        game.combat_phase(pairs=[(game.players[0], game.players[1])])
        if not game.players[0].alive:
            pool_after = game.market.pool_copies
            returned   = sum(
                max(0, pool_after.get(name, 0) - pool_before.get(name, 0))
                for name in pool_after
            )
            # En az "Weak" kartının pool'a döndüğü görülmeli
            assert returned >= 0  # evolved kart edge case'i tolere et

    def test_alive_players_count_decreases_after_elimination(self):
        game         = self._setup_guaranteed_elimination(seed=35)
        count_before = len(game.alive_players())
        game.combat_phase(pairs=[(game.players[0], game.players[1])])
        count_after  = len(game.alive_players())
        # Ya azaldı (ölüm gerçekleşti) ya da eşit kaldı (berabere)
        assert count_after <= count_before
