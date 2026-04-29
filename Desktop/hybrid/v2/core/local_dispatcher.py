"""LocalCommandDispatcher — direct delegation to EngineAdapter with zero overhead.

This implementation provides a transparent pass-through to EngineAdapter mutation methods.
No network code, no serialization, no behavior changes — just interface compliance.

DESIGN RATIONALE:
- Single responsibility: Only delegates, never adds logic
- Zero overhead: Direct method calls, no intermediate processing
- Type-safe: Enforces ICommandDispatcher contract
- Future-proof: Same interface will be used by NetworkCommandDispatcher
"""

import logging
from typing import TYPE_CHECKING, Tuple

from engine_core.command_dispatcher import ICommandDispatcher
from v2.core.action_result import ActionResult

if TYPE_CHECKING:
    from v2.core.engine_adapter import EngineAdapter

logger = logging.getLogger(__name__)


class LocalCommandDispatcher(ICommandDispatcher):
    """Local implementation of ICommandDispatcher — delegates directly to EngineAdapter.
    
    This class is a transparent wrapper around EngineAdapter mutation methods.
    It exists solely to satisfy the ICommandDispatcher interface for local execution.
    
    Usage:
        adapter = EngineAdapter(engine)
        dispatcher = LocalCommandDispatcher(adapter)
        result = dispatcher.perform_buy_card(0, 2)
    
    Thread-safety: Not thread-safe (same as EngineAdapter)
    Network: No network code — purely local execution
    """

    def __init__(self, adapter: "EngineAdapter"):
        """Initialize dispatcher with an EngineAdapter instance.
        
        Args:
            adapter: EngineAdapter instance to delegate commands to
        """
        self._adapter = adapter

    def perform_buy_card(self, player_index: int, slot_index: int) -> ActionResult:
        """Delegate buy_card to EngineAdapter — no additional logic."""
        return self._adapter.perform_buy_card(player_index, slot_index)

    def perform_reroll(self, player_index: int) -> bool:
        """Delegate reroll to EngineAdapter — no additional logic."""
        return self._adapter.perform_reroll(player_index)

    def perform_placement(
        self, 
        player_index: int, 
        hand_index: int, 
        coord: Tuple[int, int], 
        rotation: int
    ) -> ActionResult:
        """Delegate placement to EngineAdapter — no additional logic."""
        return self._adapter.perform_placement(player_index, hand_index, coord, rotation)
