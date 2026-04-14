"""Unit tests for ParameterizedAI.place_cards() delegation.

Tests that ParameterizedAI.place_cards() correctly delegates to AI.place_cards()
with all parameters passed through.

Feature: strategy-params-hot-reload
Task: 2.5 Implement ParameterizedAI.place_cards() delegation
Requirements: 3.1
"""

import pytest
from unittest.mock import Mock, patch, call
from engine_core.ai import ParameterizedAI, AI
from engine_core.player import Player
from engine_core.board import Board


class TestPlaceCardsDelegation:
    """Test ParameterizedAI.place_cards() delegation to AI.place_cards()."""
    
    def test_place_cards_delegates_to_ai(self):
        """Test that place_cards delegates to AI.place_cards with all parameters."""
        # Arrange
        ai = ParameterizedAI(strategy="economist")
        mock_player = Mock(spec=Player)
        mock_rng = Mock()
        power_thresh = 50.0
        combo_weight = 2.0
        
        # Act & Assert
        with patch.object(AI, 'place_cards') as mock_ai_place:
            ai.place_cards(
                mock_player,
                rng=mock_rng,
                power_center_thresh=power_thresh,
                combo_center_weight=combo_weight
            )
            
            # Verify AI.place_cards was called with correct parameters
            mock_ai_place.assert_called_once_with(
                mock_player,
                mock_rng,
                power_thresh,
                combo_weight
            )
    
    def test_place_cards_with_default_parameters(self):
        """Test place_cards delegation with default parameters."""
        # Arrange
        ai = ParameterizedAI(strategy="economist")
        mock_player = Mock(spec=Player)
        
        # Act & Assert
        with patch.object(AI, 'place_cards') as mock_ai_place:
            ai.place_cards(mock_player)
            
            # Verify AI.place_cards was called with defaults
            mock_ai_place.assert_called_once_with(
                mock_player,
                None,  # rng default
                45.0,  # power_center_thresh default
                1.5    # combo_center_weight default
            )
    
    def test_place_cards_with_partial_parameters(self):
        """Test place_cards delegation with some parameters specified."""
        # Arrange
        ai = ParameterizedAI(strategy="economist")
        mock_player = Mock(spec=Player)
        mock_rng = Mock()
        
        # Act & Assert
        with patch.object(AI, 'place_cards') as mock_ai_place:
            ai.place_cards(mock_player, rng=mock_rng)
            
            # Verify AI.place_cards was called with mixed params
            mock_ai_place.assert_called_once_with(
                mock_player,
                mock_rng,
                45.0,  # default
                1.5    # default
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
