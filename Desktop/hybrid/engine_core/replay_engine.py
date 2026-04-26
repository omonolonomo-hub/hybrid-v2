"""
engine_core/replay_engine.py
═══════════════════════════════════════════════════════════════════
Replay Engine.

Executes ActionLog entries on a Game instance to reproduce 
identical state for analysis or spectating.
═══════════════════════════════════════════════════════════════════
"""

import logging
from typing import Any, Dict, List, Optional
from engine_core.action_log import ActionLog, ActionEntry

logger = logging.getLogger(__name__)

class ReplayEngine:
    def __init__(self, game: Any):
        self.game = game
        self.log: Optional[ActionLog] = None
        self.current_entry_idx = 0

    def load_log(self, log: ActionLog):
        self.log = log
        self.current_entry_idx = 0
        if log.seed is not None:
            # We assume the game is already initialized with this seed
            # or we need a way to reset the game with this seed.
            pass

    def step(self) -> bool:
        """Executes the next entry in the log. Returns False if end of log."""
        if not self.log or self.current_entry_idx >= len(self.log.entries):
            return False

        entry = self.log.entries[self.current_entry_idx]
        self._execute_entry(entry)
        self.current_entry_idx += 1
        return True

    def run_until(self, turn: int, sub_turn: Optional[int] = None) -> None:
        """Runs the log until reaching the specified turn/sub-turn."""
        while self.current_entry_idx < len(self.log.entries):
            entry = self.log.entries[self.current_entry_idx]
            if entry.turn > turn:
                break
            if entry.turn == turn and sub_turn is not None and entry.sub_turn >= sub_turn:
                break
            
            self._execute_entry(entry)
            self.current_entry_idx += 1

    def _execute_entry(self, entry: ActionEntry):
        """Dispatches action to the game engine."""
        atype = entry.action_type
        params = entry.params

        logger.debug(f"Replaying action: {atype} with {params}")

        if atype == "turn_start":
            # In replay, we might need to manually trigger things 
            # that TurnManager normally does automatically.
            pass
        elif atype == "market_deal":
            # Force the market to deal these specific cards to the player
            pid = params["pid"]
            card_names = params["cards"]
            # Implementation depends on internal Market/Game methods
            pass
        elif atype == "buy_card":
            pid = params["pid"]
            slot = params["slot"]
            # Execute buy
            pass
        elif atype == "place_card":
            pid = params["pid"]
            # Execute place
            pass
        elif atype == "combat_start":
            # Run combat with the recorded pairs
            pass
        # ... more action types ...
