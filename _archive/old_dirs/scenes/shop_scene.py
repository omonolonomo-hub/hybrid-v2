"""
Retro-futuristic shop scene for Autochess Hybrid.

Refactored from ShopScreen to use Scene architecture:
- No while loop (controlled by SceneManager)
- Uses InputState for intent-based input
- Uses Actions for state modification (BuyCardAction, PlaceCardAction)
- Uses HexSystem for coordinate conversions
- Stores UI state in self.ui_state (THROWAWAY)
- Stores game state in self.core_game_state (SAVEABLE)
"""

import math
from collections import Counter
from typing import List, Optional, TYPE_CHECKING

import pygame

from core.scene import Scene
from core.core_game_state import CoreGameState
from core.ui_state import UIState
from core.input_state import InputState

if TYPE_CHECKING:
    from core.action_system import ActionSystem
    from core.animation_system import AnimationSystem

try:
    from engine_core.card import Card
    from engine_core.player import Player
    from engine_core.constants import (
        CARD_COSTS,
        STAT_TO_GROUP,
        MARKET_REFRESH_COST,
        STARTING_HP,
    )
    from engine_core.market import RARITY_WEIGHT
    from ui.card_meta import CATEGORY_META, get_passive_desc
    from ui.renderer_v3 import CyberRendererV3 as CyberRenderer, RARITY_COLORS as C_RARE
except ImportError:
    from ..engine_core.card import Card
    from ..engine_core.player import Player
    from ..engine_core.constants import (
        CARD_COSTS,
        STAT_TO_GROUP,
        MARKET_REFRESH_COST,
        STARTING_HP,
    )
    from ..engine_core.market import RARITY_WEIGHT
    from ..ui.card_meta import CATEGORY_META, get_passive_desc
    from ..ui.renderer_v3 import CyberRendererV3 as CyberRenderer, RARITY_COLORS as C_RARE


# Color palette
NEON = {
    "bg": (10, 11, 18),
    "grid": (20, 25, 45),
    "panel": (15, 20, 40, 185),
    "panel_dark": (12, 15, 28, 225),
    "card": (24, 28, 44, 240),
    "card_hover": (38, 46, 76, 255),
    "line": (50, 60, 95),
    "cyan": (0, 242, 255),
    "pink": (255, 0, 255),
    "gold": (255, 204, 0),
    "white": (240, 245, 255),
    "muted": (145, 155, 185),
    "danger": (255, 95, 110),
    "ok": (70, 225, 140),
    "sold": (60, 65, 84),
    "rarity_cols": {**C_RARE, "E": (255, 255, 255)},
}

GROUP_COLORS = {
    "EXISTENCE": (255, 110, 80),
    "MIND": (70, 150, 255),
    "CONNECTION": (60, 235, 150),
}

STAT_SHORT = {
    "Power": "PWR",
    "Durability": "DUR",
    "Size": "SIZ",
    "Speed": "SPD",
    "Meaning": "MNG",
    "Secret": "SEC",
    "Intelligence": "INT",
    "Trace": "TRC",
    "Gravity": "GRV",
    "Harmony": "HRM",
    "Spread": "SPR",
    "Prestige": "PRS",
}

# Layout constants
CARD_W = 300  # Increased from 264 (14% bigger, total 36% from original)
CARD_H = 490  # Increased from 432 (13% bigger, total 36% from original)
CARD_RADIUS = 12
CARD_GAP = 18  # Slightly reduced to fit bigger cards
SIDEBAR_W = 280
FOOTER_H = 84


# Helper functions
def _round_rect(surface, color, rect, radius, width=0):
    """Draw rounded rectangle."""
    pygame.draw.rect(surface, color, rect, width, border_radius=radius)


def _lerp_color(a, b, t):
    """Linear interpolation between two colors."""
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _darken(color, factor):
    """Darken a color by factor."""
    return tuple(max(0, int(channel * (1.0 - factor))) for channel in color[:3])


def _safe_rarity_int(value) -> int:
    """Safely convert rarity to int."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return 6 if str(value).upper() == "E" else 0


def _wrap_words(text: str, font: pygame.font.Font, max_width: int) -> List[str]:
    """Wrap text to fit within max_width."""
    words = (text or "").split()
    if not words:
        return ["-"]

    lines: List[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _current_turn(game, player: Player) -> int:
    """Get current turn number."""
    return max(1, int(max(getattr(game, "turn", 0), getattr(player, "turns_played", 0), 1)))


def _current_rarity_weight(rarity_id: str, turn: int) -> float:
    """Get rarity weight for current turn."""
    weight = 0.0
    for min_turn, step_weight in RARITY_WEIGHT.get(rarity_id, [(1, 0.0)]):
        if turn >= min_turn:
            weight = step_weight
    return weight


class ShopCard:
    """Represents a card in the shop with animation state."""
    
    def __init__(self, card: Card, index: int, rect: pygame.Rect):
        self.card = card
        self.index = index
        self.rect = rect
        self.draw_rect = rect.copy()
        self.bought = False
        self.hovered = False
        self.anim_t = 0.0
        self.buy_flash = 0

    def update(self, dt: int, mouse_pos):
        """Update animation state."""
        self.hovered = self.rect.collidepoint(mouse_pos) and not self.bought
        target = 1.0 if self.hovered else 0.0
        self.anim_t += (target - self.anim_t) * min(1.0, dt * 0.012)
        if self.buy_flash > 0:
            self.buy_flash = max(0, self.buy_flash - dt)

    def draw(self, surf: pygame.Surface, fonts: dict, player: Player,
             timer: float, fade_alpha: int, flip_value: float = 0.0,
             card_front_img: Optional[pygame.Surface] = None,
             card_back_img: Optional[pygame.Surface] = None,
             renderer: Optional[CyberRenderer] = None) -> pygame.Rect:
        """Draw shop card with hex flip animation ONLY.
        
        NO RECTANGLES - Only hex card surfaces with flip animation.
        
        Args:
            surf: Surface to draw on
            fonts: Font dictionary
            player: Current player
            timer: Animation timer
            fade_alpha: Fade alpha value
            flip_value: Flip animation value (0.0 = front, 1.0 = back)
            card_front_img: Front card hex image (REQUIRED)
            card_back_img: Back card hex image (REQUIRED)
            renderer: Optional renderer (NOT USED - hex only)
        
        Returns:
            Draw rectangle
        """
        # Calculate vertical offset for hover animation
        y_off = int(-15 * self.anim_t)
        draw_rect = self.rect.move(0, y_off)
        self.draw_rect = draw_rect

        # CRITICAL: If no hex images provided, cannot draw
        if card_front_img is None or card_back_img is None:
            # Emergency fallback: draw a warning
            error_font = fonts.get("xs", pygame.font.SysFont("consolas", 12))
            error_text = error_font.render("NO HEX ASSETS", True, (255, 0, 0))
            surf.blit(error_text, (draw_rect.x, draw_rect.y))
            return draw_rect

        # Calculate flip scale using cosine for smooth 3D effect
        # Full 180-degree rotation feel
        scale_x = abs(math.cos(flip_value * math.pi))
        
        # Determine which side to show (flip at midpoint)
        show_back = flip_value > 0.5
        
        # Select the appropriate hex surface
        if show_back:
            card_surf = card_back_img
        else:
            card_surf = card_front_img
        
        # Get original dimensions
        original_width = card_surf.get_width()
        original_height = card_surf.get_height()
        
        # Calculate scaled width (minimum 1 to avoid zero-width)
        scaled_width = max(1, int(original_width * scale_x))
        
        # Apply horizontal scaling for flip effect
        scaled_surf = pygame.transform.scale(card_surf, (scaled_width, original_height))
        
        # Calculate center position to keep card centered during flip
        center_x = draw_rect.centerx
        center_y = draw_rect.centery
        
        # Position scaled surface at center
        scaled_x = center_x - scaled_width // 2
        scaled_y = center_y - original_height // 2
        
        # Apply fade alpha if needed
        if fade_alpha < 255:
            scaled_surf = scaled_surf.copy()
            scaled_surf.set_alpha(fade_alpha)
        
        # Blit the hex card surface (NO RECTANGLES!)
        surf.blit(scaled_surf, (scaled_x, scaled_y))

        return draw_rect


def draw_hand_card(surf: pygame.Surface, card: Card, rect: pygame.Rect, fonts: dict, hovered: bool):
    """Draw a card in the hand buffer."""
    rarity_color = NEON["rarity_cols"].get(str(card.rarity), NEON["muted"])
    dom = card.dominant_group()
    group_color = GROUP_COLORS.get(dom, NEON["muted"])
    base = (22, 28, 46) if not hovered else (36, 44, 72)

    _round_rect(surf, base, rect, 8)
    _round_rect(surf, rarity_color if hovered else NEON["line"], rect, 8, 1)
    pygame.draw.rect(surf, rarity_color, (rect.x + 8, rect.y, rect.width - 16, 3), border_radius=2)
    pygame.draw.circle(surf, group_color, (rect.x + 12, rect.y + 16), 4)

    name = card.name if len(card.name) <= 20 else card.name[:18] + ".."
    name_text = fonts["xs_bold"].render(name, True, NEON["white"])
    surf.blit(name_text, (rect.x + 20, rect.y + 8))

    pwr_text = fonts["xs"].render(f"PWR {card.total_power()}  |  {card.rarity}", True, group_color)
    surf.blit(pwr_text, (rect.x + 8, rect.y + 28))

    desc = get_passive_desc(card.name, card.passive_type)
    desc_text = fonts["xs"].render(desc[:28], True, NEON["muted"])
    surf.blit(desc_text, (rect.x + 8, rect.y + 46))


class ShopScene(Scene):
    """Shop scene for card purchasing and board management.
    
    Refactored from ShopScreen to use Scene architecture.
    """
    
    def __init__(self, core_game_state: CoreGameState, 
                 action_system: Optional['ActionSystem'] = None,
                 animation_system: Optional['AnimationSystem'] = None,
                 asset_loader: 'AssetLoader' = None,
                 renderer: Optional[CyberRenderer] = None, 
                 fonts: Optional[dict] = None):
        """Initialize shop scene.
        
        Args:
            core_game_state: SAVEABLE state that persists across scenes
            action_system: Optional ActionSystem for executing actions
            animation_system: Optional AnimationSystem for animations
            asset_loader: REQUIRED AssetLoader for card asset management
            renderer: Optional CyberRenderer instance
            fonts: Optional font dictionary
        """
        super().__init__(core_game_state)
        
        # Validate required asset_loader parameter
        if asset_loader is None:
            raise ValueError("asset_loader is required for ShopScene")
        
        # Core systems
        self.action_system = action_system
        self.animation_system = animation_system
        self.asset_loader = asset_loader
        
        # Screen dimensions (will be set in draw when we have access to screen)
        self.W = 1600
        self.H = 960
        
        # Renderer and fonts
        self.renderer = renderer
        if fonts is not None:
            self.fonts = fonts
        elif self.renderer is not None and getattr(self.renderer, "fonts", None):
            self.fonts = self.renderer.fonts
        else:
            self._init_fonts()
        
        # Create renderer if not provided
        if self.renderer is None:
            self.renderer = CyberRenderer(self.fonts)
        else:
            self.renderer.set_fonts(self.fonts)

    def _init_fonts(self):
        """Initialize pygame fonts."""
        def f(name, size, bold=False):
            try:
                return pygame.font.SysFont(name, size, bold=bold)
            except Exception:
                return pygame.font.SysFont("consolas", size, bold=bold)

        self.fonts = {
            "title": f("bahnschrift", 30, bold=True),
            "lg": f("consolas", 28, bold=True),
            "md": f("consolas", 16),
            "md_bold": f("consolas", 16, bold=True),
            "sm": f("consolas", 14),
            "sm_bold": f("consolas", 14, bold=True),
            "xs": f("consolas", 12),
            "xs_bold": f("consolas", 12, bold=True),
            "icon": f("segoeuisymbol", 20, bold=True),
        }

    def on_enter(self) -> None:
        """Called when scene becomes active. Create fresh UIState."""
        # Create fresh THROWAWAY state
        self.ui_state = UIState()
        
        # Initialize shop-specific UI state
        self.ui_state.time = 0.0
        self.ui_state.fade_alpha = 0
        self.ui_state.hover_refresh = False
        self.ui_state.hover_done = False
        self.ui_state.hovered_market_card = None
        self.ui_state.hovered_card_idx = None
        self.ui_state.particles = []
        self.ui_state.shop_cards = []
        self.ui_state.card_flip_states = []
        
        # Build layout
        self._build_layout()
        
        # Preload visible card assets using AssetLoader
        visible_cards = []
        player = self.core_game_state.current_player
        
        # Collect market window cards
        market = self.core_game_state.game.market if hasattr(self.core_game_state.game, 'market') else None
        if market and hasattr(market, '_player_windows'):
            window = market._player_windows.get(player.pid, [])
            visible_cards.extend([c.name for c in window if c])
        
        # Collect player board cards
        if player and hasattr(player, 'board'):
            board_cards = player.board.alive_cards() if hasattr(player.board, 'alive_cards') else []
            visible_cards.extend([c.name for c in board_cards if c])
        
        # Collect player hand cards
        if player and hasattr(player, 'hand'):
            visible_cards.extend([c.name for c in player.hand if c])
        
        # Deduplicate and preload
        if visible_cards:
            self.asset_loader.preload(list(set(visible_cards)))
        
        # Initialize flip states for each card (0.0 = front, 1.0 = back)
        if market and hasattr(market, '_player_windows'):
            window = market._player_windows.get(player.pid, [])
            self.ui_state.card_flip_states = [0.0] * len(window)
        else:
            self.ui_state.card_flip_states = []

    def on_exit(self) -> None:
        """Called when scene is deactivated. Discard UIState."""
        # Apply interest to current player after shop closes (T1.12)
        player = self.core_game_state.current_player
        player.apply_interest()
        
        # Explicitly discard THROWAWAY state
        self.ui_state = None

    def _build_layout(self):
        """Build shop card layout."""
        player = self.core_game_state.current_player
        
        # Get player's market window
        market = self.core_game_state.game.market if hasattr(self.core_game_state.game, 'market') else None
        if market and hasattr(market, '_player_windows'):
            window = market._player_windows.get(player.pid, [])
        else:
            window = []
        
        total_w = len(window) * CARD_W + max(0, len(window) - 1) * CARD_GAP
        start_x = max(24, (self.W - total_w) // 2)
        start_y = 168

        self.ui_state.shop_cards = []
        for idx, card in enumerate(window):
            rect = pygame.Rect(start_x + idx * (CARD_W + CARD_GAP), start_y, CARD_W, CARD_H)
            self.ui_state.shop_cards.append(ShopCard(card, idx, rect))

        # Sidebar: Always align to right edge of screen (dynamic screen width)
        self.sidebar_rect = pygame.Rect(self.W - SIDEBAR_W, 70, SIDEBAR_W, self.H - 70 - FOOTER_H)
        
        # Buttons: Center horizontally
        self.btn_refresh = pygame.Rect(self.W // 2 - 210, self.H - 56, 185, 38)
        self.btn_done = pygame.Rect(self.W // 2 + 25, self.H - 56, 185, 38)

    def handle_input(self, input_state: InputState) -> None:
        """Process input intents for shop scene.
        
        Args:
            input_state: Intent-based input abstraction (not raw events)
        
        Requirements:
        - T2.2: Fast mode toggle (F key) - global across all scenes
        - T2.3a: Player switching (1-8 keys) - global across all scenes
        """
        # Update hover states
        self._update_hover(input_state.mouse_pos)
        
        # ============================================================================
        # GLOBAL INPUT HANDLING (works in all scenes)
        # ============================================================================
        
        # Toggle fast mode on F key (T2.2) - global across all scenes
        if input_state.is_fast_mode_toggled():
            self.core_game_state.fast_mode = not self.core_game_state.fast_mode
            print(f"✓ Fast mode {'enabled' if self.core_game_state.fast_mode else 'disabled'}")
            return
        
        # Player switching via 1-8 keys (T2.3a) - global across all scenes
        # NOTE: This takes priority over number keys for buying cards
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
            else:
                print(f"✗ Invalid player switch request: index {player_switch_request} "
                      f"(only {num_players} players exist)")
            return
        
        # ============================================================================
        # SHOP-SPECIFIC INPUT HANDLING
        # ============================================================================
        
        # Handle keyboard shortcuts
        if input_state.was_key_pressed_this_frame(pygame.K_RETURN) or input_state.was_key_pressed_this_frame(pygame.K_ESCAPE):
            # T1.10: Transition to combat (not game_loop)
            self.scene_manager.request_transition("combat")
            return
        
        if input_state.was_key_pressed_this_frame(pygame.K_SPACE) or input_state.was_key_pressed_this_frame(pygame.K_r):
            self._request_refresh()
            return
        
        # Handle number keys for buying (1-5)
        # NOTE: These are now handled AFTER player switching check above
        for key_code in range(pygame.K_1, pygame.K_6):
            if input_state.was_key_pressed_this_frame(key_code):
                self._try_buy(key_code - pygame.K_1)
                return
        
        # Handle mouse clicks
        if input_state.mouse_clicked:
            self._handle_click(input_state.mouse_pos)

    def _update_hover(self, mouse_pos):
        """Update hover states based on mouse position."""
        self.ui_state.hover_refresh = self.btn_refresh.collidepoint(mouse_pos)
        self.ui_state.hover_done = self.btn_done.collidepoint(mouse_pos)

    def _handle_click(self, pos):
        """Handle mouse click at position."""
        # Check shop cards
        for shop_card in self.ui_state.shop_cards:
            if shop_card.draw_rect.collidepoint(pos) and not shop_card.bought:
                self._try_buy(shop_card.index)
                return
        
        # Check buttons
        if self.btn_refresh.collidepoint(pos):
            self._request_refresh()
        elif self.btn_done.collidepoint(pos):
            # T1.10: Transition to combat (not game_loop)
            self.scene_manager.request_transition("combat")

    def _request_refresh(self):
        """Request market refresh."""
        player = self.core_game_state.current_player
        if player.gold < MARKET_REFRESH_COST:
            self.ui_state.set_message(
                f"Refresh locked: need {MARKET_REFRESH_COST}G, have {player.gold}G"
            )
            return
        
        # TODO: Use RefreshMarketAction when implemented
        # For now, directly modify state (will be replaced with Action)
        player.gold -= MARKET_REFRESH_COST
        if hasattr(self.core_game_state.game, 'market'):
            market = self.core_game_state.game.market
            market._return_window(player.pid)
            market.deal_market_window(player, n=5)
            self._build_layout()  # Rebuild layout with new cards
            self.ui_state.set_message(f"Market refreshed for {MARKET_REFRESH_COST}G")

    def _try_buy(self, idx: int):
        """Try to buy card at index using BuyCardAction."""
        if idx >= len(self.ui_state.shop_cards):
            return

        shop_card = self.ui_state.shop_cards[idx]
        if shop_card.bought:
            return

        player = self.core_game_state.current_player
        card = shop_card.card
        cost = CARD_COSTS.get(str(card.rarity), 99)
        
        if player.gold < cost:
            self.ui_state.set_message(f"Insufficient gold: {cost}G required")
            return

        # Use BuyCardAction if action_system is available
        if self.action_system is not None:
            from core.action_system import BuyCardAction
            
            action = BuyCardAction(shop_idx=idx, cost=cost)
            success = self.action_system.execute(
                action, 
                self.core_game_state, 
                self.animation_system
            )
            
            if success:
                shop_card.bought = True
                shop_card.buy_flash = 320
                self._spawn_particles(shop_card.rect)
                
                # Check if card was dropped due to hand overflow
                if action.dropped_card:
                    self.ui_state.set_message(
                        f"Purchased {card.name} ({cost}G). Buffer full: dropped {action.dropped_card.name}."
                    )
                else:
                    self.ui_state.set_message(f"Purchased {card.name} for {cost}G.")
            else:
                self.ui_state.set_message(f"Failed to purchase {card.name}")
        else:
            # Fallback: Direct state modification (for backward compatibility)
            player.gold -= cost
            player.stats["gold_spent"] += cost

            cloned = card.clone()
            player.hand.append(cloned)
            player.copies[card.name] = player.copies.get(card.name, 0) + 1
            player.cards_bought_this_turn += 1
            player.stats["cards_bought_this_turn"] = (
                player.stats.get("cards_bought_this_turn", 0) + 1
            )
            player._window_bought.append(card.name)

            dropped_name = None
            if len(player.hand) > 6:
                dropped = player.hand.pop(0)
                dropped_name = dropped.name
                if player.copies.get(dropped.name, 0) > 0:
                    player.copies[dropped.name] -= 1
                market = getattr(self.core_game_state.game, "market", None)
                if market is not None and hasattr(market, "pool_copies"):
                    market.pool_copies[dropped.name] = market.pool_copies.get(dropped.name, 0) + 1
                player.stats["cards_dropped"] = player.stats.get("cards_dropped", 0) + 1

            shop_card.bought = True
            shop_card.buy_flash = 320
            self._spawn_particles(shop_card.rect)

            if dropped_name:
                self.ui_state.set_message(f"Purchased {card.name} ({cost}G). Buffer full: dropped {dropped_name}.")
            else:
                self.ui_state.set_message(f"Purchased {card.name} for {cost}G.")

    def _spawn_particles(self, rect: pygame.Rect):
        """Spawn particle effects at rect."""
        import random

        for _ in range(14):
            angle = random.uniform(0.0, 2.0 * math.pi)
            speed = random.uniform(1.5, 4.0)
            life = random.randint(300, 700)
            self.ui_state.particles.append({
                "x": rect.centerx,
                "y": rect.centery,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - 1.0,
                "life": life,
                "max": life,
                "r": random.randint(2, 5),
                "col": random.choice([NEON["gold"], NEON["cyan"], NEON["pink"], NEON["ok"]]),
            })

    def update(self, dt: float) -> None:
        """Update scene logic with delta time.
        
        Args:
            dt: Delta time in milliseconds since last frame
        """
        # Update time for animations
        self.ui_state.time += dt / 1000.0
        self.ui_state.fade_alpha = min(255, self.ui_state.fade_alpha + int(dt * 1.6))

        # Update shop cards
        mouse = pygame.mouse.get_pos()
        
        # Track which card is hovered
        self.ui_state.hovered_card_idx = None
        for idx, shop_card in enumerate(self.ui_state.shop_cards):
            shop_card.update(int(dt), mouse)
            if shop_card.hovered:
                self.ui_state.hovered_card_idx = idx
        
        # Update card flip animations (smooth interpolation)
        flip_speed = 0.1  # Flip speed per frame
        for idx in range(len(self.ui_state.card_flip_states)):
            if idx == self.ui_state.hovered_card_idx:
                # Flip to back (1.0) when hovered
                target = 1.0
            else:
                # Flip to front (0.0) when not hovered
                target = 0.0
            
            # Smooth interpolation
            current = self.ui_state.card_flip_states[idx]
            self.ui_state.card_flip_states[idx] += (target - current) * flip_speed

        # Update particles
        alive_particles = []
        for particle in self.ui_state.particles:
            particle["x"] += particle["vx"]
            particle["y"] += particle["vy"]
            particle["vy"] += 0.08
            particle["life"] -= dt
            if particle["life"] > 0:
                alive_particles.append(particle)
        self.ui_state.particles = alive_particles

        # Update message timer
        self.ui_state.update_message_timer(dt)

    def draw(self, screen: pygame.Surface) -> None:
        """Render shop scene to screen.
        
        Args:
            screen: Pygame surface to draw on
        """
        # Update screen dimensions and rebuild layout if screen size changed
        new_w, new_h = screen.get_size()
        if new_w != self.W or new_h != self.H:
            self.W, self.H = new_w, new_h
            self._build_layout()  # Rebuild layout with new screen dimensions
        
        # Draw all shop elements
        screen.fill(NEON["bg"])
        self.renderer.draw_vfx_base(screen)
        self.ui_state.time = self.renderer.timer
        
        self._draw_economy_dash(screen)
        self._draw_market_grid(screen)
        self._draw_compare_sidebar(screen)
        self._draw_footer(screen)
        self._draw_particles(screen)

    # ========== Drawing Methods ==========

    def _draw_economy_dash(self, surf: pygame.Surface):
        """Draw economy dashboard (gold, turn)."""
        player = self.core_game_state.current_player
        gold = self.fonts["lg"].render(f"{player.gold} CR", True, NEON["gold"])
        surf.blit(gold, (self.W - gold.get_width() - 40, 30))

        turn = self.fonts["sm"].render(
            f"TURN {_current_turn(self.core_game_state.game, player)}",
            True,
            NEON["muted"],
        )
        surf.blit(turn, (40, 38))

    def _draw_market_grid(self, surf: pygame.Surface):
        """Draw market cards grid with flip animations."""
        mx, my = pygame.mouse.get_pos()
        hovered_card = None
        
        label = self.fonts["title"].render("MARKET", True, NEON["white"])
        surf.blit(label, (self.W // 2 - label.get_width() // 2, 120))
        
        sub = self.fonts["sm"].render("Hover to inspect passive data. Press 1-5 to buy.", True, NEON["muted"])
        surf.blit(sub, (self.W // 2 - sub.get_width() // 2, 154))

        player = self.core_game_state.current_player
        for idx, shop_card in enumerate(self.ui_state.shop_cards):
            # Get flip value for this card
            flip_value = self.ui_state.card_flip_states[idx] if idx < len(self.ui_state.card_flip_states) else 0.0
            
            # Get card faces from AssetLoader
            faces = self.asset_loader.get(shop_card.card.name)
            
            draw_rect = shop_card.draw(
                surf,
                self.fonts,
                player,
                self.renderer.timer if self.renderer is not None else self.ui_state.time,
                self.ui_state.fade_alpha,
                flip_value=flip_value,
                card_front_img=faces.front,
                card_back_img=faces.back,
                renderer=self.renderer,
            )
            if draw_rect.collidepoint(mx, my) and not shop_card.bought:
                hovered_card = shop_card.card

        self.ui_state.hovered_market_card = hovered_card

        self.renderer.draw_priority_popup(
            surf,
            hovered_card,
            mx,
            my,
        )

    def _draw_synergy_sidebar(self, surf: pygame.Surface):
        """Draw synergy sidebar showing board stats."""
        panel = pygame.Surface((self.sidebar_rect.width, self.sidebar_rect.height), pygame.SRCALPHA)
        panel.fill(NEON["panel"])
        surf.blit(panel, self.sidebar_rect.topleft)
        pygame.draw.line(
            surf,
            NEON["cyan"],
            self.sidebar_rect.topleft,
            (self.sidebar_rect.left, self.sidebar_rect.bottom),
            2,
        )

        x = self.sidebar_rect.x + 16
        y = self.sidebar_rect.y + 10

        header = self.fonts["md_bold"].render("SYNERGY_OS", True, NEON["pink"])
        surf.blit(header, (x, y))
        y += 30

        player = self.core_game_state.current_player
        counts = Counter()
        for board_card in player.board.grid.values():
            for stat_name, value in board_card.stats.items():
                if value <= 0 or str(stat_name).startswith("_"):
                    continue
                group = STAT_TO_GROUP.get(stat_name)
                if group:
                    counts[group] += 1

        if not counts:
            empty = self.fonts["xs"].render("Board is idle. No synergy traces yet.", True, NEON["muted"])
            surf.blit(empty, (x, y))
            y += 30
        else:
            for group, count in counts.most_common():
                color = GROUP_COLORS.get(group, NEON["muted"])
                label = self.fonts["xs_bold"].render(group, True, NEON["white"])
                surf.blit(label, (x, y))
                pygame.draw.rect(surf, (20, 26, 45), (x, y + 18, 190, 7), border_radius=4)
                fill_w = min(190, count * 18)
                pygame.draw.rect(surf, color, (x, y + 18, fill_w, 7), border_radius=4)
                count_text = self.fonts["xs"].render(str(count), True, color)
                surf.blit(count_text, (x + 200, y + 10))
                y += 34

        y += 14
        hand_header = self.fonts["md_bold"].render(f"HAND_BUFFER [{len(player.hand)}/6]", True, NEON["cyan"])
        surf.blit(hand_header, (x, y))
        y += 28

        mouse = pygame.mouse.get_pos()
        if not player.hand:
            empty = self.fonts["xs"].render("- buffer empty -", True, NEON["muted"])
            surf.blit(empty, (x, y))
            return

        card_h = 72
        for hand_card in player.hand:
            rect = pygame.Rect(x, y, self.sidebar_rect.width - 32, card_h)
            if rect.bottom > self.sidebar_rect.bottom - 16:
                break
            draw_hand_card(surf, hand_card, rect, self.fonts, rect.collidepoint(mouse))
            y += card_h + 8

    def _draw_compare_sidebar(self, surf: pygame.Surface):
        """Draw hover compare mode sidebar.
        
        When hovering over a market card, shows MATCH/CLASH with board cards.
        Otherwise shows synergy sidebar.
        """
        hovered = self.ui_state.hovered_market_card
        if hovered is None:
            self._draw_synergy_sidebar(surf)
            return

        # Get hovered card's groups
        hovered_groups = set()
        for stat_name, value in getattr(hovered, "stats", {}).items():
            if value > 0 and not str(stat_name).startswith("_"):
                g = STAT_TO_GROUP.get(stat_name)
                if g:
                    hovered_groups.add(g)

        panel = pygame.Surface(
            (self.sidebar_rect.width, self.sidebar_rect.height), pygame.SRCALPHA
        )
        panel.fill((12, 15, 28, 200))
        surf.blit(panel, self.sidebar_rect.topleft)
        pygame.draw.line(
            surf, NEON["cyan"],
            self.sidebar_rect.topleft,
            (self.sidebar_rect.left, self.sidebar_rect.bottom), 2,
        )

        x = self.sidebar_rect.x + 14
        y = self.sidebar_rect.y + 10

        # Header
        header = self.fonts["md_bold"].render("COMPARE_MODE", True, NEON["cyan"])
        surf.blit(header, (x, y))
        y += 24

        # Hovered card name
        sub = self.fonts["xs_bold"].render(
            hovered.name.upper()[:22], True, NEON["gold"]
        )
        surf.blit(sub, (x, y))
        y += 18

        # Hovered groups
        for grp in sorted(hovered_groups):
            col = GROUP_COLORS.get(grp, NEON["muted"])
            gi = self.fonts["xs"].render(f"  ● {grp}", True, col)
            surf.blit(gi, (x, y))
            y += 14
        y += 8

        # Legend
        surf.blit(
            self.fonts["xs_bold"].render("■ MATCH", True, NEON["ok"]), (x, y)
        )
        surf.blit(
            self.fonts["xs_bold"].render("■ CLASH", True, NEON["danger"]), (x + 90, y)
        )
        y += 20
        pygame.draw.line(
            surf, NEON["line"],
            (x, y), (self.sidebar_rect.right - 14, y), 1
        )
        y += 8

        # Mini board
        self._draw_mini_board(surf, x, y, hovered_groups)

    def _draw_mini_board(self, surf: pygame.Surface, start_x: int, start_y: int, hovered_groups: set):
        """Draw mini board with MATCH/CLASH highlighting."""
        MINI_R = 20
        MAX_W = self.sidebar_rect.width - 28
        player = self.core_game_state.current_player
        board = player.board
        board_cards = list(board.grid.values())
        
        if not board_cards:
            empty = self.fonts["xs"].render("Board empty.", True, NEON["muted"])
            surf.blit(empty, (start_x, start_y))
            return

        cols = max(1, MAX_W // (MINI_R * 2 + 8))
        row_h = MINI_R * 2 + 12
        font_xs = self.fonts["xs"]

        for idx, card in enumerate(board_cards):
            col = idx % cols
            row = idx // cols
            cx = start_x + col * (MINI_R * 2 + 8) + MINI_R
            cy = start_y + row * row_h + MINI_R

            # Check if exceeds sidebar bottom
            if cy + MINI_R > self.sidebar_rect.bottom - 10:
                break

            # Check if card matches hovered groups
            card_groups = set()
            for sn, sv in getattr(card, "stats", {}).items():
                if sv > 0 and not str(sn).startswith("_"):
                    g = STAT_TO_GROUP.get(sn)
                    if g:
                        card_groups.add(g)

            is_match = bool(card_groups & hovered_groups)

            # Draw hex
            pts_hex = [
                (
                    int(cx + MINI_R * math.cos(math.radians(60 * i))),
                    int(cy + MINI_R * math.sin(math.radians(60 * i))),
                )
                for i in range(6)
            ]
            dom = card.dominant_group()
            gc = GROUP_COLORS.get(dom, NEON["muted"])
            fill = tuple(max(0, c // 4) for c in gc)
            pygame.draw.polygon(surf, fill, pts_hex)

            if is_match:
                pygame.draw.polygon(surf, NEON["ok"], pts_hex, 2)
            else:
                pygame.draw.polygon(surf, NEON["muted"], pts_hex, 1)

            # Draw edges with MATCH/CLASH colors
            edges = getattr(card, "rotated_edges", lambda: [])()
            for ei, (stat_name, value) in enumerate(edges[:6]):
                if value <= 0 or str(stat_name).startswith("_"):
                    continue
                eg = STAT_TO_GROUP.get(stat_name)
                if eg in hovered_groups:
                    ecol = GROUP_COLORS.get(eg, NEON["ok"])
                else:
                    ecol = (180, 60, 60)  # muted red = clash

                a1 = pts_hex[ei]
                b1 = pts_hex[(ei + 1) % 6]
                pygame.draw.line(surf, ecol, a1, b1, 2)

            # Card name
            name_short = card.name[:8].upper()
            ni = font_xs.render(name_short, True, NEON["white"] if is_match else NEON["muted"])
            nx = cx - ni.get_width() // 2
            ny = cy - ni.get_height() // 2
            surf.blit(ni, (nx, ny))

    def _draw_footer(self, surf: pygame.Surface):
        """Draw footer with buttons and messages."""
        footer = pygame.Surface((self.W, FOOTER_H), pygame.SRCALPHA)
        surf.blit(footer, (0, self.H - FOOTER_H))
        pygame.draw.line(surf, NEON["line"], (0, self.H - FOOTER_H), (self.W, self.H - FOOTER_H), 1)

        player = self.core_game_state.current_player
        self._draw_button(
            surf,
            self.btn_refresh,
            f"[SPACE] RE-ROLL ({MARKET_REFRESH_COST}G)",
            self.ui_state.hover_refresh,
            player.gold >= MARKET_REFRESH_COST,
            NEON["cyan"],
        )
        self._draw_button(
            surf,
            self.btn_done,
            "[ENTER] BATTLE",
            self.ui_state.hover_done,
            True,
            NEON["ok"],
        )

        if self.ui_state.message and self.ui_state.message_timer > 0:
            msg_text = self.fonts["xs"].render(self.ui_state.message, True, NEON["white"])
            surf.blit(msg_text, (24, self.H - 24))

        hint = self.fonts["xs"].render(
            "1-5 buy  |  SPACE reroll  |  ENTER battle  |  ESC exits shop",
            True,
            NEON["muted"],
        )
        surf.blit(hint, (self.W - hint.get_width() - 24, self.H - 24))

    def _draw_button(self, surf: pygame.Surface, rect: pygame.Rect, label: str, 
                     hovered: bool, enabled: bool, color):
        """Draw a button."""
        if not enabled:
            bg = (22, 24, 34)
            fg = NEON["muted"]
            border = NEON["line"]
        elif hovered:
            bg = _lerp_color((24, 28, 46), color, 0.25)
            fg = color
            border = color
        else:
            bg = (22, 26, 40)
            fg = color
            border = NEON["line"]

        _round_rect(surf, bg, rect, 8)
        _round_rect(surf, border, rect, 8, 2 if hovered else 1)
        text = self.fonts["sm_bold"].render(label, True, fg)
        surf.blit(
            text,
            (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2),
        )

    def _draw_particles(self, surf: pygame.Surface):
        """Draw particle effects."""
        for particle in self.ui_state.particles:
            alpha = int(255 * (particle["life"] / particle["max"]))
            radius = max(1, int(particle["r"] * particle["life"] / particle["max"]))
            sprite = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(sprite, (*particle["col"], max(0, min(255, alpha))), (radius, radius), radius)
            surf.blit(sprite, (int(particle["x"]) - radius, int(particle["y"]) - radius))
