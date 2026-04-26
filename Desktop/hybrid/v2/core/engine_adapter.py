import logging
from typing import Any, Dict, List, Optional, Tuple

from engine_core.constants import CARD_COSTS
from engine_core.game import Game
from engine_core.card import Card
from v2.core.action_result import ActionResult

logger = logging.getLogger(__name__)


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
        try:
            return self._engine.players[index]
        except (IndexError, AttributeError):
            logger.warning("EngineAdapter.get_player failed for index=%s", index)
            return None

    def get_market(self):
        market = getattr(self._engine, "market", None)
        return market if hasattr(market, "get_window") else None

    def get_shop_window(self, player_index: int) -> List[Optional[str]]:
        """Return the 5-slot market window as card name strings (or None)."""
        try:
            if player_index >= len(self._engine.players):
                return [None] * 5
            pid = self._engine.players[player_index].pid
            market = getattr(self._engine, "market", None)
            player_windows = getattr(market, "_player_windows", {}) if market is not None else {}
            window = player_windows.get(pid, [])
            names = [c.name if c is not None else None for c in window]
            return names + [None] * (5 - len(names))
        except Exception:
            logger.exception("EngineAdapter.get_shop_window failed for player_index=%s", player_index)
            return [None] * 5

    def _record_action(self, action_type: str, params: Dict[str, Any]):
        if hasattr(self._engine, "action_log"):
            self._engine.action_log.record(action_type, params, turn=self._engine.turn)

    def perform_buy_card(self, player_index: int, slot_index: int) -> ActionResult:
        player = self.get_player(player_index)
        if not player or not player.alive:
            return ActionResult.ERR_NOT_IN_PREP_PHASE

        market = self.get_market()
        if not market:
            return ActionResult.ERR_ENGINE_EXCEPTION

        try:
            window = market.get_window(player.pid)
            if slot_index >= len(window) or window[slot_index] is None:
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
            )
            market.clear_slot(player.pid, slot_index)
            
            # Record action
            self._record_action("buy_card", {"pid": player.pid, "slot": slot_index, "card": card.name})
            
            return ActionResult.OK
        except Exception:
            logger.exception(
                "EngineAdapter.perform_buy_card failed player_index=%s slot_index=%s",
                player_index,
                slot_index,
            )
            return ActionResult.ERR_ENGINE_EXCEPTION

    def perform_reroll(self, player_index: int) -> bool:
        """Spend 2 gold to refresh the market window. Returns True on success."""
        try:
            player = self.get_player(player_index)
            if not player:
                return False
            
            # Use formal economy API to spend gold (SSoT)
            economy = getattr(player, "economy", None)
            if economy is None or not economy.spend_gold(2):
                return False
                
            self._engine.market.deal_market_window(player, 5)
            
            # Record action
            self._record_action("reroll", {"pid": player.pid, "cost": 2})
            
            return True
        except Exception:
            logger.exception("EngineAdapter.perform_reroll failed for player_index=%s", player_index)
            return False

    def perform_placement(self, player_index: int, hand_index: int, coord: Tuple[int, int], rotation: int) -> ActionResult:
        try:
            player = self.get_player(player_index)
            if not player:
                return ActionResult.ERR_ENGINE_EXCEPTION

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

            # Actual Card object handling
            if isinstance(card, str):
                # Fallback: create a card if we somehow got a string (should not happen in production)
                card_template = getattr(self._engine, "card_by_name", {}).get(card)
                if card_template:
                    card = card_template.clone()
                    card.uid = self._engine.next_card_uid()
                else:
                    logger.error("Could not resolve card name %s to Card object", card)
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
        if hasattr(self._engine, "get_hp"):
            hp = self._engine.get_hp(index)
            if isinstance(hp, (int, float)):
                return int(hp)
        player = self.get_player(index)
        return self._coerce_int(getattr(player, "hp", 0), default=0)

    def get_player_gold(self, index: int) -> int:
        player = self.get_player(index)
        return self._coerce_int(getattr(player, "gold", 0), default=0)

    def get_alive_players(self) -> List[Any]:
        return [player for player in self._engine.players if player.alive]

    def get_all_players(self) -> List[Any]:
        return self._engine.players

    def get_last_results(self) -> List[Dict[str, Any]]:
        results = getattr(self._engine, "last_combat_results", [])
        return results if isinstance(results, list) else []

    def get_pool_copies(self) -> Dict[str, int]:
        market = self.get_market()
        return dict(market.pool_copies) if market else {}

    def toggle_lock_shop(self, player_index: int) -> None:
        """Directly toggle shop_locked on the player — no longer delegates to Game."""
        player = self.get_player(player_index)
        if player is None:
            return
        player.shop_locked = not getattr(player, "shop_locked", False)

    def is_shop_locked(self, player_index: int) -> bool:
        player = self.get_player(player_index)
        if player is None:
            return False
        return bool(getattr(player, "shop_locked", False))

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
        player = self.get_player(player_index)
        board = getattr(player, "board", None) if player is not None else None
        if board is None or not hasattr(board, "remove"):
            return
        for coord in coords:
            board.remove(coord)

    def get_eliminated_coords(self, player_index: int) -> list:
        player = self.get_player(player_index)
        board = getattr(player, "board", None) if player is not None else None
        grid = getattr(board, "grid", None)
        if not isinstance(grid, dict):
            return []
        return [coord for coord, card in grid.items() if hasattr(card, "is_eliminated") and card.is_eliminated()]

    def get_passive_buff_log(self, player_index: int) -> list:
        player = self.get_player(player_index)
        if player is None:
            return []
        return list(getattr(player, "passive_buff_log", []))

    def get_rarity_weight(self, rarity: str, turn: int) -> float:
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
        """
        if player_index >= len(self._engine.players):
            return [None] * 6
        hand = self._engine.players[player_index].hand
        # None dahil tüm slotları koru; position integrity bozulmasın
        result = [
            (c.name if hasattr(c, "name") else str(c)) if c is not None else None
            for c in hand[:6]
        ]
        return result + [None] * max(0, 6 - len(result))

    def reroll_market(self, player_index: int = 0, cost: int = 2) -> bool:
        """Spend `cost` gold to refresh the market window for the player.
        Returns True on success, False if the player cannot afford it.
        Delegates to perform_reroll() for cost=2; handles custom cost inline."""
        if cost == 2:
            return self.perform_reroll(player_index)
        # Custom cost path (future use)
        player = self.get_player(player_index)
        if not player or player.gold < cost:
            return False
        player.gold -= cost
        self._engine.market.deal_market_window(player, 5)
        return True

    def get_display_name(self, pid: int) -> str:
        """Return the UI-friendly name for a player. Avoids AttributeError on
        players that only have .pid (not .name)."""
        for p in self._engine.players:
            if p.pid == pid:
                return getattr(p, "name", f"P{pid}")
        return f"P{pid}"