import logging
from typing import Any, Dict, List, Optional, Tuple, NamedTuple

from engine_core.constants import (
    CARD_COSTS,
    STARTING_HP,
    CATEGORY_DISPLAY_MAP,
    COPY_THRESH,
    COPY_THRESH_C,
    SYNERGY_THRESHOLDS,
    BOARD_RADIUS,
)
from engine_core.game import Game
from engine_core.card import Card
from engine_core.synergy import tier_bonus as _engine_tier_bonus
from engine_core.board import hex_coords as _engine_hex_coords
from v2.core.action_result import ActionResult
from v2.core.exceptions import (
    EngineAdapterError,
    PlayerNotFoundError,
    MarketNotAvailableError,
    InvalidSlotError,
    InvalidCoordinateError,
    InsufficientResourcesError,
    PlayerDeadError,
    InvalidGameStateError,
    CardDataError,
)

logger = logging.getLogger(__name__)


class EngineConstants(NamedTuple):
    """Immutable snapshot of engine constants to prevent direct engine_core imports."""
    STARTING_HP: int
    CATEGORY_DISPLAY_MAP: Dict[str, str]
    COPY_THRESH: Tuple[int, int]
    COPY_THRESH_C: Tuple[int, int]
    SYNERGY_THRESHOLDS: Tuple[int, ...]
    CARD_COSTS: Dict[str, int]
    BOARD_RADIUS: int


class CardDataSnapshot(NamedTuple):
    """Immutable snapshot of card data to prevent direct CardDatabase access."""
    name: str
    category: str
    rarity: str
    stats: Dict[str, int]
    passive_type: str
    passive_effect: str
    synergy_group: str


class EngineAdapter:
    """
    Formal API to interact with the game engine.
    Encapsulates all direct engine attribute access.
    """

    def __init__(self, engine: Game):
        self._engine = engine

    @staticmethod
    def _coerce_int(value: Any, default: int = 0) -> int:
        return int(value) if isinstance(value, (int, float)) else default

    @staticmethod
    def _coerce_float(value: Any, default: float = 0.0) -> float:
        return float(value) if isinstance(value, (int, float)) else default

    def get_player(self, index: int):
        """Get player by index.
        
        Raises:
            PlayerNotFoundError: If index is out of bounds or players list is invalid.
        """
        try:
            players = self._engine.players
            if not players:
                raise PlayerNotFoundError(index, 0)
            if index < 0 or index >= len(players):
                raise PlayerNotFoundError(index, len(players))
            return players[index]
        except (AttributeError, TypeError) as e:
            logger.error("EngineAdapter.get_player: engine.players is invalid: %s", e)
            raise InvalidGameStateError("Engine players list is corrupted or missing") from e

    def get_market(self):
        """Get market instance, or None if unavailable.
        
        Returns None if market is not initialized or missing required methods.
        Use get_market_or_raise() when you need to guarantee a valid market.
        """
        market = getattr(self._engine, "market", None)
        if market is None or not hasattr(market, "get_window"):
            return None
        return market

    def get_market_or_raise(self):
        """Get market instance, raising if unavailable.
        
        Raises:
            MarketNotAvailableError: If market is not initialized or invalid.
        """
        market = getattr(self._engine, "market", None)
        if market is None:
            raise MarketNotAvailableError("Market not initialized in engine")
        if not hasattr(market, "get_window"):
            raise MarketNotAvailableError("Market missing required methods")
        return market

    def get_shop_window(self, player_index: int) -> List[Optional[str]]:
        """Return the 5-slot market window as card name strings (or None).
        
        Returns [None]*5 if market is unavailable (e.g. mock engines in tests).
        
        Raises:
            PlayerNotFoundError: If player_index is invalid.
        """
        try:
            player = self.get_player(player_index)  # Raises PlayerNotFoundError
        except PlayerNotFoundError:
            raise

        try:
            market = self.get_market()  # Raises MarketNotAvailableError
            pid = player.pid
            player_windows = getattr(market, "_player_windows", {})
            window = player_windows.get(pid, [])
            names = [c.name if c is not None else None for c in window]
            return names + [None] * (5 - len(names))
        except MarketNotAvailableError:
            logger.debug("get_shop_window: market not available for player_index=%s, returning empty slots", player_index)
            return [None] * 5
        except Exception as e:
            logger.exception("EngineAdapter.get_shop_window failed for player_index=%s", player_index)
            return [None] * 5

    def _record_action(self, action_type: str, params: Dict[str, Any]):
        if hasattr(self._engine, "action_log"):
            self._engine.action_log.record(action_type, params, turn=self._engine.turn)

    def perform_buy_card(self, player_index: int, slot_index: int) -> ActionResult:
        """Purchase a card from the shop."""
        try:
            player = self.get_player(player_index)
            if not player.alive:
                return ActionResult.ERR_NOT_IN_PREP_PHASE

            market = self.get_market()
            if not market:
                return ActionResult.ERR_ENGINE_EXCEPTION

            window = market.get_window(player.pid)
            
            if slot_index < 0 or slot_index >= len(window):
                return ActionResult.ERR_POOL_EMPTY
            if window[slot_index] is None:
                return ActionResult.ERR_POOL_EMPTY

            card = window[slot_index]
            cost = CARD_COSTS.get(card.rarity, 2)
            if player.gold < cost:
                return ActionResult.ERR_INSUFFICIENT_GOLD

            player.buy_card(
                card,
                market=market,
                uid=self._engine.next_card_uid(),
                trigger_passive_fn=getattr(self._engine, "trigger_passive_fn", None),
                game_ref=self._engine,
            )
            market.clear_slot(player.pid, slot_index)
            
            self._record_action("buy_card", {"pid": player.pid, "slot": slot_index, "card": card.name})
            return ActionResult.OK
        except PlayerNotFoundError:
            logger.error("perform_buy_card: player_index=%s not found", player_index)
            return ActionResult.ERR_ENGINE_EXCEPTION
        except Exception:
            logger.exception(
                "EngineAdapter.perform_buy_card failed player_index=%s slot_index=%s",
                player_index, slot_index,
            )
            return ActionResult.ERR_ENGINE_EXCEPTION

    def perform_reroll(self, player_index: int) -> bool:
        """Spend 2 gold to refresh the market window. Returns True on success."""
        try:
            player = self.get_player(player_index)
            
            economy = getattr(player, "economy", None)
            if economy is None or not economy.spend_gold(2):
                return False
            
            player.stats["gold_spent"] = player.stats.get("gold_spent", 0) + 2
            
            market = self.get_market()
            if not market:
                return False
            market.deal_market_window(player, 5)
            
            self._record_action("reroll", {"pid": player.pid, "cost": 2})
            return True
        except PlayerNotFoundError:
            logger.error("perform_reroll: player_index=%s not found", player_index)
            return False
        except Exception:
            logger.exception("EngineAdapter.perform_reroll failed for player_index=%s", player_index)
            return False

    def perform_placement(self, player_index: int, hand_index: int, coord: Tuple[int, int], rotation: int) -> ActionResult:
        """Place a card from hand onto the board.
        
        Returns ActionResult enum for backward compatibility with existing callers.
        Logs exceptions but doesn't raise them to maintain current error handling flow.
        """
        try:
            player = self.get_player(player_index)

            board = getattr(player, "board", None)
            if board is None:
                logger.error("Player has no board in perform_placement")
                return ActionResult.ERR_ENGINE_EXCEPTION

            hand = getattr(player, "hand", [])
            if hand_index < 0 or hand_index >= len(hand):
                return ActionResult.ERR_INVALID_HAND_IDX

            if coord in board.grid:
                return ActionResult.ERR_SLOT_OCCUPIED

            card = hand[hand_index]
            if card is None:
                return ActionResult.ERR_INVALID_HAND_IDX

            # Type safety: hand must contain Card objects, not strings
            if not isinstance(card, Card):
                logger.error(
                    "perform_placement: hand[%d] is not a Card object (type=%s). "
                    "This indicates a data integrity violation. Rejecting placement.",
                    hand_index, type(card).__name__
                )
                return ActionResult.ERR_ENGINE_EXCEPTION

            # Update rotation
            card.rotation = rotation % 6

            # Remove from hand (positional integrity) via formal API
            if hasattr(player, "inventory") and hasattr(player.inventory, "clear_slot"):
                player.inventory.clear_slot(hand_index)
            else:
                # Emergency fallback if API is missing (should not happen after refactor)
                hand[hand_index] = None
                if hasattr(player, "inventory") and hasattr(player.inventory, "_emit_change"):
                    player.inventory._emit_change()

            # Place on board
            board.place(coord, card)

            # Record action
            self._record_action("place_card", {
                "pid": player.pid, 
                "hand_idx": hand_index, 
                "coord": coord, 
                "rotation": rotation % 6,
                "card": card.name
            })

            return ActionResult.OK
        except PlayerNotFoundError:
            logger.error("perform_placement: player_index=%s not found", player_index)
            return ActionResult.ERR_ENGINE_EXCEPTION
        except Exception:
            logger.exception(
                "EngineAdapter.perform_placement failed player_index=%s hand_index=%s coord=%s rotation=%s",
                player_index,
                hand_index,
                coord,
                rotation,
            )
            return ActionResult.ERR_ENGINE_EXCEPTION

    def get_turn(self) -> int:
        return self._coerce_int(getattr(self._engine, "turn", 0), default=0)

    def get_player_hp(self, index: int) -> int:
        """Get player HP, with fallback to 0 for backward compatibility."""
        try:
            if hasattr(self._engine, "get_hp"):
                hp = self._engine.get_hp(index)
                if isinstance(hp, (int, float)):
                    return int(hp)
            player = self.get_player(index)
            return self._coerce_int(getattr(player, "hp", 0), default=0)
        except PlayerNotFoundError:
            logger.warning("get_player_hp: player_index=%s not found, returning 0", index)
            return 0

    def get_player_gold(self, index: int) -> int:
        """Get player gold, with fallback to 0 for backward compatibility."""
        try:
            player = self.get_player(index)
            return self._coerce_int(getattr(player, "gold", 0), default=0)
        except PlayerNotFoundError:
            logger.warning("get_player_gold: player_index=%s not found, returning 0", index)
            return 0

    def get_alive_players(self) -> List[Any]:
        return [player for player in self._engine.players if player.alive]

    def get_all_players(self) -> List[Any]:
        return self._engine.players

    def get_last_results(self) -> List[Dict[str, Any]]:
        results = getattr(self._engine, "last_combat_results", [])
        return results if isinstance(results, list) else []

    def get_pool_copies(self) -> Dict[str, int]:
        """Get pool copies from market, with fallback to empty dict."""
        market = self.get_market()
        if market is None:
            return {}
        return dict(market.pool_copies)

    def toggle_lock_shop(self, player_index: int) -> None:
        """Directly toggle shop_locked on the player — no longer delegates to Game.
        
        Silently fails if player not found (for backward compatibility).
        """
        try:
            player = self.get_player(player_index)
            player.shop_locked = not getattr(player, "shop_locked", False)
        except PlayerNotFoundError:
            logger.warning("toggle_lock_shop: player_index=%s not found", player_index)

    def is_shop_locked(self, player_index: int) -> bool:
        """Check if shop is locked, with fallback to False."""
        try:
            player = self.get_player(player_index)
            return bool(getattr(player, "shop_locked", False))
        except PlayerNotFoundError:
            logger.warning("is_shop_locked: player_index=%s not found, returning False", player_index)
            return False

    def commit_turn(self):
        try:
            # Game class always has finish_turn which delegates to TurnManager
            self._engine.finish_turn()
            return self._engine.swiss_pairs()
        except Exception:
            logger.exception("EngineAdapter.commit_turn failed")
            return []

    def start_turn(self) -> None:
        if self._engine is None:
            return
        if hasattr(self._engine, "start_turn"):
            self._engine.start_turn()

    def run_combat_phase(self) -> None:
        if self._engine is None:
            return
        if hasattr(self._engine, "combat_phase"):
            self._engine.combat_phase()

    def remove_eliminated_cards(self, player_index: int, coords: list) -> None:
        """Remove eliminated cards from board, silently fails if player not found."""
        try:
            player = self.get_player(player_index)
            board = getattr(player, "board", None)
            if board is None or not hasattr(board, "remove"):
                return
            for coord in coords:
                board.remove(coord)
        except PlayerNotFoundError:
            logger.warning("remove_eliminated_cards: player_index=%s not found", player_index)

    def get_eliminated_coords(self, player_index: int) -> list:
        """Get coordinates of eliminated cards, with fallback to empty list."""
        try:
            player = self.get_player(player_index)
            board = getattr(player, "board", None)
            grid = getattr(board, "grid", None)
            if not isinstance(grid, dict):
                return []
            return [coord for coord, card in grid.items() if hasattr(card, "is_eliminated") and card.is_eliminated()]
        except PlayerNotFoundError:
            logger.warning("get_eliminated_coords: player_index=%s not found, returning []", player_index)
            return []

    def get_passive_buff_log(self, player_index: int) -> list:
        """Get passive buff log, with fallback to empty list."""
        try:
            player = self.get_player(player_index)
            return list(getattr(player, "passive_buff_log", []))
        except PlayerNotFoundError:
            logger.warning("get_passive_buff_log: player_index=%s not found, returning []", player_index)
            return []

    def get_rarity_weight(self, rarity: str, turn: int) -> float:
        """Get rarity weight from market, with fallback to 0.0."""
        market = self.get_market()
        if market is None:
            return 0.0
        weight = market.get_rarity_weight(rarity, turn)
        return self._coerce_float(weight, default=0.0)

    def get_hand(self, player_index: int = 0) -> list:
        """Return the 6-slot hand for the given player as card name strings
        (or None for empty slots). Slot pozisyonları korunur — None slotlar
        filtrelenmez, böylece drag-drop kaynak indeksi doğru kalır.

        H3-2 düzeltmesi: Eskiden None slotları filtreleyip trailing None ekliyordu,
        bu da orta boşluklarda indeks kaymasına neden oluyordu.
        
        Raises:
            PlayerNotFoundError: If player_index is invalid.
        """
        player = self.get_player(player_index)  # Now raises PlayerNotFoundError
        hand = player.hand
        # None dahil tüm slotları koru; position integrity bozulmasın
        result = [
            (c.name if hasattr(c, "name") else str(c)) if c is not None else None
            for c in hand[:6]
        ]
        return result + [None] * max(0, 6 - len(result))

    def reroll_market(self, player_index: int = 0, cost: int = 2) -> bool:
        """Spend `cost` gold to refresh the market window for the player.
        
        Returns True on success, False if the player cannot afford it.
        
        SECURITY: Always delegates to perform_reroll() which uses Economy.spend_gold()
        for proper validation, stats tracking, and signal emission. Custom cost paths
        have been removed to prevent economy API bypass exploits.
        """
        if cost != 2:
            logger.warning(
                "reroll_market called with non-standard cost=%d. "
                "Only cost=2 is supported. Rejecting operation.",
                cost
            )
            return False
        
        return self.perform_reroll(player_index)

    def get_display_name(self, pid: int) -> str:
        """Return the UI-friendly name for a player. Avoids AttributeError on
        players that only have .pid (not .name)."""
        for p in self._engine.players:
            if p.pid == pid:
                return getattr(p, "name", f"P{pid}")
        return f"P{pid}"

    @staticmethod
    def get_constants() -> EngineConstants:
        """Return immutable snapshot of engine constants.
        
        This prevents UI/view layers from directly importing engine_core.constants.
        All constant access should go through this method to maintain layer isolation.
        """
        return EngineConstants(
            STARTING_HP=STARTING_HP,
            CATEGORY_DISPLAY_MAP=dict(CATEGORY_DISPLAY_MAP),
            COPY_THRESH=COPY_THRESH,
            COPY_THRESH_C=COPY_THRESH_C,
            SYNERGY_THRESHOLDS=SYNERGY_THRESHOLDS,
            CARD_COSTS=dict(CARD_COSTS),
            BOARD_RADIUS=BOARD_RADIUS,
        )

    @staticmethod
    def get_card_info(name: str) -> Optional[CardDataSnapshot]:
        """Return immutable snapshot of card data from CardDatabase.
        
        This prevents UI/view layers from directly importing CardDatabase.
        All card data access should go through this method to maintain layer isolation.
        
        Returns None if card not found or database not initialized.
        """
        try:
            from v2.core.card_database import CardDatabase
            db = CardDatabase.get()
            card = db.lookup(name)
            if card is None:
                return None
            return CardDataSnapshot(
                name=card.name,
                category=card.category,
                rarity=card.rarity,
                stats=dict(card.stats),
                passive_type=card.passive_type,
                passive_effect=card.passive_effect,
                synergy_group=card.synergy_group,
            )
        except Exception:
            logger.exception("EngineAdapter.get_card_info failed for name=%s", name)
            return None

    @staticmethod
    def tier_bonus(threshold: int) -> int:
        """Calculate tier bonus for a given threshold.
        
        Delegates to engine_core.synergy.tier_bonus to ensure UI and engine
        use the same bonus calculation logic.
        """
        return _engine_tier_bonus(threshold)

    @staticmethod
    def get_hex_coords(radius: int) -> List[Tuple[int, int]]:
        """Return list of valid hex coordinates for the given radius.
        
        Delegates to engine_core.board.hex_coords to ensure UI and engine
        use the same coordinate system.
        """
        return _engine_hex_coords(radius)