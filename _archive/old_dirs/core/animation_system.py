"""
Animation System

Manages all animations and provides visual feedback for game state changes.

CRITICAL: This is the missing piece for combat visualization and smooth UI feedback.
"""

from typing import List, Tuple
import pygame


class Animation:
    """Base class for all animations.
    
    All animations must:
    - Track elapsed time with delta time
    - Know when they're finished
    - Be able to draw themselves
    """
    
    def __init__(self, duration_ms: float):
        """Initialize animation.
        
        Args:
            duration_ms: Animation duration in milliseconds
        """
        self.duration_ms = duration_ms
        self.elapsed_ms = 0.0
        self.finished = False
    
    def update(self, dt: float) -> None:
        """Update animation progress.
        
        Args:
            dt: Delta time in milliseconds
        """
        self.elapsed_ms += dt
        if self.elapsed_ms >= self.duration_ms:
            self.finished = True
            self.elapsed_ms = self.duration_ms  # Clamp to duration
    
    def is_finished(self) -> bool:
        """Check if animation is complete.
        
        Returns:
            True if animation has finished
        """
        return self.finished
    
    def get_progress(self) -> float:
        """Get animation progress (0.0 to 1.0).
        
        Returns:
            Progress from 0.0 (start) to 1.0 (end)
        """
        if self.duration_ms <= 0:
            return 1.0
        return min(1.0, self.elapsed_ms / self.duration_ms)
    
    def draw(self, screen: pygame.Surface) -> None:
        """Render animation. Override in subclasses.
        
        Args:
            screen: Pygame surface to draw on
        """
        pass


class CardMoveAnimation(Animation):
    """Animates a card moving from one position to another.
    
    Uses linear interpolation for smooth movement.
    """
    
    def __init__(self, card, start_pos: Tuple[int, int], end_pos: Tuple[int, int], 
                 duration_ms: float = 300.0):
        """Initialize card move animation.
        
        Args:
            card: Card object being animated
            start_pos: Starting (x, y) position
            end_pos: Ending (x, y) position
            duration_ms: Animation duration in milliseconds
        """
        super().__init__(duration_ms)
        self.card = card
        self.start_pos = start_pos
        self.end_pos = end_pos
    
    def get_current_pos(self) -> Tuple[int, int]:
        """Get interpolated position.
        
        Returns:
            Current (x, y) position
        """
        t = self.get_progress()
        x = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * t
        y = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * t
        return (int(x), int(y))
    
    def draw(self, screen: pygame.Surface) -> None:
        """Draw card at interpolated position.
        
        Args:
            screen: Pygame surface to draw on
        """
        pos = self.get_current_pos()
        # TODO: Draw card at pos (implementation depends on renderer)
        # For now, just draw a placeholder circle
        pygame.draw.circle(screen, (255, 200, 0), pos, 10)


class FadeAnimation(Animation):
    """Animates alpha fade in/out.
    
    Can be used for fade in (0 -> 255) or fade out (255 -> 0).
    """
    
    def __init__(self, start_alpha: int, end_alpha: int, duration_ms: float = 500.0):
        """Initialize fade animation.
        
        Args:
            start_alpha: Starting alpha value (0-255)
            end_alpha: Ending alpha value (0-255)
            duration_ms: Animation duration in milliseconds
        """
        super().__init__(duration_ms)
        self.start_alpha = start_alpha
        self.end_alpha = end_alpha
    
    def get_current_alpha(self) -> int:
        """Get interpolated alpha value.
        
        Returns:
            Current alpha value (0-255)
        """
        t = self.get_progress()
        alpha = self.start_alpha + (self.end_alpha - self.start_alpha) * t
        return int(max(0, min(255, alpha)))


class ScaleAnimation(Animation):
    """Animates scale/size changes.
    
    Can be used for pop-in effects, pulse animations, etc.
    """
    
    def __init__(self, start_scale: float, end_scale: float, duration_ms: float = 200.0):
        """Initialize scale animation.
        
        Args:
            start_scale: Starting scale factor (1.0 = normal)
            end_scale: Ending scale factor
            duration_ms: Animation duration in milliseconds
        """
        super().__init__(duration_ms)
        self.start_scale = start_scale
        self.end_scale = end_scale
    
    def get_current_scale(self) -> float:
        """Get interpolated scale value.
        
        Returns:
            Current scale factor
        """
        t = self.get_progress()
        return self.start_scale + (self.end_scale - self.start_scale) * t


class AnimationSystem:
    """Manages all active animations.
    
    Responsibilities:
    - Add animations to the system
    - Update all animations with delta time
    - Remove finished animations
    - Render all active animations
    - Provide query for "is anything animating?"
    """
    
    def __init__(self):
        """Initialize animation system."""
        self.animations: List[Animation] = []
    
    def add(self, animation: Animation) -> None:
        """Add animation to system.
        
        Args:
            animation: Animation to add
        """
        self.animations.append(animation)
    
    def update(self, dt: float) -> None:
        """Update all animations.
        
        Args:
            dt: Delta time in milliseconds
        """
        # Update all animations
        for anim in self.animations:
            anim.update(dt)
        
        # Remove finished animations
        self.animations = [a for a in self.animations if not a.is_finished()]
    
    def draw(self, screen: pygame.Surface) -> None:
        """Draw all animations.
        
        Args:
            screen: Pygame surface to draw on
        """
        for anim in self.animations:
            anim.draw(screen)
    
    def is_animating(self) -> bool:
        """Check if any animations are active.
        
        Returns:
            True if any animations are running
        """
        return len(self.animations) > 0
    
    def clear(self) -> None:
        """Clear all animations.
        
        Useful for scene transitions or when resetting state.
        """
        self.animations.clear()
    
    def count(self) -> int:
        """Get number of active animations.
        
        Returns:
            Number of animations currently running
        """
        return len(self.animations)
