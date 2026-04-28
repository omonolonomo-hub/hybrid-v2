"""
CameraController - Isolated camera state and input handling.

Manages zoom, pan, offset state without coupling to scene logic.
"""
from dataclasses import dataclass
from typing import Tuple
import pygame


@dataclass
class CameraState:
    """Camera state snapshot."""
    zoom: float = 1.0
    offset_x: float = 0.0
    offset_y: float = 0.0
    min_zoom: float = 0.5
    max_zoom: float = 3.0


@dataclass
class WorldDragState:
    """World drag (pan) state."""
    active: bool = False
    last_pos: Tuple[int, int] = (0, 0)


class CameraController:
    """
    Camera controller with zoom, pan, and keyboard controls.
    
    Usage:
        camera = CameraController()
        
        # Handle events
        camera.handle_scroll(event)  # Mouse wheel
        camera.handle_drag_start(event.pos)
        camera.handle_drag_move(event.pos)
        camera.handle_drag_end()
        
        # Update (keyboard controls)
        camera.update(dt_ms, keys=pygame.key.get_pressed())
        
        # Access state
        zoom = camera.zoom
        offset = camera.offset
        
        # World-to-screen conversion
        screen_x, screen_y = camera.world_to_screen(world_x, world_y)
    """

    def __init__(
        self,
        zoom: float = 1.0,
        min_zoom: float = 0.5,
        max_zoom: float = 3.0,
        pan_speed: float = 1000.0,
        zoom_speed: float = 1.5,
    ):
        """
        Args:
            zoom: Initial zoom level
            min_zoom: Minimum zoom level
            max_zoom: Maximum zoom level
            pan_speed: Pan speed (pixels/sec at zoom=1.0)
            zoom_speed: Zoom speed (units/sec)
        """
        self._state = CameraState(
            zoom=zoom,
            offset_x=0.0,
            offset_y=0.0,
            min_zoom=min_zoom,
            max_zoom=max_zoom,
        )
        self._drag = WorldDragState()
        self._pan_speed = pan_speed
        self._zoom_speed = zoom_speed
        self._dirty = False

    def handle_scroll(self, event: pygame.event.Event, mouse_pos: Tuple[int, int], origin: Tuple[int, int]) -> bool:
        """
        Handle mouse wheel scroll for zoom.
        
        Args:
            event: Pygame MOUSEWHEEL event
            mouse_pos: Current mouse position
            origin: World origin point (for zoom pivot)
            
        Returns:
            True if zoom changed
        """
        if event.type != pygame.MOUSEWHEEL:
            return False

        zoom_delta = 0.1 if event.y > 0 else -0.1
        return self._apply_zoom(zoom_delta, mouse_pos, origin)

    def handle_drag_start(self, mouse_pos: Tuple[int, int]) -> None:
        """Start world drag (pan)."""
        self._drag = WorldDragState(active=True, last_pos=mouse_pos)

    def handle_drag_move(self, mouse_pos: Tuple[int, int]) -> bool:
        """
        Update world drag position.
        
        Returns:
            True if camera moved
        """
        if not self._drag.active:
            return False

        dx = mouse_pos[0] - self._drag.last_pos[0]
        dy = mouse_pos[1] - self._drag.last_pos[1]
        self._state.offset_x += dx
        self._state.offset_y += dy
        self._drag = WorldDragState(active=True, last_pos=mouse_pos)
        self._dirty = True
        return True

    def handle_drag_end(self) -> None:
        """End world drag."""
        self._drag = WorldDragState()

    def update(self, dt_ms: float, keys: pygame.key.ScancodeWrapper, origin: tuple[int, int] = (0, 0)) -> bool:
        """
        Update camera with keyboard controls.
        
        Args:
            dt_ms: Delta time (milliseconds)
            keys: Pygame key state (from pygame.key.get_pressed())
            origin: World origin point for zoom pivot
            
        Returns:
            True if camera state changed
        """
        dt_sec = dt_ms / 1000.0
        changed = False

        # Pan controls (WASD)
        pan_delta = (self._pan_speed / self._state.zoom) * dt_sec
        old_offset = (self._state.offset_x, self._state.offset_y)

        if keys[pygame.K_w]:
            self._state.offset_y += pan_delta
        if keys[pygame.K_s]:
            self._state.offset_y -= pan_delta
        if keys[pygame.K_a]:
            self._state.offset_x += pan_delta
        if keys[pygame.K_d]:
            self._state.offset_x -= pan_delta

        if (self._state.offset_x, self._state.offset_y) != old_offset:
            changed = True
            self._dirty = True

        # Zoom controls (Q/E or -/+)
        zoom_delta = self._zoom_speed * dt_sec
        if keys[pygame.K_q] or keys[pygame.K_MINUS]:
            if self._apply_zoom(-zoom_delta, pygame.mouse.get_pos(), origin):
                changed = True
        if keys[pygame.K_e] or keys[pygame.K_PLUS] or keys[pygame.K_KP_PLUS]:
            if self._apply_zoom(zoom_delta, pygame.mouse.get_pos(), origin):
                changed = True

        return changed

    def reset(self) -> None:
        """Reset camera to default state."""
        self._state.zoom = 1.0
        self._state.offset_x = 0.0
        self._state.offset_y = 0.0
        self._dirty = True

    def _apply_zoom(self, zoom_delta: float, mouse_pos: Tuple[int, int], origin: Tuple[int, int]) -> bool:
        """
        Apply zoom with pivot point.
        
        Args:
            zoom_delta: Zoom change amount
            mouse_pos: Mouse position (pivot point)
            origin: World origin
            
        Returns:
            True if zoom changed
        """
        old_zoom = self._state.zoom
        new_zoom = max(self._state.min_zoom, min(self._state.max_zoom, old_zoom + zoom_delta))

        if old_zoom == new_zoom:
            return False

        # Zoom toward mouse position
        mx, my = mouse_pos
        ox, oy = origin
        rel_x, rel_y = mx - ox, my - oy
        ratio = new_zoom / old_zoom
        self._state.offset_x = rel_x - ratio * (rel_x - self._state.offset_x)
        self._state.offset_y = rel_y - ratio * (rel_y - self._state.offset_y)
        self._state.zoom = new_zoom
        self._dirty = True
        return True

    def world_to_screen(self, world_x: float, world_y: float, origin: Tuple[int, int]) -> Tuple[float, float]:
        """
        Convert world coordinates to screen coordinates.
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            origin: World origin point
            
        Returns:
            (screen_x, screen_y)
        """
        ox, oy = origin
        screen_x = ox + (world_x * self._state.zoom) + self._state.offset_x
        screen_y = oy + (world_y * self._state.zoom) + self._state.offset_y
        return screen_x, screen_y

    def screen_to_world(self, screen_x: float, screen_y: float, origin: Tuple[int, int]) -> Tuple[float, float]:
        """
        Convert screen coordinates to world coordinates.
        
        Args:
            screen_x: Screen X coordinate
            screen_y: Screen Y coordinate
            origin: World origin point
            
        Returns:
            (world_x, world_y)
        """
        ox, oy = origin
        world_x = (screen_x - ox - self._state.offset_x) / self._state.zoom
        world_y = (screen_y - oy - self._state.offset_y) / self._state.zoom
        return world_x, world_y

    @property
    def zoom(self) -> float:
        """Current zoom level."""
        return self._state.zoom

    @property
    def offset(self) -> Tuple[float, float]:
        """Current offset (x, y)."""
        return (self._state.offset_x, self._state.offset_y)

    @property
    def offset_x(self) -> float:
        """Current X offset."""
        return self._state.offset_x

    @property
    def offset_y(self) -> float:
        """Current Y offset."""
        return self._state.offset_y

    @property
    def is_dragging(self) -> bool:
        """Is world drag active?"""
        return self._drag.active

    @property
    def is_dirty(self) -> bool:
        """Has camera state changed since last clear?"""
        return self._dirty

    def clear_dirty(self) -> None:
        """Clear dirty flag."""
        self._dirty = False

    def get_state(self) -> CameraState:
        """Get camera state snapshot."""
        return self._state
