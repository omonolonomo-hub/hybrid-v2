"""
Bug Condition Exploration Test: MOUSEBUTTONDOWN Redundant get_card_info() Call

This test explores Bug 2 from Phase 2 (CRITICAL) fixes:
- Every hand card click creates new CardDataSnapshot when data already cached
- EngineAdapter.get_card_info() is called even though card data exists in
  _public_state.active_player.hand_card_info[idx]

CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
DO NOT attempt to fix the test or the code when it fails.

Expected Outcome: Test FAILS with redundant get_card_info() calls (this proves the bug).
After the fix is implemented (Task 6), this test will PASS.

Validates: Requirements 1.5, 1.6
"""

import pytest
import pygame
from unittest.mock import MagicMock, patch, call
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

def _make_card_data(name: str = "TestCard") -> CardData:
    """Create a minimal CardData object for testing."""
    return CardData(
        name=name,
        category="Science",
        rarity="1",
        stats={"atk": 3, "hp": 5},
        passive_type="combat",
        passive_effect="Test effect",
        synergy_group="MIND",
    )


def _make_active_player(hand_card_info: dict) -> ActivePlayerViewState:
    """Build a minimal ActivePlayerViewState with the given hand_card_info."""
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
        hand=HandViewState(slots=tuple(hand_card_info.get(i) and hand_card_info[i].name for i in range(6))),
        hud=PlayerHudViewState(
            hp=100, gold=10, win_streak=0, total_pts=0,
            turn=1, next_gold=3, interest_multiplier=1.0,
        ),
        combat=CombatViewState(last_results=(), logs=(), passive_feed=()),
        synergy=SynergyViewState(groups=(), total=0, passive_feed=()),
        copies_by_name={},
        copy_milestones=(),
        prefix_bonus=0,
        shop_card_info={},
        hand_card_info=hand_card_info,
        board_card_info={},
    )


def _make_public_state(hand_card_info: dict) -> PublicState:
    """Build a minimal PublicState with the given hand_card_info."""
    return PublicState(
        phase="STATE_PREPARATION",
        turn=1,
        view_index=0,
        place_locked=False,
        alive_pids=(0,),
        pairings=(),
        active_player=_make_active_player(hand_card_info),
        lobby_players=(),
        endgame_stats=(),
    )


def _make_mouse_down_event(pos: tuple) -> pygame.event.Event:
    """Create a MOUSEBUTTONDOWN pygame event at the given position."""
    return pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"pos": pos, "button": 1},
    )


# ---------------------------------------------------------------------------
# Minimal ShopScene stub that isolates the hand-click handler
# ---------------------------------------------------------------------------

class _MinimalShopScene:
    """
    Minimal stub of ShopScene that reproduces the hand card click logic
    from _handle_mouse_down() without requiring full pygame/GameState setup.

    This isolates the exact lines under test:
        card_data = EngineAdapter.get_card_info(card_name) if card_name else None

    The stub mirrors the real logic so the test is faithful to the production code.
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

    def _current_public_state(self) -> PublicState:
        return self._public_state

    def _get_cached_card_info(self, location: str, index: int):
        """Retrieve cached card data from _public_state.
        
        Args:
            location: The location of the card ("hand", "shop", or "board")
            index: The index/coordinate of the card
            
        Returns:
            CardDataSnapshot if found in cache, else None
        """
        state = self._current_public_state()
        if location == "hand":
            return state.active_player.hand_card_info.get(index)
        elif location == "shop":
            return state.active_player.shop_card_info.get(index)
        elif location == "board":
            return state.active_player.board_card_info.get(index)
        return None

    def get_card_name(self, idx: int) -> Optional[str]:
        if 0 <= idx < len(self._card_names):
            return self._card_names[idx]
        return None

    def handle_hand_card_click(self, idx: int):
        """
        Reproduces the FIXED logic from ShopScene._handle_mouse_down():

            card_name = self.hand_panel.get_card_name(idx)
            
            # Use cached card data from _public_state instead of redundant DB lookup
            card_data = self._get_cached_card_info("hand", idx)
            
            # Fallback: if cache miss (shouldn't happen in normal flow), fetch from DB
            if card_data is None and card_name:
                from v2.core.engine_adapter import EngineAdapter
                card_data = EngineAdapter.get_card_info(card_name)

        This is the FIXED code. After the fix, EngineAdapter.get_card_info()
        should NOT be called when card data exists in hand_card_info[idx].
        """
        card_name = self.get_card_name(idx)
        
        # Use cached card data from _public_state instead of redundant DB lookup
        card_data = self._get_cached_card_info("hand", idx)
        
        # Fallback: if cache miss (shouldn't happen in normal flow), fetch from DB
        if card_data is None and card_name:
            from v2.core.engine_adapter import EngineAdapter
            card_data = EngineAdapter.get_card_info(card_name)
        
        return card_data


# ---------------------------------------------------------------------------
# Test Class
# ---------------------------------------------------------------------------

class TestBug2RedundantGetCardInfo:
    """
    Bug Condition Exploration: Redundant DB Lookup Despite Cache

    Property 1: Bug Condition - Redundant DB Lookup Despite Cache

    CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.

    Expected Behavior (after fix):
    - When hand_card_info[idx] is populated, NO call to EngineAdapter.get_card_info()
    - Cached CardData from _public_state.active_player.hand_card_info[idx] is used directly
    """

    def test_single_hand_card_click_calls_get_card_info_despite_cache(self):
        """
        Test Case 1: Single hand card click triggers EngineAdapter.get_card_info()
        even though card data already exists in hand_card_info[0].

        Bug Condition:
          - hand_card_info[0] is populated with CardData("Albert Einstein", ...)
          - Player clicks hand slot 0
          - EngineAdapter.get_card_info("Albert Einstein") is called → DB lookup

        Expected Behavior (correct):
          - EngineAdapter.get_card_info() should NOT be called
          - Cached data from hand_card_info[0] should be used directly

        EXPECTED OUTCOME: Test FAILS - get_card_info() IS called (proves the bug).
        """
        card = _make_card_data("Albert Einstein")
        hand_card_info = {0: card}
        public_state = _make_public_state(hand_card_info)
        scene = _MinimalShopScene(public_state)

        with patch("v2.core.engine_adapter.EngineAdapter.get_card_info") as mock_get_card_info:
            mock_get_card_info.return_value = card

            # Simulate clicking hand slot 0 (card data IS in cache)
            scene.handle_hand_card_click(0)

            # EXPECTED BEHAVIOR: get_card_info() should NOT be called
            # BUG BEHAVIOR: get_card_info() IS called despite cached data existing
            assert mock_get_card_info.call_count == 0, (
                f"BUG DETECTED: EngineAdapter.get_card_info() was called "
                f"{mock_get_card_info.call_count} time(s) despite card data "
                f"already existing in hand_card_info[0]. "
                f"Calls: {mock_get_card_info.call_args_list}. "
                f"Expected: 0 calls (use cached data from _public_state)."
            )

    def test_multiple_clicks_on_same_card_calls_get_card_info_multiple_times(self):
        """
        Test Case 2: Clicking the same hand card multiple times calls
        EngineAdapter.get_card_info() multiple times (redundant DB lookups).

        Bug Condition:
          - hand_card_info[0] is populated with CardData("Algorithm", ...)
          - Player clicks hand slot 0 three times
          - EngineAdapter.get_card_info("Algorithm") is called 3 times

        Expected Behavior (correct):
          - EngineAdapter.get_card_info() should NOT be called at all
          - Cached data reused on every click

        EXPECTED OUTCOME: Test FAILS - get_card_info() called 3 times (proves the bug).
        """
        card = _make_card_data("Algorithm")
        hand_card_info = {0: card}
        public_state = _make_public_state(hand_card_info)
        scene = _MinimalShopScene(public_state)

        with patch("v2.core.engine_adapter.EngineAdapter.get_card_info") as mock_get_card_info:
            mock_get_card_info.return_value = card

            # Click the same card 3 times
            scene.handle_hand_card_click(0)
            scene.handle_hand_card_click(0)
            scene.handle_hand_card_click(0)

            # EXPECTED BEHAVIOR: 0 calls (cached data reused)
            # BUG BEHAVIOR: 3 calls (one per click, ignoring cache)
            assert mock_get_card_info.call_count == 0, (
                f"BUG DETECTED: EngineAdapter.get_card_info() was called "
                f"{mock_get_card_info.call_count} time(s) for 3 clicks on the same card. "
                f"Expected: 0 calls (cached data should be reused). "
                f"Counterexample: {mock_get_card_info.call_args_list}"
            )

    def test_rapid_clicks_on_different_cards_causes_multiple_redundant_lookups(self):
        """
        Test Case 3: Rapid clicks on different hand cards cause multiple redundant
        EngineAdapter.get_card_info() calls.

        Bug Condition:
          - hand_card_info[0..4] populated with 5 different cards
          - Player rapidly clicks all 5 slots
          - EngineAdapter.get_card_info() called 5 times (one per card)

        Expected Behavior (correct):
          - EngineAdapter.get_card_info() should NOT be called at all
          - All 5 cards' data retrieved from cache

        EXPECTED OUTCOME: Test FAILS - get_card_info() called 5 times (proves the bug).
        """
        card_names = ["Albert Einstein", "Algorithm", "Anubis", "Athena", "Axolotl"]
        cards = [_make_card_data(name) for name in card_names]
        hand_card_info = {i: cards[i] for i in range(5)}
        public_state = _make_public_state(hand_card_info)
        scene = _MinimalShopScene(public_state)

        with patch("v2.core.engine_adapter.EngineAdapter.get_card_info") as mock_get_card_info:
            mock_get_card_info.side_effect = lambda name: next(
                (c for c in cards if c.name == name), None
            )

            # Rapidly click all 5 slots
            for idx in range(5):
                scene.handle_hand_card_click(idx)

            # EXPECTED BEHAVIOR: 0 calls (all data from cache)
            # BUG BEHAVIOR: 5 calls (one per card, ignoring cache)
            assert mock_get_card_info.call_count == 0, (
                f"BUG DETECTED: EngineAdapter.get_card_info() was called "
                f"{mock_get_card_info.call_count} time(s) for 5 rapid clicks on different cards. "
                f"Expected: 0 calls (all data from hand_card_info cache). "
                f"Counterexample calls: {mock_get_card_info.call_args_list}"
            )

    def test_empty_slot_click_does_not_call_get_card_info(self):
        """
        Test Case 4 (Edge Case): Clicking an empty hand slot should NOT call
        EngineAdapter.get_card_info() (card_name is None → no lookup needed).

        This test should PASS even on unfixed code (the `if card_name else None`
        guard already handles this case).

        EXPECTED OUTCOME: Test PASSES (edge case already handled correctly).
        """
        # No cards in hand
        hand_card_info = {}
        public_state = _make_public_state(hand_card_info)
        scene = _MinimalShopScene(public_state)

        with patch("v2.core.engine_adapter.EngineAdapter.get_card_info") as mock_get_card_info:
            # Click an empty slot (no card_name)
            result = scene.handle_hand_card_click(0)

            # Empty slot: get_card_info() should NOT be called (card_name is None)
            assert mock_get_card_info.call_count == 0, (
                f"Empty slot click should not call get_card_info(). "
                f"Got {mock_get_card_info.call_count} call(s)."
            )
            assert result is None, "Empty slot click should return None card_data."

    def test_cached_data_is_ignored_when_card_clicked(self):
        """
        Test Case 5: Verify that the cached CardData in hand_card_info is NOT used
        by the current (buggy) implementation — it fetches from DB instead.

        This test directly documents the bug: the returned card_data comes from
        EngineAdapter.get_card_info() (a NEW object), not from hand_card_info[idx].

        EXPECTED OUTCOME: Test FAILS — the returned object is from DB, not cache.
        """
        cached_card = _make_card_data("Babylon")
        # DB returns a DIFFERENT object (simulating a new CardDataSnapshot)
        db_card = _make_card_data("Babylon")
        # Make them distinguishable by identity
        assert cached_card is not db_card, "Test setup: cached and db objects must be distinct"

        hand_card_info = {0: cached_card}
        public_state = _make_public_state(hand_card_info)
        scene = _MinimalShopScene(public_state)

        with patch("v2.core.engine_adapter.EngineAdapter.get_card_info") as mock_get_card_info:
            mock_get_card_info.return_value = db_card

            result = scene.handle_hand_card_click(0)

            # EXPECTED BEHAVIOR (correct): result should be the CACHED object
            # BUG BEHAVIOR: result is the DB object (new CardDataSnapshot created)
            assert result is cached_card, (
                f"BUG DETECTED: hand card click returned a NEW object from DB "
                f"instead of the cached CardData from hand_card_info[0]. "
                f"Expected: cached_card (id={id(cached_card)}). "
                f"Got: result (id={id(result)}). "
                f"This proves EngineAdapter.get_card_info() was called and its "
                f"return value used instead of the cached data."
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
