"""
CombatScene - 37-Hex Radial Grid Combat Visualization

This scene displays a 37-hex radial grid (radius=3) for tactical combat visualization
in a pygame-based autochess game. It integrates with CoreGameState and HexSystem to
provide a deterministic, crash-proof rendering environment.

Architecture:
- Extends Scene base class with proper lifecycle methods
- Uses HexSystem for coordinate conversion and geometry
- Maintains UIState for throwaway animation/interaction state
- Reads from CoreGameState as single source of truth
"""

from typing import Optional, Tuple, TYPE_CHECKING, Dict
from dataclasses import dataclass, field
from enum import Enum
import pygame
import math

from core.scene import Scene
from core.core_game_state import CoreGameState
from core.ui_state import UIState
from core.input_state import InputState
from core.hex_system import HexSystem

if TYPE_CHECKING:
    from core.scene_manager import SceneManager


class InputMode(Enum):
    """Input mode states for the combat scene.
    
    Defines the different input handling modes that determine how user input
    is processed and routed to appropriate handlers.
    
    Requirements:
    - 15.1: Define input mode states for state machine
    """
    NORMAL = "normal"           # Default mode: hover, debug toggle, scene navigation
    PLACING = "placing"         # Card placement mode: preview, rotation, placement
    CARD_DETAIL = "card_detail" # Card detail view mode: inspect card stats
    PAUSED = "paused"           # Pause menu mode: game paused


@dataclass
class HexCard:
    """Data structure representing a card placed on a hex with rendering information.
    
    Attributes:
        hex_coord: Axial (q, r) coordinate of the hex
        card_data: Reference to the Card object from CoreGameState
        front_image: Pygame surface for card front
        back_image: Pygame surface for card back
        position: Pixel (x, y) position for rendering
        hex_size: Size of the hex for rendering calculations
        rotation: Rotation angle in degrees (0, 60, 120, 180, 240, 300)
        placement_state: State of card placement (e.g., "placed", "preview")
        is_rotation_locked: Whether rotation is locked after placement
        flip_value: Current flip animation value (0.0 = back, 1.0 = front)
        flip_value_eased: Eased flip value for smooth animation
    """
    hex_coord: Tuple[int, int]
    card_data: any  # Card object from CoreGameState
    front_image: pygame.Surface
    back_image: pygame.Surface
    position: Tuple[float, float]
    hex_size: float
    rotation: int = 0
    placement_state: str = "placed"
    is_rotation_locked: bool = False
    flip_value: float = 0.0
    flip_value_eased: float = 0.0


class LayoutCalculator:
    """Helper class for calculating hex grid layout with safety margins.
    
    Provides deterministic layout calculations to ensure the 37-hex grid
    fits within available screen space without overlapping UI panels.
    
    Requirements:
    - 1.3: Calculate hex_size with 15% safety margin
    - 1.4: Calculate grid origin for exact centering
    - 2.6: Verify no overlap between grid and UI panels
    """
    
    @staticmethod
    def calculate_hex_size(available_width: float, available_height: float, 
                          grid_radius: int) -> float:
        """Calculate optimal hex size with 15% safety margin.
        
        Uses the grid radius to determine the bounding box in hex units,
        then calculates the maximum hex size that fits within the available
        space. Applies a 15% safety margin to prevent edge cases.
        
        Args:
            available_width: Available horizontal space in pixels
            available_height: Available vertical space in pixels
            grid_radius: Radius of the radial hex grid (3 for 37 hexes)
        
        Returns:
            Optimal hex_size in pixels with safety margin applied
        
        Requirements:
        - 1.3: Apply 15% safety margin to calculated hex_size
        """
        # Maximum grid extent for given radius
        max_q_extent = grid_radius
        max_r_extent = grid_radius
        
        # Bounding box in hex units (flat-top orientation)
        grid_width_in_hexes = 2 * max_q_extent + 1
        grid_height_in_hexes = 2 * max_r_extent + 1
        
        # Calculate hex_size to fit grid in available space
        # For flat-top hexes: width = sqrt(3) * hex_size, height = 1.5 * hex_size
        sqrt_3 = math.sqrt(3)
        hex_size_by_width = available_width / (sqrt_3 * grid_width_in_hexes)
        hex_size_by_height = available_height / (1.5 * grid_height_in_hexes + 0.5)
        
        # Take minimum and apply 15% safety margin
        hex_size = min(hex_size_by_width, hex_size_by_height) * 0.85
        
        return hex_size
    
    @staticmethod
    def calculate_grid_origin(grid_area: Dict[str, float]) -> Tuple[float, float]:
        """Calculate grid origin at exact center of available area.
        
        Args:
            grid_area: Dictionary with keys 'left', 'right', 'top', 'bottom'
        
        Returns:
            Tuple of (origin_x, origin_y) at the center of grid_area
        
        Requirements:
        - 1.4: Position grid origin at exact center of available area
        """
        origin_x = (grid_area['left'] + grid_area['right']) / 2
        origin_y = (grid_area['top'] + grid_area['bottom']) / 2
        
        return origin_x, origin_y
    
    @staticmethod
    def verify_no_overlap(hex_size: float, origin: Tuple[float, float], 
                         grid_area: Dict[str, float], radius: int,
                         left_panel_width: int, right_panel_width: int,
                         top_margin: int, bottom_hub_height: int,
                         screen_width: int, screen_height: int) -> None:
        """Verify grid bounds do not overlap with UI panels.
        
        Calculates the actual pixel bounds of the hex grid and asserts
        that it stays within the available grid area without overlapping
        any UI panels.
        
        Args:
            hex_size: Size of each hex in pixels
            origin: Tuple of (origin_x, origin_y)
            grid_area: Dictionary with grid boundaries
            radius: Grid radius (3 for 37 hexes)
            left_panel_width: Width of left UI panel
            right_panel_width: Width of right UI panel
            top_margin: Top margin height
            bottom_hub_height: Bottom hub height
            screen_width: Total screen width
            screen_height: Total screen height
        
        Raises:
            AssertionError: If grid overlaps with any UI panel
        
        Requirements:
        - 2.6: Assert no overlap between grid bounds and panel boundaries
        """
        origin_x, origin_y = origin
        
        # Calculate grid extent in hex units
        grid_width_in_hexes = 2 * radius + 1
        grid_height_in_hexes = 2 * radius + 1
        
        # Calculate actual grid bounds in pixels
        sqrt_3 = math.sqrt(3)
        grid_pixel_width = sqrt_3 * hex_size * grid_width_in_hexes
        grid_pixel_height = 1.5 * hex_size * grid_height_in_hexes
        
        grid_left = origin_x - grid_pixel_width / 2
        grid_right = origin_x + grid_pixel_width / 2
        grid_top = origin_y - grid_pixel_height / 2
        grid_bottom = origin_y + grid_pixel_height / 2
        
        # Verify no overlap with UI panels
        assert grid_left >= left_panel_width, \
            f"Grid overlaps left panel: grid_left={grid_left:.1f}, panel_width={left_panel_width}"
        
        assert grid_right <= screen_width - right_panel_width, \
            f"Grid overlaps right panel: grid_right={grid_right:.1f}, panel_edge={screen_width - right_panel_width}"
        
        assert grid_top >= top_margin, \
            f"Grid overlaps top margin: grid_top={grid_top:.1f}, margin={top_margin}"
        
        assert grid_bottom <= screen_height - bottom_hub_height, \
            f"Grid overlaps bottom hub: grid_bottom={grid_bottom:.1f}, hub_edge={screen_height - bottom_hub_height}"




class AnimationController:
    """Controller for managing flip animations on hex cards.
    
    Handles smooth interpolation of flip values based on hover state.
    Uses cosine easing for natural animation feel.
    
    Requirements:
    - 9.1: Update flip animations based on hovered_hex from UIState
    - 9.2: Interpolate flip_value toward target (1.0 if hovered, 0.0 otherwise)
    - 9.3: Apply cosine easing for smooth animation
    - 9.4: Complete animation in 0.3 seconds
    """
    
    def __init__(self, ui_state: UIState):
        """Initialize AnimationController with UIState reference.
        
        Args:
            ui_state: Reference to UIState for reading hovered_hex
        """
        self.ui_state = ui_state
        self.flip_speed = 1.0 / 300.0  # Complete in 300ms (0.3 seconds)
    
    def update_flip_animations(self, hex_cards: list, dt: float) -> None:
        """Update flip animations for all hex cards.
        
        For each hex_card:
        - Determine target flip value (1.0 if hovered, 0.0 otherwise)
        - Skip animation if already at target (dirty flag optimization)
        - Interpolate current flip_value toward target
        - Apply cosine easing: flip_value_eased = (1 - cos(π * flip_value)) / 2
        
        Args:
            hex_cards: List of HexCard objects to update
            dt: Delta time in milliseconds since last frame
        
        Requirements:
        - 9.2: Interpolate flip_value toward target using flip_speed * dt
        - 9.3: Apply cosine easing
        - 9.4: Complete in 0.3 seconds
        - 17.2: Skip animation update if flip_value already at target (dirty flag optimization)
        """
        import math
        
        hovered_hex = self.ui_state.hovered_hex
        
        for hex_card in hex_cards:
            # Determine target flip value
            target_flip = 1.0 if hex_card.hex_coord == hovered_hex else 0.0
            
            # Skip entire update if already at target (dirty flag optimization, Requirement 17.2)
            # Use threshold of 0.01 for "close enough"
            if abs(hex_card.flip_value - target_flip) < 0.01:
                # Already at target, skip all animation updates
                continue
            
            # Interpolate toward target
            if hex_card.flip_value < target_flip:
                hex_card.flip_value = min(target_flip, hex_card.flip_value + self.flip_speed * dt)
            else:
                hex_card.flip_value = max(target_flip, hex_card.flip_value - self.flip_speed * dt)
            
            # Apply cosine easing
            hex_card.flip_value_eased = self._apply_cosine_easing(hex_card.flip_value)
    
    def _apply_cosine_easing(self, t: float) -> float:
        """Apply cosine easing function.
        
        Formula: (1 - cos(π * t)) / 2
        
        Args:
            t: Input value in range [0.0, 1.0]
        
        Returns:
            Eased value in range [0.0, 1.0]
        
        Requirement 9.3: Apply cosine easing
        """
        import math
        return (1.0 - math.cos(math.pi * t)) / 2.0


class PlacementController:
    """Controller for managing card placement and rotation mechanics.
    
    Handles card selection, placement preview, rotation, and validation
    of placement positions on the hex grid.
    
    Requirements:
    - 5.1: Handle card selection and placement mode
    - 5.2: Validate placement positions
    - 5.3: Handle rotation with right-click
    - 5.4: Place cards with locked rotation
    - 6.1: Lock rotation after placement
    """
    
    def __init__(self, core_game_state: CoreGameState, ui_state: UIState, hex_system: HexSystem):
        """Initialize PlacementController with required references.
        
        Args:
            core_game_state: Reference to CoreGameState for board access
            ui_state: Reference to UIState for placement state
            hex_system: Reference to HexSystem for coordinate validation
        
        Requirement 5.1, 5.2: Store references to dependencies
        """
        self.core_game_state = core_game_state
        self.ui_state = ui_state
        self.hex_system = hex_system
        
        # Placement state
        self.selected_card = None
        self.preview_hex: Optional[Tuple[int, int]] = None
        self.preview_rotation: int = 0  # 0, 60, 120, 180, 240, 300 degrees
    
    def handle_card_selection(self, card) -> None:
        """Handle card selection to enter placement mode.
        
        Stores the selected card reference, resets preview rotation,
        and updates UIState to indicate placement mode is active.
        
        Args:
            card: Card object to be placed
        
        Requirement 5.1: Store selected card and enter placement mode
        """
        self.selected_card = card
        self.preview_rotation = 0
        # Note: UIState doesn't have is_placing field yet, but we store the state here
        # The CombatScene will manage the input mode transition
    
    def is_valid_placement(self, hex_coord: Tuple[int, int], current_player_id: int) -> bool:
        """Check if a hex coordinate is valid for card placement.
        
        Validates that:
        1. Hex is in the grid (within radius 3)
        2. Hex is empty (not in board.grid)
        3. Hex is within player's board area
        
        Args:
            hex_coord: (q, r) axial coordinate to validate
            current_player_id: ID of the current player
        
        Returns:
            True if placement is valid, False otherwise
        
        Requirements:
        - 5.2: Check if hex is in grid and empty
        - 7.1: Check if hex is within player's board area
        """
        q, r = hex_coord
        
        # Check if hex is in grid (radius 3 = 37 hexes)
        # Distance from center (0, 0) must be <= 3
        distance = (abs(q) + abs(r) + abs(-q - r)) // 2
        if distance > 3:
            return False
        
        # Get current player's board
        if current_player_id >= len(self.core_game_state.game.players):
            return False
        
        current_player = self.core_game_state.game.players[current_player_id]
        board = current_player.board
        
        # Check if hex is empty (not in board.grid)
        if hex_coord in board.grid and board.grid[hex_coord] is not None:
            return False
        
        # TODO: Check if hex is within player's board area
        # For now, all hexes in the grid are valid for any player
        # This can be extended later with player-specific board areas
        
        return True
    
    def handle_right_click(self) -> None:
        """Handle right-click to rotate preview card.
        
        Increments preview rotation by 60 degrees clockwise,
        wrapping around at 360 degrees.
        
        Requirement 5.3: Rotate preview card by 60 degrees on right-click
        """
        self.preview_rotation = (self.preview_rotation + 60) % 360
    
    def can_rotate_card(self, hex_card: HexCard) -> bool:
        """Check if a card can be rotated.
        
        Returns True only if the card's rotation is not locked.
        Once a card is placed, its rotation is permanently locked.
        
        Args:
            hex_card: HexCard object to check
        
        Returns:
            True if rotation is not locked, False otherwise
        
        Requirement 6.2: Prevent rotation changes when is_rotation_locked is True
        """
        return not hex_card.is_rotation_locked
    
    def handle_left_click(self, hex_coord: Tuple[int, int], current_player_id: int, 
                         asset_loader, hex_size: float) -> bool:
        """Handle left-click to place card at hex coordinate.
        
        Validates placement, adds card to board.grid, creates HexCard
        with locked rotation, and updates UIState.
        
        Args:
            hex_coord: (q, r) axial coordinate for placement
            current_player_id: ID of the current player
            asset_loader: AssetLoader for loading card images
            hex_size: Size of hex for HexCard creation
        
        Returns:
            True if placement successful, False otherwise
        
        Requirements:
        - 5.4: Place card and lock rotation
        - 6.1: Set is_rotation_locked to True
        """
        # Validate placement
        if not self.is_valid_placement(hex_coord, current_player_id):
            return False
        
        if self.selected_card is None:
            return False
        
        # Get current player's board
        current_player = self.core_game_state.game.players[current_player_id]
        board = current_player.board
        
        # Add card to board.grid
        board.grid[hex_coord] = self.selected_card
        
        # Load card images using AssetLoader
        card_name = self.selected_card.name
        faces = asset_loader.get(card_name)
        front_image = faces.front
        back_image = faces.back
        
        # Calculate pixel position
        pixel_x, pixel_y = self.hex_system.hex_to_pixel(hex_coord[0], hex_coord[1])
        
        # Create HexCard with locked rotation
        hex_card = HexCard(
            hex_coord=hex_coord,
            card_data=self.selected_card,
            front_image=front_image,
            back_image=back_image,
            position=(pixel_x, pixel_y),
            hex_size=hex_size,
            rotation=self.preview_rotation,
            placement_state="placed",
            is_rotation_locked=True,  # Lock rotation after placement
            flip_value=0.0,
            flip_value_eased=0.0
        )
        
        # Add HexCard to UIState (assuming hex_cards list exists)
        # Note: This assumes CombatScene maintains hex_cards list
        # The actual implementation may need to be adjusted based on scene structure
        
        # Clear placement state
        self.selected_card = None
        self.preview_hex = None
        self.preview_rotation = 0
        
        return True


class HexCardRenderer:
    """Renderer for hex cards with flip animation support.
    
    Handles rendering of card images with horizontal flip animation,
    hex borders, and proper scaling/positioning.
    
    Requirements:
    - 9.5: Render cards with flip animation
    - 9.6: Switch between front/back images based on flip_value
    - 17.1: Performance optimization with early exits
    """
    
    def __init__(self, hex_system):
        """Initialize HexCardRenderer.
        
        Args:
            hex_system: HexSystem instance for coordinate conversion
        
        Requirement 9.5: Store reference to HexSystem
        """
        self.hex_system = hex_system
    
    def render_card(self, screen: pygame.Surface, hex_card: HexCard, flip_value_eased: float) -> None:
        """Render a single card with flip animation.
        
        Determines which image to show based on flip_value, applies horizontal
        scaling for flip effect, and blits the scaled image centered at card position.
        
        Args:
            screen: Pygame surface to draw on
            hex_card: HexCard object containing card data and images
            flip_value_eased: Eased flip animation value (0.0 = back, 1.0 = front)
        
        Requirements:
        - 9.5: Render card with flip animation
        - 9.6: Switch between front/back based on flip_value
        - 17.1: Skip rendering if scaled width < 2 pixels (optimization)
        - 17.3: Skip rendering if card is off-screen (optimization)
        """
        # Get screen dimensions for off-screen culling
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # Determine which image to show based on flip_value
        # < 0.5: back, >= 0.5: front (Requirement 9.6)
        if flip_value_eased < 0.5:
            image = hex_card.back_image
        else:
            image = hex_card.front_image
        
        # Get original image dimensions
        original_width = image.get_width()
        original_height = image.get_height()
        
        # Calculate horizontal scale factor for flip effect
        # Scale goes from 1.0 -> 0.0 -> 1.0 as flip_value goes from 0.0 -> 0.5 -> 1.0
        if flip_value_eased < 0.5:
            scale_x = 1.0 - (flip_value_eased * 2.0)  # 1.0 -> 0.0
        else:
            scale_x = (flip_value_eased - 0.5) * 2.0  # 0.0 -> 1.0
        
        # Calculate scaled width
        scaled_width = int(original_width * scale_x)
        
        # Skip rendering if scaled width < 2 pixels (optimization, Requirement 17.1)
        if scaled_width < 2:
            return
        
        # Calculate position to center the scaled image at card position
        card_x, card_y = hex_card.position
        blit_x = card_x - scaled_width // 2
        blit_y = card_y - original_height // 2
        
        # Skip rendering if card is off-screen (optimization, Requirement 17.3)
        # Check if card bounding box is completely outside screen bounds
        if (blit_x + scaled_width < 0 or blit_x > screen_width or
            blit_y + original_height < 0 or blit_y > screen_height):
            return
        
        # Scale image width (horizontal flip)
        scaled_image = pygame.transform.scale(image, (scaled_width, original_height))
        
        # Blit scaled image centered at card position
        screen.blit(scaled_image, (blit_x, blit_y))
    
    def render_hex_border(self, screen: pygame.Surface, center: Tuple[float, float], 
                         hex_size: float, color: Tuple[int, int, int], width: int = 2) -> None:
        """Draw hex outline using polygon.
        
        Gets hex corners and draws a polygon outline with specified color and width.
        
        Args:
            screen: Pygame surface to draw on
            center: (x, y) center position of hex
            hex_size: Size of hex (radius from center to corner)
            color: RGB color tuple
            width: Line width in pixels (default: 2)
        
        Requirement 1.5: Draw hex border using polygon with flat-top orientation
        """
        # Get hex corners using flat-top orientation
        center_x, center_y = center
        corners = self._get_hex_corners(center_x, center_y, hex_size)
        
        # Draw polygon outline with specified color and width
        pygame.draw.polygon(screen, color, corners, width)
    
    def _get_hex_corners(self, center_x: float, center_y: float, size: float) -> list[Tuple[float, float]]:
        """Calculate 6 corner positions for a flat-top hex.
        
        Calculates corner positions at angles: 0°, 60°, 120°, 180°, 240°, 300°
        for flat-top orientation hexagons.
        
        Args:
            center_x: X coordinate of hex center
            center_y: Y coordinate of hex center
            size: Hex size (radius from center to corner)
        
        Returns:
            List of 6 (x, y) tuples representing hex corners in clockwise order
        
        Requirement 1.5: Support flat-top orientation with correct corner angles
        """
        angles = [0, 60, 120, 180, 240, 300]  # degrees
        corners = []
        for angle in angles:
            rad = math.radians(angle)
            x = center_x + size * math.cos(rad)
            y = center_y + size * math.sin(rad)
            corners.append((x, y))
        return corners


class CombatScene(Scene):
    """Combat scene with 37-hex radial grid.
    
    Lifecycle:
    - on_enter(): Initialize layout, create HexSystem, build hex cards
    - handle_input(): Process mouse/keyboard input
    - update(): Update animations and timers
    - draw(): Render grid, cards, and UI
    - on_exit(): Clean up resources
    
    Requirements:
    - 1.1: Render exactly 37 hexes in radial pattern with radius 3
    - 16.1: CoreGameState passed by reference (same instance across scenes)
    - 16.2: Validate CoreGameState is not None in on_enter()
    """
    
    # Fixed layout constants (immutable)
    SCREEN_WIDTH = 1920
    SCREEN_HEIGHT = 1080
    LEFT_PANEL_WIDTH = 300
    RIGHT_PANEL_WIDTH = 300
    BOTTOM_HUB_HEIGHT = 175
    TOP_MARGIN = 50
    
    def __init__(self, core_game_state: CoreGameState, action_system=None, animation_system=None, asset_loader=None):
        """Initialize combat scene with shared core game state.
        
        Args:
            core_game_state: SAVEABLE state that persists across scenes
            action_system: Optional action system for game actions
            animation_system: Optional animation system for visual effects
            asset_loader: REQUIRED AssetLoader for card asset management
        """
        super().__init__(core_game_state)
        
        # Validate required asset_loader parameter
        if asset_loader is None:
            raise ValueError("asset_loader is required for CombatScene")
        
        self.action_system = action_system
        self.animation_system = animation_system
        self.asset_loader = asset_loader
        
        # Layout state (calculated once in on_enter)
        self.hex_size: float = 0.0
        self.origin_x: float = 0.0
        self.origin_y: float = 0.0
        self.grid_area: Dict[str, float] = {}
        
        # Rendering components
        self.hex_system: Optional[HexSystem] = None
        self.hex_grid: list[Tuple[int, int]] = []  # 37 hex coordinates
        
        # Player strategies (loaded in on_enter)
        self.player_strategies: Dict[int, str] = {}
        
        # Animation controller (initialized in on_enter)
        self.animation_controller: Optional[AnimationController] = None
        
        # Input state machine (Requirement 15.1, 15.5)
        self.input_mode: InputMode = InputMode.NORMAL
        self.input_stack: list[InputMode] = []
        
        # Debug mode state (Requirement 10.1)
        self.debug_mode: bool = False
        
        # Store last input state for debug overlay
        self.last_input_state: Optional[InputState] = None
        
        # Frame counter for layout validation throttling (Requirement 14.1)
        self.frame_counter: int = 0
    
    def on_enter(self) -> None:
        """Called when scene becomes active.
        
        Validates CoreGameState integrity and initializes scene resources.
        
        Requirements:
        - 16.2: Validate CoreGameState is not None
        - 16.3: Validate game has at least one player
        - 1.2: Calculate layout with fixed constants
        - 11.1: Pre-load all card assets before building hex cards
        """
        # Requirement 16.2, 16.3: Validate CoreGameState integrity
        assert self.core_game_state is not None, "CoreGameState is None"
        assert self.core_game_state.game is not None, "Game is None"
        assert len(self.core_game_state.game.players) > 0, "No players in game"
        
        print("✓ CoreGameState validation passed")
        print(f"  - Game instance: {type(self.core_game_state.game).__name__}")
        print(f"  - Player count: {len(self.core_game_state.game.players)}")
        
        # Create fresh UIState (THROWAWAY)
        self.ui_state = UIState()
        
        # Calculate board layout (deterministic)
        self._calculate_board_layout()
        
        # Initialize HexSystem with calculated parameters (Requirement 3.5)
        self.hex_system = HexSystem(
            hex_size=self.hex_size,
            origin=(int(self.origin_x), int(self.origin_y))
        )
        
        # Generate 37-hex radial grid (Requirement 1.1)
        self.hex_grid = self.hex_system.radial_grid(radius=3)
        
        # Verify exactly 37 hexes were generated
        assert len(self.hex_grid) == 37, f"Expected 37 hexes, got {len(self.hex_grid)}"
        
        # Validate coordinate consistency (Requirement 18.1)
        self._validate_coordinate_consistency()
        
        # Pre-load all card assets (Requirement 11.1)
        self._preload_all_assets()
        
        # Load player strategies from lobby data (Requirement 20.1)
        self._load_player_strategies()
        
        # Build hex cards from CoreGameState (Requirement 16.3)
        self._build_hex_cards()
        
        # Initialize AnimationController (Requirement 9.2, 9.3)
        self.animation_controller = AnimationController(self.ui_state)
        
        # Initialize HexCardRenderer (Requirement 9.5, 9.6)
        self.hex_card_renderer = HexCardRenderer(self.hex_system)
        
        # Initialize PlacementController (Requirement 5.1, 5.2)
        self.placement_controller = PlacementController(
            self.core_game_state, 
            self.ui_state, 
            self.hex_system
        )
        
        print("✓ CombatScene.on_enter() - CoreGameState validated")
        print(f"✓ Layout calculated: hex_size={self.hex_size:.2f}, origin=({self.origin_x:.1f}, {self.origin_y:.1f})")
        print(f"✓ HexSystem initialized with {len(self.hex_grid)} hexes")
        print(f"✓ Loaded {len(self.player_strategies)} player strategies")
    
    def _calculate_board_layout(self) -> None:
        """Calculate hex grid layout with fixed UI boundaries.
        
        Computes the available grid area between UI panels, calculates
        optimal hex_size with safety margin, and determines grid origin
        for exact centering. Validates no overlap with UI panels.
        
        Requirements:
        - 1.2: Use fixed constants for screen dimensions and panel sizes
        - 2.1: Calculate available grid area between UI panels
        - 2.2: Left panel width = 300px
        - 2.3: Right panel width = 300px
        - 2.4: Bottom hub height = 150px
        - 2.5: Top margin = 50px
        """
        # Define grid area boundaries
        self.grid_area = {
            'left': self.LEFT_PANEL_WIDTH,
            'right': self.SCREEN_WIDTH - self.RIGHT_PANEL_WIDTH,
            'top': self.TOP_MARGIN,
            'bottom': self.SCREEN_HEIGHT - self.BOTTOM_HUB_HEIGHT,
            'width': self.SCREEN_WIDTH - self.LEFT_PANEL_WIDTH - self.RIGHT_PANEL_WIDTH,
            'height': self.SCREEN_HEIGHT - self.TOP_MARGIN - self.BOTTOM_HUB_HEIGHT,
        }
        
        # Calculate hex_size using LayoutCalculator
        available_width = self.grid_area['width']
        available_height = self.grid_area['height']
        grid_radius = 3  # 37 hexes = radius 3
        
        self.hex_size = LayoutCalculator.calculate_hex_size(
            available_width, available_height, grid_radius
        )
        
        # Calculate grid origin (exact center)
        self.origin_x, self.origin_y = LayoutCalculator.calculate_grid_origin(
            self.grid_area
        )
        
        # Verify no overlap with UI panels
        LayoutCalculator.verify_no_overlap(
            hex_size=self.hex_size,
            origin=(self.origin_x, self.origin_y),
            grid_area=self.grid_area,
            radius=grid_radius,
            left_panel_width=self.LEFT_PANEL_WIDTH,
            right_panel_width=self.RIGHT_PANEL_WIDTH,
            top_margin=self.TOP_MARGIN,
            bottom_hub_height=self.BOTTOM_HUB_HEIGHT,
            screen_width=self.SCREEN_WIDTH,
            screen_height=self.SCREEN_HEIGHT
        )
    
    def _validate_coordinate_consistency(self) -> None:
        """Validate coordinate conversion consistency for all hexes.
        
        For each hex in the grid, converts to pixel coordinates and back
        to hex coordinates, verifying that the result matches the original.
        This detects any coordinate drift or rounding errors.
        
        Raises:
            AssertionError: If any coordinate drift is detected
        
        Requirements:
        - 18.1: Run coordinate consistency check in on_enter()
        - 18.2: Verify hex_to_pixel followed by pixel_to_hex returns original
        - 18.3: Raise AssertionError if drift detected
        """
        drift_detected = False
        drift_details = []
        
        for q, r in self.hex_grid:
            # Convert hex to pixel
            pixel_x, pixel_y = self.hex_system.hex_to_pixel(q, r)
            
            # Convert pixel back to hex
            recovered_q, recovered_r = self.hex_system.pixel_to_hex(pixel_x, pixel_y)
            
            # Check if we got the same coordinate back
            if (recovered_q, recovered_r) != (q, r):
                drift_detected = True
                drift_details.append(
                    f"  Hex ({q}, {r}) -> Pixel ({pixel_x:.2f}, {pixel_y:.2f}) -> "
                    f"Hex ({recovered_q}, {recovered_r})"
                )
        
        if drift_detected:
            error_msg = "Coordinate drift detected:\n" + "\n".join(drift_details)
            raise AssertionError(error_msg)
        
        print("✓ Coordinate consistency validation passed - no drift detected")
    
    def _load_player_strategies(self) -> None:
        """Load player strategy names from CoreGameState.
        
        Reads strategy names from each player and stores them for display
        in the right panel. Uses fallback "Player {id}" if strategy not set.
        
        Requirements:
        - 20.1: Load player strategy names from CoreGameState
        - 20.2: Display strategy names in right panel
        - 20.5: Use fallback if strategy_name not set
        """
        self.player_strategies = {}
        
        for player in self.core_game_state.game.players:
            # Get player ID (try both pid and player_id for compatibility)
            player_id = getattr(player, 'player_id', getattr(player, 'pid', 0))
            
            # Get strategy name from player
            strategy_name = getattr(player, 'strategy', None)
            if strategy_name is None or strategy_name == "":
                strategy_name = f"Player {player_id}"
            else:
                # Capitalize first letter for display
                strategy_name = strategy_name.capitalize()
            
            self.player_strategies[player_id] = strategy_name
    
    def _preload_all_assets(self) -> None:
        """Pre-load all card assets before building hex cards.
        
        Collects all unique card names from all players' boards and hands,
        then preloads them using AssetLoader. Deduplicates card names before
        preloading for efficiency.
        
        Requirements:
        - 11.1: Pre-load all card assets during scene entry
        - 11.2: Load both front and back images for each unique card
        - 11.3: Validate assets are not None
        - 11.4: Log progress for each loaded card
        """
        # Collect all unique card names from all players
        visible_cards = []
        
        for player in self.core_game_state.game.players:
            # Collect from board (defensive check for mock objects)
            if hasattr(player, 'board') and hasattr(player.board, 'grid'):
                try:
                    for card in player.board.grid.values():
                        if card is not None and hasattr(card, 'name'):
                            visible_cards.append(card.name)
                except (TypeError, AttributeError):
                    # Handle mock objects or invalid board structures
                    pass
            
            # Collect from hand (defensive check for mock objects)
            if hasattr(player, 'hand'):
                try:
                    for card in player.hand:
                        if card is not None and hasattr(card, 'name'):
                            visible_cards.append(card.name)
                except (TypeError, AttributeError):
                    # Handle mock objects or invalid hand structures
                    pass
        
        # Skip if no cards to load (e.g., in tests with mock objects)
        if len(visible_cards) == 0:
            print("✓ No cards to pre-load (empty game state)")
            return
        
        # Deduplicate and preload using AssetLoader
        unique_cards = list(set(visible_cards))
        print(f"✓ Pre-loading assets for {len(unique_cards)} unique cards...")
        self.asset_loader.preload(unique_cards)
        print(f"✓ Asset pre-loading complete")
    
    def _validate_card_data(self, card) -> bool:
        """Validate card data integrity.
        
        Checks that required attributes exist (name, stats) and that stat
        values are integers in the valid range (0-99). Returns False if
        validation fails.
        
        Args:
            card: Card object to validate
        
        Returns:
            True if card data is valid, False otherwise
        
        Requirements:
        - 13.1: Check required attributes exist and validate stat values
        """
        # Check required attributes exist
        if not hasattr(card, 'name'):
            print(f"Warning: Card missing 'name' attribute")
            return False
        
        if not hasattr(card, 'stats'):
            print(f"Warning: Card '{card.name}' missing 'stats' attribute")
            return False
        
        # Validate stats is a dictionary
        if not isinstance(card.stats, dict):
            print(f"Warning: Card '{card.name}' stats is not a dictionary")
            return False
        
        # Validate stat values are integers in range 0-99
        for stat_name, stat_value in card.stats.items():
            if not isinstance(stat_value, int):
                print(f"Warning: Card '{card.name}' stat '{stat_name}' is not an integer: {stat_value}")
                return False
            
            if stat_value < 0 or stat_value > 99:
                print(f"Warning: Card '{card.name}' stat '{stat_name}' out of range (0-99): {stat_value}")
                return False
        
        # All checks passed
        return True
    
    def _create_fallback_card(self, hex_coord: Tuple[int, int]):
        """Create fallback card with safe default values.
        
        Creates a Card object with safe default values when card data is
        corrupted or invalid. Uses hex coordinate in name for uniqueness.
        Sets all stats to 1, cost to 0.
        
        Args:
            hex_coord: Hex coordinate (q, r) for unique naming
        
        Returns:
            Card object with safe default values
        
        Requirements:
        - 13.3: Create Card object with safe default values
        """
        from engine_core.card import Card
        
        # Create unique name using hex coordinate
        fallback_name = f"Fallback_{hex_coord[0]}_{hex_coord[1]}"
        
        # Create safe default stats (all stats set to 1)
        default_stats = {
            "strength": 1,
            "agility": 1,
            "intelligence": 1,
            "vitality": 1,
            "luck": 1,
            "charisma": 1
        }
        
        # Create fallback card
        fallback_card = Card(
            name=fallback_name,
            category="fallback",
            rarity="1",
            stats=default_stats,
            passive_type="none"
        )
        
        print(f"✓ Created fallback card for hex {hex_coord}: {fallback_name}")
        
        return fallback_card
    
    def _build_hex_cards(self) -> None:
        """Build HexCard objects from CoreGameState board data.
        
        Reads the current player's board from CoreGameState and creates
        HexCard objects for each non-None card in the grid. Stores the
        resulting HexCard objects in self.hex_cards list.
        
        Requirements:
        - 16.3: Get current player's board and create HexCard objects
        """
        self.hex_cards = []
        
        # Get current player's board from CoreGameState
        if not hasattr(self.core_game_state, 'game') or self.core_game_state.game is None:
            print("Warning: CoreGameState.game is None, cannot build hex cards")
            return
        
        if not hasattr(self.core_game_state.game, 'players') or len(self.core_game_state.game.players) == 0:
            print("Warning: No players in game, cannot build hex cards")
            return
        
        # Get current player (default to first player if current_player_id not set)
        current_player_id = getattr(self, 'current_player_id', 0)
        if current_player_id >= len(self.core_game_state.game.players):
            current_player_id = 0
        
        current_player = self.core_game_state.game.players[current_player_id]
        
        # Check if player has a board
        if not hasattr(current_player, 'board') or current_player.board is None:
            print(f"Warning: Player {current_player_id} has no board")
            return
        
        board = current_player.board
        
        # Check if board has a grid
        if not hasattr(board, 'grid') or board.grid is None:
            print(f"Warning: Player {current_player_id} board has no grid")
            return
        
        # Check if grid is iterable (defensive check for mock objects)
        try:
            grid_items = board.grid.items()
        except (TypeError, AttributeError):
            print(f"Warning: Player {current_player_id} board.grid is not iterable")
            return
        
        # Iterate over board.grid dictionary
        for hex_coord, card in grid_items:
            if card is None:
                continue  # Empty hex, skip
            
            # Create HexCard object
            hex_card = self._create_hex_card(hex_coord, card)
            if hex_card is not None:
                self.hex_cards.append(hex_card)
        
        # Sync hex_cards to UIState for animation and rendering
        self.ui_state.hex_cards = self.hex_cards
        
        print(f"✓ Built {len(self.hex_cards)} hex cards from board")
    
    def _create_hex_card(self, hex_coord: Tuple[int, int], card) -> Optional[HexCard]:
        """Create a HexCard object with loaded assets.
        
        Validates card data, loads front and back images via AssetManager,
        and creates a HexCard object with all required fields. On data
        corruption, uses corrupted visual and fallback card.
        
        Args:
            hex_coord: Axial (q, r) coordinate of the hex
            card: Card object from CoreGameState
        
        Returns:
            HexCard object (never None)
        
        Requirements:
        - 4.1, 4.2, 4.3: Load front and back images via AssetManager
        - 13.2, 13.3: Handle corrupted data with fallback
        """
        # Validate card data
        is_valid = self._validate_card_data(card)
        
        if not is_valid:
            print(f"Warning: Card data invalid at {hex_coord}, using fallback")
            # Create fallback card
            card = self._create_fallback_card(hex_coord)
            # Use AssetLoader to get placeholder for corrupted card
            faces = self.asset_loader.get(f"CORRUPTED_{hex_coord[0]}_{hex_coord[1]}")
            front_image = faces.front
            back_image = faces.back
        else:
            # Load front and back images via AssetLoader
            card_name = card.name
            faces = self.asset_loader.get(card_name)
            front_image = faces.front
            back_image = faces.back
        
        # Convert hex coordinate to pixel position
        pixel_x, pixel_y = self.hex_system.hex_to_pixel(hex_coord[0], hex_coord[1])
        
        # Create HexCard object with all required fields
        hex_card = HexCard(
            hex_coord=hex_coord,
            card_data=card,
            front_image=front_image,
            back_image=back_image,
            position=(pixel_x, pixel_y),
            hex_size=self.hex_size,
            rotation=0,
            placement_state="placed",
            is_rotation_locked=True,  # Cards on board are locked
            flip_value=0.0,
            flip_value_eased=0.0
        )
        
        return hex_card
    
    def on_exit(self) -> None:
        """Called when scene is deactivated.
        
        Cleans up scene-specific resources and discards UIState.
        
        Requirements:
        - 16.4: Clean up resources on scene exit
        - T1.12: Apply post-placement updates (evolution, copy strengthening)
        """
        # Apply post-placement updates to current player (T1.12)
        player = self.core_game_state.current_player
        player.check_evolution()
        player.check_copy_strengthening(self.core_game_state.turn)
        
        # Clear hex_cards list
        self.hex_cards.clear()
        
        # Clear UIState references
        if self.ui_state is not None:
            self.ui_state.hovered_hex = None
            self.ui_state.selected_hex = None
        
        # Discard THROWAWAY state
        self.ui_state = None
        
        # Log scene exit
        print("✓ CombatScene.on_exit() - Resources cleaned up")
        print(f"  - Cleared {len(self.hex_cards)} hex cards")
        print("  - Cleared UIState references")
        print("  - Scene exit complete")
    
    def push_input_mode(self, mode: InputMode) -> None:
        """Push a new input mode onto the stack.
        
        Saves the current mode and switches to the new mode. This allows
        nested input modes (e.g., PAUSED while in PLACING mode).
        
        Args:
            mode: The new input mode to activate
        
        Requirements:
        - 15.5: Implement input mode stack for nested modes
        """
        # Save current mode to stack
        self.input_stack.append(self.input_mode)
        
        # Switch to new mode
        self.input_mode = mode
        
        print(f"✓ Input mode pushed: {self.input_mode.value} (stack depth: {len(self.input_stack)})")
    
    def pop_input_mode(self) -> None:
        """Pop the current input mode and return to the previous mode.
        
        Restores the previous input mode from the stack. If the stack is empty,
        defaults to NORMAL mode.
        
        Requirements:
        - 15.5: Implement input mode stack for nested modes
        """
        if self.input_stack:
            # Restore previous mode from stack
            self.input_mode = self.input_stack.pop()
            print(f"✓ Input mode popped: {self.input_mode.value} (stack depth: {len(self.input_stack)})")
        else:
            # Stack is empty, default to NORMAL
            self.input_mode = InputMode.NORMAL
            print(f"✓ Input mode reset to NORMAL (stack was empty)")
    
    def handle_input(self, input_state: InputState) -> None:
        """Process input intents for this scene.
        
        Routes input to appropriate handler based on current input mode.
        
        Args:
            input_state: Intent-based input abstraction (not raw events)
        
        Requirements:
        - 10.1: Toggle debug mode on F3 key press
        - 9.1: Update hovered_hex in UIState based on mouse position
        - 15.6: Route input handling based on current input mode
        - T2.2: Fast mode toggle (F key) - global across all scenes
        - T2.3a: Player switching (1-8 keys) - global across all scenes
        """
        # Store input state for debug overlay
        self.last_input_state = input_state
        
        # ============================================================================
        # GLOBAL INPUT HANDLING (works in all scenes and modes)
        # ============================================================================
        
        # Toggle debug mode on F3 (Requirement 10.1)
        if input_state.was_key_pressed_this_frame(pygame.K_F3):
            self.debug_mode = not self.debug_mode
            print(f"✓ Debug mode {'enabled' if self.debug_mode else 'disabled'}")
        
        # Toggle fast mode on F key (T2.2) - global across all scenes
        if input_state.is_fast_mode_toggled():
            self.core_game_state.fast_mode = not self.core_game_state.fast_mode
            print(f"✓ Fast mode {'enabled' if self.core_game_state.fast_mode else 'disabled'}")
        
        # Player switching via 1-8 keys (T2.3a) - global across all scenes
        player_switch_request = input_state.get_player_switch_request()
        if player_switch_request != -1:
            # Validate that target player exists
            num_players = len(self.core_game_state.game.players)
            if 0 <= player_switch_request < num_players:
                # Set view_player_index directly
                old_index = self.core_game_state.view_player_index
                self.core_game_state.view_player_index = player_switch_request
                
                # Print debug message showing switch
                old_player = self.core_game_state.game.players[old_index]
                new_player = self.core_game_state.game.players[player_switch_request]
                print(f"✓ Player switch: Player {old_index + 1} → Player {player_switch_request + 1} "
                      f"(PID {old_player.pid} → PID {new_player.pid})")
                
                # Update current_player_id to match new view
                self.current_player_id = player_switch_request
            else:
                print(f"✗ Invalid player switch request: index {player_switch_request} "
                      f"(only {num_players} players exist)")
        
        # ============================================================================
        # MODE-SPECIFIC INPUT HANDLING
        # ============================================================================
        
        # Route input based on current mode (Requirement 15.6)
        if self.input_mode == InputMode.NORMAL:
            self._handle_input_normal(input_state)
        elif self.input_mode == InputMode.PLACING:
            self._handle_input_placing(input_state)
        elif self.input_mode == InputMode.CARD_DETAIL:
            self._handle_input_card_detail(input_state)
        elif self.input_mode == InputMode.PAUSED:
            self._handle_input_paused(input_state)
    
    def _handle_input_normal(self, input_state: InputState) -> None:
        """Handle input in NORMAL mode.
        
        NORMAL mode allows:
        - Hovering over hexes to flip cards
        - Left-click on hand area to select card and enter placement mode
        - Left-click on player panel to switch players (T2.3b)
        - ENTER to complete placement and return to game_loop
        - ESC to enter PAUSED mode
        - Scene navigation
        
        Args:
            input_state: Intent-based input abstraction
        
        Requirements:
        - 9.1: Update hovered_hex in UIState based on mouse position
        - 15.2: ESC in NORMAL mode enters PAUSED mode
        - 5.1: Left-click on hand area to select card and enter placement mode
        - T1.10: ENTER to complete placement and transition to game_loop
        - T2.3b: Left-click on player panel to switch players
        """
        # Handle mouse click on player panel (T2.3b) - BEFORE other click handling
        if input_state.mouse_clicked:
            mouse_pos = input_state.mouse_pos
            
            # Check if click is within any player rectangle
            if self.ui_state and self.ui_state.player_panel_rects:
                for player_index, rect in enumerate(self.ui_state.player_panel_rects):
                    if rect.collidepoint(mouse_pos):
                        # Validate that target player exists
                        num_players = len(self.core_game_state.game.players)
                        if 0 <= player_index < num_players:
                            # Set view_player_index directly
                            old_index = self.core_game_state.view_player_index
                            self.core_game_state.view_player_index = player_index
                            
                            # Update current_player_id to match new view
                            self.current_player_id = player_index
                            
                            # Print debug message showing switch
                            old_player = self.core_game_state.game.players[old_index]
                            new_player = self.core_game_state.game.players[player_index]
                            print(f"✓ Player switch (click): Player {old_index + 1} → Player {player_index + 1} "
                                  f"(PID {old_player.pid} → PID {new_player.pid})")
                        return  # Don't process other click handling
        
        # Update hovered hex based on mouse position (Requirement 9.1)
        if self.hex_system and self.ui_state:
            mouse_x, mouse_y = input_state.mouse_pos
            hex_coord = self.hex_system.pixel_to_hex(mouse_x, mouse_y)
            
            # Only set hovered_hex if the hex is in the grid
            if hex_coord in self.hex_grid:
                self.ui_state.hovered_hex = hex_coord
            else:
                self.ui_state.hovered_hex = None
        
        # ENTER to complete placement and transition to game_loop (T1.10, T1.13)
        if input_state.was_key_pressed_this_frame(pygame.K_RETURN):
            print("✓ Placement complete - transitioning to game_loop")
            # ========================================================================
            # TEMPORARY: Cross-scene signaling via trigger_combat flag (T1.13)
            # ========================================================================
            # This passes a flag to GameLoopScene to trigger combat phase.
            # FUTURE REFACTOR: Remove this flag - GameLoopScene should own combat
            # triggering logic without needing signals from CombatScene.
            # ========================================================================
            self.scene_manager.request_transition("game_loop", trigger_combat=True)
            return
        
        # Left-click on hand area to select card (Requirement 5.1, Task 27.3)
        if input_state.mouse_clicked:
            mouse_x, mouse_y = input_state.mouse_pos
            card = self._get_card_at_hand_position(mouse_x, mouse_y)
            if card is not None:
                self._start_placement(card)
        
        # ESC to enter PAUSED mode (Requirement 15.2)
        if input_state.was_key_pressed_this_frame(pygame.K_ESCAPE):
            self.push_input_mode(InputMode.PAUSED)
            print("✓ Entered PAUSED mode (pause menu placeholder)")
    
    def _handle_input_placing(self, input_state: InputState) -> None:
        """Handle input in PLACING mode.
        
        PLACING mode allows:
        - Right-click to rotate preview card
        - Left-click to place card
        - ESC to cancel placement and return to NORMAL mode
        
        Args:
            input_state: Intent-based input abstraction
        
        Requirements:
        - 15.3: ESC in PLACING mode cancels placement and returns to NORMAL
        - 5.3: Right-click rotates preview card by 60 degrees
        - 7.3: Place card at hex center position (snap-to-grid)
        - 7.4: Validate hex is in grid and valid for placement
        """
        # ESC to cancel placement (Requirement 15.3)
        if input_state.was_key_pressed_this_frame(pygame.K_ESCAPE):
            self._cancel_placement()
            self.pop_input_mode()
            print("✓ Placement cancelled, returned to NORMAL mode")
        
        # Right-click to rotate preview card (Requirement 5.3, Task 25.1)
        if input_state.right_clicked:
            self.placement_controller.handle_right_click()
            print(f"✓ Rotated preview card to {self.placement_controller.preview_rotation}°")
        
        # Left-click to place card (Task 28.2)
        if input_state.mouse_clicked:
            # Convert mouse position to hex coordinate (Requirement 7.3)
            mouse_x, mouse_y = input_state.mouse_pos
            hex_coord = self.hex_system.pixel_to_hex(mouse_x, mouse_y)
            
            # Validate hex is in grid and valid for placement (Requirement 7.4)
            if hex_coord in self.hex_grid:
                current_player_id = getattr(self, 'current_player_id', 0)
                
                # Attempt to place card at hex center position
                success = self.placement_controller.handle_left_click(
                    hex_coord, 
                    current_player_id, 
                    self.asset_loader, 
                    self.hex_size
                )
                
                if success:
                    # Add the newly placed card to hex_cards list for rendering
                    # Get the HexCard that was just created
                    current_player = self.core_game_state.game.players[current_player_id]
                    board = current_player.board
                    placed_card = board.grid.get(hex_coord)
                    
                    if placed_card:
                        # Create HexCard for rendering
                        hex_card = self._create_hex_card(hex_coord, placed_card)
                        if hex_card:
                            self.hex_cards.append(hex_card)
                    
                    # Exit placement mode
                    self.ui_state.is_placing = False
                    self.pop_input_mode()
                    print(f"✓ Card placed at hex {hex_coord}, rotation locked at {self.placement_controller.preview_rotation}°")
                else:
                    print(f"✗ Cannot place card at hex {hex_coord} (invalid placement)")
            else:
                print(f"✗ Hex {hex_coord} is not in grid")
    
    def _handle_input_card_detail(self, input_state: InputState) -> None:
        """Handle input in CARD_DETAIL mode.
        
        CARD_DETAIL mode allows:
        - ESC to close card detail view and return to previous mode
        - Click outside card to close detail view
        
        Args:
            input_state: Intent-based input abstraction
        
        Requirements:
        - 15.4: ESC in CARD_DETAIL mode closes detail view and returns to previous mode
        """
        # ESC to close card detail view (Requirement 15.4)
        if input_state.was_key_pressed_this_frame(pygame.K_ESCAPE):
            self.pop_input_mode()
            print("✓ Card detail view closed, returned to previous mode")
        
        # TODO: Implement card detail view rendering and interaction
        # - Display card stats, synergies, abilities
        # - Click outside to close
    
    def _handle_input_paused(self, input_state: InputState) -> None:
        """Handle input in PAUSED mode.
        
        PAUSED mode allows:
        - ESC to close pause menu and return to previous mode
        - Pause menu interactions (resume, settings, quit)
        
        Args:
            input_state: Intent-based input abstraction
        
        Requirements:
        - 15.2: ESC in PAUSED mode closes pause menu and returns to previous mode
        """
        # ESC to close pause menu (Requirement 15.2)
        if input_state.was_key_pressed_this_frame(pygame.K_ESCAPE):
            self.pop_input_mode()
            print("✓ Pause menu closed, returned to previous mode")
        
        # TODO: Implement pause menu rendering and interaction
        # - Resume button: pop_input_mode()
        # - Settings button: open settings menu
        # - Quit button: return to main menu
    
    def _start_placement(self, card) -> None:
        """Start card placement mode.
        
        Sets up placement controller with selected card, resets preview rotation,
        updates UI state, and pushes PLACING input mode.
        
        Args:
            card: Card object to be placed
        
        Requirements:
        - 5.1: Handle card selection and enter placement mode
        """
        # Set placement controller state
        self.placement_controller.selected_card = card
        self.placement_controller.preview_rotation = 0
        
        # Update UI state
        self.ui_state.is_placing = True
        
        # Push PLACING input mode
        self.push_input_mode(InputMode.PLACING)
        
        print(f"✓ Started placement mode for card: {card.name if hasattr(card, 'name') else 'Unknown'}")
    
    def _get_card_at_hand_position(self, mouse_x: int, mouse_y: int):
        """Get card from hand at mouse position using rendered slot rects.

        Checks if (mouse_x, mouse_y) falls inside any of the hex card slots
        rendered by _draw_hand_panel.  When a slot with a card is clicked:
        - Updates ui_state.selected_hand_idx
        - Returns the Card object so the caller can start placement

        Args:
            mouse_x: Mouse X coordinate
            mouse_y: Mouse Y coordinate

        Returns:
            Card object if a valid hand slot was clicked, None otherwise
        """
        hand: list = []
        try:
            cp = self.core_game_state.current_player
            if hasattr(cp, 'hand') and cp.hand:
                hand = list(cp.hand)
        except (TypeError, AttributeError):
            pass

        slot_rects = getattr(self, '_hand_slot_rects', [])
        for i, rect in enumerate(slot_rects):
            if i >= len(hand):
                break                     # empty ghost slot – no card
            if rect.collidepoint(mouse_x, mouse_y):
                # Update selection highlight
                if self.ui_state:
                    self.ui_state.selected_hand_idx = i
                return hand[i]

        return None
    
    def _cancel_placement(self) -> None:
        """Cancel card placement and clean up placement state.
        
        Clears placement controller state and resets UI state.
        
        Requirements:
        - 15.3: Clean up placement state when cancelling
        """
        # Clear placement controller state
        self.placement_controller.selected_card = None
        self.placement_controller.preview_hex = None
        self.placement_controller.preview_rotation = 0
        
        # Update UI state
        self.ui_state.is_placing = False
        
        print("✓ Placement cancelled, state cleared")
    
    def update(self, dt: float) -> None:
        """Update scene logic with delta time.
        
        All time-based animations and movement must use dt for
        frame-independent behavior.
        
        Args:
            dt: Delta time in milliseconds since last frame
        
        Requirements:
        - 9.2: Update flip animations based on hover state
        - 9.3: Apply cosine easing for smooth animation
        - 14.1: Run layout safety check once per second (every 60 frames)
        """
        # Update flip animations for all hex cards (Requirement 9.2, 9.3)
        if self.animation_controller and hasattr(self, 'hex_cards'):
            self.animation_controller.update_flip_animations(self.hex_cards, dt)
        
        # Layout safety check throttling (Requirement 14.1)
        # Run once per second (every 60 frames at 60 FPS)
        self.frame_counter += 1
        if self.frame_counter % 60 == 0:
            self._validate_layout_safety()
    
    def _validate_layout_safety(self) -> None:
        """Validate layout safety by checking screen resolution and grid bounds.
        
        Checks if screen resolution has changed from 1920x1080 and if grid bounds
        overlap with UI panels. Logs warnings if issues detected but does NOT
        recalculate layout (fixed resolution only).
        
        Requirements:
        - 14.1: Run layout safety check once per second (every 60 frames)
        - 14.2: Log warning if screen resolution changed from 1920x1080
        - 14.3: Log warning if grid bounds overlap with UI panels
        - 14.4: Do NOT recalculate layout dynamically
        """
        # Get current screen dimensions
        screen = pygame.display.get_surface()
        if screen is None:
            return  # No display surface available
        
        screen_width, screen_height = screen.get_size()
        
        # Check if resolution changed (Requirement 14.2)
        if screen_width != self.SCREEN_WIDTH or screen_height != self.SCREEN_HEIGHT:
            print(f"⚠ WARNING: Screen size changed to {screen_width}x{screen_height}")
            print(f"  Expected: {self.SCREEN_WIDTH}x{self.SCREEN_HEIGHT}")
            print(f"  Layout may be compromised. Recommend restarting with correct resolution.")
        
        # Verify grid bounds (Requirement 14.3)
        grid_bounds = self._calculate_grid_bounds()
        
        if grid_bounds['left'] < self.LEFT_PANEL_WIDTH:
            print(f"⚠ WARNING: Grid overlaps left panel")
            print(f"  Grid left: {grid_bounds['left']:.1f}, Panel width: {self.LEFT_PANEL_WIDTH}")
        
        if grid_bounds['right'] > screen_width - self.RIGHT_PANEL_WIDTH:
            print(f"⚠ WARNING: Grid overlaps right panel")
            print(f"  Grid right: {grid_bounds['right']:.1f}, Panel edge: {screen_width - self.RIGHT_PANEL_WIDTH}")
        
        if grid_bounds['top'] < self.TOP_MARGIN:
            print(f"⚠ WARNING: Grid overlaps top margin")
            print(f"  Grid top: {grid_bounds['top']:.1f}, Margin: {self.TOP_MARGIN}")
        
        if grid_bounds['bottom'] > screen_height - self.BOTTOM_HUB_HEIGHT:
            print(f"⚠ WARNING: Grid overlaps bottom hub")
            print(f"  Grid bottom: {grid_bounds['bottom']:.1f}, Hub edge: {screen_height - self.BOTTOM_HUB_HEIGHT}")
    
    def _calculate_grid_bounds(self) -> Dict[str, float]:
        """Calculate current grid bounds in pixels.
        
        Calculates the bounding box of the hex grid based on current hex_size
        and origin. Used for layout validation.
        
        Returns:
            Dictionary with keys 'left', 'right', 'top', 'bottom' representing
            the pixel boundaries of the hex grid
        
        Requirements:
        - 14.3: Calculate grid bounds for overlap detection
        """
        # Grid extent for radius 3 (7 hexes wide, 7 hexes tall)
        grid_width_hexes = 7
        grid_height_hexes = 7
        
        # Calculate grid dimensions in pixels
        sqrt_3 = math.sqrt(3)
        grid_pixel_width = sqrt_3 * self.hex_size * grid_width_hexes
        grid_pixel_height = 1.5 * self.hex_size * grid_height_hexes
        
        return {
            'left': self.origin_x - grid_pixel_width / 2,
            'right': self.origin_x + grid_pixel_width / 2,
            'top': self.origin_y - grid_pixel_height / 2,
            'bottom': self.origin_y + grid_pixel_height / 2,
        }
    
    def _get_hex_corners(self, center_x: float, center_y: float, size: float) -> list[Tuple[float, float]]:
        """Calculate 6 corner positions for a flat-top hex.
        
        Calculates corner positions at angles: 0°, 60°, 120°, 180°, 240°, 300°
        for flat-top orientation hexagons.
        
        Args:
            center_x: X coordinate of hex center
            center_y: Y coordinate of hex center
            size: Hex size (radius from center to corner)
        
        Returns:
            List of 6 (x, y) tuples representing hex corners in clockwise order
        
        Requirements:
        - 1.5: Support flat-top orientation with correct corner angles
        """
        angles = [0, 60, 120, 180, 240, 300]  # degrees
        corners = []
        for angle in angles:
            rad = math.radians(angle)
            x = center_x + size * math.cos(rad)
            y = center_y + size * math.sin(rad)
            corners.append((x, y))
        return corners
    
    def _draw_hex_grid(self, screen: pygame.Surface) -> None:
        """Draw hex grid outlines for all 37 hexes.
        
        Iterates over all hex coordinates from self.hex_grid, converts each
        to pixel position, calculates hex corners, and draws outline using
        pygame.draw.polygon with 1px white lines at 50% alpha.
        
        Args:
            screen: Pygame surface to draw on
        
        Requirements:
        - 1.5: Render hex grid with flat-top orientation
        - 3.1: Use HexSystem for coordinate conversion
        """
        # Create a semi-transparent surface for alpha blending
        alpha_surface = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
        
        # White color with 50% alpha (127 out of 255)
        line_color = (255, 255, 255, 127)
        
        # Draw each hex outline
        for q, r in self.hex_grid:
            # Convert hex coordinate to pixel position
            center_x, center_y = self.hex_system.hex_to_pixel(q, r)
            
            # Calculate hex corners
            corners = self._get_hex_corners(center_x, center_y, self.hex_size)
            
            # Draw hex outline with 1px width
            pygame.draw.polygon(alpha_surface, line_color, corners, width=1)
        
        # Blit the alpha surface onto the main screen
        screen.blit(alpha_surface, (0, 0))
    
    def _draw_debug_overlay(self, screen: pygame.Surface) -> None:
        """Draw debug overlay with coordinate information.
        
        Renders crosshairs at each hex center, coordinate labels, mouse position,
        detected hex coordinate, grid parameters, and grid bounds rectangle.
        
        Args:
            screen: Pygame surface to draw on
        
        Requirements:
        - 10.2: Draw crosshairs at each hex center (yellow, 20px cross)
        - 10.3: Render coordinate labels (q, r) at each hex
        - 10.4: Display mouse position and detected hex coordinate
        - 10.5: Show grid origin, hex_size, and grid bounds rectangle
        """
        # Skip if no input state available
        if self.last_input_state is None:
            return
        
        # Font for rendering text
        font = pygame.font.Font(None, 20)
        large_font = pygame.font.Font(None, 24)
        
        # Colors
        yellow = (255, 255, 0)
        white = (255, 255, 255)
        red = (255, 0, 0)
        black = (0, 0, 0)
        
        # Draw crosshairs and coordinate labels at each hex center (Requirement 10.2, 10.3)
        for q, r in self.hex_grid:
            center_x, center_y = self.hex_system.hex_to_pixel(q, r)
            
            # Draw crosshair (20px cross)
            cross_size = 10  # 10px in each direction = 20px total
            pygame.draw.line(screen, yellow, 
                           (center_x - cross_size, center_y), 
                           (center_x + cross_size, center_y), 2)
            pygame.draw.line(screen, yellow, 
                           (center_x, center_y - cross_size), 
                           (center_x, center_y + cross_size), 2)
            
            # Render coordinate label with black background
            label_text = f"({q},{r})"
            text_surface = font.render(label_text, True, white)
            text_rect = text_surface.get_rect(center=(center_x, center_y + 25))
            
            # Draw black background rectangle
            bg_rect = text_rect.inflate(4, 2)
            pygame.draw.rect(screen, black, bg_rect)
            
            # Draw text
            screen.blit(text_surface, text_rect)
        
        # Draw grid bounds rectangle (Requirement 10.5)
        grid_radius = 3
        grid_width_in_hexes = 2 * grid_radius + 1
        grid_height_in_hexes = 2 * grid_radius + 1
        
        sqrt_3 = math.sqrt(3)
        grid_pixel_width = sqrt_3 * self.hex_size * grid_width_in_hexes
        grid_pixel_height = 1.5 * self.hex_size * grid_height_in_hexes
        
        grid_left = self.origin_x - grid_pixel_width / 2
        grid_top = self.origin_y - grid_pixel_height / 2
        
        grid_bounds_rect = pygame.Rect(grid_left, grid_top, grid_pixel_width, grid_pixel_height)
        pygame.draw.rect(screen, red, grid_bounds_rect, 2)
        
        # Display mouse position and detected hex coordinate (Requirement 10.4)
        mouse_x, mouse_y = self.last_input_state.mouse_pos
        detected_q, detected_r = self.hex_system.pixel_to_hex(mouse_x, mouse_y)
        
        # Check if detected hex is in grid
        in_grid = (detected_q, detected_r) in self.hex_grid
        grid_status = "IN GRID" if in_grid else "OUT OF GRID"
        
        # Create info panel in top-left corner
        info_lines = [
            f"Mouse: ({mouse_x}, {mouse_y})",
            f"Detected Hex: ({detected_q}, {detected_r}) [{grid_status}]",
            f"Grid Origin: ({self.origin_x:.1f}, {self.origin_y:.1f})",
            f"Hex Size: {self.hex_size:.2f}",
            f"Grid Bounds: ({grid_left:.1f}, {grid_top:.1f}, {grid_pixel_width:.1f}, {grid_pixel_height:.1f})"
        ]
        
        # Draw info panel background
        panel_x = 10
        panel_y = 10
        panel_width = 500
        panel_height = len(info_lines) * 25 + 10
        
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill((0, 0, 0, 200))
        screen.blit(panel_surface, (panel_x, panel_y))
        
        # Draw info text
        for i, line in enumerate(info_lines):
            text_surface = large_font.render(line, True, white)
            screen.blit(text_surface, (panel_x + 5, panel_y + 5 + i * 25))
        
        # Draw panel boundary rectangles for validation
        # Left panel boundary
        left_panel_rect = pygame.Rect(0, self.TOP_MARGIN, self.LEFT_PANEL_WIDTH, 
                                      self.SCREEN_HEIGHT - self.TOP_MARGIN - self.BOTTOM_HUB_HEIGHT)
        pygame.draw.rect(screen, (0, 255, 255), left_panel_rect, 1)  # Cyan
        
        # Right panel boundary
        right_panel_rect = pygame.Rect(self.SCREEN_WIDTH - self.RIGHT_PANEL_WIDTH, self.TOP_MARGIN,
                                       self.RIGHT_PANEL_WIDTH,
                                       self.SCREEN_HEIGHT - self.TOP_MARGIN - self.BOTTOM_HUB_HEIGHT)
        pygame.draw.rect(screen, (255, 0, 255), right_panel_rect, 1)  # Magenta
        
        # Bottom hub boundary
        bottom_hub_rect = pygame.Rect(0, self.SCREEN_HEIGHT - self.BOTTOM_HUB_HEIGHT,
                                      self.SCREEN_WIDTH, self.BOTTOM_HUB_HEIGHT)
        pygame.draw.rect(screen, (255, 255, 255), bottom_hub_rect, 1)  # White
        
        # Top margin boundary
        top_margin_rect = pygame.Rect(0, 0, self.SCREEN_WIDTH, self.TOP_MARGIN)
        pygame.draw.rect(screen, (255, 255, 0), top_margin_rect, 1)  # Yellow
    
    def _draw_hex_cards(self, screen: pygame.Surface) -> None:
        """Draw all hex cards with flip animation.
        
        Iterates over all hex_cards and renders each one using HexCardRenderer.
        This is Layer 2 (Z=2) - rendered after grid, before UI panels.
        
        Args:
            screen: Pygame surface to draw on
        
        Requirements:
        - 9.5: Render cards with flip animation
        - 9.6: Use flip_value_eased for smooth animation
        """
        # Check if hex_cards attribute exists (defensive check)
        if not hasattr(self, 'hex_cards'):
            return
        
        # Iterate over all hex cards
        for hex_card in self.hex_cards:
            # Render card with eased flip value
            self.hex_card_renderer.render_card(screen, hex_card, hex_card.flip_value_eased)
            
            # Render edge stats (Layer 3: Card overlays)
            # Only render stats when card is showing front (flip_value_eased >= 0.5)
            if hex_card.flip_value_eased >= 0.5:
                self._render_edge_stats(screen, hex_card)
    
    def _draw_hover_highlights(self, screen: pygame.Surface) -> None:
        """Draw hover highlights for hovered hexes.
        
        This is Layer 4 (Z=4) - rendered after cards, before UI panels.
        Draws a cyan glow border around the hovered hex.
        
        Args:
            screen: Pygame surface to draw on
        
        Requirements:
        - 9.1: Draw cyan glow border for hovered hex
        """
        # Check if there is a hovered hex
        if self.ui_state.hovered_hex is None:
            return
        
        # Check if the hovered hex has a card
        hovered_hex_coord = self.ui_state.hovered_hex
        
        # Find the hex card at the hovered position
        for hex_card in self.ui_state.hex_cards:
            if hex_card.hex_coord == hovered_hex_coord:
                # Draw cyan glow border (2px, 80% alpha)
                cyan_color = (0, 255, 255, int(255 * 0.8))  # Cyan with 80% alpha
                
                # Create a temporary surface with per-pixel alpha for the glow
                temp_surface = pygame.Surface((int(self.hex_size * 3), int(self.hex_size * 3)), pygame.SRCALPHA)
                
                # Calculate center position relative to temp surface
                temp_center_x = self.hex_size * 1.5
                temp_center_y = self.hex_size * 1.5
                
                # Draw the hex border on temp surface
                corners = self._get_hex_corners(temp_center_x, temp_center_y, self.hex_size)
                pygame.draw.polygon(temp_surface, cyan_color, corners, 2)
                
                # Blit temp surface to screen at card position
                blit_x = hex_card.position[0] - self.hex_size * 1.5
                blit_y = hex_card.position[1] - self.hex_size * 1.5
                screen.blit(temp_surface, (blit_x, blit_y))
                
                break
    
    def _draw_priority_popup(self, screen: pygame.Surface) -> None:
        """Draw priority/stat popup for hovered card.
        
        Displays card information (name, rarity, stats, passive) in a tooltip
        near the mouse cursor when hovering over a card.
        
        This is Layer 6 (Z=6) - rendered after UI panels, before debug overlay.
        
        Args:
            screen: Pygame surface to draw on
        
        Requirements:
        - T1.3: Integrate CyberRenderer draw_priority_popup functionality
        """
        # Check if there is a hovered hex
        if self.ui_state.hovered_hex is None or self.last_input_state is None:
            return
        
        # Find the hex card at the hovered position
        hovered_card = None
        for hex_card in self.ui_state.hex_cards:
            if hex_card.hex_coord == self.ui_state.hovered_hex:
                hovered_card = hex_card.card_data
                break
        
        if hovered_card is None:
            return
        
        # Get mouse position
        mx, my = self.last_input_state.mouse_pos
        
        # Create font for popup text
        font = pygame.font.Font(None, 16)
        font_bold = pygame.font.Font(None, 18)
        
        # Build popup lines
        lines = []
        lines.append(f"{hovered_card.name.upper()}")
        lines.append(f"Rarity: {hovered_card.rarity}")
        
        # Show edges (rotated stats)
        edges = hovered_card.rotated_edges()
        for i, (stat_name, value) in enumerate(edges[:6]):
            if value > 0 and not str(stat_name).startswith("_"):
                # Use short stat names
                stat_short = {
                    "Power": "PW",
                    "Durability": "DR",
                    "Speed": "SP",
                    "Intelligence": "IN",
                    "Harmony": "HR",
                    "Spread": "SD"
                }
                short = stat_short.get(stat_name, stat_name[:2])
                lines.append(f"{short}: {value}")
        
        # Passive
        passive = hovered_card.passive_type
        if passive and passive != "none":
            lines.append(f"✦ {passive}")
        
        # Calculate popup dimensions
        padding = 8
        line_h = 16
        max_w = max(font.size(line)[0] for line in lines) if lines else 100
        popup_w = max_w + padding * 2
        popup_h = len(lines) * line_h + padding * 2
        
        # Position near mouse
        px = mx + 20
        py = my - popup_h // 2
        
        # Keep on screen
        W, H = screen.get_size()
        if px + popup_w > W - 10:
            px = mx - popup_w - 20
        if py < 10:
            py = 10
        if py + popup_h > H - 10:
            py = H - popup_h - 10
        
        # Draw background
        popup_rect = pygame.Rect(px, py, popup_w, popup_h)
        # Create semi-transparent background
        popup_surface = pygame.Surface((popup_w, popup_h), pygame.SRCALPHA)
        popup_surface.fill((8, 10, 18, 240))
        screen.blit(popup_surface, (px, py))
        
        # Draw border
        pygame.draw.rect(screen, (0, 242, 255), popup_rect, width=1, border_radius=6)
        
        # Draw text
        y = py + padding
        for i, line in enumerate(lines):
            # Use bold font for first line (card name)
            current_font = font_bold if i == 0 else font
            text_img = current_font.render(line, True, (255, 255, 255))
            screen.blit(text_img, (px + padding, y))
            y += line_h
    
    def _draw_void_background(self, screen: pygame.Surface) -> None:
        """Draw void/space background with cyber VFX effects.
        
        Fills screen with dark space-themed background color, then adds
        CyberRenderer VFX effects (grid lines, scanlines) for visual consistency
        with run_game.py.
        
        This is Layer 0 (Z=0) - rendered first.
        
        Args:
            screen: Pygame surface to draw on
        
        Requirements:
        - 2.1: Render void background as first layer
        - T1.3: Integrate CyberRenderer draw_vfx_base effects
        """
        # Dark space color (very dark blue-black)
        void_color = (5, 8, 15)
        screen.fill(void_color)
        
        # Add CyberRenderer VFX effects (T1.3: CyberRenderer integration)
        # Draw cyber grid background with horizon lines and perspective
        W, H = screen.get_size()
        
        # Horizon grid lines (horizontal)
        for i in range(12):
            y = H - int((i ** 1.6) * 8)
            alpha = max(8, 120 - i * 10)
            # Create color with alpha
            color = (20, 25, 45, alpha)
            # Draw line on a temporary surface with alpha support
            line_surface = pygame.Surface((W, 1), pygame.SRCALPHA)
            line_surface.fill(color)
            screen.blit(line_surface, (0, y))
        
        # Vertical perspective lines
        horizon_y = 140
        center_x = W // 2
        for lane in range(-8, 9):
            start_x = center_x + lane * 80
            end_x = center_x + lane * 360
            # Create line with alpha
            line_color = (20, 25, 45, 35)
            # Calculate line points
            points = [(start_x, horizon_y), (end_x, H)]
            # Draw line with alpha using a temporary surface
            if start_x >= 0 and end_x >= 0 and start_x < W and end_x < W:
                pygame.draw.line(screen, (20, 25, 45), points[0], points[1], 1)
    
    def _draw_left_panel(self, screen: pygame.Surface) -> None:
        """Draw left panel with passive information.
        
        Displays player's passive skills and hand information.
        Panel has semi-transparent dark background with cyan border glow.
        
        Args:
            screen: Pygame surface to draw on
        
        Requirements:
        - 2.1: Left panel 300px width for passive information
        - 8.1: Semi-transparent dark background with cyan border
        """
        # Panel dimensions
        panel_x = 0
        panel_y = self.TOP_MARGIN
        panel_width = self.LEFT_PANEL_WIDTH
        panel_height = self.SCREEN_HEIGHT - self.TOP_MARGIN - self.BOTTOM_HUB_HEIGHT
        
        # Create semi-transparent surface
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill((20, 20, 40, 200))  # Dark with alpha
        
        # Draw panel background
        screen.blit(panel_surface, (panel_x, panel_y))
        
        # Draw cyan border glow (2px)
        border_color = (0, 255, 255)  # Cyan
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(screen, border_color, panel_rect, 2)
        
        # Font for text
        font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 18)
        
        # Get current player
        current_player = self.core_game_state.current_player
        
        # Section 1: Passive Icons (y_offset: 20)
        y_offset = 20
        label = font.render("Passive Skills", True, (0, 255, 255))
        screen.blit(label, (panel_x + 10, panel_y + y_offset))
        y_offset += 35
        
        # Placeholder passive icons (5 slots, 64x64 each)
        icon_size = 64
        icon_spacing = 10
        for i in range(5):
            icon_x = panel_x + (panel_width - icon_size) // 2
            icon_y = panel_y + y_offset + i * (icon_size + icon_spacing)
            
            # Draw colored placeholder square
            color = [(100, 100, 255), (255, 100, 100), (100, 255, 100), 
                     (255, 255, 100), (255, 100, 255)][i]
            pygame.draw.rect(screen, color, (icon_x, icon_y, icon_size, icon_size))
            pygame.draw.rect(screen, (255, 255, 255), (icon_x, icon_y, icon_size, icon_size), 1)
        
        # Section 2: Passive Description (y_offset: 400)
        y_offset = 400
        label = font.render("Description", True, (0, 255, 255))
        screen.blit(label, (panel_x + 10, panel_y + y_offset))
        y_offset += 30
        
        # Text area with border
        text_area_rect = pygame.Rect(panel_x + 20, panel_y + y_offset, 260, 200)
        pygame.draw.rect(screen, (40, 40, 60), text_area_rect)
        pygame.draw.rect(screen, (100, 100, 150), text_area_rect, 1)
        
        # Placeholder text
        desc_text = "Hover over passive"
        desc_text2 = "to see description"
        text_surface = small_font.render(desc_text, True, (200, 200, 200))
        text_surface2 = small_font.render(desc_text2, True, (200, 200, 200))
        screen.blit(text_surface, (panel_x + 30, panel_y + y_offset + 10))
        screen.blit(text_surface2, (panel_x + 30, panel_y + y_offset + 30))
        
        # Section 3: Hand/Deck Display (y_offset: 650)
        y_offset = 650
        
        # Defensive check for mock objects
        try:
            hand_count = len(current_player.hand) if hasattr(current_player, 'hand') else 0
            deck_count = sum(current_player.copies.values()) - hand_count if hasattr(current_player, 'copies') else 0
        except (TypeError, AttributeError):
            # Handle mock objects
            hand_count = 0
            deck_count = 0
        
        hand_text = f"Hand: {hand_count}"
        deck_text = f"Deck: {deck_count}"
        
        hand_surface = font.render(hand_text, True, (0, 255, 255))
        deck_surface = font.render(deck_text, True, (0, 255, 255))
        
        screen.blit(hand_surface, (panel_x + 20, panel_y + y_offset))
        screen.blit(deck_surface, (panel_x + 20, panel_y + y_offset + 30))
    
    def _draw_right_panel(self, screen: pygame.Surface) -> None:
        """Draw right panel with player information.
        
        Uses the same beautiful player panel from GameLoopScene (draw_player_panel).
        This provides consistent UI across scenes and allows clicking to switch players.
        
        Args:
            screen: Pygame surface to draw on
        
        Requirements:
        - 2.2: Right panel 300px width for player information
        - 9.1: Semi-transparent dark background with magenta border
        - 20.2: Display strategy names from lobby data
        - 20.3: Display HP bars with color coding
        - T2.3b: Clickable player panel for player switching
        """
        from ui.hud_renderer import draw_player_panel
        
        # Initialize fonts (same as GameLoopScene)
        def _font(name, size, bold=False):
            try:
                return pygame.font.SysFont(name, size, bold=bold)
            except Exception:
                return pygame.font.SysFont("consolas", size, bold=bold)
        
        fonts = {
            "md_bold": _font("consolas", 16, bold=True),
            "sm_bold": _font("consolas", 13, bold=True),
        }
        
        # Draw player panel (right side) using the same function as GameLoopScene
        players = self.core_game_state.game.players
        selected_player_idx = self.core_game_state.view_player_index
        panel_x = screen.get_width() - 300
        panel_y = 20
        
        # Draw the beautiful player panel from GameLoopScene
        player_rects = draw_player_panel(
            screen,
            players,
            selected_player_idx,
            fonts["md_bold"],
            fonts["sm_bold"],
            panel_x,
            panel_y
        )
        
        # Store player rectangles in UIState for click detection (T2.3b)
        if self.ui_state:
            self.ui_state.player_panel_rects = player_rects
        
        # Section 2: Synergy Icons (below player panel)
        # Keep the synergy section from the original implementation
        font = pygame.font.Font(None, 22)
        y_offset = 700
        label = font.render("Synergies", True, (255, 0, 255))
        screen.blit(label, (panel_x + 10, y_offset))
        y_offset += 30
        
        # Placeholder synergy icons (4x2 grid, 48x48 each)
        icon_size = 48
        icon_spacing = 10
        icons_per_row = 4
        
        for i in range(8):
            row = i // icons_per_row
            col = i % icons_per_row
            
            icon_x = panel_x + 20 + col * (icon_size + icon_spacing)
            icon_y = panel_y + y_offset + row * (icon_size + icon_spacing)
            
            # Draw colored placeholder square
            color = [(255, 100, 100), (100, 255, 100), (100, 100, 255), (255, 255, 100),
                     (255, 100, 255), (100, 255, 255), (255, 200, 100), (200, 100, 255)][i]
            pygame.draw.rect(screen, color, (icon_x, icon_y, icon_size, icon_size))
            pygame.draw.rect(screen, (255, 255, 255), (icon_x, icon_y, icon_size, icon_size), 1)
    
    def _draw_hand_panel(self, screen: pygame.Surface) -> None:
        """Draw hand panel showing the player's hand cards in hex card slots.

        Replaces the old bottom hub. Renders up to 8 hex-shaped card slots
        with actual hand card data, a selection highlight, rotation badge, and
        a 220px detail panel on the right for the selected card.

        Uses screen.get_width() / screen.get_height() instead of class
        constants so the panel is always anchored to the real display surface.

        Args:
            screen: Pygame surface to draw on

        Requirements:
        - 2.3: Bottom hand panel 175px height
        - 5.1: Clicking a card slot selects the card and enters placement mode
        """
        # ── Dimensions ────────────────────────────────────────────────────────
        screen_w = screen.get_width()
        screen_h = screen.get_height()
        panel_h  = self.BOTTOM_HUB_HEIGHT          # 175
        panel_y  = screen_h - panel_h

        DETAIL_W  = 220
        HEADER_H  = 26
        MAX_SLOTS = 8
        HEX_W = HEX_H = 76                         # hex shape size
        SLOT_W    = 88                              # slot column width
        SLOT_GAP  = 8
        SLOT_PAD  = 16                              # left padding

        # Colour palette (matching HTML mockup)
        C_BG          = (10,  13,  26,  247)
        C_BORDER      = (0,  242, 255,  64)
        C_CYAN        = (0,  242, 255)
        C_GOLD        = (255, 204,   0)
        C_DIM         = (100, 110, 135)
        C_TEXT        = (230, 235, 255)
        C_TEXT_BRIGHT = (240, 245, 255)

        GROUP_COLORS  = {
            'MIND':  (70,  150, 255),
            'EXIST': (255, 110,  80),
            'CONN':  ( 60, 235, 150),
        }
        RARITY_COLORS = {
            'S': (255,  80, 120),
            'A': (255, 204,   0),
            'B': (  0, 242, 255),
            'C': (145, 155, 185),
        }

        # ── Fonts ─────────────────────────────────────────────────────────────
        try:
            f_tiny  = pygame.font.SysFont("consolas", 11)
            f_small = pygame.font.SysFont("consolas", 13)
            f_name  = pygame.font.SysFont("consolas", 10)
        except Exception:
            f_tiny  = pygame.font.Font(None, 16)
            f_small = pygame.font.Font(None, 18)
            f_name  = pygame.font.Font(None, 15)

        # ── Background ────────────────────────────────────────────────────────
        bg = pygame.Surface((screen_w, panel_h), pygame.SRCALPHA)
        bg.fill(C_BG)
        screen.blit(bg, (0, panel_y))

        # Top border line (dim cyan)
        border_surf = pygame.Surface((screen_w, 1), pygame.SRCALPHA)
        border_surf.fill(C_BORDER)
        screen.blit(border_surf, (0, panel_y))

        # ── Hand data ─────────────────────────────────────────────────────────
        current_player = self.core_game_state.current_player
        hand: list = []
        try:
            if hasattr(current_player, 'hand') and current_player.hand:
                hand = list(current_player.hand)
        except (TypeError, AttributeError):
            pass

        turn        = getattr(self.core_game_state, 'turn', 0)
        hand_count  = len(hand)
        selected_idx = getattr(self.ui_state, 'selected_hand_idx', None)

        # ── Header row ────────────────────────────────────────────────────────
        hdr_y = panel_y + 5

        lbl = f_tiny.render("HAND BUFFER", True, (0, 180, 210))
        screen.blit(lbl, (SLOT_PAD, hdr_y))

        meta_cx = screen_w // 2
        for i, txt in enumerate([f"CARDS {hand_count}/8",
                                  f"PLACED 0/1",
                                  f"TURN {turn}"]):
            s = f_tiny.render(txt, True, C_DIM)
            screen.blit(s, (meta_cx - 200 + i * 140, hdr_y))

        hint = f_tiny.render("[CLICK] select  ·  [R] rotate  ·  [ESC] cancel",
                             True, (60, 70, 95))
        screen.blit(hint, (screen_w - DETAIL_W - hint.get_width() - 16, hdr_y))

        # Separator under header
        sep_y = panel_y + HEADER_H
        pygame.draw.line(screen, (40, 45, 65), (0, sep_y), (screen_w, sep_y), 1)

        # ── Helper: draw pointy-top hex polygon ───────────────────────────────
        def hex_pts(ox: int, oy: int, w: int = HEX_W, h: int = HEX_H):
            """Return 6-point polygon for a pointy-top hex at offset (ox, oy)."""
            hw, hh = w // 2, h // 2
            q4h = h // 4
            return [
                (ox + hw,  oy     ),   # top
                (ox + w,   oy + q4h),  # top-right
                (ox + w,   oy + h - q4h),  # bot-right
                (ox + hw,  oy + h ),   # bottom
                (ox,       oy + h - q4h),  # bot-left
                (ox,       oy + q4h),  # top-left
            ]

        # ── Cards row ─────────────────────────────────────────────────────────
        cards_h   = panel_h - HEADER_H - 2
        cards_area_w = screen_w - DETAIL_W

        # Store hit-rects so _get_card_at_hand_position can use them
        self._hand_slot_rects: list = []

        for i in range(MAX_SLOTS):
            slot_x  = SLOT_PAD + i * (SLOT_W + SLOT_GAP)
            slot_cx = slot_x + SLOT_W // 2
            hex_x   = slot_x + (SLOT_W - HEX_W) // 2
            hex_y   = sep_y + 2 + (cards_h - HEX_H - 16) // 2   # leave 16px for badge

            pts = hex_pts(hex_x, hex_y)
            self._hand_slot_rects.append(
                pygame.Rect(hex_x, hex_y, HEX_W, HEX_H)
            )

            has_card   = i < len(hand)
            is_selected = has_card and (i == selected_idx)

            if not has_card:
                # Empty ghost slot
                ghost = pygame.Surface((HEX_W, HEX_H), pygame.SRCALPHA)
                local = [(p[0] - hex_x, p[1] - hex_y) for p in pts]
                pygame.draw.polygon(ghost, (20, 25, 45, 90), local)
                pygame.draw.polygon(ghost, (50, 60, 95, 60), local, 1)
                screen.blit(ghost, (hex_x, hex_y))
                continue

            card = hand[i]

            # --- Card properties (safe fallbacks) ---
            card_name  = getattr(card, 'name', f'CARD {i+1}')
            rotation   = getattr(card, 'rotation', 0)
            rarity     = getattr(card, 'rarity', 'C').upper()
            group_raw  = getattr(card, 'group',
                         getattr(card, 'type', '')).upper()
            group_col  = GROUP_COLORS.get(group_raw, (145, 155, 185))
            rarity_col = RARITY_COLORS.get(rarity,   (145, 155, 185))
            has_passive = bool(getattr(card, 'passive', None))

            try:
                pwr = sum(v for _, v in card.edges)
            except (TypeError, AttributeError):
                pwr = getattr(card, 'power', 0)

            # --- Hex background surface (SRCALPHA for clean edges) ---
            hex_surf = pygame.Surface((HEX_W, HEX_H), pygame.SRCALPHA)
            local    = [(p[0] - hex_x, p[1] - hex_y) for p in pts]
            pygame.draw.polygon(hex_surf, (18, 22, 42, 230), local)
            border_col = (0, 242, 255, 220) if is_selected else (50, 60, 95, 140)
            pygame.draw.polygon(hex_surf, border_col, local, 1)
            screen.blit(hex_surf, (hex_x, hex_y))

            # Glow ring for selected
            if is_selected:
                glow = pygame.Surface((HEX_W + 20, HEX_H + 20), pygame.SRCALPHA)
                gl = [(p[0] - hex_x + 10, p[1] - hex_y + 10) for p in pts]
                pygame.draw.polygon(glow, (0, 242, 255, 35), gl, 7)
                screen.blit(glow, (hex_x - 10, hex_y - 10))

            # Rarity accent bar (horizontal stripe near top of hex)
            bar_w = 36
            bar_surf = pygame.Surface((bar_w, 3), pygame.SRCALPHA)
            bar_surf.fill((*rarity_col, 210))
            screen.blit(bar_surf, (slot_cx - bar_w // 2, hex_y + 6))

            # Passive indicator dot (top-right of hex)
            if has_passive:
                pygame.draw.circle(screen, (255, 200, 80),
                                   (hex_x + HEX_W - 10, hex_y + 14), 3)

            # Card name (split words across 2 lines)
            words = card_name.split()
            line1 = words[0] if words else card_name
            line2 = ' '.join(words[1:]) if len(words) > 1 else ''
            n1 = f_name.render(line1.upper(), True, C_TEXT)
            screen.blit(n1, (slot_cx - n1.get_width() // 2, hex_y + 22))
            if line2:
                n2 = f_name.render(line2.upper(), True, C_TEXT)
                screen.blit(n2, (slot_cx - n2.get_width() // 2, hex_y + 34))

            # Power label
            pwr_s = f_name.render(f"PWR {pwr}", True, group_col)
            screen.blit(pwr_s, (slot_cx - pwr_s.get_width() // 2, hex_y + 50))

            # Group dot (bottom-right)
            pygame.draw.circle(screen, group_col,
                               (hex_x + HEX_W - 10, hex_y + HEX_H - 12), 4)

            # Selection indicator (tiny bar above hex)
            if is_selected:
                pygame.draw.rect(screen, C_CYAN,
                                 (slot_cx - 2, hex_y - 7, 3, 5))

            # Rotation badge (below hex)
            rot_s = f_name.render(f"ROT {rotation}°", True, C_DIM)
            screen.blit(rot_s, (slot_cx - rot_s.get_width() // 2,
                                hex_y + HEX_H + 3))

        # ── Divider line before detail panel ──────────────────────────────────
        div_x = screen_w - DETAIL_W
        pygame.draw.line(screen, (0, 242, 255, 25),
                         (div_x, sep_y + 4), (div_x, panel_y + panel_h - 4), 1)

        # ── Selected card detail panel ─────────────────────────────────────────
        if selected_idx is not None and selected_idx < len(hand):
            card      = hand[selected_idx]
            dx        = div_x + 12
            dy        = sep_y + 8

            # "SELECTED" label
            ttl = f_tiny.render("SELECTED", True, (0, 130, 155))
            screen.blit(ttl, (dx, dy));  dy += 13
            pygame.draw.line(screen, (0, 60, 80),
                             (dx, dy), (dx + DETAIL_W - 24, dy), 1);  dy += 5

            # Card name
            disp = getattr(card, 'name', 'Unknown')
            ns = f_small.render(disp, True, C_TEXT_BRIGHT)
            screen.blit(ns, (dx, dy));  dy += 18

            # Helper: key/value row
            def kv_row(key, val, col=C_TEXT_BRIGHT):
                nonlocal dy
                ks = f_tiny.render(key, True, C_DIM)
                vs = f_tiny.render(str(val), True, col)
                screen.blit(ks, (dx, dy))
                screen.blit(vs, (dx + 70, dy))
                dy += 13

            rarity     = getattr(card, 'rarity', 'C').upper()
            rarity_col = RARITY_COLORS.get(rarity, (145, 155, 185))
            kv_row("RARITY",   rarity,         rarity_col)

            group_raw  = getattr(card, 'group',
                         getattr(card, 'type', 'N/A')).upper()
            group_col  = GROUP_COLORS.get(group_raw, (145, 155, 185))
            kv_row("GROUP",    group_raw,       group_col)

            try:
                pwr = sum(v for _, v in card.edges)
            except (TypeError, AttributeError):
                pwr = getattr(card, 'power', 0)
            kv_row("POWER",    pwr,             C_GOLD)

            rotation  = getattr(card, 'rotation', 0)
            next_rot  = (rotation + 60) % 360
            kv_row("ROTATION", f"{rotation}°  →  {next_rot}°")

            # Passive ability (word-wrapped)
            passive_txt = getattr(card, 'passive', None)
            if passive_txt:
                dy += 3
                words = f"✦ {passive_txt}".split()
                line, lines = "", []
                for w in words:
                    test = (line + " " + w).strip()
                    if len(test) <= 26:
                        line = test
                    else:
                        if line:
                            lines.append(line)
                        line = w
                if line:
                    lines.append(line)

                pygame.draw.rect(screen, (255, 200, 80, 0),
                                 (dx - 5, dy, 2, len(lines) * 12))
                pygame.draw.rect(screen, (100, 80, 20),
                                 (dx - 5, dy, 2, len(lines) * 12))
                for ln in lines:
                    ps = f_name.render(ln, True, (190, 150, 55))
                    screen.blit(ps, (dx, dy));  dy += 12

            # Action buttons (pinned to panel bottom)
            btn_y = panel_y + panel_h - 26
            bw    = (DETAIL_W - 28) // 2 - 4

            # Place button
            pr = pygame.Rect(dx, btn_y, bw, 18)
            btn_bg = pygame.Surface((bw, 18), pygame.SRCALPHA)
            btn_bg.fill((0, 242, 255, 13))
            screen.blit(btn_bg, (dx, btn_y))
            pygame.draw.rect(screen, (0, 140, 165), pr, 1, border_radius=2)
            ps = f_name.render("[CLICK HEX] PLACE", True, (0, 190, 210))
            screen.blit(ps, (pr.centerx - ps.get_width() // 2, btn_y + 4))

            # Rotate button
            rr = pygame.Rect(dx + bw + 6, btn_y, bw, 18)
            pygame.draw.rect(screen, (30, 35, 55), rr, border_radius=2)
            pygame.draw.rect(screen, (70, 80, 105), rr, 1, border_radius=2)
            rs = f_name.render("[R] ROTATE", True, (100, 110, 135))
            screen.blit(rs, (rr.centerx - rs.get_width() // 2, btn_y + 4))
    
    def _draw_hex_border_highlight(self, screen: pygame.Surface, hex_coord: Tuple[int, int], 
                                   color: Tuple[int, int, int], width: int = 3) -> None:
        """Draw a clean hex border highlight at the specified hex coordinate.
        
        Gets hex corners and draws a polygon with specified color and width.
        No particles, no glow effects, just a clean line.
        
        Args:
            screen: Pygame surface to draw on
            hex_coord: (q, r) axial coordinate of the hex
            color: RGB color tuple for the border
            width: Line width in pixels (default: 3)
        
        Requirements:
        - 19.1: Draw hex border with specified color
        - 19.2: Use clean line without glow effects or particles
        """
        # Convert hex coordinate to pixel position
        center_x, center_y = self.hex_system.hex_to_pixel(hex_coord[0], hex_coord[1])
        
        # Get hex corners using existing helper method
        corners = self._get_hex_corners(center_x, center_y, self.hex_size)
        
        # Draw polygon with specified color and width
        pygame.draw.polygon(screen, color, corners, width)
    
    def _draw_invalid_hex_border(self, screen: pygame.Surface, hex_coord: Tuple[int, int]) -> None:
        """Draw red border for invalid placement hex.
        
        Calls _draw_hex_border_highlight() with red color to indicate
        that the hex is not valid for card placement.
        
        Args:
            screen: Pygame surface to draw on
            hex_coord: (q, r) axial coordinate of the hex
        
        Requirements:
        - 19.2: Draw red border for invalid placement
        """
        # Red color for invalid placement
        red_color = (255, 0, 0)
        
        # Call helper with red color
        self._draw_hex_border_highlight(screen, hex_coord, red_color, width=3)
    
    def _render_placement_preview(self, screen: pygame.Surface) -> None:
        """Render placement preview with ghost card and hex border.
        
        Checks if UIState.is_placing is True, gets mouse position, converts
        to nearest hex, validates placement, and renders appropriate feedback:
        - Invalid hex: red border
        - Valid hex: cyan border + ghost card with rotation and transparency
        
        Args:
            screen: Pygame surface to draw on
        
        Requirements:
        - 19.1: Check if UIState.is_placing is True
        - 19.2: Draw red border for invalid hex, cyan for valid
        - 19.3: Render ghost card with preview_rotation
        - 19.4: Set alpha to 120 (47% transparency)
        """
        # Check if in placement mode
        if not self.ui_state.is_placing:
            return
        
        # Check if PlacementController exists and has selected card
        if not hasattr(self, 'placement_controller'):
            return
        
        if self.placement_controller.selected_card is None:
            return
        
        # Get mouse position from last input state
        if self.last_input_state is None:
            return
        
        mouse_x, mouse_y = self.last_input_state.mouse_pos
        
        # Convert mouse position to nearest hex coordinate
        hex_coord = self.hex_system.pixel_to_hex(mouse_x, mouse_y)
        
        # Check if hex is in grid
        if hex_coord not in self.hex_grid:
            return
        
        # Store preview hex in placement controller
        self.placement_controller.preview_hex = hex_coord
        
        # Check if hex is valid for placement
        current_player_id = getattr(self, 'current_player_id', 0)
        is_valid = self.placement_controller.is_valid_placement(hex_coord, current_player_id)
        
        if not is_valid:
            # Draw red border for invalid hex (Requirement 19.2)
            self._draw_invalid_hex_border(screen, hex_coord)
            return
        
        # Valid hex: draw cyan border (Requirement 19.2)
        cyan_color = (0, 255, 255)
        self._draw_hex_border_highlight(screen, hex_coord, cyan_color, width=3)
        
        # Render ghost card at preview hex (Requirement 19.3, 19.4)
        # Get card front image using AssetLoader
        card_name = self.placement_controller.selected_card.name
        faces = self.asset_loader.get(card_name)
        front_image = faces.front
        
        # Apply preview_rotation using pygame.transform.rotate()
        rotation_angle = self.placement_controller.preview_rotation
        if rotation_angle != 0:
            rotated_image = pygame.transform.rotate(front_image, -rotation_angle)  # Negative for clockwise
        else:
            rotated_image = front_image
        
        # Set alpha to 120 (47% transparency) (Requirement 19.4)
        ghost_image = rotated_image.copy()
        ghost_image.set_alpha(120)
        
        # Get hex center position (snapped to grid)
        center_x, center_y = self.hex_system.hex_to_pixel(hex_coord[0], hex_coord[1])
        
        # Blit at hex center position
        image_rect = ghost_image.get_rect(center=(center_x, center_y))
        screen.blit(ghost_image, image_rect)
    
    def _rotate_point(self, x: float, y: float, angle_degrees: float, 
                     origin_x: float, origin_y: float) -> Tuple[float, float]:
        """Apply rotation matrix to point coordinates.
        
        Args:
            x: Point x coordinate
            y: Point y coordinate
            angle_degrees: Rotation angle in degrees
            origin_x: Rotation origin x
            origin_y: Rotation origin y
        
        Returns:
            Rotated (x, y) tuple
        
        Requirements: 8.2
        """
        # Convert angle to radians
        angle_rad = math.radians(angle_degrees)
        
        # Translate point to origin
        dx = x - origin_x
        dy = y - origin_y
        
        # Apply rotation matrix
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        rotated_x = dx * cos_a - dy * sin_a
        rotated_y = dx * sin_a + dy * cos_a
        
        # Translate back
        return (origin_x + rotated_x, origin_y + rotated_y)
    
    def _get_rotated_edge_stats(self, hex_card: HexCard) -> Dict[str, Tuple[str, int]]:
        """Get stat-to-edge mapping based on card rotation.
        
        Args:
            hex_card: HexCard object with card data and rotation
        
        Returns:
            Dictionary mapping edge_name -> (stat_name, stat_value)
            Edge names: "N", "NE", "SE", "S", "SW", "NW"
        
        Requirements: 8.2, 8.4
        """
        # Get rotated edges from card data
        rotated_edges = hex_card.card_data.rotated_edges()
        
        # Define edge names in order (starting from North, clockwise)
        edge_names = ["N", "NE", "SE", "S", "SW", "NW"]
        
        # Map edges to names
        edge_stats = {}
        for i, edge_name in enumerate(edge_names):
            if i < len(rotated_edges):
                stat_name, stat_value = rotated_edges[i]
                edge_stats[edge_name] = (stat_name, stat_value)
            else:
                edge_stats[edge_name] = ("", 0)
        
        return edge_stats
    
    def _render_stat_text(self, screen: pygame.Surface, position: Tuple[float, float], 
                         stat_value: int, stat_name: str) -> None:
        """Render stat value with background circle.
        
        Args:
            screen: Pygame surface to draw on
            position: (x, y) position for stat text center
            stat_value: Stat value to render
            stat_name: Stat name for color coding
        
        Requirements: 8.3
        """
        # Circle parameters
        circle_radius = 16
        border_width = 2
        
        # Draw background circle (dark with transparency)
        circle_surface = pygame.Surface((circle_radius * 2 + 4, circle_radius * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(circle_surface, (20, 20, 40, 220), 
                          (circle_radius + 2, circle_radius + 2), circle_radius)
        
        # Draw white border
        pygame.draw.circle(circle_surface, (255, 255, 255, 255), 
                          (circle_radius + 2, circle_radius + 2), circle_radius, border_width)
        
        # Blit circle to screen
        circle_rect = circle_surface.get_rect(center=(int(position[0]), int(position[1])))
        screen.blit(circle_surface, circle_rect)
        
        # Render stat value text (always upright, rotation=0)
        font = pygame.font.Font(None, 24)
        text_surface = font.render(str(stat_value), True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(int(position[0]), int(position[1])))
        screen.blit(text_surface, text_rect)
    
    def _render_edge_stats(self, screen: pygame.Surface, hex_card: HexCard) -> None:
        """Render stat values at hex edges.
        
        Args:
            screen: Pygame surface to draw on
            hex_card: HexCard object with card data and position
        
        Requirements: 8.1, 8.2, 8.3
        """
        # Get card position and hex size
        center_x, center_y = hex_card.position
        hex_size = hex_card.hex_size
        
        # Define base edge positions (before rotation)
        # Positions are at distance hex_size * 0.85 from center
        edge_distance = hex_size * 0.85
        
        # Base edge positions (flat-top hex, starting from North, clockwise)
        # N: top, NE: top-right, SE: bottom-right, S: bottom, SW: bottom-left, NW: top-left
        base_edge_positions = {
            "N":  (center_x, center_y - edge_distance),
            "NE": (center_x + edge_distance * math.sqrt(3) / 2, center_y - edge_distance / 2),
            "SE": (center_x + edge_distance * math.sqrt(3) / 2, center_y + edge_distance / 2),
            "S":  (center_x, center_y + edge_distance),
            "SW": (center_x - edge_distance * math.sqrt(3) / 2, center_y + edge_distance / 2),
            "NW": (center_x - edge_distance * math.sqrt(3) / 2, center_y - edge_distance / 2),
        }
        
        # Get rotated edge stats mapping
        edge_stats = self._get_rotated_edge_stats(hex_card)
        
        # Render stat at each edge
        for edge_name, (stat_name, stat_value) in edge_stats.items():
            if stat_name:  # Only render if stat exists
                position = base_edge_positions[edge_name]
                self._render_stat_text(screen, position, stat_value, stat_name)
    
    def draw(self, screen: pygame.Surface) -> None:
        """Render scene to screen.
        
        Args:
            screen: Pygame surface to draw on
        
        Requirements:
        - Layer 0: Background with CyberRenderer VFX
        - Layer 1: Hex grid
        - Layer 2: Hex cards
        - Layer 4: Interaction highlights
        - Layer 5: UI panels
        - Layer 6: Priority popup (hover tooltip)
        - Layer 7: Debug overlay (if debug_mode enabled)
        """
        # Layer 0: Void background with CyberRenderer VFX (T1.3)
        self._draw_void_background(screen)
        
        # Layer 1: Draw hex grid
        self._draw_hex_grid(screen)
        
        # Layer 2: Draw hex cards (Requirement 9.5, 9.6)
        self._draw_hex_cards(screen)
        
        # Layer 4: Draw hover highlights (Requirement 9.1)
        self._draw_hover_highlights(screen)
        
        # Layer 4: Draw placement preview (if in placement mode)
        self._render_placement_preview(screen)
        
        # Layer 5: Draw UI panels
        self._draw_left_panel(screen)
        self._draw_right_panel(screen)
        self._draw_hand_panel(screen)
        
        # Layer 5.5: Draw fast mode indicator (T2.2)
        if self.core_game_state.fast_mode:
            self._draw_fast_mode_indicator(screen)
        
        # Layer 6: Draw priority popup for hovered card (T1.3: CyberRenderer integration)
        self._draw_priority_popup(screen)
        
        # Layer 7: Draw debug overlay if enabled (Requirement 10.1)
        if self.debug_mode:
            self._draw_debug_overlay(screen)
        
        # TODO: Implement remaining rendering layers:
        # 3. Card overlays

    def _draw_fast_mode_indicator(self, screen: pygame.Surface) -> None:
        """Draw fast mode indicator when fast mode is active.
        
        Displays a lightning bolt icon and "FAST MODE" text in top-left corner.
        
        Args:
            screen: Pygame surface to draw on
        
        Requirements:
        - T2.2: Visual feedback for fast mode toggle
        """
        # Position in top-left corner (below turn counter if present)
        x = 20
        y = 80
        
        # Create semi-transparent background
        bg_width = 180
        bg_height = 40
        bg_surface = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
        bg_surface.fill((255, 215, 0, 100))  # Gold with transparency
        screen.blit(bg_surface, (x, y))
        
        # Draw border
        border_rect = pygame.Rect(x, y, bg_width, bg_height)
        pygame.draw.rect(screen, (255, 215, 0), border_rect, 2, border_radius=8)
        
        # Draw lightning bolt icon (⚡)
        icon_font = pygame.font.SysFont("segoeuisymbol", 24, bold=True)
        icon_text = icon_font.render("⚡", True, (255, 215, 0))
        screen.blit(icon_text, (x + 10, y + 8))
        
        # Draw "FAST MODE" text
        text_font = pygame.font.SysFont("consolas", 16, bold=True)
        text_surface = text_font.render("FAST MODE", True, (255, 255, 255))
        screen.blit(text_surface, (x + 45, y + 12))
