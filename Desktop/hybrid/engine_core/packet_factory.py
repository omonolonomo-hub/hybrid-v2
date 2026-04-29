"""
Packet Factory - Centralized packet creation and parsing.

All network message schemas are defined here for consistency and testability.
"""

import json
from typing import Any


class PacketFactory:
    """Factory for creating and parsing network packets."""

    @staticmethod
    def make_join(pid: int) -> str:
        """Create a join packet.
        
        Args:
            pid: Player ID
            
        Returns:
            JSON string representing the join packet
        """
        return json.dumps({
            "type": "join",
            "pid": pid
        })

    @staticmethod
    def make_action(action: dict) -> str:
        """Create an action packet.
        
        Args:
            action: Action dictionary containing action details
            
        Returns:
            JSON string representing the action packet
        """
        return json.dumps({
            "type": "action",
            "action": action
        })

    @staticmethod
    def make_snapshot(state_dict: dict) -> str:
        """Create a snapshot packet.
        
        Args:
            state_dict: Game state dictionary
            
        Returns:
            JSON string representing the snapshot packet
        """
        return json.dumps({
            "type": "snapshot",
            "state": state_dict
        })

    @staticmethod
    def make_action_result(ok: bool, error: str | None = None) -> str:
        """Create an action result packet.
        
        Args:
            ok: Whether the action succeeded
            error: Error message if action failed
            
        Returns:
            JSON string representing the action result packet
        """
        return json.dumps({
            "type": "action_result",
            "ok": ok,
            "error": error
        })

    @staticmethod
    def make_game_start(seed: int | None = None) -> str:
        """Create a game start packet.
        
        Args:
            seed: Random seed for the game (optional)
            
        Returns:
            JSON string representing the game start packet
        """
        return json.dumps({
            "type": "game_start",
            "seed": seed
        })

    @staticmethod
    def parse(raw: str) -> dict[str, Any]:
        """Parse a raw packet string into a dictionary.
        
        Args:
            raw: Raw JSON string
            
        Returns:
            Parsed packet dictionary
            
        Raises:
            json.JSONDecodeError: If the string is not valid JSON
        """
        return json.loads(raw)
