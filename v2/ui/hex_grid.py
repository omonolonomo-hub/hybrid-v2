import math
import pygame

from v2.constants import GridMath, Layout

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
    """Alpha kanallı (SRCALPHA) çizgi — geçici yüzey üzerinden blitlenir."""
    x1, y1 = int(start[0]), int(start[1])
    x2, y2 = int(end[0]), int(end[1])
    pad = width + 2
    min_x = min(x1, x2) - pad
    min_y = min(y1, y2) - pad
    w = max(x1, x2) - min_x + pad
    h = max(y1, y2) - min_y + pad
    if w <= 0 or h <= 0:
        return
    tmp = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.line(
        tmp, color_rgba,
        (x1 - min_x, y1 - min_y),
        (x2 - min_x, y2 - min_y),
        width,
    )
    surface.blit(tmp, (min_x, min_y))


def _draw_circle_alpha(
    surface: pygame.Surface,
    color_rgba: tuple,
    center: tuple,
    radius: int,
) -> None:
    """Alpha kanallı daire — uç nokta vurgusu için."""
    cx, cy = int(center[0]), int(center[1])
    r = radius + 2
    tmp = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    pygame.draw.circle(tmp, color_rgba, (r, r), radius)
    surface.blit(tmp, (cx - r, cy - r))


def render_synergy_lines(
    surface: pygame.Surface,
    adjacency_pairs: list,
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

    from v2.constants import Colors, Layout

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

        x1, y1 = axial_to_pixel(*coord_a)
        x2, y2 = axial_to_pixel(*coord_b)

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
) -> None:
    """
    Sürüklenen kartın hover ettiği hex'e yerleşince oluşturacağı
    kenar-kenar eşleşmelerini ghost olarak gösterir.
    - drag_rotation: sürüklenen kartın şu anki rotasyonu (0-5)
    - board_rotations: {(q,r): int} board'daki her kartın rotasyonu
    Sadece aynı grup eşleşmeleri (synergy) için çizgi çizilir.
    """
    if hover_coord not in VALID_HEX_COORDS:
        return

    from v2.constants import Colors, Layout, ENGINE_HEX_DIRS, OPP_DIR, STAT_TO_GROUP
    from v2.core.card_database import CardDatabase

    if board_rotations is None:
        board_rotations = {}

    try:
        db = CardDatabase.get()
    except RuntimeError:
        return

    drag_data = db.lookup(card_name)
    if not drag_data:
        return
    drag_edges = list(drag_data.stats.items())  # [(stat_name, val), ...] len=6, orijinal sıra
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
    cx, cy  = axial_to_pixel(q, r)
    found   = False

    for dir_idx, (dq, dr) in enumerate(ENGINE_HEX_DIRS):
        nb = (q + dq, r + dr)
        if nb not in board_cards:
            continue
        item = board_cards[nb]
        nb_card_name = item.get("name") if isinstance(item, dict) else item
        nb_data = db.lookup(nb_card_name)
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

        nx, ny = axial_to_pixel(*nb)
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

def render_ghost_preview(surface: pygame.Surface, card_name: str, mouse_pos: tuple[int, int], rotation: int = 0):
    """
    Sürüklenen kartın (hand/shop) altındaki hex grid üzerinde 
    %60 saydam önizlemesini ve kenar statlarını (edge stats) çizer.
    rotation: mevcut rotasyon adımı (0-5), her adım 60° döndürür.
    """
    from v2.core.card_database import CardDatabase
    from v2.constants import GridMath, Colors
    from v2.ui import font_cache
    
    # 1. Mouse altındaki en yakın hex'i bul
    q, r = pixel_to_axial(mouse_pos[0], mouse_pos[1])
    
    # 2. Hex geçerli mi (aktif board içinde mi)?
    is_valid = (q, r) in VALID_HEX_COORDS
    
    # 3. Hex merkezini bul (ekran koordinatı)
    cx, cy = axial_to_pixel(q, r)
    
    zoom = GridMath.camera.zoom
    radius = GridMath.HEX_SIZE * zoom
    
    # 4. Ghost Kart Render (Hafif saydam)
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
    
    # Dolgu (Şeffaflık için temp surface)
    temp_surf = pygame.Surface((radius*4, radius*4), pygame.SRCALPHA)
    lx, ly = radius*2, radius*2
    local_points = [(p[0]-cx+lx, p[1]-cy+ly) for p in points]
    ghost_color = (60, 80, 120, alpha) if is_valid else (180, 60, 60, alpha)
    pygame.draw.polygon(temp_surf, ghost_color, local_points)
    surface.blit(temp_surf, (cx-lx, cy-ly))

    # 5. Edge Stats Overlay (Sadece valid ise)
    if is_valid and card_data:
        raw_stats = getattr(card_data, "stats", {})
        if not raw_stats:
            stat_values = [(hash(card_name + str(i)) % 9) + 1 for i in range(6)]
        else:
            stat_values = list(raw_stats.values())
        
        # Stat rengini belirle
        color = (255, 255, 255)
        
        # CardData içindeki synergy_group veya category'den grubu bul
        group = getattr(card_data, "synergy_group", "").upper()
        if not group:
            category = getattr(card_data, "category", "")
            from v2.core.card_database import CATEGORY_TO_SYNERGY
            group = CATEGORY_TO_SYNERGY.get(category, "").upper()

        if group == "MIND": color = Colors.MIND
        elif group == "CONNECTION": color = Colors.CONNECTION
        elif group == "EXISTENCE": color = Colors.EXISTENCE

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
            
            # Label render
            font_size = max(8, int(14 * zoom))
            font = font_cache.mono(font_size)
            
            # Shadow
            shadow_surf = font.render(str(stat_val), True, (10, 10, 15))
            sw, sh = shadow_surf.get_size()
            surface.blit(shadow_surf, (int(sx - sw//2 + 1), int(sy - sh//2 + 1)))
            
            # Text
            text_surf = font.render(str(stat_val), True, color)
            tw, th = text_surf.get_size()
            surface.blit(text_surf, (int(sx - tw//2), int(sy - th//2)))

def render_hex_grid(surface: pygame.Surface):
    """
    Board üzerindeki aktif (board) hücreleri "A2 Premium" stiliyle çizer.
    """
    from v2.ui.ui_utils import UIUtils

    # UI panelleri için clip rect (Board panellerin altına girmesin)
    # Shop panel altı ile Hand panel üstü arasını temiz bir alan olarak tanımlıyoruz
    center_rect = pygame.Rect(
        Layout.CENTER_ORIGIN_X,
        Layout.SHOP_PANEL_Y + Layout.SHOP_PANEL_H + 5,
        Layout.CENTER_W,
        Layout.HAND_PANEL_Y - (Layout.SHOP_PANEL_Y + Layout.SHOP_PANEL_H) - 10
    )
    
    # Board render alanı sınırlama
    old_clip = surface.get_clip()
    surface.set_clip(center_rect)

    zoom = GridMath.camera.zoom
    radius = GridMath.HEX_SIZE * zoom
    
    # Sadece aktif (board) hücreleri "A2 Premium" stiliyle çiz
    for q, r in VALID_HEX_COORDS:
        cx, cy = axial_to_pixel(q, r)
        
        # Görünürlük kontrolü (Merkez nokta veya köşelerden biri clip içindeyse çiz)
        if (center_rect.collidepoint(cx, cy) or 
            center_rect.collidepoint(cx + radius, cy) or 
            center_rect.collidepoint(cx - radius, cy) or
            center_rect.collidepoint(cx, cy + radius) or
            center_rect.collidepoint(cx, cy - radius)):
            
            # 1. Hücre Geometrisi
            points = []
            for i in range(6):
                angle = math.radians(60 * i - 30)
                px = cx + (radius - 1) * math.cos(angle)
                py = cy + (radius - 1) * math.sin(angle)
                points.append((int(px), int(py)))
            
            # 2. Glass Inset (Hafif şeffaf dolgu)
            # Katmanlı bir derinlik hissi için iki kademeli dolgu
            pygame.draw.polygon(surface, (20, 25, 40, 80), points)
            
            # 3. Premium Neon Kenarlık (Zoom'a göre kalınlık ayarı)
            border_w = max(1, int(2 * zoom))
            pygame.draw.polygon(surface, (42, 58, 92, 180), points, border_w)

    surface.set_clip(old_clip)

def axial_to_pixel(q: int, r: int) -> tuple[float, float]:
    """Converts coordinate from Axial to center pixel rendering location with camera support."""
    zoom = GridMath.camera.zoom
    off_x = GridMath.camera.offset_x
    off_y = GridMath.camera.offset_y
    
    # Base unscaled position
    base_x = GridMath.HEX_SIZE * (math.sqrt(3) * q + math.sqrt(3) / 2 * r)
    base_y = GridMath.HEX_SIZE * (3 / 2 * r)
    
    # Apply zoom and offset
    x = (base_x * zoom) + GridMath.ORIGIN_X + off_x
    y = (base_y * zoom) + GridMath.ORIGIN_Y + off_y
    
    return x, y

def pixel_to_axial(px: float, py: float) -> tuple[int, int]:
    """Converts a mouse pixel click location to the nearest axial hex grid location with camera support."""
    zoom = GridMath.camera.zoom
    off_x = GridMath.camera.offset_x
    off_y = GridMath.camera.offset_y
    
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

VALID_HEX_COORDS: set[tuple[int,int]] = {
    (q, r) for q in range(-3, 4) for r in range(-3, 4)
    if abs(q) <= 3 and abs(r) <= 3 and abs(q + r) <= 3
}

HEX_DIRECTION_MAP = {
    0: (1, -1),
    1: (1, 0),
    2: (0, 1),
    3: (-1, 1),
    4: (-1, 0),
    5: (0, -1)
}
