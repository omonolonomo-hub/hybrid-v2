"""
================================================================
  Autochess Hybrid - Hex Renderer  (v3 — boyut revizyonu + rotasyon)
================================================================
  Değişiklikler:
    • HEX_SIZE 48 → 38  (37 hex board'da iç içe geçme yok)
    • Kenar etiket offset daraltıldı, sadece hex içine sığan
      kısa bilgi gösteriliyor
    • Stat etiketi: değer hex içinde kenara yakın,
      kısa ad kaldırıldı (yer yok)
    • Hover tooltip ayrı yüzey olarak hex dışına çıkıyor
    • Rotasyon desteği: card.rotated_edges() ile doğru yön
    • Yerleştirme öncesi rotasyon göstergesi (preview)
================================================================
"""

import math
import pygame
from typing import Optional, Tuple, Dict, List

try:
    from ui.card_meta import (
        CATEGORY_META,
        CATEGORY_COLORS,
        get_category_color,
        get_category_icon,
        get_passive_desc,
    )
except ImportError:
    try:
        from .card_meta import (
            CATEGORY_META,
            CATEGORY_COLORS,
            get_category_color,
            get_category_icon,
            get_passive_desc,
        )
    except ImportError:
        CATEGORY_META = {}
        CATEGORY_COLORS = {}
        def get_category_color(category):
            return (150, 150, 170)
        def get_category_icon(category):
            return "*"
        def get_passive_desc(n, t=""):
            return t

try:
    from engine_core.constants import STAT_TO_GROUP
except ImportError:
    try:
        from ..engine_core.constants import STAT_TO_GROUP
    except ImportError:
        STAT_TO_GROUP = {}

try:
    from engine_core.board import BOARD_COORDS
except ImportError:
    try:
        from ..engine_core.board import BOARD_COORDS
    except ImportError:
        BOARD_COORDS = []


C_BG = (10, 11, 18)

# ── Cyber-Victorian Palet ────────────────────────────
C_BRONZE    = (150,  80,  40)
C_RUST      = ( 60,  30,  20)
C_NEON_PINK = (255,   0, 150)

C_CYAN = (0, 242, 255)
C_PINK = (255, 0, 255)
C_GOLD = (255, 204, 0)
C_WHITE = (245, 245, 255)
C_PANEL = (16, 20, 34)
C_PANEL_2 = (22, 28, 46)
C_L_GRID = (30, 35, 50, 15)
C_L_SCAN = (0, 0, 0, 10)
C_RARE: Dict[str, Tuple[int, int, int]] = {
    "1": (160, 160, 160),
    "2": (50, 255, 120),
    "3": (0, 180, 255),
    "4": (255, 0, 255),
    "5": (255, 215, 0),
    "E": (255, 255, 255),
}

# ── Boyut sabitleri ───────────────────────────────────────────
HEX_SIZE   = 68          # yarıçap — büyütüldü v0.8
HEX_INNER  = HEX_SIZE - 4   # iç dolgu (border boşluğu)

# Kenar etiketi için hex içindeki offset (merkeze doğru)
EDGE_LABEL_INSET = 12    # kenar ortasından merkeze doğru bu kadar içeri

# ── Renk paletleri ────────────────────────────────────────────
STRATEGY_COLORS: Dict[str, Tuple[int,int,int]] = {
    "tempo":       (220,  80,  80),
    "warrior":     (200, 120,  40),
    "builder":     ( 60, 160, 220),
    "evolver":     ( 80, 200, 120),
    "economist":   (200, 180,  40),
    "balancer":    (160,  80, 200),
    "rare_hunter": (200,  60, 160),
    "random":      (120, 120, 120),
}

GROUP_COLORS: Dict[str, Tuple[int,int,int]] = {
    "EXISTENCE":   (255,  60,  50),   # canlı kırmızı
    "MIND":        ( 50, 130, 255),   # canlı mavi
    "CONNECTION":  ( 40, 230, 130),   # canlı yeşil
}

SYNERGY_META: Dict[str, Tuple[str, Tuple[int, int, int]]] = {
    "EXISTENCE":  ("EX", GROUP_COLORS["EXISTENCE"]),
    "MIND":       ("MN", GROUP_COLORS["MIND"]),
    "CONNECTION": ("CN", GROUP_COLORS["CONNECTION"]),
}

# Kategori renkleri
CATEGORY_COLORS: Dict[str, Tuple[int,int,int]] = {
    "Mythology & Gods":        (248, 222,  34),  # F8DE22 sarı
    "Art & Culture":           (209,  32,  82),  # D12052 kırmızı
    "Nature & Creatures":      ( 35, 114,  39),  # 237227 yeşil
    "Cosmos":                  ( 40,  28,  89),  # 281C59 mor
    "Science":                 (  3, 174, 210),  # 03AED2 cyan
    "History & Civilizations": (244,  91,  38),  # F45B26 turuncu
}

RARITY_COLORS: Dict[str, Tuple[int, int, int]] = {
    **C_RARE,
}

COLOR_EMPTY    = ( 20,  24,  38)
COLOR_BORDER   = ( 40,  52,  84)
COLOR_HOVER    = ( 46,  62, 102)
COLOR_TEXT     = C_WHITE
COLOR_TEXT_DIM = (130, 130, 150)
COLOR_BG       = C_BG

# Rotasyon önizleme rengi
COLOR_ROT_PREVIEW = C_GOLD

STAT_SHORT: Dict[str, str] = {
    "Power":        "PW",
    "Durability":   "DU",
    "Size":         "SZ",
    "Speed":        "SP",
    "Meaning":      "MN",
    "Secret":       "SC",
    "Intelligence": "IN",
    "Trace":        "TR",
    "Gravity":      "GR",
    "Harmony":      "HR",
    "Spread":       "SR",
    "Prestige":     "PR",
}

FIXED_SHOP_STATS = [
    ("Power", "PWR"),
    ("Durability", "DUR"),
    ("Size", "SIZ"),
    ("Speed", "SPD"),
    ("Intelligence", "INT"),
    ("Secret", "SEC"),
]

_STAT_GROUP: Dict[str, str] = {
    "Power": "EXISTENCE", "Durability": "EXISTENCE",
    "Size":  "EXISTENCE", "Speed":      "EXISTENCE",
    "Meaning":      "MIND", "Secret":       "MIND",
    "Intelligence": "MIND", "Trace":        "MIND",
    "Gravity": "CONNECTION", "Harmony":   "CONNECTION",
    "Spread":  "CONNECTION", "Prestige":  "CONNECTION",
}

# Yön adları (0=N, 1=NE, 2=SE, 3=S, 4=SW, 5=NW)
DIR_LABELS = ["N", "NE", "SE", "S", "SW", "NW"]


# ── Passive açıklamaları (tooltip için) ──────────────────────
PASSIVE_DESCS: Dict[str, str] = {
    # Kart adına göre özel açıklamalar
    "Ragnarök":      "Savaş kazanıldığında düşmanın en güçlü kartının en yüksek kenarını siler.",
    "World War II":  "Savaş kazanıldığında TÜM düşman kartlarının en yüksek kenarını siler.",
    "Loki":          "Savaş kazanıldığında düşmanın en güçlü kartının Meaning değerini -1 azaltır.",
    "Cubism":        "Savaş kazanıldığında düşmanın en güçlü kartının Size değerini -1 azaltır.",
    "Midas":         "Her gold kazanma olayında +1 ekstra gold üretir.",
    "Catalyst":      "Board'daki tüm kartlara gelir fazı başında +1 güç ekler.",
    "Eclipse":       "Savaş öncesinde düşman kartlarından birinin en yüksek kenarını sıfırlar.",
    # Genel pasif tiplerine göre fallback açıklamalar
    "gold_on_win":   "Savaş kazanıldığında bonus gold kazanır.",
    "power_on_copy": "Aynı karttan 2. kopya alındığında tüm kopyaları güçlenir.",
    "edge_debuff":   "Tetiklendiğinde düşman kartlarından birinin kenarını zayıflatır.",
    "group_synergy": "Aynı gruptaki komşu kartlarla sinerji bonusu üretir.",
    "economy":       "Gelir fazlarında ekstra gold veya faiz bonusu sağlar.",
    "survival":      "Düşük HP'de aktive olarak hasar azaltır veya iyileşir.",
}


def _wrap_text(text: str, max_chars: int) -> List[str]:
    """Uzun metni max_chars genişliğinde satırlara böler."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= max_chars:
            cur = (cur + " " + w).strip()
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ── Koordinat dönüşümleri ─────────────────────────────────────
def hex_to_pixel(q: int, r: int, ox: int, oy: int) -> Tuple[int, int]:
    x = HEX_SIZE * (3 / 2 * q)
    y = HEX_SIZE * (math.sqrt(3) / 2 * q + math.sqrt(3) * r)
    return int(ox + x), int(oy + y)


def pixel_to_hex(px: int, py: int, ox: int, oy: int) -> Tuple[int, int]:
    x = (px - ox) / HEX_SIZE
    y = (py - oy) / HEX_SIZE
    q = (2 / 3) * x
    r = (-1 / 3) * x + (math.sqrt(3) / 3) * y
    return _hex_round(q, r)


def _hex_round(q: float, r: float) -> Tuple[int, int]:
    s = -q - r
    rq, rr, rs = round(q), round(r), round(s)
    dq, dr, ds = abs(rq - q), abs(rr - r), abs(rs - s)
    if dq > dr and dq > ds:
        rq = -rr - rs
    elif dr > ds:
        rr = -rq - rs
    return rq, rr


# ── Geometri yardımcıları ─────────────────────────────────────
def _hex_corners(cx: float, cy: float, size: float) -> List[Tuple[float, float]]:
    """Flat-top hex köşe noktaları (0° = sağ, saat yönü)."""
    return [
        (cx + size * math.cos(math.radians(60 * i)),
         cy + size * math.sin(math.radians(60 * i)))
        for i in range(6)
    ]


def _edge_midpoint(corners: List, i: int) -> Tuple[float, float]:
    ax, ay = corners[i]
    bx, by = corners[(i + 1) % 6]
    return (ax + bx) / 2, (ay + by) / 2


def _toward_center(mx: float, my: float, cx: float, cy: float,
                   inset: float) -> Tuple[float, float]:
    """Kenar ortasından merkeze doğru `inset` piksel ileri git."""
    dx, dy = cx - mx, cy - my
    dist   = math.hypot(dx, dy)
    if dist == 0:
        return mx, my
    return mx + dx / dist * inset, my + dy / dist * inset


def draw_hex_flat(surface, cx, cy, size, fill, border, border_w=1):
    pts = [(int(x), int(y)) for x, y in _hex_corners(cx, cy, size)]
    pygame.draw.polygon(surface, fill, pts)
    pygame.draw.polygon(surface, border, pts, border_w)


# ── Renk yardımcıları ─────────────────────────────────────────
def _darken(color, factor: float):
    return tuple(max(0, int(c * (1 - factor))) for c in color)


def _lighten(color, factor: float):
    return tuple(min(255, int(c + (255 - c) * factor)) for c in color[:3])


def _lerp_col(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _alpha(color, value: int):
    return (color[0], color[1], color[2], max(0, min(255, value)))


def _rarity_color(rarity: str) -> Tuple[int, int, int]:
    return RARITY_COLORS.get(str(rarity), C_WHITE)


def _safe_rarity_int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 6 if str(value).upper() == "E" else 0


def _group_short(group: str) -> str:
    return {
        "EXISTENCE": "EX",
        "MIND": "MN",
        "CONNECTION": "CN",
    }.get(group, group[:2].upper())


def _wrap_text_to_width(font, text: str, max_width: int, max_lines: Optional[int] = None) -> List[str]:
    words = (text or "").split()
    if not words:
        return ["-"]
    lines: List[str] = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if font.size(trial)[0] <= max_width:
            current = trial
            continue
        if current:
            lines.append(current)
        current = word
        if max_lines is not None and len(lines) >= max_lines:
            break
    if current and (max_lines is None or len(lines) < max_lines):
        lines.append(current)
    return lines


def _truncate_to_width(font, text: str, max_width: int, suffix: str = "..") -> str:
    if font.size(text)[0] <= max_width:
        return text
    trimmed = text
    while trimmed and font.size(trimmed + suffix)[0] > max_width:
        trimmed = trimmed[:-1]
    return (trimmed + suffix) if trimmed else suffix


class CyberRenderer:
    """Shared cyberpunk/synthwave VFX layer for board and shop screens."""

    def __init__(self, fonts: Optional[Dict[str, pygame.font.Font]] = None):
        self.fonts = fonts or {}
        self.tt_alpha = 0
        self.last_card = None
        self.timer = 0.0
        self.C_RARE = C_RARE

    def set_fonts(self, fonts: Dict[str, pygame.font.Font]):
        self.fonts = fonts or {}

    def _font(self, key: str, fallback_name: str, size: int, bold: bool = False):
        if key in self.fonts:
            return self.fonts[key]
        font = pygame.font.SysFont(fallback_name, size, bold=bold)
        self.fonts[key] = font
        return font

    def draw_vfx_base(self, surface):
        """Cyber-Victorian: paslı metal doku + neon izgara + tarama çizgileri."""
        self.timer += 0.05
        w, h = surface.get_size()
        # Pirinç-rengi dikey ızgara (salınımlı opakluk)
        for x in range(0, w, 120):
            alpha = max(8, 14 + int(math.sin(self.timer + x * 0.015) * 5))
            s = pygame.Surface((1, h), pygame.SRCALPHA)
            s.fill((C_BRONZE[0], C_BRONZE[1], C_BRONZE[2], alpha))
            surface.blit(s, (x, 0))
        for y in range(0, h, 120):
            pygame.draw.line(surface, C_L_GRID, (0, y), (w, y), 1)
        # Tarama çizgileri
        for y in range(0, h, 8):
            pygame.draw.line(surface, C_L_SCAN, (0, y), (w, y), 1)

    def draw_stat_line(self, surface, card, rect):
        """Minimal vertical stat list with large total power."""
        font_xs = self._font("xs", "consolas", 12)
        font_md_bold = self._font("md_bold", "consolas", 16, bold=True)
        stats = [
            ("PW", "Power"),
            ("DR", "Durability"),
            ("SZ", "Size"),
            ("SP", "Speed"),
            ("IN", "Intelligence"),
            ("SC", "Secret"),
        ]

        for i, (short, full) in enumerate(stats):
            val = getattr(card, "stats", {}).get(full, 0)
            s_img = font_xs.render(f"{short} {val}", True, (130, 140, 160))
            surface.blit(s_img, (rect.x + 12, rect.y + 45 + (i * 18)))

        total_pwr = sum(
            value for key, value in getattr(card, "stats", {}).items()
            if not str(key).startswith("_")
        )
        pwr_img = font_md_bold.render(str(total_pwr), True, C_WHITE)
        surface.blit(pwr_img, (rect.right - pwr_img.get_width() - 15, rect.bottom - 45))
        lbl = font_xs.render("PWR", True, (100, 110, 140))
        surface.blit(lbl, (rect.right - lbl.get_width() - 15, rect.bottom - 22))

    def draw_card_tooltip(self, surface, card, mx, my, active=True):
        if not active or card is None:
            self.tt_alpha = max(0, self.tt_alpha - 30)
            return

        if self.last_card is not card:
            self.tt_alpha = 0
            self.last_card = card
        self.tt_alpha = min(245, self.tt_alpha + 35)

        rarity = str(getattr(card, "rarity", ""))
        rarity_col = C_RARE.get(rarity, C_WHITE)
        category = getattr(card, "category", "")
        category_col = get_category_color(category)
        category_icon = get_category_icon(category)
        desc = get_passive_desc(card.name, getattr(card, "passive_type", ""))

        font_title = self._font("md_bold", "consolas", 16, bold=True)
        font_body = self._font("sm", "consolas", 14)
        font_chip = self._font("xs_bold", "consolas", 12, bold=True)

        lines = _wrap_text_to_width(font_body, desc, 286, max_lines=6)
        tw = 330
        th = 88 + len(lines) * 22
        tx = mx + 24
        ty = my - th - 16 if my > surface.get_height() * 0.68 else my + 18
        if tx + tw > surface.get_width():
            tx = mx - tw - 24
        tx = max(12, tx)
        ty = max(12, min(ty, surface.get_height() - th - 12))

        tooltip = pygame.Surface((tw, th), pygame.SRCALPHA)
        pygame.draw.rect(tooltip, (7, 10, 18, self.tt_alpha), (0, 0, tw, th), border_radius=14)
        pygame.draw.rect(tooltip, _alpha(C_BRONZE, self.tt_alpha), (0, 0, tw, th), width=2, border_radius=14)
        pygame.draw.rect(tooltip, _alpha(rarity_col, self.tt_alpha), (10, 0, tw - 20, 4), border_radius=3)

        title = font_title.render(card.name.upper(), True, rarity_col)
        tooltip.blit(title, (16, 14))

        chip = pygame.Rect(16, 42, min(180, tw - 32), 22)
        pygame.draw.rect(tooltip, _alpha(_darken(category_col, 0.35), 235), chip, border_radius=10)
        pygame.draw.rect(tooltip, _alpha(category_col, 240), chip, width=1, border_radius=10)
        chip_text = font_chip.render(f"{category_icon}  {category}", True, category_col)
        tooltip.blit(chip_text, (chip.x + 10, chip.y + 4))

        info = font_chip.render(
            f"PWR {getattr(card, 'total_power', lambda: 0)()}  |  RARITY {rarity}",
            True,
            COLOR_TEXT_DIM,
        )
        tooltip.blit(info, (16, 70))

        y = 96
        for line in lines:
            body = font_body.render(line, True, (228, 232, 242))
            tooltip.blit(body, (16, y))
            y += 22

        surface.blit(tooltip, (tx, ty))

    def draw_clean_tooltip(self, surface, card, mx, my, active=True):
        self.draw_card_tooltip(surface, card, mx, my, active=active)

    def _draw_hex_card_legacy(self, surface, card, pos, r=68, is_hovered=False, highlighted=False):
        """Cyber-Victorian board karti: plazma halkalar + pirinc percinler."""
        x, y = pos
        rarity = str(getattr(card, "rarity", ""))
        color  = _rarity_color(rarity)

        # Plazma Pizzazz: donen enerji noktalar
        rot_speed = self.timer * 2.0
        n_rings   = 4 if rarity in ("4", "5", "E") else 2
        for i in range(n_rings):
            angle = rot_speed + (i * (2 * math.pi / n_rings))
            px_   = x + math.cos(angle) * (r + 7)
            py_   = y + math.sin(angle) * (r + 7)
            pygame.draw.circle(surface, color, (int(px_), int(py_)), 3)
            if is_hovered or highlighted:
                pygame.draw.line(surface, color, (x, y), (int(px_), int(py_)), 1)

        # Yuksek nadi: nabiz halkasi
        if rarity in ("4", "5", "E"):
            pulse = math.sin(self.timer * 3.0) * 1.5
            ring  = pygame.Surface((int((r + 10) * 2), int((r + 10) * 2)), pygame.SRCALPHA)
            rc    = ring.get_width() // 2
            pygame.draw.circle(ring, (*color, 28), (rc, rc), int(r + 5 + pulse), 2)
            surface.blit(ring, (x - rc, y - rc))

        # Pas altyapi + Pirinc cerceve
        pygame.draw.circle(surface, C_RUST,   (x, y), r + 3)
        pygame.draw.circle(surface, C_BRONZE, (x, y), r + 3, 3)
        border_w = 3 if (is_hovered or highlighted) else 1
        draw_col = color if (is_hovered or highlighted) else tuple(max(0, int(c * 0.45)) for c in color)
        pygame.draw.circle(surface, draw_col, (x, y), r + 4, border_w)

        # Pirinc percinler (6 kose)
        for a in range(0, 360, 60):
            ppx = x + int(math.cos(math.radians(a)) * r)
            ppy = y + int(math.sin(math.radians(a)) * r)
            pygame.draw.circle(surface, C_BRONZE, (ppx, ppy), 4)

        # Ic dolgu
        pygame.draw.circle(surface, (15, 18, 28), (x, y), r - 1)

        # Kart adi
        font_xs_bold = self._font("xs_bold", "consolas", 12, bold=True)
        name_txt = font_xs_bold.render(getattr(card, "name", "")[:12].upper(), True, C_WHITE)
        surface.blit(name_txt, (x - name_txt.get_width() // 2, y - 8))

    def draw_stat_bar(self, surface, x: int, y: int, label: str,
                       val: float, max_val: float, color):
        """Maksimalist Cyber-Victorian neon dolgu bari."""
        font = self._font("xs_bold", "consolas", 12, bold=True)
        lbl  = font.render(label[:3].upper(), True, color)
        surface.blit(lbl, (x, y))

        bar_x = x + 32
        bar_w = 90
        bar_h = 9
        bg_rect = pygame.Rect(bar_x, y + 2, bar_w, bar_h)
        pygame.draw.rect(surface, (40, 20, 10), bg_rect, border_radius=3)
        if max_val > 0:
            fill_w = max(0, int((val / max_val) * bar_w))
            pygame.draw.rect(surface, color, (bar_x, y + 2, fill_w, bar_h), border_radius=3)
            # Parlama seridi
            shine = pygame.Surface((fill_w, 2), pygame.SRCALPHA)
            shine.fill((255, 255, 255, 85))
            surface.blit(shine, (bar_x, y + 2))
        pygame.draw.rect(surface, C_BRONZE, bg_rect, 1, border_radius=3)
        val_img = font.render(str(int(val)), True, color)
        surface.blit(val_img, (bar_x + bar_w + 5, y))

    def draw_priority_popup(self, surface, card, mx: int, my: int):
        self.draw_card_tooltip(surface, card, mx, my, active=(card is not None))

    def draw_smart_tooltip(self, surface, card, mx, my, player_board_groups=None):
        self.draw_card_tooltip(surface, card, mx, my, active=(card is not None))

    def _draw_shop_cameo(self, surface, card, rect: pygame.Rect, hovered: bool):
        category = getattr(card, "category", "")
        category_col = get_category_color(category)
        category_icon = get_category_icon(category)
        dominant_group = getattr(card, "dominant_group", lambda: "EXISTENCE")()
        group_col = GROUP_COLORS.get(dominant_group, category_col)

        pygame.draw.rect(surface, (11, 14, 24), rect, border_radius=16)
        pygame.draw.rect(surface, _darken(category_col, 0.15), rect, width=1, border_radius=16)

        oval = pygame.Rect(rect.x + 16, rect.y + 12, rect.width - 32, rect.height - 24)
        pygame.draw.ellipse(surface, _darken(category_col, 0.55), oval)
        pygame.draw.ellipse(surface, C_BG, oval.inflate(-10, -10))
        pygame.draw.ellipse(surface, category_col, oval, 2)

        for corner in (
            (rect.x + 12, rect.y + 12),
            (rect.right - 12, rect.y + 12),
            (rect.x + 12, rect.bottom - 12),
            (rect.right - 12, rect.bottom - 12),
        ):
            pygame.draw.circle(surface, C_BRONZE, corner, 3)

        font_icon = self._font("icon", "segoeuisymbol", 36, bold=True)
        font_group = self._font("sm_bold", "consolas", 13, bold=True)

        icon_img = font_icon.render(category_icon, True, category_col)
        surface.blit(icon_img, (rect.centerx - icon_img.get_width() // 2, rect.y + 26))

        group_chip = pygame.Rect(rect.centerx - 34, rect.bottom - 52, 68, 20)
        pygame.draw.rect(surface, _darken(group_col, 0.45), group_chip, border_radius=10)
        pygame.draw.rect(surface, group_col, group_chip, width=1, border_radius=10)
        group_img = font_group.render(_group_short(dominant_group), True, group_col)
        surface.blit(group_img, (group_chip.centerx - group_img.get_width() // 2, group_chip.centery - group_img.get_height() // 2))

        if hovered:
            aura = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.ellipse(aura, _alpha(_lighten(category_col, 0.2), 18), oval.inflate(8, 8), 1)
            surface.blit(aura, rect.topleft)

    def draw_shop_stat_grid(self, surface, card, rect: pygame.Rect):
        """v3: Kartın gerçek stat seti; 0-değerler hiç çizilmez; aynı üst grup = aynı renk."""
        font_label = self._font("xs", "consolas", 11)
        font_value = self._font("xs_bold", "consolas", 12, bold=True)

        edge_source = getattr(card, "edges", None) or list(getattr(card, "stats", {}).items())
        real_stats = []
        for stat_name, value in edge_source:
            if str(stat_name).startswith("_") or value <= 0:
                continue
            real_stats.append((stat_name, value))

        # Gerçek stat'lar, 0 değerler atla
        # real_stats already normalized from card edges above
        if not real_stats:
            return

        cols    = 2
        rows    = (len(real_stats) + cols - 1) // cols
        cell_w  = (rect.width  - 6)  // cols
        cell_h  = max(28, (rect.height - 6) // max(1, rows))

        for idx, (stat_name, value) in enumerate(real_stats):
            col = idx % cols
            row = idx // cols
            cell = pygame.Rect(
                rect.x + col * cell_w,
                rect.y + row * cell_h,
                cell_w - 6, cell_h - 4,
            )
            stat_group = STAT_TO_GROUP.get(stat_name, "EXISTENCE")
            tone = GROUP_COLORS.get(stat_group, COLOR_TEXT_DIM)

            pygame.draw.rect(surface, (9, 12, 22), cell, border_radius=8)
            pygame.draw.rect(surface, _darken(tone, 0.2), cell, width=1, border_radius=8)

            short     = STAT_SHORT.get(stat_name, stat_name[:3].upper())
            label_img = font_label.render(short, True, tone)
            value_img = font_value.render(str(value), True, tone)
            surface.blit(label_img, (cell.x + 6, cell.y + 4))
            surface.blit(value_img, (cell.right  - value_img.get_width()  - 6,
                                     cell.bottom - value_img.get_height() - 4))

    def _draw_shop_passive_preview(self, surface, card, rect: pygame.Rect):
        font_body = self._font("xs", "consolas", 12)
        font_label = self._font("xs_bold", "consolas", 11, bold=True)
        desc = get_passive_desc(card.name, getattr(card, "passive_type", ""))
        lines = _wrap_text_to_width(font_body, desc, rect.width - 18, max_lines=3)

        pygame.draw.rect(surface, (10, 12, 22), rect, border_radius=10)
        pygame.draw.rect(surface, C_BRONZE, rect, width=1, border_radius=10)
        label = font_label.render("PASSIVE", True, C_BRONZE)
        surface.blit(label, (rect.x + 8, rect.y + 6))
        y = rect.y + 24
        for line in lines:
            img = font_body.render(line, True, (224, 228, 238))
            surface.blit(img, (rect.x + 8, y))
            y += 15

    def _draw_shop_cost_medallion(self, surface, rect: pygame.Rect, cost: int, affordable: bool, bought: bool, rarity_col):
        font_cost = self._font("sm_bold", "consolas", 13, bold=True)
        col = C_GOLD if affordable else C_NEON_PINK
        if bought:
            col = COLOR_TEXT_DIM

        pygame.draw.rect(surface, (8, 10, 18), rect, border_radius=11)
        pygame.draw.rect(surface, _darken(rarity_col, 0.2), rect, width=1, border_radius=11)
        cost_img = font_cost.render(f"{cost}G", True, col)
        surface.blit(cost_img, (rect.centerx - cost_img.get_width() // 2, rect.centery - cost_img.get_height() // 2))

    def draw_shop_card(self, surface, card, rect: pygame.Rect, hovered=False, bought=False, affordable=True, cost=0, alpha=255):
        """v3 Shop kartı: category ribbon, cameo, gerçek stat grid, passive preview,
        altta tarot-style title plate (kart adı + cost).
        Rarity geometry frame shop'ta da farklılaşır.
        """
        rarity       = str(getattr(card, "rarity", ""))
        rarity_col   = _rarity_color(rarity)
        rarity_level = _safe_rarity_int(rarity)
        category     = getattr(card, "category", "")
        category_col = get_category_color(category)
        category_icon = get_category_icon(category)

        layer = pygame.Surface(rect.size, pygame.SRCALPHA)
        W_    = rect.width
        H_    = rect.height
        margin = 12
        spacing = 8
        ribbon_h = 22
        cameo_h = 92
        stats_h = 92
        passive_h = 56
        plate_h = 30
        bottom_pad = 12

        # ── Arka plan ──────────────────────────────────────────
        bg = (22, 26, 40, 245) if not hovered else (32, 39, 64, 255)
        if bought:
            bg = (50, 54, 74, 240)
        pygame.draw.rect(layer, bg, (0, 0, W_, H_), border_radius=18)

        # ── Rarity geometry border ─────────────────────────────
        border_col = rarity_col if not bought else COLOR_TEXT_DIM
        bw = 3 if hovered and not bought else 2
        if rarity_level >= 3:
            pygame.draw.rect(layer, border_col, (0, 0, W_, H_), bw, border_radius=18)
            pygame.draw.rect(layer, _darken(border_col, 0.35),
                             (6, 6, W_ - 12, H_ - 12), 1, border_radius=14)
        else:
            pygame.draw.rect(layer, border_col, (0, 0, W_, H_), bw, border_radius=18)

        if rarity_level == 2:
            # Köşe tick'leri
            tick = 18
            corners_xy = [(4, 4), (W_ - 4, 4), (4, H_ - 4), (W_ - 4, H_ - 4)]
            offsets     = [(tick, 0), (-tick, 0), (tick, 0), (-tick, 0)]
            offsets_y   = [(0, tick), (0, tick), (0, -tick), (0, -tick)]
            for (cx_, cy_), (ox, oy), (ox2, oy2) in zip(corners_xy, offsets, offsets_y):
                pygame.draw.line(layer, border_col, (cx_, cy_), (cx_ + ox, cy_), 2)
                pygame.draw.line(layer, border_col, (cx_, cy_), (cx_, cy_ + oy2), 2)

        if rarity_level >= 4:
            # İç motif çizgiler (köşegen)
            mc = _darken(rarity_col, 0.42)
            pygame.draw.line(layer, mc, (0, 0), (W_, H_), 1)
            pygame.draw.line(layer, mc, (W_, 0), (0, H_), 1)

        if rarity_level >= 5:
            # Bronze/gold çift hat
            pygame.draw.rect(layer, C_GOLD, (4, 4, W_ - 8, H_ - 8), 1, border_radius=16)

        # ── Category ribbon ───────────────────────────────────
        ribbon = pygame.Rect(margin, 8, W_ - margin * 2, ribbon_h)
        pygame.draw.rect(layer, _darken(category_col, 0.4), ribbon, border_radius=9)
        pygame.draw.rect(layer, category_col, ribbon, width=1, border_radius=9)
        ribbon_font = self._font("xs_bold", "consolas", 11, bold=True)
        cat_text = _truncate_to_width(ribbon_font, f"{category_icon}  {category}", ribbon.width - 18)
        ribbon_img = ribbon_font.render(cat_text, True, category_col)
        layer.blit(ribbon_img, (ribbon.x + 8, ribbon.y + 4))

        # ── Cameo / sigil ─────────────────────────────────────
        cameo_rect = pygame.Rect(margin, ribbon.bottom + 6, W_ - margin * 2, cameo_h)
        self._draw_shop_cameo(layer, card, cameo_rect, hovered)

        # ── Stats (real, no-zero) ─────────────────────────────
        stats_rect = pygame.Rect(margin, cameo_rect.bottom + spacing, W_ - margin * 2, stats_h)
        self.draw_shop_stat_grid(layer, card, stats_rect)

        # ── Passive preview ───────────────────────────────────
        passive_rect = pygame.Rect(margin, stats_rect.bottom + spacing, W_ - margin * 2, passive_h)
        self._draw_shop_passive_preview(layer, card, passive_rect)

        # ── Tarot title plate ─────────────────────────────────
        cost_rect = pygame.Rect(W_ - margin - 56, H_ - bottom_pad - plate_h - 2, 56, 24)
        plate = pygame.Rect(margin, H_ - bottom_pad - plate_h, W_ - (margin * 2) - cost_rect.width - 8, plate_h)
        pygame.draw.rect(layer, (8, 10, 18), plate, border_radius=12)
        pygame.draw.rect(layer, _darken(rarity_col, 0.2) if not bought else COLOR_TEXT_DIM,
                         plate, width=1, border_radius=12)
        # Rarity aksan şeridi (plate üst kenarı)
        pygame.draw.rect(layer, rarity_col if not bought else COLOR_TEXT_DIM,
                         (plate.x + 12, plate.y, plate.width - 24, 3), border_radius=2)

        font_plate_name = self._font("sm_bold", "consolas", 14, bold=True)
        font_plate_cost = self._font("md_bold", "consolas", 15, bold=True)

        # Kart adı — plate içinde truncate + ortala
        name_str = _truncate_to_width(font_plate_name, getattr(card, "name", "").upper(), plate.width - 72)
        name_img = font_plate_name.render(name_str, True, C_WHITE)
        # Adı plate sol üstüne yaz
        layer.blit(name_img, (plate.centerx - name_img.get_width() // 2, plate.centery - name_img.get_height() // 2))

        # Cost — sağ taraf
        cost_col = C_GOLD if affordable and not bought else (150, 150, 160)
        cost_img = font_plate_cost.render(f"{cost}G", True, cost_col)
        layer.blit(cost_img, (plate.right - cost_img.get_width() - 10, plate.y + 7))

        # Alt satır: rarity yıldızları
        stars = "★" * min(5, rarity_level) + ("☆" * (5 - min(5, rarity_level)))
        stars = ""
        font_stars = self._font("xs", "consolas", 11)
        star_img = font_stars.render(stars, True, rarity_col if not bought else COLOR_TEXT_DIM)
        layer.blit(star_img, (plate.x + 10, plate.bottom - star_img.get_height() - 5))

        # ── "Bought" katmanı ──────────────────────────────────
        if bought:
            sold = pygame.Surface(rect.size, pygame.SRCALPHA)
            sold.fill((6, 8, 16, 120))
            layer.blit(sold, (0, 0))
            sold_text = self._font("md_bold", "consolas", 18, bold=True).render("SOLD", True, C_WHITE)
            layer.blit(sold_text, (W_ // 2 - sold_text.get_width() // 2,
                                   H_ // 2 - sold_text.get_height() // 2))

        if alpha < 255:
            layer.set_alpha(alpha)
        surface.blit(layer, rect.topleft)

    def draw_board_pizzazz(self, surface, hex_pos, rarity):
        """v3: kaldırıldı — tarot-style hex frame görsel kimliği üstlendi."""
        pass

    def _draw_tarot_frame(self, surface, cx, cy, r, rarity_col, rarity_level, highlight=False):
        """Tarot-style hex identity frame. Geometry farklaşır rarity'ye göre.

        1 : tek ince kontur
        2 : köşe tick'leri + çift kontur
        3 : çift ince kontur
        4 : çift kontur + iç motif çizgiler
        5 : köşe ornament + bronze aksan
        E (6): köşe ornament + gold aksan + diamond markers
        tüm rarity: 6 köşede minimal node noktaları
        """
        corners = _hex_corners(cx, cy, r)
        border_col = rarity_col if highlight else _darken(rarity_col, 0.15)
        bw = 3 if highlight else 2

        if rarity_level >= 3:
            outer = [(int(x), int(y)) for x, y in _hex_corners(cx, cy, r)]
            inner = [(int(x), int(y)) for x, y in _hex_corners(cx, cy, r - 5)]
            pygame.draw.polygon(surface, border_col, outer, bw)
            pygame.draw.polygon(surface, _darken(border_col, 0.35), inner, 1)
        else:
            pts = [(int(x), int(y)) for x, y in corners]
            pygame.draw.polygon(surface, border_col, pts, bw if rarity_level == 2 else 1)

        if rarity_level == 2:
            t = 0.18
            for i in range(6):
                ax, ay = corners[i]
                bx_, by_ = corners[(i + 1) % 6]
                pygame.draw.line(surface, border_col,
                                 (int(ax), int(ay)),
                                 (int(ax + (bx_ - ax) * t), int(ay + (by_ - ay) * t)), 2)
                pygame.draw.line(surface, border_col,
                                 (int(bx_), int(by_)),
                                 (int(bx_ + (ax - bx_) * t), int(by_ + (ay - by_) * t)), 2)

        if rarity_level >= 4:
            mids = [_edge_midpoint(corners, i) for i in range(6)]
            mc = _darken(rarity_col, 0.45)
            for i in range(3):
                ax, ay = mids[i]
                bx_, by_ = mids[i + 3]
                pygame.draw.line(surface, mc, (int(ax), int(ay)), (int(bx_), int(by_)), 1)

        # Rarity E (level 6) gets distinctive diamond markers at edge midpoints
        if rarity_level == 6:
            mids = [_edge_midpoint(corners, i) for i in range(6)]
            diamond_size = 5
            for mx, my in mids:
                # Draw diamond shape at each edge midpoint
                diamond_pts = [
                    (int(mx), int(my - diamond_size)),  # top
                    (int(mx + diamond_size), int(my)),  # right
                    (int(mx), int(my + diamond_size)),  # bottom
                    (int(mx - diamond_size), int(my))   # left
                ]
                pygame.draw.polygon(surface, C_GOLD, diamond_pts)
                pygame.draw.polygon(surface, border_col, diamond_pts, 1)

        # Köşe node'ları kaldırıldı - daha temiz tarot frame için

        if rarity_level >= 5:
            gold_pts = [(int(x), int(y)) for x, y in _hex_corners(cx, cy, r - 8)]
            pygame.draw.polygon(surface, C_GOLD, gold_pts, 1)

    def draw_hex_card(self, surface, card, pos, r=68, is_hovered=False, highlighted=False):
        """v3 Board kartı: tarot-style hex frame, kenar statı metin+shadow.

        Kaldırılanlar: circular aura, glow ring, center circle/medallion,
                       header chip, power circle, kutulu stat badge.
        Eklenenler  : _draw_tarot_frame, edge-near stat text, minimal passive dot.
        """
        x, y = pos
        rarity        = str(getattr(card, "rarity", ""))
        rarity_col    = _rarity_color(rarity)
        rarity_level  = _safe_rarity_int(rarity)
        dominant_group = getattr(card, "dominant_group", lambda: "EXISTENCE")()
        highlight = is_hovered or highlighted

        # Hex gövde dolgu
        body_pts = [(int(px), int(py)) for px, py in _hex_corners(x, y, r - 6)]
        pygame.draw.polygon(surface, C_PANEL_2, body_pts)

        # Tarot kimlik frame’i
        self._draw_tarot_frame(surface, x, y, r - 6, rarity_col, rarity_level, highlight)

        # Kart adı — merkez
        font_name = self._font("xs_bold", "consolas", 11, bold=True)
        name_raw  = getattr(card, "name", "")
        name_img  = font_name.render(_truncate_to_width(font_name, name_raw[:16].upper(), 78, ""), True, C_WHITE)
        surface.blit(name_img, (x - name_img.get_width() // 2, y - name_img.get_height() // 2))

        # Grup kısaltması (ismin hemen altı)
        # no secondary center badge; frame and edge labels carry identity

        # Kenar stat değleri — edge midpoint’ine yakın, text shadow, kutu yok
        corners    = _hex_corners(x, y, r - 6)
        edges      = getattr(card, "rotated_edges", lambda: [])()
        font_stat  = self._font("xs_bold", "consolas", 12, bold=True)
        for index, (stat_name, value) in enumerate(edges[:6]):
            if str(stat_name).startswith("_") or value == 0:
                continue
            mp          = _edge_midpoint(corners, index)
            lp          = _toward_center(mp[0], mp[1], x, y, EDGE_LABEL_INSET)
            stat_group  = STAT_TO_GROUP.get(stat_name, dominant_group)
            stat_col    = GROUP_COLORS.get(stat_group, rarity_col)
            val_str     = str(value)
            val_img     = font_stat.render(val_str, True, stat_col)
            vx = int(lp[0] - val_img.get_width()  / 2)
            vy = int(lp[1] - val_img.get_height() / 2)
            shadow_img  = font_stat.render(val_str, True, (0, 0, 0))
            for sdx, sdy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                surface.blit(shadow_img, (vx + sdx, vy + sdy))
            surface.blit(val_img, (vx, vy))

        # Passive göstergesi — sağ üst köşede minimal nokta
        if getattr(card, "passive_type", "") not in ("", "none"):
            px_ = x + int(r * 0.52)
            py_ = y - int(r * 0.52)
            pygame.draw.circle(surface, rarity_col, (px_, py_), 4)
            pygame.draw.circle(surface, C_BG,        (px_, py_), 2)

# ══════════════════════════════════════════════════════════════
#  BOARD RENDERER
# ══════════════════════════════════════════════════════════════
class BoardRenderer:
    def __init__(self, origin: Tuple[int, int], player_strategy: str = "random",
                 cyber_renderer: Optional[CyberRenderer] = None):
        self.ox, self.oy = origin
        self.strategy    = player_strategy
        self.cyber_renderer = cyber_renderer
        self.font_val    = None   # kenar değer fontu (küçük, bold)
        self.font_name   = None   # merkez kart adı
        self.font_tiny   = None   # tooltip içeriği
        self.hovered     = None   # (q, r)
        self.hovered_card = None

        # Hover tooltip yüzeyi (board dışına taşabilir)
        self._tooltip_surf  = None
        self._tooltip_pos   = (0, 0)
        self._tooltip_card  = None

    def init_fonts(self):
        self.font_val  = pygame.font.SysFont("segoeui", 15, bold=True)
        self.font_name = pygame.font.SysFont("segoeui", 15, bold=True)
        self.font_tiny = pygame.font.SysFont("segoeui", 13)

    def update_hover(self, mouse_pos: Tuple[int, int], board_coords):
        mx, my = mouse_pos
        q, r   = pixel_to_hex(mx, my, self.ox, self.oy)
        self.hovered = (q, r) if (q, r) in board_coords else None

    # ── Tüm board ────────────────────────────────────────────
    def _draw_legacy(self, surface, board, board_coords, locked_coords=None,
             show_tooltip: bool = True):
        """Render board.
        
        locked_coords: set of (q,r) coords that are locked (can't be moved).
        """
        if locked_coords is None:
            locked_coords = set()
        self._tooltip_card = None
        self.hovered_card = None

        for (q, r) in board_coords:
            cx, cy = hex_to_pixel(q, r, self.ox, self.oy)
            card   = board.grid.get((q, r))
            hover  = (self.hovered == (q, r))
            locked = (q, r) in locked_coords

            if card:
                dom  = card.dominant_group()
                fill = _darken(GROUP_COLORS.get(dom, (80, 80, 120)), 0.35)
                bord = GROUP_COLORS.get(dom, (80, 80, 120))
                bw   = 3 if locked else 2
            elif hover:
                fill, bord, bw = COLOR_HOVER, (100, 140, 200), 2
            else:
                fill, bord, bw = COLOR_EMPTY, COLOR_BORDER, 1

            # Hex background artık tarot frame tarafından çiziliyor
            # draw_hex_flat kaldırıldı - daha temiz görünüm için

            # Kilitli kart köşe işareti
            if card and locked:
                self._draw_lock_indicator(surface, cx, cy)

            if card:
                if self.cyber_renderer is not None:
                    self.cyber_renderer.draw_hex_card(surface, card, (cx, cy), r=HEX_SIZE, is_hovered=hover)
                # ESKİ _draw_card_hex çağrısı kaldırıldı - yeni tarot frame kullanılıyor
                if hover:
                    self.hovered_card = card
                    self._tooltip_card = card
                    self._tooltip_pos  = (cx, cy)

        # Sinerji çizgileri (kartlar arasında eşleşen kenarlar)
        self._draw_synergy_lines(surface, board, board_coords)

        # Tooltip en üstte çizilir
        if show_tooltip and self._tooltip_card:
            self._draw_tooltip(surface, self._tooltip_pos, self._tooltip_card)

    def _draw_lock_indicator(self, surface, cx, cy):
        """Kilitli kart için küçük kilit ikonu (sol üst köşe)."""
        size = HEX_INNER
        corners = _hex_corners(cx, cy, size)
        # Sol üst kenarın ortası (direction 5=NW kenarı)
        ax, ay = corners[5]
        bx, by = corners[0]
        lx, ly = int((ax + bx) / 2), int((ay + by) / 2)
        pygame.draw.circle(surface, (200, 160, 40), (lx, ly), 5)

    # ── Sinerji çizgisi ──────────────────────────────────────
    def _draw_synergy_lines(self, surface, board, board_coords):
        """Komşu hexler arasında aynı grup kenarları eşleşiyorsa enerji çizgisi çizer."""
        HEX_DIRS = [(1,0),(1,-1),(0,-1),(-1,0),(-1,1),(0,1)]
        OPP      = [3, 4, 5, 0, 1, 2]   # karşı yön indeksleri
        drawn    = set()
        for (q, r) in board_coords:
            card = board.grid.get((q, r))
            if not card:
                continue
            rot_edges = card.rotated_edges()
            cx, cy = hex_to_pixel(q, r, self.ox, self.oy)
            for d, (dq, dr) in enumerate(HEX_DIRS):
                nc = (q + dq, r + dr)
                if nc not in board.grid:
                    continue
                pair = tuple(sorted([(q,r), nc]))
                if pair in drawn:
                    continue
                drawn.add(pair)
                ncx, ncy = hex_to_pixel(nc[0], nc[1], self.ox, self.oy)
                n_card    = board.grid[nc]
                n_rot     = n_card.rotated_edges()
                # Bu kenar çifti: card'ın d yönü ↔ komşunun OPP[d] yönü
                my_stat,   my_val  = rot_edges[d]  if d  < len(rot_edges) else ("", 0)
                opp_stat,  opp_val = n_rot[OPP[d]] if OPP[d] < len(n_rot) else ("", 0)
                if my_val <= 0 or opp_val <= 0:
                    continue
                from engine_core.constants import STAT_TO_GROUP
                g1 = STAT_TO_GROUP.get(my_stat,  "")
                g2 = STAT_TO_GROUP.get(opp_stat, "")
                if g1 != g2:
                    continue
                # Aynı grup → sinerji var, çizgi çiz
                col = GROUP_COLORS.get(g1, (160, 160, 160))
                # İnce parlayan çizgi
                mx, my_ = (cx + ncx) // 2, (cy + ncy) // 2
                pygame.draw.line(surface, col, (int(cx), int(cy)), (int(ncx), int(ncy)), 2)
                pygame.draw.circle(surface, col, (int(mx), int(my_)), 3)

    # ── ESKİ _draw_card_hex metodu kaldırıldı - yeni tarot frame kullanılıyor ──

    def draw_placement_preview(self, surface, cx: int, cy: int, card, rotation: int):
        """
        Yerleştirme öncesi rotasyon önizlemesi.
        Kartın rotasyon=`rotation` halinde kenarlarını gösterir.
        """
        size    = float(HEX_INNER)
        corners = _hex_corners(cx, cy, size)
        n       = len(card.edges)

        for i in range(6):
            # Rotasyon uygulanmış kenar indeksi
            base_idx  = (i - rotation) % n if n > 0 else 0
            stat_name, val = card.edges[base_idx] if base_idx < n else ("", 0)
            if str(stat_name).startswith("_"):
                continue

            group = _STAT_GROUP.get(stat_name, "EXISTENCE")
            gcol  = GROUP_COLORS.get(group, (120, 120, 120))
            col   = gcol if val > 0 else _darken(gcol, 0.6)

            ax, ay = corners[i]
            bx, by = corners[(i + 1) % 6]
            pygame.draw.line(surface, col,
                             (int(ax), int(ay)), (int(bx), int(by)), 2)

            if self.font_val and val > 0:
                emx, emy = _edge_midpoint(corners, i)
                lx, ly   = _toward_center(emx, emy, cx, cy, EDGE_LABEL_INSET)
                val_s = self.font_val.render(str(val), True, col)
                vx    = int(lx - val_s.get_width()  / 2)
                vy    = int(ly - val_s.get_height() / 2)
                bg_s  = pygame.Surface((val_s.get_width() + 2, val_s.get_height() + 2),
                                       pygame.SRCALPHA)
                bg_s.fill((0, 0, 0, 140))
                surface.blit(bg_s, (vx - 1, vy - 1))
                surface.blit(val_s, (vx, vy))

        # Merkez rotasyon bilgisi
        if self.font_name:
            rot_lbl = self.font_name.render(f"↻ {rotation * 60}°", True, COLOR_ROT_PREVIEW)
            surface.blit(rot_lbl, (int(cx - rot_lbl.get_width() / 2),
                                    int(cy - rot_lbl.get_height() / 2)))

    # ── Hover Tooltip (hex dışı, büyük bilgi kutusu) ──────────
    def _draw_tooltip(self, surface, pos, card):
        if not self.font_tiny:
            return

        cx, cy = pos
        W, H   = surface.get_size()

        # Passive açıklaması varsa daha geniş/uzun tooltip
        has_passive = card.passive_type and card.passive_type != "none"
        passive_desc = PASSIVE_DESCS.get(card.name, "") or PASSIVE_DESCS.get(card.passive_type, "")
        passive_lines = _wrap_text(passive_desc, 26) if passive_desc else []

        TW  = 220
        TH  = 180 + len(passive_lines) * 14
        PAD = 8

        # Kutu konumu: hexin sağ üstüne, ekrandan taşmayacak şekilde
        tx = cx + HEX_SIZE + 6
        ty = cy - TH // 2
        if tx + TW > W:
            tx = cx - HEX_SIZE - 6 - TW
        ty = max(4, min(ty, H - TH - 4))

        # Arka plan — hafif blur etkisi için çift katman
        bg = pygame.Surface((TW, TH), pygame.SRCALPHA)
        bg.fill((8, 10, 20, 230))
        surface.blit(bg, (tx, ty))

        dom  = card.dominant_group()
        gcol = GROUP_COLORS.get(dom, COLOR_TEXT)
        pygame.draw.rect(surface, gcol,
                         (tx, ty, TW, TH), 2, border_radius=8)

        # Rarity şeridi (üst)
        rc = RARITY_COLORS.get(card.rarity, COLOR_TEXT_DIM)
        pygame.draw.rect(surface, rc, (tx + 6, ty, TW - 12, 4), border_radius=2)

        y = ty + PAD + 4

        # Kart adı (büyük)
        name_s = self.font_name.render(card.name[:22], True, COLOR_TEXT)
        surface.blit(name_s, (tx + PAD, y));  y += name_s.get_height() + 2

        # Kategori + toplam güç + rotasyon
        rot_deg  = card.rotation * 60
        cat_col  = CATEGORY_COLORS.get(card.category, COLOR_TEXT_DIM)
        info     = f"{card.category[:16]}  ·  PWR {card.total_power()}  ↻{rot_deg}°"
        info_s   = self.font_tiny.render(info, True, cat_col)
        surface.blit(info_s, (tx + PAD, y));  y += info_s.get_height() + 5

        # Ayırıcı
        pygame.draw.line(surface, _darken(gcol, 0.35),
                         (tx + PAD, y), (tx + TW - PAD, y), 1)
        y += 4

        # Rotasyona göre her stat + yön
        rot_edges = card.rotated_edges()
        for d, (stat_name, val) in enumerate(rot_edges[:6]):
            if str(stat_name).startswith("_") or val == 0:
                continue
            sg    = _STAT_GROUP.get(stat_name, "EXISTENCE")
            scol  = GROUP_COLORS.get(sg, COLOR_TEXT_DIM)
            short = STAT_SHORT.get(stat_name, stat_name[:2])
            dir_lbl = DIR_LABELS[d]
            row   = f"{dir_lbl}:{short}  {val}"
            rs    = self.font_tiny.render(row, True, scol)
            surface.blit(rs, (tx + PAD, y))
            y    += rs.get_height() + 2
            if y > ty + TH - PAD - 30:
                break

        # Passive bölümü
        if has_passive:
            pygame.draw.line(surface, _darken(gcol, 0.35),
                             (tx + PAD, y), (tx + TW - PAD, y), 1)
            y += 4
            full_desc = get_passive_desc(card.name, card.passive_type)
            desc_lines = _wrap_text(full_desc, 28)
            ph = self.font_tiny.render("✦ PASSIVE", True, gcol)
            surface.blit(ph, (tx + PAD, y));  y += ph.get_height() + 2
            for line in desc_lines:
                if y + 14 > ty + TH - 4:
                    break
                ls = self.font_tiny.render(line, True, _lerp_col(COLOR_TEXT_DIM, gcol, 0.3))
                surface.blit(ls, (tx + PAD + 4, y));  y += 14

    def _card_groups(self, card) -> set:
        groups = set()
        for stat_name, value in getattr(card, "stats", {}).items():
            if value <= 0 or str(stat_name).startswith("_"):
                continue
            group = STAT_TO_GROUP.get(stat_name)
            if group:
                groups.add(group)
        return groups

    def _draw_socket(self, surface, cx, cy, card, hover: bool, highlighted: bool):
        base = STRATEGY_COLORS.get(self.strategy, C_CYAN)
        border = base if not card else _lerp_col(base, _rarity_color(str(card.rarity)), 0.45)
        if hover:
            border = C_CYAN
        if highlighted:
            border = C_PINK

        glow = pygame.Surface((180, 180), pygame.SRCALPHA)
        gc = glow.get_width() // 2
        for radius in range(68, 30, -6):
            alpha = 10 if not (hover or card or highlighted) else max(8, 24 - radius // 4)
            pygame.draw.circle(glow, _alpha(border, alpha), (gc, gc), radius)
        surface.blit(glow, (cx - gc, cy - gc), special_flags=pygame.BLEND_ADD)

        outer = [(int(px), int(py)) for px, py in _hex_corners(cx, cy, HEX_SIZE - 2)]
        mid = [(int(px), int(py)) for px, py in _hex_corners(cx, cy, HEX_SIZE - 10)]
        inner = [(int(px), int(py)) for px, py in _hex_corners(cx, cy, HEX_SIZE - 18)]

        pygame.draw.polygon(surface, _darken(border, 0.55), outer)
        pygame.draw.polygon(surface, border, outer, 3 if (hover or highlighted or card) else 2)
        pygame.draw.polygon(surface, (15, 33, 52), mid)
        pygame.draw.polygon(surface, _darken(border, 0.2), mid, 1)
        pygame.draw.polygon(surface, (8, 20, 34), inner)

        for angle in (0, 120, 240):
            orb_x = cx + int(math.cos(math.radians(angle)) * (HEX_SIZE - 8))
            orb_y = cy + int(math.sin(math.radians(angle)) * (HEX_SIZE - 8))
            pygame.draw.circle(surface, _darken(border, 0.15), (orb_x, orb_y), 5)
            pygame.draw.circle(surface, border, (orb_x, orb_y), 3)

    def draw(self, surface, board, board_coords, locked_coords=None,
             show_tooltip: bool = True):
        """Render board with optional synergy-group highlight support."""
        if locked_coords is None:
            locked_coords = set()
        self._tooltip_card = None
        self.hovered_card = None
        highlight_group = getattr(self, "highlight_group", None)

        for (q, r) in board_coords:
            cx, cy = hex_to_pixel(q, r, self.ox, self.oy)
            card = board.grid.get((q, r))
            hover = (self.hovered == (q, r))
            locked = (q, r) in locked_coords

            highlighted = highlight_group is not None and card is not None and highlight_group in self._card_groups(card)
            self._draw_socket(surface, cx, cy, card, hover, highlighted)

            if card and locked:
                self._draw_lock_indicator(surface, cx, cy)

            if card:
                if self.cyber_renderer is not None:
                    self.cyber_renderer.draw_hex_card(
                        surface,
                        card,
                        (cx, cy),
                        r=HEX_SIZE,
                        is_hovered=hover,
                        highlighted=highlighted,
                    )
                # ESKİ _draw_card_hex çağrısı kaldırıldı - yeni tarot frame kullanılıyor
                if hover:
                    self.hovered_card = card
                    self._tooltip_card = card
                    self._tooltip_pos = (cx, cy)

        self._draw_synergy_lines(surface, board, board_coords)

        if show_tooltip and self._tooltip_card:
            if self.cyber_renderer is not None:
                mx, my = pygame.mouse.get_pos()
                self.cyber_renderer.draw_card_tooltip(surface, self._tooltip_card, mx, my, active=True)
            else:
                self._draw_tooltip(surface, self._tooltip_pos, self._tooltip_card)
