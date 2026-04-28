# Refactored Components - Usage Examples

## AudioSystem

### Basic Usage

```python
from v2.ui import AudioSystem
from v2.constants import Paths

# Initialize
audio = AudioSystem()

# Preload sounds (recommended in scene.on_enter())
audio.preload(Paths.SFX_BUY)
audio.preload(Paths.SFX_PLACE)
audio.preload(Paths.SFX_REROLL)

# Play sound
audio.play(Paths.SFX_BUY)

# Play with custom volume
audio.play(Paths.SFX_PLACE, volume=0.5)

# Stop specific sound
audio.stop(Paths.SFX_BUY)

# Stop all sounds
audio.stop_all()

# Clear cache (e.g., on scene exit)
audio.clear_cache()

# Check cache size
print(f"Cached sounds: {audio.cached_count}")
```

### In a Scene

```python
class MyScene(Scene):
    def __init__(self):
        super().__init__()
        self._audio = AudioSystem()
    
    def on_enter(self):
        # Preload all sounds for this scene
        self._audio.preload(Paths.SFX_BUY)
        self._audio.preload(Paths.SFX_SELL)
        self._audio.preload(Paths.SFX_PLACE)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.buy_button.collidepoint(event.pos):
                self._audio.play(Paths.SFX_BUY)
                self._execute_buy()
    
    def on_exit(self):
        # Clean up
        self._audio.stop_all()
        self._audio.clear_cache()
```

### Error Handling

```python
# AudioSystem handles errors gracefully
audio = AudioSystem()

# If file doesn't exist, play() fails silently
audio.play("nonexistent.wav")  # No crash, just no sound

# Same with preload
audio.preload("missing.wav")  # No crash
```

---

## HoverControl

### Basic Usage

```python
from v2.ui import HoverControl

# Initialize with custom delay
hover = HoverControl(delay_ms=150)

# Start hover on an item
hover.start("shop", item=2)

# Update timer (call every frame)
hover.update(dt_ms)

# Check if hover is active
if hover.is_active():
    panel = hover.get_panel()  # "shop"
    item = hover.get_item()    # 2
    print(f"Hovering over {panel} item {item}")

# Reset hover
hover.reset()
```

### In a Scene

```python
class MyScene(Scene):
    def __init__(self):
        super().__init__()
        self._hover = HoverControl(delay_ms=150)
        self._info_box = InfoBox()
    
    def _handle_hover(self, mouse_pos):
        # Detect what's under the mouse
        shop_idx = self._get_shop_slot_at(mouse_pos)
        board_coord = self._get_board_coord_at(mouse_pos)
        
        if shop_idx != -1:
            # Start hover on shop slot
            self._hover.start("shop", item=shop_idx)
            if not self._hover.is_active():
                self._info_box.hide()
        elif board_coord:
            # Start hover on board
            self._hover.start("board", item=board_coord)
            if not self._hover.is_active():
                self._info_box.hide()
        else:
            # No hover target
            self._hover.reset()
            self._info_box.hide()
    
    def update(self, dt_ms):
        # Update hover timer
        self._hover.update(dt_ms)
        
        # Show info box when hover is active
        if self._hover.is_active():
            panel = self._hover.get_panel()
            item = self._hover.get_item()
            card_data = self._get_card_data(panel, item)
            self._info_box.show(card_data)
```

### Advanced: Multiple Hover Zones

```python
class ComplexScene(Scene):
    def __init__(self):
        super().__init__()
        # Different delays for different zones
        self._shop_hover = HoverControl(delay_ms=100)
        self._board_hover = HoverControl(delay_ms=200)
        self._hand_hover = HoverControl(delay_ms=150)
    
    def _handle_hover(self, mouse_pos):
        shop_idx = self._get_shop_slot_at(mouse_pos)
        board_coord = self._get_board_coord_at(mouse_pos)
        hand_idx = self._get_hand_slot_at(mouse_pos)
        
        # Reset all hovers first
        self._shop_hover.reset()
        self._board_hover.reset()
        self._hand_hover.reset()
        
        # Start appropriate hover
        if shop_idx != -1:
            self._shop_hover.start("shop", item=shop_idx)
        elif board_coord:
            self._board_hover.start("board", item=board_coord)
        elif hand_idx != -1:
            self._hand_hover.start("hand", item=hand_idx)
    
    def update(self, dt_ms):
        # Update all hovers
        self._shop_hover.update(dt_ms)
        self._board_hover.update(dt_ms)
        self._hand_hover.update(dt_ms)
        
        # Show appropriate info box
        if self._shop_hover.is_active():
            self._show_shop_info(self._shop_hover.get_item())
        elif self._board_hover.is_active():
            self._show_board_info(self._board_hover.get_item())
        elif self._hand_hover.is_active():
            self._show_hand_info(self._hand_hover.get_item())
```

### Using HoverState

```python
from v2.ui import HoverControl, HoverState

hover = HoverControl()
hover.start("shop", item=5)
hover.update(200)

# Get full state object
state: HoverState = hover.get_state()

print(f"Panel: {state.panel}")        # "shop"
print(f"Item: {state.item}")          # 5
print(f"Elapsed: {state.elapsed_ms}") # 200
print(f"Active: {state.active}")      # True

# HoverState is immutable (dataclass)
# state.panel = "board"  # This would fail
```

---

## Combined Usage

### Shop Scene Example

```python
class ShopScene(Scene):
    def __init__(self):
        super().__init__()
        self._audio = AudioSystem()
        self._hover = HoverControl(delay_ms=150)
        self._info_box = InfoBox()
    
    def on_enter(self):
        # Preload all audio
        self._audio.preload(Paths.SFX_BUY)
        self._audio.preload(Paths.SFX_SELL)
        self._audio.preload(Paths.SFX_PLACE)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self._hover.is_active():
                panel = self._hover.get_panel()
                item = self._hover.get_item()
                
                if panel == "shop":
                    self._buy_card(item)
                    self._audio.play(Paths.SFX_BUY)
                elif panel == "board":
                    self._sell_card(item)
                    self._audio.play(Paths.SFX_SELL)
        
        elif event.type == pygame.MOUSEMOTION:
            self._handle_hover(event.pos)
    
    def _handle_hover(self, mouse_pos):
        shop_idx = self._get_shop_slot_at(mouse_pos)
        board_coord = self._get_board_coord_at(mouse_pos)
        
        if shop_idx != -1:
            self._hover.start("shop", item=shop_idx)
        elif board_coord:
            self._hover.start("board", item=board_coord)
        else:
            self._hover.reset()
            self._info_box.hide()
    
    def update(self, dt_ms):
        # Update hover timer
        self._hover.update(dt_ms)
        
        # Show info box when hover is active
        if self._hover.is_active():
            panel = self._hover.get_panel()
            item = self._hover.get_item()
            card_data = self._get_card_data(panel, item)
            self._info_box.show(card_data)
    
    def on_exit(self):
        self._audio.stop_all()
        self._audio.clear_cache()
```

---

## Testing Examples

### Unit Test: AudioSystem

```python
import pytest
from v2.ui import AudioSystem
from v2.constants import Paths
from v2.assets.loader import AssetLoader

def test_audio_preload():
    AssetLoader.initialize("v2/assets")
    audio = AudioSystem()
    
    audio.preload(Paths.SFX_BUY)
    assert audio.cached_count == 1
    
    # Duplicate preload should not increase count
    audio.preload(Paths.SFX_BUY)
    assert audio.cached_count == 1

def test_audio_play():
    AssetLoader.initialize("v2/assets")
    audio = AudioSystem()
    
    # Play uncached sound (should auto-load)
    audio.play(Paths.SFX_BUY)
    assert audio.cached_count == 1
    
    # Play with volume
    audio.play(Paths.SFX_BUY, volume=0.5)

def test_audio_clear():
    AssetLoader.initialize("v2/assets")
    audio = AudioSystem()
    
    audio.preload(Paths.SFX_BUY)
    audio.preload(Paths.SFX_PLACE)
    assert audio.cached_count == 2
    
    audio.clear_cache()
    assert audio.cached_count == 0
```

### Unit Test: HoverControl

```python
import pytest
from v2.ui import HoverControl

def test_hover_initial_state():
    hover = HoverControl()
    assert not hover.is_active()
    assert hover.get_panel() is None

def test_hover_activation():
    hover = HoverControl(delay_ms=100)
    
    hover.start("shop", item=2)
    assert not hover.is_active()
    
    hover.update(50)
    assert not hover.is_active()
    
    hover.update(60)
    assert hover.is_active()
    assert hover.get_panel() == "shop"
    assert hover.get_item() == 2

def test_hover_reset():
    hover = HoverControl(delay_ms=100)
    
    hover.start("shop", item=2)
    hover.update(200)
    assert hover.is_active()
    
    hover.reset()
    assert not hover.is_active()
    assert hover.get_panel() is None

def test_hover_same_item():
    hover = HoverControl(delay_ms=100)
    
    hover.start("shop", item=2)
    hover.update(200)
    assert hover.is_active()
    
    # Same item should preserve state
    hover.start("shop", item=2)
    assert hover.is_active()

def test_hover_different_item():
    hover = HoverControl(delay_ms=100)
    
    hover.start("shop", item=2)
    hover.update(200)
    assert hover.is_active()
    
    # Different item should reset
    hover.start("shop", item=3)
    assert not hover.is_active()
```

### Integration Test

```python
import pytest
from v2.ui import AudioSystem, HoverControl
from v2.constants import Paths
from v2.assets.loader import AssetLoader

def test_hover_with_audio():
    AssetLoader.initialize("v2/assets")
    audio = AudioSystem()
    hover = HoverControl(delay_ms=100)
    
    # Simulate hover workflow
    hover.start("shop", item=0)
    hover.update(50)
    
    # Not active yet, no sound
    assert not hover.is_active()
    
    hover.update(60)
    
    # Active, play sound
    if hover.is_active():
        audio.play(Paths.SFX_BUY, volume=0.3)
        assert audio.cached_count == 1
    
    # Reset
    hover.reset()
    audio.stop_all()
```

---

## Migration Guide

### From Old Pattern to New Pattern

#### Audio Migration

**Before:**
```python
def _play_sfx(self, sfx_name: str) -> None:
    try:
        if self._audio_loader is None:
            self._audio_loader = AssetLoader.get()
        self._audio_loader.get_sfx(sfx_name).play()
    except AutochessException:
        pass

# Usage
self._play_sfx(Paths.SFX_BUY)
```

**After:**
```python
# In __init__
self._audio = AudioSystem()

# In on_enter
self._audio.preload(Paths.SFX_BUY)

# Usage
self._audio.play(Paths.SFX_BUY)
```

#### Hover Migration

**Before:**
```python
# In __init__
self._hover = {
    "panel": None,
    "slot_idx": -1,
    "coord": None,
    "elapsed_ms": 0.0,
    "active": False
}

# Start hover
self._hover.update({
    "panel": "shop",
    "slot_idx": idx,
    "coord": None,
    "elapsed_ms": 0.0,
    "active": False
})

# Update
if self._hover["panel"] is not None and not self._hover["active"]:
    self._hover["elapsed_ms"] += dt_ms
    if self._hover["elapsed_ms"] >= self._HOVER_DELAY_MS:
        self._hover["active"] = True

# Check
if self._hover["active"] and self._hover["panel"] is not None:
    source = self._hover["panel"]
    key = self._hover.get("coord") if source == "board" else self._hover["slot_idx"]
```

**After:**
```python
# In __init__
self._hover = HoverControl(delay_ms=150)

# Start hover
self._hover.start("shop", item=idx)

# Update
self._hover.update(dt_ms)

# Check
if self._hover.is_active():
    source = self._hover.get_panel()
    key = self._hover.get_item()
```

---

## Best Practices

### AudioSystem

1. **Preload in on_enter():** Avoid loading during gameplay
2. **Use volume parameter:** Don't modify global volume
3. **Clean up in on_exit():** Call stop_all() and clear_cache()
4. **Handle missing files gracefully:** AudioSystem does this automatically

### HoverControl

1. **Update every frame:** Call update(dt_ms) in scene.update()
2. **Reset on no target:** Call reset() when mouse leaves all targets
3. **Use appropriate delays:** 100-200ms is typical
4. **Preserve same-item state:** start() handles this automatically

### General

1. **Type hints:** Use them for better IDE support
2. **Test in isolation:** Unit test components separately
3. **Document usage:** Add docstrings to custom methods
4. **Profile performance:** Use cProfile if needed

---

## Common Pitfalls

### AudioSystem

❌ **Don't:** Load sounds in tight loops
```python
for i in range(100):
    audio.play("sound.wav")  # Loads 100 times!
```

✅ **Do:** Preload once
```python
audio.preload("sound.wav")
for i in range(100):
    audio.play("sound.wav")  # Uses cache
```

### HoverControl

❌ **Don't:** Forget to update
```python
hover.start("shop", item=0)
# Missing: hover.update(dt_ms)
if hover.is_active():  # Never true!
    ...
```

✅ **Do:** Update every frame
```python
hover.start("shop", item=0)
hover.update(dt_ms)
if hover.is_active():
    ...
```

❌ **Don't:** Check state before activation
```python
hover.start("shop", item=0)
if hover.get_panel() == "shop":  # True immediately
    show_info()  # Shows before delay!
```

✅ **Do:** Check is_active() first
```python
hover.start("shop", item=0)
if hover.is_active():  # False until delay passes
    show_info()
```

---

## Performance Tips

1. **Preload all sounds:** Avoid runtime loading
2. **Reuse instances:** Don't create new AudioSystem/HoverControl every frame
3. **Clear cache on scene exit:** Free memory when not needed
4. **Use appropriate delays:** Longer delays = less frequent updates

---

**Documentation Status:** ✅ Complete  
**Last Updated:** 2026-04-28
