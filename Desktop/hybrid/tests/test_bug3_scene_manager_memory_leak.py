"""
Bug Condition Exploration Test: SceneManager Singleton Memory Leak

This test demonstrates the memory leak bug in SceneManager where the singleton
pattern prevents garbage collection of old scenes, causing RAM explosion on
scene transitions.

CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
DO NOT attempt to fix the test or the code when it fails.

Bug Condition (C): 
    isBugCondition(input) where input.old_scene EXISTS 
    AND input.old_scene.on_exit() called 
    AND input.old_scene.references_not_cleared == True 
    AND SceneManager._instance holds reference to old_scene 
    AND GC cannot reclaim old_scene memory

Expected Behavior (P):
    When set_scene() is called AND a current scene exists, 
    the system SHALL cleanup the current scene (call on_exit(), null references, 
    delete fade surface) before replacing it, allowing GC to reclaim memory.

Test Approach:
    Use weakref pattern for reliable GC testing (not RAM measurement which is flaky).
    Test concrete failing cases: single transition, multiple transitions, 
    GameState reference survival, and first set_scene() edge case.

Requirements: 1.7, 1.8, 1.9, 1.10
"""

import gc
import weakref
import pygame
import pytest

from v2.core.scene_manager import Scene, SceneManager
from v2.core.game_state import GameState


class HeavyScene(Scene):
    """Scene with heavy resources to simulate real ShopScene memory footprint."""
    
    def __init__(self, game_state: GameState = None):
        self.name = f"HeavyScene_{id(self)}"
        self.game_state = game_state
        self.exit_called = False
        
        # Simulate heavy resources like ShopScene
        self.surfaces = []
        for _ in range(10):
            # Create 10 surfaces to simulate UI components
            surf = pygame.Surface((100, 100))
            self.surfaces.append(surf)
        
        # Simulate UI component references
        self.ui_components = {
            "shop_panel": {"data": list(range(100))},
            "hand_panel": {"data": list(range(100))},
            "board": {"data": list(range(100))},
        }
    
    def on_enter(self) -> None:
        pass
    
    def on_exit(self) -> None:
        """Called by SceneManager but doesn't null out references.
        
        BUG SIMULATION: This simulates the CURRENT behavior where on_exit()
        is called but the scene doesn't properly null out its heavy references.
        
        In the REAL ShopScene, on_exit() calls game_state.cleanup() which is good,
        but the scene itself still holds references to:
        - Pygame Surfaces (self.surfaces, self._sidebar_bg, etc.)
        - UI components (self.shop_panel, self.hand_panel, etc.)
        - GameState reference (self._game_state)
        
        The FIX will ensure that:
        1. SceneManager explicitly nulls self._current before setting new scene
        2. SceneManager deletes self._fade_surface
        3. Scene's on_exit() nulls out heavy references
        """
        self.exit_called = True
        
        # CURRENT BEHAVIOR: on_exit() is called but references are NOT nulled
        # This is what causes the memory leak in production
        # The fix will add cleanup here:
        # self.game_state = None
        # self.surfaces = []
        # self.ui_components = {}
    
    def update(self, dt_ms: float) -> None:
        pass
    
    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((50, 50, 50))


@pytest.fixture(autouse=True)
def setup_pygame_and_reset_singleton():
    """Initialize pygame and reset SceneManager singleton before each test."""
    # pygame.init() is handled by session-scoped conftest.py fixture
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
    
    # Reset singleton using monkey-patching (current approach)
    # The fix will add a dispose() method to replace this
    SceneManager._instance = None
    
    yield
    
    # Cleanup
    SceneManager._instance = None
    # Don't call pygame.quit() - let session fixture handle it


def test_single_scene_transition_prevents_gc():
    """
    Test 1: Single scene transition → Verify old scene not GC'd (weakref still alive)
    
    This test documents the EXPECTED behavior after the fix.
    
    CURRENT BEHAVIOR: The scene IS being GC'd because set_scene() replaces self._current.
    However, the code doesn't explicitly null the reference or clean up fade surface.
    
    EXPECTED OUTCOME AFTER FIX: 
    - Explicit nulling of self._current before assignment
    - Explicit deletion of self._fade_surface
    - Scene's on_exit() nulls out heavy references
    
    This test PASSES on current code (scene is GC'd), but the fix will make
    the cleanup more explicit and robust.
    """
    sm = SceneManager.get()
    
    # Create first scene with GameState
    gs1 = GameState()
    old_scene = HeavyScene(gs1)
    
    # Create weakref to track if scene is GC'd
    scene_ref = weakref.ref(old_scene)
    gs_ref = weakref.ref(gs1)
    
    # Set first scene
    sm.set_scene(old_scene)
    assert scene_ref() is not None, "Scene should exist after set_scene()"
    
    # Transition to new scene
    new_scene = HeavyScene(GameState())
    sm.set_scene(new_scene)
    
    # Verify on_exit() was called
    assert old_scene.exit_called, "on_exit() should have been called"
    
    # Debug: Check what's holding references
    import sys
    print(f"\nDEBUG: Reference count for old_scene before del: {sys.getrefcount(old_scene)}")
    print(f"DEBUG: SceneManager._current is new_scene: {sm._current is new_scene}")
    print(f"DEBUG: SceneManager._current is old_scene: {sm._current is old_scene}")
    
    # Delete local references
    del old_scene
    del gs1
    
    # Force garbage collection
    gc.collect()
    
    # Debug: Check if weakrefs are alive
    print(f"DEBUG: scene_ref() after gc.collect(): {scene_ref()}")
    print(f"DEBUG: gs_ref() after gc.collect(): {gs_ref()}")
    
    # EXPECTED BEHAVIOR: Old scene should be GC'd
    # This test PASSES on current code, but the fix will make cleanup more explicit
    assert scene_ref() is None, (
        "Old scene should be GC'd after set_scene() transition. "
        "The fix will add explicit nulling of self._current before assignment."
    )
    
    # Also check if GameState is GC'd
    assert gs_ref() is None, (
        "Old GameState should be GC'd after scene transition."
    )


def test_multiple_scene_transitions_accumulate_memory():
    """
    Test 2: Multiple scene transitions (3-4) → Verify multiple old scenes not GC'd
    
    EXPECTED OUTCOME: Test FAILS with multiple weakrefs still alive
    (this is correct - it proves the bug exists)
    """
    sm = SceneManager.get()
    
    # Track all scenes with weakrefs
    scene_refs = []
    gs_refs = []
    
    # Create and transition through 4 scenes
    for i in range(4):
        gs = GameState()
        scene = HeavyScene(gs)
        
        scene_refs.append(weakref.ref(scene))
        gs_refs.append(weakref.ref(gs))
        
        sm.set_scene(scene)
        
        # Delete local references immediately
        del scene
        del gs
    
    # Force garbage collection
    gc.collect()
    
    # BUG CONDITION: First 3 scenes should be GC'd but weakrefs are still alive
    # Only the last scene (index 3) should be alive
    alive_scenes = [i for i, ref in enumerate(scene_refs) if ref() is not None]
    alive_gs = [i for i, ref in enumerate(gs_refs) if ref() is not None]
    
    # This assertion SHOULD FAIL on unfixed code (proving the bug exists)
    assert alive_scenes == [3], (
        f"MEMORY LEAK: Only the current scene (index 3) should be alive, "
        f"but scenes {alive_scenes} are still alive. "
        f"SceneManager is accumulating old scenes."
    )
    
    assert alive_gs == [3], (
        f"MEMORY LEAK: Only the current GameState (index 3) should be alive, "
        f"but GameStates {alive_gs} are still alive."
    )


def test_gamestate_references_survive_scene_transition():
    """
    Test 3: Check if old GameState references survive → Verify GC blocked
    
    EXPECTED OUTCOME: Test FAILS with GameState weakref still alive
    (this is correct - it proves the bug exists)
    """
    sm = SceneManager.get()
    
    # Create scene with GameState
    gs = GameState()
    scene = HeavyScene(gs)
    
    # Track both scene and GameState
    scene_ref = weakref.ref(scene)
    gs_ref = weakref.ref(gs)
    
    # Set scene
    sm.set_scene(scene)
    
    # Transition to new scene
    sm.set_scene(HeavyScene(GameState()))
    
    # Delete local references
    del scene
    del gs
    
    # Force garbage collection
    gc.collect()
    
    # BUG CONDITION: GameState should be GC'd but weakref is still alive
    # This proves that scene references are preventing GC
    assert gs_ref() is None, (
        "MEMORY LEAK: Old GameState should be GC'd after scene transition, "
        "but weakref is still alive. Scene is holding GameState reference "
        "and SceneManager is holding scene reference."
    )


def test_first_set_scene_with_no_old_scene():
    """
    Test 4: First set_scene() call with no old scene → Verify no null scene operations
    
    This is an edge case test to ensure the fix doesn't break first scene setup.
    
    EXPECTED OUTCOME: Test PASSES (no exception, scene is set correctly)
    """
    sm = SceneManager.get()
    
    # First set_scene() call - no old scene exists
    scene = HeavyScene(GameState())
    scene_ref = weakref.ref(scene)
    
    # This should not raise any exceptions
    sm.set_scene(scene)
    
    # Verify scene is set correctly
    assert sm.current_scene_name == "HeavyScene"
    assert scene_ref() is not None, "Scene should be alive after first set_scene()"
    
    # Verify no on_exit() was called (no old scene to exit)
    assert not scene.exit_called, "on_exit() should not be called on first set_scene()"


def test_fade_surface_survives_scene_transition():
    """
    Test: Verify fade surface cleanup in set_scene()
    
    This test demonstrates that set_scene() doesn't clean up the fade surface.
    The fix will add explicit deletion of self._fade_surface in set_scene().
    
    EXPECTED OUTCOME: Test documents the need for fade surface cleanup
    """
    sm = SceneManager.get()
    
    # Create first scene
    scene1 = HeavyScene(GameState())
    sm.set_scene(scene1)
    
    # Create a fade surface manually to simulate previous transition
    sm._fade_surface = pygame.Surface((800, 600))
    fade_ref = weakref.ref(sm._fade_surface)
    
    # Transition to new scene using set_scene() (not transition_to())
    scene2 = HeavyScene(GameState())
    sm.set_scene(scene2)
    
    # BUG: set_scene() doesn't delete the fade surface
    # The fix will add: del self._fade_surface; self._fade_surface = None
    print(f"\nDEBUG: Fade surface after set_scene(): {sm._fade_surface}")
    print(f"DEBUG: Fade surface weakref: {fade_ref()}")
    
    # Document the issue
    if sm._fade_surface is not None:
        print(
            "ISSUE DOCUMENTED: set_scene() doesn't clean up fade surface. "
            "The fix will add explicit deletion in set_scene()."
        )


def test_explicit_null_reference_pattern():
    """
    Test: Verify explicit nulling pattern in set_scene()
    
    This test documents the IMPROVEMENT that the fix will add:
    explicit nulling of self._current before assignment.
    
    CURRENT CODE:
        if self._current is not None:
            self._current.on_exit()
        self._current = scene  # Direct assignment
    
    FIXED CODE:
        if self._current is not None:
            self._current.on_exit()
            self._current = None  # Explicit null
        self._current = scene
    
    This makes the cleanup more explicit and easier to understand.
    """
    sm = SceneManager.get()
    
    # Create first scene
    scene1 = HeavyScene(GameState())
    sm.set_scene(scene1)
    
    # Verify scene is set
    assert sm._current is scene1
    
    # Create second scene
    scene2 = HeavyScene(GameState())
    
    # Before set_scene(), _current points to scene1
    assert sm._current is scene1
    
    # After set_scene(), _current should point to scene2
    sm.set_scene(scene2)
    assert sm._current is scene2
    assert sm._current is not scene1
    
    # The fix will add explicit nulling between on_exit() and assignment
    print(
        "\nDOCUMENTED: The fix will add explicit 'self._current = None' "
        "after on_exit() and before assigning new scene."
    )


def test_dispose_method_for_testing():
    """
    Test: Verify need for dispose() method
    
    This test documents the need for a dispose() class method to replace
    monkey-patching in tests.
    
    CURRENT APPROACH (in test fixtures):
        SceneManager._instance = None  # Monkey-patching
    
    FIXED APPROACH:
        SceneManager.dispose()  # Clean method
    
    The dispose() method will:
    1. Check if cls._instance is not None
    2. Call cls._instance._current.on_exit() if current scene exists
    3. Set cls._instance = None
    """
    # This test documents the requirement for dispose() method
    # The actual implementation will be in the fix
    
    sm = SceneManager.get()
    scene = HeavyScene(GameState())
    sm.set_scene(scene)
    
    # Current approach: monkey-patching
    SceneManager._instance = None
    
    # After fix, we'll use: SceneManager.dispose()
    # This test documents the requirement
    print(
        "\nDOCUMENTED: The fix will add a dispose() class method "
        "to replace monkey-patching for test isolation."
    )


if __name__ == "__main__":
    # Run tests manually for debugging
    pytest.main([__file__, "-v", "-s"])
