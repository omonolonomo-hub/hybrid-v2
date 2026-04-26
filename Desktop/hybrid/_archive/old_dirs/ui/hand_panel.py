"""
Hand Panel - Horizontal Bottom Bar for Combat Scene

Displays 6 hex-shaped card slots horizontally at bottom of screen
with detailed info panel on the right for selected card.

Visual Design:
- 175px height bottom bar
- 6 hex slots (76x76px each) with 88px column width, 8px gap
- 320px detail panel on right side
- Header row with labels and hints
- Hex slots with rarity bars, passive dots, group colors, rotation badges
- Selection glow effect for selected card

Architecture:
- Reads from CoreGameState (current player's hand)
- Reads from UIState (selected_hand_idx)
- Provides click detection via get_card_at_position()
"""

from typing import Optional, Tuple, List
import pygame


class HandPanel:
    """Hand panel renderer for combat scene.
    
    Displays 6 hex-shaped card slots horizontally at bottom of screen
    with detailed info panel on the right.
    
    Requirements:
    - T3.2: Hand panel with 175px height, 6 hex slots, 320px detail panel
    - Modern autochess UX pattern (TFT/Underlords style)
    """
    
    # Layout constants
    PANEL_HEIGHT = 175          # Total panel height
    MAX_SLOTS = 6               # Maximum card slots
    HEX_SIZE = 110              # Hex width and height (increased from 76)
    SLOT_WIDTH = 125            # Slot column width (increased from 88)
    SLOT_GAP = 10               # Gap between slots (increased from 8)
    SLOT_PADDING = 20           # Left padding for first slot (increased from 16)
    DETAIL_PANEL_WIDTH = 320    # Right detail panel width
    HEADER_HEIGHT = 26          # Header row height
    
    # Color palette (matching combat_scene_alternative.py)
    C_BG = (10, 13, 26, 247)
    C_BORDER = (0, 242, 255, 64)
    C_CYAN = (0, 242, 255)
    C_GOLD = (255, 204, 0)
    C_DIM = (100, 110, 135)
    C_TEXT = (230, 235, 255)
    C_TEXT_BRIGHT = (240, 245, 255)
    
    # Group colors
    GROUP_COLORS = {
        'MIND': (70, 150, 255),
        'EXISTENCE': (255, 110, 80),
        'CONNECTION': (60, 235, 150),
    }
    
    # Rarity colors
    RARITY_COLORS = {
        'S': (255, 80, 120),
        'A': (255, 204, 0),
        'B': (0, 242, 255),
        'C': (145, 155, 185),
    }
    
    def __init__(self, core_game_state, ui_state, asset_loader=None):
        """Initialize HandPanel with required state references.
        
        Args:
            core_game_state: Reference to CoreGameState for reading player hand
            ui_state: Reference to UIState for reading selected_hand_idx
            asset_loader: REQUIRED AssetLoader for card asset management
        
        Raises:
            ValueError: If asset_loader is None
        
        Requirements:
        - T3.2b-i: AssetLoader dependency injection (same pattern as ShopScene)
        """
        # Validate required asset_loader parameter (T3.2b-i)
        if asset_loader is None:
            raise ValueError("asset_loader is required for HandPanel")
        
        self.core_game_state = core_game_state
        self.ui_state = ui_state
        self.asset_loader = asset_loader
        
        # Slot rectangles for click detection (populated in draw())
        self._hand_slot_rects: List[pygame.Rect] = []
        
        # Initialize fonts (will be created in draw() if needed)
        self._fonts_initialized = False
        self._font_tiny = None
        self._font_small = None
        self._font_name = None
    
    def _init_fonts(self):
        """Initialize fonts for rendering.
        
        Creates fonts once and reuses them for performance.
        Falls back to default fonts if system fonts unavailable.
        """
        if self._fonts_initialized:
            return
        
        try:
            self._font_tiny = pygame.font.SysFont("consolas", 11)
            self._font_small = pygame.font.SysFont("consolas", 13)
            self._font_name = pygame.font.SysFont("consolas", 10)
        except Exception:
            # Fallback to default fonts
            self._font_tiny = pygame.font.Font(None, 16)
            self._font_small = pygame.font.Font(None, 18)
            self._font_name = pygame.font.Font(None, 15)
        
        self._fonts_initialized = True
    
    def preload(self) -> None:
        """Preload card assets for current player's hand.
        
        Extracts card names from player.hand and preloads them via AssetLoader.
        This should be called in CombatScene.on_enter() after HandPanel initialization.
        
        Requirements:
        - T3.2b-ii: Preload hand card assets (same pattern as ShopScene)
        """
        # Get current player's hand
        hand: list = []
        try:
            current_player = self.core_game_state.current_player
            if hasattr(current_player, 'hand') and current_player.hand:
                hand = list(current_player.hand)
        except (TypeError, AttributeError):
            pass
        
        # Extract card names
        card_names = []
        for card in hand:
            if hasattr(card, 'name'):
                card_names.append(card.name)
        
        # Preload via AssetLoader (deduplicates automatically)
        if card_names:
            self.asset_loader.preload(card_names)
            print(f"[HandPanel] Preloaded {len(card_names)} hand card assets")
    
    def draw(self, screen: pygame.Surface) -> None:
        """Draw hand panel with hex slots and detail panel.
        
        Renders:
        - Background with border
        - Header row with labels and hints
        - 6 hex-shaped card slots with visual features
        - Detail panel for selected card
        
        Args:
            screen: Pygame surface to draw on
        """
        # Initialize fonts if needed
        self._init_fonts()
        
        # ── Dimensions ────────────────────────────────────────────────────────
        screen_w = screen.get_width()
        screen_h = screen.get_height()
        panel_h = self.PANEL_HEIGHT  # 175
        panel_y = screen_h - panel_h
        
        # ── Background ────────────────────────────────────────────────────────
        bg = pygame.Surface((screen_w, panel_h), pygame.SRCALPHA)
        bg.fill(self.C_BG)
        screen.blit(bg, (0, panel_y))
        
        # Top border line (dim cyan)
        border_surf = pygame.Surface((screen_w, 1), pygame.SRCALPHA)
        border_surf.fill(self.C_BORDER)
        screen.blit(border_surf, (0, panel_y))
        
        # ── Hand data ─────────────────────────────────────────────────────────
        current_player = self.core_game_state.current_player
        hand: list = []
        try:
            if hasattr(current_player, 'hand') and current_player.hand:
                hand = list(current_player.hand)
        except (TypeError, AttributeError):
            pass
        
        turn = getattr(self.core_game_state, 'turn', 0)
        hand_count = len(hand)
        selected_idx = getattr(self.ui_state, 'selected_hand_idx', None)
        
        # ── Header row ────────────────────────────────────────────────────────
        hdr_y = panel_y + 5
        
        lbl = self._font_tiny.render("HAND BUFFER", True, (0, 180, 210))
        screen.blit(lbl, (self.SLOT_PADDING, hdr_y))
        
        meta_cx = screen_w // 2
        for i, txt in enumerate([f"CARDS {hand_count}/{self.MAX_SLOTS}",
                                  f"PLACED 0/1",
                                  f"TURN {turn}"]):
            s = self._font_tiny.render(txt, True, self.C_DIM)
            screen.blit(s, (meta_cx - 200 + i * 140, hdr_y))
        
        hint = self._font_tiny.render("[CLICK] select  ·  [R] rotate  ·  [ESC] cancel",
                                     True, (60, 70, 95))
        screen.blit(hint, (screen_w - self.DETAIL_PANEL_WIDTH - hint.get_width() - 16, hdr_y))
        
        # Separator under header
        sep_y = panel_y + self.HEADER_HEIGHT
        pygame.draw.line(screen, (40, 45, 65), (0, sep_y), (screen_w, sep_y), 1)
        
        # ── Cards row ─────────────────────────────────────────────────────────
        cards_h = panel_h - self.HEADER_HEIGHT - 2
        
        # Clear and rebuild slot rects
        self._hand_slot_rects = []
        
        for i in range(self.MAX_SLOTS):
            slot_x = self.SLOT_PADDING + i * (self.SLOT_WIDTH + self.SLOT_GAP)
            slot_cx = slot_x + self.SLOT_WIDTH // 2
            hex_x = slot_x + (self.SLOT_WIDTH - self.HEX_SIZE) // 2
            hex_y = sep_y + 2 + (cards_h - self.HEX_SIZE - 16) // 2  # leave 16px for badge
            
            pts = self._hex_points(hex_x, hex_y)
            self._hand_slot_rects.append(
                pygame.Rect(hex_x, hex_y, self.HEX_SIZE, self.HEX_SIZE)
            )
            
            has_card = i < len(hand)
            is_selected = has_card and (i == selected_idx)
            
            if not has_card:
                # Empty ghost slot
                ghost = pygame.Surface((self.HEX_SIZE, self.HEX_SIZE), pygame.SRCALPHA)
                local = [(p[0] - hex_x, p[1] - hex_y) for p in pts]
                pygame.draw.polygon(ghost, (20, 25, 45, 90), local)
                pygame.draw.polygon(ghost, (50, 60, 95, 60), local, 1)
                screen.blit(ghost, (hex_x, hex_y))
                continue
            
            card = hand[i]
            
            # --- Card properties (safe fallbacks) ---
            card_name = getattr(card, 'name', f'CARD {i+1}')
            rotation = getattr(card, 'rotation', 0)
            rarity = getattr(card, 'rarity', 'C').upper()
            
            # Use dominant_group() method instead of group/type attributes
            group_raw = card.dominant_group() if hasattr(card, 'dominant_group') else ''
            group_col = self.GROUP_COLORS.get(group_raw, (145, 155, 185))
            rarity_col = self.RARITY_COLORS.get(rarity, (145, 155, 185))
            
            # Use passive_type instead of passive
            has_passive = bool(getattr(card, 'passive_type', None))
            
            # Use total_power() method instead of sum(edges)
            try:
                pwr = card.total_power() if hasattr(card, 'total_power') else 0
            except (TypeError, AttributeError):
                pwr = getattr(card, 'power', 0)
            
            # --- Hex background surface (SRCALPHA for clean edges) ---
            hex_surf = pygame.Surface((self.HEX_SIZE, self.HEX_SIZE), pygame.SRCALPHA)
            local = [(p[0] - hex_x, p[1] - hex_y) for p in pts]
            pygame.draw.polygon(hex_surf, (18, 22, 42, 230), local)
            border_col = (0, 242, 255, 220) if is_selected else (50, 60, 95, 140)
            pygame.draw.polygon(hex_surf, border_col, local, 1)
            screen.blit(hex_surf, (hex_x, hex_y))
            
            # --- T3.2b-ii: Load and render card image from AssetLoader ---
            try:
                faces = self.asset_loader.get(card_name)
                
                # Use front face for hand display
                card_image = faces.front
                
                # Calculate target size for hex slot
                # HEX_SIZE=110 → scale card to fit nicely in hex
                target_w = int(self.HEX_SIZE * 1.0)  # Full hex width
                target_h = int(self.HEX_SIZE * 1.15)  # Slightly taller for card aspect ratio
                
                # Scale card image to fit hex slot
                scaled_image = pygame.transform.smoothscale(card_image, (target_w, target_h))
                
                # Center the image within the hex
                img_x = hex_x + (self.HEX_SIZE - target_w) // 2
                img_y = hex_y + (self.HEX_SIZE - target_h) // 2
                
                # Blit card image (will be clipped by hex mask if needed)
                screen.blit(scaled_image, (img_x, img_y))
                
                # If placeholder, add visual indicator (neon hex already handled by AssetLoader)
                if faces.is_placeholder:
                    # AssetLoader already provides neon hex placeholder
                    pass
                    
            except Exception as e:
                # Fallback: if asset loading fails, show error indicator
                err_surf = pygame.Surface((self.HEX_SIZE - 10, self.HEX_SIZE - 10), pygame.SRCALPHA)
                err_local = [(p[0] - hex_x - 5, p[1] - hex_y - 5) for p in pts]
                pygame.draw.polygon(err_surf, (80, 40, 40, 180), err_local)
                screen.blit(err_surf, (hex_x + 5, hex_y + 5))
                print(f"[HandPanel] Failed to load asset for {card_name}: {e}")
            
            # Glow ring for selected
            if is_selected:
                glow = pygame.Surface((self.HEX_SIZE + 20, self.HEX_SIZE + 20), pygame.SRCALPHA)
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
                                   (hex_x + self.HEX_SIZE - 10, hex_y + 14), 3)
            
            # Card name (split words across 2 lines)
            words = card_name.split()
            line1 = words[0] if words else card_name
            line2 = ' '.join(words[1:]) if len(words) > 1 else ''
            n1 = self._font_name.render(line1.upper(), True, self.C_TEXT)
            screen.blit(n1, (slot_cx - n1.get_width() // 2, hex_y + 22))
            if line2:
                n2 = self._font_name.render(line2.upper(), True, self.C_TEXT)
                screen.blit(n2, (slot_cx - n2.get_width() // 2, hex_y + 34))
            
            # Power label
            pwr_s = self._font_name.render(f"PWR {pwr}", True, group_col)
            screen.blit(pwr_s, (slot_cx - pwr_s.get_width() // 2, hex_y + 50))
            
            # Group dot (bottom-right)
            pygame.draw.circle(screen, group_col,
                               (hex_x + self.HEX_SIZE - 10, hex_y + self.HEX_SIZE - 12), 4)
            
            # Selection indicator (tiny bar above hex)
            if is_selected:
                pygame.draw.rect(screen, self.C_CYAN,
                                 (slot_cx - 2, hex_y - 7, 3, 5))
            
            # Rotation badge (below hex)
            rot_s = self._font_name.render(f"ROT {rotation}°", True, self.C_DIM)
            screen.blit(rot_s, (slot_cx - rot_s.get_width() // 2,
                                hex_y + self.HEX_SIZE + 3))
        
        # ── Divider line before detail panel ──────────────────────────────────
        div_x = screen_w - self.DETAIL_PANEL_WIDTH
        pygame.draw.line(screen, (0, 242, 255, 25),
                         (div_x, sep_y + 4), (div_x, panel_y + panel_h - 4), 1)
        
        # ── Selected card detail panel ─────────────────────────────────────────
        if selected_idx is not None and selected_idx < len(hand):
            self._draw_detail_panel(screen, hand[selected_idx], div_x, sep_y, panel_y, panel_h)
    
    def get_card_at_position(self, mouse_x: int, mouse_y: int) -> Optional[int]:
        """Get card index at mouse position.
        
        Checks if (mouse_x, mouse_y) falls inside any hex slot rect.
        Returns the card index if a slot with a card is clicked.
        
        Args:
            mouse_x: Mouse X coordinate
            mouse_y: Mouse Y coordinate
        
        Returns:
            Card index (0-5) if clicked on a card slot, None otherwise
        """
        # Get current player's hand
        hand: list = []
        try:
            cp = self.core_game_state.current_player
            if hasattr(cp, 'hand') and cp.hand:
                hand = list(cp.hand)
        except (TypeError, AttributeError):
            pass
        
        # Check each slot rect for collision
        for i, rect in enumerate(self._hand_slot_rects):
            if i >= len(hand):
                break  # Empty ghost slot - no card
            if rect.collidepoint(mouse_x, mouse_y):
                return i  # Return card index
        
        return None
    
    def _hex_points(self, ox: int, oy: int) -> List[Tuple[int, int]]:
        """Return 6-point polygon for a pointy-top hex at offset (ox, oy).
        
        Args:
            ox: X offset for hex center
            oy: Y offset for hex center
        
        Returns:
            List of 6 (x, y) tuples representing hex corners
        """
        w = h = self.HEX_SIZE
        hw, hh = w // 2, h // 2
        q4h = h // 4
        return [
            (ox + hw, oy),  # top
            (ox + w, oy + q4h),  # top-right
            (ox + w, oy + h - q4h),  # bot-right
            (ox + hw, oy + h),  # bottom
            (ox, oy + h - q4h),  # bot-left
            (ox, oy + q4h),  # top-left
        ]
    
    def _draw_detail_panel(self, screen: pygame.Surface, card, div_x: int, 
                          sep_y: int, panel_y: int, panel_h: int) -> None:
        """Draw detail panel for selected card.
        
        Shows card details including pending rotation from UIState.
        
        Args:
            screen: Pygame surface to draw on
            card: Selected card object
            div_x: X position of divider line
            sep_y: Y position of separator
            panel_y: Y position of panel top
            panel_h: Panel height
        
        Requirements:
        - T3.3d: Show pending_rotation in detail panel
        """
        dx = div_x + 12
        dy = sep_y + 8
        
        # "SELECTED" label
        ttl = self._font_tiny.render("SELECTED", True, (0, 130, 155))
        screen.blit(ttl, (dx, dy))
        dy += 13
        pygame.draw.line(screen, (0, 60, 80),
                         (dx, dy), (dx + self.DETAIL_PANEL_WIDTH - 24, dy), 1)
        dy += 5
        
        # Card name
        disp = getattr(card, 'name', 'Unknown')
        ns = self._font_small.render(disp, True, self.C_TEXT_BRIGHT)
        screen.blit(ns, (dx, dy))
        dy += 18
        
        # Helper: key/value row
        def kv_row(key, val, col=self.C_TEXT_BRIGHT):
            nonlocal dy
            ks = self._font_tiny.render(key, True, self.C_DIM)
            vs = self._font_tiny.render(str(val), True, col)
            screen.blit(ks, (dx, dy))
            screen.blit(vs, (dx + 70, dy))
            dy += 13
        
        rarity = getattr(card, 'rarity', 'C').upper()
        rarity_col = self.RARITY_COLORS.get(rarity, (145, 155, 185))
        kv_row("RARITY", rarity, rarity_col)
        
        # Use dominant_group() method instead of group/type attributes
        group_raw = card.dominant_group() if hasattr(card, 'dominant_group') else 'N/A'
        group_col = self.GROUP_COLORS.get(group_raw, (145, 155, 185))
        kv_row("GROUP", group_raw, group_col)
        
        # Use total_power() method instead of sum(edges)
        try:
            pwr = card.total_power() if hasattr(card, 'total_power') else 0
        except (TypeError, AttributeError):
            pwr = getattr(card, 'power', 0)
        kv_row("POWER", pwr, self.C_GOLD)
        
        # T3.3d: Show pending_rotation from UIState (current → next)
        pending_rotation = getattr(self.ui_state, 'pending_rotation', 0)
        current_rot = pending_rotation * 60  # Convert 0-5 to degrees
        next_rot = ((pending_rotation + 1) % 6) * 60
        kv_row("ROTATION", f"{current_rot}°  →  {next_rot}°")
        
        # Passive ability (word-wrapped)
        # Use passive_type instead of passive attribute
        passive_txt = getattr(card, 'passive_type', None)
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
            
            pygame.draw.rect(screen, (100, 80, 20),
                             (dx - 5, dy, 2, len(lines) * 12))
            for ln in lines:
                ps = self._font_name.render(ln, True, (190, 150, 55))
                screen.blit(ps, (dx, dy))
                dy += 12
