# UI Components Analysis - 2026-04-17

## Overview
AutoChess Hybrid V2 has a comprehensive UI system with 18+ components implementing a "Digital Combat Interface (DCI)" aesthetic with cyberpunk/tactical styling.

## Key UI Components Status

### 1. MinimapHUD (`v2/ui/minimap_hud.py`) ✅
**Status**: COMPLETE - v13 Optimized Layout & Proportions
**Location**: Left sidebar, bottom (y=700, 340x380px - fills remaining space)
**Features**:
- Tactical hex grid visualization (37 hexes, 22px size - larger & centered)
- Category synergy dashboard with 6 categories (3x2 grid layout)
- Icon-based category display (ANKH, PALETTE, SEEDLING, PLANET, ATOM, LANDMARK)
- Real-time board state sync
- Glass-style UI with tactical color coding
- Seamless integration with SynergyHud
- Optimized proportions: 60% hex grid, 40% category dashboard
- Header with "TACTICAL OVERVIEW" label
- Separator line between sections

**Categories Tracked**:
- MYTHOLOGY (Yellow, ⚡)
- ART (Pink, ♪)
- NATURE (Green, ♣)
- COSMOS (Purple, ★)
- SCIENCE (Cyan, ⊕)
- HISTORY (Orange, ⚜)

**Key Methods**:
- `update(dt_ms, mouse_pos)` - Sync data and animations
- `_sync_data()` - Pull board state from GameState
- `_draw_hex_grid()` - Render tactical hex array
- `_draw_category_overlay()` - Icon-based synergy bars

### 2. SynergyHud (`v2/ui/synergy_hud.py`) ✅
**Status**: COMPLETE - DCI Refit (Digital Combat Interface)
**Location**: Left sidebar, top (y=0, height=700px)
**Features**:
- Group synergy tracking (MIND, CONNECTION, EXISTENCE)
- Tier system with pip visualization (6 pips per group)
- Passive combat log feed with animated entries
- Kinematic rolling numbers with lerp
- Flash animations for tier upgrades
- Trigger-based color coding
- Noise/grain texture overlay
- Scanline effects

**Sections**:
1. **Groups Box** (204px) - Synergy board with tier tracking
2. **Passive Feed** (320px) - Animated combat log terminal

**Trigger Colors**:
- copy_2/3: Gold (255, 200, 55)
- income: Green (70, 210, 130)
- combat_win: Green (100, 220, 120)
- combat_lose: Red (220, 80, 80)
- card_killed: Orange (255, 120, 40)
- combo: Gold (255, 215, 50)

**Key Methods**:
- `add_log(trigger, card_name, delta, res)` - Add animated log entry
- `update(dt_ms)` - Lerp animations and sync GameState logs
- `_compute_state()` - Calculate group bonuses and clusters
- `_trigger_burst(g_name)` - Visual burst effect on tier upgrade

### 3. PlayerHub (`v2/ui/player_hub.py`) ✅
**Status**: COMPLETE - DCI Refit
**Location**: Left sidebar, top (150px height)
**Features**:
- Octagon tactical plate design
- HP bar with 18 hex cells (ghost damage trail)
- Gold display with flash feedback
- Win/loss streak indicator
- Strategy score counter
- Income projection
- Holographic pulse animation
- Dynamic scanline effect
- Critical HP shake effect (<30 HP)

**Key Methods**:
- `sync(player_index)` - Pull data from GameState
- `update(dt_ms)` - Kinematic animations and flash decay
- `_render_hp_cell()` - 18-segment hex HP bar with ghost trail
- `_render_economy_row()` - Gold and streak boxes
- `_trigger_flash(key, color)` - Feedback flash effect

### 4. IncomePreview (`v2/ui/income_preview.py`) ✅
**Status**: COMPLETE
**Location**: Below shop panel (440x44px)
**Features**:
- Next turn income calculation
- Formula breakdown display
- Color-coded components (base, interest, streak, bailout)
- Economist multiplier support
- Gradient panel with neon border

**Formula**:
```
base = 3
interest = min(floor(gold/10), 5) * multiplier
streak = floor(win_streak/3)  [positive only]
bailout = +1 (HP<75) or +3 (HP<45)
total = base + interest + streak + bailout
```

**Key Methods**:
- `_compute(gold, hp, win_streak, multiplier)` - Calculate income
- `render(surface, pid)` - Draw 2-line preview panel

### 5. LobbyPanel (`v2/ui/lobby_panel.py`) ✅
**Status**: COMPLETE
**Location**: Right sidebar (full height)
**Features**:
- 8-player scoreboard
- Rank-based coloring (Top 3 special gradients)
- Segmented HP bars (5 HP per block)
- Category composition strips
- Hover scale effect (1.03x)
- Threat-based border color (blue→red as HP drops)
- Dead state overlay
- Click-to-spectate functionality

**Key Methods**:
- `update(mouse_pos)` - Hover detection
- `render(surface, players)` - Draw all player rows
- `_draw_segmented_health_bar()` - Block-based HP visualization
- `handle_event(event, players)` - Click detection for spectate

## UI Design System

### Color Palette (DCI Theme)
- **Void Background**: (10, 12, 18) - Deep carbon base
- **Glass Borders**: (42, 58, 92) - Tactical frame
- **Neon Accents**: (100, 150, 255) - Holographic pulse
- **Gold**: (255, 210, 60) - Economy/rewards
- **HP Full**: (60, 200, 100) - Healthy green
- **HP Low**: (220, 60, 60) - Danger red

### Group Colors
- **MIND**: (80, 140, 255) - Blue
- **CONNECTION**: (60, 200, 100) - Green
- **EXISTENCE**: (220, 60, 60) - Red

### Animation Techniques
1. **Kinematic Lerp**: Smooth value transitions with easing
2. **Flash Feedback**: Temporary color bursts on state changes
3. **Pulse Effects**: Sine-wave based glow animations
4. **Ghost Trails**: Delayed follow animations (HP damage)
5. **Scanlines**: Moving horizontal lines for tech aesthetic
6. **Noise Overlay**: Grain texture for depth

### Font System (`v2/ui/font_cache.py`)
- **Bold**: UI headers and important values
- **Mono**: Technical readouts and formulas
- **Icons**: Symbol rendering (HEART, GOLD, FIRE, SKULL, etc.)

## Integration Points

### GameState Dependencies
All UI components read from `GameState.get()`:
- `get_hp(pid)` - Player health
- `get_gold(pid)` - Player gold
- `get_board_cards(pid)` - Board state
- `get_win_streak(pid)` - Win/loss streak
- `get_total_pts(pid)` - Strategy score
- `get_passive_buff_log(pid)` - Combat log entries
- `get_interest_multiplier(pid)` - Economist bonus

### Event System
- UI components use `EventBus` for decoupled communication
- Flash effects triggered on state changes
- Log entries added via `add_log()` method

## Performance Optimizations
1. **Surface Caching**: Pre-rendered gradient panels
2. **Throttled Updates**: Lobby data cache with update limits
3. **Clipping Regions**: Scroll areas use surface clipping
4. **Lerp Smoothing**: Gradual value changes reduce visual jitter

## Known Issues & TODOs
1. ~~Category HUD removed from SynergyHud~~ - Now in MinimapHUD
2. Ghost card cleanup implemented in ShopScene
3. Duplicate log guard prevents spam
4. Icon rendering uses font_cache.render_icon()

## Next UI Improvements
1. **Combat Terminal** - Already complete, streaming at 80ms/line
2. **Overlays** - VersusOverlay, CombatOverlay, EndgameOverlay all complete
3. **Phase 5 Bridge** - UI ready, waiting for engine integration
4. **Spectator Mode** - Click-to-spectate working, needs dead player lock

## File Structure
```
v2/ui/
├── minimap_hud.py       # Tactical hex grid + category dashboard
├── synergy_hud.py       # Group synergy + passive log feed
├── player_hub.py        # HP/Gold/Streak display
├── income_preview.py    # Income calculation preview
├── lobby_panel.py       # 8-player scoreboard
├── shop_panel.py        # Shop interface
├── hand_panel.py        # Hand management
├── timer_bar.py         # Turn timer
├── combat_terminal.py   # Combat log streaming
├── card_flip.py         # Card animations
├── hex_grid.py          # Hex math utilities
├── widgets.py           # FloatingText, buttons
├── font_cache.py        # Font management
├── ui_utils.py          # Gradient panels, utilities
├── background_manager.py # Dynamic backgrounds
└── overlays/
    ├── versus_overlay.py   # Matchup splash
    ├── combat_overlay.py   # Combat execution
    └── endgame_overlay.py  # Game over screen
```
