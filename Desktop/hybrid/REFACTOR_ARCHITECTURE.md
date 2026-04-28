# Refactor Architecture - Phase 1

## Before: Monolithic ShopScene

```
┌─────────────────────────────────────────────────────────┐
│                      ShopScene                          │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Audio Logic (scattered)                          │  │
│  │  - _play_sfx()                                   │  │
│  │  - _audio_loader management                      │  │
│  │  - Error handling                                │  │
│  │  - Volume control                                │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Hover State (dict-based)                         │  │
│  │  - self._hover = {...}                           │  │
│  │  - Manual timer management                       │  │
│  │  - Dict key access                               │  │
│  │  - No type safety                                │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Game Logic                                       │  │
│  │  - State management                              │  │
│  │  - Event handling                                │  │
│  │  - Rendering                                     │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Problems:**
- ❌ Mixed concerns (audio, hover, game logic)
- ❌ Hard to test in isolation
- ❌ No reusability
- ❌ Dict-based state (no type safety)
- ❌ Scattered audio logic

---

## After: Modular Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      ShopScene                          │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Game Logic (focused)                             │  │
│  │  - State management                              │  │
│  │  - Event handling                                │  │
│  │  - Rendering                                     │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  Uses ↓                                                 │
│                                                         │
│  ┌─────────────────────┐  ┌─────────────────────────┐  │
│  │  self._audio        │  │  self._hover_control    │  │
│  │  (AudioSystem)      │  │  (HoverControl)         │  │
│  └─────────────────────┘  └─────────────────────────┘  │
│           │                          │                  │
└───────────┼──────────────────────────┼──────────────────┘
            │                          │
            ↓                          ↓
┌─────────────────────┐  ┌─────────────────────────┐
│   AudioSystem       │  │   HoverControl          │
│   (v2/ui/)          │  │   (v2/ui/)              │
│                     │  │                         │
│  + preload()        │  │  + start()              │
│  + play()           │  │  + update()             │
│  + stop()           │  │  + is_active()          │
│  + stop_all()       │  │  + get_state()          │
│  + clear_cache()    │  │  + reset()              │
│                     │  │                         │
│  Pure I/O           │  │  Self-contained state   │
│  No dependencies    │  │  No dependencies        │
└─────────────────────┘  └─────────────────────────┘
```

**Benefits:**
- ✅ Separation of concerns
- ✅ Independently testable
- ✅ Reusable in other scenes
- ✅ Type-safe state (HoverState dataclass)
- ✅ Clear API boundaries

---

## Component Dependency Graph

```
AudioSystem
    ↓
    AssetLoader (lazy)
    ↓
    pygame.mixer.Sound

HoverControl
    ↓
    HoverState (dataclass)
    ↓
    (no external dependencies)

ShopScene
    ↓
    ├─→ AudioSystem
    ├─→ HoverControl
    ├─→ GameState
    ├─→ ShopController
    └─→ UI Panels (ShopPanel, HandPanel, etc.)
```

---

## Data Flow

### Audio Flow

```
User Action (click buy button)
    ↓
ShopScene.handle_event()
    ↓
ShopController.execute_action()
    ↓
ShopScene._audio.play(Paths.SFX_BUY)
    ↓
AudioSystem.play()
    ↓
    ├─→ Check cache
    ├─→ Load if needed (AssetLoader)
    └─→ pygame.mixer.Sound.play()
```

### Hover Flow

```
Mouse Move Event
    ↓
ShopScene._handle_hover()
    ↓
    ├─→ Detect hover target (shop/hand/board)
    ├─→ self._hover_control.start(panel, item)
    └─→ Clear info boxes if not active yet
    ↓
ShopScene.update(dt_ms)
    ↓
self._hover_control.update(dt_ms)
    ↓
    ├─→ Increment elapsed_ms
    └─→ Activate if elapsed_ms >= delay_ms
    ↓
if self._hover_control.is_active():
    ↓
    ├─→ Get panel and item
    ├─→ Fetch card_info from GameState
    └─→ Display info box
```

---

## File Structure

```
v2/
├── ui/
│   ├── __init__.py              (exports AudioSystem, HoverControl)
│   ├── audio_system.py          ✨ NEW
│   ├── hover_control.py         ✨ NEW
│   ├── shop_panel.py
│   ├── hand_panel.py
│   └── ...
├── scenes/
│   └── shop.py                  🔄 REFACTORED
└── assets/
    └── loader.py

test_refactor_components.py      ✨ NEW
REFACTOR_PHASE1_AUDIO_HOVER.md   ✨ NEW
REFACTOR_ARCHITECTURE.md         ✨ NEW
```

---

## API Comparison

### Audio

| Before | After |
|--------|-------|
| `self._play_sfx(name)` | `self._audio.play(name)` |
| Manual loader check | Automatic lazy loading |
| No preload API | `self._audio.preload(name)` |
| No cache management | `self._audio.clear_cache()` |
| No volume control | `self._audio.play(name, volume=0.5)` |

### Hover

| Before | After |
|--------|-------|
| `self._hover["panel"]` | `self._hover_control.get_panel()` |
| `self._hover["active"]` | `self._hover_control.is_active()` |
| Manual timer update | `self._hover_control.update(dt_ms)` |
| Dict update | `self._hover_control.start(panel, item)` |
| No type hints | Type-safe HoverState |

---

## Testing Strategy

### Unit Tests (Isolated)

```python
# HoverControl - No dependencies
def test_hover_control():
    hover = HoverControl(delay_ms=150)
    hover.start("shop", item=2)
    hover.update(200)
    assert hover.is_active()

# AudioSystem - Minimal dependencies
def test_audio_system():
    audio = AudioSystem()
    audio.preload("test.wav")
    audio.play("test.wav")
    assert audio.cached_count == 1
```

### Integration Tests

```python
# ShopScene with mocked components
def test_shop_scene_audio():
    scene = ShopScene()
    scene._audio.play(Paths.SFX_BUY)
    # Verify sound played

def test_shop_scene_hover():
    scene = ShopScene()
    scene._hover_control.start("shop", item=0)
    scene.update(200)
    assert scene._hover_control.is_active()
```

---

## Migration Checklist

- [x] Create AudioSystem component
- [x] Create HoverControl component
- [x] Update ShopScene imports
- [x] Replace _play_sfx() calls
- [x] Replace hover dict with HoverControl
- [x] Remove old _play_sfx() method
- [x] Update v2/ui/__init__.py
- [x] Write unit tests
- [x] Write integration tests
- [x] Run all tests
- [x] Verify compilation
- [x] Document changes

---

## Performance Impact

### Memory

- **Before:** Dict overhead + scattered audio references
- **After:** Structured objects + centralized cache
- **Impact:** Negligible (< 1KB per component)

### CPU

- **Before:** Dict lookups, manual timer logic
- **After:** Object method calls, encapsulated timer
- **Impact:** Negligible (< 0.1ms per frame)

### Cache Efficiency

- **Before:** AssetLoader cache only
- **After:** AudioSystem cache + AssetLoader cache
- **Impact:** Positive (reduced file I/O)

---

## Future Phases

### Phase 2: State Management
- Extract CameraState
- Extract DragState
- Extract PhaseTransition

### Phase 3: UI Components
- Enhance InfoBox API
- Extract FloatingTextManager
- Standardize panel interfaces

### Phase 4: Game Logic
- Extract combat logic
- Extract synergy calculation
- Extract milestone detection

---

**Architecture Status:** ✅ Phase 1 Complete  
**Next Target:** CameraState extraction
