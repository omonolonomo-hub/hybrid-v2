"""
screens/shop.py
---------------
Shop ekranı: 5 dükkan kartı, elde 6 slot, yenile + savaşa geç.
pygame_gui butonlar + elle çizilmiş kart widget'ları.
"""

import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UILabel

from core.game_state import GameState
from widgets.card_widget import CardWidget

# ─── Renk paleti ─────────────────────────────────────────────────────────────
C_BG       = (10, 11, 18)
C_PANEL    = (18, 20, 32)
C_PANEL2   = (24, 28, 48)
C_BORDER   = (44, 52, 80)
C_ACCENT   = (0, 242, 255)
C_GOLD     = (255, 200, 50)
C_RED      = (220, 60, 60)
C_TEXT     = (220, 228, 248)
C_DIM      = (100, 110, 140)

# ─── Kart boyutları ───────────────────────────────────────────────────────────
SHOP_CARD_W  = 130
SHOP_CARD_H  = 182
HAND_CARD_W  = 100
HAND_CARD_H  = 140
CARD_GAP     = 14


class ShopScreen:
    """
    handle_event(event) → "combat" | None
    update(dt)
    draw(screen)
    """

    def __init__(self, state: GameState, manager: pygame_gui.UIManager):
        self.state   = state
        self.manager = manager
        self.W, self.H = manager.get_root_container().get_size()

        self._selected_shop: int = -1   # seçili dükkan kartı
        self._selected_hand: int = -1   # seçili el kartı

        # Kart rect'leri (tıklama tespiti)
        self._shop_rects: list  = []
        self._hand_rects: list  = []

        # Surface cache (her frame'de yeniden render etmemek için)
        self._dirty = True

        self._build_ui()

    def _build_ui(self):
        W, H = self.W, self.H

        # ── Yenile butonu ──
        self.btn_refresh = UIButton(
            relative_rect=pygame.Rect(W - 180, 14, 160, 42),
            text="🔄  YENİLE (2💰)",
            manager=self.manager,
        )

        # ── Savaşa Git butonu ──
        self.btn_combat = UIButton(
            relative_rect=pygame.Rect(W - 180, 66, 160, 42),
            text="⚔  SAVAŞ",
            manager=self.manager,
        )

        # ── Sat butonu ──
        self.btn_sell = UIButton(
            relative_rect=pygame.Rect(W - 180, 118, 160, 42),
            text="💱  SAT",
            manager=self.manager,
        )

        # ── Satın Al butonu ──
        self.btn_buy = UIButton(
            relative_rect=pygame.Rect(W - 180, 170, 160, 42),
            text="🛒  SATIN AL",
            manager=self.manager,
        )

    def destroy(self):
        self.btn_refresh.kill()
        self.btn_combat.kill()
        self.btn_sell.kill()
        self.btn_buy.kill()

    # ─────────────────────────────────────────────────────────────────────────
    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_refresh:
                self.state.refresh_shop(cost=2)
                self._selected_shop = -1
                self._dirty = True

            elif event.ui_element == self.btn_combat:
                self.state.current_screen = "combat"
                return "combat"

            elif event.ui_element == self.btn_buy:
                if self._selected_shop >= 0:
                    ok = self.state.buy_card(self._selected_shop)
                    if ok:
                        self._selected_shop = -1
                    self._dirty = True

            elif event.ui_element == self.btn_sell:
                if self._selected_hand >= 0:
                    self.state.sell_card(self._selected_hand)
                    self._selected_hand = -1
                    self._dirty = True

        # ── Mouse tıklama (kart seçimi) ──
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for i, r in enumerate(self._shop_rects):
                if r.collidepoint(mx, my):
                    self._selected_shop = i if self._selected_shop != i else -1
                    self._selected_hand = -1
                    self._dirty = True
                    break
            for i, r in enumerate(self._hand_rects):
                if r.collidepoint(mx, my):
                    self._selected_hand = i if self._selected_hand != i else -1
                    self._selected_shop = -1
                    self._dirty = True
                    break

        return None

    def update(self, dt: float):
        self.state.tick(dt)

    # ─────────────────────────────────────────────────────────────────────────
    def draw(self, screen: pygame.Surface):
        W, H = self.W, self.H
        screen.fill(C_BG)

        # ── Başlık çubuğu ──
        pygame.draw.rect(screen, C_PANEL, (0, 0, W - 200, 58))
        hdr_font = pygame.font.SysFont("segoeui", 20, bold=True)
        info_font = pygame.font.SysFont("segoeui", 16)

        hdr_s = hdr_font.render(f"DÜKKAN  —  TUR {self.state.round}", True, C_ACCENT)
        screen.blit(hdr_s, (16, 16))

        info_s = info_font.render(
            f"💰 Altın: {self.state.gold}    ❤  HP: {self.state.hp}    El: {len(self.state.hand)}/6",
            True, C_GOLD
        )
        screen.blit(info_s, (16, 36))

        # ── Ayraç çizgisi ──
        pygame.draw.line(screen, C_BORDER, (0, 60), (W - 200, 60), 1)

        # ── Dükkan kartları ──
        shop_label_font = pygame.font.SysFont("segoeui", 13)
        sl = shop_label_font.render("DÜKKAN", True, C_DIM)
        screen.blit(sl, (16, 70))

        shop_cards = self.state.shop
        total_shop_w = len(shop_cards) * SHOP_CARD_W + (len(shop_cards) - 1) * CARD_GAP
        shop_x0 = max(16, (W - 200 - total_shop_w) // 2)
        shop_y0 = 90

        self._shop_rects = []
        for i, card in enumerate(shop_cards):
            x = shop_x0 + i * (SHOP_CARD_W + CARD_GAP)
            y = shop_y0
            card_surf = CardWidget.render(
                card, SHOP_CARD_W, SHOP_CARD_H,
                selected=(i == self._selected_shop)
            )
            screen.blit(card_surf, (x, y))
            self._shop_rects.append(pygame.Rect(x, y, SHOP_CARD_W, SHOP_CARD_H))

            # Fiyat rozeti
            cost_font = pygame.font.SysFont("segoeui", 14, bold=True)
            can_afford = self.state.gold >= card["cost"]
            cost_col = C_GOLD if can_afford else C_RED
            c_s = cost_font.render(f"{card['cost']}💰", True, cost_col)
            screen.blit(c_s, (x + SHOP_CARD_W // 2 - c_s.get_width() // 2,
                               y + SHOP_CARD_H + 4))

        # ── El ──
        pygame.draw.line(screen, C_BORDER, (0, H - HAND_CARD_H - 60), (W - 200, H - HAND_CARD_H - 60), 1)
        hl = shop_label_font.render(f"EL  ({len(self.state.hand)}/6)", True, C_DIM)
        screen.blit(hl, (16, H - HAND_CARD_H - 52))

        hand_y0 = H - HAND_CARD_H - 24
        self._hand_rects = []
        for i, card in enumerate(self.state.hand):
            x = 16 + i * (HAND_CARD_W + CARD_GAP)
            y = hand_y0
            card_surf = CardWidget.render(
                card, HAND_CARD_W, HAND_CARD_H,
                selected=(i == self._selected_hand)
            )
            screen.blit(card_surf, (x, y))
            self._hand_rects.append(pygame.Rect(x, y, HAND_CARD_W, HAND_CARD_H))

        # ── Seçili kart detayı ──
        sel_card = None
        if self._selected_shop >= 0 and self._selected_shop < len(self.state.shop):
            sel_card = self.state.shop[self._selected_shop]
        elif self._selected_hand >= 0 and self._selected_hand < len(self.state.hand):
            sel_card = self.state.hand[self._selected_hand]

        if sel_card:
            self._draw_detail(screen, sel_card, W - 196, 224)

        # ── Mesaj ──
        if self.state.message:
            msg_font = pygame.font.SysFont("segoeui", 16)
            msg_s = msg_font.render(self.state.message, True, (255, 80, 80))
            screen.blit(msg_s, (W // 2 - msg_s.get_width() // 2, H // 2 - 20))

    def _draw_detail(self, screen: pygame.Surface, card: dict, x: int, y: int):
        """Sağ panelde seçili kartın detayını göster."""
        from core.card_loader import GROUP_COLORS, RARITY_COLORS
        panel_w = 186
        panel_h = 220
        pygame.draw.rect(screen, C_PANEL2, (x, y, panel_w, panel_h), border_radius=8)
        pygame.draw.rect(screen, C_BORDER,  (x, y, panel_w, panel_h), 1, border_radius=8)

        f_title = pygame.font.SysFont("segoeui", 13, bold=True)
        f_body  = pygame.font.SysFont("segoeui", 11)

        ty = y + 8
        for text, font, col in [
            (card["name"],     f_title, C_TEXT),
            (card["category"], f_body,  C_DIM),
            (f"Rarity: {'◆' * int(card['rarity'])}", f_body, RARITY_COLORS.get(card["rarity"], C_DIM)),
            (f"Grup: {card['dominant_group']}", f_body, GROUP_COLORS.get(card["dominant_group"], C_DIM)),
            ("", f_body, C_DIM),
        ]:
            s = font.render(text, True, col)
            screen.blit(s, (x + 8, ty))
            ty += s.get_height() + 2

        # Stats
        for stat_name, val in list(card["stats"].items())[:6]:
            bar_w = int((val / 10) * (panel_w - 80))
            from core.card_loader import STAT_TO_GROUP
            g = STAT_TO_GROUP.get(stat_name, "EXISTENCE")
            col = GROUP_COLORS.get(g, C_DIM)
            s = f_body.render(f"{stat_name[:8]}", True, C_TEXT)
            screen.blit(s, (x + 8, ty))
            pygame.draw.rect(screen, C_BORDER, (x + 72, ty + 2, panel_w - 80, 8), border_radius=3)
            pygame.draw.rect(screen, col,      (x + 72, ty + 2, bar_w, 8), border_radius=3)
            v = f_body.render(str(val), True, col)
            screen.blit(v, (x + panel_w - 20, ty))
            ty += 14
            if ty > y + panel_h - 20:
                break

        # Passive
        passive = card.get("passive_effect", "")
        if passive:
            ty += 4
            p_lines = _wrap_text(passive, f_body, panel_w - 16)
            for line in p_lines[:3]:
                s = f_body.render(line, True, C_ACCENT)
                screen.blit(s, (x + 8, ty))
                ty += s.get_height() + 1


def _wrap_text(text: str, font: pygame.font.Font, max_w: int) -> list:
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if font.size(test)[0] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines
