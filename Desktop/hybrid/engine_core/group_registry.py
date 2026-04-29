"""
engine_core/group_registry.py
═══════════════════════════════════════════════════════════════════
Group Registry — Single Source of Truth for Group Definitions

This module centralizes all group-related metadata:
  • Group names
  • Stats belonging to each group
  • Rock-paper-scissors relationships (GROUP_BEATS)
  • Display colors (for UI)

Before: GROUPS tuple scattered across synergy.py, combo_detector.py
        GROUP_BEATS dict in constants.py
        STAT_GROUPS dict in constants.py

After:  Single registry with GroupDefinition dataclass
        Adding a new group = one line in REGISTRY
        No code changes needed elsewhere

Usage:
    from engine_core.group_registry import GroupRegistry
    
    # Get all group names
    groups = GroupRegistry.all_groups()  # ("MIND", "CONNECTION", "EXISTENCE")
    
    # Get group definition
    mind = GroupRegistry.get("MIND")
    print(mind.stats)  # ["Meaning", "Secret", "Intelligence", "Trace"]
    print(mind.beats)  # "EXISTENCE"
    
    # Get what beats what
    winner = GroupRegistry.get_winner("MIND", "EXISTENCE")  # "MIND"
    
    # Get stat-to-group mapping
    group = GroupRegistry.stat_to_group("Power")  # "EXISTENCE"
═══════════════════════════════════════════════════════════════════
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class GroupDefinition:
    """
    Immutable definition of a stat group.
    
    Attributes:
        name: Group identifier (e.g., "MIND")
        stats: List of stat names belonging to this group
        beats: Name of the group this group defeats in combat (+1 bonus)
        color: Hex color code for UI display (optional)
    """
    name: str
    stats: Tuple[str, ...]
    beats: str
    color: str = "#FFFFFF"
    
    def __post_init__(self):
        # Ensure stats is a tuple for immutability
        if not isinstance(self.stats, tuple):
            object.__setattr__(self, 'stats', tuple(self.stats))


# ═══════════════════════════════════════════════════════════════════
# GROUP REGISTRY — Add new groups here
# ═══════════════════════════════════════════════════════════════════

_REGISTRY: Dict[str, GroupDefinition] = {
    "MIND": GroupDefinition(
        name="MIND",
        stats=("Meaning", "Secret", "Intelligence", "Trace"),
        beats="EXISTENCE",
        color="#9B59B6",  # Purple
    ),
    "CONNECTION": GroupDefinition(
        name="CONNECTION",
        stats=("Gravity", "Harmony", "Spread", "Prestige"),
        beats="MIND",
        color="#3498DB",  # Blue
    ),
    "EXISTENCE": GroupDefinition(
        name="EXISTENCE",
        stats=("Power", "Durability", "Size", "Speed"),
        beats="CONNECTION",
        color="#E74C3C",  # Red
    ),
}


# ═══════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════

class GroupRegistry:
    """
    Static registry for group definitions.
    All methods are class methods — no instantiation needed.
    """
    
    @classmethod
    def all_groups(cls) -> Tuple[str, ...]:
        """
        Get tuple of all group names.
        
        Returns:
            Tuple of group names in registry order
            
        Example:
            >>> GroupRegistry.all_groups()
            ('MIND', 'CONNECTION', 'EXISTENCE')
        """
        return tuple(_REGISTRY.keys())
    
    @classmethod
    def get(cls, group_name: str) -> GroupDefinition:
        """
        Get group definition by name.
        
        Args:
            group_name: Name of the group (e.g., "MIND")
            
        Returns:
            GroupDefinition instance
            
        Raises:
            KeyError: If group_name not found in registry
            
        Example:
            >>> mind = GroupRegistry.get("MIND")
            >>> mind.stats
            ('Meaning', 'Secret', 'Intelligence', 'Trace')
        """
        return _REGISTRY[group_name]
    
    @classmethod
    def stat_to_group(cls, stat_name: str) -> Optional[str]:
        """
        Get group name for a given stat.
        
        Args:
            stat_name: Name of the stat (e.g., "Power")
            
        Returns:
            Group name or None if stat not found
            
        Example:
            >>> GroupRegistry.stat_to_group("Power")
            'EXISTENCE'
            >>> GroupRegistry.stat_to_group("Unknown")
            None
        """
        for group_def in _REGISTRY.values():
            if stat_name in group_def.stats:
                return group_def.name
        return None
    
    @classmethod
    def get_stat_groups(cls) -> Dict[str, List[str]]:
        """
        Get STAT_GROUPS dict format (for backward compatibility).
        
        Returns:
            Dict mapping group name to list of stats
            
        Example:
            >>> GroupRegistry.get_stat_groups()
            {'MIND': ['Meaning', 'Secret', ...], ...}
        """
        return {
            group_def.name: list(group_def.stats)
            for group_def in _REGISTRY.values()
        }
    
    @classmethod
    def get_stat_to_group_map(cls) -> Dict[str, str]:
        """
        Get STAT_TO_GROUP dict format (for backward compatibility).
        
        Returns:
            Dict mapping stat name to group name
            
        Example:
            >>> GroupRegistry.get_stat_to_group_map()
            {'Power': 'EXISTENCE', 'Meaning': 'MIND', ...}
        """
        result = {}
        for group_def in _REGISTRY.values():
            for stat in group_def.stats:
                result[stat] = group_def.name
        return result
    
    @classmethod
    def get_beats_map(cls) -> Dict[str, str]:
        """
        Get GROUP_BEATS dict format (for backward compatibility).
        
        Returns:
            Dict mapping group name to the group it beats
            
        Example:
            >>> GroupRegistry.get_beats_map()
            {'MIND': 'EXISTENCE', 'CONNECTION': 'MIND', 'EXISTENCE': 'CONNECTION'}
        """
        return {
            group_def.name: group_def.beats
            for group_def in _REGISTRY.values()
        }
    
    @classmethod
    def get_winner(cls, group_a: str, group_b: str) -> Optional[str]:
        """
        Determine which group wins in combat (rock-paper-scissors).
        
        Args:
            group_a: First group name
            group_b: Second group name
            
        Returns:
            Name of winning group, or None if draw (same group or invalid)
            
        Example:
            >>> GroupRegistry.get_winner("MIND", "EXISTENCE")
            'MIND'
            >>> GroupRegistry.get_winner("MIND", "MIND")
            None
        """
        if group_a == group_b:
            return None
        
        try:
            group_a_def = cls.get(group_a)
            if group_a_def.beats == group_b:
                return group_a
            
            group_b_def = cls.get(group_b)
            if group_b_def.beats == group_a:
                return group_b
        except KeyError:
            return None
        
        return None
    
    @classmethod
    def beats(cls, group_a: str, group_b: str) -> bool:
        """
        Check if group_a beats group_b.
        
        Args:
            group_a: Attacker group name
            group_b: Defender group name
            
        Returns:
            True if group_a beats group_b
            
        Example:
            >>> GroupRegistry.beats("MIND", "EXISTENCE")
            True
            >>> GroupRegistry.beats("EXISTENCE", "MIND")
            False
        """
        try:
            group_a_def = cls.get(group_a)
            return group_a_def.beats == group_b
        except KeyError:
            return False


# ═══════════════════════════════════════════════════════════════════
# BACKWARD COMPATIBILITY EXPORTS
# ═══════════════════════════════════════════════════════════════════

# These can be imported directly for drop-in replacement:
#   from engine_core.group_registry import GROUPS, STAT_GROUPS, GROUP_BEATS

GROUPS = GroupRegistry.all_groups()
STAT_GROUPS = GroupRegistry.get_stat_groups()
STAT_TO_GROUP = GroupRegistry.get_stat_to_group_map()
GROUP_BEATS = GroupRegistry.get_beats_map()
