"""
Scene Manager

Manages scene lifecycle, transitions, and delegates game loop calls to the active scene.

CRITICAL: Transition check happens BEFORE scene.update() to prevent double-update bug.
"""

from typing import Optional, Dict, Any, Callable
import pygame

from .scene import Scene
from .input_state import InputState


class SceneManager:
    """Manages scene transitions and delegates to active scene.
    
    Responsibilities:
    - Maintain reference to active scene
    - Delegate handle_input, update, draw to active scene
    - Handle scene transitions with proper lifecycle calls
    - Ensure CoreGameState is preserved, UIState is reset
    """
    
    # Valid scene transitions (from_scene, to_scene)
    VALID_TRANSITIONS = {
        ("lobby", "game_loop"),
        ("game_loop", "shop"),
        ("shop", "combat"),
        ("combat", "game_loop"),
        ("game_loop", "game_over"),
        ("game_over", "lobby"),
    }
    
    def __init__(self, initial_scene: Scene):
        """Initialize with starting scene.
        
        Args:
            initial_scene: The first scene to activate
        """
        self.active_scene: Scene = initial_scene
        self.active_scene.scene_manager = self
        self.active_scene.on_enter()
        self._transition_requested: Optional[tuple] = None
        
        # Scene factory registry
        self._scene_factories: Dict[str, Callable] = {}
    
    def register_scene_factory(self, scene_name: str, factory: Callable) -> None:
        """Register a scene factory function.
        
        Args:
            scene_name: Name to identify the scene
            factory: Callable that creates the scene (receives core_game_state, **kwargs)
        """
        self._scene_factories[scene_name] = factory
    
    def update(self, dt: float, input_state: InputState) -> None:
        """Update active scene and process transitions.
        
        CRITICAL: Check transition BEFORE update to prevent double-update bug.
        
        Args:
            dt: Delta time in milliseconds
            input_state: Intent-based input abstraction
        """
        # Handle input
        self.active_scene.handle_input(input_state)
        
        # CRITICAL: Check transition BEFORE update
        # This prevents the old scene from updating after requesting transition
        if self._transition_requested is not None:
            self._execute_transition()
            return  # Don't update old scene
        
        # Update scene
        self.active_scene.update(dt)
    
    def draw(self, screen: pygame.Surface) -> None:
        """Render active scene.
        
        Args:
            screen: Pygame surface to draw on
        """
        self.active_scene.draw(screen)
    
    def request_transition(self, scene_name: str, override_validation: bool = False, **kwargs) -> None:
        """Request transition to a new scene.
        
        The transition will be executed at the start of the next update cycle,
        BEFORE the old scene's update() is called.
        
        Args:
            scene_name: Name of scene to transition to
            override_validation: If True, skip transition validation (for testing)
            **kwargs: Additional data to pass to new scene
        """
        # Get current scene name
        current_scene_name = self._get_scene_name(self.active_scene)
        
        # Validate transition unless override is set
        if not override_validation:
            transition = (current_scene_name, scene_name)
            if transition not in self.VALID_TRANSITIONS:
                print(f"ERROR: Invalid scene transition: {current_scene_name} -> {scene_name}")
                print(f"Valid transitions from '{current_scene_name}': {self._get_valid_targets(current_scene_name)}")
                return
        
        self._transition_requested = (scene_name, kwargs)
    
    def _execute_transition(self) -> None:
        """Execute pending scene transition.
        
        Lifecycle:
        1. Exit current scene (discards UIState)
        2. Create new scene (preserves CoreGameState)
        3. Enter new scene (creates new UIState)
        4. Activate new scene
        """
        if self._transition_requested is None:
            return
        
        scene_name, kwargs = self._transition_requested
        self._transition_requested = None
        
        # Exit current scene (discards UIState)
        self.active_scene.on_exit()
        
        # Create new scene (preserves CoreGameState)
        new_scene = self._create_scene(scene_name, **kwargs)
        
        if new_scene is None:
            print(f"ERROR: Failed to create scene '{scene_name}'. Staying in current scene.")
            # Re-enter current scene to restore state
            self.active_scene.on_enter()
            return
        
        new_scene.scene_manager = self
        
        # Enter new scene (creates new UIState)
        new_scene.on_enter()
        
        # Activate new scene
        self.active_scene = new_scene
    
    def _create_scene(self, scene_name: str, **kwargs) -> Optional[Scene]:
        """Create a new scene instance.
        
        CRITICAL: CoreGameState is passed by reference (same instance).
        No serialization or copying occurs.
        
        Args:
            scene_name: Name of scene to create
            **kwargs: Additional data to pass to scene factory
        
        Returns:
            New scene instance, or None if scene_name not registered
        
        Requirements:
        - 16.1: CoreGameState passed by reference
        - 16.4: No serialization or copying
        """
        factory = self._scene_factories.get(scene_name)
        
        if factory is None:
            print(f"ERROR: Scene '{scene_name}' not registered in SceneManager.")
            print(f"Available scenes: {list(self._scene_factories.keys())}")
            return None
        
        try:
            # Requirement 16.1, 16.4: Pass CoreGameState by reference (same instance)
            core_game_state = self.active_scene.core_game_state
            
            # Verify it's the same instance (not a copy)
            core_game_state_id = id(core_game_state)
            
            new_scene = factory(core_game_state, **kwargs)
            
            # Verify new scene received the same instance
            if new_scene is not None:
                assert id(new_scene.core_game_state) == core_game_state_id, \
                    "CoreGameState was copied instead of passed by reference"
            
            return new_scene
        except Exception as e:
            print(f"ERROR: Failed to create scene '{scene_name}': {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_scene_name(self, scene: Scene) -> str:
        """Get the registered name of a scene instance.
        
        Args:
            scene: Scene instance to identify
        
        Returns:
            Scene name, or "unknown" if not found
        """
        # Try to get scene name from class name (convert CamelCase to snake_case)
        class_name = scene.__class__.__name__
        
        # Convert CamelCase to snake_case
        # LobbyScene -> lobby_scene -> lobby
        # GameLoopScene -> game_loop_scene -> game_loop
        # MockLobbyScene -> mock_lobby_scene -> lobby (remove mock_ prefix)
        import re
        snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()
        
        # Remove "mock_" prefix if present (for testing)
        if snake_case.startswith("mock_"):
            snake_case = snake_case[5:]
        
        # Remove "_scene" suffix if present
        if snake_case.endswith("_scene"):
            snake_case = snake_case[:-6]
        
        return snake_case
    
    def _get_valid_targets(self, from_scene: str) -> list:
        """Get list of valid target scenes from a given scene.
        
        Args:
            from_scene: Source scene name
        
        Returns:
            List of valid target scene names
        """
        return [to_scene for (from_s, to_scene) in self.VALID_TRANSITIONS if from_s == from_scene]
