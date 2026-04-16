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
  │   ├── scene_manager.py     # SceneManager (Lobby only; ShopScene is permanent root)
+ │   ├── event_bus.py         # Internal UI event system
  │   └── clock.py             # DeltaClock wrapper
  ├── scenes/
  │   ├── lobby.py             # Entry strategy-select screen
  │   └── shop.py              # ROOT SCENE — permanent canvas; owns Phase State Machine
- │   ├── versus_splash.py     # DELETED — replaced by VersusOverlay
- │   ├── combat.py            # DELETED — replaced by CombatOverlay
- │   └── endgame.py           # DELETED — replaced by EndgameOverlay
  ├── ui/
+ │   ├── hex_grid.py          # HexGrid math + rendering
  │   ├── hand_panel.py
  │   ├── shop_panel.py
  │   ├── player_hub.py
  │   ├── synergy_hud.py
  │   ├── combat_terminal.py
  │   ├── income_preview.py
  │   ├── lobby_panel.py
+ │   ├── overlays/            # Pop-up containers drawn ON TOP of ShopScene
+ │   │   ├── versus_overlay.py   # STATE_VERSUS — matchup banner + HP bars
+ │   │   ├── combat_overlay.py   # STATE_COMBAT — streaming combat terminal
+ │   │   └── endgame_overlay.py  # STATE_ENDGAME — scoreboard + restart
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
PLAYER_HUB_H    = 150             # compact current-player summary panel
LOBBY_ROW_H     = 70              # right sidebar scoreboard row height
HUB_ROW_H       = SCREEN_H // 8   # legacy scoreboard approximation; prefer LOBBY_ROW_H
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
TIMER_BAR_H    = 8
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
```

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

```python
def _hex_round(q_f, r_f):
    s_f = -q_f - r_f
    q, r, s = round(q_f), round(r_f), round(s_f)
    dq, dr, ds = abs(q - q_f), abs(r - r_f), abs(s - s_f)
    if dq > dr and dq > ds: q = -r - s
    elif dr > ds:            r = -q - s
    return q, r
```

**Direction → Edge index mapping (Pointy-Top, 6 edges):**

| Direction index | Engine label | Axial neighbor delta |
|---|---|---|
| 0 | N | (0, -1) |
| 1 | NE | (+1, -1) |
| 2 | SE | (+1, 0) |
| 3 | S | (0, +1) |
| 4 | SW | (-1, +1) |
| 5 | NW | (-1, 0) |

`pending_rotation = N` means direction 0 (North edge) is rotated by `N * 60°` clockwise. UI rotation math MUST stay compatible with the engine's `HEX_DIRS` ordering.

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
5. **Pairing:** Call `engine.swiss_pairs()` exactly once for the turn. Store the resulting PID pairs in `GameState.current_pairings: list[tuple[int, int]]`.
6. **Transition:** `ShopScene.set_phase(STATE_VERSUS)`.

### 1.2 Handshake Logistics

- **Combat → Prep:** After `engine.combat_phase()` resolves and damage is applied, call `engine.clear_boards()`. Then increment `GameState.turn_counter`. Call `player.synergy_matrix.decay()` for ALL active (non-eliminated) players. Then loop to Step 1.
- **Elimination check:** After damage application, evaluate `player.hp <= 0` for all players. Eliminated players are flagged `GameState.eliminated: set[int]`. They are excluded from subsequent `run_ai_turn()` calls and `synergy_matrix.decay()` calls.
- **Game-end check:** If `len(alive_players) <= 1` OR `GameState.turn_counter == 50`, call `ShopScene.set_phase(STATE_ENDGAME)` instead of looping.

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
    def get_board(self, pid: int) -> dict:         # UI-facing {(q,r): card_name} board snapshot
    def get_hand(self, pid: int) -> list:          # engine.get_player(pid).hand
    def get_shop(self) -> list:                    # engine.market.get_window(human_pid)
    def get_turn(self) -> int:
    def get_alive_pids(self) -> list[int]:
    def get_hp(self, pid: int) -> int:
    def get_gold(self, pid: int) -> int:
    def get_streak(self, pid: int) -> int:         # positive = win streak, negative = loss streak
    def get_strategy(self, pid: int) -> str:
    def get_display_name(self, pid: int) -> str:   # name if present, else synthetic "P{pid}"
    def get_stats(self, pid: int) -> dict:         # total_pts, evolutions, market_rolls, win_streak_max
    def get_last_combat_results(self) -> list[dict]:
    def get_current_pairings(self) -> list[tuple[int, int]]:  # stored snapshot; MUST NOT reroll swiss pairs
    def get_elimination_order(self) -> list[int]:  # newest elimination appended last
    def get_rarity_weights(self) -> dict:          # engine.market.RARITY_WEIGHT for current turn
    def get_combat_log(self) -> list[str]:         # optional formatter helper; MUST use combat-relevant trigger set
    def get_prefix_bonus(self, pid: int) -> int:  # (sum of _prefix stats of player pid) // 6

    # --- Internal state fields ---
    turn_counter:    int  = 0
    place_locked:    bool = False
    in_prep_phase:   bool = False
    eliminated:      set[int]
    elimination_order: list[int]
    current_pairings: list[tuple[int, int]]
    human_pid:       int  = 0       # always 0
```

`turn_counter` is a mirror/cache of `engine.turn`. Scenes and widgets should read `get_turn()` instead of touching `turn_counter` directly.

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
| `.swiss_pairs()` | `List[Tuple]` | `get_current_pairings() → List[Tuple[int,int]]` (stored snapshot, no reroll) |
| `.market.pool_copies` | `Dict[str,int]` | `get_pool_copies() → Dict[str,int]` |
| `.card_by_name` | `Dict[str,Card]` | CardDatabase singleton köprüler — ayrı accessor gerekmez |

#### `Player` nesnesi — her `pid` için erişimciler

| `Player` Alanı | Tip | Gerekli `GameState` Accessor | MockGame'de Var mı? |
|---|---|---|---|
| `.pid` | `int` | index | ✅ |
| `.hp` | `int` | `get_hp(pid)` | ✅ |
| `.gold` | `int` | `get_gold(pid)` | ✅ |
| `.hand` | `List[Card]` | `get_hand(pid) → List[str\|None]` | ✅ (sadece isim string'i) |
| `.strategy` | `str` | `get_strategy(pid) → str` | ❌ **EKSİK / BRIDGE GEREKLI** |
| `.board.grid` | `Dict[(q,r), Card]` | `get_board(pid) → Dict[(q,r), str]` | ❌ **EKSİK** |
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

**Kimlik köprüsü notu:** Mock ve gerçek engine aynı anda hem `.name` hem `.strategy` sunmaz. UI katmanı doğrudan bu alanlara güvenmez; `get_display_name(pid)` ve `get_strategy(pid)` üzerinden tekil sözleşme kullanır.

#### `last_combat_results` — savaş sonucu kayıt formatı

`engine.combat_phase()` her çağrısında `engine.last_combat_results` listesi sıfırlanır ve yeniden doldurulur. Her eleman şu sözleşmeye uyar:

```python
{
    "pid_a":       int,   "pid_b":       int,   # dövüşen oyuncu PID'leri
    "pts_a":       int,   "pts_b":       int,   # toplam maç puanı (kill + combo + synergy)
    "kill_a":      int,   "kill_b":      int,   # combat point bucket; Phase 4 UI'da saf kill gibi etiketlenmez
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

**Pairing snapshot rule:** `get_current_pairings()` render anında `engine.swiss_pairs()` çağırmaz. VersusOverlay ve CombatOverlay, aynı tur için Phase 1.1 Step 5’te dondurulmuş eşleşme snapshot’ını okur.

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

The root game loop owns `ShopScene` as the permanent active canvas. Overlay states (`VersusOverlay`, `CombatOverlay`, `EndgameOverlay`) are managed by `ShopScene`’s internal Phase State Machine (`STATE_PREPARATION → STATE_VERSUS → STATE_COMBAT → STATE_ENDGAME`). Overlays do NOT hold references to each other — they communicate only through `GameState` and `EventBus`.

### 3.2 Lobby Scene

- **Strategy grid:** 8 strategy cards arranged in 2 rows × 4 columns. Each card: 180×220 px, 24px gap. Centered in screen.
- **Card content:** Strategy name (FONT_BOLD, 18px), flavor description (FONT_REGULAR, 13px, max 3 lines), starting stat preview.
- **Selection:** Left-click calls `GameState.initialize(strategy_idx)`. Then `ShopScene` is launched directly as the permanent root scene in `main.py`.
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
- Displayed as a compact 2-line panel under the gold counter.
- Line 1: title, e.g. `"Next Income"`.
- Line 2: monospace formula line:
  `Base: {b} + Interest: {i} + Streak: {s} + Bailout: {bail} = {total}`
- Values computed client-side from engine-readable fields:
  - `b` = engine base income (constant per GDD)
  - `i` = `min(floor(player.gold / 10), 5)` (interest, capped at 5)
  - `s` = `floor(abs(win_streak) / 3)` (applies only to win streak, not loss)
  - `bail` = `1 if player.hp < 75 else 0` + `2 if player.hp < 45 else 0`
- Typography: title uses UI bold font; formula line uses `FONT_MONO`, `FONT_SIZE_LABEL`, `COLOR_GOLD_TEXT`.

**"Opponents deciding..." overlay:**
- Triggered when `GameState.run_ai_turns()` is executing.
- Full-screen semi-transparent overlay (black, alpha 160).
- Centered text: `"Opponents deciding..."`, FONT_BOLD, FONT_SIZE_LARGE.
- No input is forwarded to any widget during this state.
- Dismissed automatically when `run_ai_turns()` returns.

### 3.4 Versus Overlay (Popup)

- **Trigger:** `ShopScene.set_phase(STATE_VERSUS)` after pairings are resolved.
- **Duration:** Dismissed after `SPLASH_DURATION_MS = 3000 ms` OR on any mouse click / SPACE key.
- **Layout:**
  - Background: full-screen dark overlay rendered over a blurred snapshot of the shop scene.
  - Center: Matchup string `"{P_label} vs {Opp_label} ({Opp_strategy})"`, FONT_BOLD, FONT_SIZE_LARGE.
  - Below: two horizontal HP bars (SPLASH_HP_BAR_W × SPLASH_HP_BAR_H) for each combatant with integer HP labels.
  - Top-right corner: `"Turn {N}"`, FONT_REGULAR, FONT_SIZE_HEADER.
  - Labels are read via `GameState.get_display_name(pid)`, not by directly assuming a `.name` field exists on the engine object.
- **On dismiss:** `ShopScene.set_phase(STATE_COMBAT)`.

### 3.5 Combat Overlay (Popup)

**Layout mirrors Shop scene panels (left / center / right), hex board visible, hand panel hidden.**

**Combat resolution — step sequence:**

Combat is NOT animated frame-by-frame. `engine.combat_phase()` resolves atomically. The Combat Overlay reads the resulting `passive_buff_log` and **replays** it as a timed terminal stream.

1. On Phase switch (`STATE_COMBAT`): call `engine.combat_phase()`. Store full result snapshot.
2. Normalize `GameState.get_last_combat_results()` + `GameState.get_passive_buff_log(pid)` (or an internal helper built from the same inputs) into an ordered list of terminal lines.
3. Stream lines to Combat Terminal at a rate of one line per 80 ms (configurable). Terminal scrolls automatically. No user input pauses this.
4. After all log lines are streamed, display the final damage equation prominently:
   `[Base] + [Alive/2] + [Rarity/2] + [Prefix bonus] = Final_Damage`
   where `Prefix bonus = GameState.get_prefix_bonus(human_pid)`.
5. After 1500 ms additional wait, transition: `ShopScene.set_phase(STATE_PREPARATION)` (or `STATE_ENDGAME` if game-end condition is met).

**`_prefix` visual rule:** If `get_prefix_bonus(pid) > 0`, the damage equation line MUST include the `[Prefix bonus]` term. If it is 0, the term is omitted from the display string. Omitting this term when the bonus is non-zero causes visible math desync and is a critical rendering bug.

**Combat Terminal spec:**
- Background: COLOR_TERMINAL_BG. Font: FONT_MONO, FONT_SIZE_BODY. Text color: COLOR_TERMINAL_FG.
- Terminal area: left panel lower zone, y from `SYNERGY_HUD_H` to `SCREEN_H`. Width: `LEFT_PANEL_W`.
- Lines are appended bottom-up (newest at bottom). Max visible lines: `floor(COMBAT_TERM_H / (FONT_SIZE_BODY + 4))`.
- Older lines scroll up. No scrollbar — terminal is non-interactive.
- Filter: terminal formatting uses the combat-relevant trigger set (`pre_combat`, `combat_win`, `combat_lose`, `card_killed`, `copy_2`, `copy_3`). It MUST NOT rely on a literal `entry.trigger == "combat"` check.

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
- Threshold source is explicit: use `COPY_THRESH = [4, 7]` normally, or `COPY_THRESH_C = [3, 6]` when `has_catalyst(pid)` is active. Eclipse does not modify copy-strengthening thresholds unless a later rule is added explicitly to this document.
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

### 5.3 Player Hub & Lobby Panel

`PlayerHub` ile `LobbyPanel` aynı şey değildir. `PlayerHub`, mevcut oyuncunun kompakt özet panelidir. `LobbyPanel` ise sağ kenardaki 8 oyunculuk skor/listing panelidir.

**PlayerHub (compact current-player summary):**
- **Height:** `PLAYER_HUB_H = 150`.
- **Layout:** 5 satırlı kompakt düzen.
- Row 1: başlık + `"Turn: N"`.
- Row 2: segmentli HP bar.
- Row 3: Gold kutusu + streak kutusu.
- Row 4: `★ Pts` + `Board N/37`.
- Row 5: gelecek tur gelir özeti.
- **Data source:** `get_hp(pid)`, `get_gold(pid)`, `get_win_streak(pid)`, `get_total_pts(pid)`, `get_turn()`, `get_board(pid)`, `get_interest_multiplier(pid)`.

**LobbyPanel (right sidebar scoreboard):**
- **Position:** x=`SCREEN_W-RIGHT_PANEL_W`, y=0, w=`RIGHT_PANEL_W`, h=`SCREEN_H`.
- **Rows:** 8 rows, each `LOBBY_ROW_H` px tall, centered vertically.
- **Row content:** rank badge, player label, HP number, segmented HP bar, optional highlight styling.
- **Click:** Left-click on any row → `GameState.active_board_pid = pid`. Board re-renders immediately using `GameState.get_board(pid)`.
- **Eliminated row:** darkened overlay + `"ELIMINATED"` label.
- **Identity source:** labels come from `GameState.get_display_name(pid)` and strategy visuals come from `get_strategy(pid)` or a strategy-to-icon bridge.
- **Icon assets:** UI icons are sprites, e.g. `sprites/icon_flame.png`, not SFX files.

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
| Shop BGM (Preparation Phase) | `music/shop_loop.ogg` | Music (loop) |
| Combat BGM (Combat Phase) | `music/combat_loop.ogg` | Music (loop) |
| Victory | `music/victory.ogg` | Music (one-shot) |

Audio channels: 1 music channel (via `pygame.mixer.music`), 8 SFX channels (via `pygame.mixer.Sound`).

### 5.6 EndGame Overlay (Popup)

- **Trigger:** `alive_players <= 1` OR `turn_counter == 50`.
- **Sort order:** surviving players are sorted by `player.hp` descending. Eliminated players are ordered using `GameState.get_elimination_order()` (latest eliminated ranks higher).
- **Table columns:** `Rank | Player | Strategy | Final HP | Total Pts | Evolutions | Rerolls | Win Streak Max`
- **Data source:** `GameState.get_stats(pid)` for `total_pts`, `evolutions`, `market_rolls`, `win_streak_max`; `get_hp(pid)` for Final HP; `get_display_name(pid)` for player label; `get_strategy(pid)` for strategy label.
- **Winner banner:** If exactly 1 alive player, render `"{GameState.get_display_name(pid)} WINS"` above the table in FONT_BOLD, 48px.
- **Restart button:** Bottom center. Calls `GameState.reset()` and re-initializes `ShopScene` in `STATE_PREPARATION`.

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

Bu bölümün amacı tarihsel eksik listesi değil, bugünkü sözleşme durumunu göstermektir. Phase 3c ile kapanan alanlar burada `✅ Var` olarak işaretlenir; hâlâ açık kalanlar ise sonraki Phase'ler için blocking gap sayılır.

#### `MockPlayer` — Mevcut vs. Gerekli

| Alan | Şu An | Gerekli Phase | Bloke Ettiği UI Feature |
|---|---|---|---|
| `name`, `hp`, `gold`, `hand` | ✅ Var | — | — |
| `strategy: str` | ❌ **EKSİK** | Phase 4 (item 23) | `VersusOverlay` matchup etiketi; strategy icon bridge |
| `win_streak: int = 0` | ✅ Var | Phase 3 (item 15) | `IncomePreview` streak terimi; `PlayerHub` streak göstergesi |
| `alive: bool = True` | ✅ Var | Phase 3 (item 17) | `LobbyPanel` ELIMINATED overlay; `get_alive_pids()` filtresi |
| `copies: Dict[str, int] = {}` | ✅ Var | Phase 3 (item 16) | Shop/Hand kart üzerindeki `"Copies: X/3"` etiketi |
| `total_pts: int = 0` | ✅ Var | Phase 4 (item 22) | `CombatTerminal` birikimli puan satırı |
| `turn_pts: int = 0` | ✅ Var | Phase 4 (item 22) | `CombatTerminal` anlık tur puanı |
| `passive_buff_log: list = []` | ✅ Var | Phase 3b (item 18) | `FloatingText` `"+N STATS"` kaynağı |
| `evolved_card_names: list = []` | ✅ Var | Phase 3b (item 20) | Evolved kart Platinum border tetikleyici |
| `stats: dict` | ✅ Var | Phase 4 (item 25) | `EndgameOverlay` tablo sütunları |

`stats` dict alanları ve başlangıç değerleri: `wins=0, losses=0, draws=0, market_rolls=0, evolutions=0, win_streak_max=0`.

#### `MockGame` — Mevcut vs. Gerekli

| Alan / Metod | Şu An | Gerekli Phase | Bloke Ettiği UI Feature |
|---|---|---|---|
| `turn: int = 1` | ✅ Var | Phase 3c (item 30) | `TimerBar` gerçek ratio; rarity ağırlığı display |
| `state: str = "SHOP"` | ✅ Var | — | — |
| `last_combat_results: list = []` | ✅ Var | Phase 4 (item 22) | `CombatTerminal` savaş log kaynağı |
| `swiss_pairs()` | ❌ **EKSİK** | Phase 4 (item 23) | `VersusOverlay` pairing snapshot |

`buy_card_from_slot()` içinde alım yapıldığında `player.copies[card_name] = player.copies.get(card_name, 0) + 1` güncellemesi de yapılmalıdır.

#### `MockPlayer.hand` tip farkı — köprü notu

Gerçek engine: `player.hand: List[Card]` — `Card` nesnesi.
MockGame: `player.hand: List[str | None]` — sadece kart isim string'i.

Bu fark `GameState.get_hand()` tarafından şeffaf biçimde köprülenir (her zaman sadece `str | None` döner). Ancak `GameState.place_card()` içindeki `hasattr(raw, 'rotation')` guard'ı bu farkı korumak için zorunludur (bkz. Section 2.4 çift-yazma sözleşmesi). Bu guard olmadan MockGame üzerinde `place_card()` çağrısı `AttributeError` fırlatır.

---

## 9. EXECUTION PLAN

**Yürütme sırası notu:** Aşağıdaki Phase blokları tarihsel olarak büyümüş durumda. Otoritatif uygulama sırası `Phase 0 -> Phase 1 -> Phase 2 -> Phase 3 -> Phase 3c -> Phase 3b -> Phase 3d -> Phase 4 -> Phase 4a guardrail'leri -> Phase 5` şeklindedir. Bir alt Phase, kendisine referans veren prerequisite kapanmadan başlatılmaz.

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
9. <span style="color:#4ade80">🟩 Implement the 5-step phase pipeline in `GameState`: `commit_human_turn()`, `run_ai_turns()` with timeout, `swiss_pairs()` snapshot wiring.</span>
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

### <span style="color:#4ade80">Phase 3 — Interaction & Feedback (🟩 TAMAMLANDI)</span>

14. <span style="color:#4ade80">🟩 **SynergyHUD** tamamen yeniden yazıldı: `_group_bonus(n) = min(18, floor(3*(n-1)^1.25))` formülü (GDD §8 birebir), 6-daire pip bar, tier milestone çizgileri (2/3/4/5/6 eşiğinde), 600 ms flash animasyonu, diversity bonus kutucuğu, combat log placeholder. `shop.py.update()` içinde `synergy_hud.update(dt_ms)` çağrısı mevcuttur. Bkz. `v2/ui/synergy_hud.py`.</span>
15. <span style="color:#4ade80">🟩 **IncomePreview** (`v2/ui/income_preview.py`) tam olarak implementedir: GDD §13.1 dört terim formülü (`base=3`, `interest`, `streak`, `bailout`). 2 satırlı panel tasarımı: Inter-Bold başlık + JetBrainsMono formül. Her terim ayrı renk (yeşil/altın/turuncu), sıfır değerler soluk gri. `_compute()` statik metod 14 unit test ile doğrulanmış. TimerBar altında tam opak dark navy backdrop üzerinde render edilir. Ekonomist faiz ölçeklemesi desteklenir.</span>
16. <span style="color:#4ade80">🟩 **Copy count tracking** uygulandı: `ShopScene._render_copy_labels()` her kart slotunun altına `"Copies: N/3"` etiketi çizer. Shop ve Hand panellerinin her ikisi kapsanır. `n < 3` → beyaz, `n == 3` → COLOR_GOLD_TEXT. `GameState.get_copies(card_name, 0)` üzerinden canlı okuma. MockPlayer.copies alım anında güncellenir.</span>
17. <span style="color:#4ade80">🟩 **PlayerHub** yeniden tasarlandı (`v2/ui/player_hub.py`): 5-satır compact layout (PLAYER_HUB_H=150 içinde). Satır 1: başlık + `"Tur: N"` sağda. Satır 2: segmentli HP bar. Satır 3: Gold kutusu + Streak kutusu (🔥 ≥3W turuncu / ▲ yeşil / nötr gri / ▼ kırmızı). Satır 4: `★ Pts: N` + `Board: N/37` kapasite barıyla. Satır 5: `→ +Ng gelecek tur` income özet. `sync()` artık `win_streak`, `total_pts`, `turn`, `board_used`, `next_gold` çeker.</span>

### <span style="color:#4ade80">Phase 3c — MockGame & GameState Adapter Patch (🟩 TAMAMLANDI)</span>

Bu phase'deki maddeler tamamlanmadan Phase 3b ve Phase 4 başlanamaz. Section 2.4 ve Section 8.1'deki tüm boşlukları kapatır. Maddeler sırayla uygulanır.

28. <span style="color:#4ade80">🟩 **`MockPlayer` genişletme:** `win_streak=0`, `alive=True`, `copies={}`, `total_pts=0`, `turn_pts=0`, `passive_buff_log=[]`, `evolved_card_names=[]`, `stats={wins,losses,draws,market_rolls,evolutions,win_streak_max}` — tümü `__init__()` içinde başlatıldı. 5 yeni unit test ile doğrulandı.</span>
29. <span style="color:#4ade80">🟩 **`MockGame` genişletme:** `last_combat_results: list = []` eklendi. `buy_card_from_slot()` içinde `copies` sayacı güncelleniyor. `reroll_market()` içinde `market_rolls` artırılıyor. 3 yeni unit test ile doğrulandı.</span>
30. <span style="color:#4ade80">🟩 **`GameState` 16 yeni accessor:** `get_turn()`, `get_alive_pids()`, `get_win_streak()`, `get_copies()`, `is_alive()`, `get_total_pts()`, `get_turn_pts()`, `get_last_combat_results()`, `get_passive_buff_log()`, `get_stats()`, `has_catalyst()`, `has_eclipse()`, `get_interest_multiplier()`, `get_turns_played()`, `get_current_pairings()`, `get_pool_copies()` — tümü `try/except` guard ile, tip-uyumlu varsayılan döner. Not: Phase 4 kimlik/combat-bridge accessors (`get_strategy()`, `get_display_name()`, `get_prefix_bonus()`, `get_elimination_order()`) bu batch'in dışında bırakılmıştır; Phase 4 başlamadan netleştirilmelidir.</span>
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

### <span style="color:#4ade80">Phase 3b — Visual Feedback & Animation (🟩 TAMAMLANDI)</span>

18. <span style="color:#4ade80">🟩 **FloatingText system:** rise + fade, stacking. `FLOAT_TEXT_RISE_PX_PER_SEC`, `FLOAT_TEXT_LIFETIME_MS`, `FLOAT_TEXT_FADE_START_MS` sabitleri `constants.py`'den okunur. Origin: hedef kartın board koordinatının center-top'u. Birden fazla FloatingText aynı koordinatta yığılırken 4 px dikey boşluk bırakılır. Kaynak: `GameState.get_passive_buff_log(pid)` entry'leri — `{"trigger": "copy_2"|"copy_3", "delta": N}` → `FloatingText(f"+{N} STATS (MILESTONE)", board_coord, COLOR_GOLD_TEXT)`. MultiManager wagon-queue ile uygulandı. `v2/ui/widgets.py`'de `FloatingTextManager` sınıfı.</span>
19. <span style="color:#4ade80">🟩 **Milestone detection at turn start:** `GameState.get_turns_played(0)` okunur. `has_catalyst(0)` durumuna göre eşik dizisi `COPY_THRESH_C = [3, 6]` (Catalyst aktif) veya `COPY_THRESH = [4, 7]` (normal) seçilir. Eşik aşımı tespit edildiğinde board'daki etkilenen kartlar için FloatingText spawn edilir. ShopScene `_check_tier_milestones()` içinde uygulandı.</span>
20. <span style="color:#4ade80">🟩 **Evolved card (`"E"` rarity) Platinum border rendering:** `card.rarity == "E"` string kontrolü kullanılır. Border rengi `COLOR_PLATINUM = (220, 220, 240)`, genişlik 4 px. Rarity badge: `"E"` karakteri, FONT_BOLD, 14 px, COLOR_PLATINUM arka plan. CardFlip `evolved=True, evolved_color` parametreleri ile uygulandı. UI/shop_panel.py ve ui/hand_panel.py'de CardFlip instantiation'ı güncellendi.</span>
21. <span style="color:#4ade80">🟩 **Audio events wired:** `AssetLoader.get_sfx()` çağrıları trigger noktalarında. Ön yükleme `ShopScene.__init__()` içinde `AssetLoader.preload_scene()` çağrısıyla. SFX (buy/place/reroll) ve music (shop/combat/lobby) preload edildi. ShopScene `_play_sfx()` helper metot ile çağrılar merkezi. `v2/assets/loader.py` SFX/music caching ve volume scaling uygulandı.</span>

### Phase 3d — Adapter / Contract Test Expansion (<span style="color:#f59e0b">⚠️ PHASE 4 ÖNCESİ ZORUNLU TEST HARDENING</span>)

Bu phase'in amacı mevcut `MockGame` tabanlı UI testlerini kaldırmak değil, onların üstüne iki yeni güvenlik katmanı eklemektir:

1. **Adapter / Contract tests:** `v2/core/game_state.py` ile gerçek `engine_core` arasındaki veri sözleşmesini doğrular.
2. **Real-engine smoke tests:** küçük ama yüksek değerli akışları gerçek engine ile sınar; tam UI entegrasyonu değildir.

**Test matrisi (otoritatif):**

| Katman | Amaç | Engine | Örnek dosyalar |
|---|---|---|---|
| UI unit / widget | Render ve etkileşim davranışı | `MockGame` | `tests/test_player_hub.py`, `tests/test_synergy_hud.py`, `tests/test_shop_panel.py` |
| Adapter / contract | `GameState` accessors ve bridge semantiği | gerçek `engine_core` | `tests/test_game_state_engine_contract.py` |
| Smoke / flow | turn, pairing, combat snapshot, elimination zinciri | gerçek `engine_core` | `tests/test_engine_turn_flow_smoke.py`, `tests/test_engine_combat_contract.py` |

**Kurallar:**

- `MockGame` testleri korunur; bunlar presentation/TDD hızı için hâlâ birinci sınıf katmandır.
- Phase 4 öncesi yeni işlerde yalnızca Mock test eklemek yeterli sayılmaz; ilgili contract veya smoke testi de eklenmelidir.
- Gerçek engine testleri sahne çizimi değil, veri sözleşmesi ve akış doğruluğu odaklı olmalıdır.
- Testler deterministik seed veya fixture ile çalışmalıdır; rastgelelik test oracle'ını bulanıklaştırmamalıdır.

31a. Add contract test coverage for pairing snapshot semantics. `GameState.get_current_pairings()` aynı tur içinde yeni eşleşme üretmez; `engine.swiss_pairs()` sonucu bir kez dondurulup okunur. Beklenen dosya: `tests/test_game_state_engine_contract.py`.
31b. Add contract tests for identity bridge. `get_display_name(pid)` ve `get_strategy(pid)` Mock ve gerçek engine şema farkını UI için tek sözleşmeye indirir. Beklenen dosya: `tests/test_game_state_engine_contract.py`.
31c. Add contract tests for combat snapshot shape. `get_last_combat_results()` beklenen key set'ini, `winner_pid`, `dmg`, `hp_before_*`, `hp_after_*` alanlarını taşır ve Phase 4 formatter için yeterlidir. Beklenen dosya: `tests/test_engine_combat_contract.py`.
31d. Add contract tests for combat semantics guardrails. `kill_a` / `kill_b` alanları saf kill diye etiketlenmez; test adı ve assertion'lar bu bucket'ları "combat score bucket" olarak ele alır. Beklenen dosya: `tests/test_engine_combat_contract.py`.
31e. Add contract tests for `_prefix` bridge math. `get_prefix_bonus(pid)` UI summary terimi olarak hesaplanır ve sıfır / sıfır-dışı koşulları ayrı doğrulanır. Beklenen dosya: `tests/test_game_state_engine_contract.py`.
31f. Add smoke tests for turn flow. `preparation_phase()` -> pairing snapshot -> `combat_phase()` -> turn progression -> alive player filtering zinciri küçük fixture ile doğrulanır. Beklenen dosya: `tests/test_engine_turn_flow_smoke.py`.
31g. Add smoke tests for elimination ordering. Yeni ölen oyuncu sırası `get_elimination_order()` veya eşdeğer cache üzerinden kararlı biçimde tutulur; Endgame sıralaması canlı HP ile birlikte doğrulanır. Beklenen dosya: `tests/test_engine_turn_flow_smoke.py`.
31h. Add smoke tests for copy / milestone compatibility. Gerçek engine üzerinde `passive_buff_log`, `copy_2`, `copy_3`, `has_catalyst()` ve `get_turns_played()` birlikte çalışır mı doğrulanır. Beklenen dosya: `tests/test_game_state_engine_contract.py`.
31i. Add smoke tests for rarity bridge stability. `CardData.rarity_level`, gerçek engine rarity formatı ve UI rarity badge aklındaki sözleşmeyi sessizce bozmaz. Mevcut `tests/test_card_database.py` genişletilir.
31j. Add pre-Phase-4 regression gate. Phase 4 feature diffinden önce minimum paket: `test_game_state.py` + ilgili widget testi + ilgili contract/smoke testi birlikte güncellenir.

### Phase 4 — Overlay Architecture & Combat Execution

**Otoritatif uygulama sırası:** (YENİ MİMARİ): Bu aşamada artık bağımsız Sahneler (Scenes) yaratmak yerine, `ShopScene` oyunun ana ve ölümsüz tahtası olarak kalacaktır. Dövüş ve eşleşme ekranları, `ShopScene`'in durumuna (Preparation -> Matchmaking -> Combat) bağlı olarak ekrana çizilen devasa Overlay (Pop-up) Container'larına dönüştürülmüştür. Bu sayede sahne geçişi sırasındaki veri/scroll kaybı ve state bozulması tamamen ortadan kaldırılmıştır.

22. Implement `ShopScene` Phase State Machine: `PREPARATION` ve `COMBAT` fazları kurulur. TimerBar 0'a ulaştığında shop inputları kilitlenir ve tahta karararak olay akışı Overlay'lere devredilir. (Klasik AutoChess mantığı).
23. Implement `VersusOverlay`: Bağımsız sahne yerine ShopScene üzerinde çalışan bir Popup Overlay olarak tasarlandı. `ShopScene`'in ortasında belirir. `GameState.get_current_pairings()` ile eşleşme çifti okunur. Matchup string `"{P_label} vs {Opp_label}"`. Belirli bir animasyon süresi (örn. 2s) bittiğinde yerini CombatOverlay'e bırakır.
24. Implement `CombatOverlay` & `CombatTerminal`: Bağımsız sahne yerine ShopScene üzerinde çalışan Pop-up olarak tasarlandı. `VersusOverlay` bitince ekrana bu gelir. `output/logs/hud_analysis.txt` şablonuna sadık kalarak motorun verbose dökümünü yukarıdan aşağı streaming (kayan metin) şeklinde akıtır. Hasar denklemi ve kimin hasar aldığı gösterilir. Bittiğinde ShopScene tekrar `PREPARATION` fazına uyanır.
25. Implement `EndgameOverlay`: Bağımsız sahne yerine ShopScene üzerinde çalışan Pop-up olarak tasarlandı. Eğer oyuncu elenirse veya maçı kazanırsa `ShopScene` üzerinde belirir. `GameState.get_stats(pid)` ve `get_elimination_order()` okuyarak skor tablosu (Rank | Player | Strategy | Final HP | Total Pts) basar. Restart butonu ile ana menüye dönülür.
26. Reroll button disabled state: `get_gold(0) < 2` → background `COLOR_DISABLED`, cursor default, click no-op.
27. End-to-end integration test (Overlay Flow): ShopScene'in bir fazdan (Hazırlık) Versus'a, oradan Combat'a, oradan tekrar yeni tura başarıyla döndüğü AAA testlerle doğrulanır.

### Phase 4a — Delivery Strategy & QA Sandbox (ANALYSIS-DRIVEN ADDITION)

**Amaç:** Bu bölüm, Phase 4 için yapılan analizden çıkan veri akışı, riskler ve teslim stratejisini bağlayıcı hale getirir. Bu bölüm planlama amaçlıdır; tek başına implementasyon onayı vermez. Aynı içeriğin ayrı doküman sürümü: `docs/phase4_delivery_strategy.md`.

**Bağlayıcı guardrail'ler:**

1. Her görev tek deliverable ile sınırlıdır. `VersusOverlay` ile başlanırsa aynı onay döngüsünde otomatik olarak `CombatTerminal` veya `CombatOverlay`’a geçilmez.
2. QA Sandbox zorunludur. Her görev, ilgili `test_*.py` dosyaları oluşturulmadan veya güncellenmeden tamamlanmış sayılmaz.
3. `"Görmediğim koda onay vermem"` kuralı bağlayıcıdır. Her görev, production diff ve ilgili test diff'i gösterildikten sonra durur.
4. `v2/` dosyaları `engine_core`'a doğrudan bağımlı hale getirilmez. Phase 4 erişimi `GameState` veya açık bir bridge/adapter katmanı üzerinden akar.
5. `passive_buff_log`, savaş anlatısına yardımcı veridir; tek başına tam combat truth olarak kabul edilmez.
6. Scene ve widget'lar normalize UI payload'u tüketmelidir. Raw engine object'leri, canlı board okuması ve score bucket'ları bir kez `GameState` veya formatter/bridge katmanında adapte edilmeli; alta display-ready veri inmelidir.

**Hedef veri akışı:**

```text
ShopScene Ready / prep commit
  -> GameState phase wrapper
  -> engine.preparation_phase()
  -> GameState stores pairings / turn snapshot
  -> ShopScene.set_phase(STATE_VERSUS)

VersusOverlay (Popup)
  -> reads pairing, hp, labels, turn from GameState only
  -> no combat resolution
  -> dismiss on timeout or input
  -> ShopScene.set_phase(STATE_COMBAT)

CombatOverlay (Popup)
  -> GameState combat wrapper
  -> engine.combat_phase()
  -> engine.last_combat_results populated
  -> player.passive_buff_log populated
  -> GameState accessors expose raw combat snapshot
  -> Combat formatter converts raw data into terminal lines + footer
  -> CombatOverlay streams lines at 80 ms/line
  -> post-combat transition logic decides STATE_PREPARATION vs STATE_ENDGAME
```

**Mevcut blocking gap'ler:**

Bu liste, canlı repo taramasının sonucudur. Erken Phase başlıklarındaki tarihsel "tamamlandı" işaretleri ile çelişirse, implementation öncesi source of truth olarak bu gap listesi kabul edilir.

1. `v2/ui/combat_terminal.py` hâlâ stub; terminal yüzeyi henüz yok.
2. `v2/ui/overlays/combat_overlay.py` hâlâ stub; combat snapshot, formatter, streaming ve çıkış geçişi için bir orchestration noktası yok.
3. `v2/ui/overlays/versus_overlay.py` yalnızca kısmi durumda; planlanan overlay sözleşmesini henüz uygulamıyor.
4. `v2/core/game_state.py` içinde hâlâ eksik orchestration metotları var: `sync_state()`, `commit_human_turn()`, `run_ai_turns()`, `get_combat_log()`, `get_prefix_bonus()`.
5. `v2/mock/engine_mock.py`, Phase 4 için gereken pairing ve kimlik verisini henüz sağlamıyor. Bugün `swiss_pairs()`, oyuncu `strategy` alanı ve terminal replay'e uygun combat fixture eksik.
6. Mock ve gerçek engine kimlik şeması ayrışıyor: Mock tarafta `name` var ama `strategy` yok; gerçek engine tarafında `strategy` ve `pid` var ama ayrı bir `name` alanı yok.
7. Shop tarafında hâlâ hardcoded sağ panel oyuncu verisi var; bu temizlenmeden yapılan Phase 4 geçişleri canlı veriyi sessizce bypass edebilir.
8. `v2/scenes/shop.py` Phase makinesi fade gecişlerini sunmuyor. Testle pin'lenmezse `PREP -> VERSUS -> COMBAT -> PREP/ENDGAME` faz akışı sessizce drift edebilir.
9. `v2/ui/synergy_hud.py`, `kill_a` / `kill_b` alanlarını saf kill puanıymış gibi okuyor; oysa canlı engine combat çözümünde bazı combat passive puanları da bu bucket'lara karışıyor. Bu alanların anlamı henüz dondurulmuş değil.

**Analiz nedeniyle zorunlu spec açıklamaları:**

1. Mevcut plan metni CombatTerminal için `entry.trigger == "combat"` filtresi diyor. Gerçek engine trigger'ları ise `pre_combat`, `combat_win`, `combat_lose`, `card_killed`, `copy_2`, `copy_3`. Bir normalizasyon katmanı eklenene kadar formatter, literal `"combat"` yerine "combat-relevant trigger set" yaklaşımı kullanmalıdır.
2. `passive_buff_log`, yalnızca pasif gerçekten stat gücü değiştirdiğinde kayıt düşer. Bazı combat pasifleri puan üretir ama stat artırmaz; bu olaylar logda görünmeyebilir.
3. Mevcut footer hasar denklemi, exact engine math gibi gösterilecekse eksiktir. Gerçek engine, turn-based scaling ve early-game cap de uygular. Bu nedenle footer ya tam hesaplamayı göstermeli ya da partial breakdown + final damage olarak açıkça etiketlenmelidir.
4. `_prefix` uygulaması da yanıltıcı olabilir. Combat çözümünde hidden `_prefix` bonusları kart bazında iç combat hesabına dağılır; plandaki board-geneli footer terimi ise UI summary olarak görülmelidir, exact internal application order olarak değil.

**Önerilen görev parçalama sırası:**

### `Pre-Task A - Phase State Machine Foundation` <span style="color:green">(🟩 TAMAMLANDI)</span>

Kapsam:
- `MockPlayer.pid` eklendi, `get_alive_pids()` düzeltildi.
- `GameState.freeze_pairings()` eklendi (eşleşmelerin her karede değişmesi engellendi).
- `get_prefix_bonus()` ve `MockGame.combat_phase/swiss_pairs` stub'ları eklendi.
- 4 adet kırık entegrasyon testi onarıldı (`mocker` kaldırıldı).
- `test_shop_scene_phase_machine.py` ile 12 AAA TDD sözleşme testi yazıldı (RED fazda).

### `Task A.1 - ShopScene Phase State Machine Core` <span style="color:green">(🟩 TAMAMLANDI)</span>

Kapsam:
- ShopScene içine `phase` property'si ve `set_phase()` eklenecek.
- `STATE_PREPARATION` dışındaki fazlarda inputlar (lock, reroll, buy vb.) yutulacak (ignore edilecek).
- `test_shop_scene_phase_machine.py` içindeki temel state ve input bloklama testleri yeşile dönecek.
- `STATE_VERSUS` bittiğinde → `STATE_COMBAT` fazına geçişini tetikle.
- `STATE_COMBAT` başladığında savaş matematiğini *sadece bir kez* çalıştır (Single-fire).
- `STATE_COMBAT` bittiğinde, hayatta 1'den fazla oyuncu varsa → `STATE_PREPARATION`. Tek oyuncu kaldıysa → `STATE_ENDGAME`.

### `Task A.2 - VersusOverlay Entegrasyonu` <span style="color:green">(🟩 TAMAMLANDI)</span>

Kapsam:
Sadece matchup splash sahnesi yapılır. Sadece pairing, hp, turn ve player label verisi okunur. Combat çözülmez, terminal streaming eklenmez.

Çıkış kriterleri:
Timeout dismiss çalışır. Click/SPACE dismiss çalışır. Sahne tek bir pairing'i combat verisine bağımlı olmadan gösterebilir.

QA Sandbox:
İlgili sahne testleri birinci sınıf deliverable olarak güncellenir.
Beklenen testler: `tests/test_versus_overlay.py` ve gerekirse `tests/test_game_state.py`.

### `Task B - CombatTerminal only` <span style="color:green">(🟩 TAMAMLANDI)</span>

Kapsam:
`CombatTerminal`, saf presentation widget olarak inşa edilir. Girdi sözleşmesi deterministic olmalıdır: preformatted `lines` + final `footer` string veya yapılandırılmış footer payload. Widget engine çağırmaz.

Çıkış kriterleri:
80 ms/satır streaming çalışır. Auto-scroll çalışır. En yeni satır altta görünür. Footer yalnızca satır akışı tamamlandıktan sonra görünür.

QA Sandbox:
Widget odaklı terminal testleri eklenir/güncellenir.
Beklenen testler: `tests/test_combat_terminal.py`.

### `Task C - CombatOverlay only` <span style="color:green">(🟩 TAMAMLANDI)</span>

Kapsam:
Combat çözümü scene entry point'ine bağlanır. `get_last_combat_results()` ve `get_passive_buff_log(pid)` okunur. Bunlar terminal payload'ına normalize edilir. Stream sonrası bekleme ve transition-out zamanı burada yönetilir.

Çıkış kriterleri:
Combat sahne girişinde tam bir kez çözülür. Terminal girdisi tek formatter yolundan gelir. Sahne replay sonrası doğru next state'i seçer.

QA Sandbox:
Combat scene entegrasyon testleri eklenir/güncellenir.
Beklenen testler: `tests/test_combat_overlay.py`.

### `Task D - Endgame and elimination separately` <span style="color:green">(🟩 TAMAMLANDI)</span>

Kapsam:
Elimination görünümü ve Endgame screen, terminal göreviyle paketlenmez. Combat replay akışı stabil olduktan sonra ayrı görev olarak ele alınır.

Çıkış kriterleri:
Yeni elenen oyuncular doğru görünür. Endgame tetikleyicisi combat çözümünden sonra doğrulanır.

QA Sandbox:
Endgame/elimination davranışı için ayrı testler eklenir/güncellenir.
Beklenen testler: `tests/test_endgame_overlay.py` ve ilgili lobby testleri.

**Risk kaydı:**

`Risk 1 - Silent math desync in footer`

Neden:
Combat sonrası kart silinmiş veya stat değişmiş canlı board üzerinden hasarı yeniden hesaplamak.

Azaltım:
`engine.combat_phase()` hemen sonrasında combat snapshot dondurulmalı; footer bu snapshot'tan türetilmelidir.

`Risk 2 - Incomplete combat narrative`

Neden:
`passive_buff_log`'u tek anlatı kaynağı olarak kullanmak.

Azaltım:
`last_combat_results` authoritative scoreboard truth olarak kalmalı, `passive_buff_log` ise flavor/context katmanı olarak kullanılmalıdır.

`Risk 3 - Mock and real engine drift`

Neden:
Mock şeması, Versus ve Combat sahnelerinin ihtiyaç duyduğu pairing ve kimlik sözleşmesini henüz karşılamıyor.

Azaltım:
Scene implementasyonundan önce minimal Phase 4 fixture sözleşmesi eklenmeli veya net biçimde belgelenmelidir.

`Risk 4 - Scope creep across tasks`

Neden:
"Madem girdik, tüm combat stack'i bitirelim" yaklaşımı.

Azaltım:
Her görev sonunda sert duruş. Diff, test diff ve risk notları görüldükten sonra bir sonraki deliverable açılır.

`Risk 5 - Hidden spec mismatch`

Neden:
Plan metni ile gerçek engine davranışı, trigger naming ve damage presentation konularında şimdiden ayrışmış durumda.

Azaltım:
Yukarıdaki açıklamalar, production code başlamadan önce bu ana plan dosyasına kilitlenmiştir ve bağlayıcı yorum olarak ele alınmalıdır.

**Her future task için agent checklist:**

1. Edit öncesi tam sahip olunan dosyaları açıkça yaz.
2. Görev sınırını dar tut ve istenen deliverable tamamlanınca dur.
3. Aynı görev içinde ilgili `test_*.py` dosyalarını güncelle.
4. Production diff ile test diff'ini birlikte göster.
5. Sonraki deliverable için yeni onay almadan otomatik ilerleme yapma.
6. Görev scene flow veya score presentation'a dokunuyorsa, transition ve score-semantics testleri aynı review döngüsünde güncellenmelidir.

**Phase 4a - İkinci Tarama Ekleri**

**Ek spec netleştirmeleri:**

1. `kill_a` / `kill_b`, bugün için güvenilir "saf kill" alanları değildir. Canlı engine'de bazı `combat_win` passive puanları da `last_combat_results` yazılmadan önce bu alanlara karışıyor. Bu nedenle UI katmanı bu alanları ya normalize etmeli ya da net etiketlemelidir.
2. Phase 4 için açık bir faz makinesi kontratı gerekiyor. Normal akış `STATE_PREPARATION -> STATE_VERSUS -> STATE_COMBAT -> STATE_PREPARATION` olmalıdır; `STATE_ENDGAME` yalnızca post-combat elimination/game-over kontrolünden sonra devreye girmelidir.
3. `CombatOverlay` ve `CombatTerminal`, raw engine object’leri değil normalize edilmiş formatter payload’larını tüketmelidir. Bridge/adapter katmanı dışında canlı board veya ham score bucket okuması yayılmamalıdır.

**Ek QA kapsamı:**

1. Phase transition validation: hedef akış testle pin'lenmeli; geçersiz doğrudan sıçrama, duplicate transition ve accidental skip durumları deterministik davranışla engellenmelidir.
2. Combat trigger single-fire coverage: `STATE_COMBAT` fazına girildiğinde combat tam bir kez çözülmeli; sonraki frame'lerde `update()` tekrar çalışsa bile ikinci kez tetiklenmemelidir.
3. Replay state capture: `last_combat_results`, UI replay formatter çalışmadan önce dondurulmuş olmalı; daha sonra canlı board'dan yeniden türetilmemelidir.
4. Timer/stream lifecycle: terminal stream zamanı, post-stream bekleme süresi ve varsa replay/popup timer başlangıç/decrement davranışı testle sabitlenmelidir.
5. Turn cleanup contract: turn increment, locked coordinate cleanup ve post-combat cleanup sırası replay verisi capture edildikten sonra doğrulanmalıdır.
6. Score semantics coverage: passive combat points ile gerçek kill points ayrımı için açık test yazılmalı; `CombatTerminal` ve `SynergyHud` bu iki kaynağı karıştırmamalıdır.

**Ek riskler:**

1. `kill_a` / `kill_b` bucket'ları saf kill gibi okunursa UI yanıltıcı skor anlatımı üretir.
2. Scene flow testle pin'lenmezse `Shop -> Versus -> Combat -> Shop/Endgame` dışına kayan veya double-combat üreten geçişler sessizce yerleşebilir.

### Phase 5a — Interface Bridge Fixes (CRITICAL DISCONNECTS)

> [!WARNING]
> While preparing to switch from `MockGame` to the real engine (`engine_core`), we identified massive architectural disconnects deep within the integration layer (`GameState`). If the switch is made without fixing these, the game will crash instantly upon the first card component interaction.

**1. The Hand Array Discrepancy (`player.hand`)**
*   **Engine Core Logic:** `player.hand` is a dynamically resizing list of `Card` objects (Length goes 0 -> 1 -> 2 ... up to `HAND_LIMIT`). When a card is placed, it is physically `.pop()`'ed out.
*   **UI Frontend Expectation:** The drag-and-drop systems (`HandPanel`) strictly rely on a fixed 6-element list containing `[str | None]` to preserve physical slot locations.
*   **The Danger:** The UI's `place_card` bridge directly executes `player.hand[i] = None`. This injects `None` into the engine's dynamic list. At the end of the combat phase, the engine loops over `list(player.hand)` to return unplaced cards to the pool. When it hits the UI-injected `None`, **a terminal crash occurs.**
*   **The Fix:** Rewrite `GameState.get_hand()` to translate the engine's dynamic array into a fixed 6-slot dictionary representation, and remap `GameState.place_card()` to `.pop()` the specific index intelligently without breaking UI slot layouts.

**2. Physical Shop Index Discrepancy**
*   **Engine Core Logic:** The real market simply delivers an array of options to the AI/player via `deal_market_window`. AI executes `player.buy_card(card)` directly.
*   **UI Frontend Expectation:** The user clicks a physical slot on screen (e.g. Slot `#2`). The UI calls `GameState.buy_card_from_slot(pid, slot=2)`.
*   **The Danger:** The `buy_card_from_slot()` method does not exist in the real engine! The Mock Engine had it, but the integration will raise `AttributeError`.
*   **The Fix:** Implement `buy_card_from_slot()` inside `GameState` mapping it to `engine.market._player_windows[pid][slot_idx]`, replacing the selection with `None` so the UI knows the slot is now empty, and manually running the backend's `player.buy_card(card)` taking gold into account.

**3. Shop Lock Stub**
*   **The Danger:** Locking the shop (`GameState.toggle_lock_shop`) was stubbed in MockGame. The real `engine_core` has no concept of it yet. Pressing the lock button in the real engine will crash.
*   **The Fix:** Safely intercept and ignore this action in the adapter.

### Phase 5b — The Time-Dilation Disconnect (CRITICAL ARCHITECTURE FLAW)

> [!CAUTION]
> The deepest and most destructive disconnect lies in how `engine_core` simulates time versus how a human plays the game. `engine_core` is a *simulator*.

**The Autochess Simulator Problem:**
*   **Engine Core Logic:** The `engine.preparation_phase()` function increments the turn, calculates income, deals market windows, runs AI buying, and runs AI placement **all in a single non-yielding microsecond method.**
*   **UI Frontend Expectation:** The human expects the turn to start, to receive their income, and to see a refreshed shop. Then they spend 30 seconds dragging cards, looking at the UI, rerolling the shop, and finally pressing the "READY" button.
*   **The Danger:** If `commit_human_turn()` blind-calls `engine.preparation_phase()`, the human starts Turn 1 with 0 gold and an empty shop. They have nothing to do, so they click "Ready". *Instantly*, the engine gives them gold, completely overrides any board placement, buys random cards with the AI fallback (`AI._buy_random` since strategy `"human"` isn't registered), and slams them straight into Combat.
*   **The Fix:** 
    1. **Split the Engine Execution:** We cannot use `engine.preparation_phase()` for interactive UI hookups. Instead, when the game boots (and after every combat), we must run a new `engine.start_turn()` logic that increments `turn`, gives `income`, applies passive triggers, and deals `deal_market_window` for all players.
    2. **Human Immunity:** We must register `"human"` as an explicit strategy in `engine_core/ai.py` that immediately `return`s gracefully, preventing the AI from stealing the human's gold or hand during automated steps.
    3. **AI Execution:** When the human presses "READY", the game must invoke `run_ai_turns()` which runs `_ai.buy` and `_ai.place` strictly for the bot players. After that, we proceed safely to Combat.

### Phase 5c — The Turn-Lifecycle Orchestrator (HIDDEN MECHANICS)

> [!CAUTION]
> If a human bypasses the `engine.preparation_phase()` by taking a manual turn, they accidentally bypass 4 critical sub-systems of the engine loop. We MUST manually execute these for the human upon clicking the "READY" button.

**1. The Interest System (apply_interest)**
*   The engine calculates interest *after* cards are bought (based on leftover gold). We must explicitly call `human.apply_interest()` when they click "Ready", otherwise the human will never earn interest!

**2. The Progression Systems (Evolutions & Copy-strengthening)**
*   The AI calculates `check_evolution` and `check_copy_strengthening` automatically at the end of its turn. If the human drags and drops cards manually, these functions are never triggered! We must explicitly call them during `commit_human_turn`.

**3. Market Pool Bleeding (return_unsold)**
*   Every turn, the engine deals 5 cards into the Shop. The AI buys 1, and crucially calls `market.return_unsold()` to put the other 4 back into the global pool. If the human's turn doesn't fire this, **the human permanently removes 5 cards from the pool every single turn without buying them!** 
*   **The Fix:** We must manually trigger `return_unsold(human)` inside `commit_human_turn`.

### Phase 5d — The Hidden 3 Catastrophes (FINAL ANALYSIS)

> [!CAUTION]
> A final sweep revealed 3 more hidden traps. `engine_core` never expected a human to die and stay connected, nor did it expect a human to reroll the shop.

**1. Spectator Drift (The Zombie Player)**
*   If the human's HP drops to 0, they are eliminated from the engine (`p.alive = False`). Their cards are returned to the pool, and they are skipped in future AI loops.
*   However, the `ShopScene` Phase Machine blindly loops everyone back to `STATE_PREPARATION` as long as there are >1 remaining players overall!
*   **The Danger:** A dead human gets sent back to the Shop, with 0 new income, no board, and active UI controls, allowing them to click Reroll/Buy on a broken state.
*   **The Fix:** When returning to `STATE_PREPARATION`, if `gs.is_alive(0) == False`, the UI must enter a locked "Spectating Mode", disabling drags, buying, and locking, until `STATE_ENDGAME` is triggered.

**2. The Missing "Reroll" Engine Method**
*   **The Danger:** The UI's Reroll button bridges to `GameState.reroll_market()`. This function tries to execute `self._engine.reroll_market(pid)`. But the actual real engine **doesn't even have this method!** AI bots don't reroll, so the method was never written. Clicking Reroll will crash the game with an `AttributeError`.
*   **The Fix:** We must manually implement reroll logic purely inside `GameState.reroll_market()`. It must verify gold, subtract `market.refresh_cost()`, call `market.return_unsold(human)`, and then run `market.deal_market_window(human)`.

**3. Test Determinism Leakage (RNG Drift)**
*   The phase rules strictly demand deterministic tests. However, `trigger_passive_fn` in `engine_core` uses the global `import random` rather than the `engine.rng`. Because passives like `rare_hunter` trigger chance-based effects, this global RNG call will subtly drift and break snapshot tests if not intercepted.

**4. Ghost Stats (Stat Kayması)**
*   **The Danger:** The UI (`ShopScene` and `HandPanel`) completely ignores dynamic engine stats! When it draws a card, it just asks the engine for the `card_name` string, then looks up the static base template directly from `CardDatabase.json`. If a card is strengthened via `copy_2` or a passive ability (e.g. its Power goes from 30 to 35), the engine fights with `35`, but the human will always see it rendered as `30`!
*   **The Fix:** We must modify `GameState.get_board_cards()` and `get_hand()` to return a bundle: `(card_name, dynamic_stats_dict)`. `ShopScene` and `CardDatabase.render_card_surface` must be updated to accept dynamic override values, ensuring the Pygame surface reflects the exact engine state, not the static JSON template.

### Phase 5e — The Ultimate Disconnects (DEEP ENGINE)

> [!CAUTION]
> The final sweep into how the engine executes mathematics and randomizations vs what the UI expects.

**5. The "Bait and Switch" Matchup (Kör Dövüşü)**
*   **The Danger:** To draw the "Versus Overlay" smoothly before combat, `GameState.freeze_pairings()` calls `engine.swiss_pairs()` and caches who the human fights (e.g., "YOU vs P2"). Then we proceed to `STATE_COMBAT` and call `engine.combat_phase()`. BUT `engine.combat_phase()` internally ignores the cache and manually calls `swiss_pairs()` **again**! Because pairings are randomly jittered by HP bands, the engine generates a *different* pairing. The UI shows you are fighting P2, but the engine secretly fights you against P7!
*   **The Fix:** We must modify `engine_core.game.py`'s `combat_phase(pairs=None)` to accept the UI's frozen pairs, bypassing the internal regeneration loop.

**6. Damage Cap Math Mystery (Bozuk Hasar Özeti)**
*   **The Danger:** The UI Terminal expects a pure mathematical string to explain the combat: `|W - L| + bonuses = Final`. But the real `engine_core.board.calculate_damage()` heavily scales damage over time: turns 1-5 have a 50% penalty, and turns 1-10 have a hard limit of `15` damage. This logic is hidden. The UI terminal will output mathematically impossible equations like `(24 + 5 + 3 = 15)`, leading the player to think the code is entirely broken.
*   **The Fix:** The `GameState.format_combat_logs` must be enhanced to manually recalculate and append warning strings like `(Early Game Limit: 15)` or `(Turn Penalty: 50%)` exactly when the engine applies them.

**7. The Zombie Board (Ölü Kartların Dirilişi)**
*   **The Danger:** The UI adapter `GameState` maintains its own local dictionary `self._board = {}`. When the human places a card, it writes to `self._board` AND the engine grid. BUT it never reads back! In AutoChess, combat damage permanently destroys weak cards and removes them from the grid. Because `GameState` never clears or re-syncs `self._board` from the engine after combat, the UI will eternally draw "Ghost Cards" that the engine has already deleted! The human will watch combat, see an empty hex, and think they are still fighting with a full board. (Furthermore, `ShopScene._board_flips` never garbage-collects deleted hexes!).
*   **The Fix:** `GameState` must completely abandon `self._board` caching when connected to the real engine. `get_board_cards()` and `get_board_rotations()` must dynamically read directly from `self._engine.players[0].board.grid` every frame. `ShopScene._update_board_cards` must garbage-collect stale `CardFlip` instances.

**8. Blackout of Evolved Cards (Evrim Silinmesi)**
*   **The Danger:** When an AI evolves a card, the engine dynamically instantiates a new Card object with the name `"Evolved <Base Name>"`. However, the UI relies on `CardDatabase.json` to draw images and stats. The JSON file *only* contains base cards! When the UI tries to lookup `"Evolved Narwhal"` to render an enemy's board or the combat logs, the database will return `None`. The entire Pygame rendering pipeline will instantly fallback to drawing **blank, empty grey polygons** for all evolved cards across the entire game, completely shattering visual feedback in the late-game.
*   **The Fix:** `CardDatabase.lookup()` must act as a smart proxy. If a card name starts with `"Evolved "`, it must dynamically lookup the base card, apply the engine's 72-point math scaling, and synthesize a mock `CardData` object in real-time so Pygame can draw the platinum borders.

**9. The "get_hand" Crash (Eksik Metod Çöküşü)**
*   **The Danger:** `GameState` features safe `try-except AttributeError` blocks for functions like `get_shop` and `get_hp` because the real engine doesn't exactly match the Mock framework. However, `GameState.get_hand` completely lacks this safety block! Since `engine_core.game.Game` does not have a `get_hand()` method at all, the moment the Pygame screen boots and tries to draw the hand panel, it will instantly throw an `AttributeError` and crash the window.
*   **The Fix:** We must wrap `GameState.get_hand` with a try-except block. Upon catching the `AttributeError`, it must directly access `self._engine.players[pid].hand`, extract the card names, and pad the list with `None` to satisfy exactly the 6 slots expected by the UI.

### Phase 5f — TDD Architecture Blueprint (Test Stratejisi)

Testleri yazmadan önce, çözümlerimizin "Ne"yi başaracağını ve TDD testlerinin bunu "Nasıl" kanıtlayacağını aşağıdaki vizyonla kuracağız:

1. **Player name vs pid (Identity)**
   *   *Test:* P0'ın `.name` verisine erişim yerine `get_endgame_stats` çağrısını test et. Beklenti: İstisna atmadan `P0` veya özel bir string dönmesi.
2. **Missing `buy_card_from_slot`**
   *   *Test:* `GameState.buy_card_from_slot` çağrıldığında motor pazarındaki sıradaki slotun çıkarılıp ele eklenmesini test et. Beklenti: Pazar havuzundan isim düşmesi ve elin büyümesi.
3. **Time Dilation (Split Phase)**
   *   *Test:* `start_turn()` çalıştırıldığında (hazırlık aşaması başladığında) insan board'unun kitlenmediğini, ancak AI sıralarının dönmek için `finish_turn()` beklediğini test et.
4. **Human Strategy Immunity**
   *   *Test:* AI motoru insan için döndüğünde insanın altınının eksilmediğini (`gold` sabit) ve pazardaki slotların değişmediğini doğrula.
5. **Interest & Strengthening Bypasses**
   *   *Test:* UI üzerinden `commit_human_turn()` atıldığında, faiz fonksiyonlarının sadece 1 tur çalıştığını ve faiz limitine sadık kalındığını kanıtla.
6. **Spectator Zombie Loop**
   *   *Test:* İnsan oyuncunun canı 0 olduğunda `GameState`'in herhangi bir tur aksiyonunu doğrudan reddetmesini ve zorla `Endgame`'e geçmesini test et.
7. **Reroll Interface Exception**
   *   *Test:* Motorun kendi içinde reroll olmamasına rağmen, `GameState.reroll_market` çağrımının altını 2 düşürüp havuzdan yeni 5 kart çekimini tetiklediğini onayla.
8. **Bait-and-Switch Matchup (Kör Dövüşü)**
   *   *Test:* UI'da `freeze_pairings` ile eşleştirme yapıp, ardından `combat_phase(pairs=frozen)` verdiğimizde RNG oynama payının eski listeyi ezmemesini sağla.
9. **Ghost Stats (Stat Kayması)**
   *   *Test:* Oyun içi kazanılan güçleri test etmek için `get_board_cards()`'ın `{coord: {name, power, hp}}` formatında paket dönmesini sağla.
10. **Damage Math Cap (Bozuk Hasar Özeti)**
    *   *Test:* Erken turlarda Combat Log formatının, motorun hasar formülündeki 15 barajını ve tur limitlerini string olarak okuduğunu doğrula.
11. **Ghost Board (Zombi Tahta)**
    *   *Test:* Savaşta bir kart silindikten sonra `GameState._board` üzerinden okumanın da o kartı sildiğini (veya direkt motordan veri geldiğini) doğrula.
12. **Evolved Card Blackout ve get_hand Crash**
    *   *Test:* `get_hand()` hatasını sarmalayıp 6'lık boş liste dönüp dönmediğini test et. `Lookup`'ın "Evolved" öneki için Base objenin klonunu yarattığını assert et.

### Phase 5g — Execution Plan (TDD DRIVEN BRIDGE)

> [!IMPORTANT]
> Handoff / Devir-Teslim: Bu aşamada test kodlaması başlayacaktır. Asla düzeltmeleri (fix) hemen koda dökmeyin. Önce `tests/test_engine_bridge_contracts.py` dosyasına girerek Phase 5f'te belirlenen 12 adet felaketi sistematik olarak çökeltecek KIRMIZI (Failed) testleri yazın. Ancak test tablosu kızardığında, hataları çözmek için `v2/core/game_state.py`, `v2/scenes/shop.py` ve `engine_core/game.py` dosyalarına müdahale edin.

**Engine Core Modifikasyonları Beklentisi:**
12 sorunun büyük çoğunluğu `GameState` adaptörü kullanılarak (motor ellenmeden) çözülecek. Ancak **3 kritik problem** için doğrudan `engine_core` içerisine müdahale sözleşmemiz var:
1. `engine_core/game.py`: Zaman paradoksundan kaçınmak için devasa `preparation_phase` fonksiyonunu `start_turn()` ve `finish_turn()` olarak iki parçaya bölmek ZORUNDAYIZ.
2. `engine_core/game.py`: Kör Dövüşü bug'ını önlemek için `combat_phase()` metoduna `pairs=None` şeklinde dışarıdan eşleşme alan bir parametre enjekte edeceğiz.
3. `engine_core/ai.py`: Botların insanın altınıyla ve kartlarıyla oynamasını önlemek için `ParameterizedAI` sınıfına `"human"` stratejisini (early-return yapan boş bir strateji olarak) tanıtacağız.

**The "Main Switch" (Final Entegrasyon ve Doğrulama):**
Tüm TDD testleri yeşile döndükten ve köprüler sağlamlaştırıldıktan sonra, en son adım olarak `v2/main.py` içerisindeki `MockGame()` başlatmasını silip yerine `engine_core.game_factory.build_game(policies=["human", "ai", ...])` koyarak gerçek motoru UI'a bağlayın. Ekran açıldığında ve loglara hata düşmediğinde **Oyun Resmen Entegre Edilmiş** demektir.
