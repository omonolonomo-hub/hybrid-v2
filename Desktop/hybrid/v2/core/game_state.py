import logging
from typing import Any, Dict, List, Optional, Tuple

from v2.core.action_result import ActionResult
from v2.core.engine_adapter import EngineAdapter
from v2.core.public_state import PublicState
from v2.core.state_store import StateStore
from v2.core.ui_adapter import UIAdapter
from v2.core.ui_formatter import UIFormatter

logger = logging.getLogger(__name__)


class GameState:
    """
    Faz 4: game_state.py slim-down + H4-1 accessor cleanup.
    
    Public API:
    - Mutations: buy_card, reroll_market, place_card, commit_human_turn, etc.
    - Reads: get_public_state() → PublicState (single source of truth)
    - Properties: view_index, place_locked
    
    Legacy accessor methods (get_hp, get_gold, get_hand, get_shop, get_board_cards,
    get_board_rotations, get_strategy, get_interest_multiplier) have been removed.
    All UI reads now go through get_public_state().
    """

    def __init__(self):
        self._adapter: Optional[EngineAdapter] = None
        self._store = StateStore()
        self._formatter = UIFormatter()
        self._ui_adapter = UIAdapter()
        # — Ön-bellek: build_public_state() pahalıdır (BFS dahil). Her mutasyondan sonra
        #   _invalidate_cache() çağrılır; sonraki get_public_state() yeniden inşa eder.
        self._cached_public_state: Optional[PublicState] = None

    def hook_engine(self, engine):
        self._adapter = EngineAdapter(engine)
        self._attach_engine_signals()

    def cleanup(self) -> None:
        """Explicitly cleanup resources. Call before discarding GameState instance.
        
        This method is idempotent and can be safely called multiple times.
        """
        self._detach_engine_signals()
        self._cached_public_state = None
        self._adapter = None

    def _attach_engine_signals(self) -> None:
        """Hook engine signals to invalidate cached public state."""
        if not self._adapter:
            return
        game = getattr(self._adapter, "_engine", None)
        if game is None:
            return
            
        if not hasattr(game, "signals"):
            logger.warning("Engine has no 'signals' attribute. Cache invalidation will be manual only.")
            return
        
        # Connect signals to invalidate cache
        game.signals.board_mutated.connect(self._invalidate_cache)
        game.signals.economy_changed.connect(self._invalidate_cache)
        game.signals.inventory_changed.connect(self._invalidate_cache)
        game.signals.turn_started.connect(self._invalidate_cache)
        game.signals.combat_finished.connect(self._invalidate_cache)

    def _detach_engine_signals(self) -> None:
        """Unhook engine signals to prevent memory leaks."""
        if not self._adapter:
            return
        game = getattr(self._adapter, "_engine", None)
        if game is None:
            return
            
        if not hasattr(game, "signals"):
            return
        
        # Disconnect all signals
        game.signals.board_mutated.disconnect(self._invalidate_cache)
        game.signals.economy_changed.disconnect(self._invalidate_cache)
        game.signals.inventory_changed.disconnect(self._invalidate_cache)
        game.signals.turn_started.disconnect(self._invalidate_cache)
        game.signals.combat_finished.disconnect(self._invalidate_cache)

    def _attach_board_mutation_hooks(self) -> None:
        """Deprecated: use _attach_engine_signals instead."""
        pass

    # ------------------------------------------------------------------ cache
    def _invalidate_cache(self, **kwargs) -> None:
        """Herhangi bir mutasyon sonrası çağrılır; bir sonraki get_public_state() yeniden inşa eder.
        
        Sinyal pid içeriyorsa, sadece view_index ile eşleşen oyuncu için cache invalidate edilir.
        Global sinyaller (pid içermeyenler) her zaman invalidate eder.
        
        SECURITY FIX: Eskiden pid != 0 kontrolü yapıyordu, bu spectator modunda stale data
        gösterilmesine neden oluyordu. Artık view_index ile karşılaştırılıyor.
        """
        pid = kwargs.get("pid")
        if pid is not None and pid != self._store.view_index:
            # Sadece izlenen oyuncunun mutasyonu cache'i invalidate eder
            return
            
        self._cached_public_state = None

    def get_public_state(self) -> PublicState:
        """Tüm UI okuma erişiminin tek giriş noktası."""
        if self._cached_public_state is None:
            self._cached_public_state = self._ui_adapter.build_public_state(
                self._adapter, self._store, self._formatter
            )
        return self._cached_public_state

    # ------------------------------------------------------------------ store properties
    @property
    def view_index(self) -> int:
        return self._store.view_index

    @view_index.setter
    def view_index(self, value: int):
        self._store.view_index = value
        self._invalidate_cache()

    @property
    def place_locked(self) -> bool:
        return self._store.place_locked

    @place_locked.setter
    def place_locked(self, value: bool):
        self._store.place_locked = value

    # ------------------------------------------------------------------ internal helper
    def _get_player(self, player_index: Optional[int] = None):
        if player_index is None:
            player_index = self.view_index
        return self._adapter.get_player(player_index) if self._adapter else None

    # ------------------------------------------------------------------ mutations
    def buy_card_from_slot(self, player_index: int, slot_index: int) -> ActionResult:
        if player_index != 0:
            return ActionResult.ERR_NOT_OWNER
        if self._store.phase != "STATE_PREPARATION":
            return ActionResult.ERR_NOT_IN_PREP_PHASE
        if not self._adapter:
            return ActionResult.ERR_ENGINE_EXCEPTION
        result = self._adapter.perform_buy_card(player_index, slot_index)
        self._invalidate_cache()
        return result

    def buy_card(self, player_index: int, slot_index: int) -> ActionResult:
        return self.buy_card_from_slot(player_index, slot_index)

    def reroll_market(self, player_index: int = 0) -> ActionResult:
        if player_index != 0:
            return ActionResult.ERR_NOT_OWNER
        if not self._adapter:
            return ActionResult.ERR_ENGINE_EXCEPTION
        ok = self._adapter.perform_reroll(player_index)
        self._invalidate_cache()
        return ActionResult.OK if ok else ActionResult.ERR_INSUFFICIENT_GOLD

    def toggle_lock_shop(self, player_index: int = 0) -> None:
        if player_index == 0 and self._adapter:
            self._adapter.toggle_lock_shop(player_index)
            self._invalidate_cache()

    def place_card(
        self,
        hand_index: int,
        coord: tuple[int, int],
        rotation: int = 0,
        player_index: int = 0,
    ) -> ActionResult:
        if player_index != 0:
            return ActionResult.ERR_NOT_OWNER
        if self.place_locked:
            return ActionResult.ERR_PLACE_LOCKED
        if not self._adapter:
            return ActionResult.ERR_ENGINE_EXCEPTION

        result = self._adapter.perform_placement(player_index, hand_index, coord, rotation)
        self._invalidate_cache()
        # H3-5: store.update_board() kaldırıldı — board verisi PublicState üzerinden erişiliyor
        return result

    def reset_turn(self) -> None:
        self.place_locked = False
        self._invalidate_cache()
        player = self._get_player(0)
        if player and hasattr(player, "passive_buff_log"):
            player.passive_buff_log.clear()

    def commit_human_turn(self) -> None:
        if not self._adapter:
            return
        pairs = self._adapter.commit_turn()
        self._store.update_pairings(pairs)
        self._invalidate_cache()

    def start_turn(self) -> None:
        if self._adapter:
            self._adapter.start_turn()
            self._invalidate_cache()

    def run_combat_phase(self) -> None:
        if self._adapter:
            self._adapter.run_combat_phase()
            self._invalidate_cache()

    def remove_eliminated_cards(self, player_index: int, coords: list) -> None:
        if self._adapter:
            self._adapter.remove_eliminated_cards(player_index, coords)
            self._invalidate_cache()

    def _mirror_phase(self, phase: str) -> None:
        self._store.phase = phase

    def get_pool_copies(self) -> dict:
        """Havuz kopya sayaçları — PublicState'te karşılığı yoktur."""
        return self._adapter.get_pool_copies() if self._adapter else {}

    def get_endgame_stats(self) -> list:
        return list(self.get_public_state().endgame_stats)

    def get_display_name(self, player_index: Optional[int] = None) -> str:
        if player_index is None or (self._adapter and player_index == self.view_index):
            return self.get_public_state().active_player.display_name
        return f"P{player_index}"

    def get_current_pairings(self) -> list:
        return list(self.get_public_state().pairings)

    def get_alive_pids(self) -> list:
        return list(self.get_public_state().alive_pids)

    def get_last_combat_results(self) -> list:
        return list(self.get_public_state().active_player.combat.last_results)
