"""
UI Components Package

Refactored components for better separation of concerns.
"""

from v2.ui.audio_system import AudioSystem
from v2.ui.hover_control import HoverControl, HoverState

__all__ = [
    "AudioSystem",
    "HoverControl",
    "HoverState",
]
