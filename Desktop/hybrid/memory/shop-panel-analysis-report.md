# ShopPanel - Comprehensive Analysis Report
**Date**: 2026-04-17
**File**: `v2/ui/shop_panel.py`
**Status**: Fully Functional, DCI-Refit Complete

---

## 📋 Executive Summary

ShopPanel is the primary player interaction interface for card purchasing and shop management. It features a full-width tactical shelf design with 5 card slots, 3 action buttons, rarity statistics, and DCI (Digital Combat Interface) aesthetic.

**Key Stats**:
- **Lines of Code**: ~400
- **UI Elements**: 11 (5 cards + 3 buttons + stats + info + background)
- **Animation System**: CardFlip with hover effects
- **State Management**: GameState integration
- **Visual Style**: DCI Tactical Shelf (Octagon buttons, rim lights, glass panels)

---

## 🎨 Layout Structure

### Panel Dimensions
```
┌─────────────────────────────────────────────────────────────────┐
│ SHOP_BAY // ONLINE                                              │
│                                                                  │
│  [Card1] [Card2] [Card3] [Card4] [Card5]  [Stats] [Buttons]    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
Width: 1920px (full screen)
Height: 210px (Layout.SHOP_PANEL_H)
Position: y=0 (top of screen)
```

### Component Positions

| Component      | X Position        | Y Position | Width | Height | Notes                    |
|----------------|-------------------|------------|-------|--------|--------------------------|
| Main Panel     | 0                 | 0          | 1920  | 210    | Full width bar           |
| Card Slots (5) | CENTER_X + 20     | 12         | 160   | 186    | 20px gap between         |
| Stats Panel    | 1290              | 27         | 130   | 156    | Rarity probabilities     |
| Reroll Button  | 1415              | 27         | 140   | 42     | Top button               |
| Lock Button    | 1415              | 84         | 140   | 42     | Middle button            |
| Ready Button   | 1415              | 141        | 140   | 42     | Bottom button            |
| Info Panel     | 1570              | 12         | 340   | 186    | Hover card details       |

---

## 🃏 Card System

### Card Slots (5 Total)
**Layout**:
- Start X: `Layout.CENTER_ORIGIN_X + 20`
- Start Y: `12px` (vertical padding)
- Card Size: `160x186px`
- Gap: `20px`
- Total Width: `(160 * 5) + (20 * 4) = 880px`

### CardFlip Animation System
**Class**: `CardFlip` (from `v2/ui/card_flip.py`)

**Features**:
- Front/back surfaces (card art)
- Flip animation on hover
- Scale-up effect (hover)
- Evolved card detection (platinum border)
- Fallback rendering (if assets missing)

**States**:
```python
flip_progress = 1.0  # 0.0 = back, 1.0 = front
_flip_target = 1.0   # Target state
```

**Hover Behavior**:
- Mouse over → `hover_start()` → scale up + flip
- Mouse out → `hover_end()` → scale down + flip back

### Card Data Flow
```
GameState.get_shop(player_index=0)
    ↓
ShopPanel._card_names: list[str | None]
    ↓
ShopPanel._build_flips()
    ↓
AssetLoader.get_card_front/back(name)
    ↓
CardFlip objects with surfaces
    ↓
Render to screen
```

---

## 🎮 Button System

### 3 Action Buttons (DCI Octagon Design)

#### 1. REROLL Button
**Position**: Top (y=27)
**Label**: `"REROLL [2G]"`
**Icon**: `SYNC` (↻)
**Cost**: 2 gold
**Enabled**: `gold >= 2`
**Color**: Gold (255, 180, 50) / Gray (disabled)
**Action**: `GameState.reroll_market(player_index=0)`

#### 2. LOCK Button
**Position**: Middle (y=84)
**Label**: `"LOCK SHOP"` / `"LOCKED"`
**Icon**: `LOCK` (🔒)
**Cost**: Free
**Enabled**: Always
**Color**: Red (locked) / Gold (unlocked)
**Action**: `GameState.toggle_lock_shop(player_index=0)`

#### 3. READY Button
**Position**: Bottom (y=141)
**Label**: `"READY PHASE"`
**Icon**: `READY` (▶)
**Cost**: Free
**Enabled**: `phase == "STATE_PREPARATION"`
**Color**: Green (80, 255, 160)
**Action**: Returns `"READY"` signal → triggers phase transition

### DCI Button Rendering (`_render_dci_button`)

**4-Layer System**:
1. ~~Outer Glow~~ (REMOVED for readability)
2. **Glass Body**: Semi-transparent background with inner glow
3. **Borders & Rim Light**: Hue-shifted borders + top highlight
4. **Label & Icon**: Max contrast white text + vibrant icon

**Octagon Geometry**:
```python
cut = 8  # Corner cut size
points = [
    (x+cut, y), (right-cut, y), (right, y+cut),
    (right, bottom-cut), (right-cut, bottom), (left+cut, bottom),
    (left, bottom-cut), (left, y+cut)
]
```

**Hover Effects**:
- Inner glow alpha: 20 → 45
- Border width: 1 → 2
- Border alpha: +100

---

## 📊 Stats Panel

### Rarity Probability Display
**Position**: Left of buttons (x=1290)
**Size**: 130x156px
**Content**: Tier 1-5 probabilities

**Format**:
```
Tier 1: %100.0
Tier 2: %0.0
Tier 3: %0.0
Tier 4: %0.0
Tier 5: %0.0
```

**Data Source**: `GameState.get_rarity_probabilities()`
**Font**: Mono 9pt
**Color**: 
- Active (p > 0): (160, 160, 180)
- Inactive: (60, 65, 80)

---

## 🔄 State Management

### Sync System
**Method**: `sync()`
**Trigger**: After buy/reroll/turn start
**Logic**:
1. Fetch new shop data from GameState
2. Compare with current `_card_names`
3. **Smart Update**:
   - If only purchases (None slots) → Replace with MockCardBox
   - If real changes (reroll) → Full rebuild with `assign_shop()`

### Purchase Detection
```python
is_just_purchase = True
for i in range(5):
    if new_names[i] != old_names[i]:
        if new_names[i] is not None:
            is_just_purchase = False
            break
```

### MockCardBox
**Purpose**: Empty slot placeholder
**Appearance**: Dark gray box (30, 30, 30)
**Usage**: Replaces CardFlip when card is purchased

---

## 🎨 Visual Design

### Background System
**Type**: Gradient panel (UIUtils)
**Colors**:
- Top: (15, 18, 26, 255)
- Bottom: (10, 12, 18, 255)
**Border**: (42, 58, 92, 255)

**Decorative Elements**:
1. **Bottom Rim Light**: Cyan line (80, 140, 255, 180) - 2px thick
2. **Decal Line**: Subtle line 15px from bottom
3. **Decal Text**: "SHOP_BAY // ONLINE" (top-left, mono 9pt)

### Card Slot Insets
**Purpose**: Visual depth for empty slots
**Rendering**:
```python
# Inner shadow (rounded inset)
pygame.draw.rect(bg, (4, 6, 8, 180), slot_rect, border_radius=4)
# Border (depth)
pygame.draw.rect(bg, (0, 0, 0, 200), slot_rect, width=1, border_radius=4)
```

---

## 🔧 Event Handling

### `handle_event(event)` Flow

```
MOUSEBUTTONDOWN (left click)
    ↓
Check READY button → Return "READY"
    ↓
Check REROLL button → Call reroll_market() → Return True
    ↓
Check LOCK button → Call toggle_lock_shop() → Return True
    ↓
Check Card Slots (5) → Call buy_card_from_slot(idx) → Return True
    ↓
No match → Return False
```

**Return Values**:
- `"READY"`: Phase transition signal
- `True`: Action performed, refresh UI
- `False`: No action

### Debug Logging
All actions print debug info:
```python
print(f"[DEBUG] >>> SATIN AL: slot={idx}  kart='{name}'")
print(f"[DEBUG]     buy_card_from_slot -> {result}  | altin={gold}  el={hand_count}")
```

---

## 🎭 Animation System

### Update Loop
**Method**: `update(dt_ms)`
**Frequency**: Every frame (60 FPS)
**Actions**:
- Update all CardFlip animations
- Hover scale transitions
- Flip progress interpolation

### Hover System
**Method**: `handle_hover(mouse_pos)`
**Returns**: Hovered slot index (-1 if none)
**Behavior**:
- Hovered card: `flip.hover_start()`
- Other cards: `flip.hover_end()`

---

## 🔗 GameState Integration

### Read Operations
```python
state.get_shop(player_index=0)           # Card names
state.get_gold(player_index=0)           # Gold amount
state.get_phase()                        # Current phase
state.get_rarity_probabilities()         # Tier chances
state._engine.players[0].shop_locked     # Lock status
```

### Write Operations
```python
state.reroll_market(player_index=0)      # Reroll shop
state.toggle_lock_shop(player_index=0)   # Toggle lock
state.buy_card_from_slot(pid, slot_idx)  # Purchase card
```

---

## 🐛 Error Handling

### Try-Catch Blocks
1. **Asset Loading**: Fallback surfaces if assets missing
2. **GameState Access**: Graceful degradation if state unavailable
3. **Shop Sync**: Print traceback on errors
4. **Button Actions**: Catch and log exceptions

### Fallback Rendering
```python
def _make_fallback_surface(color, w, h):
    # Hexagon shape with border
    # Used when card assets not found
```

---

## 📈 Performance

### Optimization Techniques
1. **Surface Caching**: Background pre-rendered once
2. **Smart Sync**: Only rebuild changed cards
3. **Lazy Updates**: Render-time dt calculation
4. **Minimal Redraws**: CardFlip handles own dirty regions

### Draw Calls Per Frame
- Background: 1 blit
- Cards: 5 CardFlip renders
- Buttons: 3 polygon draws + text
- Stats: 5 text renders
- **Total**: ~20 draw calls

---

## 🎯 Current Issues & Limitations

### Known Issues
1. **Info Panel**: Defined but not rendered (rect exists, no content)
2. **Lock State**: Reads from `_engine.players[0].shop_locked` directly (fragile)
3. **Probabilities**: Empty dict fallback, no error display
4. **Hover Info**: No tooltip/card preview on hover

### Missing Features
1. **Card Tooltips**: Info panel not implemented
2. **Cost Display**: Card costs not shown on slots
3. **Rarity Indicators**: No visual tier markers on cards
4. **Animation Feedback**: No purchase/reroll animations
5. **Sound Effects**: No audio integration

---

## 🔮 Improvement Opportunities

### Visual Enhancements
1. **Card Cost Badges**: Show gold cost on each card
2. **Rarity Borders**: Color-coded borders by tier
3. **Purchase Animation**: Flash/fade effect on buy
4. **Reroll Animation**: Flip all cards simultaneously
5. **Hover Tooltips**: Full card stats in info panel

### UX Improvements
1. **Keyboard Shortcuts**: 1-5 for buy, R for reroll, Space for ready
2. **Drag to Buy**: Drag card to hand instead of click
3. **Right-Click Preview**: Show full card details
4. **Cost Indicators**: Red highlight if can't afford
5. **Lock Visual**: Padlock icon on locked cards

### Code Quality
1. **Separate Button Class**: Extract DCI button to reusable component
2. **Info Panel Implementation**: Complete the hover tooltip system
3. **Event System**: Use EventBus instead of return signals
4. **State Validation**: Check phase before allowing actions
5. **Asset Preloading**: Load all shop assets at init

---

## 📝 Code Metrics

| Metric                | Value |
|-----------------------|-------|
| Total Lines           | ~400  |
| Methods               | 10    |
| UI Elements           | 11    |
| Event Handlers        | 1     |
| Animation Objects     | 5     |
| External Dependencies | 5     |
| GameState Calls       | 8     |

---

## 🎨 Visual Style Guide

### Colors
- **Background**: Dark navy gradient (10-18)
- **Buttons**: Octagon glass with color accents
- **Text**: White (255) for max contrast
- **Icons**: Vibrant color-matched
- **Borders**: Hue-shifted for readability

### Typography
- **Button Labels**: Bold 12pt
- **Stats**: Mono 9pt
- **Decals**: Mono 9pt, low opacity

### Spacing
- **Card Gap**: 20px
- **Button Gap**: 15px (reroll-lock), 30px (lock-ready)
- **Padding**: 12px vertical, 20px horizontal

---

## ✅ Summary

**Strengths**:
✅ Clean DCI aesthetic
✅ Smooth CardFlip animations
✅ Smart sync system (purchase vs reroll)
✅ Robust error handling
✅ Octagon button design
✅ Full GameState integration

**Weaknesses**:
❌ Info panel not implemented
❌ No card cost display
❌ No hover tooltips
❌ Missing purchase animations
❌ No keyboard shortcuts

**Overall**: Solid foundation, ready for enhancement. Core functionality complete and stable.
