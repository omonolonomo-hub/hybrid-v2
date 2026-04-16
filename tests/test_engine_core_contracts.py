"""
test_engine_core_contracts.py
=============================================================
Phase 5 Ön Koşul TDD Paketi — engine_core AAA sözleşme testleri

Kapsam:
  A. calculate_damage() formül doğrulaması
  B. Market → GameState.get_shop() köprüsü
  C. swiss_pairs() adil eşleşme davranışı  
  D. income() + apply_interest() → get_gold() senkronu
  E. Eleme → get_endgame_stats() sıralaması
  F. game.run() sonsuz döngü koruması (50 tur guard)
  G. LobbyPanel render payloadu player kimliği köprüsü
=============================================================
"""

import random
import pytest

from engine_core.board import Board, calculate_damage, find_combos, calculate_group_synergy_bonus
from engine_core.card import get_card_pool
from engine_core.constants import STARTING_HP, BASE_INCOME, KILL_PTS
from engine_core.game import Game
from engine_core.game_factory import build_game
from engine_core.passive_trigger import trigger_passive
from engine_core.player import Player
from engine_core.board import combat_phase
from v2.core.game_state import GameState


# ─── Ortak yardımcı ────────────────────────────────────────────────────────

def _build_seeded_game(n=4, seed=42, strategies=None):
    rng = random.Random(seed)
    if strategies is None:
        strategies = ["random", "builder", "economist", "warrior"][:n]
    players = [Player(pid=i, strategy=s) for i, s in enumerate(strategies)]
    return Game(
        players, verbose=False, rng=rng,
        trigger_passive_fn=trigger_passive,
        combat_phase_fn=combat_phase,
        card_pool=get_card_pool(),
    )


@pytest.fixture
def gs_real():
    GameState._instance = None
    gs = GameState.get()
    game = _build_seeded_game()
    gs.hook_engine(game)
    yield gs, game
    GameState._instance = None


# ─── A. calculate_damage() Formül Doğrulaması ─────────────────────────────


class TestCalculateDamage:

    def test_damage_formula_base_plus_alive_div2_plus_rarity(self):
        """
        DAMAGE = max(1, |Wpts - Lpts| + floor(alive/2) + rarity//2) * turn_mult
        Tur 16+ için tur çarpanı 1.0'dır.
        """
        board = Board()
        # Board boş → alive=0, rarity=0
        dmg = calculate_damage(winner_pts=10, loser_pts=3, winner_board=board, turn=20)
        # base = |10-3| = 7, alive=0//2=0, rarity=0, raw=max(1,7)=7, mult=1.0
        assert dmg == 7

    def test_damage_minimum_is_always_1(self):
        """Berabere senaryosunda (dmg=0 hesaplanmadan önce) min 1 hasar gelir."""
        board = Board()
        # pts eşit → orijinal game.py'de dmg hesaplanmaz; ama calculate_damage'i doğrudan test edelim
        dmg = calculate_damage(winner_pts=0, loser_pts=0, winner_board=board, turn=20)
        assert dmg >= 1

    def test_damage_halved_in_early_turns(self):
        """Tur 1-5 → hasar 0.50x çarpanla ölçeklenir ve tur 1-10 hard cap 15."""
        board = Board()
        # raw_damage = 20, turn=3 → mult=0.5 → scaled=10, cap=min(10,15)=10
        dmg_early = calculate_damage(winner_pts=25, loser_pts=5, winner_board=board, turn=3)
        dmg_late  = calculate_damage(winner_pts=25, loser_pts=5, winner_board=board, turn=20)
        assert dmg_early < dmg_late

    def test_damage_hard_cap_15_for_turns_1_to_10(self):
        """Tur 10 ve öncesinde hasar en fazla 15 olabilir."""
        board = Board()
        # Çok büyük fark: raw=1000+
        dmg = calculate_damage(winner_pts=1000, loser_pts=0, winner_board=board, turn=5)
        assert dmg <= 15

    def test_damage_no_cap_after_turn_10(self):
        """Tur 11+'dan itibaren hard cap kalkar."""
        board = Board()
        # raw=1000 → turn=20 → mult=1.0 → scaled=1000
        dmg = calculate_damage(winner_pts=1000, loser_pts=0, winner_board=board, turn=20)
        assert dmg > 15


# ─── B. Market → GameState.get_shop() köprüsü ────────────────────────────


class TestMarketBridge:

    def test_get_shop_returns_5_slots_before_preparation(self, gs_real):
        """
        preparation_phase çağrısından önce dükkan penceresi 5 slot döndürmeli.
        MockGame'e bağlı olmayan gerçek motor ile test.
        """
        gs, game = gs_real
        shop = gs.get_shop(0)
        assert isinstance(shop, list)
        assert len(shop) == 5

    def test_get_shop_contents_are_card_names_or_none(self, gs_real):
        """Dükkan slotları kart adı (str) veya None olmalı."""
        gs, game = gs_real
        shop = gs.get_shop(0)
        for slot in shop:
            assert slot is None or isinstance(slot, str)

    def test_get_shop_changes_after_preparation_phase(self, gs_real):
        """Hazır basınca (preparation_phase) dükkan yenilenir, içerik değişebilir."""
        gs, game = gs_real
        shop_before = gs.get_shop(0)
        gs.commit_human_turn()
        shop_after = gs.get_shop(0)
        # Her iki sonuç da 5 elemanlı liste
        assert len(shop_before) == 5
        assert len(shop_after) == 5


# ─── C. swiss_pairs() Eşleşme Davranışı ──────────────────────────────────


class TestSwissPairs:

    def test_swiss_pairs_covers_all_alive_players(self):
        """Her canlı oyuncu en fazla 1 eşleşmede yer almalı."""
        game = _build_seeded_game(n=4)
        pairs = game.swiss_pairs()
        flat = [p.pid for pair in pairs for p in pair]
        assert len(flat) == len(set(flat)), "Oyuncu birden fazla eşleşmede görünmemeli"

    def test_swiss_pairs_only_includes_alive_players(self):
        """Ölü oyuncular eşleşmeye dahil edilmemeli."""
        game = _build_seeded_game(n=4)
        game.players[0].alive = False
        game.players[0].hp    = 0
        pairs = game.swiss_pairs()
        alive_pids = {p.pid for p in game.alive_players()}
        pair_pids  = {p.pid for pair in pairs for p in pair}
        assert pair_pids.issubset(alive_pids)
        assert 0 not in pair_pids

    def test_swiss_pairs_with_odd_player_count_skips_one(self):
        """Tek sayıda oyuncu varsa biri BYE alır (eşleşmesiz kalır)."""
        game = _build_seeded_game(n=3)
        pairs = game.swiss_pairs()
        # 3 oyuncu → 1 çift
        assert len(pairs) == 1
        covered = {p.pid for pair in pairs for p in pair}
        assert len(covered) == 2

    def test_swiss_pairs_result_is_deterministic_with_fixed_rng(self):
        """Aynı seed ile oluşturulan iki motor aynı eşleşmeyi vermeli."""
        game1 = _build_seeded_game(seed=999)
        game2 = _build_seeded_game(seed=999)
        pairs1 = [(p1.pid, p2.pid) for p1, p2 in game1.swiss_pairs()]
        pairs2 = [(p1.pid, p2.pid) for p1, p2 in game2.swiss_pairs()]
        assert pairs1 == pairs2


# ─── D. income() + apply_interest() → get_gold() Senkronu ────────────────


class TestGoldSync:

    def test_get_gold_reflects_engine_after_income(self, gs_real):
        """
        preparation_phase sonrası player.gold engine ile UI'dan eşit görünmeli.
        """
        gs, game = gs_real
        gs.commit_human_turn()
        for p in game.players:
            assert gs.get_gold(p.pid) == p.gold

    def test_income_gives_base_income_each_turn(self):
        """Her turda BASE_INCOME kadar altın kazanılmalı (streak/bailout hariç)."""
        p = Player(pid=0, strategy="random")
        gold_before = p.gold
        p.income()
        # Kazanç en az BASE_INCOME olmalı
        assert p.gold >= gold_before + BASE_INCOME

    def test_economist_gets_boosted_interest(self):
        """Ekonomist stratejisi faiz çarpanı (1.5x) almalı."""
        eco = Player(pid=0, strategy="economist")
        norm = Player(pid=1, strategy="random")
        # Her ikisine 50 altın ver
        eco.gold  = 50
        norm.gold = 50
        eco.apply_interest()
        norm.apply_interest()
        assert eco.gold > norm.gold, "Ekonomist daha fazla faiz almalı"


# ─── E. Eleme → get_endgame_stats() Sıralaması ───────────────────────────


class TestEndgameStatsSorting:

    def test_endgame_stats_puts_alive_players_first(self, gs_real):
        """Hayatta olan oyuncular ölü olanlardan önce sıralanmalı."""
        gs, game = gs_real
        game.players[2].alive = False
        game.players[2].hp    = 0
        game.players[3].alive = False
        game.players[3].hp    = 0

        stats = gs.get_endgame_stats()
        # İlk 2 entry alive olmalı
        assert stats[0]["alive"] is True
        assert stats[1]["alive"] is True

    def test_endgame_stats_dead_players_have_rank_greater_than_alive(self, gs_real):
        """Ölü oyuncuların rank'ı canlılardan yüksek olmalı."""
        gs, game = gs_real
        game.players[0].hp    = 100
        game.players[0].alive = True
        game.players[1].hp    = 0
        game.players[1].alive = False

        stats = gs.get_endgame_stats()
        alive_ranks = [s["rank"] for s in stats if s["alive"]]
        dead_ranks  = [s["rank"] for s in stats if not s["alive"]]

        if alive_ranks and dead_ranks:
            assert max(alive_ranks) < min(dead_ranks), \
                "Hiçbir canlının rank'ı ölüden yüksek olmamalı"

    def test_endgame_stats_includes_all_players(self, gs_real):
        """get_endgame_stats tüm oyuncuları döndürmeli."""
        gs, game = gs_real
        stats = gs.get_endgame_stats()
        assert len(stats) == len(game.players)


# ─── F. game.run() Sonsuz Döngü Koruması ─────────────────────────────────


class TestRunLoopGuard:

    def test_run_finishes_within_50_turns(self):
        """
        game.run() 50 tur guard ile sonlanmalı; hiçbir zaman sonsuz döngüye girmemeli.
        """
        # 2 oyunculuyla hızlı oyun
        game = _build_seeded_game(n=2, seed=7)
        winner = game.run()
        assert winner is not None
        assert game.turn <= 50

    def test_run_returns_player_with_highest_hp_alive(self):
        """run() sonunda dönen oyuncu canlı olmalı ya da en yüksek HP'ye sahip olmalı."""
        game = _build_seeded_game(n=2, seed=13)
        winner = game.run()
        alive = [p for p in game.players if p.alive]
        if alive:
            assert winner in alive
        else:
            # Tüm oyuncular öldüyse, en yüksek HP'li kazanır
            best = max(game.players, key=lambda p: p.hp)
            assert winner.pid == best.pid


# ─── G. LobbyPanel Render Payload — Kimlik Köprüsü ───────────────────────


class TestLobbyRenderPayloadBridge:

    def test_get_display_name_returns_p_pid_format(self, gs_real):
        """
        get_display_name(idx) → 'P{pid}' formatı döndürmeli.
        Gerçek engine player objesinin .name field'ı yok, sadece .pid var.
        """
        gs, game = gs_real
        for i, player in enumerate(game.players):
            label = gs.get_display_name(i)
            assert label == f"P{player.pid}", \
                f"Beklenen 'P{player.pid}', alınan '{label}'"

    def test_get_strategy_matches_engine_strategy(self, gs_real):
        """get_strategy(idx) motordaki player.strategy ile birebir eşleşmeli."""
        gs, game = gs_real
        for i, player in enumerate(game.players):
            assert gs.get_strategy(i) == player.strategy

    def test_lobby_payload_uses_pid_based_name_not_dot_name(self, gs_real):
        """
        Render pipeline, player'ın .name attribute'una bakmamalı.
        GameState.get_display_name() üzerinden pid bazlı label kullanmalı.
        Bu test, 'test_render_passes_live_lobby_payload_from_game_state'
        testinin düzeltilmesi gerektiğini belgeler.
        """
        gs, game = gs_real
        # Gerçek Player'da .name yok — bu AttributeError üretmemeli
        for i in range(len(game.players)):
            label = gs.get_display_name(i)
            assert isinstance(label, str)
            assert label.startswith("P")
