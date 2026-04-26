from typing import List, Dict, Optional
from engine_core.card import Card
from engine_core.constants import HAND_LIMIT

class Inventory:
    def __init__(self):
        self.hand: List[Card] = []
        self.copies: Dict[str, int] = {}
        self.copy_turns: Dict[str, int] = {}
        self.copy_applied: Dict[str, Dict[str, bool]] = {}
        self._on_change = None

    def _emit_change(self):
        if self._on_change:
            self._on_change()

    def add_to_hand(self, card: Card) -> Optional[Card]:
        """Adds card to hand. Fills first empty (None) slot if available, 
        otherwise appends. Returns dropped card if hand overflowed.
        """
        filled_slot = False
        # 1. Try to fill an existing None slot (positional integrity)
        for i in range(len(self.hand)):
            if self.hand[i] is None:
                self.hand[i] = card
                filled_slot = True
                break
        
        # 2. No None slot, append if not at limit or handle overflow
        if not filled_slot:
            self.hand.append(card)
            
        self.copies[card.name] = self.copies.get(card.name, 0) + 1
        
        dropped = None
        # Hand limit check (ignores None slots for actual count)
        actual_cards = [c for c in self.hand if c is not None]
        if len(actual_cards) > HAND_LIMIT:
            # Find the first actual card to drop (usually index 0)
            for i in range(len(self.hand)):
                if self.hand[i] is not None:
                    dropped = self.hand.pop(i)
                    break
                    
            if dropped is not None:
                if self.copies.get(dropped.name, 0) > 0:
                    self.copies[dropped.name] -= 1
        
        self._emit_change()
        return dropped

    def remove_from_hand(self, card_name: str) -> Optional[Card]:
        """Removes a card by name and leaves a None slot (positional integrity)."""
        for i, card in enumerate(self.hand):
            if card is not None and card.name == card_name:
                removed = self.hand[i]
                self.hand[i] = None
                self._emit_change()
                return removed
        return None

    def get_copy_count(self, card_name: str) -> int:
        return self.copies.get(card_name, 0)

    def clear_slot(self, index: int) -> None:
        """Clears a specific hand slot by index without shifting other cards.
        Maintains positional integrity for UI drag-drop.
        """
        if 0 <= index < len(self.hand):
            self.hand[index] = None
            self._emit_change()
    
    def clear_slots_batch(self, indices: List[int]) -> None:
        """Clears multiple hand slots without emitting signals for each.
        
        Emits only ONE signal after all slots are cleared, preventing
        N-signal emission when clearing N cards (e.g., during place_cards).
        
        Args:
            indices: List of slot indices to clear
        """
        for index in indices:
            if 0 <= index < len(self.hand):
                self.hand[index] = None
        # Single signal emission after all clears
        if indices:
            self._emit_change()
