"""
Action System

Command pattern implementation for all game state modifications.

CRITICAL: This layer enables undo/redo, replay, network sync, and AI integration.
All modifications to CoreGameState MUST go through Actions.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .core_game_state import CoreGameState
    from .animation_system import AnimationSystem


class Action(ABC):
    """Base class for all game actions.
    
    Actions represent state modifications in a replayable, undoable way.
    
    Key Principles:
    - Actions modify CoreGameState (not UIState)
    - Actions spawn animations for visual feedback
    - Actions can be undone
    - Actions are serializable for replay/network
    """
    
    @abstractmethod
    def execute(self, core_game_state: 'CoreGameState', 
                animation_system: Optional['AnimationSystem'] = None) -> bool:
        """Execute action, modify state, spawn animations.
        
        Args:
            core_game_state: Game state to modify
            animation_system: System to spawn animations (optional)
        
        Returns:
            True if action succeeded, False otherwise
        """
        pass
    
    @abstractmethod
    def undo(self, core_game_state: 'CoreGameState') -> None:
        """Undo action (for undo/redo support).
        
        Args:
            core_game_state: Game state to restore
        """
        pass
    
    def can_execute(self, core_game_state: 'CoreGameState') -> bool:
        """Check if action can be executed.
        
        Override this for validation logic.
        
        Args:
            core_game_state: Game state to check
        
        Returns:
            True if action can be executed
        """
        return True


class BuyCardAction(Action):
    """Action to buy a card from the shop.
    
    Modifies:
    - Player gold (decrease)
    - Player hand (add card)
    - Market pool (decrease card count)
    - Player stats (track purchases)
    """
    
    def __init__(self, shop_idx: int, cost: int):
        """Initialize buy card action.
        
        Args:
            shop_idx: Index of card in shop window
            cost: Cost of the card
        """
        self.shop_idx = shop_idx
        self.cost = cost
        
        # For undo support
        self.card = None
        self.prev_gold = 0
        self.dropped_card = None
    
    def can_execute(self, core_game_state: 'CoreGameState') -> bool:
        """Check if player can afford the card.
        
        Args:
            core_game_state: Game state to check
        
        Returns:
            True if player has enough gold
        """
        player = core_game_state.current_player
        return player.gold >= self.cost
    
    def execute(self, core_game_state: 'CoreGameState', 
                animation_system: Optional['AnimationSystem'] = None) -> bool:
        """Buy card and spawn animation.
        
        Args:
            core_game_state: Game state to modify
            animation_system: System to spawn animations
        
        Returns:
            True if purchase succeeded
        """
        player = core_game_state.current_player
        market = core_game_state.game.market
        
        # Get player's market window
        if not hasattr(market, '_player_windows'):
            return False
        
        window = market._player_windows.get(player.pid, [])
        
        # Validate index
        if self.shop_idx >= len(window):
            return False
        
        card = window[self.shop_idx]
        
        # Validate gold
        if player.gold < self.cost:
            return False
        
        # Save state for undo
        self.card = card
        self.prev_gold = player.gold
        
        # Execute purchase
        player.gold -= self.cost
        player.stats["gold_spent"] = player.stats.get("gold_spent", 0) + self.cost
        
        # Clone card and add to hand
        cloned = card.clone()
        player.hand.append(cloned)
        player.copies[card.name] = player.copies.get(card.name, 0) + 1
        player.cards_bought_this_turn += 1
        player.stats["cards_bought_this_turn"] = (
            player.stats.get("cards_bought_this_turn", 0) + 1
        )
        player._window_bought.append(card.name)
        
        # Handle hand overflow (max 6 cards)
        if len(player.hand) > 6:
            dropped = player.hand.pop(0)
            self.dropped_card = dropped
            if player.copies.get(dropped.name, 0) > 0:
                player.copies[dropped.name] -= 1
            if hasattr(market, "pool_copies"):
                market.pool_copies[dropped.name] = market.pool_copies.get(dropped.name, 0) + 1
            player.stats["cards_dropped"] = player.stats.get("cards_dropped", 0) + 1
        
        # Mark card as bought in window (don't remove yet - that's for market.return_unsold)
        # The window will be cleaned up when player leaves shop
        
        # Spawn animation if system provided
        if animation_system is not None:
            from .animation_system import CardMoveAnimation
            # TODO: Get actual positions from renderer
            start_pos = (400, 300)  # Shop card position
            end_pos = (100, 800)    # Hand position
            anim = CardMoveAnimation(cloned, start_pos, end_pos, duration_ms=400)
            animation_system.add(anim)
        
        return True
    
    def undo(self, core_game_state: 'CoreGameState') -> None:
        """Restore gold and return card.
        
        Args:
            core_game_state: Game state to restore
        """
        player = core_game_state.current_player
        market = core_game_state.game.market
        
        # Restore gold
        player.gold = self.prev_gold
        player.stats["gold_spent"] = player.stats.get("gold_spent", 0) - self.cost
        
        # Remove card from hand
        if self.card and self.card.name in [c.name for c in player.hand]:
            # Find and remove the card
            for i, c in enumerate(player.hand):
                if c.name == self.card.name:
                    player.hand.pop(i)
                    break
        
        # Restore dropped card if any
        if self.dropped_card:
            player.hand.insert(0, self.dropped_card)
            player.copies[self.dropped_card.name] = player.copies.get(self.dropped_card.name, 0) + 1
        
        # Update stats
        player.copies[self.card.name] = max(0, player.copies.get(self.card.name, 0) - 1)
        player.cards_bought_this_turn = max(0, player.cards_bought_this_turn - 1)


class PlaceCardAction(Action):
    """Action to place a card on the board.
    
    Modifies:
    - Player hand (remove card)
    - Player board (add card at position)
    """
    
    def __init__(self, hand_idx: int, coord: tuple, rotation: int):
        """Initialize place card action.
        
        Args:
            hand_idx: Index of card in hand
            coord: (q, r) hex coordinate to place card
            rotation: Card rotation (0-5)
        """
        self.hand_idx = hand_idx
        self.coord = coord
        self.rotation = rotation
        
        # For undo support
        self.card = None
        self.prev_board_state = None
    
    def execute(self, core_game_state: 'CoreGameState', 
                animation_system: Optional['AnimationSystem'] = None) -> bool:
        """Place card and spawn animation.
        
        Args:
            core_game_state: Game state to modify
            animation_system: System to spawn animations
        
        Returns:
            True if placement succeeded
        """
        player = core_game_state.current_player
        
        # Validate hand index
        if self.hand_idx >= len(player.hand):
            return False
        
        card = player.hand[self.hand_idx]
        
        # Save state for undo (would need proper board serialization)
        self.card = card
        # self.prev_board_state = player.board.copy()  # TODO: Implement board copy
        
        # Execute placement
        # TODO: Implement actual board placement logic
        # success = player.board.place_card(card, self.coord, self.rotation)
        success = True  # Placeholder
        
        if success:
            # Remove from hand
            player.hand.pop(self.hand_idx)
            
            # Spawn animation if system provided
            if animation_system is not None:
                from .animation_system import CardMoveAnimation
                # TODO: Get actual positions
                start_pos = (100, 800)  # Hand position
                end_pos = (400, 400)    # Board position
                anim = CardMoveAnimation(card, start_pos, end_pos, duration_ms=300)
                animation_system.add(anim)
        
        return success
    
    def undo(self, core_game_state: 'CoreGameState') -> None:
        """Restore previous board state.
        
        Args:
            core_game_state: Game state to restore
        """
        player = core_game_state.current_player
        
        # Restore board state
        # player.board = self.prev_board_state  # TODO: Implement
        
        # Restore card to hand
        if self.card:
            player.hand.insert(self.hand_idx, self.card)


class ActionSystem:
    """Manages action execution and history.
    
    Responsibilities:
    - Execute actions
    - Maintain action history for undo
    - Maintain redo stack
    - Provide undo/redo functionality
    """
    
    def __init__(self):
        """Initialize action system."""
        self.history: List[Action] = []
        self.redo_stack: List[Action] = []
    
    def execute(self, action: Action, core_game_state: 'CoreGameState', 
                animation_system: Optional['AnimationSystem'] = None) -> bool:
        """Execute action and add to history.
        
        Args:
            action: Action to execute
            core_game_state: Game state to modify
            animation_system: System to spawn animations
        
        Returns:
            True if action succeeded
        """
        # Check if action can be executed
        if not action.can_execute(core_game_state):
            return False
        
        # Execute action
        success = action.execute(core_game_state, animation_system)
        
        if success:
            self.history.append(action)
            self.redo_stack.clear()  # Clear redo stack on new action
        
        return success
    
    def undo(self, core_game_state: 'CoreGameState') -> bool:
        """Undo last action.
        
        Args:
            core_game_state: Game state to restore
        
        Returns:
            True if undo succeeded
        """
        if not self.history:
            return False
        
        action = self.history.pop()
        action.undo(core_game_state)
        self.redo_stack.append(action)
        
        return True
    
    def redo(self, core_game_state: 'CoreGameState', 
             animation_system: Optional['AnimationSystem'] = None) -> bool:
        """Redo last undone action.
        
        Args:
            core_game_state: Game state to modify
            animation_system: System to spawn animations
        
        Returns:
            True if redo succeeded
        """
        if not self.redo_stack:
            return False
        
        action = self.redo_stack.pop()
        success = action.execute(core_game_state, animation_system)
        
        if success:
            self.history.append(action)
        
        return success
    
    def can_undo(self) -> bool:
        """Check if undo is available.
        
        Returns:
            True if there are actions to undo
        """
        return len(self.history) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available.
        
        Returns:
            True if there are actions to redo
        """
        return len(self.redo_stack) > 0
    
    def clear(self) -> None:
        """Clear all history and redo stack.
        
        Useful for scene transitions or when starting a new turn.
        """
        self.history.clear()
        self.redo_stack.clear()
