"""
Retro-futuristic shop screen for Autochess Hybrid.

This keeps the existing ShopScreen(screen, game, player, window) API used by
run_game.py, but refreshes the visuals with a neon dashboard, scanlines,
hover lift, rarity glow, wrapped passive tooltips, and a compact synergy
sidebar.
"""

import math
from collections import Counter
from typing import List, Optional

import pygame

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
    from ...engine_core.card import Card
    from ...engine_core.player import Player
    from ...engine_core.constants import (
        CARD_COSTS,
        STAT_TO_GROUP,
        MARKET_REFRESH_COST,
        STARTING_HP,
    )
    from ...engine_core.market import RARITY_WEIGHT
    from ..card_meta import CATEGORY_META, get_passive_desc
    from ..renderer_v3 import CyberRendererV3 as CyberRenderer, RARITY_COLORS as C_RARE


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

CARD_W = 220
CARD_H = 360
CARD_RADIUS = 12
CARD_GAP = 20
SIDEBAR_W = 280
FOOTER_H = 84


def _round_rect(surface, color, rect, radius, width=0):
    pygame.draw.rect(surface, color, rect, width, border_radius=radius)


def _lerp_color(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _darken(color, factor):
    return tuple(max(0, int(channel * (1.0 - factor))) for channel in color[:3])


def _safe_rarity_int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 6 if str(value).upper() == "E" else 0


def _wrap_words(text: str, font: pygame.font.Font, max_width: int) -> List[str]:
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
    return max(1, int(max(getattr(game, "turn", 0), getattr(player, "turns_played", 0), 1)))


def _current_rarity_weight(rarity_id: str, turn: int) -> float:
    weight = 0.0
    for min_turn, step_weight in RARITY_WEIGHT.get(rarity_id, [(1, 0.0)]):
        if turn >= min_turn:
            weight = step_weight
    return weight


class ShopCard:
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
        self.hovered = self.rect.collidepoint(mouse_pos) and not self.bought
        target = 1.0 if self.hovered else 0.0
        self.anim_t += (target - self.anim_t) * min(1.0, dt * 0.012)
        if self.buy_flash > 0:
            self.buy_flash = max(0, self.buy_flash - dt)

    def draw(self, surf: pygame.Surface, fonts: dict, player: Player,
             timer: float, fade_alpha: int, renderer: Optional[CyberRenderer] = None) -> pygame.Rect:
        card = self.card
        rarity_id = str(card.rarity)
        cost = CARD_COSTS.get(rarity_id, 99)
        can_afford = player.gold >= cost and not self.bought

        y_off = int(-15 * self.anim_t)
        draw_rect = self.rect.move(0, y_off)
        self.draw_rect = draw_rect

        if renderer is not None:
            renderer.draw_shop_card(
                surf,
                card,
                draw_rect,
                hovered=self.hovered,
                bought=self.bought,
                affordable=can_afford,
                cost=cost,
                alpha=fade_alpha,
            )
        else:
            rarity_color = NEON["rarity_cols"].get(rarity_id, NEON["muted"])
            pygame.draw.rect(surf, (22, 26, 40), draw_rect, border_radius=12)
            pygame.draw.rect(surf, rarity_color, draw_rect, width=2, border_radius=12)
            title = fonts["xs_bold"].render(card.name.upper(), True, NEON["white"])
            surf.blit(title, (draw_rect.x + 12, draw_rect.y + 15))

        return draw_rect


def draw_hand_card(surf: pygame.Surface, card: Card, rect: pygame.Rect, fonts: dict, hovered: bool):
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


class ShopScreen:
    def __init__(self, screen: pygame.Surface, game, player: Player, market_window: List[Card],
                 renderer: Optional[CyberRenderer] = None, fonts: Optional[dict] = None):
        self.screen = screen
        self.game = game
        self.player = player
        self.window = market_window
        self.W, self.H = screen.get_size()
        self.renderer = renderer

        self.timer = 0.0
        self.fade_alpha = 0
        self._result: Optional[str] = None
        self._msg = ""
        self._msg_timer = 0
        self._particles = []
        self._hover_refresh = False
        self._hover_done = False
        self._hovered_market_card = None

        if fonts is not None:
            self.fonts = fonts
        elif self.renderer is not None and getattr(self.renderer, "fonts", None):
            self.fonts = self.renderer.fonts
        else:
            self._init_fonts()

        if self.renderer is None:
            self.renderer = CyberRenderer(self.fonts)
        else:
            self.renderer.set_fonts(self.fonts)

        self._build_layout()

    def _init_fonts(self):
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

    def _build_layout(self):
        total_w = len(self.window) * CARD_W + max(0, len(self.window) - 1) * CARD_GAP
        start_x = max(24, (self.W - total_w) // 2)
        start_y = 168

        self.shop_cards: List[ShopCard] = []
        for idx, card in enumerate(self.window):
            rect = pygame.Rect(start_x + idx * (CARD_W + CARD_GAP), start_y, CARD_W, CARD_H)
            self.shop_cards.append(ShopCard(card, idx, rect))

        self.sidebar_rect = pygame.Rect(self.W - SIDEBAR_W, 70, SIDEBAR_W, self.H - 70 - FOOTER_H)
        self.btn_refresh = pygame.Rect(self.W // 2 - 210, self.H - 56, 185, 38)
        self.btn_done = pygame.Rect(self.W // 2 + 25, self.H - 56, 185, 38)

    def run(self) -> str:
        clock = pygame.time.Clock()
        while self._result is None:
            dt = clock.tick(60)
            self._handle_events()
            self._update(dt)
            self._draw()
            pygame.display.flip()
        return self._result

    def _handle_events(self):
        mouse = pygame.mouse.get_pos()
        self._hover_refresh = self.btn_refresh.collidepoint(mouse)
        self._hover_done = self.btn_done.collidepoint(mouse)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self._result = "quit"
            elif ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    self._result = "done"
                elif ev.key in (pygame.K_SPACE, pygame.K_r):
                    self._request_refresh()
                elif pygame.K_1 <= ev.key <= pygame.K_5:
                    self._try_buy(ev.key - pygame.K_1)
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for shop_card in self.shop_cards:
                    if shop_card.draw_rect.collidepoint(ev.pos) and not shop_card.bought:
                        self._try_buy(shop_card.index)
                        break
                if self.btn_refresh.collidepoint(ev.pos):
                    self._request_refresh()
                elif self.btn_done.collidepoint(ev.pos):
                    self._result = "done"

    def _request_refresh(self):
        if self.player.gold < MARKET_REFRESH_COST:
            self._set_msg(
                f"Refresh locked: need {MARKET_REFRESH_COST}G, have {self.player.gold}G"
            )
            return
        self._result = "refresh"

    def _try_buy(self, idx: int):
        if idx >= len(self.shop_cards):
            return

        shop_card = self.shop_cards[idx]
        if shop_card.bought:
            return

        card = shop_card.card
        cost = CARD_COSTS.get(str(card.rarity), 99)
        if self.player.gold < cost:
            self._set_msg(f"Insufficient gold: {cost}G required")
            return

        self.player.gold -= cost
        self.player.stats["gold_spent"] += cost

        cloned = card.clone()
        self.player.hand.append(cloned)
        self.player.copies[card.name] = self.player.copies.get(card.name, 0) + 1
        self.player.cards_bought_this_turn += 1
        self.player.stats["cards_bought_this_turn"] = (
            self.player.stats.get("cards_bought_this_turn", 0) + 1
        )
        self.player._window_bought.append(card.name)

        dropped_name = None
        if len(self.player.hand) > 6:
            dropped = self.player.hand.pop(0)
            dropped_name = dropped.name
            if self.player.copies.get(dropped.name, 0) > 0:
                self.player.copies[dropped.name] -= 1
            market = getattr(self.game, "market", None)
            if market is not None and hasattr(market, "pool_copies"):
                market.pool_copies[dropped.name] = market.pool_copies.get(dropped.name, 0) + 1
            self.player.stats["cards_dropped"] = self.player.stats.get("cards_dropped", 0) + 1

        shop_card.bought = True
        shop_card.buy_flash = 320
        self._spawn_particles(shop_card.rect)

        if dropped_name:
            self._set_msg(f"Purchased {card.name} ({cost}G). Buffer full: dropped {dropped_name}.")
        else:
            self._set_msg(f"Purchased {card.name} for {cost}G.")

    def _set_msg(self, message: str):
        self._msg = message
        self._msg_timer = 2400

    def _spawn_particles(self, rect: pygame.Rect):
        import random

        for _ in range(14):
            angle = random.uniform(0.0, 2.0 * math.pi)
            speed = random.uniform(1.5, 4.0)
            life = random.randint(300, 700)
            self._particles.append({
                "x": rect.centerx,
                "y": rect.centery,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - 1.0,
                "life": life,
                "max": life,
                "r": random.randint(2, 5),
                "col": random.choice([NEON["gold"], NEON["cyan"], NEON["pink"], NEON["ok"]]),
            })

    def _update(self, dt: int):
        self.timer += dt / 1000.0
        self.fade_alpha = min(255, self.fade_alpha + int(dt * 1.6))

        mouse = pygame.mouse.get_pos()
        for shop_card in self.shop_cards:
            shop_card.update(dt, mouse)

        alive_particles = []
        for particle in self._particles:
            particle["x"] += particle["vx"]
            particle["y"] += particle["vy"]
            particle["vy"] += 0.08
            particle["life"] -= dt
            if particle["life"] > 0:
                alive_particles.append(particle)
        self._particles = alive_particles

        if self._msg_timer > 0:
            self._msg_timer = max(0, self._msg_timer - dt)

    def _draw(self):
        self.screen.fill(NEON["bg"])
        self.renderer.draw_vfx_base(self.screen)
        self.timer = self.renderer.timer
        self._draw_economy_dash()
        self._draw_market_grid()
        self._draw_compare_sidebar()
        self._draw_footer()
        self._draw_particles()

    def _draw_scanlines(self):
        for y in range(0, self.H, 3):
            pygame.draw.line(self.screen, (0, 0, 0, 0), (0, y), (self.W, y))
            overlay = pygame.Surface((self.W, 1), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 36))
            self.screen.blit(overlay, (0, y))

    def _draw_cyber_grid(self):
        grid = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        horizon_y = 145

        for i in range(16):
            y = self.H - int((i ** 1.8) * 6)
            alpha = max(10, 150 - i * 10)
            pygame.draw.line(grid, (*NEON["grid"], alpha), (0, y), (self.W, y), 1)

        center_x = self.W // 2 - 80
        for lane in range(-10, 11):
            start_x = center_x + lane * 96
            end_x = center_x + lane * 420
            pygame.draw.line(grid, (*NEON["grid"], 48), (start_x, horizon_y), (end_x, self.H), 1)

        vignette = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        vignette.fill((0, 0, 0, 0))
        pygame.draw.rect(vignette, (0, 0, 0, 55), vignette.get_rect(), width=70)

        self.screen.blit(grid, (0, 0))
        self.screen.blit(vignette, (0, 0))

    def _draw_economy_dash(self):
        gold = self.fonts["lg"].render(f"{self.player.gold} CR", True, NEON["gold"])
        self.screen.blit(gold, (self.W - gold.get_width() - 40, 30))

        turn = self.fonts["sm"].render(
            f"TURN {_current_turn(self.game, self.player)}",
            True,
            NEON["muted"],
        )
        self.screen.blit(turn, (40, 38))

    def _draw_market_grid(self):
        mx, my = pygame.mouse.get_pos()
        hovered_card = None
        label = self.fonts["title"].render("MARKET", True, NEON["white"])
        self.screen.blit(label, (self.W // 2 - label.get_width() // 2, 120))
        sub = self.fonts["sm"].render("Hover to inspect passive data. Press 1-5 to buy.", True, NEON["muted"])
        self.screen.blit(sub, (self.W // 2 - sub.get_width() // 2, 154))

        for shop_card in self.shop_cards:
            draw_rect = shop_card.draw(
                self.screen,
                self.fonts,
                self.player,
                self.renderer.timer if self.renderer is not None else self.timer,
                self.fade_alpha,
                renderer=self.renderer,
            )
            if draw_rect.collidepoint(mx, my) and not shop_card.bought:
                hovered_card = shop_card.card

        self._hovered_market_card = hovered_card

        self.renderer.draw_priority_popup(
            self.screen,
            hovered_card,
            mx,
            my,
        )

    def _draw_smart_tooltip(self, card: Card, mx: int, my: int):
        self.renderer.draw_clean_tooltip(self.screen, card, mx, my, active=(card is not None))

    def _draw_synergy_sidebar(self):
        panel = pygame.Surface((self.sidebar_rect.width, self.sidebar_rect.height), pygame.SRCALPHA)
        panel.fill(NEON["panel"])
        self.screen.blit(panel, self.sidebar_rect.topleft)
        pygame.draw.line(
            self.screen,
            NEON["cyan"],
            self.sidebar_rect.topleft,
            (self.sidebar_rect.left, self.sidebar_rect.bottom),
            2,
        )

        x = self.sidebar_rect.x + 16
        y = self.sidebar_rect.y + 10

        header = self.fonts["md_bold"].render("SYNERGY_OS", True, NEON["pink"])
        self.screen.blit(header, (x, y))
        y += 30

        counts = Counter()
        for board_card in self.player.board.grid.values():
            for stat_name, value in board_card.stats.items():
                if value <= 0 or str(stat_name).startswith("_"):
                    continue
                group = STAT_TO_GROUP.get(stat_name)
                if group:
                    counts[group] += 1

        if not counts:
            empty = self.fonts["xs"].render("Board is idle. No synergy traces yet.", True, NEON["muted"])
            self.screen.blit(empty, (x, y))
            y += 30
        else:
            for group, count in counts.most_common():
                color = GROUP_COLORS.get(group, NEON["muted"])
                label = self.fonts["xs_bold"].render(group, True, NEON["white"])
                self.screen.blit(label, (x, y))
                pygame.draw.rect(self.screen, (20, 26, 45), (x, y + 18, 190, 7), border_radius=4)
                fill_w = min(190, count * 18)
                pygame.draw.rect(self.screen, color, (x, y + 18, fill_w, 7), border_radius=4)
                count_text = self.fonts["xs"].render(str(count), True, color)
                self.screen.blit(count_text, (x + 200, y + 10))
                y += 34

        y += 14
        hand_header = self.fonts["md_bold"].render(f"HAND_BUFFER [{len(self.player.hand)}/6]", True, NEON["cyan"])
        self.screen.blit(hand_header, (x, y))
        y += 28

        mouse = pygame.mouse.get_pos()
        if not self.player.hand:
            empty = self.fonts["xs"].render("- buffer empty -", True, NEON["muted"])
            self.screen.blit(empty, (x, y))
            return

        card_h = 72
        for hand_card in self.player.hand:
            rect = pygame.Rect(x, y, self.sidebar_rect.width - 32, card_h)
            if rect.bottom > self.sidebar_rect.bottom - 16:
                break
            draw_hand_card(self.screen, hand_card, rect, self.fonts, rect.collidepoint(mouse))
            y += card_h + 8

    # ------------------------------------------------------------------
    # Hover Compare Mode
    # ------------------------------------------------------------------

    def _draw_compare_sidebar(self):
        """v3 Hover compare mode: hovered market kartının gruplanmasına göre
        board kartları MATCH / CLASH ile vurgulanır.

        Hovered kart yoksa klasik synergy sidebar gösterilir.
        """
        hovered = getattr(self, "_hovered_market_card", None)
        if hovered is None:
            self._draw_synergy_sidebar()
            return

        # Hovered kartın aktif üst-grupları
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
        self.screen.blit(panel, self.sidebar_rect.topleft)
        pygame.draw.line(
            self.screen, NEON["cyan"],
            self.sidebar_rect.topleft,
            (self.sidebar_rect.left, self.sidebar_rect.bottom), 2,
        )

        x = self.sidebar_rect.x + 14
        y = self.sidebar_rect.y + 10

        # Başlık
        header = self.fonts["md_bold"].render("COMPARE_MODE", True, NEON["cyan"])
        self.screen.blit(header, (x, y)); y += 24

        # Hovered kart ismi
        sub = self.fonts["xs_bold"].render(
            hovered.name.upper()[:22], True, NEON["gold"]
        )
        self.screen.blit(sub, (x, y)); y += 18

        # Hovered grupları
        for grp in sorted(hovered_groups):
            col = GROUP_COLORS.get(grp, NEON["muted"])
            gi  = self.fonts["xs"].render(f"  ● {grp}", True, col)
            self.screen.blit(gi, (x, y)); y += 14
        y += 8

        # Legend
        self.screen.blit(
            self.fonts["xs_bold"].render("■ MATCH", True, NEON["ok"]),   (x,      y)
        )
        self.screen.blit(
            self.fonts["xs_bold"].render("■ CLASH", True, NEON["danger"]), (x + 90, y)
        )
        y += 20
        pygame.draw.line(
            self.screen, NEON["line"],
            (x, y), (self.sidebar_rect.right - 14, y), 1
        )
        y += 8

        # Mini board
        self._draw_mini_board(x, y, hovered_groups)

    def _draw_mini_board(self, start_x: int, start_y: int, hovered_groups: set):
        """Board kartlarını küçük hex'ler halinde listele; MATCH/CLASH vurgula."""
        import math as _math
        MINI_R   = 20
        MAX_W    = self.sidebar_rect.width - 28
        board    = self.player.board
        board_cards = list(board.grid.values())
        if not board_cards:
            empty = self.fonts["xs"].render("Board empty.", True, NEON["muted"])
            self.screen.blit(empty, (start_x, start_y))
            return

        cols    = max(1, MAX_W // (MINI_R * 2 + 8))
        row_h   = MINI_R * 2 + 12
        font_xs = self.fonts["xs"]
        font_xb = self.fonts["xs_bold"]

        for idx, card in enumerate(board_cards):
            col = idx % cols
            row = idx // cols
            cx  = start_x + col * (MINI_R * 2 + 8) + MINI_R
            cy  = start_y + row * row_h + MINI_R

            # Board ekraninin alt sinirini aşma
            if cy + MINI_R > self.sidebar_rect.bottom - 10:
                break

            # Bu kart MATCH mi?
            card_groups = set()
            for sn, sv in getattr(card, "stats", {}).items():
                if sv > 0 and not str(sn).startswith("_"):
                    g = STAT_TO_GROUP.get(sn)
                    if g:
                        card_groups.add(g)

            is_match = bool(card_groups & hovered_groups)

            # Hex gövde
            pts_hex = [
                (
                    int(cx + MINI_R * _math.cos(_math.radians(60 * i))),
                    int(cy + MINI_R * _math.sin(_math.radians(60 * i))),
                )
                for i in range(6)
            ]
            dom   = card.dominant_group()
            gc    = GROUP_COLORS.get(dom, NEON["muted"])
            fill  = tuple(max(0, c // 4) for c in gc)
            pygame.draw.polygon(self.screen, fill, pts_hex)

            if is_match:
                pygame.draw.polygon(self.screen, NEON["ok"], pts_hex, 2)
            else:
                pygame.draw.polygon(self.screen, NEON["muted"], pts_hex, 1)

            # Edge renkleri: MATCH grubu = grup rengi, diğer aktif = muted red
            edges = getattr(card, "rotated_edges", lambda: [])()
            for ei, (stat_name, value) in enumerate(edges[:6]):
                if value <= 0 or str(stat_name).startswith("_"):
                    continue
                eg  = STAT_TO_GROUP.get(stat_name)
                if eg in hovered_groups:
                    ecol = GROUP_COLORS.get(eg, NEON["ok"])
                else:
                    ecol = (180, 60, 60)   # muted red = clash

                a1 = pts_hex[ei]
                b1 = pts_hex[(ei + 1) % 6]
                pygame.draw.line(self.screen, ecol, a1, b1, 2)

            # Kart adı (mini)
            name_short = card.name[:8].upper()
            ni = font_xs.render(name_short, True, NEON["white"] if is_match else NEON["muted"])
            nx = cx - ni.get_width() // 2
            ny = cy - ni.get_height() // 2
            self.screen.blit(ni, (nx, ny))

    def _draw_footer(self):
        footer = pygame.Surface((self.W, FOOTER_H), pygame.SRCALPHA)
        self.screen.blit(footer, (0, self.H - FOOTER_H))
        pygame.draw.line(self.screen, NEON["line"], (0, self.H - FOOTER_H), (self.W, self.H - FOOTER_H), 1)

        self._draw_button(
            self.btn_refresh,
            f"[SPACE] RE-ROLL ({MARKET_REFRESH_COST}G)",
            self._hover_refresh,
            self.player.gold >= MARKET_REFRESH_COST,
            NEON["cyan"],
        )
        self._draw_button(
            self.btn_done,
            "[ENTER] BATTLE",
            self._hover_done,
            True,
            NEON["ok"],
        )

        if self._msg and self._msg_timer > 0:
            msg_text = self.fonts["xs"].render(self._msg, True, NEON["white"])
            self.screen.blit(msg_text, (24, self.H - 24))

        hint = self.fonts["xs"].render(
            "1-5 buy  |  SPACE reroll  |  ENTER battle  |  ESC exits shop",
            True,
            NEON["muted"],
        )
        self.screen.blit(hint, (self.W - hint.get_width() - 24, self.H - 24))

    def _draw_button(self, rect: pygame.Rect, label: str, hovered: bool, enabled: bool, color):
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

        _round_rect(self.screen, bg, rect, 8)
        _round_rect(self.screen, border, rect, 8, 2 if hovered else 1)
        text = self.fonts["sm_bold"].render(label, True, fg)
        self.screen.blit(
            text,
            (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2),
        )

    def _draw_particles(self):
        for particle in self._particles:
            alpha = int(255 * (particle["life"] / particle["max"]))
            radius = max(1, int(particle["r"] * particle["life"] / particle["max"]))
            sprite = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(sprite, (*particle["col"], max(0, min(255, alpha))), (radius, radius), radius)
            self.screen.blit(sprite, (int(particle["x"]) - radius, int(particle["y"]) - radius))
