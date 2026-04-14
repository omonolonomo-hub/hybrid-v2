"""
Scene Base Class

Abstract base class defining the lifecycle interface for all game scenes.
Scenes no longer control the game loop; instead, the game loop controls scenes
through well-defined lifecycle methods.
"""

from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from .scene_manager import SceneManager
    from .input_state import InputState


class Scene(ABC):
    """Abstract base class for all game scenes.
    
    Core Principles:
    - Scenes do NOT control the game loop
    - Scenes are controlled BY the game loop
    - Scenes have access to CoreGameState (SAVEABLE)
    - Scenes manage their own UIState (THROWAWAY)
    """
    
    def __init__(self, core_game_state: 'CoreGameState'):
        """Initialize scene with shared core game state.
        
        CRITICAL: core_game_state is stored by reference (same instance).
        No copying or serialization occurs.
        
        Args:
            core_game_state: SAVEABLE state that persists across scenes (by reference)
        
        Requirements:
        - 16.1: CoreGameState passed by reference
        - 16.4: No serialization or copying
        """
        # Requirement 16.1, 16.4: Store reference (not a copy)
        self.core_game_state = core_game_state
        self.ui_state: Optional['UIState'] = None  # THROWAWAY - created in on_enter
        self.scene_manager: Optional['SceneManager'] = None
    
    @abstractmethod
    def handle_input(self, input_state: 'InputState') -> None:
        """Process input intents for this scene.
        
        This method receives intent-based input (not raw events).
        Scenes should respond to intents like:
        - input_state.intent_confirm
        - input_state.intent_cancel
        - input_state.mouse_clicked
        
        Args:
            input_state: Intent-based input abstraction (not raw events)
        """
        pass
    
    @abstractmethod
    def update(self, dt: float) -> None:
        """Update scene logic with delta time.
        
        All time-based animations and movement must use dt for
        frame-independent behavior.
        
        Args:
            dt: Delta time in milliseconds since last frame
        """
        pass
    
    @abstractmethod
    def draw(self, screen: pygame.Surface) -> None:
        """Render scene to screen.
        
        Args:
            screen: Pygame surface to draw on
        """
        pass
    
    def on_enter(self) -> None:
        """Called when scene becomes active.
        
        Override this method to:
        - Create fresh UIState (THROWAWAY)
        - Initialize scene-specific resources
        - Set up scene-local state
        
        Default implementation creates empty UIState.
        """
        # Subclasses should create their own UIState here
        pass
    
    def on_exit(self) -> None:
        """Called when scene is deactivated.
        
        Override this method to:
        - Clean up scene-specific resources
        - Discard UIState (THROWAWAY)
        
        Default implementation discards UIState.
        """
        self.ui_state = None  # Explicitly discard THROWAWAY state
