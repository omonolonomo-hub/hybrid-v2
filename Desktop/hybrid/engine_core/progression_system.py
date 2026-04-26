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
    def check_copy_strengthening(player: Any, turn: int, trigger_passive_fn=None):
        """
        Checks if any cards in player's inventory copies meet the thresholds 
        for strengthening on the board.
        """
        board = player.board
        inventory = player.inventory
        
        thresholds = COPY_THRESH_C if board.has_catalyst else COPY_THRESH
        grid_vals = list(board.grid.values())
        _ctx = {
            "turn": turn, 
            "game": player.game,
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
    def check_evolution(player: Any, market=None, card_by_name=None) -> List[str]:
        """
        Handles card evolution logic for players with the 'evolver' strategy.
        """
        if player.strategy != "evolver":
            return []
            
        inventory = player.inventory
        board = player.board
        progression = player.progression
        
        evolved_names = []
        for base_name, count in list(inventory.copies.items()):
            if count < EVOLVE_COPIES_REQUIRED:
                continue
            if inventory.copies.get(f"Evolved {base_name}", 0) > 0:
                continue
            if card_by_name is None:
                continue
                
            base_template = card_by_name.get(base_name)
            if base_template is None:
                continue

            removed = 0
            # Remove from hand
            for i in range(len(inventory.hand)):
                if removed >= 2:
                    break
                card = inventory.hand[i]
                if card is not None and card.name == base_name:
                    inventory.hand[i] = None
                    removed += 1
                    if market:
                        market.pool_copies[base_name] = market.pool_copies.get(base_name, 0) + 1

            # Remove from board if needed
            if removed < 2:
                for coord, card in list(board.grid.items()):
                    if removed >= 2:
                        break
                    if card.name == base_name:
                        board.remove(coord)
                        removed += 1
                        if market:
                            market.pool_copies[base_name] = market.pool_copies.get(base_name, 0) + 1

            inventory.copies[base_name] = max(0, inventory.copies.get(base_name, 0) - 2)
            evolved = evolve_card(base_template)
            if player.game:
                evolved.uid = player.game.next_card_uid()

            # Evolution bonus
            try:
                rarity_int = int(base_template.rarity)
                if 3 <= rarity_int <= 5:
                    bonus_pct = 0.04 * rarity_int
                    evolved.strengthen(int(round(evolved.total_power() * bonus_pct)))
            except (ValueError, TypeError):
                pass

            # Replace on board or hand
            replaced = False
            for coord, card in list(board.grid.items()):
                if card.name == base_name:
                    board.place(coord, evolved)
                    replaced = True
                    break
            if not replaced:
                for i, card in enumerate(inventory.hand):
                    if card is not None and card.name == base_name:
                        inventory.hand[i] = evolved
                        replaced = True
                        break
                if not replaced:
                    inventory.add_to_hand(evolved)

            inventory.copies[f"Evolved {base_name}"] = inventory.copies.get(f"Evolved {base_name}", 0) + 1
            player.stats["evolutions"] = player.stats.get("evolutions", 0) + 1
            evolved_names.append(base_name)
            progression.record_evolution(base_name, player.turns_played if player.turns_played > 0 else 1)
            
        return evolved_names
