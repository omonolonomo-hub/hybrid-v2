"""
Input State

Intent-based input abstraction that translates raw pygame events into game intents.

CRITICAL: This is NOT just an event wrapper. It provides intent abstraction,
making the system AI/replay/network ready.
"""

from typing import Tuple, Dict, List
import pygame


class InputState:
    """Intent-based input abstraction (not just event wrapper).
    
    Key Principle: event ≠ intent
    
    This class translates raw pygame events into game intents:
    - Multiple input sources can trigger the same intent
    - Intents are testable and replayable
    - AI can generate intents without knowing input details
    """
    
    def __init__(self, events: List[pygame.event.Event]):
        """Translate events into intents.
        
        Args:
            events: Raw pygame events from pygame.event.get()
        """
        # Mouse state
        self.mouse_pos: Tuple[int, int] = pygame.mouse.get_pos()
        self.mouse_down: bool = False  # Button is held
        self.mouse_clicked: bool = False  # Button was pressed THIS FRAME
        self.mouse_released: bool = False  # Button was released THIS FRAME
        self.right_clicked: bool = False  # Right button was pressed THIS FRAME
        
        # Keyboard state
        self.keys_pressed = pygame.key.get_pressed()
        self.key_down_events: Dict[int, bool] = {}  # Key -> True for keys pressed this frame
        
        # Intent flags (derived from events)
        self.intent_confirm: bool = False  # Enter, Space, or Left Click
        self.intent_cancel: bool = False  # Escape or Right Click
        self.intent_rotate_cw: bool = False  # R key
        self.intent_rotate_ccw: bool = False  # Shift+R
        
        # Game-specific intents
        self.intent_toggle_fast_mode: bool = False  # F key
        self.intent_open_shop: bool = False  # S key
        self.intent_switch_player: int = -1  # 1-8 keys (0-7 index, -1 = no switch)
        
        # Process events to set intents
        self._process_events(events)
    
    def _process_events(self, events: List[pygame.event.Event]) -> None:
        """Process raw events and set intent flags.
        
        Args:
            events: List of pygame events
        """
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.mouse_clicked = True
                    self.mouse_down = True
                    self.intent_confirm = True
                elif event.button == 3:  # Right click
                    self.right_clicked = True
                    self.intent_cancel = True
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.mouse_released = True
                    self.mouse_down = False
            
            elif event.type == pygame.KEYDOWN:
                self.key_down_events[event.key] = True
                
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    self.intent_confirm = True
                elif event.key == pygame.K_ESCAPE:
                    self.intent_cancel = True
                elif event.key == pygame.K_r:
                    if event.mod & pygame.KMOD_SHIFT:
                        self.intent_rotate_ccw = True
                    else:
                        self.intent_rotate_cw = True
                elif event.key == pygame.K_f:
                    self.intent_toggle_fast_mode = True
                elif event.key == pygame.K_s:
                    self.intent_open_shop = True
                elif event.key == pygame.K_1:
                    self.intent_switch_player = 0
                elif event.key == pygame.K_2:
                    self.intent_switch_player = 1
                elif event.key == pygame.K_3:
                    self.intent_switch_player = 2
                elif event.key == pygame.K_4:
                    self.intent_switch_player = 3
                elif event.key == pygame.K_5:
                    self.intent_switch_player = 4
                elif event.key == pygame.K_6:
                    self.intent_switch_player = 5
                elif event.key == pygame.K_7:
                    self.intent_switch_player = 6
                elif event.key == pygame.K_8:
                    self.intent_switch_player = 7
    
    def is_key_pressed(self, key: int) -> bool:
        """Check if key is currently held down.
        
        Args:
            key: Pygame key constant (e.g., pygame.K_SPACE)
        
        Returns:
            True if key is held down
        """
        return bool(self.keys_pressed[key])
    
    def was_key_pressed_this_frame(self, key: int) -> bool:
        """Check if key was pressed THIS FRAME.
        
        Args:
            key: Pygame key constant
        
        Returns:
            True if key was pressed this frame
        """
        return self.key_down_events.get(key, False)
    
    def is_fast_mode_toggled(self) -> bool:
        """Check if fast mode toggle was requested this frame.
        
        Returns:
            True if F key was pressed this frame
        """
        return self.intent_toggle_fast_mode
    
    def is_shop_requested(self) -> bool:
        """Check if shop open was requested this frame.
        
        Returns:
            True if S key was pressed this frame
        """
        return self.intent_open_shop
    
    def get_player_switch_request(self) -> int:
        """Get player switch request from 1-8 keys.
        
        Returns:
            Player index (0-7) if switch requested, -1 otherwise
        """
        return self.intent_switch_player
