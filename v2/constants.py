import os

def _load_env_file(path: str = ".env"):
    """Dış bağımlılık (dotenv) gerektirmeden basit .env fallback okuması."""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, _, val = line.partition("=")
                    key = key.strip()
                    # LEAK KORUMASI: Sadece eğer sistemde override edilmemişse .env'den oku
                    if key not in os.environ:
                        os.environ[key] = val.strip()

_load_env_file()

class Config:
    DEBUG_MODE: bool = os.environ.get("DEBUG_MODE", "False").lower() == "true"
    VSYNC: int       = int(os.environ.get("VSYNC", "1"))
    FPS: int         = int(os.environ.get("FPS", "60"))

class Screen:
    W: int = 1920
    H: int = 1080

class Layout:
    LEFT_PANEL_W: int    = 280
    RIGHT_PANEL_W: int   = 280
    SIDEBAR_LEFT_W: int  = LEFT_PANEL_W
    SIDEBAR_RIGHT_W: int = RIGHT_PANEL_W
    SIDEBAR_RIGHT_X: int = Screen.W - RIGHT_PANEL_W
    PLAYER_HUB_H: int    = 150
    SYNERGY_HUD_Y: int   = 150
    LOBBY_ROW_H: int     = 70
    CENTER_W: int        = Screen.W - LEFT_PANEL_W - RIGHT_PANEL_W - 30
    CENTER_ORIGIN_X: int = LEFT_PANEL_W + 15
    CENTER_ORIGIN_Y: int = 15
    SYNERGY_HUD_H: int   = 320
    COMBAT_TERM_H: int   = Screen.H - SYNERGY_HUD_H
    HAND_PANEL_H: int    = 180
    HAND_PANEL_Y: int    = Screen.H - HAND_PANEL_H - 15
    HAND_CARD_W: int     = 140
    HAND_CARD_H: int     = 160
    HAND_CARD_GAP: int   = 16
    HAND_MAX_CARDS: int  = 6
    HAND_INFO_W: int     = 340
    SHOP_PANEL_H: int    = 180
    SHOP_PANEL_Y: int    = 15
    SHOP_CARD_W: int     = 140
    SHOP_CARD_H: int     = 160
    SHOP_CARD_GAP: int   = 16
    SHOP_SLOTS: int      = 5
    SHOP_INFO_W: int     = 340
    REROLL_BTN_X: int    = CENTER_ORIGIN_X + CENTER_W - 160
    REROLL_BTN_Y: int    = SHOP_PANEL_Y + 40
    REROLL_BTN_W: int    = 140
    REROLL_BTN_H: int    = 44
    LOCK_BTN_H: int      = 34

class CameraState:
    offset_x: float = 0.0
    offset_y: float = 0.0
    zoom: float = 1.0
    MIN_ZOOM: float = 0.5
    MAX_ZOOM: float = 2.5

class GridMath:
    HEX_SIZE: int = 54
    ORIGIN_X: int = Layout.CENTER_ORIGIN_X + (Layout.CENTER_W // 2)
    ORIGIN_Y: int = 520

    # Kamera objesi (Singleton benzeri global erişim için)
    camera = CameraState()

class Typography:
    FONT_UI_REGULAR: str = "Inter-Regular.ttf"
    FONT_UI_BOLD: str    = "Inter-Bold.ttf"
    FONT_MONO: str       = "JetBrainsMono-Regular.ttf"
    SIZE_BODY: int       = 15
    SIZE_LABEL: int      = 13
    SIZE_HEADER: int     = 20
    SIZE_LARGE: int      = 28

# Stat → Grup eşlemesi (engine_core/constants.py ile birebir eş)
STAT_TO_GROUP: dict[str, str] = {
    "Power":        "EXISTENCE", "Durability": "EXISTENCE",
    "Size":         "EXISTENCE", "Speed":       "EXISTENCE",
    "Meaning":      "MIND",      "Secret":       "MIND",
    "Intelligence": "MIND",      "Trace":        "MIND",
    "Gravity":      "CONNECTION", "Harmony":     "CONNECTION",
    "Spread":       "CONNECTION", "Prestige":    "CONNECTION",
}
# Grup üstnük taş-kağıt-makas
GROUP_BEATS: dict[str, str] = {
    "EXISTENCE": "CONNECTION",
    "MIND":      "EXISTENCE",
    "CONNECTION": "MIND",
}
# Engine kenar yönleri (axial) — index = yön numarası (N=0, NE=1, SE=2, S=3, SW=4, NW=5)
ENGINE_HEX_DIRS: list[tuple[int, int]] = [
    (0,-1), (1,-1), (1,0), (0,1), (-1,1), (-1,0)
]
OPP_DIR: dict[int, int] = {0:3, 1:4, 2:5, 3:0, 4:1, 5:2}

class Colors:
    MIND: tuple[int, int, int]        = (80,  140, 255)
    CONNECTION: tuple[int, int, int]  = (60,  200, 100)
    EXISTENCE: tuple[int, int, int]   = (220,  60,  60)
    DISABLED: tuple[int, int, int]    = (90,   90,  90)
    PLATINUM: tuple[int, int, int]    = (220, 220, 240)
    GOLD_TEXT: tuple[int, int, int]   = (255, 210,  60)
    HP_FULL: tuple[int, int, int]     = (60,  200, 100)
    HP_LOW: tuple[int, int, int]      = (220,  60,  60)
    TERMINAL_BG: tuple[int, int, int] = (15,   15,  20)
    TERMINAL_FG: tuple[int, int, int] = (180, 220, 180)
    GHOST_ALPHA: int                  = 153

class Timing:
    FLOAT_TEXT_RISE_PX_PER_SEC: int = 60      # legacy — yeni kod RISE_PX_S kullanır
    FLOAT_TEXT_LIFETIME_MS: int     = 1400    # legacy — yeni kod _total_lifetime kullanır
    FLOAT_TEXT_FADE_START_MS: int   = 900     # legacy

    # ── 3-Faz FloatingText parametreleri ─────────────────────────────
    FLOAT_TEXT_RISE_PX_S:       int = 80   # yükselme hızı (px/s)
    FLOAT_TEXT_MAX_RISE_PX:     int = 80   # en fazla kaç px yükseleceği
    FLOAT_TEXT_HOLD_MS:         int = 650  # max yükseklikte bekleme süresi (ms)
    FLOAT_TEXT_FADE_MS:         int = 550  # solma süresi (ms)
    # rise_duration = MAX_RISE_PX / RISE_PX_S * 1000 = 80/80*1000 = 1000 ms
    # toplam ömür   = 1000 + 650 + 550 = 2200 ms

    # ── Vagon kuyruğu gecikmesi ───────────────────────────────────────
    FLOAT_TEXT_WAGON_DELAY_MS:  int = 220  # aynı coord_key'deki ardışık metinler arası gecikme

    SPLASH_DURATION_MS: int         = 3000
    AI_TURN_MAX_MS: int             = 2000
    DEBUG_TERMINAL_TICK_RATE: int   = 80

class Paths:
    BASE_ASSETS: str = "v2/assets"
    FONTS: str       = "v2/assets/fonts"
    SPRITES: str     = "v2/assets/sprites"
    SFX: str         = "v2/assets/sfx"
    MUSIC: str       = "v2/assets/music"

class AudioConfig:
    MASTER: float = 0.8
    SFX: float    = 0.5
    MUSIC: float  = 0.6
