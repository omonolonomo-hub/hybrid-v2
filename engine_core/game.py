"""
================================================================
|         AUTOCHESS HYBRID - Game Module                       |
|  Game class for managing match flow and game loop            |
================================================================

This module contains the Game class which manages the overall game flow,
including preparation phase, combat phase, and the main game loop.
"""

import random
from typing import List, Tuple, Callable, Dict

# Import dependencies
try:
    from .player import Player
    from .board import Board, find_combos, calculate_group_synergy_bonus, calculate_damage
    from .market import Market
    from .ai import AI
    from .constants import KILL_PTS, STARTING_HP
    # get_card_pool is defined in autochess_sim_v06, will be passed via Market
except ImportError:
    from player import Player
    from board import Board, find_combos, calculate_group_synergy_bonus, calculate_damage
    from market import Market
    from ai import AI
    from constants import KILL_PTS, STARTING_HP
    # get_card_pool is defined in autochess_sim_v06, will be passed via Market


# ===================================================================
# GAME
# ===================================================================

class Game:
    def __init__(self, players: List[Player], verbose: bool = False, rng=None, 
                 trigger_passive_fn: Callable = None, combat_phase_fn: Callable = None,
                 card_pool: list = None, ai_override=None):
        """Initialize game with players and optional dependencies.
        
        Args:
            players: List of Player instances
            verbose: Whether to print detailed logs
            rng: Random number generator (optional)
            trigger_passive_fn: Function to trigger passive abilities (injected dependency)
            combat_phase_fn: Function to resolve combat phase (injected dependency)
            card_pool: Card pool to use for market (injected dependency)
            ai_override: Custom AI instance to replace default AI (optional).
                         Must expose buy_cards(player, market, ...) and
                         place_cards(player, rng=...) with the same signatures as AI.
                         Used by train_strategies.py for parameterized training.
        """
        self.players  = players
        self.card_pool = card_pool if card_pool is not None else []
        self.card_by_name = {c.name: c for c in self.card_pool}  # built once
        self.market   = Market(self.card_pool, rng=rng)
        self.turn     = 0
        self.verbose  = verbose
        self.log: List[str] = []
        self.rng = rng if rng is not None else random.Random()
        self.trigger_passive_fn = trigger_passive_fn
        self.combat_phase_fn = combat_phase_fn
        # ai_override: ParameterizedAI instance or None (→ default AI class)
        self._ai = ai_override if ai_override is not None else AI
        # UI için: son turun tüm maçlarının sonuç listesi
        # Her eleman: {pid_a, pid_b, pts_a, pts_b,
        #   kill_a, kill_b, combo_a, combo_b, synergy_a, synergy_b,
        #   winner_pid, dmg, hp_before_a, hp_before_b, hp_after_a, hp_after_b, draws}
        self.last_combat_results: List[dict] = []
        # Lobby: each player gets 3 random rarity-1 (common) cards
        self._deal_starting_hands()

    # ------------------------------------------------------------------
    # Card-pool management
    # ------------------------------------------------------------------

    def _return_cards_to_pool(self, player) -> None:
        """Return all board and hand cards of an eliminated player back to
        the shared market pool.

        Why this matters:
        - Prevents 'ghost board' (B1_DEAD_BOARD) validation errors: the AI
          no longer tries to validate/interact with a dead player's board.
        - Restores card availability: surviving Economists / Rare Hunters can
          find quality cards in the market again instead of hitting scarcity.
        - Net effect: ~40-50 % speed-up in long simulations and cleaner
          fitness measurements (strategy performance, not bug-survival).

        Safety guarantees:
        - Called only once per player death because dead players never appear
          in alive_players() -> swiss_pairs() again, so combat_phase won't
          re-trigger this for the same player.
        - Evolved cards ("Evolved X") return 1 copy of their base name (X)
          so pool availability is always non-negative and capped at 3.
        """
        _pool_copies = self.market.pool_copies

        def _return_one(card) -> None:
            name = card.name
            # Evolved cards consumed 3 base copies; return 1 base copy (conservative)
            base = name[8:] if name.startswith("Evolved ") else name
            if base in _pool_copies:
                _pool_copies[base] = min(_pool_copies[base] + 1, 3)

        # --- Board ---
        for card in list(player.board.grid.values()):
            _return_one(card)
        player.board.grid.clear()
        # Reset board-level flags so no stale state leaks
        if hasattr(player.board, "has_catalyst"):
            player.board.has_catalyst = False

        # --- Hand ---
        for card in list(player.hand):
            _return_one(card)
        player.hand.clear()

        # --- Internal copy tracking (prevent phantom evolutions) ---
        player.copies.clear()
        player.copy_turns.clear()

    def _deal_starting_hands(self):
        """Deal 3 random rarity-1 (lowest tier) cards to each player at match start."""
        common_cards = [c for c in self.card_pool if c.rarity == "1"]
        for player in self.players:
            chosen = self.rng.sample(common_cards, min(3, len(common_cards)))
            for card in chosen:
                cloned = card.clone()
                player.hand.append(cloned)
                player.copies[card.name] = player.copies.get(card.name, 0) + 1
            self._log(f"  P{player.pid} starting cards: "
                      f"{', '.join(c.name for c in chosen)}")

    def _log(self, msg: str):
        if self.verbose:
            print(msg)
        self.log.append(msg)

    def alive_players(self) -> List[Player]:
        return [p for p in self.players if p.alive]

    # -- Swiss pairing --

    def swiss_pairs(self) -> List[Tuple[Player, Player]]:
        """Sort by HP, jitter same-HP band, pair nearest opponents."""
        alive = self.alive_players()
        # FIX 6: shuffle within HP jitter so pairings vary each turn
        alive.sort(key=lambda p: p.hp + self.rng.random() * 0.5, reverse=True)
        pairs = []
        used: set = set()
        for i, p1 in enumerate(alive):
            if p1.pid in used:
                continue
            for j in range(i+1, len(alive)):
                p2 = alive[j]
                if p2.pid not in used:
                    pairs.append((p1, p2))
                    used.add(p1.pid)
                    used.add(p2.pid)
                    break
        return pairs

    # ================================================================
    # UI BRIDGE METHODS — The "Manual Orchestrator" interface.
    # These methods replace preparation_phase() for human games.
    # start_turn()  → called when the shop screen opens (income + market)
    # finish_turn() → called when human clicks "Ready" (AI acts + hooks)
    # ================================================================

    def start_turn(self) -> None:
        """Phase 1 of 2: Advance turn counter, deal income + market windows.
        Does NOT run AI buy/place logic — that waits until finish_turn().
        This allows the human player to browse the shop before any AI acts.
        """
        self.turn += 1
        _turn = self.turn
        _log  = self._log
        _verbose = self.verbose
        _trigger_passive = self.trigger_passive_fn
        _market = self.market

        _log(f"\n{'-'*50}\n  TURN {_turn} — PREPARATION START\n{'-'*50}")

        alive = self.alive_players()

        # Open market windows, respecting shop_locked
        self._current_player_markets = {}
        for player in alive:
            if not getattr(player, "shop_locked", False):
                self._current_player_markets[player.pid] = _market.deal_market_window(player, 5)
            else:
                self._current_player_markets[player.pid] = _market._player_windows.get(player.pid, [])
                # Auto-unlock for next turn so it refreshes unless locked again
                player.shop_locked = False

        # Give income to everyone (including human)
        for player in alive:
            player.income()
            if _trigger_passive:
                for card in tuple(player.board.grid.values()):
                    _trigger_passive(card, "income", player, None,
                                     {"turn": _turn}, verbose=_verbose)
            if _trigger_passive:
                for card in tuple(player.board.grid.values()):
                    _trigger_passive(card, "market_refresh", player, None,
                                     {"turn": _turn}, verbose=_verbose)

    def finish_turn(self) -> None:
        """Phase 2 of 2: Run AI for every NON-human player, then apply
        apply_interest, check_evolution, check_copy_strengthening for all.
        Called when human clicks "Ready".
        """
        _turn = self.turn
        _log  = self._log
        _verbose = self.verbose
        _trigger_passive = self.trigger_passive_fn
        _market = self.market
        _rng = self.rng
        _ai = self._ai

        alive = self.alive_players()
        player_markets = getattr(self, "_current_player_markets", {})

        for player in alive:
            player_market = player_markets.get(player.pid, [])

            # HUMAN IMMUNITY: skip AI logic for human-controlled player
            if player.strategy == "human":
                # Human already committed their buys via GameState.buy_card_from_slot
                # Pass None so return_unsold reads player._window_bought (set by player.buy_card)
                newly_bought = None
            else:
                hand_before = len(player.hand)
                _ai.buy_cards(player, player_market, market_obj=_market,
                              rng=_rng, trigger_passive_fn=_trigger_passive)
                newly_bought = player.hand[hand_before:]

            if not getattr(player, "shop_locked", False):
                _market.return_unsold(player, bought=newly_bought)
            else:
                if hasattr(player, "_window_bought"):
                    player._window_bought = []
            player.apply_interest()
            evos = player.check_evolution(market=_market, card_by_name=self.card_by_name)
            if evos and _verbose:
                for base_name in evos:
                    _log(f"  *** EVOLUTION: P{player.pid} evolved "
                         f"{base_name} -> Evolved {base_name}! ***")

            if player.strategy != "human":
                _ai.place_cards(player, rng=_rng)

            if _trigger_passive:
                player.check_copy_strengthening(_turn, trigger_passive_fn=_trigger_passive)

            # Per-turn board snapshot
            for _c in player.board.grid.values():
                player.card_turns_alive[_c.name] = \
                    player.card_turns_alive.get(_c.name, 0) + 1
                player.stats["board_power"] += _c.total_power()
                player.stats["unit_count"]  += 1
            player.stats["gold_per_turn"] += player.gold

    def toggle_lock_shop(self, player_index: int = 0) -> None:
        """Lock or unlock the market window for the player."""
        if player_index >= len(self.players):
            return
        player = self.players[player_index]
        current_lock = getattr(player, "shop_locked", False)
        player.shop_locked = not current_lock

    def get_shop_window(self, player_index: int = 0) -> list:
        """Return the 5-slot market window for the given player as a list of
        card name strings (or None for empty slots). Safe to call any time."""
        if player_index >= len(self.players):
            return [None] * 5
        pid = self.players[player_index].pid
        window = self.market._player_windows.get(pid, [])
        names = [c.name if c is not None else None for c in window]
        return names + [None] * (5 - len(names))

    def get_hand(self, player_index: int = 0) -> list:
        """Return the 6-slot hand for the given player as card name strings
        (or None for empty slots). Safe even when hand has < 6 cards."""
        if player_index >= len(self.players):
            return [None] * 6
        hand = self.players[player_index].hand
        names = [c.name for c in hand if c is not None]
        return names + [None] * (6 - len(names))

    def reroll_market(self, player_index: int = 0, cost: int = 2) -> bool:
        """Spend `cost` gold to refresh the market window for the player.
        Returns True on success, False if the player cannot afford it."""
        if player_index >= len(self.players):
            return False
        player = self.players[player_index]
        if player.gold < cost:
            return False
        player.gold -= cost
        # deal_market_window içinde _return_window çağrılır — eski window'u iade eder
        # Burada ekstra iade yapmayın (double-return pool-inflation bug)
        self.market.deal_market_window(player, 5)
        return True

    def get_display_name(self, pid: int) -> str:
        """Return the UI-friendly name for a player. Avoids AttributeError on
        players that only have .pid (not .name)."""
        for p in self.players:
            if p.pid == pid:
                return getattr(p, "name", f"P{pid}")
        return f"P{pid}"

    # -- Preparation phase (legacy — used by run() for full AI simulations) --

    def preparation_phase(self):
        self.turn += 1
        _turn = self.turn
        _log = self._log
        _verbose = self.verbose
        _market = self.market
        _rng = self.rng
        _trigger_passive = self.trigger_passive_fn
        _ai = self._ai  # default AI class or ParameterizedAI instance
        _log(f"\n{'-'*50}\n  TURN {_turn}\n{'-'*50}")

        # Market order fix: open all windows first to remove first-player advantage
        alive = self.alive_players()
        player_markets = {
            player.pid: _market.deal_market_window(player, 5)
            for player in alive
        }

        for player in alive:
            player.income()
            if _trigger_passive:
                for card in tuple(player.board.grid.values()):
                    _trigger_passive(card, "income", player, None, {"turn": _turn}, verbose=_verbose)

            player_market = player_markets[player.pid]
            if _trigger_passive:
                for card in tuple(player.board.grid.values()):
                    _trigger_passive(card, "market_refresh", player, None, {"turn": _turn}, verbose=_verbose)

            hand_before_count = len(player.hand)
            _ai.buy_cards(player, player_market, market_obj=_market, rng=_rng, trigger_passive_fn=_trigger_passive)
            newly_bought = player.hand[hand_before_count:]
            _market.return_unsold(player, bought=newly_bought)
            player.apply_interest()
            evos = player.check_evolution(market=_market, card_by_name=self.card_by_name)
            if evos and _verbose:
                for base_name in evos:
                    _log(f"  *** EVOLUTION: P{player.pid} evolved {base_name} -> Evolved {base_name}! ***")
            _ai.place_cards(player, rng=_rng)
            if _trigger_passive:
                player.check_copy_strengthening(_turn, trigger_passive_fn=_trigger_passive)
            _card_turns_alive = player.card_turns_alive
            _stats = player.stats
            _grid = player.board.grid
            # per-turn board snapshot (lightweight counters, no allocations)
            _bp = 0
            _uc = 0
            for _c in _grid.values():
                _bp += _c.total_power()
                _uc += 1
                _card_turns_alive[_c.name] = _card_turns_alive.get(_c.name, 0) + 1
            _stats["board_power"] += _bp
            _stats["unit_count"]  += _uc
            _stats["gold_per_turn"] += player.gold

    # -- Combat + damage phase --

    def combat_phase(self, pairs=None):
        """Resolve combat for all alive player pairs this turn.
        
        Args:
            pairs: Optional pre-computed list of (Player, Player) tuples.
                   If provided (e.g. frozen by the UI's Versus overlay),
                   those exact matchups are used — swiss_pairs() is NOT 
                   called again, preventing RNG drift (Bait-and-Switch bug).
                   If None, swiss_pairs() is called normally.
        """
        if pairs is None:
            pairs = self.swiss_pairs()


        if not pairs:
            return

        _log = self._log
        _verbose = self.verbose
        _turn = self.turn
        _KILL_PTS = KILL_PTS
        _trigger_passive = self.trigger_passive_fn
        _combat_phase_fn = self.combat_phase_fn

        # Her tur sonuç listesini sıfırla
        self.last_combat_results = []

        for p_a, p_b in pairs:
            _log(f"\n  P{p_a.pid}({p_a.strategy}, {p_a.hp}HP)"
                 f" vs P{p_b.pid}({p_b.strategy}, {p_b.hp}HP)")

            _ctx = {"turn": _turn}
            board_a = p_a.board
            board_b = p_b.board

            if _trigger_passive:
                for card in tuple(board_a.grid.values()):
                    _trigger_passive(card, "pre_combat", p_a, p_b, _ctx, verbose=_verbose)
                for card in tuple(board_b.grid.values()):
                    _trigger_passive(card, "pre_combat", p_b, p_a, _ctx, verbose=_verbose)

            # Combo bonuses (Baseline 1pt per line, doubled by Catalyst)
            combo_pts_a, bonus_a = find_combos(board_a)
            combo_pts_b, bonus_b = find_combos(board_b)
            if board_a.has_catalyst:
                combo_pts_a *= 2
            if board_b.has_catalyst:
                combo_pts_b *= 2

            # Group synergy bonus (Clusters & Connection Quality)
            synergy_pts_a = calculate_group_synergy_bonus(board_a)
            synergy_pts_b = calculate_group_synergy_bonus(board_b)

            # Board combat resolution
            if _combat_phase_fn:
                kill_a, kill_b, draws = _combat_phase_fn(board_a, board_b, bonus_a, bonus_b, p_a, p_b, _ctx)
            else:
                kill_a, kill_b, draws = 0, 0, 0

            # TOTAL SCORE: Kills (8) + Baseline Lines (1) + Cluster/Quality (New System)
            pts_a = kill_a + combo_pts_a + synergy_pts_a
            pts_b = kill_b + combo_pts_b + synergy_pts_b

            p_a.turn_pts  = pts_a
            p_b.turn_pts  = pts_b
            p_a.total_pts += pts_a
            p_b.total_pts += pts_b


            stats_a = p_a.stats
            stats_b = p_b.stats
            stats_a["kills"] += kill_a // _KILL_PTS
            stats_b["kills"] += kill_b // _KILL_PTS

            # per-turn combat metrics
            stats_a["combo_triggers"] += combo_pts_a
            stats_b["combo_triggers"] += combo_pts_b
            if synergy_pts_a > 0:
                stats_a["synergy_trigger_count"] += 1
            if synergy_pts_b > 0:
                stats_b["synergy_trigger_count"] += 1

            _log(f"    Score: P{p_a.pid}={pts_a} (kill={kill_a} combo={combo_pts_a} synergy={synergy_pts_a})"
                 f"  |  P{p_b.pid}={pts_b} (kill={kill_b} combo={combo_pts_b} synergy={synergy_pts_b})")

            stats_a["synergy_sum"] += synergy_pts_a
            stats_b["synergy_sum"] += synergy_pts_b
            stats_a["synergy_turns"] += 1
            stats_b["synergy_turns"] += 1

            # HP snapshot — hasar uygulanmadan önce
            hp_before_a = p_a.hp
            hp_before_b = p_b.hp

            # Damage to loser
            result_dmg    = 0
            result_winner = -1   # -1 = berabere
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
            else:
                p_a.gold += 1
                p_b.gold += 1
                stats_a["gold_earned"] += 1
                stats_b["gold_earned"] += 1
                stats_a["draws"] += 1
                stats_b["draws"] += 1
                p_a.win_streak = 0
                p_b.win_streak = 0
                _log(f"    -> Draw! Both players +1 gold.")

            # UI için sonucu kaydet
            self.last_combat_results.append({
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

            # Elimination check — return cards to pool immediately on death
            if not p_a.alive:
                self._return_cards_to_pool(p_a)
                _log(f"    ELIMINATED: P{p_a.pid} (HP=0) — cards returned to pool")
            if not p_b.alive:
                self._return_cards_to_pool(p_b)
                _log(f"    ELIMINATED: P{p_b.pid} (HP=0) — cards returned to pool")

    # -- Main game loop --

    def run(self) -> Player:
        _players = self.players
        while len([p for p in _players if p.alive]) > 1:
            self.preparation_phase()
            self.combat_phase()
            # Builder synergy matrix: her tur sonunda hafifçe unuttur
            for p in _players:
                if p.alive and p.synergy_matrix is not None:
                    p.synergy_matrix.decay()
            if self.turn >= 50:  # infinite-loop guard
                break

        winners = [p for p in _players if p.alive]
        if winners:
            winner = max(winners, key=lambda p: p.hp)
        else:
            winner = max(_players, key=lambda p: p.hp)

        self._log(f"\n  WINNER: P{winner.pid} ({winner.strategy})"
                  f"  HP={winner.hp}  Score={winner.total_pts}")
        return winner
