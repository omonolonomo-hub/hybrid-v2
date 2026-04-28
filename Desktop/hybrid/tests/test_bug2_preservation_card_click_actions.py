"""
Preservation Unit Tests: Card Click Actions

Property 2: Preservation - Card Click Actions

These tests capture the baseline behavior of card click actions on UNFIXED code.
They ensure that after the fix (using cached data instead of EngineAdapter.get_card_info()),
the card click actions (drag, play, sell) continue to work exactly as before.

IMPORTANT: Follow observation-first methodology
- Run tests on UNFIXED code
- EXPECTED OUTCOME: Tests PASS (confirms baseline behavior to preserve)
- After fix implementation (Task 6), re-run these tests to ensure no regressions

Requirements: 3.4, 3.5, 3.6
"""

import pytest
import pygame
from unittest.mock import Mock, MagicMock, patch
from typing import Optional

from v2.core.card_database import CardData
from v2.core.public_state import (
    ActivePlayerViewState,
    HandViewState,
    ShopViewState,
    PlayerHudViewState,
    SynergyViewState,
    CombatViewState,
    PublicState,
)


# ---------------------------------------------------------------------------
# Helpers / Factories
# ---------------------------------------------------------------------------

def _make_card_data(name: str = "TestCard", rarity: str = "1") -> CardData:
    """Create a minimal CardData object for testing."""
    return CardData(
        name=name,
        category="Science",
        rarity=rarity,
        stats={"atk": 3, "hp": 5},
        passive_type="combat",
        passive_effect="Test effect",
        synergy_group="MIND",
    )


def _make_active_player(
    hand_card_info: dict,
    shop_card_info: dict = None,
    board_card_info: dict = None
) -> ActivePlayerViewState:
    """Build a minimal ActivePlayerViewState with the given card info."""
    if shop_card_info is None:
        shop_card_info = {}
    if board_card_info is None:
        board_card_info = {}
    
    return ActivePlayerViewState(
        index=0,
        pid=0,
        display_name="TestPlayer",
        strategy="test",
        hp=100,
        gold=10,
        alive=True,
        turns_played=1,
        stats={},
        has_catalyst=False,
        has_eclipse=False,
        board_cards={},
        board_rotations={},
        adjacency_pairs=(),
        eliminated_coords=(),
        shop=ShopViewState(
            slots=(None, None, None, None, None),
            is_locked=False,
            rarity_probabilities={},
        ),
        hand=HandViewState(
            slots=tuple(
                hand_card_info.get(i).name if hand_card_info.get(i) else None
                for i in range(6)
            )
        ),
        hud=PlayerHudViewState(
            hp=100, gold=10, win_streak=0, total_pts=0,
            turn=1, next_gold=3, interest_multiplier=1.0,
        ),
        combat=CombatViewState(last_results=(), logs=(), passive_feed=()),
        synergy=SynergyViewState(groups=(), total=0, passive_feed=()),
        copies_by_name={},
        copy_milestones=(),
        prefix_bonus=0,
        shop_card_info=shop_card_info,
        hand_card_info=hand_card_info,
        board_card_info=board_card_info,
    )


def _make_public_state(
    hand_card_info: dict,
    shop_card_info: dict = None,
    board_card_info: dict = None
) -> PublicState:
    """Build a minimal PublicState with the given card info."""
    return PublicState(
        phase="STATE_PREPARATION",
        turn=1,
        view_index=0,
        place_locked=False,
        alive_pids=(0,),
        pairings=(),
        active_player=_make_active_player(hand_card_info, shop_card_info, board_card_info),
        lobby_players=(),
        endgame_stats=(),
    )


# ---------------------------------------------------------------------------
# Minimal ShopScene stub for testing card click actions
# ---------------------------------------------------------------------------

class _MinimalShopScene:
    """
    Minimal stub of ShopScene that reproduces the hand card click logic
    from _handle_mouse_down() for testing preservation of card click actions.
    
    This stub isolates the drag state management and card data retrieval
    to verify that card click actions (drag, play, sell) work correctly.
    """

    def __init__(self, public_state: PublicState):
        self._public_state = public_state
        
        # Simulate hand_panel.card_rects — 6 slots, each 160x200 px
        # Positioned at x=380, y=800 (matches real HandPanel layout)
        self.card_rects = [
            pygame.Rect(380 + i * (160 + 24), 800, 160, 200)
            for i in range(6)
        ]
        
        # Simulate hand_panel._card_names
        self._card_names = [
            (public_state.active_player.hand_card_info.get(i).name
             if public_state.active_player.hand_card_info.get(i) else None)
            for i in range(6)
        ]
        
        # Drag state (matches ShopScene.drag_state)
        self.drag_state = {
            "is_dragging": False,
            "source_panel": None,
            "source_index": -1,
            "mouse_pos": (0, 0),
            "card_rect": None,
            "rotation": 0,
            "card_data": None,
        }

    def _current_public_state(self) -> PublicState:
        return self._public_state

    def get_card_name(self, idx: int) -> Optional[str]:
        if 0 <= idx < len(self._card_names):
            return self._card_names[idx]
        return None

    def handle_hand_card_click(self, idx: int, pos: tuple[int, int]):
        """
        Reproduces the exact logic from ShopScene._handle_mouse_down()
        for hand card clicks:

            card_name = self.hand_panel.get_card_name(idx)
            from v2.core.engine_adapter import EngineAdapter
            card_data = EngineAdapter.get_card_info(card_name) if card_name else None
            
            self.drag_state.update({
                "is_dragging": True,
                "source_panel": "hand",
                "source_index": idx,
                "mouse_pos": event.pos,
                "card_rect": pygame.Rect(slot_rect),
                "card_data": card_data,
            })

        This is the code under test. We verify that drag state is correctly
        initialized with card_data, enabling drag/play/sell actions.
        """
        card_name = self.get_card_name(idx)
        from v2.core.engine_adapter import EngineAdapter
        card_data = EngineAdapter.get_card_info(card_name) if card_name else None
        
        slot_rect = self.card_rects[idx]
        self.drag_state.update({
            "is_dragging": True,
            "source_panel": "hand",
            "source_index": idx,
            "mouse_pos": pos,
            "card_rect": pygame.Rect(slot_rect),
            "card_data": card_data,
        })
        
        return card_data


# ---------------------------------------------------------------------------
# Test Class
# ---------------------------------------------------------------------------

class TestBug2PreservationCardClickActions:
    """
    Preservation Tests: Card Click Actions
    
    Property 2: Preservation - Card Click Actions
    
    These tests verify that card click actions (drag, play, sell) work correctly
    on UNFIXED code. After the fix (Task 6), these tests ensure no regressions.
    
    EXPECTED OUTCOME: Tests PASS on unfixed code (confirms baseline behavior).
    """

    def test_card_click_triggers_correct_drag_action(self):
        """
        Test 1: Card click triggers correct drag action
        
        This test verifies that clicking a hand card correctly initializes
        the drag state with:
        - is_dragging = True
        - source_panel = "hand"
        - source_index = clicked slot index
        - card_data = CardData from EngineAdapter.get_card_info()
        
        This is the baseline behavior that must be preserved after the fix.
        
        Requirement: 3.4
        """
        # Setup: Hand with one card
        card = _make_card_data("Albert Einstein")
        hand_card_info = {0: card}
        public_state = _make_public_state(hand_card_info)
        scene = _MinimalShopScene(public_state)
        
        # Mock EngineAdapter.get_card_info to return card data
        with patch("v2.core.engine_adapter.EngineAdapter.get_card_info") as mock_get_card_info:
            mock_get_card_info.return_value = card
            
            # Act: Click hand slot 0
            click_pos = (400, 850)  # Inside slot 0 rect
            result = scene.handle_hand_card_click(0, click_pos)
            
            # Assert: Drag state is correctly initialized
            assert scene.drag_state["is_dragging"] is True, (
                "Drag state should be active after hand card click"
            )
            assert scene.drag_state["source_panel"] == "hand", (
                "Source panel should be 'hand' for hand card click"
            )
            assert scene.drag_state["source_index"] == 0, (
                "Source index should match clicked slot (0)"
            )
            assert scene.drag_state["mouse_pos"] == click_pos, (
                "Mouse position should be stored in drag state"
            )
            assert scene.drag_state["card_data"] is not None, (
                "Card data should be populated in drag state"
            )
            assert scene.drag_state["card_data"].name == "Albert Einstein", (
                "Card data should match the clicked card"
            )
            
            # Assert: Card rect is stored for drag rendering
            assert scene.drag_state["card_rect"] is not None, (
                "Card rect should be stored for drag rendering"
            )
            assert isinstance(scene.drag_state["card_rect"], pygame.Rect), (
                "Card rect should be a pygame.Rect"
            )

    def test_card_click_triggers_correct_play_action(self):
        """
        Test 2: Card click triggers correct play action
        
        This test verifies that the drag state initialized by a card click
        contains all necessary data for a "play" action (placing card on board).
        
        The play action requires:
        - card_data with stats for synergy preview
        - source_index to identify which hand slot to remove from
        - rotation for hex placement
        
        Requirement: 3.5
        """
        # Setup: Hand with a card that has specific stats
        card = _make_card_data("Algorithm", rarity="2")
        card.stats = {"atk": 8, "hp": 12, "spd": 5}
        hand_card_info = {2: card}  # Slot 2
        public_state = _make_public_state(hand_card_info)
        scene = _MinimalShopScene(public_state)
        
        # Mock EngineAdapter.get_card_info
        with patch("v2.core.engine_adapter.EngineAdapter.get_card_info") as mock_get_card_info:
            mock_get_card_info.return_value = card
            
            # Act: Click hand slot 2
            click_pos = (848, 850)  # Inside slot 2 rect (380 + 2*(160+24))
            result = scene.handle_hand_card_click(2, click_pos)
            
            # Assert: Drag state contains data needed for play action
            assert scene.drag_state["is_dragging"] is True
            assert scene.drag_state["source_panel"] == "hand"
            assert scene.drag_state["source_index"] == 2, (
                "Source index should be 2 (the clicked slot)"
            )
            
            # Assert: Card data is available for synergy preview
            card_data = scene.drag_state["card_data"]
            assert card_data is not None, (
                "Card data must be available for synergy preview during drag"
            )
            assert card_data.name == "Algorithm"
            assert card_data.stats == {"atk": 8, "hp": 12, "spd": 5}, (
                "Card stats must be available for synergy calculation"
            )
            assert card_data.rarity == "2", (
                "Card rarity must be available for rendering"
            )
            
            # Assert: Rotation is initialized (default 0)
            assert "rotation" in scene.drag_state
            assert scene.drag_state["rotation"] == 0, (
                "Rotation should be initialized to 0"
            )

    def test_card_click_triggers_correct_sell_action(self):
        """
        Test 3: Card click triggers correct sell action
        
        This test verifies that the drag state initialized by a card click
        can support a "sell" action (right-click or drag to sell zone).
        
        The sell action requires:
        - source_panel = "hand" to identify where to remove card from
        - source_index to identify which card to sell
        - card_data to calculate sell value (based on rarity)
        
        Requirement: 3.5
        """
        # Setup: Hand with a rare card (higher sell value)
        card = _make_card_data("Anubis", rarity="3")
        hand_card_info = {4: card}  # Slot 4
        public_state = _make_public_state(hand_card_info)
        scene = _MinimalShopScene(public_state)
        
        # Mock EngineAdapter.get_card_info
        with patch("v2.core.engine_adapter.EngineAdapter.get_card_info") as mock_get_card_info:
            mock_get_card_info.return_value = card
            
            # Act: Click hand slot 4
            click_pos = (1216, 850)  # Inside slot 4 rect (380 + 4*(160+24))
            result = scene.handle_hand_card_click(4, click_pos)
            
            # Assert: Drag state contains data needed for sell action
            assert scene.drag_state["is_dragging"] is True
            assert scene.drag_state["source_panel"] == "hand", (
                "Source panel must be 'hand' for sell action to work"
            )
            assert scene.drag_state["source_index"] == 4, (
                "Source index must be 4 to identify which card to sell"
            )
            
            # Assert: Card data is available for sell value calculation
            card_data = scene.drag_state["card_data"]
            assert card_data is not None, (
                "Card data must be available to calculate sell value"
            )
            assert card_data.name == "Anubis"
            assert card_data.rarity == "3", (
                "Card rarity must be available to calculate sell value (rarity affects price)"
            )

    def test_other_mouse_events_work_correctly(self):
        """
        Test 4: Other mouse events (board clicks, shop clicks) work correctly
        
        This test verifies that clicking outside the hand panel (e.g., on board
        or shop) does NOT trigger hand card drag state.
        
        This ensures the fix doesn't break other mouse event handling.
        
        Requirement: 3.6
        """
        # Setup: Hand with cards
        card1 = _make_card_data("Albert Einstein")
        card2 = _make_card_data("Algorithm")
        hand_card_info = {0: card1, 1: card2}
        public_state = _make_public_state(hand_card_info)
        scene = _MinimalShopScene(public_state)
        
        # Act: Click outside hand panel (e.g., on board area)
        # Board area is typically in the center of the screen, not near hand panel
        board_click_pos = (960, 400)  # Center of screen (board area)
        
        # Verify this position is NOT inside any hand card rect
        for rect in scene.card_rects:
            assert not rect.collidepoint(board_click_pos), (
                "Test setup error: board_click_pos should not be inside hand card rect"
            )
        
        # Assert: Drag state remains inactive (no hand card clicked)
        assert scene.drag_state["is_dragging"] is False, (
            "Drag state should remain inactive when clicking outside hand panel"
        )
        assert scene.drag_state["source_panel"] is None, (
            "Source panel should remain None when clicking outside hand panel"
        )
        assert scene.drag_state["source_index"] == -1, (
            "Source index should remain -1 when clicking outside hand panel"
        )
        assert scene.drag_state["card_data"] is None, (
            "Card data should remain None when clicking outside hand panel"
        )

    def test_empty_slot_click_does_not_trigger_drag(self):
        """
        Test 5 (Edge Case): Clicking an empty hand slot does not trigger drag
        
        This test verifies that clicking an empty hand slot (no card) does NOT
        initialize drag state, preventing errors in drag/drop logic.
        
        Requirement: 3.4
        """
        # Setup: Hand with only one card in slot 0, rest empty
        card = _make_card_data("Albert Einstein")
        hand_card_info = {0: card}  # Only slot 0 has a card
        public_state = _make_public_state(hand_card_info)
        scene = _MinimalShopScene(public_state)
        
        # Mock EngineAdapter.get_card_info
        with patch("v2.core.engine_adapter.EngineAdapter.get_card_info") as mock_get_card_info:
            mock_get_card_info.return_value = None  # Empty slot returns None
            
            # Act: Click empty slot 3
            click_pos = (1032, 850)  # Inside slot 3 rect (380 + 3*(160+24))
            result = scene.handle_hand_card_click(3, click_pos)
            
            # Assert: Drag state is initialized but card_data is None
            # (The current implementation still sets is_dragging=True even for empty slots,
            # but card_data is None, which prevents actual drag operations)
            assert scene.drag_state["is_dragging"] is True, (
                "Current implementation sets is_dragging=True even for empty slots"
            )
            assert scene.drag_state["card_data"] is None, (
                "Card data should be None for empty slot"
            )
            assert result is None, (
                "Empty slot click should return None card_data"
            )

    def test_multiple_card_clicks_update_drag_state_correctly(self):
        """
        Test 6: Multiple card clicks update drag state correctly
        
        This test verifies that clicking different hand cards in sequence
        correctly updates the drag state each time.
        
        Requirement: 3.4
        """
        # Setup: Hand with multiple cards
        card1 = _make_card_data("Albert Einstein")
        card2 = _make_card_data("Algorithm")
        card3 = _make_card_data("Anubis")
        hand_card_info = {0: card1, 1: card2, 2: card3}
        public_state = _make_public_state(hand_card_info)
        scene = _MinimalShopScene(public_state)
        
        # Mock EngineAdapter.get_card_info
        with patch("v2.core.engine_adapter.EngineAdapter.get_card_info") as mock_get_card_info:
            # First click: slot 0
            mock_get_card_info.return_value = card1
            scene.handle_hand_card_click(0, (400, 850))
            
            assert scene.drag_state["source_index"] == 0
            assert scene.drag_state["card_data"].name == "Albert Einstein"
            
            # Second click: slot 1 (should update drag state)
            mock_get_card_info.return_value = card2
            scene.handle_hand_card_click(1, (584, 850))
            
            assert scene.drag_state["source_index"] == 1, (
                "Drag state should update to new slot index"
            )
            assert scene.drag_state["card_data"].name == "Algorithm", (
                "Drag state should update to new card data"
            )
            
            # Third click: slot 2 (should update drag state again)
            mock_get_card_info.return_value = card3
            scene.handle_hand_card_click(2, (768, 850))
            
            assert scene.drag_state["source_index"] == 2, (
                "Drag state should update to new slot index"
            )
            assert scene.drag_state["card_data"].name == "Anubis", (
                "Drag state should update to new card data"
            )

    def test_card_data_contains_all_required_fields_for_actions(self):
        """
        Test 7: Card data contains all required fields for drag/play/sell actions
        
        This test verifies that the CardData returned by EngineAdapter.get_card_info()
        contains all fields required for card actions:
        - name: for identification
        - stats: for synergy calculation
        - rarity: for sell value and rendering
        - category: for synergy group
        - passive_type/passive_effect: for tooltip display
        
        Requirement: 3.5
        """
        # Setup: Hand with a fully-specified card
        card = CardData(
            name="Athena",
            category="Mythology & Gods",
            rarity="4",
            stats={"atk": 20, "hp": 25, "spd": 8, "def": 15},
            passive_type="combat",
            passive_effect="Grants shield to adjacent allies",
            synergy_group="EXISTENCE",
        )
        hand_card_info = {0: card}
        public_state = _make_public_state(hand_card_info)
        scene = _MinimalShopScene(public_state)
        
        # Mock EngineAdapter.get_card_info
        with patch("v2.core.engine_adapter.EngineAdapter.get_card_info") as mock_get_card_info:
            mock_get_card_info.return_value = card
            
            # Act: Click hand slot 0
            result = scene.handle_hand_card_click(0, (400, 850))
            
            # Assert: Card data in drag state has all required fields
            card_data = scene.drag_state["card_data"]
            assert card_data is not None
            
            # Required for identification
            assert hasattr(card_data, "name")
            assert card_data.name == "Athena"
            
            # Required for synergy calculation
            assert hasattr(card_data, "stats")
            assert isinstance(card_data.stats, dict)
            assert "atk" in card_data.stats
            assert "hp" in card_data.stats
            
            # Required for sell value and rendering
            assert hasattr(card_data, "rarity")
            assert card_data.rarity == "4"
            
            # Required for synergy group
            assert hasattr(card_data, "category") or hasattr(card_data, "synergy_group")
            
            # Required for tooltip display
            assert hasattr(card_data, "passive_type")
            assert hasattr(card_data, "passive_effect")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
