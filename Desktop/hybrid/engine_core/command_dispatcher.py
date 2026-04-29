"""CommandDispatcher interface — abstracts mutation commands for local/network execution.

This module defines the ICommandDispatcher protocol that decouples command execution
from the EngineAdapter. Implementations can be local (direct delegation) or networked
(serialization + RPC).

DESIGN RATIONALE:
- Zero behavior change: LocalCommandDispatcher is a transparent pass-through
- Network-ready: Interface designed for future NetworkCommandDispatcher
- Type-safe: Uses ActionResult enum and explicit signatures
"""

from abc import ABC, abstractmethod
from typing import Tuple

from v2.core.action_result import ActionResult


class ICommandDispatcher(ABC):
    """Abstract interface for dispatching mutation commands to the game engine.
    
    Implementations:
    - LocalCommandDispatcher: Direct delegation to EngineAdapter (v2/core/local_dispatcher.py)
    - NetworkCommandDispatcher: TODO — serialize commands and send over network
    
    All methods must maintain exact signature compatibility with EngineAdapter.
    """

    @abstractmethod
    def perform_buy_card(self, player_index: int, slot_index: int) -> ActionResult:
        """Purchase a card from the shop.
        
        Args:
            player_index: Player performing the purchase (0 = human)
            slot_index: Shop slot index (0-4)
            
        Returns:
            ActionResult enum indicating success or failure reason
        """
        pass

    @abstractmethod
    def perform_reroll(self, player_index: int) -> bool:
        """Spend 2 gold to refresh the market window.
        
        Args:
            player_index: Player performing the reroll (0 = human)
            
        Returns:
            True if reroll succeeded, False if insufficient gold
        """
        pass

    @abstractmethod
    def perform_placement(
        self, 
        player_index: int, 
        hand_index: int, 
        coord: Tuple[int, int], 
        rotation: int
    ) -> ActionResult:
        """Place a card from hand onto the board.
        
        Args:
            player_index: Player performing the placement (0 = human)
            hand_index: Hand slot index (0-5)
            coord: Board coordinate tuple (q, r)
            rotation: Card rotation (0-5)
            
        Returns:
            ActionResult enum indicating success or failure reason
        """
        pass
