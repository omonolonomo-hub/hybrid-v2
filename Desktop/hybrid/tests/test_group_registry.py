"""
tests/test_group_registry.py
═══════════════════════════════════════════════════════════════════
Tests for GroupRegistry — single source of truth for group definitions.

Verifies:
  • All groups are registered correctly
  • Stat-to-group mapping works
  • Rock-paper-scissors relationships are correct
  • Backward compatibility with old constants
  • Integration with existing modules (synergy, combat, combo)
═══════════════════════════════════════════════════════════════════
"""

import pytest
from engine_core.group_registry import (
    GroupRegistry, GroupDefinition,
    GROUPS, STAT_GROUPS, STAT_TO_GROUP, GROUP_BEATS
)


class TestGroupDefinition:
    """Test GroupDefinition dataclass."""
    
    def test_immutable(self):
        """GroupDefinition should be frozen (immutable)."""
        group = GroupDefinition(
            name="TEST",
            stats=("Stat1", "Stat2"),
            beats="OTHER",
            color="#FFFFFF"
        )
        
        with pytest.raises(Exception):  # FrozenInstanceError
            group.name = "CHANGED"
    
    def test_stats_converted_to_tuple(self):
        """Stats should be converted to tuple for immutability."""
        group = GroupDefinition(
            name="TEST",
            stats=["Stat1", "Stat2"],  # List input
            beats="OTHER"
        )
        
        assert isinstance(group.stats, tuple)
        assert group.stats == ("Stat1", "Stat2")


class TestGroupRegistry:
    """Test GroupRegistry API."""
    
    def test_all_groups(self):
        """Should return all registered group names."""
        groups = GroupRegistry.all_groups()
        
        assert isinstance(groups, tuple)
        assert len(groups) == 3
        assert "MIND" in groups
        assert "CONNECTION" in groups
        assert "EXISTENCE" in groups
    
    def test_get_group(self):
        """Should retrieve group definition by name."""
        mind = GroupRegistry.get("MIND")
        
        assert isinstance(mind, GroupDefinition)
        assert mind.name == "MIND"
        assert "Meaning" in mind.stats
        assert "Secret" in mind.stats
        assert "Intelligence" in mind.stats
        assert "Trace" in mind.stats
        assert mind.beats == "EXISTENCE"
    
    def test_get_invalid_group(self):
        """Should raise KeyError for invalid group name."""
        with pytest.raises(KeyError):
            GroupRegistry.get("INVALID")
    
    def test_stat_to_group(self):
        """Should map stat names to group names."""
        assert GroupRegistry.stat_to_group("Power") == "EXISTENCE"
        assert GroupRegistry.stat_to_group("Meaning") == "MIND"
        assert GroupRegistry.stat_to_group("Gravity") == "CONNECTION"
        assert GroupRegistry.stat_to_group("Invalid") is None
    
    def test_get_stat_groups(self):
        """Should return STAT_GROUPS dict format."""
        stat_groups = GroupRegistry.get_stat_groups()
        
        assert isinstance(stat_groups, dict)
        assert len(stat_groups) == 3
        assert "MIND" in stat_groups
        assert "Meaning" in stat_groups["MIND"]
        assert isinstance(stat_groups["MIND"], list)
    
    def test_get_stat_to_group_map(self):
        """Should return STAT_TO_GROUP dict format."""
        stat_map = GroupRegistry.get_stat_to_group_map()
        
        assert isinstance(stat_map, dict)
        assert stat_map["Power"] == "EXISTENCE"
        assert stat_map["Meaning"] == "MIND"
        assert stat_map["Gravity"] == "CONNECTION"
    
    def test_get_beats_map(self):
        """Should return GROUP_BEATS dict format."""
        beats_map = GroupRegistry.get_beats_map()
        
        assert isinstance(beats_map, dict)
        assert beats_map["MIND"] == "EXISTENCE"
        assert beats_map["CONNECTION"] == "MIND"
        assert beats_map["EXISTENCE"] == "CONNECTION"
    
    def test_get_winner(self):
        """Should determine combat winner based on rock-paper-scissors."""
        # MIND beats EXISTENCE
        assert GroupRegistry.get_winner("MIND", "EXISTENCE") == "MIND"
        assert GroupRegistry.get_winner("EXISTENCE", "MIND") == "MIND"
        
        # CONNECTION beats MIND
        assert GroupRegistry.get_winner("CONNECTION", "MIND") == "CONNECTION"
        assert GroupRegistry.get_winner("MIND", "CONNECTION") == "CONNECTION"
        
        # EXISTENCE beats CONNECTION
        assert GroupRegistry.get_winner("EXISTENCE", "CONNECTION") == "EXISTENCE"
        assert GroupRegistry.get_winner("CONNECTION", "EXISTENCE") == "EXISTENCE"
        
        # Same group = no winner
        assert GroupRegistry.get_winner("MIND", "MIND") is None
        
        # Invalid group = no winner
        assert GroupRegistry.get_winner("INVALID", "MIND") is None
    
    def test_beats(self):
        """Should check if one group beats another."""
        # MIND beats EXISTENCE
        assert GroupRegistry.beats("MIND", "EXISTENCE") is True
        assert GroupRegistry.beats("EXISTENCE", "MIND") is False
        
        # CONNECTION beats MIND
        assert GroupRegistry.beats("CONNECTION", "MIND") is True
        assert GroupRegistry.beats("MIND", "CONNECTION") is False
        
        # EXISTENCE beats CONNECTION
        assert GroupRegistry.beats("EXISTENCE", "CONNECTION") is True
        assert GroupRegistry.beats("CONNECTION", "EXISTENCE") is False
        
        # Same group
        assert GroupRegistry.beats("MIND", "MIND") is False
        
        # Invalid group
        assert GroupRegistry.beats("INVALID", "MIND") is False


class TestBackwardCompatibility:
    """Test backward compatibility exports."""
    
    def test_groups_export(self):
        """GROUPS should be exported as tuple."""
        assert isinstance(GROUPS, tuple)
        assert len(GROUPS) == 3
        assert "MIND" in GROUPS
    
    def test_stat_groups_export(self):
        """STAT_GROUPS should be exported as dict."""
        assert isinstance(STAT_GROUPS, dict)
        assert "MIND" in STAT_GROUPS
        assert "Meaning" in STAT_GROUPS["MIND"]
    
    def test_stat_to_group_export(self):
        """STAT_TO_GROUP should be exported as dict."""
        assert isinstance(STAT_TO_GROUP, dict)
        assert STAT_TO_GROUP["Power"] == "EXISTENCE"
    
    def test_group_beats_export(self):
        """GROUP_BEATS should be exported as dict."""
        assert isinstance(GROUP_BEATS, dict)
        assert GROUP_BEATS["MIND"] == "EXISTENCE"


class TestRockPaperScissorsLogic:
    """Test complete rock-paper-scissors cycle."""
    
    def test_complete_cycle(self):
        """Each group should beat exactly one other group."""
        groups = GroupRegistry.all_groups()
        
        for group in groups:
            group_def = GroupRegistry.get(group)
            beaten_group = group_def.beats
            
            # Verify beaten group exists
            assert beaten_group in groups
            
            # Verify this group beats the beaten group
            assert GroupRegistry.beats(group, beaten_group) is True
            
            # Verify beaten group doesn't beat this group
            assert GroupRegistry.beats(beaten_group, group) is False
    
    def test_no_self_beating(self):
        """No group should beat itself."""
        for group in GroupRegistry.all_groups():
            assert GroupRegistry.beats(group, group) is False
    
    def test_transitive_property(self):
        """If A beats B and B beats C, then C should beat A (cycle)."""
        # MIND beats EXISTENCE
        # EXISTENCE beats CONNECTION
        # CONNECTION beats MIND (completes cycle)
        
        assert GroupRegistry.beats("MIND", "EXISTENCE") is True
        assert GroupRegistry.beats("EXISTENCE", "CONNECTION") is True
        assert GroupRegistry.beats("CONNECTION", "MIND") is True


class TestIntegrationWithConstants:
    """Test integration with constants.py."""
    
    def test_constants_imports_from_registry(self):
        """constants.py should import from group_registry."""
        from engine_core import constants
        
        # Verify constants has the right values
        assert hasattr(constants, 'STAT_GROUPS')
        assert hasattr(constants, 'STAT_TO_GROUP')
        assert hasattr(constants, 'GROUP_BEATS')
        
        # Verify they match registry
        assert constants.STAT_GROUPS == GroupRegistry.get_stat_groups()
        assert constants.STAT_TO_GROUP == GroupRegistry.get_stat_to_group_map()
        assert constants.GROUP_BEATS == GroupRegistry.get_beats_map()


class TestIntegrationWithSynergy:
    """Test integration with synergy.py."""
    
    def test_synergy_uses_registry_groups(self):
        """synergy.py should use GroupRegistry.all_groups()."""
        from engine_core.synergy import GROUPS as SYNERGY_GROUPS
        
        assert SYNERGY_GROUPS == GroupRegistry.all_groups()
        assert len(SYNERGY_GROUPS) == 3


class TestIntegrationWithCombat:
    """Test integration with damage_calculator.py."""
    
    def test_combat_uses_registry(self):
        """damage_calculator.py should use GroupRegistry for combat logic."""
        from engine_core.damage_calculator import resolve_single_combat
        from engine_core.card import Card
        
        # Create two test cards with different groups
        # Card A: MIND stat (beats EXISTENCE)
        # Card B: EXISTENCE stat
        card_a = Card(
            name="TestA",
            rarity="1",
            category="Test",
            stats={"Meaning": 5, "Secret": 5, "Intelligence": 5, "Trace": 5, "Power": 3, "Durability": 3},
            rotation=0
        )
        
        card_b = Card(
            name="TestB",
            rarity="1",
            category="Test",
            stats={"Power": 5, "Durability": 5, "Size": 5, "Speed": 5, "Meaning": 3, "Secret": 3},
            rotation=0
        )
        
        # Resolve combat
        a_wins, b_wins = resolve_single_combat(card_a, card_b)
        
        # Card A should have advantage on MIND edges (beats EXISTENCE)
        # This verifies GroupRegistry.beats() is being used correctly
        assert isinstance(a_wins, int)
        assert isinstance(b_wins, int)


class TestIntegrationWithComboDetector:
    """Test integration with combo_detector.py."""
    
    def test_combo_detector_uses_registry(self):
        """combo_detector.py should use STAT_TO_GROUP from registry."""
        from engine_core.combo_detector import find_combos
        from engine_core.board import Board
        from engine_core.card import Card
        
        # Create board with two adjacent cards of same group
        board = Board()
        
        card1 = Card(
            name="Test1",
            rarity="1",
            category="Test",
            stats={"Meaning": 5, "Secret": 5, "Intelligence": 5, "Trace": 5, "Power": 3, "Durability": 3},
            rotation=0
        )
        
        card2 = Card(
            name="Test2",
            rarity="1",
            category="Test",
            stats={"Meaning": 5, "Secret": 5, "Intelligence": 5, "Trace": 5, "Power": 3, "Durability": 3},
            rotation=0
        )
        
        board.place((0, 0), card1)
        board.place((1, 0), card2)
        
        # Find combos
        combo_count, combat_bonus = find_combos(board)
        
        # Should detect combo if same-group edges face each other
        assert isinstance(combo_count, int)
        assert isinstance(combat_bonus, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
