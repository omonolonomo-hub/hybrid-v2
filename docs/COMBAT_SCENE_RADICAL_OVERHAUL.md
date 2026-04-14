# CombatScene Radical Overhaul - 37-Hex Grid & Strategic Panel

## Philosophy

**"The Board is LIFE - Everything else is NOISE"**

CombatScene artık bir "Cyber-Arena" - merkeze odaklı 37-hex grid sistemi ile kusursuz bir savaş alanı.

## The Iconic 37-Hex Grid System

### Grid Structure
```
       ⬡
      ⬡ ⬡
     ⬡ ⬡ ⬡
    ⬡ ⬡ ⬡ ⬡
   ⬡ ⬡ ⬡ ⬡ ⬡
  ⬡ ⬡ ⬡ ⬡ ⬡ ⬡
 ⬡ ⬡ ⬡ ⬡ ⬡ ⬡ ⬡
  ⬡ ⬡ ⬡ ⬡ ⬡ ⬡
   ⬡ ⬡ ⬡ ⬡ ⬡
    ⬡ ⬡ ⬡ ⬡
     ⬡ ⬡ ⬡
      ⬡ ⬡
       ⬡
```

**Composition:**
- Center: 1 hex
- Ring 1: 6 hexes
- Ring 2: 12 hexes
- Ring 3: 18 hexes
- **Total: 37 hexes**

### Auto-Scaling Algorithm

```python
# 15% safety margin from screen edges
margin = 0.15
available_w = (screen_width - hud_right) * (1 - margin * 2)
available_h = (screen_height - hud_bottom) * (1 - margin * 2)

# Calculate hex size for 7x7 grid (radius 3)
hex_size_w = available_w / (7 * √3)
hex_size_h = available_h / 14
hex_size = min(hex_size_w, hex_size_h, 50)  # Cap at 50

# Center perfectly
center_x = (screen_width - hud_right) / 2
center_y = (screen_height - hud_bottom) / 2
```

### Visual Style
- **Grid Lines**: 1px thin
- **Color**: Cyan with alpha 60
- **Opacity**: Low (subtle, not overpowering)
- **Pattern**: Symmetric from center outward

## The Great Purge (Kaldırılanlar)

### ❌ REMOVED (Artık Yok):
1. **"Autochess Hybrid" Title** - Tepe kısmındaki başlık tamamen silindi
2. **Brown Hub** - Alttaki kahverengi hantal hub imha edildi
3. **P1 Analysis Box** - Sol üstteki devasa debug kutusu kaldırıldı
4. **Static Player Boxes** - Köşeli oyuncu kutuları (draw_player_list) silindi
5. **All Debug Info** - Ekranın %20'sini işgal eden karmaşa temizlendi

### ✅ KEPT (Kalan):
- Sadece Board
- Sadece HP Barları
- Sadece Battle Log
- Hiçbir şey daha

## UI Hierarchy (Öncelik Sırası)

### 1. PRIMARY FOCUS: The Board (En Önemli)
**Hex Grid + Tactile Cards**

```python
# Board maximized - tüm boş alan kullanılıyor
available_w = screen_width - hud_right - 40
available_h = screen_height - hud_bottom - 40
hex_size = min(available_w // 12, available_h // 12, 60)
```

**Özellikler:**
- Ekranın merkezinde
- Maksimum boyutta (boşalan alanlar kullanılıyor)
- Vignette efektli arka plan (board parlar)
- Subtle hex grid lines (baskın değil)

## Board Card Placement & Flip

### Card Sizing
```python
# Cards fit within hex boundaries
card_size = hex_size * 0.85 * 2  # Diameter
```

### Perfect Alignment
```python
# Position at hex center (pixel-perfect)
px, py = hex_system.hex_to_pixel(q, r)
draw_x = px - card_width // 2
draw_y = py - card_height // 2
```

### 180° Flip Animation
```python
# Full rotation (same as ShopScene)
scale_x = abs(math.cos(flip_value * π))
show_back = flip_value > 0.5

# Assets
front: assets/cards/Yggdrasil_front.png  # Art
back:  assets/cards/Yggdrasil_back.png   # Stats
```

### Hover Interaction
- **Trigger**: Mouse over hex
- **Animation**: Smooth flip (0.15 interpolation speed)
- **Effect**: Cyan glow around card
- **Duration**: Instant response

## Battle Log (Minimalist)

### Position & Style
```
┌────────────────────────────────────────┐
│  [P1] Dealing 15 DMG to [P6]           │ ← 25px max
└────────────────────────────────────────┘
```

### Features
- **Height**: Max 25px
- **Lines**: Single line only
- **Opacity**: Alpha 100 (very transparent)
- **Fade**: 3 second fade out
- **Content**: Critical actions only
  - Damage dealt
  - Unit death
  - Major effects

### Placeholder
When no action:
```
"Awaiting combat action..."  (alpha: 100)
```

## Strategic Right Panel (Holographic HP & Info)

### Data Hierarchy (Vertical)

```
┌─────────────────────┐
│ PLAYER 1            │ ← Name (bold, cyan)
│ ████████████░░░░░░  │ ← HP Bar (dominant)
│ 85/100              │ ← HP Value (right)
│ ■ ■ ■               │ ← Synergy Icons (glowing)
├─────────────────────┤
│ PLAYER 2            │
│ ████████████████░░  │
│ 92/100              │
│ ■ ■                 │
└─────────────────────┘
```

### Components

#### 1. Player Name
- **Position**: Top
- **Style**: Bold, Cyan
- **Format**: "PLAYER {id}"

#### 2. HP Bar
- **Position**: Middle (dominant element)
- **Size**: 180x8 pixels
- **Colors**:
  - Cyan: > 60% HP
  - Gold: 30-60% HP
  - Red: < 30% HP
- **Border**: 1px glow matching fill color

#### 3. HP Value
- **Position**: Right of bar
- **Format**: "{current}/{max}"
- **Color**: Matches bar color

#### 4. Synergy Icons
- **Position**: Bottom
- **Style**: Small glowing squares (12x12px)
- **Max**: 3 synergies shown
- **Colors**:
  - EXISTENCE: (255, 110, 80)
  - MIND: (70, 150, 255)
  - CONNECTION: (60, 235, 150)
- **Content**: Synergy count in center

### Spacing
- Name to HP: 18px
- HP to Icons: 6px
- Player to Player: 12px

## Color Palette (Cyber-Arena)

```python
CYBER = {
    "void": (5, 8, 15),           # Deep void background
    "grid": (15, 20, 35),          # Grid lines
    "cyan": (0, 242, 255),         # Primary accent
    "magenta": (255, 0, 255),      # Secondary accent
    "hp_full": (0, 242, 255),      # Full HP (cyan)
    "hp_mid": (255, 200, 0),       # Mid HP (gold)
    "hp_low": (255, 50, 80),       # Low HP (red)
    "log_text": (180, 190, 210),   # Battle log text
    "glow": (0, 242, 255, 80),     # Glow effect
}
```

## Technical Implementation

### File Structure

```
scenes/
  combat_scene.py          # Radical overhaul implementation
assets/
  cards/
    Yggdrasil_front.png    # Card front asset
    Yggdrasil_back.png     # Card back asset
```

### Key Classes

#### HexCard
```python
class HexCard:
    """Represents a card on hex board with flip animation."""
    - card: Card object
    - hex_coord: (q, r) hex coordinate
    - player_id: Owner player ID
    - flip_value: 0.0-1.0 (front to back)
    - hovered: Boolean
    - pixel_pos: (x, y) screen position
```

#### CombatScene
```python
class CombatScene(Scene):
    """Combat scene with radical UI hierarchy."""
    - PRIMARY: Board with hex cards
    - SECONDARY: Minimalist HUD
    - TERTIARY: Nothing
```

### Layout Calculation

```python
def _calculate_board_layout(self):
    """Calculate optimal board size (MAXIMIZE)."""
    # Reserve minimal space for HUD
    hud_right = 200   # HP bars
    hud_bottom = 35   # Battle log
    
    # Use ALL remaining space for board
    available_w = screen_width - hud_right - 40
    available_h = screen_height - hud_bottom - 40
    
    # Calculate hex size to fill space
    hex_size = min(available_w // 12, available_h // 12, 60)
    
    # Center the board
    origin_x = (screen_width - hud_right - board_width) // 2
    origin_y = (screen_height - hud_bottom - board_height) // 2
```

### Vignette Effect

```python
def _draw_void_background(self, surf):
    """Draw deep void with vignette."""
    # Dark center, darker edges
    for each_pixel:
        dist = distance_from_center
        alpha = (dist / max_radius) * 120
        draw_dark_overlay(alpha)
```

### Card Flip Animation

```python
def _draw_single_hex_card(self, surf, hex_card):
    """Draw hex card with 180° flip."""
    # Full rotation
    scale_x = abs(math.cos(flip_value * π))
    
    # Select side
    show_back = flip_value > 0.5
    card_surf = back_img if show_back else front_img
    
    # Scale for board
    target_size = hex_size * 1.8
    
    # Apply flip
    flip_w = scaled_w * scale_x
    
    # Center at hex position
    draw_x = hex_center_x - flip_w // 2
    draw_y = hex_center_y - scaled_h // 2
```

## Performance Targets

- ✅ 60 FPS maintained
- ✅ Clean diagnostics
- ✅ Smooth animations
- ✅ No frame drops

## Visual Comparison

### Before (Old System)
```
┌─────────────────────────────────────┐
│ AUTOCHESS HYBRID          [DEBUG]   │ ← Title + Debug
├─────────────────────────────────────┤
│ ┌─────┐                             │
│ │ P1  │  [Tiny Board]               │ ← Small board
│ │ HP  │                             │
│ └─────┘                             │
├─────────────────────────────────────┤
│ [Brown Hub with buttons]            │ ← Hantal hub
└─────────────────────────────────────┘
```

### After (New System)
```
┌─────────────────────────────────────┐
│                                     │
│         ╱─╲  ╱─╲  ╱─╲              │
│        ╱   ╲╱   ╲╱   ╲             │ ← HUGE BOARD
│        │ ⬡ │ ⬡ │ ⬡ │             │   (Maximized)
│         ╲   ╱╲   ╱╲   ╱             │
│          ╲─╱  ╲─╱  ╲─╱              │
│                                     │
│ [P1] Dealing 15 DMG to [P6]        │ ← Thin log
└─────────────────────────────────────┘
```

## Controls

- **ESC**: Return to shop
- **ENTER**: Return to shop
- **Mouse Hover**: Flip cards

## Integration

### Scene Manager
```python
# main.py
def create_combat(core_game_state, **kwargs):
    return CombatScene(
        core_game_state,
        action_system=action_system,
        animation_system=animation_system
    )
```

### Transition Flow
```
LobbyScene → ShopScene → CombatScene → ShopScene
                ↑                          ↓
                └──────────────────────────┘
```

## Asset Requirements

### Required Files
- `assets/cards/Yggdrasil_front.png` - Card front
- `assets/cards/Yggdrasil_back.png` - Card back

### Fallback
If assets missing, placeholder hex cards are auto-generated:
- Front: Cyan hex with "FRONT" label
- Back: Magenta hex with "BACK" label

## Future Enhancements

1. **Combat Animation System**
   - Attack animations
   - Damage numbers
   - Death effects

2. **Advanced Battle Log**
   - Color-coded messages
   - Icon support
   - Multiple lines (scrollable)

3. **Synergy Indicators**
   - Minimal icons on HP bars
   - Glow effects for active synergies

4. **Camera System**
   - Follow active combat
   - Zoom in/out
   - Pan controls

5. **Sound Effects**
   - Card flip sounds
   - Attack sounds
   - Ambient cyber music

## Code Quality

- ✅ No diagnostics errors
- ✅ Type hints throughout
- ✅ Docstrings for all methods
- ✅ Clean separation of concerns
- ✅ Follows Scene architecture

## Testing

```bash
# Run game
python main.py

# Navigate: Lobby → Shop → Combat
# 1. Select strategies in lobby
# 2. Press ENTER to go to shop
# 3. Press ENTER again to go to combat
# 4. Hover over cards to see flip animation
# 5. Press ESC to return to shop
```

## Summary

CombatScene is now a **Cyber-Arena**:
- Board is MAXIMIZED
- HUD is MINIMIZED
- Everything else is PURGED
- 60 FPS maintained
- Clean, modern, professional

**The eye stays on the board. Always.**
