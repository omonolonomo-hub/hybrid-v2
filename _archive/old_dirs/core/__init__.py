"""
Core engine systems for Scene Manager architecture.

This package contains the foundational systems for the refactored game engine:
- Scene: Abstract base class for all game scenes
- SceneManager: Manages scene lifecycle and transitions
- InputState: Intent-based input abstraction
- HexSystem: Centralized hex coordinate math with cube rounding
- CoreGameState: SAVEABLE domain state
- UIState: THROWAWAY scene-local state
- AnimationSystem: Visual feedback management
- ActionSystem: Command pattern for state modifications
"""

from .scene import Scene
from .scene_manager import SceneManager
from .input_state import InputState
from .hex_system import HexSystem
from .core_game_state import CoreGameState
from .ui_state import UIState

__all__ = [
    'Scene',
    'SceneManager',
    'InputState',
    'HexSystem',
    'CoreGameState',
    'UIState',
]
