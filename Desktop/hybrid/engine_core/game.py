"""
================================================================
|         AUTOCHESS HYBRID - Game Module                       |
|  Game class for managing match flow and game loop            |
================================================================

This module contains the Game class which manages the overall game flow,
including preparation phase, combat phase, and the main game loop.

Faz 3: Tur yönetim mantığı TurnManager'a taşındı.
  • game.turn         → TurnManager.turn'ün property alias'ı
  • game.start_turn() → TurnManager.start_turn()'e delege eder
  • game.finish_turn()→ TurnManager.finish_turn()'e delege eder
  • game.swiss_pairs()→ TurnManager.swiss_pairs()'e delege eder
  • combat_phase()    → swiss_pairs TurnManager'dan alınır
"""

import random
import warnings
from typing import List, Tuple, Callable, Dict
from collections import defaultdict, deque

from engine_core.player import Player
from engine_core.market import Market
from engine_core.ai import AI
from engine_core.constants import STARTING_HP
from engine_core.combat_engine import CombatEngine
from engine_core.turn_manager import TurnManager
from engine_core.board_utils import iter_board_cards, clear_transient_board_state
from engine_core.action_log import ActionLog
from engine_core.signals import SignalBus


# ===================================================================
# GAME
# ===================================================================

class Game:
    def __init__(self, players: List[Player], verbose: bool = False, rng=None, seed: int = None,
                 trigger_passive_fn: Callable = None, combat_phase_fn: Callable = None,
                 card_pool: list = None, ai_override=None):
        """Initialize game with players and optional dependencies.

        Args:
            players: List of Player instances
            verbose: Whether to print detailed logs
            rng: Random number generator (optional, mutually exclusive with seed)
            seed: Random seed for deterministic games (optional, mutually exclusive with rng)
            trigger_passive_fn: Function to trigger passive abilities (injected dependency)
            combat_phase_fn: Function to resolve combat phase (injected dependency)
            card_pool: Card pool to use for market (injected dependency)
            ai_override: Custom AI instance to replace default AI (optional).
                         Must expose buy_cards(player, market, ...) and
                         place_cards(player, rng=...) with the same signatures as AI.
                         Used by train_strategies.py for parameterized training.
        
        Note:
            For network games, prefer passing 'seed' parameter instead of 'rng' to ensure
            the seed can be transmitted to clients for deterministic replay.
        """
        self.players  = players
        self.action_log = ActionLog()
        self.signals = SignalBus()

        for p in self.players:
            # REMOVED: p.game = self (circular reference fix)
            # Game reference now passed via context dict in trigger_passive calls
            
            # Connect components to signals with captured PID (Yaklaşım B)
            _pid = p.pid
            p.board._mutation_callback = lambda pid=_pid: self.signals.board_mutated.emit(pid=pid)
            p.economy._on_change = lambda pid=_pid: self.signals.economy_changed.emit(pid=pid)
            p.inventory._on_change = lambda pid=_pid: self.signals.inventory_changed.emit(pid=pid)
        
        self.card_pool = card_pool if card_pool is not None else []
        self.card_by_name = {c.name: c for c in self.card_pool}  # built once
        
        # ── RNG initialization with seed tracking ─────────────────────────────
        # CRITICAL: _rng_seed must be set for multiplayer determinism to work!
        # NetworkServer._send_game_start() reads this to sync clients.
        
        if seed is not None and rng is not None:
            raise ValueError("Cannot specify both 'seed' and 'rng' parameters")
        
        if seed is not None:
            # Explicit seed provided - create RNG and store seed
            self._rng_seed = seed
            self.rng = random.Random(seed)
        elif rng is not None:
            # DEPRECATED: rng= parameter cannot reliably extract seed for multiplayer sync.
            # For network games, ALWAYS use Game(seed=N) instead of Game(rng=rng).
            # This path exists only for backward compatibility with local/test code.
            self.rng = rng
            
            # Attempt to extract seed (UNRELIABLE - state[1][0] is NOT the original seed!)
            try:
                state = rng.getstate()
                # WARNING: This is Mersenne Twister internal state, not the original seed.
                # Two machines using this value will produce DIFFERENT sequences!
                self._rng_seed = state[1][0] if len(state) > 1 and len(state[1]) > 0 else None
            except (AttributeError, IndexError, TypeError):
                self._rng_seed = random.randint(0, 2**32 - 1)
            
            warnings.warn(
                "Game(rng=...) is deprecated for multiplayer. Use Game(seed=N) instead. "
                "The rng= parameter cannot extract the original seed, breaking multiplayer sync.",
                DeprecationWarning,
                stacklevel=2
            )
        else:
            # No seed or RNG provided - generate both
            self._rng_seed = random.randint(0, 2**32 - 1)
            self.rng = random.Random(self._rng_seed)
        
        self.market   = Market(self.card_pool, rng=self.rng)
        self.verbose  = verbose
        self.log: deque = deque(maxlen=10000)
        
        self.trigger_passive_fn = trigger_passive_fn
        self.combat_phase_fn = combat_phase_fn
        # ai_override: ParameterizedAI instance or None (→ default AI class)
        self._ai = ai_override if ai_override is not None else AI
        # UI için: son turun tüm maçlarının sonuç listesi
        self.last_combat_results: List[dict] = []

        # Global-state removal: instances now track their own counters/logs
        self._card_id_counter = 0
        self._passive_trigger_log = defaultdict(lambda: defaultdict(int))

        # ── Faz 3: TurnManager inject edilir ─────────────────────────────────
        # _card_id_counter, next_card_uid() için buradan önce hazır olmalı.
        self._turn_manager = TurnManager(
            players=self.players,
            market=self.market,
            rng=self.rng,
            trigger_passive_fn=self.trigger_passive_fn,
            next_card_uid_fn=self.next_card_uid,
            ai_class=self._ai,
            verbose=self.verbose,
            signals=self.signals,
            action_log=self.action_log,
            game_ref=self,
        )
        # NOT: TurnManager.__init__ içinde _deal_starting_hands() çağrılır.
        # Game.__init__ artık _deal_starting_hands() çağırmaz; çift dağıtım olmaz.

        # ── Faz 2: CombatEngine inject edilir ────────────────────────────────
        self._combat_engine = CombatEngine(
            players=self.players,
            market=self.market,
            rng=self.rng,
            trigger_passive_fn=self.trigger_passive_fn,
            combat_phase_fn=self.combat_phase_fn,
            next_card_uid_fn=self.next_card_uid,
            verbose=self.verbose,
            game_ref=self,  # Pass self for weakref
        )

    # ── turn property: TurnManager tek gerçek kaynak ─────────────────────────

    @property
    def turn(self) -> int:
        """Tur sayacı — TurnManager.turn'ün alias'ı (tek gerçek kaynak)."""
        return self._turn_manager.turn

    @turn.setter
    def turn(self, value: int) -> None:
        self._turn_manager.turn = value

    # ─────────────────────────────────────────────────────────────────────────

    def next_card_uid(self) -> int:
        self._card_id_counter += 1
        return self._card_id_counter

    def _deal_starting_hands(self):
        """Backward-compat shim — TurnManager.__init__ bu işi zaten yapar.
        Yeniden çağrıldığında TurnManager'a delege eder (çökmez).
        """
        self._turn_manager._deal_starting_hands()

    def _log(self, msg: str):
        if self.verbose:
            print(msg)
        self.log.append(msg)

    def alive_players(self) -> List[Player]:
        return [p for p in self.players if p.alive]

    # ── Swiss pairing (TurnManager'a delege) ─────────────────────────────────

    def swiss_pairs(self) -> List[Tuple[Player, Player]]:
        """Faz 3: TurnManager.swiss_pairs()'e delege eder."""
        return self._turn_manager.swiss_pairs()

    # ================================================================
    # UI BRIDGE METHODS — "Manual Orchestrator" arayüzü.
    # Faz 3: tüm mantık TurnManager'da; bu yöntemler yalnızca delege eder.
    # ================================================================

    def start_turn(self) -> None:
        """Phase 1 of 2: Faz 3 — TurnManager.start_turn()'e delege eder.

        Tur sayacı, gelir, market penceresi TurnManager tarafından yönetilir.
        game.turn, TurnManager.turn'ün property alias'ı olduğundan otomatik
        senkronizedir.
        """
        self._turn_manager.start_turn()

    def finish_turn(self) -> None:
        """Phase 2 of 2: Faz 3 — TurnManager.finish_turn()'e delege eder.

        AI satın alma / yerleştirme, faiz, evrim mantığı TurnManager'dadır.
        """
        self._turn_manager.finish_turn()

    # ── Preparation phase (AI simülasyon yolu, run() tarafından kullanılır) ──

    def preparation_phase(self):
        """Faz 3: TurnManager.preparation_phase()'e delege eder.

        start_turn + finish_turn zincirine eşdeğerdir.
        """
        self._turn_manager.preparation_phase()

    # ── Combat + damage phase ─────────────────────────────────────────────────

    def combat_phase(self, pairs=None):
        """Tüm canlı oyuncu çiftleri için kombatı çöz.

        Args:
            pairs: Önceden hesaplanmış (Player, Player) tuple listesi.
                   Verilirse swiss_pairs() çağrılmaz (Bait-and-Switch bug'ını önler).
                   None ise TurnManager.swiss_pairs() çağrılır.

        Faz 2: CombatEngine.run_combat()'a delege eder.
        Faz 3: pairs=None durumunda TurnManager.swiss_pairs() kullanılır.
        """
        if pairs is None:
            pairs = self._turn_manager.swiss_pairs()

        self._combat_engine.turn = self.turn
        self.last_combat_results = self._combat_engine.run_combat(pairs)

    # ── Main game loop ────────────────────────────────────────────────────────

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
