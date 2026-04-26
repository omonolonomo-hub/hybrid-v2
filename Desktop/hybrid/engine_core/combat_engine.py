"""
engine_core/combat_engine.py
═══════════════════════════════════════════════════════════════════════
Faz 2 — CombatEngine Ayrımı

game.py'den ayrıştırılan combat mantığı. Sorumlulukları:
  • run_combat(pairs)         — tur için tüm eşleşmeleri çözer
  • _return_cards_to_pool()  — elenen oyuncunun kartlarını pool'a iade eder
  • _clear_transient_board_state() — combat öncesi/sonrası kart durumu temizleme

game.py bu sınıfı oluşturur ve combat_phase()'de run_combat()'ı çağırır.
TurnManager (Faz 3) inject edilene kadar self.turn, Game tarafından her
combat_phase() öncesinde senkronize edilir.
"""

import warnings
from typing import Callable, List, Optional

from engine_core.combo_detector import find_combos
from engine_core.combat_resolver import resolve_combat_phase as _resolve_combat_phase_fn
from engine_core.damage_calculator import calculate_damage
from engine_core.synergy import compute_board_synergy as calculate_group_synergy_bonus
from engine_core.constants import KILL_PTS
from engine_core.board_utils import iter_board_cards, clear_transient_board_state


class CombatEngine:
    def __init__(
        self,
        players,
        market,
        rng,
        trigger_passive_fn: Optional[Callable],
        combat_phase_fn: Optional[Callable],
        next_card_uid_fn: Optional[Callable] = None,
        verbose: bool = False,
    ):
        self._players        = players
        self._market         = market
        self._rng            = rng
        self._trigger_passive = trigger_passive_fn
        self._combat_phase_fn = combat_phase_fn
        self._next_card_uid_fn = next_card_uid_fn
        self._verbose        = verbose
        self._log_buf: List[str] = []

        # Game.combat_phase() bu değeri run_combat() çağrısından önce senkronize eder
        self.turn: int = 0

    # ── Logging ───────────────────────────────────────────────────────────────

    def _log(self, msg: str) -> None:
        if self._verbose:
            print(msg)
        self._log_buf.append(msg)

    # ── Board state helpers ───────────────────────────────────────────────────

    @staticmethod
    def _iter_board_cards(players):
        """Backward-compat — delegates to board_utils.iter_board_cards()."""
        warnings.warn(
            "_iter_board_cards is deprecated; use board_utils.iter_board_cards() directly.",
            DeprecationWarning, stacklevel=2
        )
        return iter_board_cards(players)

    def _clear_transient_board_state(
        self,
        players,
        *,
        current_turn: int,
        clear_combat_meta: bool,
    ) -> None:
        """Backward-compat — delegates to board_utils.clear_transient_board_state()."""
        warnings.warn(
            "_clear_transient_board_state is deprecated; use board_utils.clear_transient_board_state() directly.",
            DeprecationWarning, stacklevel=2
        )
        clear_transient_board_state(players, current_turn=current_turn, clear_combat_meta=clear_combat_meta)

    # ── Combat phase resolution (moved from board.py — P1-1 Phase 3) ──────────

    def _resolve_combat_phase(self, board_a, board_b,
                              combo_bonus_a, combo_bonus_b,
                              player_a=None, player_b=None, ctx=None):
        """
        Resolve combat at every overlapping coordinate.
        Returns: (kill_pts_a, kill_pts_b, draw_count)

        Delegates to combat_resolver.resolve_combat_phase() — tek kaynak.
        """
        return _resolve_combat_phase_fn(
            board_a, board_b, combo_bonus_a, combo_bonus_b,
            player_a, player_b, ctx,
            trigger_passive_fn=self._trigger_passive,
        )

    # ── Card pool management ──────────────────────────────────────────────────

    def _return_cards_to_pool(self, player) -> None:
        """Return all board and hand cards of an eliminated player back to
        the shared market pool.

        Aynı garantiler game.py versiyonuyla korunur:
        - Evolved kartlar 1 base kopya olarak iade edilir
        - pool_copies asla 3'ü geçmez
        - board.grid, player.hand, player.copies, player.copy_turns temizlenir
        """
        _pool_copies = self._market.pool_copies

        def _return_one(card) -> None:
            name = card.name
            base = name[8:] if name.startswith("Evolved ") else name
            if base in _pool_copies:
                _pool_copies[base] = min(_pool_copies[base] + 1, 3)

        for card in list(player.board.grid.values()):
            _return_one(card)
        player.board.grid.clear()
        if hasattr(player.board, "has_catalyst"):
            player.board.has_catalyst = False

        for card in list(player.hand):
            _return_one(card)
        player.hand.clear()

        player.copies.clear()
        player.copy_turns.clear()

    # ── Ana combat çözücü ─────────────────────────────────────────────────────

    def run_combat(self, pairs) -> List[dict]:
        """Verilen tüm eşleşmeleri çözer.

        Returns:
            game.last_combat_results formatıyla uyumlu dict listesi.
            Her dict aynı 17 anahtarı içerir.
        """
        if not pairs:
            return []

        _log             = self._log
        _verbose         = self._verbose
        _turn            = self.turn
        _KILL_PTS        = KILL_PTS
        _trigger_passive = self._trigger_passive
        _combat_phase_fn = self._combat_phase_fn

        # ActionLog entry
        game_ref = getattr(self._players[0], "game", None)
        if game_ref and hasattr(game_ref, "action_log"):
            game_ref.action_log.record("combat_start", {"turn": _turn, "pair_count": len(pairs)}, turn=_turn)

        results = []

        for p_a, p_b in pairs:
            _log(
                f"\n  P{p_a.pid}({p_a.strategy}, {p_a.hp}HP)"
                f" vs P{p_b.pid}({p_b.strategy}, {p_b.hp}HP)"
            )

            # Passive trigger'lar game referansına ihtiyaç duyabilir;
            # player.game üstünden sağlanır (Game.__init__'te set edilir).
            game_ref = getattr(p_a, "game", None)
            
            # H3-2: Support independent context without game ref
            _ctx = {
                "turn": _turn, 
                "game": game_ref,
                "market": self._market,
                "market_window": getattr(p_a, "market", []) # Compatibility
            }

            board_a = p_a.board
            board_b = p_b.board
            self._clear_transient_board_state(
                [p_a, p_b], current_turn=_turn, clear_combat_meta=True
            )

            if _trigger_passive:
                for card in tuple(board_a.grid.values()):
                    _trigger_passive(card, "pre_combat", p_a, p_b, _ctx, verbose=_verbose)
                for card in tuple(board_b.grid.values()):
                    _trigger_passive(card, "pre_combat", p_b, p_a, _ctx, verbose=_verbose)

            combo_pts_a, bonus_a = find_combos(board_a)
            combo_pts_b, bonus_b = find_combos(board_b)
            if board_a.has_catalyst:
                combo_pts_a *= 2
            if board_b.has_catalyst:
                combo_pts_b *= 2

            synergy_pts_a = calculate_group_synergy_bonus(board_a)
            synergy_pts_b = calculate_group_synergy_bonus(board_b)

            # Use injected combat_phase_fn if provided, otherwise use internal method
            if _combat_phase_fn:
                kill_a, kill_b, draws = _combat_phase_fn(
                    board_a, board_b, bonus_a, bonus_b, p_a, p_b, _ctx
                )
            else:
                kill_a, kill_b, draws = self._resolve_combat_phase(
                    board_a, board_b, bonus_a, bonus_b, p_a, p_b, _ctx
                )

            pts_a = kill_a + combo_pts_a + synergy_pts_a
            pts_b = kill_b + combo_pts_b + synergy_pts_b

            p_a.turn_pts   = pts_a
            p_b.turn_pts   = pts_b
            p_a.total_pts += pts_a
            p_b.total_pts += pts_b

            stats_a = p_a.stats
            stats_b = p_b.stats
            stats_a["kills"] += kill_a // _KILL_PTS
            stats_b["kills"] += kill_b // _KILL_PTS
            stats_a["combo_triggers"] += combo_pts_a
            stats_b["combo_triggers"] += combo_pts_b
            if synergy_pts_a > 0:
                stats_a["synergy_trigger_count"] += 1
            if synergy_pts_b > 0:
                stats_b["synergy_trigger_count"] += 1
            stats_a["synergy_sum"] += synergy_pts_a
            stats_b["synergy_sum"] += synergy_pts_b
            stats_a["synergy_turns"] += 1
            stats_b["synergy_turns"] += 1

            _log(
                f"    Score: P{p_a.pid}={pts_a}"
                f" (kill={kill_a} combo={combo_pts_a} synergy={synergy_pts_a})"
                f"  |  P{p_b.pid}={pts_b}"
                f" (kill={kill_b} combo={combo_pts_b} synergy={synergy_pts_b})"
            )

            hp_before_a = p_a.hp
            hp_before_b = p_b.hp
            result_dmg    = 0
            result_winner = -1

            if pts_a > pts_b:
                dmg = calculate_damage(pts_a, pts_b, board_a, turn=_turn)
                p_b.take_damage(dmg)
                stats_a["wins"] += 1
                stats_b["losses"] += 1
                stats_a["damage_dealt"] += dmg
                p_a.win_streak += 1
                if p_a.win_streak > stats_a["win_streak_max"]:
                    stats_a["win_streak_max"] = p_a.win_streak
                p_b.win_streak = 0
                result_winner = p_a.pid
                result_dmg    = dmg
                _log(f"    -> P{p_a.pid} wins! P{p_b.pid} -{dmg} HP  [HP: {p_b.hp}]")

            elif pts_b > pts_a:
                dmg = calculate_damage(pts_b, pts_a, board_b, turn=_turn)
                p_a.take_damage(dmg)
                stats_b["wins"] += 1
                stats_a["losses"] += 1
                stats_b["damage_dealt"] += dmg
                p_b.win_streak += 1
                if p_b.win_streak > stats_b["win_streak_max"]:
                    stats_b["win_streak_max"] = p_b.win_streak
                p_a.win_streak = 0
                result_winner = p_b.pid
                result_dmg    = dmg
                _log(f"    -> P{p_b.pid} wins! P{p_a.pid} -{dmg} HP  [HP: {p_a.hp}]")

            else:  # Berabere
                p_a.gold += 1
                p_b.gold += 1
                stats_a["gold_earned"] += 1
                stats_b["gold_earned"] += 1
                stats_a["draws"] += 1
                stats_b["draws"] += 1
                p_a.win_streak = 0
                p_b.win_streak = 0
                _log("    -> Draw! Both players +1 gold.")

            results.append({
                "pid_a":       p_a.pid,
                "pid_b":       p_b.pid,
                "pts_a":       pts_a,
                "pts_b":       pts_b,
                "kill_a":      kill_a,
                "kill_b":      kill_b,
                "combo_a":     combo_pts_a,
                "combo_b":     combo_pts_b,
                "synergy_a":   synergy_pts_a,
                "synergy_b":   synergy_pts_b,
                "draws":       draws,
                "winner_pid":  result_winner,
                "dmg":         result_dmg,
                "hp_before_a": hp_before_a,
                "hp_before_b": hp_before_b,
                "hp_after_a":  p_a.hp,
                "hp_after_b":  p_b.hp,
            })

            # Record result in ActionLog
            if game_ref and hasattr(game_ref, "action_log"):
                game_ref.action_log.record("combat_result", results[-1], turn=_turn)

            if not p_a.alive:
                self._return_cards_to_pool(p_a)
                _log(f"    ELIMINATED: P{p_a.pid} (HP=0) — cards returned to pool")
            if not p_b.alive:
                self._return_cards_to_pool(p_b)
                _log(f"    ELIMINATED: P{p_b.pid} (HP=0) — cards returned to pool")

            self._clear_transient_board_state(
                [p_a, p_b], current_turn=_turn + 1, clear_combat_meta=True
            )

        # Signal emission
        if game_ref and hasattr(game_ref, "signals"):
            game_ref.signals.combat_finished.emit(turn=_turn)

        return results
