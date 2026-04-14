"""
UI State

THROWAWAY state that is reset when scene changes.

CRITICAL RULE: This state is NOT saved, NOT preserved across scenes.
All UI-specific state (selections, hovers, animations) goes here.
"""

from typing import Optional, Tuple, Set, List, Dict, Any


class UIState:
    """THROWAWAY - reset when scene changes.
    
    This class contains ONLY UI state:
    - Card selections
    - Mouse hover state
    - Camera/view state
    - Temporary UI state
    - Animation timers
    
    NO domain state (game logic, player data) should be here.
    """
    
    def __init__(self):
        """Initialize fresh UI state.
        
        All values start at their default/empty state.
        This is called in Scene.on_enter() to create fresh state.
        """
        # Card selection state
        self.selected_hand_idx: Optional[int] = None
        self.selected_card = None
        
        # Mouse interaction state
        self.hovered_tile: Optional[Tuple[int, int]] = None  # (q, r) hex coordinate
        self.hovered_card_idx: Optional[int] = None
        self.hovered_hex: Optional[Tuple[int, int]] = None
        
        # Camera/view state
        self.camera_offset: Tuple[float, float] = (0.0, 0.0)
        self.zoom_level: float = 1.0
        
        # Temporary placement state
        self.pending_rotation: int = 0  # 0-5 for hex rotation
        self.placed_this_turn: int = 0
        self.locked_coords: Set[Tuple[int, int]] = set()
        self.is_placing: bool = False  # Whether in placement mode
        
        # Hex cards for combat scene (list of HexCard objects)
        self.hex_cards: List[Any] = []
        
        # Animation state (managed by AnimationSystem)
        self.is_animating: bool = False
        
        # Flash/highlight effects
        self.flash_timers: Dict[str, float] = {}  # key -> remaining time in ms
        
        # Drag state
        self.drag_start_pos: Optional[Tuple[int, int]] = None
        self.is_dragging: bool = False
        
        # Message/notification state
        self.message: str = ""
        self.message_timer: float = 0.0  # ms remaining
        
        # Lobby-specific state (only used in LobbyScene)
        self.strategies: List[str] = []
        self.hover_left: List[bool] = []
        self.hover_right: List[bool] = []
        self.hover_start: bool = False
        self.hover_rand: bool = False
        self.flash: List[int] = []
        self.time: float = 0.0
        
        # Shop-specific state (only used in ShopScene)
        self.shop_cards: List[Any] = []  # List of ShopCard instances
        self.hover_refresh: bool = False
        self.hover_done: bool = False
        self.hovered_market_card = None
        self.particles: List[Dict[str, Any]] = []
        self.fade_alpha: int = 0
        
        # Player panel state (used in GameLoopScene and CombatScene for T2.3b)
        self.player_panel_rects: List[Any] = []  # List of pygame.Rect for click detection
    
    def reset_turn_state(self) -> None:
        """Reset per-turn state variables.
        
        Called at the start of each turn to clear temporary state.
        """
        self.selected_hand_idx = None
        self.selected_card = None
        self.pending_rotation = 0
        self.placed_this_turn = 0
        self.hovered_tile = None
        self.hovered_card_idx = None
    
    def set_message(self, message: str, duration_ms: float = 2000.0) -> None:
        """Set a temporary message to display.
        
        Args:
            message: Message text
            duration_ms: How long to display in milliseconds
        """
        self.message = message
        self.message_timer = duration_ms
    
    def update_message_timer(self, dt: float) -> None:
        """Update message timer.
        
        Args:
            dt: Delta time in milliseconds
        """
        if self.message_timer > 0:
            self.message_timer = max(0, self.message_timer - dt)
            if self.message_timer == 0:
                self.message = ""
    
    def add_flash(self, key: str, duration_ms: float = 250.0) -> None:
        """Add a flash effect.
        
        Args:
            key: Identifier for the flash effect
            duration_ms: Duration in milliseconds
        """
        self.flash_timers[key] = duration_ms
    
    def update_flash_timers(self, dt: float) -> None:
        """Update all flash timers.
        
        Args:
            dt: Delta time in milliseconds
        """
        expired = []
        for key, remaining in self.flash_timers.items():
            new_remaining = remaining - dt
            if new_remaining <= 0:
                expired.append(key)
            else:
                self.flash_timers[key] = new_remaining
        
        for key in expired:
            del self.flash_timers[key]
    
    def get_flash_intensity(self, key: str) -> float:
        """Get flash intensity (0.0 to 1.0).
        
        Args:
            key: Flash effect identifier
        
        Returns:
            Intensity from 0.0 (expired) to 1.0 (just started)
        """
        if key not in self.flash_timers:
            return 0.0
        # Assume 250ms default duration for intensity calculation
        return min(1.0, self.flash_timers[key] / 250.0)
