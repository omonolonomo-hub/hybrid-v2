"""
screens/combat.py
-----------------
Savaş ekranı — 37-hex pointy-top axial grid.

Layout:
  Sol+Orta : 37 hexlik tahta (yarıçap=3, eksen koordinatı)
  Alt      : El paneli  (kart küçük resmi + isim)
  Sağ      : Seçili kart detayı + aksiyon butonları

Nasıl oynanır:
  1. Alt eldeki bir karta tıkla (sarı seçim)
  2. Tahtadaki boş bir hexe tıkla → kart oraya yerleşir
  3. Yerleşmiş karta tıkla → seçili (mavi), sonra "GERİ AL"
  4. "SAVAŞI BİTİR" → savaş simüle edilir, shop'a dön
"""

import math
from typing import Dict, List, Optional, Tuple, Set

import pygame
import pygame_gui
from pygame_gui.elements import UIButton

from core.game_state import GameState
from core.card_loader import STAT_TO_GROUP, GROUP_COLORS, RARITY_COLORS
from widgets.card_widget import CardWidget

# ─── Renkler ──────────────────────────────────────────────────────────────────
C_BG        = (10,  11,  18)
C_PANEL     = (18,  20,  32)
C_BORDER    = (44,  52,  80)
C_CYAN      = (0,  242, 255)
C_GOLD      = (255, 200,  50)
C_TEXT      = (220, 228, 248)
C_DIM       = (100, 110, 140)
C_ACCENT    = (0,  242, 255)
C_RED       = (220,  60,  60)
C_GREEN     = ( 80, 220, 100)

C_HEX_EMPTY = ( 18,  24,  46)
C_HEX_HOVER = ( 28,  40,  70)
C_HEX_SEL_BORDER = C_CYAN
C_HEX_DEST  = ( 20,  60,  80)   # boş ama seçili hedef hex

# ─── Layout sabitleri ─────────────────────────────────────────────────────────
HEADER_H  = 60
HAND_H    = 165
RIGHT_W   = 230

HEX_SIZE  = 42       # pointy-top yarıçap (piksel)
BOARD_RADIUS = 3     # 37 hex

# ─── Axial koordinat yardımcıları ─────────────────────────────────────────────

def _hex_coords(radius: int) -> Set[Tuple[int, int]]:
    return {
        (q, r)
        for q in range(-radius, radius + 1)
        for r in range(-radius, radius + 1)
        if abs(q + r) <= radius
    }

BOARD_COORDS: Set[Tuple[int, int]] = _hex_coords(BOARD_RADIUS)


def _axial_to_pixel(q: int, r: int, size: float, ox: int, oy: int) -> Tuple[int, int]:
    """Axial koordinatı piksel merkezine çevirir (pointy-top)."""
    x = ox + size * (math.sqrt(3) * q + math.sqrt(3) / 2 * r)
    y = oy + size * (3 / 2 * r)
    return int(x), int(y)


def _pixel_to_hex(px: int, py: int, size: float, ox: int, oy: int) -> Tuple[int, int]:
    """Piksel → en yakın axial hex koordinatı."""
    px -= ox
    py -= oy
    q_f = (math.sqrt(3) / 3 * px - 1 / 3 * py) / size
    r_f = (2 / 3 * py) / size
    # Cube round
    s_f = -q_f - r_f
    q, r, s = round(q_f), round(r_f), round(s_f)
    dq, dr, ds = abs(q - q_f), abs(r - r_f), abs(s - s_f)
    if dq > dr and dq > ds:
        q = -r - s
    elif dr > ds:
        r = -q - s
    return (q, r)


def _hex_corners(cx: int, cy: int, size: float) -> List[Tuple[float, float]]:
    """Pointy-top hex'in 6 köşesi."""
    return [
        (cx + size * math.cos(math.radians(60 * i + 30)),
         cy + size * math.sin(math.radians(60 * i + 30)))
        for i in range(6)
    ]


def _edge_label_pos(cx: int, cy: int, size: float, edge_idx: int) -> Tuple[int, int]:
    """
    Her kenardaki stat değerinin yazılacağı nokta.
    Pointy-top'ta kenar orta noktaları 0°, 60°, 120°, 180°, 240°, 300° yönlerinde.
    """
    angle = math.radians(60 * edge_idx)          # 0,60,120,180,240,300
    dist  = size * 0.78                           # köşeden biraz içeride
    return (int(cx + dist * math.cos(angle)),
            int(cy + dist * math.sin(angle)))


# ─── CombatScreen ─────────────────────────────────────────────────────────────

class CombatScreen:
    """
    handle_event(event) → "shop" | "game_over" | None
    update(dt)
    draw(screen)
    """

    def __init__(self, state: GameState, manager: pygame_gui.UIManager):
        self.state   = state
        self.manager = manager
        self.W, self.H = manager.get_root_container().get_size()

        # Tahta orta noktası (board coordinate origin)
        board_area_w = self.W - RIGHT_W
        board_area_h = self.H - HEADER_H - HAND_H
        self._ox = board_area_w // 2
        self._oy = HEADER_H + board_area_h // 2

        # Seçim durumu
        self._sel_hand:  int                    = -1    # elden seçili kart indeksi
        self._sel_coord: Optional[Tuple[int,int]] = None  # tahtada seçili hex

        # El rektleri (her frame güncellenir)
        self._hand_rects: List[pygame.Rect] = []
        self._hand_coords: List[Tuple[int,int]] = []  # coord-to-pixel cache

        self._build_ui()

    # ── UI inşa ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        W, H = self.W, self.H
        rx = W - RIGHT_W + 8

        self.btn_recall = UIButton(
            relative_rect=pygame.Rect(rx, HEADER_H + 10, RIGHT_W - 16, 40),
            text="↩  GERİ AL",
            manager=self.manager,
        )
        self.btn_end = UIButton(
            relative_rect=pygame.Rect(rx, H - HAND_H - 60, RIGHT_W - 16, 48),
            text="⚔  SAVAŞI BİTİR",
            manager=self.manager,
        )

    def destroy(self):
        self.btn_recall.kill()
        self.btn_end.kill()

    # ── Olay işleme ───────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:

            if event.ui_element == self.btn_recall:
                if self._sel_coord and self._sel_coord in self.state.board:
                    self.state.recall_card(self._sel_coord)
                    self._sel_coord = None
                else:
                    self.state.show_message("Geri almak için tahtadan bir kart seç.")

            elif event.ui_element == self.btn_end:
                result = self._simulate_combat()
                if self.state.current_screen == "game_over":
                    return "game_over"
                return "shop"

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # ── El paneli mi? ──
            for i, rect in enumerate(self._hand_rects):
                if rect.collidepoint(mx, my):
                    # Aynı karta tekrar tıkla → seçimi kaldır
                    self._sel_hand  = i if self._sel_hand != i else -1
                    self._sel_coord = None
                    return None

            # ── Tahta hexe tıklandı mı? ──
            if my < self.H - HAND_H:          # el panelinin üstünde
                coord = _pixel_to_hex(mx, my, HEX_SIZE, self._ox, self._oy)
                if coord in BOARD_COORDS:
                    if coord in self.state.board:
                        # Dolu hex: tahtadan seç
                        self._sel_coord = coord if self._sel_coord != coord else None
                        self._sel_hand  = -1
                    else:
                        # Boş hex: elden seçiliyse yerleştir
                        if self._sel_hand >= 0:
                            ok = self.state.place_card(self._sel_hand, coord)
                            if ok:
                                self._sel_hand = -1
                        else:
                            # Sadece hedef hex olarak işaretle
                            self._sel_coord = coord if self._sel_coord != coord else None

        return None

    # ── Savaş simülasyonu ─────────────────────────────────────────────────────

    def _simulate_combat(self) -> str:
        """
        Basit savaş: oyuncu kartlarının toplam gücü vs düşman.
        Tur × 18 düşman gücü — erken turlar kolaydan zora.
        """
        board_cards = list(self.state.board.values())
        if not board_cards:
            # Tahta boş — tam hasar
            dmg = 20
            self.state.show_message(f"Tahta boş! {dmg} hasar aldın.")
            self.state.take_damage(dmg)
            self.state.advance_round()
            return "shop"

        player_power = sum(
            sum(c["stats"].values()) for c in board_cards
        )
        enemy_power  = self.state.round * 18 + 10

        # Sinerji bonusu: aynı dominant_group'tan komşu kartlar
        synergy = self._calc_synergy()
        player_power += synergy

        if player_power >= enemy_power:
            won_by   = player_power - enemy_power
            bonus_gold = min(4, won_by // 8)
            self.state.gold += bonus_gold
            self.state.show_message(
                f"Zafer! Güç {player_power} > {enemy_power}. +{bonus_gold}💰 bonus."
            )
            dmg = 0
        else:
            lost_by = enemy_power - player_power
            dmg     = max(1, lost_by // 4)
            self.state.show_message(
                f"Yenilgi! Güç {player_power} < {enemy_power}. {dmg} hasar."
            )

        self.state.take_damage(dmg)
        if self.state.current_screen != "game_over":
            self.state.advance_round()

        return self.state.current_screen

    def _calc_synergy(self) -> int:
        """Komşu aynı-grup kartları için +2/çift sinerji bonusu."""
        # Basit: her birbirinden komşu aynı-grup çifti +2
        HEX_DIRS = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
        counted = set()
        bonus = 0
        for coord, card in self.state.board.items():
            g = card.get("dominant_group", "EXISTENCE")
            q, r = coord
            for dq, dr in HEX_DIRS:
                nb = (q + dq, r + dr)
                if nb in self.state.board:
                    pair = (min(coord, nb), max(coord, nb))
                    if pair not in counted:
                        if self.state.board[nb].get("dominant_group") == g:
                            bonus += 2
                        counted.add(pair)
        return bonus

    # ── Güncelle ──────────────────────────────────────────────────────────────

    def update(self, dt: float):
        self.state.tick(dt)

    # ── Çizim ─────────────────────────────────────────────────────────────────

    def draw(self, screen: pygame.Surface):
        W, H = self.W, self.H
        screen.fill(C_BG)

        self._draw_header(screen)
        self._draw_board(screen)
        self._draw_hand(screen)
        self._draw_right_panel(screen)

        # Mesaj overlay
        if self.state.message:
            mf = pygame.font.SysFont("segoeui", 16, bold=True)
            ms = mf.render(self.state.message, True, C_RED)
            bx = W // 2 - ms.get_width() // 2 - 8
            by = H // 2 - ms.get_height() // 2 - 6
            pygame.draw.rect(screen, (10, 10, 20, 200),
                             (bx - 4, by - 4, ms.get_width() + 24, ms.get_height() + 12),
                             border_radius=6)
            screen.blit(ms, (bx + 4, by + 2))

    def _draw_header(self, screen: pygame.Surface):
        W = self.W
        pygame.draw.rect(screen, C_PANEL, (0, 0, W, HEADER_H))
        pygame.draw.line(screen, C_BORDER, (0, HEADER_H), (W, HEADER_H), 1)

        hf = pygame.font.SysFont("segoeui", 20, bold=True)
        sf = pygame.font.SysFont("segoeui", 14)

        hs = hf.render(f"SAVAŞ — TUR {self.state.round} / {self.state.max_rounds}", True, C_CYAN)
        screen.blit(hs, (16, 10))

        board_count = len(self.state.board)
        player_pwr  = sum(sum(c["stats"].values()) for c in self.state.board.values())
        enemy_pwr   = self.state.round * 18 + 10

        ss = sf.render(
            f"💰 {self.state.gold}   ❤ {self.state.hp}   "
            f"Tahta: {board_count}/37 kart   "
            f"Güç: {player_pwr} vs {enemy_pwr} (düşman)",
            True, C_GOLD
        )
        screen.blit(ss, (16, 36))

    # ── Tahta ─────────────────────────────────────────────────────────────────

    def _draw_board(self, screen: pygame.Surface):
        ox, oy = self._ox, self._oy
        stat_font = pygame.font.SysFont("segoeui", 9)
        name_font = pygame.font.SysFont("segoeui", 10, bold=True)

        for coord in BOARD_COORDS:
            q, r = coord
            cx, cy = _axial_to_pixel(q, r, HEX_SIZE, ox, oy)
            corners = _hex_corners(cx, cy, HEX_SIZE - 1)

            card    = self.state.board.get(coord)
            is_sel_board = (coord == self._sel_coord)
            is_sel_dest  = (coord == self._sel_coord and coord not in self.state.board)

            # ── Doldur ──
            if card:
                grp  = card.get("dominant_group", "EXISTENCE")
                base = GROUP_COLORS.get(grp, (80, 80, 120))
                fill = tuple(min(255, int(c * 0.32)) for c in base)
            elif is_sel_dest:
                fill = C_HEX_DEST
            elif self._sel_hand >= 0:
                # El seçiliyken boş hexler daha parlak
                fill = (22, 32, 58)
            else:
                fill = C_HEX_EMPTY
            pygame.draw.polygon(screen, fill, corners)

            # ── Çerçeve ──
            if is_sel_board:
                pygame.draw.polygon(screen, C_CYAN, corners, 3)
            elif card:
                grp = card.get("dominant_group", "EXISTENCE")
                pygame.draw.polygon(screen, GROUP_COLORS.get(grp, C_BORDER), corners, 2)
            else:
                pygame.draw.polygon(screen, C_BORDER, corners, 1)

            # ── Kart içeriği ──
            if card:
                self._draw_card_in_hex(screen, card, cx, cy, stat_font, name_font)
            elif self._sel_hand >= 0:
                # İpucu: yerleştirilebilir
                tf = pygame.font.SysFont("segoeui", 8)
                ts = tf.render("+", True, (60, 90, 120))
                screen.blit(ts, (cx - ts.get_width() // 2, cy - ts.get_height() // 2))

    def _draw_card_in_hex(self, screen, card, cx, cy, stat_font, name_font):
        """Hex içine kart adı + 6 stat değeri (kenarlarda)."""
        # Kart adı merkez
        name = card["name"][:9]
        ns = name_font.render(name, True, C_TEXT)
        screen.blit(ns, (cx - ns.get_width() // 2, cy - ns.get_height() // 2 - 2))

        # 6 stat → 6 kenarda
        stats = list(card["stats"].items())
        for edge_idx in range(6):
            if edge_idx >= len(stats):
                break
            stat_name, val = stats[edge_idx]
            grp = STAT_TO_GROUP.get(stat_name, "EXISTENCE")
            col = GROUP_COLORS.get(grp, C_DIM)
            ex, ey = _edge_label_pos(cx, cy, HEX_SIZE, edge_idx)
            vs = stat_font.render(str(val), True, col)
            # Küçük arka plan
            pygame.draw.rect(screen, (10, 12, 22),
                             (ex - vs.get_width() // 2 - 1,
                              ey - vs.get_height() // 2 - 1,
                              vs.get_width() + 2, vs.get_height() + 2),
                             border_radius=2)
            screen.blit(vs, (ex - vs.get_width() // 2, ey - vs.get_height() // 2))

        # Rarity nokta (alt merkez)
        rarity = card.get("rarity", "1")
        dot_col = RARITY_COLORS.get(rarity, C_DIM)
        pygame.draw.circle(screen, dot_col, (cx, cy + HEX_SIZE - 10), 4)

    # ── El paneli ─────────────────────────────────────────────────────────────

    def _draw_hand(self, screen: pygame.Surface):
        W, H = self.W, self.H
        panel_y = H - HAND_H

        pygame.draw.rect(screen, C_PANEL, (0, panel_y, W - RIGHT_W, HAND_H))
        pygame.draw.line(screen, C_BORDER, (0, panel_y), (W - RIGHT_W, panel_y), 1)

        lf = pygame.font.SysFont("segoeui", 12)
        hand_count = len(self.state.hand)
        inst = "tıkla → seç, sonra hexe tıkla → yerleştir" if hand_count else "El boş"
        ls = lf.render(f"EL ({hand_count}/6)  {inst}", True, C_DIM)
        screen.blit(ls, (10, panel_y + 4))

        card_w, card_h = 105, 140
        gap = 8
        self._hand_rects = []

        for i, card in enumerate(self.state.hand):
            x = 10 + i * (card_w + gap)
            y = panel_y + 20
            sel = (i == self._sel_hand)
            surf = CardWidget.render(card, card_w, card_h, selected=sel)
            screen.blit(surf, (x, y))
            self._hand_rects.append(pygame.Rect(x, y, card_w, card_h))

    # ── Sağ panel ─────────────────────────────────────────────────────────────

    def _draw_right_panel(self, screen: pygame.Surface):
        W, H = self.W, self.H
        rx = W - RIGHT_W
        pygame.draw.rect(screen, C_PANEL, (rx, 0, RIGHT_W, H))
        pygame.draw.line(screen, C_BORDER, (rx, 0), (rx, H), 1)

        # Seçili kart
        sel_card = None
        src = ""
        if self._sel_coord and self._sel_coord in self.state.board:
            sel_card = self.state.board[self._sel_coord]
            src = "tahta"
        elif self._sel_hand >= 0 and self._sel_hand < len(self.state.hand):
            sel_card = self.state.hand[self._sel_hand]
            src = "el"

        f_t = pygame.font.SysFont("segoeui", 13, bold=True)
        f_b = pygame.font.SysFont("segoeui", 11)

        ty = HEADER_H + 65

        if sel_card:
            # Başlık
            for text, font, col in [
                (sel_card["name"],                f_t, C_TEXT),
                (sel_card.get("category", ""),    f_b, C_DIM),
                (sel_card.get("dominant_group",""),f_b,
                 GROUP_COLORS.get(sel_card.get("dominant_group",""), C_DIM)),
                (f"Rarity {'◆'*int(sel_card.get('rarity','1'))}  [{src}]", f_b, C_GOLD),
            ]:
                s = font.render(text, True, col)
                screen.blit(s, (rx + 8, ty))
                ty += s.get_height() + 3

            ty += 6
            pygame.draw.line(screen, C_BORDER, (rx + 6, ty), (W - 6, ty), 1)
            ty += 8

            # Stats + bar
            bar_max = RIGHT_W - 84
            for stat_name, val in sel_card["stats"].items():
                grp = STAT_TO_GROUP.get(stat_name, "EXISTENCE")
                col = GROUP_COLORS.get(grp, C_DIM)
                bar_w = int((max(0, val) / 10) * bar_max)
                s = f_b.render(stat_name[:9], True, C_TEXT)
                screen.blit(s, (rx + 8, ty))
                pygame.draw.rect(screen, C_BORDER,
                                 (rx + 76, ty + 2, bar_max, 8), border_radius=3)
                pygame.draw.rect(screen, col,
                                 (rx + 76, ty + 2, bar_w, 8), border_radius=3)
                vs = f_b.render(str(val), True, col)
                screen.blit(vs, (W - 20, ty))
                ty += 15
                if ty > H - HAND_H - 90:
                    break

            # Passive effect
            pe = sel_card.get("passive_effect", "")
            if pe and ty < H - HAND_H - 30:
                ty += 6
                for line in _wrap_text(pe, f_b, RIGHT_W - 16)[:5]:
                    s = f_b.render(line, True, C_ACCENT)
                    screen.blit(s, (rx + 8, ty))
                    ty += s.get_height() + 2

        else:
            hint = f_b.render("Kart seç:", True, C_DIM)
            screen.blit(hint, (rx + 8, ty))
            ty += 20
            lines = [
                "• Elden bir karta tıkla",
                "• Sonra boş hexe tıkla",
                "• Yerleşik karta tıkla",
                "  → Geri Al butonu",
            ]
            for line in lines:
                s = f_b.render(line, True, C_DIM)
                screen.blit(s, (rx + 8, ty))
                ty += s.get_height() + 4

        # Tahta özet (sağ alt)
        board_cards = list(self.state.board.values())
        if board_cards:
            ty2 = H - HAND_H - 90
            pygame.draw.line(screen, C_BORDER, (rx + 6, ty2), (W - 6, ty2), 1)
            ty2 += 8
            pwr = sum(sum(c["stats"].values()) for c in board_cards)
            syn = self._calc_synergy()
            epy = self.state.round * 18 + 10
            for txt, col in [
                (f"Kart sayısı: {len(board_cards)}", C_TEXT),
                (f"Tahta gücü: {pwr}", C_CYAN),
                (f"Sinerji:    +{syn}", C_GREEN),
                (f"Toplam:     {pwr+syn}", C_CYAN),
                (f"Düşman:     {epy}", C_RED),
            ]:
                s = f_b.render(txt, True, col)
                screen.blit(s, (rx + 8, ty2))
                ty2 += s.get_height() + 3


# ─── Yardımcı ─────────────────────────────────────────────────────────────────

def _wrap_text(text: str, font: pygame.font.Font, max_w: int) -> List[str]:
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
