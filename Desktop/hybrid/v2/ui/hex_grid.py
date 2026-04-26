import math
import pygame
import pygame.gfxdraw
from typing import Any

from v2.constants import CameraState, GridMath, Layout, Colors, ENGINE_HEX_DIRS, OPP_DIR, STAT_TO_GROUP
from v2.core.card_database import CardDatabase, CATEGORY_TO_SYNERGY
from v2.core.exceptions import AutochessException
from v2.ui import font_cache
from v2.ui.hex_grid_config import HexGridConfig, get_default_config

# Backward compatibility: module-level __getattr__ for lazy loading
# This allows existing code to use "from v2.ui.hex_grid import VALID_HEX_COORDS"
# without triggering engine initialization at import time
def __getattr__(name):
    """Lazy module attribute access for backward compatibility."""
    if name == "VALID_HEX_COORDS":
        return get_default_config().valid_coords
    elif name == "BOARD_RADIUS":
        return get_default_config().board_radius
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

# ──────────────────────────────────────────────────────────────────────────────
# Synergy Bağlantı Çizgileri
# ──────────────────────────────────────────────────────────────────────────────

def _draw_line_alpha(
    surface: pygame.Surface,
    color_rgba: tuple,
    start: tuple,
    end: tuple,
    width: int,
) -> None:
    """
    Alpha kanallı çizgi — pygame.gfxdraw kullanarak optimize edilmiştir.
    Her çağrıda yeni Surface oluşturmak yerine doğrudan hedef yüzeye çizer.
    """
    x1, y1 = start
    x2, y2 = end
    
    if width <= 1:
        pygame.gfxdraw.line(surface, int(x1), int(y1), int(x2), int(y2), color_rgba)
        return

    # Kalın çizgiyi poligon olarak çiz (gfxdraw.line genişlik desteklemez)
    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy)
    if length == 0:
        return

    # Normal vektör (genişlik/2 kadar öteleme için)
    nx = -dy / length * (width / 2.0)
    ny =  dx / length * (width / 2.0)

    points = [
        (x1 + nx, y1 + ny),
        (x1 - nx, y1 - ny),
        (x2 - nx, y2 - ny),
        (x2 + nx, y2 + ny)
    ]
    
    # Kenar yumuşatma ve dolgu
    pygame.gfxdraw.filled_polygon(surface, points, color_rgba)
    pygame.gfxdraw.aapolygon(surface, points, color_rgba)


def _draw_circle_alpha(
    surface: pygame.Surface,
    color_rgba: tuple,
    center: tuple,
    radius: int,
) -> None:
    """Alpha kanallı daire — pygame.gfxdraw ile optimize edilmiştir."""
    cx, cy = int(center[0]), int(center[1])
    if radius <= 0:
        return
    pygame.gfxdraw.filled_circle(surface, cx, cy, radius, color_rgba)
    pygame.gfxdraw.aacircle(surface, cx, cy, radius, color_rgba)


def render_synergy_lines(
    surface: pygame.Surface,
    adjacency_pairs: list,
    camera: CameraState,
) -> None:
    """
    Kenar bazlı synergy görsellemesi.

    adjacency_pairs: GameState.get_adjacency_pairs() çıktısı
        → [(coord_a, coord_b, group_a, group_b), ...]
          group_a = A'nın B'ye bakan kenar stat grubu
          group_b = B'nin A'ya bakan kenar stat grubu

    Sadece group_a == group_b olan çiftler için çizgi çizilir (gerçek synergy).
    Farklı grup çiftleri motor açısından işlevsiz — görsel olarak da gösterilmez.
    """
    if not adjacency_pairs:
        return

    GROUP_COL = {
        "EXISTENCE": Colors.EXISTENCE,
        "MIND":      Colors.MIND,
        "CONNECTION": Colors.CONNECTION,
    }

    t          = pygame.time.get_ticks() / 1000.0
    pulse_slow = 0.55 + 0.45 * math.sin(t * 1.8)
    pulse_fast = 0.70 + 0.30 * math.sin(t * 5.0)

    clip_rect = pygame.Rect(
        Layout.CENTER_ORIGIN_X,
        Layout.SHOP_PANEL_Y + Layout.SHOP_PANEL_H + 5,
        Layout.CENTER_W,
        Layout.HAND_PANEL_Y - (Layout.SHOP_PANEL_Y + Layout.SHOP_PANEL_H) - 10,
    )
    old_clip = surface.get_clip()
    surface.set_clip(clip_rect)

    # Bağlantı yoğunluğu → chain çarpanı (sadece synergy çiftleri sayılır)
    conn_count: dict = {}
    for ca, cb, ga, gb in adjacency_pairs:
        if ga == gb:  # sadece gerçek synergy bağlantıları
            conn_count[ca] = conn_count.get(ca, 0) + 1
            conn_count[cb] = conn_count.get(cb, 0) + 1

    for coord_a, coord_b, group_a, group_b in adjacency_pairs:
        # Farklı grup → çizgi yok
        if group_a != group_b:
            continue

        col_a = GROUP_COL.get(group_a, (180, 180, 180))

        max_conn   = max(conn_count.get(coord_a, 1), conn_count.get(coord_b, 1))
        chain_mult = 1.0 + 0.35 * min(max_conn - 1, 3)

        x1, y1 = axial_to_pixel(*coord_a, camera)
        x2, y2 = axial_to_pixel(*coord_b, camera)

        # ── Synergy: tek renk, daha parlak ve kalın ────────────────────────
        r, g, b = col_a
        a0 = int(35 * pulse_slow * chain_mult)
        w0 = max(12, int(18 * chain_mult))
        _draw_line_alpha(surface, (r, g, b, min(a0, 90)),  (x1,y1), (x2,y2), w0)
        a1 = int(130 * pulse_slow * chain_mult)
        w1 = max(5,  int(7  * chain_mult))
        _draw_line_alpha(surface, (r, g, b, min(a1, 200)), (x1,y1), (x2,y2), w1)
        a2 = int(230 * pulse_fast)
        _draw_line_alpha(surface, (r, g, b, min(a2, 255)), (x1,y1), (x2,y2), 2)

        # ── Uç nokta vurgusu ────────────────────────────────────────────────
        dot_r = max(4, int(6 * chain_mult))
        dot_a = int(180 * pulse_fast)
        bright = tuple(min(255, int(c * 1.4)) for c in col_a)
        _draw_circle_alpha(surface, (*bright, dot_a), (x1, y1), dot_r)
        _draw_circle_alpha(surface, (*bright, dot_a), (x2, y2), dot_r)

    surface.set_clip(old_clip)


def render_synergy_preview(
    surface: pygame.Surface,
    hover_coord: tuple,
    card_name: str,
    board_cards: dict,
    drag_rotation: int = 0,
    board_rotations: dict = None,
    card_data: any = None,
    camera: CameraState = None,
    config: HexGridConfig = None,
) -> None:
    """
    Sürüklenen kartın hover ettiği hex'e yerleşince oluşturacağı
    kenar-kenar eşleşmelerini ghost olarak gösterir.
    - drag_rotation: sürüklenen kartın şu anki rotasyonu (0-5)
    - board_rotations: {(q,r): int} board'daki her kartın rotasyonu
    - card_data: Dışarıdan sağlanan kart verisi (isteğe bağlı)
    - config: HexGridConfig instance (defaults to engine config)
    Sadece aynı grup eşleşmeleri (synergy) için çizgi çizilir.
    """
    if config is None:
        config = get_default_config()
    
    if hover_coord not in config.valid_coords:
        return

    if board_rotations is None:
        board_rotations = {}

    try:
        db = CardDatabase.get()
    except AutochessException:
        return

    # 1. Kart verisini bul (Dışardan gelmemişse lookup yap)
    if card_data is None:
        card_data = db.lookup(card_name)

    if not card_data:
        return

    drag_edges = list(card_data.stats.items())  # [(stat_name, val), ...] len=6, orijinal sıra
    if len(drag_edges) < 6:
        return

    GROUP_COL = {
        "EXISTENCE": Colors.EXISTENCE,
        "MIND":      Colors.MIND,
        "CONNECTION": Colors.CONNECTION,
    }

    t     = pygame.time.get_ticks() / 1000.0
    pulse = 0.45 + 0.35 * math.sin(t * 4.0)

    clip_rect = pygame.Rect(
        Layout.CENTER_ORIGIN_X,
        Layout.SHOP_PANEL_Y + Layout.SHOP_PANEL_H + 5,
        Layout.CENTER_W,
        Layout.HAND_PANEL_Y - (Layout.SHOP_PANEL_Y + Layout.SHOP_PANEL_H) - 10,
    )
    old_clip = surface.get_clip()
    surface.set_clip(clip_rect)

    q, r    = hover_coord
    cx, cy  = axial_to_pixel(q, r, camera)
    found   = False

    for dir_idx, (dq, dr) in enumerate(ENGINE_HEX_DIRS):
        nb = (q + dq, r + dr)
        if nb not in board_cards:
            continue
        
        # Optimization: board_cards can be Dict[Coord, CardData] (board_card_info)
        # or Dict[Coord, Dict] (board_cards)
        item = board_cards[nb]
        if hasattr(item, "stats"): # CardData object
            nb_data = item
        elif isinstance(item, dict): # ViewState dict
            nb_card_name = item.get("name")
            nb_data = db.lookup(nb_card_name) if nb_card_name else None
        else: # Just a string name
            nb_data = db.lookup(item) if item else None

        if not nb_data:
            continue
        nb_edges = list(nb_data.stats.items())
        if len(nb_edges) < 6:
            continue

        # Rotation uygulaması: (dir_idx - rotation) % 6 → gerçek kenar indeksi
        real_drag_idx = (dir_idx - drag_rotation) % 6
        rot_nb        = board_rotations.get(nb, 0)
        real_nb_idx   = (OPP_DIR[dir_idx] - rot_nb) % 6

        group_drag = STAT_TO_GROUP.get(drag_edges[real_drag_idx][0], "")
        group_nb   = STAT_TO_GROUP.get(nb_edges[real_nb_idx][0], "")
        same       = (group_drag == group_nb)

        nx, ny = axial_to_pixel(*nb, camera)
        found  = True

        if same:
            col = GROUP_COL.get(group_drag, (180, 180, 180))
            rc, gc, bc = col
            _draw_line_alpha(surface, (rc, gc, bc, int(50*pulse)),  (cx,cy), (nx,ny), 14)
            _draw_line_alpha(surface, (rc, gc, bc, int(110*pulse)), (cx,cy), (nx,ny), 5)
            _draw_line_alpha(surface, (rc, gc, bc, int(180*pulse)), (cx,cy), (nx,ny), 2)

            # Komşu nokta vurgusu (sadece synergy)
            bright_nb = tuple(min(255, int(c*1.3)) for c in col)
            _draw_circle_alpha(surface, (*bright_nb, int(140*pulse)), (nx, ny), 5)
        # Farklı grup → önizlemede de çizgi yok

    # Sürüklenen kartın potansiyel konumu (en az bir komşu varsa)
    if found:
        _draw_circle_alpha(surface, (220, 220, 255, int(200*pulse)), (cx, cy), 8)

    surface.set_clip(old_clip)

_GHOST_TXT_CACHE: dict[tuple, pygame.Surface] = {}
_GHOST_TXT_CACHE_MAX = 256  # Hard cap to prevent unbounded growth

def _get_cached_ghost_text(txt: str, color: tuple, font_size: int, font) -> pygame.Surface:
    """
    Get or create cached text surface with bounded cache size.
    When cache exceeds max size, evict half the entries (simple FIFO-style).
    """
    key = (txt, color, font_size)
    
    if key not in _GHOST_TXT_CACHE:
        # Cache full → evict half the entries
        if len(_GHOST_TXT_CACHE) >= _GHOST_TXT_CACHE_MAX:
            keys = list(_GHOST_TXT_CACHE.keys())
            for k in keys[:len(keys) // 2]:
                del _GHOST_TXT_CACHE[k]
        
        _GHOST_TXT_CACHE[key] = font.render(txt, True, color)
    
    return _GHOST_TXT_CACHE[key]

def render_ghost_preview(
    surface: pygame.Surface, 
    card_name: str, 
    mouse_pos: tuple[int, int], 
    rotation: int = 0,
    card_data: Any = None,
    camera: CameraState = None,
    config: HexGridConfig = None,
):
    """
    Sürüklenen kartın (hand/shop) altındaki hex grid üzerinde 
    %60 saydam önizlemesini ve kenar statlarını (edge stats) çizer.
    rotation: mevcut rotasyon adımı (0-5), her adım 60° döndürür.
    config: HexGridConfig instance (defaults to engine config)
    """
    if config is None:
        config = get_default_config()
    
    # 1. Mouse altındaki en yakın hex'i bul
    q, r = pixel_to_axial(mouse_pos[0], mouse_pos[1], camera)
    
    # 2. Hex geçerli mi (aktif board içinde mi)?
    is_valid = (q, r) in config.valid_coords
    
    # 3. Hex merkezini bul (ekran koordinatı)
    cx, cy = axial_to_pixel(q, r, camera)
    
    zoom = camera.zoom
    radius = GridMath.HEX_SIZE * zoom
    
    # 4. Ghost Kart Render (Hafif saydam)
    if card_data is None:
        db = CardDatabase.get()
        card_data = db.lookup(card_name)
    
    alpha = 153 if is_valid else 76 # %60 valid, %30 invalid
    
    # Hayalet hex poligonu
    points = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        px = cx + radius * math.cos(angle)
        py = cy + radius * math.sin(angle)
        points.append((int(px), int(py)))
    
    ghost_color = (60, 80, 120, alpha) if is_valid else (180, 60, 60, alpha)
    pygame.gfxdraw.filled_polygon(surface, points, ghost_color)
    pygame.gfxdraw.aapolygon(surface, points, ghost_color)

    # 5. Edge Stats Overlay (Sadece valid ise)
    if is_valid and card_data:
        raw_stats = getattr(card_data, "stats", {})
        if not raw_stats:
            # Veri yoksa sahte üretmek yerine 0 göstererek dürüst davranalım
            stat_values = [0] * 6
        else:
            stat_values = list(raw_stats.values())
        
        # Stat rengini belirle
        color = (255, 255, 255)
        
        # CardData içindeki synergy_group veya category'den grubu bul
        group = getattr(card_data, "synergy_group", "").upper()
        if not group:
            category = getattr(card_data, "category", "")
            group = CATEGORY_TO_SYNERGY.get(category, "").upper()

        if group == "MIND": color = Colors.MIND
        elif group == "CONNECTION": color = Colors.CONNECTION
        elif group == "EXISTENCE": color = Colors.EXISTENCE

        # Optimization: Get font once per frame, not inside loop
        font_size = max(8, int(14 * zoom))
        font = font_cache.mono(font_size)

        for i in range(6):
            # Kenar etiketi konumu: rotation * 60° döndür
            angle_deg = 60 * i + rotation * 60
            angle_rad = math.radians(angle_deg)
            
            # Kenar ortası uzaklığı: radius * cos(30°)
            dist = radius * 0.866
            sx = cx + dist * math.cos(angle_rad)
            sy = cy + dist * math.sin(angle_rad)
            
            # Rotasyona göre hangi orijinal kenar bu pozisyona geldi
            real_i   = (i - rotation) % 6
            stat_val = stat_values[real_i] if real_i < len(stat_values) else 0
            
            # Label render (Shadow + Text) with Caching
            txt = str(stat_val)
            
            # Use bounded cache helper
            shadow_surf = _get_cached_ghost_text(txt, (10, 10, 15), font_size, font)
            sw, sh = shadow_surf.get_size()
            surface.blit(shadow_surf, (int(sx - sw//2 + 1), int(sy - sh//2 + 1)))
            
            text_surf = _get_cached_ghost_text(txt, color, font_size, font)
            tw, th = text_surf.get_size()
            surface.blit(text_surf, (int(sx - tw//2), int(sy - th//2)))

def render_hex_grid(surface: pygame.Surface, board_cards: dict | None = None, camera: CameraState = None, config: HexGridConfig = None):
    """
    Board üzerindeki aktif (board) hücreleri "DCI Premium" stiliyle çizer.
    Glow, Depth ve Breathing efektleri içerir.
    config: HexGridConfig instance (defaults to engine config)
    """
    if board_cards is None:
        board_cards = {}
    
    if config is None:
        config = get_default_config()
    
    # ── 1. Render Alanı Sınırlama ────────────────────────────────────
    center_rect = pygame.Rect(
        Layout.CENTER_ORIGIN_X,
        Layout.SHOP_PANEL_Y + Layout.SHOP_PANEL_H + 5,
        Layout.CENTER_W,
        Layout.HAND_PANEL_Y - (Layout.SHOP_PANEL_Y + Layout.SHOP_PANEL_H) - 10
    )
    old_clip = surface.get_clip()
    surface.set_clip(center_rect)

    # ── 2. Global Animasyon & Mouse State ─────────────────────────────
    t = pygame.time.get_ticks() / 1000.0
    mouse_pos = pygame.mouse.get_pos()
    mouse_q, mouse_r = pixel_to_axial(*mouse_pos, camera)
    
    zoom = camera.zoom
    base_radius = GridMath.HEX_SIZE * zoom
    
    # ── 3. Hex Grid Çizimi ───────────────────────────────────────────
    for q, r in config.valid_coords:
        cx, cy = axial_to_pixel(q, r, camera)
        
        # Görünürlük kontrolü
        if not (center_rect.collidepoint(cx, cy) or 
                center_rect.collidepoint(cx + base_radius, cy) or 
                center_rect.collidepoint(cx - base_radius, cy)):
            continue
            
        is_hover  = (q, r) == (mouse_q, mouse_r)
        is_filled = (q, r) in board_cards
        
        # Mikro-Animasyon: Breathing (Nefes Alma)
        # Sadece boş hücreler veya hover olanlar hafifçe nefes alır
        breath_val = 0.97 + 0.03 * math.sin(t * 1.5 + q*0.4 + r*0.4)
        radius = base_radius * breath_val if not is_filled else base_radius
        
        # 4. Geometri Hazırlığı
        points = []
        inner_points = []
        for i in range(6):
            angle = math.radians(60 * i - 30)
            # Dış Sınır
            px = cx + radius * math.cos(angle)
            py = cy + radius * math.sin(angle)
            points.append((int(px), int(py)))
            # İç Sınır (Highlight için)
            ix = cx + (radius * 0.85) * math.cos(angle)
            iy = cy + (radius * 0.85) * math.sin(angle)
            inner_points.append((int(ix), int(iy)))

        # 5. [LAYER 1] Outer Glow (KALDIRILDI)
        
        # 6. [LAYER 2] Glass Body (Gövde Derinliği - Dengeli Karbon-Mor)
        # Karbon ve mor arası dengeli ton
        base_alpha = 140 if is_filled else 30
        body_col = (16, 13, 20, base_alpha)  # Karbon-mor dengeli
            
        pygame.draw.polygon(surface, body_col, points)
        # Inner Gradient/Highlight Simülasyonu
        inner_alpha = 80 if is_filled else 20
        inner_col = (25, 21, 31, inner_alpha)  # Dengeli highlight
        pygame.draw.polygon(surface, inner_col, inner_points)

        # 7. [LAYER 3] Tactical Borders (Kenarlıklar - Dengeli Neon)
        # Hover durumunda dengeli mor-gri neon
        border_col = (105, 78, 135, 180) if is_hover else (50, 41, 61, 100)  # Orta ton
        border_w = max(1, int(2 * zoom))
        
        # Dış Neon
        pygame.draw.polygon(surface, border_col, points, border_w)
        # İç Highlight (Rim Light - Dengeli)
        if is_hover or is_filled:
            pygame.draw.polygon(surface, (145, 120, 175, 100), inner_points, 1)  # Dengeli highlight

    surface.set_clip(old_clip)

def axial_to_pixel(q: int, r: int, camera: CameraState) -> tuple[float, float]:
    """Converts coordinate from Axial to center pixel rendering location with camera support."""
    zoom = camera.zoom
    off_x = camera.offset_x
    off_y = camera.offset_y
    
    # Base unscaled position
    base_x = GridMath.HEX_SIZE * (math.sqrt(3) * q + math.sqrt(3) / 2 * r)
    base_y = GridMath.HEX_SIZE * (3 / 2 * r)
    
    # Apply zoom and offset
    x = (base_x * zoom) + GridMath.ORIGIN_X + off_x
    y = (base_y * zoom) + GridMath.ORIGIN_Y + off_y
    
    return x, y

def pixel_to_axial(px: float, py: float, camera: CameraState) -> tuple[int, int]:
    """Converts a mouse pixel click location to the nearest axial hex grid location with camera support."""
    zoom = camera.zoom
    off_x = camera.offset_x
    off_y = camera.offset_y
    
    # Reverse offset and zoom
    px -= (GridMath.ORIGIN_X + off_x)
    py -= (GridMath.ORIGIN_Y + off_y)
    
    px /= zoom
    py /= zoom
    
    q_f = (math.sqrt(3) / 3 * px - 1 / 3 * py) / GridMath.HEX_SIZE
    r_f = (2 / 3 * py) / GridMath.HEX_SIZE
    
    return _hex_round(q_f, r_f)

def _hex_round(q_f: float, r_f: float) -> tuple[int, int]:
    s_f = -q_f - r_f
    q, r, s = round(q_f), round(r_f), round(s_f)
    dq, dr, ds = abs(q - q_f), abs(r - r_f), abs(s - s_f)
    if dq > dr and dq > ds: 
        q = -r - s
    elif dr > ds:            
        r = -q - s
    return q, r

# VALID_HEX_COORDS is defined at the top of the file via EngineAdapter

HEX_DIRECTION_MAP = {i: d for i, d in enumerate(ENGINE_HEX_DIRS)}
