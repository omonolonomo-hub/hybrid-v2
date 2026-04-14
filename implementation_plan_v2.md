# V2 REBORN: STRICT TECHNICAL IMPLEMENTATION BLUEPRINT (AGENT-READY) — REV 2

This document is the official technical specification for implementing the `v2` 1920x1080 graphical client on top of the `engine_core` simulation. It is strictly engineered for AI agent execution. Every section is written as an unambiguous contract; if a field is not listed here it does not exist. Agents MUST NOT infer or hallucinate missing values — if an ambiguity is found, execution stops and the ambiguity is flagged.

---

## 0. TECHNOLOGY STACK & PROJECT CONSTANTS (FOUNDATIONAL — READ FIRST)

### 0.1 <span style="color:#4ade80">Canonical Tech Stack (🟩 TAMAMLANDI)</span>

| Layer | Choice | Rationale |
|---|---|---|
| Language | Python 3.11+ | Matches `engine_core` runtime |
| Rendering framework | **Pygame-CE 2.4+** (`pygame-ce`) | Hardware-accelerated surfaces, direct pixel control, `pygame.Surface` compositing, maintained fork of pygame |
| Window target | 1920×1080 @ **60 FPS** | `pygame.display.set_mode((1920, 1080), pygame.HWSURFACE \| pygame.DOUBLEBUF)` |
| Delta time unit | **milliseconds (ms)** as `float`; produced by `pygame.Clock.tick(60)` |
| Asset format — sprites | PNG with alpha channel (RGBA) |
| Asset format — fonts | TTF loaded via `pygame.font.Font` |
| Asset format — audio | OGG Vorbis for music, WAV for SFX |
| Coordinate system | Pygame standard: origin top-left, x right, y down |
| Hex coordinate system | **Axial (q, r)** — see Section 0.4 |

**HARD RULE:** Do NOT import `pygame` from any `engine_core` module. The engine is UI-agnostic. All pygame calls live exclusively inside `v2/`.

### 0.2 Directory Structure

```diff
  v2/
  ├── core/
  │   ├── game_state.py        # GameState singleton
  │   ├── scene_manager.py     # SceneManager + Scene base class
+ │   ├── event_bus.py         # Internal UI event system
  │   └── clock.py             # DeltaClock wrapper
  ├── scenes/
  │   ├── lobby.py
  │   ├── shop.py
  │   ├── versus_splash.py
  │   ├── combat.py
  │   └── endgame.py
  ├── ui/
+ │   ├── hex_grid.py          # HexGrid math + rendering
  │   ├── hand_panel.py
  │   ├── shop_panel.py
  │   ├── player_hub.py
  │   ├── synergy_hud.py
  │   ├── combat_terminal.py
  │   ├── income_preview.py
  │   └── widgets.py           # Button, Bar, FloatingText, Icon primitives
+ ├── assets/
+ │   ├── loader.py            # AssetLoader singleton
+ │   ├── sprites/             # PNG files
+ │   ├── fonts/               # TTF files
+ │   └── sfx/                 # WAV / OGG files
+ ├── constants.py             # ALL layout, color, timing constants
  ├── debug_overlay.py         # Dev-mode overlay
  ├── mock/
  │   └── engine_mock.py       # Engine stub for UI-isolated testing
  └── main.py                  # Entry point
```

### 0.3 Layout Constants (`v2/constants.py`) — SINGLE SOURCE OF TRUTH

All pixel values are defined here. No magic numbers anywhere else in the codebase. Agents MUST import from this file.

```python
# --- Screen ---
SCREEN_W = 1920
SCREEN_H = 1080
FPS      = 60

# --- Panel layout (all values in pixels) ---
LEFT_PANEL_W    = 280          # Synergy HUD + Combat Terminal
RIGHT_PANEL_W   = 280          # Player Hub
CENTER_W        = SCREEN_W - LEFT_PANEL_W - RIGHT_PANEL_W   # 1360
CENTER_ORIGIN_X = LEFT_PANEL_W                               # 280
CENTER_ORIGIN_Y = 0

# --- Left panel zones ---
SYNERGY_HUD_H   = 320          # top of left panel
COMBAT_TERM_H   = SCREEN_H - SYNERGY_HUD_H   # 760

# --- Hand panel (bottom of center) ---
HAND_PANEL_H    = 180
HAND_PANEL_Y    = SCREEN_H - HAND_PANEL_H    # 900
HAND_CARD_W     = 120
HAND_CARD_H     = 160
HAND_CARD_GAP   = 12
HAND_MAX_CARDS  = 7

# --- Shop panel (top of center, shown only in Shop scene) ---
SHOP_PANEL_H    = 180
SHOP_PANEL_Y    = 0
SHOP_CARD_W     = 140
SHOP_CARD_H     = 160
SHOP_CARD_GAP   = 16
SHOP_SLOTS      = 5

# --- Hex board (center) ---
# See GridMath for unified camera-aware constants
HEX_ORIGIN_Y    = 520          # board center y (vertical midpoint of center zone)

# --- Player Hub (right panel) ---
HUB_ROW_H       = SCREEN_H // 8   # 135 px per player row
HUB_HP_BAR_W    = 160
HUB_HP_BAR_H    = 14
HUB_GOLD_FONT_SIZE = 16

# --- Income Breakdown (below gold counter in Shop) ---
INCOME_PREVIEW_X = CENTER_ORIGIN_X + 20
INCOME_PREVIEW_Y = 50
INCOME_FONT_SIZE  = 14

# --- Reroll button ---
REROLL_BTN_X    = CENTER_ORIGIN_X + CENTER_W - 160
REROLL_BTN_Y    = SHOP_PANEL_Y + SHOP_PANEL_H + 10
REROLL_BTN_W    = 140
REROLL_BTN_H    = 44

# --- Floating text animation ---
FLOAT_TEXT_RISE_PX_PER_SEC  = 60
FLOAT_TEXT_LIFETIME_MS       = 1400
FLOAT_TEXT_FADE_START_MS     = 900

# --- Versus Splash ---
SPLASH_DURATION_MS  = 3000
SPLASH_HP_BAR_W     = 400
SPLASH_HP_BAR_H     = 36

# --- Timing ---
AI_TURN_MAX_MS  = 2000    # hard timeout for all 7 AI turns combined

# --- Colors (R, G, B) ---
COLOR_MIND       = (80,  140, 255)
COLOR_CONNECTION = (60,  200, 100)
COLOR_EXISTENCE  = (220,  60,  60)
COLOR_DISABLED   = (90,   90,  90)
COLOR_PLATINUM   = (220, 220, 240)
COLOR_GOLD_TEXT  = (255, 210,  60)
COLOR_HP_FULL    = (60,  200, 100)
COLOR_HP_LOW     = (220,  60,  60)
COLOR_GHOST_ALPHA= 153    # 60% of 255
COLOR_TERMINAL_BG= (15,   15,  20)
COLOR_TERMINAL_FG= (180, 220, 180)

# --- Font paths (relative to v2/assets/fonts/) ---
FONT_UI_REGULAR  = "Inter-Regular.ttf"
FONT_UI_BOLD     = "Inter-Bold.ttf"
FONT_MONO        = "JetBrainsMono-Regular.ttf"  # Combat Terminal only
FONT_SIZE_BODY   = 15
FONT_SIZE_LABEL  = 13
FONT_SIZE_HEADER = 20
FONT_SIZE_LARGE  = 28

### 0.4 Hex Grid Math & Unified Camera Specification

**Coordinate system: Axial (q, r).** Pointy-Top orientation. Grid shape: Radius-3, 37 hexes total (`|q| <= 3`, `|r| <= 3`, `|q+r| <= 3`).

**Unified Camera State:**
```python
class CameraState:
    offset_x: float = 0.0
    offset_y: float = 0.0
    zoom: float     = 1.0
    MIN_ZOOM: float = 0.5
    MAX_ZOOM: float = 2.5
```

**Axial → Pixel (center of hex) with Camera Support:**
```python
def axial_to_pixel(q: int, r: int) -> tuple[float, float]:
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
```

**Pixel → Axial (mouse position to nearest hex) with Camera Support:**
```python
def pixel_to_axial(px: float, py: float) -> tuple[int, int]:
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
    return _hex_round(q_f, r_f)   # cube rounding, convert back to axial
```
def _hex_round(q_f, r_f):
    s_f = -q_f - r_f
    q, r, s = round(q_f), round(r_f), round(s_f)
    dq, dr, ds = abs(q - q_f), abs(r - r_f), abs(s - s_f)
    if dq > dr and dq > ds: q = -r - s
    elif dr > ds:            r = -q - s
    return q, r
```

**Direction → Edge index mapping (Pointy-Top, 6 edges):**

| Direction index | Angle (degrees) | Edge label | Axial neighbor delta |
|---|---|---|---|
| 0 | 30° (Top-Right) | NE | (+1, -1) |
| 1 | 90° (Right) | E | (+1, 0) |
| 2 | 150° (Bottom-Right) | SE | (0, +1) |
| 3 | 210° (Bottom-Left) | SW | (-1, +1) |
| 4 | 270° (Left) | W | (-1, 0) |
| 5 | 330° (Top-Left) | NW | (0, -1) |

`pending_rotation = N` means direction 0 (NE edge) is rotated by `N * 60°` clockwise. Edge index for the rotated direction 0 becomes `(0 + N) % 6`.

**Valid hex set** — precompute at startup:
```python
VALID_HEX_COORDS: set[tuple[int,int]] = {
    (q, r) for q in range(-3, 4) for r in range(-3, 4)
    if abs(q) <= 3 and abs(r) <= 3 and abs(q + r) <= 3
}
```

---

## 1. GAME ORCHESTRATION & PREP TIMING (CRITICAL)

### 1.1 The Strict Phase Pipeline

Execution order is deterministic and sequential within a single thread. Steps 1-6 run on the main thread. AI execution (Step 4) runs synchronously but is time-bounded.

1. **Turn Start (Economy & Windows):** Call `engine.income()` for ALL 8 players. Immediately call `engine.market.deal_market_window()` for ALL 8 players. These two calls are always paired. UI reads updated gold and market state via `GameState.sync_state()` after both calls complete.
2. **Human Prep (Shop Scene):** Human player interacts with Shop/Hand. Pool depletes in real time as cards are bought — after each `buy_card()` success, the Shop panel re-renders the affected slot as empty without waiting for a full `sync_state()` cycle.
3. **Commitment (Ready Button):** Human clicks "Ready", OR the optional prep timer expires. Either event triggers `GameState.commit_human_turn()`.
4. **AI Execution:** `GameState.run_ai_turns()` is called. This method loops over the 7 bot players and calls `player.run_ai_turn()` for each sequentially. Total wall time is capped at `AI_TURN_MAX_MS = 2000 ms`. If any bot exceeds its share, it is skipped and logged as a warning. This runs **synchronously on the main thread** — the UI displays a non-interactive "Opponents deciding..." overlay (see Section 3.2) during this window. No pygame event processing occurs during AI execution.
5. **Pairing:** Call `engine.swiss_pairings()`. Store result in `GameState.current_pairings: list[tuple[int, int]]`.
6. **Transition:** `SceneManager.transition_to(VersusScene)`.

### 1.2 Handshake Logistics

- **Combat → Prep:** After `engine.combat_phase()` resolves and damage is applied, call `engine.clear_boards()`. Then increment `GameState.turn_counter`. Call `player.synergy_matrix.decay()` for ALL active (non-eliminated) players. Then loop to Step 1.
- **Elimination check:** After damage application, evaluate `player.hp <= 0` for all players. Eliminated players are flagged `GameState.eliminated: set[int]`. They are excluded from subsequent `run_ai_turn()` calls and `synergy_matrix.decay()` calls.
- **Game-end check:** If `len(alive_players) <= 1` OR `GameState.turn_counter == 50`, call `SceneManager.transition_to(EndgameScene)` instead of looping.

---

## 2. STATE MANAGEMENT & ENGINE INTEGRATION

### 2.1 `GameState` Wrapper

**Role:** Singleton. Owns the single `engine_core.game.Game` instance. All UI code accesses engine state exclusively through this wrapper. Direct imports of `engine_core` from scene or UI files are FORBIDDEN.

**Error code enum** — all mutating methods return this, never a bare `bool`:

```python
from enum import IntEnum

class ActionResult(IntEnum):
    OK              = 0
    ERR_INSUFFICIENT_GOLD  = 1
    ERR_SLOT_OCCUPIED      = 2
    ERR_POOL_EMPTY         = 3
    ERR_INVALID_COORD      = 4
    ERR_PLACE_LOCKED       = 5
    ERR_INVALID_HAND_IDX   = 6
    ERR_NOT_IN_PREP_PHASE  = 7
    ERR_ENGINE_EXCEPTION   = 99   # wraps unexpected engine exceptions
```

**Full method contract:**

```python
class GameState:
    _instance: 'GameState | None' = None

    # --- Lifecycle ---
    @classmethod
    def get(cls) -> 'GameState': ...          # singleton accessor

    def initialize(self, strategy_idx: int) -> None:
        # Calls engine.setup(strategy_idx). Resets all UI state fields.
        # MUST be called exactly once before any other method.

    def sync_state(self) -> None:
        # Reads engine.players[*].hp, .gold, .stats into local cache.
        # Called at the start of each scene's update() loop.
        # Does NOT trigger any engine mutation.

    # --- Human turn actions (all check phase; return ERR_NOT_IN_PREP_PHASE if called outside prep) ---
    def buy_card(self, shop_index: int) -> ActionResult:
        # Validates: 0 <= shop_index < 5, slot not empty, player.gold >= card.cost.
        # On OK: calls engine.buy(shop_index), decrements local gold cache, marks slot empty.

    def place_card(self, hand_index: int, coord: tuple[int,int], rotation: int) -> ActionResult:
        # Validates: hand_index in range, coord in VALID_HEX_COORDS, coord unoccupied,
        #            place_locked == False, 0 <= rotation <= 5.
        # On OK: calls engine.place(hand_index, coord, rotation).
        #         Sets self.place_locked = True immediately.

    def reroll(self) -> ActionResult:
        # Validates: player.gold >= 2.
        # On OK: calls engine.market.reroll(), triggers full shop panel re-render signal.

    def commit_human_turn(self) -> None:
        # Sets self.in_prep_phase = False. Triggers AI execution pipeline.

    def run_ai_turns(self) -> None:
        # See Section 1.1 Step 4. Time-bounded. Does NOT return until all bots done or timeout.

    # --- Read-only accessors (never mutate engine) ---
    def get_board(self, pid: int) -> dict:         # engine.get_player(pid).board
    def get_hand(self, pid: int) -> list:          # engine.get_player(pid).hand
    def get_shop(self) -> list:                    # engine.market.get_window(human_pid)
    def get_hp(self, pid: int) -> int:
    def get_gold(self, pid: int) -> int:
    def get_streak(self, pid: int) -> int:         # positive = win streak, negative = loss streak
    def get_stats(self, pid: int) -> dict:         # total_pts, evolutions, market_rolls, win_streak_max
    def get_rarity_weights(self) -> dict:          # engine.market.RARITY_WEIGHT for current turn
    def get_combat_log(self) -> list[str]:         # passive_buff_log filtered for combat triggers
    def get_prefix_bonus(self, pid: int) -> int:  # (sum of _prefix stats of player pid) // 6

    # --- Internal state fields ---
    turn_counter:    int  = 0
    place_locked:    bool = False
    in_prep_phase:   bool = False
    eliminated:      set[int]
    current_pairings: list[tuple[int, int]]
    human_pid:       int  = 0       # always 0
```

**`_prefix` stats definition:** A `_prefix` stat is any stat key on a card whose name begins with the string `"_"` (underscore). These are hidden bonus stats not displayed on card edges. The engine accumulates them internally. `get_prefix_bonus(pid)` sums all `_prefix` stat values across all cards on `pid`'s board and returns `total // 6`. This value is added to the displayed combat damage formula.

### 2.2 EventBus (`v2/core/event_bus.py`)

UI-internal publish/subscribe. Used to decouple UI components from each other without polling. The engine does NOT use this — it is UI-only.

```python
class UIEvent(IntEnum):
    SHOP_SLOT_UPDATED   = 1   # payload: shop_index
    HAND_UPDATED        = 2   # payload: None (full re-read)
    GOLD_UPDATED        = 3   # payload: new_gold int
    HP_UPDATED          = 4   # payload: pid int
    PLACE_LOCKED        = 5   # payload: None
    TURN_ADVANCED       = 6   # payload: new_turn int
    PLAYER_ELIMINATED   = 7   # payload: pid int
    COMBAT_LOG_LINE     = 8   # payload: str

class EventBus:
    # Singleton. subscribe(event, callback). publish(event, payload).
    # All callbacks execute synchronously in the same frame they are published.
```

### 2.3 Thread Safety

The current architecture is **single-threaded.** All engine calls, UI rendering, and input handling run on the main thread. There are no background threads. The only non-interactive window is the AI execution step (Section 1.1 Step 4), handled by a blocking call with a hard timeout. Do NOT introduce threads without updating this section.

### 2.4 engine_core Public API Surface — GameState Tam Köprü Sözleşmesi

**HARD RULE:** Hiçbir `v2/` dosyası `engine_core`'u doğrudan import etmez. Tüm erişim `GameState` üzerinden gerçekleşir. Bu bölüm, `GameState`'in UI'a köprülemesi gereken engine verisinin eksiksiz listesini tanımlar. Aşağıdaki tablolarda listelenen herhangi bir accessor `game_state.py`'de eksikse bu bir **blocking gap**'tir; sonraki phase'e geçilmeden kapatılmalıdır.

#### `Game` nesnesi — kök erişimciler

| engine_core Alanı / Metodu | Tip | Gerekli `GameState` Accessor |
|---|---|---|
| `.players` | `List[Player]` | index ile `engine.players[pid]` (dolaylı) |
| `.turn` | `int` | `get_turn() → int` |
| `.last_combat_results` | `List[dict]` | `get_last_combat_results() → List[dict]` |
| `.alive_players()` | `List[Player]` | `get_alive_pids() → List[int]` |
| `.swiss_pairs()` | `List[Tuple]` | `get_current_pairings() → List[Tuple[int,int]]` |
| `.market.pool_copies` | `Dict[str,int]` | `get_pool_copies() → Dict[str,int]` |
| `.card_by_name` | `Dict[str,Card]` | CardDatabase singleton köprüler — ayrı accessor gerekmez |

#### `Player` nesnesi — her `pid` için erişimciler

| `Player` Alanı | Tip | Gerekli `GameState` Accessor | MockGame'de Var mı? |
|---|---|---|---|
| `.pid` | `int` | index | ✅ |
| `.hp` | `int` | `get_hp(pid)` | ✅ |
| `.gold` | `int` | `get_gold(pid)` | ✅ |
| `.hand` | `List[Card]` | `get_hand(pid) → List[str\|None]` | ✅ (sadece isim string'i) |
| `.strategy` | `str` | `get_strategy(pid) → str` | ✅ |
| `.board.grid` | `Dict[(q,r), Card]` | `get_board_cards(pid) → Dict[(q,r), str]` | ❌ **EKSİK** |
| `.copies` | `Dict[str,int]` | `get_copies(card_name, pid) → int` | ❌ **EKSİK** |
| `.win_streak` | `int` | `get_win_streak(pid) → int` | ❌ **EKSİK** |
| `.alive` | `bool` | `is_alive(pid) → bool` | ❌ **EKSİK** |
| `.total_pts` | `int` | `get_total_pts(pid) → int` | ❌ **EKSİK** |
| `.turn_pts` | `int` | `get_turn_pts(pid) → int` | ❌ **EKSİK** |
| `.evolved_card_names` | `List[str]` | `get_evolved_names(pid) → List[str]` | ❌ **EKSİK** |
| `.passive_buff_log` | `List[dict]` | `get_passive_buff_log(pid) → List[dict]` | ❌ **EKSİK** |
| `.stats` | `dict` | `get_stats(pid) → dict` | ❌ **EKSİK** |
| `.board.has_catalyst` | `bool` | `has_catalyst(pid) → bool` | ❌ **EKSİK** |
| `.board.has_eclipse` | `bool` | `has_eclipse(pid) → bool` | ❌ **EKSİK** |
| `.interest_multiplier` | `float` | `get_interest_multiplier(pid) → float` | ❌ **EKSİK** |
| `.turns_played` | `int` | `get_turns_played(pid) → int` | ❌ **EKSİK** |

#### `last_combat_results` — savaş sonucu kayıt formatı

`engine.combat_phase()` her çağrısında `engine.last_combat_results` listesi sıfırlanır ve yeniden doldurulur. Her eleman şu sözleşmeye uyar:

```python
{
    "pid_a":       int,   "pid_b":       int,   # dövüşen oyuncu PID'leri
    "pts_a":       int,   "pts_b":       int,   # toplam maç puanı (kill + combo + synergy)
    "kill_a":      int,   "kill_b":      int,   # kill puanları (KILL_PTS=8 katı)
    "combo_a":     int,   "combo_b":     int,   # combo puanları
    "synergy_a":   int,   "synergy_b":   int,   # SynergyHud çapraz-doğrulama için
    "draws":       int,                          # beraberlik sayısı
    "winner_pid":  int,                          # -1 = berabere
    "dmg":         int,                          # kaybedene verilen hasar
    "hp_before_a": int,   "hp_before_b": int,
    "hp_after_a":  int,   "hp_after_b":  int,
}
```

`GameState.get_last_combat_results() → List[dict]` — `engine.last_combat_results`'ı doğrudan döndürür; kopyalamaz.

#### Rarity normalizasyon sözleşmesi

`engine_core` yükleme anında `cards.json` rarity string'lerini normalize eder: `"◆" → "1"`, `"◆◆" → "2"`, ..., `"◆◆◆◆◆" → "5"`, gelişmiş kart → `"E"`. Bu nedenle gerçek `Card.rarity = "3"` (ASCII rakam), ancak `CardData.rarity = "◆◆◆"` (ham JSON). `CardData.rarity_level` property'si her iki formatı da desteklemelidir:

```python
@property
def rarity_level(self) -> int:
    """Handles both '◆◆◆' (cards.json) and '3' (engine_core runtime)."""
    if self.rarity.isdigit():
        return int(self.rarity)
    return self.rarity.count("◆")
```

**Bu patch yapılmadan gerçek engine hookup'ta tüm kartlar R0 (gri) görünür — sessiz görsel bozulma.**

#### `Board.place_card()` çift-yazma sözleşmesi

`GameState.place_card()` şu anda yalnızca UI-local `_board` dict'ini günceller. Gerçek `engine.combat_phase()` ise `player.board.grid`'i okur. Bu ikisi senkronize edilmeden kalırsa insan oyuncusunun boardu savaşta **boş** görünür: 0 kill, 0 combo, 0 synergy — crash vermez, sessiz doğruluk hatasıdır.

Doğru implementasyon her zaman her iki hedefi atomik olarak günceller:

```python
def place_card(self, hand_index: int, coord: tuple, rotation: int = 0) -> ActionResult:
    ...
    # 1. UI-local board (rendering için)
    self._board[coord] = card_name
    self._board_rotations[coord] = rotation

    # 2. Engine board sync (combat resolution için)
    #    Guard: MockPlayer.hand string listesi içerir, gerçek Card objesi değil.
    raw = player.hand[hand_index]
    if hasattr(raw, 'rotation'):      # gerçek Card nesnesi
        raw.rotation = rotation
        player.board.place(coord, raw)
    player.hand[hand_index] = None
    ...
```

**MockGame uyumluluğu:** `hasattr(raw, 'rotation')` kontrolü string'lerde `False` döner; MockGame'de engine sync bloğu atlanır, ikili uyumluluk korunur.

---

## 3. SCENE SPECIFICATIONS (1920×1080)

### 3.1 SceneManager (`v2/core/scene_manager.py`)

```python
class Scene:
    def on_enter(self) -> None: ...    # called once when scene becomes active
    def on_exit(self) -> None: ...     # called once before scene is replaced; release resources here
    def handle_event(self, event: pygame.event.Event) -> None: ...
    def update(self, dt_ms: float) -> None: ...
    def draw(self, surface: pygame.Surface) -> None: ...

class SceneManager:
    _current: Scene
    _transition_pending: Scene | None

    def transition_to(self, scene: Scene, fade_ms: int = 200) -> None:
        # Initiates a linear alpha fade-out (fade_ms), calls current.on_exit(),
        # sets new scene, calls new.on_enter(), then fades in.
        # During fade, no input events are forwarded.

    def update(self, dt_ms: float) -> None: ...
    def draw(self, surface: pygame.Surface) -> None: ...
```

All scenes inherit `Scene`. `SceneManager` owns the active scene instance. Scenes do NOT hold references to each other — they communicate only through `GameState` and `EventBus`.

### 3.2 Lobby Scene

- **Strategy grid:** 8 strategy cards arranged in 2 rows × 4 columns. Each card: 180×220 px, 24px gap. Centered in screen.
- **Card content:** Strategy name (FONT_BOLD, 18px), flavor description (FONT_REGULAR, 13px, max 3 lines), starting stat preview.
- **Selection:** Left-click calls `GameState.initialize(strategy_idx)`. Then `SceneManager.transition_to(ShopScene)`.
- **No back button.** This is the entry scene.

### 3.3 Shop Scene

**Layout zones (all x/y relative to screen origin):**

| Zone | x | y | w | h |
|---|---|---|---|---|
| Shop panel | CENTER_ORIGIN_X | 0 | CENTER_W | SHOP_PANEL_H |
| Income preview | INCOME_PREVIEW_X | INCOME_PREVIEW_Y | 300 | 60 |
| Reroll button | REROLL_BTN_X | REROLL_BTN_Y | REROLL_BTN_W | REROLL_BTN_H |
| Ready button | CENTER_ORIGIN_X + CENTER_W - 160 | HAND_PANEL_Y - 60 | 140 | 44 |
| Hex board | CENTER_ORIGIN_X | SHOP_PANEL_H | CENTER_W | HAND_PANEL_Y - SHOP_PANEL_H |
| Timer bar | CENTER_ORIGIN_X | SHOP_PANEL_H | CENTER_W | TIMER_BAR_H (8) |
| Hand panel | CENTER_ORIGIN_X | HAND_PANEL_Y | CENTER_W | HAND_PANEL_H |
| Left panel (Synergy) | 0 | 0 | LEFT_PANEL_W | SCREEN_H |
| Right panel (Lobby) | SCREEN_W - RIGHT_PANEL_W | 0 | RIGHT_PANEL_W | SCREEN_H |

**Reroll button spec:**
- Label: `"REROLL [2G]"`, FONT_BOLD, 16px.
- Active state: COLOR_GOLD_TEXT background.
- Disabled state: `player.gold < 2` → background COLOR_DISABLED, no click response, cursor remains default.
- Clicking while active calls `GameState.reroll()`. If `ActionResult.OK`, publishes `UIEvent.SHOP_SLOT_UPDATED` for all 5 slots.

**Market Rarity Timeline:**
- Reads `GameState.get_rarity_weights()`. Displays rarity tiers (R1–R5, E) as labeled percentage bars.
- Positioned in left panel, below Synergy HUD, above Combat Terminal zone.
- Updates once per turn at turn start. Does NOT update mid-turn.

**Income Breakdown preview:**
- Displayed as a single line of text under the gold counter:
  `Base: {b} + Interest: {i} + Streak: {s} + Bailout: {bail} = {total}`
- Values computed client-side from engine-readable fields:
  - `b` = engine base income (constant per GDD)
  - `i` = `min(floor(player.gold / 10), 5)` (interest, capped at 5)
  - `s` = `floor(abs(win_streak) / 3)` (applies only to win streak, not loss)
  - `bail` = `1 if player.hp < 75 else 0` + `2 if player.hp < 45 else 0`
- Font: FONT_MONO, FONT_SIZE_LABEL. Color: COLOR_GOLD_TEXT.

**"Opponents deciding..." overlay:**
- Triggered when `GameState.run_ai_turns()` is executing.
- Full-screen semi-transparent overlay (black, alpha 160).
- Centered text: `"Opponents deciding..."`, FONT_BOLD, FONT_SIZE_LARGE.
- No input is forwarded to any widget during this state.
- Dismissed automatically when `run_ai_turns()` returns.

### 3.4 Versus Splash Scene

- **Trigger:** `SceneManager.transition_to(VersusScene)` after pairings are resolved.
- **Duration:** Dismissed after `SPLASH_DURATION_MS = 3000 ms` OR on any mouse click / SPACE key.
- **Layout:**
  - Background: full-screen dark overlay rendered over a blurred snapshot of the shop scene.
  - Center: Matchup string `"{P_name} vs {Opp_name} ({Opp_strategy})"`, FONT_BOLD, FONT_SIZE_LARGE.
  - Below: two horizontal HP bars (SPLASH_HP_BAR_W × SPLASH_HP_BAR_H) for each combatant with integer HP labels.
  - Top-right corner: `"Turn {N}"`, FONT_REGULAR, FONT_SIZE_HEADER.
- **On dismiss:** `SceneManager.transition_to(CombatScene)`.

### 3.5 Combat Scene

**Layout mirrors Shop scene panels (left / center / right), hex board visible, hand panel hidden.**

**Combat resolution — step sequence:**

Combat is NOT animated frame-by-frame. `engine.combat_phase()` resolves atomically. The Combat Scene reads the resulting `passive_buff_log` and **replays** it as a timed terminal stream.

1. On `on_enter()`: call `engine.combat_phase()`. Store full result snapshot.
2. Parse `GameState.get_combat_log()` into an ordered list of terminal lines.
3. Stream lines to Combat Terminal at a rate of one line per 80 ms (configurable). Terminal scrolls automatically. No user input pauses this.
4. After all log lines are streamed, display the final damage equation prominently:
   `[Base] + [Alive/2] + [Rarity/2] + [Prefix bonus] = Final_Damage`
   where `Prefix bonus = GameState.get_prefix_bonus(human_pid)`.
5. After 1500 ms additional wait, transition: `SceneManager.transition_to(ShopScene)` (or EndgameScene if game-end condition is met).

**`_prefix` visual rule:** If `get_prefix_bonus(pid) > 0`, the damage equation line MUST include the `[Prefix bonus]` term. If it is 0, the term is omitted from the display string. Omitting this term when the bonus is non-zero causes visible math desync and is a critical rendering bug.

**Combat Terminal spec:**
- Background: COLOR_TERMINAL_BG. Font: FONT_MONO, FONT_SIZE_BODY. Text color: COLOR_TERMINAL_FG.
- Terminal area: left panel lower zone, y from `SYNERGY_HUD_H` to `SCREEN_H`. Width: `LEFT_PANEL_W`.
- Lines are appended bottom-up (newest at bottom). Max visible lines: `floor(COMBAT_TERM_H / (FONT_SIZE_BODY + 4))`.
- Older lines scroll up. No scrollbar — terminal is non-interactive.
- Filter: Only log entries from `passive_buff_log` where `entry.trigger == "combat"` are shown.

---

## 4. INPUT HANDLING & PLACEMENT LOGIC

### 4.1 Full Key Mapping

| Key / Event | Context | Action |
|---|---|---|
| `W, A, S, D` | Shop Scene | Pan camera (offset). |
| `Q, E` or `+, -` | Shop Scene | Mouse-centered Zoom. |
| `R` key | Shop Scene | Reset Camera (offset=0, zoom=1.0). |
| Left-click on empty grid | Shop Scene | World Drag (if not on UI panel). |
| Left-click on hand card | Shop Scene, not locked | `selected_hand_idx = card_index` |
| Left-click on valid empty hex | Shop Scene, card selected | `GameState.place_card(selected_hand_idx, coord, pending_rotation)` |
| Left-click on occupied hex | Shop Scene | No action. Do NOT deselect. |
| Left-click on invalid hex | Shop Scene | No action. |
| `R` key | Shop Scene, card selected | `pending_rotation = (pending_rotation + 1) % 6` |
| Right-click | Shop Scene, card selected | `pending_rotation = (pending_rotation + 1) % 6` |
| Left-click on shop slot | Shop Scene | `GameState.buy_card(slot_index)`. On failure, flash slot with error color for 300ms. |
| Left-click Ready button | Shop Scene | `GameState.commit_human_turn()` |
| Left-click on Player Hub row | Any scene | `GameState.active_board_pid = clicked_pid`. Board re-renders. |
| Left-click / SPACE | Versus Splash | Dismiss splash immediately. |
| `F3` | Any scene (debug mode) | Toggle `DebugOverlay`. |
| `ESC` | Any scene | No action (quit is handled by window close event only). |

**Deselect rule:** Clicking anywhere outside the hand panel, hex board, or shop panel while a card is selected sets `selected_hand_idx = None` and clears the ghost preview.

### 4.2 Ghost Preview & Unified Board Specification

- **The Grid is the Board:** The background `void_hex` pattern and the playable board share the same coordinate system.
- **Active Cells:** Merkezdeki 37 koordinat (`|q+r| <= 3`) "aktif" kabul edilir.
- **Render Style (A2 Premium):** 
  - Passive cells: Alpha 25 stroke only.
  - Active cells: `UIUtils.create_gradient_panel` style glass inset + max(1, int(2*zoom)) neon glow border.
- **Ghost Preview Logic:** 
  - Active when: `selected_hand_idx is not None` OR dragging card AND mouse is over a valid empty hex.
  - Ghost Render: Card sprite at hovered hex, alpha 153 (60%).
  - **Edge Stats Overlay:** 
    - Position: 6 hex edge midpoints (`angle = 60 * i`).
    - Values: From `card_data.stats` (list of 6 values) or mock fallback.
    - Color: `MIND (Blue)`, `CONNECTION (Green)`, `EXISTENCE (Red)`.
    - Shadow: 1px black shadow for readability.

### 4.3 Placement Rules & Locks

- `PLACE_PER_TURN = 1`. Once `GameState.place_card()` returns `ActionResult.OK`, `GameState.place_locked = True`.
- `place_locked` resets to `False` at the start of the next `on_enter()` call of `ShopScene` (i.e., at turn start).
- If `place_card()` returns any non-OK `ActionResult`, the UI displays a brief toast notification (centered bottom, 600ms):
  - `ERR_INSUFFICIENT_GOLD` → `"Not enough gold"`
  - `ERR_SLOT_OCCUPIED` → `"Hex occupied"`
  - `ERR_INVALID_COORD` → `"Invalid position"`
  - `ERR_PLACE_LOCKED` → `"Already placed this turn"`
  - Other → `"Action failed"`
- Recall is permanently disabled. There is no undo mechanic.

---

## <span style="color:#4ade80">4.4 Top-Layer: Drag & Drop State Machine (🟩 TAMAMLANDI)</span>

<span style="color:#4ade80">
- Paneller arası kart taşıma işlemi tamamen TDD güvenceli bir State-Machine (`ShopScene.drag_state`) tarafından kontrol edilir.
- **Shop Interaction:** Satın alma yalnızca "Sol Tık" (Click-to-Buy) ile işlenir.
- **Hand Interaction:** Kart üzerine "Basılı tutup çekilerek" sürüklenir.
- **Ghost Shell:** Sürüklendiği anda Hand içerisindeki orjinal alanına %60 transparan (Karanlık) bir gölge bırakır.
- **Top Z-Index:** D&D halindeki kartlar Lobi, Sinerji HUD ve Timer Bar dahil tüm ekran bileşenlerinin "En Üstünde" süzülür.
- **Snap-Back:** Geçersiz veya boş bir alana Drop edilirse kart anında asıl koordinatına (Ghost Shell yuvasına) zıplar.
</span>

---

## 5. UI COMPONENTS & FEEDBACK

### 5.1 Synergy HUD (Left Panel Upper)

- **Position:** x=0, y=0, w=LEFT_PANEL_W, h=SYNERGY_HUD_H.
- **Group bonus formula:** `floor(3 * (n - 1) ** 1.25)`, capped at 18. `n` = number of cards on board belonging to that group.
- **Diversity bonus:** `+1` per unique group with at least 1 card on board.
- **Display:** One row per active group. Format: `[Group icon 24×24] [Group name] [Bonus value]`. Non-active groups (n=0) are shown dimmed (alpha 80).
- <span style="color:#4ade80">**Passive Tracker (🟩 TAMAMLANDI):** (Sonradan eklenen özellik). Synergy panelinin orta kutusunda yeralır. Altın sarısı kutu sınırları içinde oyuncunun Fibonaccı, Midas gibi pasif özellikleri için dolum eşiklerini progress-bar formatında görselleştirir.</span>
- **Total line:** `"Total Bonus: {group_total + diversity_bonus}"` at bottom of HUD zone.
- **Update trigger:** Re-computed on every `UIEvent.HAND_UPDATED` and after every successful `place_card()`.

### 5.2 Upgrades & Evolution Sub-System

**Copy tracking:**
- Every card in Hand or Shop renders a sub-label: `"Copies: {count}/3"`.
- `count` = total copies of that card across the player's hand + board + the current shop window.
- Font: FONT_REGULAR, FONT_SIZE_LABEL. Color: white if count < 3, COLOR_GOLD_TEXT if count == 3.

**Copy Strengthening Milestones:**
- Milestone turn thresholds per GDD (default): Turn 4 → `+2` boost, Turn 7 → `+3` limit offset.
- Catalyst/Eclipse state: if `player.stats["catalyst_active"]` is True, reduce thresholds by 1. If `player.stats["eclipse_active"]` is True, increase by 1.
- When the human player's board crosses a threshold at turn start, for each affected card on the board, spawn a `FloatingText("+{N} STATS (MILESTONE)", card_board_pos, color=COLOR_GOLD_TEXT)`.

**FloatingText animation:**
- Origin: center-top of the target card's board position.
- Motion: rises `FLOAT_TEXT_RISE_PX_PER_SEC` px/sec upward.
- Alpha: 255 for first `FLOAT_TEXT_FADE_START_MS` ms, then linear fade to 0 over the remaining duration.
- Lifetime: `FLOAT_TEXT_LIFETIME_MS` total.
- Multiple FloatingTexts stack vertically with 4px gap between origins.

**Evolved card rendering:**
- Cards with rarity `"E"` render with a `COLOR_PLATINUM` border (4px wide) replacing the standard rarity border.
- The rarity badge renders the single character `"E"` in FONT_BOLD, 14px, on a COLOR_PLATINUM background.

### 5.3 Player Hub (Right Panel)

- **Position:** x=SCREEN_W-RIGHT_PANEL_W, y=0, w=RIGHT_PANEL_W, h=SCREEN_H.
- **Rows:** 8 rows, each HUB_ROW_H px tall. Row order: sorted by PID (0–7). Human player (PID 0) is always row 0.
- **Row content (left to right, all within the row rect):**
  - PID badge (24×24, left edge + 8px margin)
  - Strategy logo (24×24 sprite, 4px gap)
  - HP bar (HUB_HP_BAR_W × HUB_HP_BAR_H). Color: interpolate COLOR_HP_FULL → COLOR_HP_LOW as `hp / max_hp` decreases from 1.0 to 0.0. Integer HP drawn centered on bar.
  - Gold value (FONT_BOLD, HUB_GOLD_FONT_SIZE, COLOR_GOLD_TEXT, right-aligned)
  - Streak icon (24×24, right edge - 8px margin)
- **Streak icon rules:**
  - `win_streak >= 2`: "flame" sprite (`sfx/icon_flame.png`)
  - `loss_streak >= 2` (i.e. `streak <= -2`): "ice" sprite (`sfx/icon_ice.png`)
  - Otherwise: no icon rendered
- **Click:** Left-click on any row → `GameState.active_board_pid = pid`. Board re-renders immediately using `GameState.get_board(pid)`. Currently active row has a 2px left-edge highlight in COLOR_GOLD_TEXT.
- **Eliminated player row:** Background set to grayscale (desaturate all colors). HP bar renders black. HP text reads `"DEAD"`. Gold renders `"—"`. Streak icon hidden.

### 5.4 Rarity Color Mapping

| Rarity | Border color (RGB) |
|---|---|
| R1 | (180, 180, 180) — gray |
| R2 | (80, 200, 120) — green |
| R3 | (80, 140, 255) — blue |
| R4 | (180, 80, 255) — purple |
| R5 | (255, 180, 60) — gold |
| E | COLOR_PLATINUM = (220, 220, 240) |

### 5.5 Audio Specification

All audio is loaded at scene entry via `AssetLoader`. Do not stream; preload all SFX.

| Event | File | Type |
|---|---|---|
| Card bought | `sfx/card_buy.wav` | SFX |
| Card placed | `sfx/card_place.wav` | SFX |
| Reroll | `sfx/reroll.wav` | SFX |
| Milestone reached | `sfx/milestone.wav` | SFX |
| Combat damage dealt | `sfx/damage.wav` | SFX |
| Player eliminated | `sfx/eliminated.wav` | SFX |
| Shop scene BGM | `music/shop_loop.ogg` | Music (loop) |
| Combat scene BGM | `music/combat_loop.ogg` | Music (loop) |
| Victory | `music/victory.ogg` | Music (one-shot) |

Audio channels: 1 music channel (via `pygame.mixer.music`), 8 SFX channels (via `pygame.mixer.Sound`).

### 5.6 EndGame Scene

- **Trigger:** `alive_players <= 1` OR `turn_counter == 50`.
- **Sort order:** `engine.players` sorted descending by `player.hp` (surviving HP). Eliminated players sorted by elimination turn descending (last eliminated = higher rank).
- **Table columns:** `Rank | Player | Strategy | Final HP | Total Pts | Evolutions | Rerolls | Win Streak Max`
- **Data source:** `GameState.get_stats(pid)` for `total_pts`, `evolutions`, `market_rolls`, `win_streak_max`. `get_hp(pid)` for Final HP.
- **Winner banner:** If exactly 1 alive player, render `"{name} WINS"` above the table in FONT_BOLD, 48px.
- **Restart button:** Bottom center. Calls `SceneManager.transition_to(LobbyScene)` and resets `GameState`.

---

## 6. ASSET LOADER (`v2/assets/loader.py`)

```python
class AssetLoader:
    # Singleton. All assets loaded relative to v2/assets/.
    # Raises FileNotFoundError with full path on missing asset — no silent fallback.

    def get_sprite(self, name: str) -> pygame.Surface:
        # name: path relative to v2/assets/sprites/, e.g. "card_back.png"
        # Returns Surface with per-pixel alpha (convert_alpha()).
        # Cached after first load.

    def get_font(self, name: str, size: int) -> pygame.font.Font:
        # name: filename in v2/assets/fonts/.
        # Cached by (name, size) tuple.

    def get_sfx(self, name: str) -> pygame.mixer.Sound:
        # name: path relative to v2/assets/sfx/.
        # Cached after first load.

    def preload_scene(self, scene_name: str) -> None:
        # Loads all assets required for the given scene name.
        # Call in SceneManager.transition_to() before on_enter().
        # Asset manifests per scene are defined in v2/assets/manifests.py.
```

---

## 7. DEBUG OVERLAY (`v2/debug_overlay.py`)

Activated by `F3`. Rendered as a transparent layer over all scenes. Displays:

- Current FPS (clock tick)
- Active scene name
- `GameState.turn_counter`, `place_locked`, `in_prep_phase`
- Mouse position in screen px AND in axial hex coords (if cursor is over board)
- `active_board_pid`
- Last `ActionResult` returned by any GameState mutation method
- Count of active FloatingText instances

Debug overlay is compiled out in production builds (`DEBUG = False` in `constants.py` disables all overlay code paths).

---

## 8. ENGINE MOCK (`v2/mock/engine_mock.py`)

Used exclusively in testing. Provides a drop-in replacement for `engine_core.game.Game` with the same public API surface but deterministic, configurable return values. No game logic runs.

```python
class MockGame:
    # Configurable fields:
    mock_gold:   int  = 10
    mock_hp:     int  = 100
    mock_shop:   list = [...]   # 5 fake card dicts
    mock_board:  dict = {}
    mock_hand:   list = []
    fail_next_buy: bool = False   # forces ERR_INSUFFICIENT_GOLD on next buy_card()

    # Mirrors full engine_core.game.Game public API.
    # All calls are logged to mock_call_log: list[str] for test assertions.
```

All tests in `v2/tests/` instantiate `GameState` with `MockGame` injected. No test may import or instantiate `engine_core` directly.

### 8.1 `MockGame` & `MockPlayer` — Eksiksizlik Sözleşmesi

Mevcut `MockGame`, gerçek engine API'sinin yaklaşık **%30'unu** modelliyor. Aşağıdaki tablolar hangi alanların eksik olduğunu ve hangi Phase'de gerekli olduklarını belirtir. İlgili Phase başlamadan önce bu alanlar eklenmiş olmalıdır — aksi hâlde UI feature tamamlanamaz.

#### `MockPlayer` — Mevcut vs. Gerekli

| Alan | Şu An | Gerekli Phase | Bloke Ettiği UI Feature |
|---|---|---|---|
| `name`, `hp`, `gold`, `hand` | ✅ Var | — | — |
| `win_streak: int = 0` | ❌ **EKSİK** | Phase 3 (item 15) | `IncomePreview` streak terimi; `PlayerHub` streak göstergesi |
| `alive: bool = True` | ❌ **EKSİK** | Phase 3 (item 17) | `LobbyPanel` ELIMINATED overlay; `get_alive_pids()` filtresi |
| `copies: Dict[str, int] = {}` | ❌ **EKSİK** | Phase 3 (item 16) | Shop/Hand kart üzerindeki `"Copies: X/3"` etiketi |
| `total_pts: int = 0` | ❌ **EKSİK** | Phase 4 (item 22) | `CombatTerminal` birikimli puan satırı |
| `turn_pts: int = 0` | ❌ **EKSİK** | Phase 4 (item 22) | `CombatTerminal` anlık tur puanı |
| `passive_buff_log: list = []` | ❌ **EKSİK** | Phase 3b (item 18) | `FloatingText` `"+N STATS"` kaynağı |
| `evolved_card_names: list = []` | ❌ **EKSİK** | Phase 3b (item 20) | Evolved kart Platinum border tetikleyici |
| `stats: dict` | ❌ **EKSİK** | Phase 4 (item 25) | `EndgameScene` tablo sütunları |

`stats` dict alanları ve başlangıç değerleri: `wins=0, losses=0, draws=0, market_rolls=0, evolutions=0, win_streak_max=0`.

#### `MockGame` — Mevcut vs. Gerekli

| Alan / Metod | Şu An | Gerekli Phase | Bloke Ettiği UI Feature |
|---|---|---|---|
| `turn: int = 1` | ✅ Var (ama `GameState.get_turn()` yok) | Phase 3c (item 30) | `TimerBar` gerçek ratio; rarity ağırlığı display |
| `state: str = "SHOP"` | ✅ Var | — | — |
| `last_combat_results: list = []` | ❌ **EKSİK** | Phase 4 (item 22) | `CombatTerminal` savaş log kaynağı |

`buy_card_from_slot()` içinde alım yapıldığında `player.copies[card_name] = player.copies.get(card_name, 0) + 1` güncellemesi de yapılmalıdır.

#### `MockPlayer.hand` tip farkı — köprü notu

Gerçek engine: `player.hand: List[Card]` — `Card` nesnesi.
MockGame: `player.hand: List[str | None]` — sadece kart isim string'i.

Bu fark `GameState.get_hand()` tarafından şeffaf biçimde köprülenir (her zaman sadece `str | None` döner). Ancak `GameState.place_card()` içindeki `hasattr(raw, 'rotation')` guard'ı bu farkı korumak için zorunludur (bkz. Section 2.4 çift-yazma sözleşmesi). Bu guard olmadan MockGame üzerinde `place_card()` çağrısı `AttributeError` fırlatır.

---

## 9. EXECUTION PLAN

### Phase 0 — Foundations (PREREQUISITE FOR ALL PHASES)

Complete these in order before writing any scene or UI code.

1. Verify `constants.py` is complete and matches this spec. No values may be changed mid-implementation without updating this document.
2. Implement `HexGrid` math module (`axial_to_pixel`, `pixel_to_axial`, `_hex_round`, `VALID_HEX_COORDS`). Write unit tests for all 37 valid coords and 10 invalid coords.
3. Implement `EventBus` and confirm publish/subscribe roundtrip in isolation.
4. Implement `AssetLoader` skeleton. Confirm it raises on missing file.
5. Implement `MockGame` and inject into `GameState`. Confirm all `ActionResult` codes are reachable via mock.
6. Implement `SceneManager` with fade transition. Confirm `on_enter` / `on_exit` lifecycle fires correctly.
7. Implement `DebugOverlay`. Confirm F3 toggle works at 60 FPS without frame drop.

### Phase 1 — Foundation (UI İSKELETLERİ: <span style="color:#4ade80">🟩 TAMAMLANDI</span>)

*Aşağıdaki maddeler v2.0 Sandbox fazında Rect limitleri çekilerek doğrulanmış ve çalıştırılmıştır:*
8. <span style="color:#4ade80">🟩 Rewrite `v2/core/game_state.py` per Section 2.1. Full `ActionResult` enum. Full method contracts. `sync_state()` wired to engine.</span>
9. <span style="color:#4ade80">🟩 Implement the 5-step phase pipeline in `GameState`: `commit_human_turn()`, `run_ai_turns()` with timeout, `swiss_pairings()` call.</span>
10. <span style="color:#4ade80">🟩 Inject `PLACE_PER_TURN = 1` lock: `place_locked` flag, reset on turn start.</span>
11. <span style="color:#4ade80">🟩 **[NEW] UI Kapsülleri TDD Sınırları test edildi (ShopPanel, HandPanel Encapsulation)**</span>
12. <span style="color:#4ade80">🟩 **[NEW] Sol HUD Segmentasyonu (Passive Tracker & Combat Log eklentisi yapılandırıldı)**</span>
13. <span style="color:#4ade80">🟩 **[NEW] Sağ HUD Lobi Skorbordu (Duvar kaldırılarak Yüzen Row tasarımı atandı)**</span>
14. <span style="color:#4ade80">🟩 **[NEW] Phase/Ateşli Timer Bar sisteme tanıtıldı.**</span>
15. <span style="color:#4ade80">🟩 **[NEW] Drag & Drop State Machine: Z-Index önceliklendirilerek kuruldu + Bug Guarding tamamlandı.**</span>

### Phase 2 — UI Math & Input (<span style="color:#4ade80">🟩 TAMAMLANDI</span>)

11. <span style="color:#4ade80">🟩 **Unified Coordinate System:** `CameraState` (zoom/offset) global state integrated into `GridMath`.</span>
12. <span style="color:#4ade80">🟩 **Dynamic Background:** `BackgroundManager` refactored to render infinite hex grid based on camera state.</span>
13. <span style="color:#4ade80">🟩 **Mouse-Centered Interaction:** Zoom and World Drag (camera panning) implemented with mouse-centered focus.</span>
14. <span style="color:#4ade80">🟩 **A2 Premium Hex Renderer:** "Glass Inset" cell style with neon borders implemented.</span>
15. <span style="color:#4ade80">🟩 **Ghost Preview & Edge Stats:** %60 alpha preview + synergy-coded edge stats with shadow labels fixed.</span>
16. <span style="color:#4ade80">🟩 **Keyboard Controls:** `W, A, S, D` (pan), `Q, E` (zoom), `R` (reset) added.</span>

### Phase 3 — Interaction & Feedback (IN PROGRESS)

14. <span style="color:#4ade80">🟩 **SynergyHUD** tamamen yeniden yazıldı: `_group_bonus(n) = min(18, floor(3*(n-1)^1.25))` formülü (GDD §8 birebir), 6-daire pip bar, tier milestone çizgileri (2/3/4/5/6 eşiğinde), 600 ms flash animasyonu, diversity bonus kutucuğu, combat log placeholder. `shop.py.update()` içinde `synergy_hud.update(dt_ms)` çağrısı mevcuttur. Bkz. `v2/ui/synergy_hud.py`.</span>
15. <span style="color:#4ade80">🟩 **IncomePreview** (`v2/ui/income_preview.py`) tam olarak implementedir: GDD §13.1 dört terim formülü (`base=3`, `interest`, `streak`, `bailout`). 2 satırlı panel tasarımı: Inter-Bold başlık + JetBrainsMono formül. Her terim ayrı renk (yeşil/altın/turuncu), sıfır değerler soluk gri. `_compute()` statik metod 14 unit test ile doğrulanmış. TimerBar altında tam opak dark navy backdrop üzerinde render edilir. Ekonomist faiz ölçeklemesi desteklenir.</span>
16. <span style="color:#4ade80">🟩 **Copy count tracking** uygulandı: `ShopScene._render_copy_labels()` her kart slotunun altına `"Copies: N/3"` etiketi çizer. Shop ve Hand panellerinin her ikisi kapsanır. `n < 3` → beyaz, `n == 3` → COLOR_GOLD_TEXT. `GameState.get_copies(card_name, 0)` üzerinden canlı okuma. MockPlayer.copies alım anında güncellenir.</span>
17. <span style="color:#4ade80">🟩 **PlayerHub** yeniden tasarlandı (`v2/ui/player_hub.py`): 5-satır compact layout (PLAYER_HUB_H=150 içinde). Satır 1: başlık + `"Tur: N"` sağda. Satır 2: segmentli HP bar. Satır 3: Gold kutusu + Streak kutusu (🔥 ≥3W turuncu / ▲ yeşil / nötr gri / ▼ kırmızı). Satır 4: `★ Pts: N` + `Board: N/37` kapasite barıyla. Satır 5: `→ +Ng gelecek tur` income özet. `sync()` artık `win_streak`, `total_pts`, `turn`, `board_used`, `next_gold` çeker.</span>

### Phase 3c — MockGame & GameState Adapter Patch (<span style="color:#f59e0b">⚠️ PHASE 3b VE PHASE 4 İÇİN ZORUNLU ÖN KOŞUL</span>)

Bu phase'deki maddeler tamamlanmadan Phase 3b ve Phase 4 başlanamaz. Section 2.4 ve Section 8.1'deki tüm boşlukları kapatır. Maddeler sırayla uygulanır.

28. <span style="color:#4ade80">🟩 **`MockPlayer` genişletme:** `win_streak=0`, `alive=True`, `copies={}`, `total_pts=0`, `turn_pts=0`, `passive_buff_log=[]`, `evolved_card_names=[]`, `stats={wins,losses,draws,market_rolls,evolutions,win_streak_max}` — tümü `__init__()` içinde başlatıldı. 5 yeni unit test ile doğrulandı.</span>
29. <span style="color:#4ade80">🟩 **`MockGame` genişletme:** `last_combat_results: list = []` eklendi. `buy_card_from_slot()` içinde `copies` sayacı güncelleniyor. `reroll_market()` içinde `market_rolls` artırılıyor. 3 yeni unit test ile doğrulandı.</span>
30. <span style="color:#4ade80">🟩 **`GameState` 16 yeni accessor:** `get_turn()`, `get_alive_pids()`, `get_win_streak()`, `get_copies()`, `is_alive()`, `get_total_pts()`, `get_turn_pts()`, `get_last_combat_results()`, `get_passive_buff_log()`, `get_stats()`, `has_catalyst()`, `has_eclipse()`, `get_interest_multiplier()`, `get_turns_played()`, `get_current_pairings()`, `get_pool_copies()` — tümü `try/except` guard ile, tip-uyumlu varsayılan döner.</span>
31. <span style="color:#4ade80">🟩 **`GameState.place_card()` çift-yazma patch:** `hasattr(raw, 'rotation')` guard eklendi. MockGame'de string hand → engine sync bloğu atlanır; gerçek Card nesnesiyle `player.board.place()` + `card.rotation` sync çalışır.</span>
32. <span style="color:#4ade80">🟩 **`CardData.rarity_level` normalizasyon patch:** `if self.rarity.isdigit(): return int(self.rarity)` — `"3"` ve `"◆◆◆"` her iki format destekleniyor. 3 regresyon + 1 engine-format unit testi eklendi.</span>
33. <span style="color:#4ade80">🟩 **`SynergyHud` çapraz-doğrulama:** `_compute_state()` içinde `DEBUG_MODE=true` ortamında `last_combat_results[-1]["synergy_a"]` ile karşılaştırma aktif. Production'da atlanır.</span>

### <span style="color:#4ade80">Phase 3 — Ek Görsel Tasarım Çalışmaları (🟩 TAMAMLANDI)</span>

*Phase 3 kapsamında planlananların ötesinde gerçekleştirilen görsel iyileştirmeler:*

- <span style="color:#4ade80">🟩 **SynergyHud tam yeniden yapılandırma (4 kutu mimarisi):** `SYNERGY BOARD` (grup pip barları) + `SKOR TABLOSU` (KILL/COMBO/SYN her biri kendi satırında, synergy grup satırlarıyla aynı tasarım dili: renk tinted bg, sol 3px accent bar, bold değer, sub-text) + `SON SAVAŞ` (kazandı/kaybetti/berabere + hasar bilgisi, `last_combat_results` okur) + `PASİF AKIŞI` (`passive_buff_log` okur, trigger renkli ikonlar: ★⚡◈▲▼). `h=118` skor kutusu TOPLAM satırını taşmadan barındırır. Bkz. `v2/ui/synergy_hud.py`.</span>
- <span style="color:#4ade80">🟩 **Panel opacity fix:** ShopPanel + HandPanel arka plan alpha `210/230 → 252/255`. Hex ızgara sızması ortadan kalktı, göz yorgunluğu azaldı.</span>
- <span style="color:#4ade80">🟩 **BackgroundManager hex desen:** alpha `25 → 15`, daha sakin arka plan.</span>
- <span style="color:#4ade80">🟩 **HUD tasarım analizi simülasyonu:** `scripts/sim_hud_analysis.py` — 8 oyunculu 32-tur tam maç. Bulgular: Synergy %76 baskın (avg 50/66 pts), Combo %17 fark yaratan, Kill %7 sporadik. Tüm veriler `output/logs/hud_analysis.txt`'e yazıldı.</span>
- <span style="color:#4ade80">🟩 **Yeni test kapsamı:** 131 → 145 test (+14). `test_player_hub.py` +7, `test_synergy_hud.py` +7 yeni test. Tüm rect sınır kontrolleri, istifleme sırası, score_rect yükseklik doğrulaması dahil.</span>

### Phase 3b — Visual Feedback & Animation

18. Implement `FloatingText` system: rise + fade, stacking. `FLOAT_TEXT_RISE_PX_PER_SEC`, `FLOAT_TEXT_LIFETIME_MS`, `FLOAT_TEXT_FADE_START_MS` sabitleri `constants.py`'den okunur. Origin: hedef kartın board koordinatının center-top'u. Birden fazla FloatingText aynı koordinatta yığılırken 4 px dikey boşluk bırakılır. Kaynak: `GameState.get_passive_buff_log(pid)` entry'leri — `{"trigger": "copy_2"|"copy_3", "delta": N}` → `FloatingText(f"+{N} STATS (MILESTONE)", board_coord, COLOR_GOLD_TEXT)`. **Prerequisite:** Phase 3c item 30 (`get_passive_buff_log` accessor'ı mevcut olmalı).
19. Implement milestone detection at turn start: `GameState.get_turns_played(0)` okunur. `has_catalyst(0)` durumuna göre eşik dizisi `COPY_THRESH_C = [3, 6]` (Catalyst aktif) veya `COPY_THRESH = [4, 7]` (normal) seçilir. Eşik aşımı tespit edildiğinde board'daki etkilenen kartlar için FloatingText spawn edilir. **Prerequisite:** Phase 3c item 30.
20. Implement evolved card (`"E"` rarity) Platinum border rendering: `card.rarity == "E"` string kontrolü kullanılır (`rarity_level` değil). Border rengi `COLOR_PLATINUM = (220, 220, 240)`, genişlik 4 px. Rarity badge: `"E"` karakteri, FONT_BOLD, 14 px, COLOR_PLATINUM arka plan.
21. Wire audio events to `AssetLoader.get_sfx()` calls at correct trigger points (bkz. Section 5.5 ses tablosu). Ön yükleme `ShopScene.on_enter()` içinde `AssetLoader.preload_scene("shop")` çağrısıyla yapılır.

### Phase 4 — Output Rendering

22. Implement `CombatTerminal`: `GameState.get_last_combat_results()` + `get_passive_buff_log(pid)` kaynaklarından beslenir. 80 ms/satır streaming, en yeni satır alta eklenir. Terminal non-interactive. Hasar denklemi son satırı: `"[Base] + [Alive/2] + [Rarity/2] + [Prefix] = {Final}"`. `_prefix` terimi yalnızca `get_prefix_bonus(pid) > 0` olduğunda gösterilir (bkz. Section 3.5 `_prefix` visual rule — sıfır olmayan değeri gizlemek kritik math desync hatasıdır). **Prerequisite:** Phase 3c item 29 (`MockGame.last_combat_results` mevcut olmalı).
23. Implement `VersusScene`: `GameState.get_current_pairings()` ile eşleşme çifti okunur. Matchup string `"{P_name} vs {Opp_name} ({Opp_strategy})"`, FONT_BOLD, FONT_SIZE_LARGE. İki HP bar `SPLASH_HP_BAR_W × SPLASH_HP_BAR_H` ve integer HP etiketleri. Üst sağ: `"Turn {N}"`. `SPLASH_DURATION_MS = 3000 ms` veya ilk click/SPACE ile dismiss → `SceneManager.transition_to(CombatScene)`. **Prerequisite:** Phase 3c item 30 (`get_current_pairings` accessor'ı).
24. Implement Reroll button disabled state: `get_gold(0) < 2` → background `COLOR_DISABLED`, cursor default, click hiçbir şey yapmaz, no-op. Mevcut kısmi implementasyon tamamlanır (renk + no-op eklenir).
25. Implement `EndgameScene`: `GameState.get_stats(pid)` okunur. Sıralama: HP azalan; elime edilmişler elime turuna göre azalan. Tablo sütunları: `Rank | Player | Strategy | Final HP | Total Pts | Evolutions | Rerolls | Win Streak Max`. Winner banner: `"{name} WINS"`, FONT_BOLD, 48 px (yalnızca 1 hayatta kalan varsa). Restart butonu bottom-center: `SceneManager.transition_to(LobbyScene)` + `GameState` sıfırlama. **Prerequisite:** Phase 3c item 30 (`get_stats` accessor'ı).
26. Implement `"Opponents deciding..."` overlay: `GameState.run_ai_turns()` çalışırken tam ekran yarı saydam siyah overlay (alpha 160) + ortalanmış metin, FONT_BOLD, FONT_SIZE_LARGE. Bu pencerede hiçbir input event iletilmez. `run_ai_turns()` döndüğünde overlay otomatik kalkar.
27. End-to-end integration test (MockGame): 3-tur tam oyun döngüsü. Doğrulama: hiçbir `ActionResult` sessizce yutulmuyor; DebugOverlay `turn_counter` ve board durumu her adımda doğru; `SynergyHud.total` ↔ `last_combat_results["synergy_a"]` eşleşiyor; PlayerHub tüm satırlar canlı veriyi yansıtıyor.

### Phase 5 — Gerçek Engine Hookup (SON ENTEGRASYON)

**Ön koşul:** Phase 3c tamamen kapalı. Tüm UI testleri MockGame ile geçiyor. Tüm `ActionResult` kodları erişilebilir durumda. `python v2/main.py` MockGame ile hatasız açılıyor.

34. **`game_factory.build_game()` → `main.py`:** `main.py._bootstrap()` içinde `MockGame()` yerine `engine_core.game_factory.build_game(strategies=list(constants.STRATEGIES))` çağrısı yap. Gerçek `Game` instance'ı `GameState.hook_engine()` ile enjekte edilir. `CardDatabase.initialize()` zaten mevcut; `game_factory` ayrı bir `build_card_pool()` çağrısı yapar — iki çağrı aynı JSON dosyasını okur, çakışma yoktur.
35. **`GameState.sync_state()` canlı bağlantı:** `ShopScene.update()` her frame `sync_state()` çağırır. Gerçek engine `players[*]` verisi PlayerHub 8 satırına yansır. Doğrulama: tüm HP / Gold / streak değerleri engine ile UI arasında eşleşmeli.
36. **`preparation_phase()` → Ready button hattı:** `GameState.commit_human_turn()` → `engine.preparation_phase()` → `GameState.sync_state()` → `SceneManager.transition_to(VersusScene)`.
37. **`combat_phase()` → `CombatScene.on_enter()`:** `engine.combat_phase()` çağrılır; dönen `engine.last_combat_results` `CombatTerminal`'e beslenir; `passive_buff_log` kayıtları terminal satırlarına dönüştürülür.
38. **FloatingText spawn pipeline:** Her `combat_phase()` sonrası `get_passive_buff_log(0)` taranır. `"copy_2"` veya `"copy_3"` trigger'lı kayıtlar için `FloatingText(f"+{delta} STATS (MILESTONE)", board_coord, COLOR_GOLD_TEXT)` spawn edilir. Birden fazla aynı koordinata denk gelirse 4 px dikey offset uygulanır.
39. **Eleme pipeline'ı:** Her `combat_phase()` sonrası tüm `engine.players[*].alive` kontrol edilir. Yeni ölen oyuncu için `UIEvent.PLAYER_ELIMINATED` publish edilir; LobbyPanel satırı grayscale + "ELIMINATED" görünümüne geçer. `engine._return_cards_to_pool(player)` engine tarafından zaten çağrılmaktadır — UI tarafında ekstra pool güncellemesi gerekmez.
40. **Hasar denklemi doğrulaması:** `CombatTerminal` son satırı `board.calculate_damage()` formülü ile birebir eşleşmeli: `|W_pts − L_pts| + floor(alive/2) + rarity_bonus//2 + _prefix_bonus = Final`. `get_prefix_bonus(pid) > 0` ise `_prefix` terimi mutlaka görünmeli (Section 3.5 visual rule).
41. **Bitiş koşulu entegrasyonu:** Her `combat_phase()` sonrası `len(get_alive_pids()) <= 1` VEYA `get_turn() >= 50` kontrolü. Doğruysa `SceneManager.transition_to(EndgameScene)`.
42. **Uçtan uca entegrasyon testi (gerçek engine):** 3-tur tam oyun döngüsü. Doğrulama kontrol listesi:
    - Hiçbir `ActionResult` sessizce yutulmuyor.
    - DebugOverlay `turn_counter` ve board durumu her adımda doğru.
    - `SynergyHud.total` ↔ `last_combat_results["synergy_a"]` eşleşiyor.
    - PlayerHub 8 satırın tümü canlı engine verisini yansıtıyor.
    - `calculate_damage()` denklemi CombatTerminal son satırıyla birebir.
    - Elime edilen oyuncu satırı doğru görünüme geçiyor.
    - `python v2/main.py` çalıştırıldığında ekran açılır, konsola hiçbir hata düşmez.
