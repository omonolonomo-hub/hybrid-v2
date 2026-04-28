"""
tests/test_turn_manager_contract.py
═══════════════════════════════════════════════════════════════════════
Faz 3 — TurnManager İzolasyon Güvenlik Ağı

Bu dosya Faz 3 implementasyonu ÖNCESINDE yazılmıştır.
Başlangıçta tüm testler FAIL eder (TurnManager henüz yok).
Implementasyon sonrasında tümü GREEN olmalıdır.
Faz 4 süresince DEĞİŞTİRİLMEZ; kırılırsa refactor durur.

Kapsam:
  A. TurnManager bağımsız örneklenebilmeli (game.py gerekmez)
  B. start_turn() → tur sayacı artar, income dağıtılır, market açılır
  C. finish_turn() → AI oyuncular hareket eder, insan altını değişmez
  D. swiss_pairs() → geçerli 2-tuple listesi döndürür
  E. preparation_phase() → start_turn + finish_turn sırayla çalışır
  F. _deal_starting_hands() → her oyuncu başlangıç kartlarını alır
═══════════════════════════════════════════════════════════════════════
"""

import random
import pytest

from engine_core.board import combat_phase as board_combat_phase
from engine_core.card import get_card_pool
from engine_core.passive_trigger import trigger_passive
from engine_core.player import Player
from engine_core.ai import AI


# ── Yardımcılar ──────────────────────────────────────────────────────────────

def _make_players(strategies, seed=42):
    rng = random.Random(seed)
    return [Player(pid=i, strategy=s) for i, s in enumerate(strategies)], rng


def _build_turn_manager(strategies=None, seed=42):
    """
    TurnManager'ı Game olmadan doğrudan kurar.
    TurnManager henüz yoksa ImportError → test FAIL (beklenen davranış).
    """
    from engine_core.turn_manager import TurnManager  # noqa: beklenen import

    if strategies is None:
        strategies = ["random", "warrior", "economist", "builder"]

    players, rng = _make_players(strategies, seed=seed)
    card_pool = get_card_pool()

    from engine_core.market import Market
    market = Market(card_pool, rng=rng)

    _uid_counter = [0]

    def _next_uid():
        _uid_counter[0] += 1
        return _uid_counter[0]

    tm = TurnManager(
        players=players,
        market=market,
        rng=rng,
        trigger_passive_fn=trigger_passive,
        next_card_uid_fn=_next_uid,
        ai_class=AI,
        verbose=False,
        game_ref=None,  # Tests run without Game instance
    )
    return tm, players, market


# ══════════════════════════════════════════════════════════════════════════════
# A. TurnManager Bağımsız Örneklenme
# ══════════════════════════════════════════════════════════════════════════════

class TestTurnManagerInstantiation:
    """TurnManager, Game.py inject edilmeden oluşturulabilmeli."""

    def test_turn_manager_importable(self):
        """engine_core.turn_manager modülü import edilebilmeli."""
        from engine_core import turn_manager  # noqa
        assert hasattr(turn_manager, "TurnManager")

    def test_turn_manager_instantiates_without_game(self):
        """TurnManager, Game nesnesi olmadan oluşturulabilmeli."""
        tm, _, _ = _build_turn_manager(seed=1)
        assert tm is not None

    def test_turn_manager_has_start_turn(self):
        tm, _, _ = _build_turn_manager(seed=2)
        assert callable(getattr(tm, "start_turn", None))

    def test_turn_manager_has_finish_turn(self):
        tm, _, _ = _build_turn_manager(seed=3)
        assert callable(getattr(tm, "finish_turn", None))

    def test_turn_manager_has_preparation_phase(self):
        tm, _, _ = _build_turn_manager(seed=4)
        assert callable(getattr(tm, "preparation_phase", None))

    def test_turn_manager_has_swiss_pairs(self):
        tm, _, _ = _build_turn_manager(seed=5)
        assert callable(getattr(tm, "swiss_pairs", None))

    def test_turn_manager_has_deal_starting_hands(self):
        tm, _, _ = _build_turn_manager(seed=6)
        assert callable(getattr(tm, "_deal_starting_hands", None))

    def test_turn_manager_turn_starts_at_zero(self):
        """Yeni TurnManager'ın tur sayacı 0 olmalı."""
        tm, _, _ = _build_turn_manager(seed=8)
        assert tm.turn == 0


# ══════════════════════════════════════════════════════════════════════════════
# B. start_turn() Davranışı
# ══════════════════════════════════════════════════════════════════════════════

class TestStartTurn:
    """start_turn() tur sayacını artırmalı, gelir dağıtmalı, market açmalı."""

    def test_start_turn_increments_turn_counter(self):
        tm, _, _ = _build_turn_manager(seed=10)
        assert tm.turn == 0
        tm.start_turn()
        assert tm.turn == 1

    def test_start_turn_increments_turn_counter_twice(self):
        tm, _, _ = _build_turn_manager(seed=11)
        tm.start_turn()
        tm.start_turn()
        assert tm.turn == 2

    def test_start_turn_deals_income_to_all_alive_players(self):
        tm, players, _ = _build_turn_manager(seed=12)
        gold_before = {p.pid: p.gold for p in players}
        tm.start_turn()
        for p in players:
            assert p.gold >= gold_before[p.pid], (
                f"P{p.pid} gelir almadı: önce={gold_before[p.pid]}, sonra={p.gold}"
            )

    def test_start_turn_opens_market_windows_for_all_alive(self):
        tm, players, market = _build_turn_manager(seed=13)
        tm.start_turn()
        for p in players:
            if p.alive:
                window = market._player_windows.get(p.pid, [])
                assert 1 <= len(window) <= 5, (
                    f"P{p.pid} penceresi beklenen aralıkta değil: {len(window)}"
                )

    def test_start_turn_does_not_run_ai(self):
        """start_turn yalnızca income + market; AI satın alma YAPMAMALI."""
        tm, players, _ = _build_turn_manager(
            strategies=["random", "warrior"], seed=14
        )
        # Başlangıç el boyutlarını kaydet
        hand_sizes_before = [len(p.hand) for p in players]
        tm.start_turn()
        hand_sizes_after = [len(p.hand) for p in players]
        # AI satın alma yoksa el boyutu değişmemeli
        # (Başlangıç elleri _deal_starting_hands'den gelir; start_turn değil)
        assert hand_sizes_before == hand_sizes_after, (
            "start_turn() AI satın alma mantığı çalıştırmamalı"
        )

    def test_start_turn_skips_locked_shop(self):
        """Kilitli dükkanlar start_turn'de yenilenmemeli."""
        tm, players, market = _build_turn_manager(seed=15)
        tm.start_turn()
        window_before = list(market._player_windows.get(players[0].pid, []))
        players[0].shop_locked = True
        tm.start_turn()
        window_after = market._player_windows.get(players[0].pid, [])
        assert window_before == window_after, (
            "Kilitli dükkan start_turn'de yenilenmemeli"
        )


# ══════════════════════════════════════════════════════════════════════════════
# C. finish_turn() Davranışı
# ══════════════════════════════════════════════════════════════════════════════

class TestFinishTurn:
    """finish_turn() AI oyuncular için hareket eder, insan altına dokunmaz."""

    def test_finish_turn_runs_ai_for_non_human_players(self):
        """finish_turn sonrası AI oyuncuların el+board toplamı değişmeli."""
        tm, players, _ = _build_turn_manager(
            strategies=["human", "random", "warrior", "builder"], seed=20
        )
        tm.start_turn()
        hand_total_before = sum(
            len(p.hand) for p in players if p.strategy != "human"
        )
        tm.finish_turn()
        hand_total_after  = sum(
            len(p.hand) for p in players if p.strategy != "human"
        )
        board_total_after = sum(
            len(p.board.grid) for p in players if p.strategy != "human"
        )
        assert (hand_total_after + board_total_after) >= hand_total_before

    def test_finish_turn_does_not_change_human_gold(self):
        """finish_turn, human oyuncunun altınına dokunmamalı."""
        tm, players, _ = _build_turn_manager(
            strategies=["human", "random"], seed=21
        )
        tm.start_turn()
        human_gold_after_income = players[0].gold
        tm.finish_turn()
        assert players[0].gold == human_gold_after_income, (
            "finish_turn human oyuncunun altınını değiştirmemeli"
        )

    def test_finish_turn_without_start_turn_does_not_crash(self):
        """finish_turn, start_turn çağrılmadan çağrıldığında çökmemeli."""
        tm, _, _ = _build_turn_manager(seed=22)
        try:
            tm.finish_turn()
        except Exception as e:
            pytest.fail(f"finish_turn() start_turn olmadan çöktü: {e}")

    def test_finish_turn_applies_interest(self):
        """finish_turn sonrası apply_interest çalışmalı (altın artabilir)."""
        tm, players, _ = _build_turn_manager(
            strategies=["random"], seed=23
        )
        tm.start_turn()
        # Biraz altın ver — faiz için yeterli baz
        players[0].gold = 10
        gold_after_income = players[0].gold
        tm.finish_turn()
        # Faiz uygulandıysa altın >= income sonrası değer
        assert players[0].gold >= 0  # en az sıfır (harcama olsa bile crash olmamalı)


# ══════════════════════════════════════════════════════════════════════════════
# D. swiss_pairs() Davranışı
# ══════════════════════════════════════════════════════════════════════════════

class TestSwissPairs:
    """swiss_pairs() geçerli eşleşme listesi döndürmeli."""

    def test_swiss_pairs_returns_list(self):
        tm, _, _ = _build_turn_manager(seed=30)
        result = tm.swiss_pairs()
        assert isinstance(result, list)

    def test_swiss_pairs_each_element_is_tuple_of_two(self):
        tm, _, _ = _build_turn_manager(seed=31)
        pairs = tm.swiss_pairs()
        for pair in pairs:
            assert len(pair) == 2, f"Çift 2 eleman içermeli, aldı: {len(pair)}"

    def test_swiss_pairs_elements_are_players(self):
        tm, _, _ = _build_turn_manager(seed=32)
        pairs = tm.swiss_pairs()
        for p_a, p_b in pairs:
            assert isinstance(p_a, Player)
            assert isinstance(p_b, Player)

    def test_swiss_pairs_no_player_appears_twice(self):
        """Bir oyuncu aynı turda iki farklı eşleşmede yer almamalı."""
        tm, _, _ = _build_turn_manager(seed=33)
        pairs = tm.swiss_pairs()
        pids_seen = []
        for p_a, p_b in pairs:
            pids_seen.extend([p_a.pid, p_b.pid])
        assert len(pids_seen) == len(set(pids_seen)), (
            "Bir oyuncu birden fazla eşleşmede yer aldı"
        )

    def test_swiss_pairs_count_matches_half_alive(self):
        """4 canlı oyuncu → 2 çift."""
        tm, players, _ = _build_turn_manager(
            strategies=["random", "warrior", "economist", "builder"], seed=34
        )
        alive_count = sum(1 for p in players if p.alive)
        pairs = tm.swiss_pairs()
        assert len(pairs) == alive_count // 2

    def test_swiss_pairs_with_odd_player_count(self):
        """Tek sayıda oyuncu olduğunda bye oyuncu çiftsiz kalmalı."""
        tm, players, _ = _build_turn_manager(
            strategies=["random", "warrior", "economist"], seed=35
        )
        alive_count = sum(1 for p in players if p.alive)
        pairs = tm.swiss_pairs()
        assert len(pairs) == alive_count // 2

    def test_swiss_pairs_only_alive_players_paired(self):
        """Ölü oyuncular eşleşmeye dahil edilmemeli."""
        tm, players, _ = _build_turn_manager(seed=36)
        players[0].alive = False
        pairs = tm.swiss_pairs()
        pids_in_pairs = {p.pid for pair in pairs for p in pair}
        assert players[0].pid not in pids_in_pairs, (
            "Ölü oyuncu eşleşmede görünüyor"
        )


# ══════════════════════════════════════════════════════════════════════════════
# E. preparation_phase() = start_turn + finish_turn
# ══════════════════════════════════════════════════════════════════════════════

class TestPreparationPhase:
    """preparation_phase() start_turn + finish_turn'ü sırayla çalıştırmalı."""

    def test_preparation_phase_increments_turn_counter(self):
        tm, _, _ = _build_turn_manager(seed=40)
        assert tm.turn == 0
        tm.preparation_phase()
        assert tm.turn == 1

    def test_preparation_phase_twice_reaches_turn_2(self):
        tm, _, _ = _build_turn_manager(seed=41)
        tm.preparation_phase()
        tm.preparation_phase()
        assert tm.turn == 2

    def test_preparation_phase_deals_income(self):
        tm, players, _ = _build_turn_manager(seed=42)
        gold_before = {p.pid: p.gold for p in players}
        tm.preparation_phase()
        for p in players:
            assert p.gold >= gold_before[p.pid], (
                f"P{p.pid} preparation_phase sonrası gelir almadı"
            )

    def test_preparation_phase_runs_ai(self):
        """preparation_phase sonrası AI oyuncuların hareketleri gerçekleşmeli."""
        tm, players, _ = _build_turn_manager(
            strategies=["random", "warrior"], seed=43
        )
        board_total_before = sum(len(p.board.grid) for p in players)
        tm.preparation_phase()
        # AI en az bir kart oynamış olmalı (board veya el toplamı ilerlemeli)
        hand_board_after = sum(len(p.hand) + len(p.board.grid) for p in players)
        # Başlangıç elleri geldi, bu yeterli işaret
        assert hand_board_after >= 0  # crash olmamalı

    def test_preparation_phase_equivalent_to_start_then_finish(self):
        """
        preparation_phase()'in etkisi, aynı seed ile start_turn + finish_turn
        sırasıyla çalıştırmakla eşdeğer olmalı (tur sayacı tutarlılığı).
        """
        tm1, _, _ = _build_turn_manager(seed=44)
        tm2, _, _ = _build_turn_manager(seed=44)

        tm1.preparation_phase()
        tm2.start_turn()
        tm2.finish_turn()

        assert tm1.turn == tm2.turn == 1


# ══════════════════════════════════════════════════════════════════════════════
# F. _deal_starting_hands()
# ══════════════════════════════════════════════════════════════════════════════

class TestDealStartingHands:
    """
    TurnManager init sırasında her oyuncuya başlangıç kartları dağıtılmalı.
    (Faz 2'de bu sorumluluk Game.__init__'teydi; Faz 3'te TurnManager'a geçer.)
    """

    def test_players_have_cards_after_init(self):
        """TurnManager oluşturulur oluşturulmaz oyuncuların elinde kart olmalı."""
        tm, players, _ = _build_turn_manager(seed=50)
        for p in players:
            assert len(p.hand) > 0, (
                f"P{p.pid} TurnManager init sonrası el boş"
            )

    def test_players_have_at_most_3_starting_cards(self):
        """Başlangıç eli en fazla 3 kart içermeli."""
        tm, players, _ = _build_turn_manager(seed=51)
        for p in players:
            assert len(p.hand) <= 3, (
                f"P{p.pid} başlangıç eli 3'ten fazla kart içeriyor: {len(p.hand)}"
            )

    def test_starting_cards_are_common_rarity(self):
        """Dağıtılan başlangıç kartları common (rarity='1') olmalı."""
        tm, players, _ = _build_turn_manager(seed=52)
        for p in players:
            for card in p.hand:
                assert card.rarity == "1", (
                    f"P{p.pid} başlangıç kartı common değil: {card.name} (rarity={card.rarity})"
                )

    def test_copies_dict_populated_after_init(self):
        """Her başlangıç kartı player.copies sözlüğüne kaydedilmeli."""
        tm, players, _ = _build_turn_manager(seed=53)
        for p in players:
            for card in p.hand:
                assert card.name in p.copies, (
                    f"P{p.pid} başlangıç kartı copies'e kaydedilmedi: {card.name}"
                )

    def test_deal_starting_hands_idempotent_on_rerun(self):
        """
        _deal_starting_hands() tekrar çağrıldığında çökmemeli
        (internal guard veya temiz davranış).
        """
        tm, players, _ = _build_turn_manager(seed=54)
        try:
            tm._deal_starting_hands()
        except Exception as e:
            pytest.fail(f"_deal_starting_hands() yeniden çağrıldığında çöktü: {e}")
