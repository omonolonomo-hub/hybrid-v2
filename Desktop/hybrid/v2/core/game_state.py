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
    Faz 4: game_state.py slim-down.
    Geriye yalnızca engine mutasyon metodları ve cache yönetimi kaldı.
    Okuma erişimi için get_public_state() → PublicState kullanılmalıdır.
    """

    def __init__(self):
        self._adapter: Optional[EngineAdapter] = None
        self._store = StateStore()
        self._formatter = UIFormatter()
        self._ui_adapter = UIAdapter()
        # — Ön-bellek: build_public_state() pahalıdır (BFS dahil). Her mutasyondan sonra
        #   _invalidate_cache() çağrılır; sonraki get_public_state() yeniden inşa eder.
        self._cached_public_state: Optional[PublicState] = None

    def __del__(self):
        """Cleanup signal observers to prevent memory leaks."""
        self._detach_engine_signals()

    def hook_engine(self, engine):
        self._adapter = EngineAdapter(engine)
        self._attach_engine_signals()

    def cleanup(self) -> None:
        """Explicitly cleanup resources. Call before discarding GameState instance."""
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
        
        Sinyal pid içeriyorsa, sadece pid=0 (insan oyuncu) için cache invalidate edilir.
        Global sinyaller (pid içermeyenler) her zaman invalidate eder.
        """
        pid = kwargs.get("pid")
        if pid is not None and pid != 0:
            # AI oyuncuların mutasyonları UI cache'ini bozmaz (performans optimizasyonu)
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

    # ------------------------------------------------------------------ H4-1: Accessors
    def get_board_cards(self, player_index: Optional[int] = None) -> dict:
        """Oyuncunun tahtasındaki kartları (coord -> dict) döner."""
        state = self.get_public_state()
        if player_index is None or (self._adapter and player_index == state.view_index):
            return dict(state.active_player.board_cards)
        
        # Fallback for non-active player
        player = self._get_player(player_index)
        if player and hasattr(player, "board"):
            return {
                coord: {
                    "name": getattr(card, "name", str(card)),
                    "stats": getattr(card, "stats", {}),
                    "rotation": getattr(card, "rotation", 0)
                } 
                for coord, card in player.board.grid.items()
            }
        return {}

    def get_board_rotations(self, player_index: Optional[int] = None) -> dict:
        cards = self.get_board_cards(player_index)
        return {coord: info.get("rotation", 0) for coord, info in cards.items()}

    def get_hp(self, player_index: Optional[int] = None) -> int:
        if player_index is None:
            return self.get_public_state().active_player.hp
        return self._adapter.get_player_hp(player_index) if self._adapter else 0

    def get_gold(self, player_index: Optional[int] = None) -> int:
        if player_index is None:
            return self.get_public_state().active_player.gold
        return self._adapter.get_player_gold(player_index) if self._adapter else 0

    def get_hand(self, player_index: Optional[int] = None) -> list:
        if player_index is None:
            return list(self.get_public_state().active_player.hand.slots)
        return self._adapter.get_hand(player_index) if self._adapter else [None] * 6

    def get_shop(self, player_index: Optional[int] = None) -> list:
        if player_index is None:
            return list(self.get_public_state().active_player.shop.slots)
        return self._adapter.get_shop_window(player_index) if self._adapter else [None] * 5

    def get_endgame_stats(self) -> list:
        return list(self.get_public_state().endgame_stats)

    def get_display_name(self, player_index: Optional[int] = None) -> str:
        if player_index is None or (self._adapter and player_index == self.view_index):
            return self.get_public_state().active_player.display_name
        return f"P{player_index}"

    def get_strategy(self, player_index: Optional[int] = None) -> str:
        if player_index is None or (self._adapter and player_index == self.view_index):
            return self.get_public_state().active_player.strategy
        
        # Search in endgame_stats or lobby_players if needed
        for stat in self.get_public_state().endgame_stats:
            if stat.get("name") == f"P{player_index}":
                return stat.get("strategy", "unknown")
        return "unknown"

    def get_current_pairings(self) -> list:
        return list(self.get_public_state().pairings)

    def get_alive_pids(self) -> list:
        return list(self.get_public_state().alive_pids)

    def get_interest_multiplier(self, player_index: Optional[int] = None) -> float:
        if player_index is None or (self._adapter and player_index == self.view_index):
            return self.get_public_state().active_player.hud.interest_multiplier
        
        player = self._get_player(player_index)
        return float(getattr(player, "interest_multiplier", 1.0)) if player else 1.0

    def get_last_combat_results(self) -> list:
        return list(self.get_public_state().active_player.combat.last_results)
