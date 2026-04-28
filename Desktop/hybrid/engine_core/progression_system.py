"""
ProgressionSystem Module

Handles evolution and copy strengthening logic for players.
"""

from typing import List, Dict, Optional, Any
from engine_core.constants import (
    COPY_THRESH, COPY_THRESH_C, EVOLVE_COPIES_REQUIRED
)
from engine_core.card import evolve_card

class ProgressionSystem:
    @staticmethod
    def check_copy_strengthening(player: Any, turn: int, trigger_passive_fn=None, game_ref=None):
        """
        Checks if any cards in player's inventory copies meet the thresholds 
        for strengthening on the board.
        
        Args:
            player: Player instance
            turn: Current turn number
            trigger_passive_fn: Passive trigger callback
            game_ref: Game instance reference (replaces player.game)
        """
        board = player.board
        inventory = player.inventory
        
        thresholds = COPY_THRESH_C if board.has_catalyst else COPY_THRESH
        grid_vals = list(board.grid.values())
        _ctx = {
            "turn": turn, 
            "game": game_ref,  # Explicit context injection
            "market_window": getattr(player, "market", []) # Compatibility
        }

        for name, count in inventory.copies.items():
            if not any(c.name == name for c in grid_vals):
                continue
            
            t = inventory.copy_turns.get(name, 0) + 1
            inventory.copy_turns[name] = t

            if name not in inventory.copy_applied:
                inventory.copy_applied[name] = {"2": False, "3": False}
            applied = inventory.copy_applied[name]

            for thresh_idx, thresh_val in [(0, "2"), (1, "3")]:
                if count >= (thresh_idx + 2) and t >= thresholds[thresh_idx] and not applied[thresh_val]:
                    for card in grid_vals:
                        if card.name == name:
                            card.strengthen(int(thresh_val))
                            if trigger_passive_fn:
                                trigger_passive_fn(card, f"copy_{thresh_val}", player, None, _ctx, verbose=False)
                    applied[thresh_val] = True
                    player.stats["copies_created"] += 1

    @staticmethod
    def check_evolution(player: Any, market=None, card_by_name=None, next_uid_fn=None) -> List[str]:
        """
        Handles card evolution logic for players with the 'evolver' strategy.
        
        ATOMIC GUARANTEE: Evolved card is fully created and validated BEFORE 
        base cards are removed. If evolution fails, no state corruption occurs.
        
        Args:
            player: Player instance
            market: Market instance (for pool management)
            card_by_name: Dict mapping card names to Card templates
            next_uid_fn: Function to generate unique card IDs (replaces player.game.next_card_uid)
        
        Returns:
            List of base card names that were evolved
        """
        # Early exit: avoid unnecessary work for 7/8 players every turn
        if player.strategy != "evolver":
            return []
        
        # Early exit: missing dependencies
        if card_by_name is None:
            return []
        
        # Fallback UID generator for backward compatibility
        if next_uid_fn is None:
            _uid_counter = [0]
            def next_uid_fn():
                _uid_counter[0] += 1
                return f"evo_{_uid_counter[0]}"
            
        inventory = player.inventory
        board = player.board
        progression = player.progression
        
        evolved_names = []
        for base_name, count in list(inventory.copies.items()):
            if count < EVOLVE_COPIES_REQUIRED:
                continue
            if inventory.copies.get(f"Evolved {base_name}", 0) > 0:
                continue
                
            base_template = card_by_name.get(base_name)
            if base_template is None:
                continue

            # ═══════════════════════════════════════════════════════════════
            # ATOMIC PHASE 1: Create evolved card FIRST (no state mutation)
            # ═══════════════════════════════════════════════════════════════
            try:
                evolved = evolve_card(base_template)
                evolved.uid = next_uid_fn()
                
                # Evolution bonus
                try:
                    rarity_int = int(base_template.rarity)
                    if 3 <= rarity_int <= 5:
                        bonus_pct = 0.04 * rarity_int
                        evolved.strengthen(int(round(evolved.total_power() * bonus_pct)))
                except (ValueError, TypeError):
                    pass
                    
            except Exception as e:
                # Evolution failed — no state was mutated, safe to continue
                print(f"[ProgressionSystem] Evolution failed for {base_name}: {e}")
                continue

            # ═══════════════════════════════════════════════════════════════
            # ATOMIC PHASE 2: Remove base cards (state mutation begins)
            # ═══════════════════════════════════════════════════════════════
            _remove_base_cards(player, base_name, count=2, market=market)

            # ═══════════════════════════════════════════════════════════════
            # ATOMIC PHASE 3: Place evolved card
            # ═══════════════════════════════════════════════════════════════
            # Place evolved card in first available slot (fills None slots first via add_to_hand)
            # Note: add_to_hand() automatically increments copies[evolved.name]
            inventory.add_to_hand(evolved)
            
            # Compact hand: remove trailing None slots for cleaner state
            while inventory.hand and inventory.hand[-1] is None:
                inventory.hand.pop()

            # Update tracking (copies already updated by add_to_hand)
            player.stats["evolutions"] = player.stats.get("evolutions", 0) + 1
            evolved_names.append(base_name)
            progression.record_evolution(base_name, player.turns_played if player.turns_played > 0 else 1)
            
        return evolved_names


def _remove_base_cards(player: Any, card_name: str, count: int, market=None):
    """
    Atomically removes 'count' copies of 'card_name' from player's hand/board.
    
    This is a separate function to ensure removal logic is isolated and testable.
    Used by check_evolution to maintain atomic guarantees.
    
    Args:
        player: Player instance
        card_name: Name of card to remove
        count: Number of copies to remove
        market: Optional market instance for pool management
    """
    inventory = player.inventory
    board = player.board
    removed = 0
    
    # Remove from hand first
    for i in range(len(inventory.hand)):
        if removed >= count:
            break
        card = inventory.hand[i]
        if card is not None and card.name == card_name:
            inventory.clear_slot(i)
            removed += 1
            if market:
                market.pool_copies[card_name] = market.pool_copies.get(card_name, 0) + 1

    # Remove from board if needed
    if removed < count:
        for coord, card in list(board.grid.items()):
            if removed >= count:
                break
            if card.name == card_name:
                board.remove(coord)
                removed += 1
                if market:
                    market.pool_copies[card_name] = market.pool_copies.get(card_name, 0) + 1

    # Update copy count
    inventory.copies[card_name] = max(0, inventory.copies.get(card_name, 0) - count)
