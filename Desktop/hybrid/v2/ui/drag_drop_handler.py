"""
DragDropHandler - Type-safe drag & drop state management.

Replaces dict-based drag_state anti-pattern with typed dataclass.
"""
from dataclasses import dataclass
from typing import Optional, Any, Tuple
import pygame


@dataclass
class DragState:
    """Immutable drag state snapshot."""
    active: bool = False
    source_panel: Optional[str] = None  # "hand", "shop", "board"
    source_index: int = -1
    mouse_pos: Tuple[int, int] = (0, 0)
    card_rect: Optional[pygame.Rect] = None
    rotation: int = 0
    card_data: Optional[Any] = None


class DragDropHandler:
    """
    Drag & drop state manager with type-safe API.
    
    Usage:
        handler = DragDropHandler()
        
        # Start drag
        handler.start("hand", slot_idx=2, pos=(100, 200), card_data=card_info)
        
        # Update position
        handler.update_position((150, 250))
        
        # Rotate (right-click)
        handler.rotate()
        
        # Drop
        result = handler.drop()
        if result:
            source_panel, source_idx, rotation, card_data = result
            # Handle drop...
        
        # Cancel
        handler.cancel()
    """

    def __init__(self):
        self._state = DragState()

    def start(
        self,
        source_panel: str,
        source_index: int,
        mouse_pos: Tuple[int, int],
        card_rect: Optional[pygame.Rect] = None,
        card_data: Optional[Any] = None,
    ) -> None:
        """
        Start dragging an item.
        
        Args:
            source_panel: Panel name ("hand", "shop", "board")
            source_index: Slot/coordinate index
            mouse_pos: Current mouse position
            card_rect: Optional card rectangle
            card_data: Optional card data snapshot
        """
        self._state = DragState(
            active=True,
            source_panel=source_panel,
            source_index=source_index,
            mouse_pos=mouse_pos,
            card_rect=card_rect,
            rotation=0,
            card_data=card_data,
        )

    def update_position(self, mouse_pos: Tuple[int, int]) -> None:
        """Update drag position."""
        if self._state.active:
            self._state = DragState(
                active=self._state.active,
                source_panel=self._state.source_panel,
                source_index=self._state.source_index,
                mouse_pos=mouse_pos,
                card_rect=self._state.card_rect,
                rotation=self._state.rotation,
                card_data=self._state.card_data,
            )

    def rotate(self) -> None:
        """Rotate dragged item (cycles 0-5 for hex rotation)."""
        if self._state.active:
            self._state = DragState(
                active=self._state.active,
                source_panel=self._state.source_panel,
                source_index=self._state.source_index,
                mouse_pos=self._state.mouse_pos,
                card_rect=self._state.card_rect,
                rotation=(self._state.rotation + 1) % 6,
                card_data=self._state.card_data,
            )

    def drop(self) -> Optional[Tuple[str, int, int, Any]]:
        """
        Complete the drag operation.
        
        Returns:
            Tuple of (source_panel, source_index, rotation, card_data) if active,
            None otherwise.
        """
        if not self._state.active:
            return None

        result = (
            self._state.source_panel,
            self._state.source_index,
            self._state.rotation,
            self._state.card_data,
        )
        self._state = DragState()  # Reset
        return result

    def cancel(self) -> None:
        """Cancel the drag operation."""
        self._state = DragState()

    @property
    def is_active(self) -> bool:
        """Is drag currently active?"""
        return self._state.active

    @property
    def state(self) -> DragState:
        """Get current drag state snapshot."""
        return self._state

    @property
    def source_panel(self) -> Optional[str]:
        """Get source panel name."""
        return self._state.source_panel if self._state.active else None

    @property
    def source_index(self) -> int:
        """Get source index."""
        return self._state.source_index if self._state.active else -1

    @property
    def mouse_pos(self) -> Tuple[int, int]:
        """Get current mouse position."""
        return self._state.mouse_pos

    @property
    def rotation(self) -> int:
        """Get current rotation."""
        return self._state.rotation

    @property
    def card_data(self) -> Optional[Any]:
        """Get card data snapshot."""
        return self._state.card_data
