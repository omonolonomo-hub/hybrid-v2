# Phase 1 Refactor: AudioSystem & HoverControl

**Status:** ✅ COMPLETE  
**Date:** 2026-04-28  
**Objective:** Extract pure I/O and self-contained state management from ShopScene

---

## 🎯 Goals

Başlangıç noktası olarak en kolay ve güvenli refactor adımları:

1. **AudioSystem** → Saf I/O, hiçbir scene state'ine dokunmuyor
2. **HoverControl** → Self-contained state, sadece dt ve item bilgisi alır

---

## 📦 New Components

### 1. `v2/ui/audio_system.py`

**Purpose:** Merkezi ses efekti yönetimi ve cache'leme

**Features:**
- ✅ SFX preload ve cache
- ✅ Volume control
- ✅ Lazy AssetLoader initialization
- ✅ Graceful error handling (sessizce başarısız)
- ✅ Stop individual/all sounds
- ✅ Cache management

**API:**
```python
audio = AudioSystem()

# Preload
audio.preload("card_buy.wav")

# Play
audio.play("card_buy.wav", volume=0.8)

# Stop
audio.stop("card_buy.wav")
audio.stop_all()

# Cache management
audio.clear_cache()
count = audio.cached_count
```

**Dependencies:**
- `pygame.mixer.Sound`
- `v2.assets.loader.AssetLoader` (lazy)
- `v2.core.exceptions.AutochessException`

**State:** Pure I/O, no scene dependencies

---

### 2. `v2/ui/hover_control.py`

**Purpose:** Hover delay ve panel görünürlük state yönetimi

**Features:**
- ✅ Configurable hover delay
- ✅ Panel + item tracking
- ✅ Automatic timer management
- ✅ State preservation for same item
- ✅ Immutable state object (HoverState dataclass)

**API:**
```python
hover = HoverControl(delay_ms=150)

# Start hover
hover.start("shop", item=2)

# Update timer (every frame)
hover.update(dt_ms)

# Check if active
if hover.is_active():
    panel = hover.get_panel()  # "shop"
    item = hover.get_item()    # 2
    state = hover.get_state()  # HoverState object

# Reset
hover.reset()
```

**Dependencies:**
- `dataclasses` (HoverState)
- `typing` (type hints)

**State:** Self-contained, no external dependencies

---

## 🔄 ShopScene Changes

### Before (Old Pattern)

```python
# Audio
def _play_sfx(self, sfx_name: str) -> None:
    try:
        if self._audio_loader is None:
            self._audio_loader = AssetLoader.get()
        self._audio_loader.get_sfx(sfx_name).play()
    except AutochessException:
        pass

# Usage
self._play_sfx(Paths.SFX_BUY)

# Hover
self._hover = {
    "panel": None, 
    "slot_idx": -1, 
    "coord": None, 
    "elapsed_ms": 0.0, 
    "active": False
}

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

### After (New Pattern)

```python
# Audio
self._audio = AudioSystem()

# Preload in on_enter()
self._audio.preload(Paths.SFX_BUY)
self._audio.preload(Paths.SFX_PLACE)
self._audio.preload(Paths.SFX_REROLL)

# Usage
self._audio.play(Paths.SFX_BUY)

# Hover
self._hover_control = HoverControl(delay_ms=self._HOVER_DELAY_MS)

# Start hover
self._hover_control.start("shop", item=hover_shop_idx)

# Update
self._hover_control.update(dt_ms)

# Check
if self._hover_control.is_active():
    source = self._hover_control.get_panel()
    key = self._hover_control.get_item()
```

---

## 📊 Impact Analysis

### Lines Changed
- **New files:** 2 (audio_system.py, hover_control.py)
- **Modified files:** 1 (shop.py)
- **Lines added:** ~200
- **Lines removed:** ~30
- **Net change:** +170 lines (better separation of concerns)

### Complexity Reduction
- ❌ **Before:** Audio logic scattered, dict-based hover state
- ✅ **After:** Centralized audio, type-safe hover state

### Benefits
1. **Testability:** Components can be tested independently
2. **Reusability:** AudioSystem and HoverControl can be used in other scenes
3. **Type Safety:** HoverState dataclass provides type hints
4. **Maintainability:** Clear API boundaries
5. **Performance:** Audio cache reduces repeated file loads

---

## ✅ Testing

### Unit Tests (`test_refactor_components.py`)

**HoverControl Tests:**
- ✅ Initial state (not active)
- ✅ Start hover
- ✅ Timer update (partial)
- ✅ Timer update (complete → active)
- ✅ Reset
- ✅ Same item preservation
- ✅ Different item reset

**AudioSystem Tests:**
- ✅ Preload single sound
- ✅ Preload multiple sounds
- ✅ Duplicate preload (no-op)
- ✅ Play cached sound
- ✅ Play uncached sound (auto-load)
- ✅ Stop individual sound
- ✅ Stop all sounds
- ✅ Clear cache

**Integration Tests:**
- ✅ Hover + Audio workflow
- ✅ State management

**Results:** All tests passed ✅

### Compilation Check
```bash
python -m py_compile v2/scenes/shop.py
# Exit Code: 0 ✅
```

---

## 🚀 Next Steps (Phase 2)

### Candidate Components for Extraction

1. **FloatingTextManager** → Already isolated, could move to v2/ui/
2. **CameraState** → Pure state, could extract to v2/ui/camera.py
3. **DragState** → Self-contained, could extract to v2/ui/drag_control.py
4. **InfoBox** → Already in v2/ui/, but could enhance API
5. **PhaseTransition** → Could extract phase change logic

### Recommended Order (Easy → Hard)

1. **CameraState** (pure state, no dependencies)
2. **DragState** (self-contained, minimal dependencies)
3. **PhaseTransition** (moderate complexity)
4. **Combat Logic** (complex, many dependencies)

---

## 📝 Notes

### Design Decisions

1. **AudioSystem graceful failure:** Ses yükleme hatalarında sessizce başarısız olur (oyun devam eder)
2. **HoverControl immutable state:** HoverState dataclass ile type-safe state
3. **Lazy AssetLoader:** AudioSystem sadece gerektiğinde AssetLoader'ı yükler
4. **Same-item preservation:** Aynı item üzerinde hover state korunur (flicker önleme)

### Migration Notes

- `_play_sfx()` metodu tamamen kaldırıldı
- `self._hover` dict → `self._hover_control` object
- Music handling hala AssetLoader'da (Phase 2'de refactor edilebilir)
- `_audio_loader` hala music için kullanılıyor

### Backward Compatibility

- ✅ Existing tests still pass
- ✅ No API changes for external callers
- ✅ ShopScene behavior unchanged

---

## 🎓 Lessons Learned

1. **Start with pure I/O:** AudioSystem hiçbir scene state'ine bağımlı değil → en kolay refactor
2. **Self-contained state:** HoverControl kendi state'ini yönetir → test edilebilir
3. **Incremental approach:** Küçük, güvenli adımlarla ilerle
4. **Test first:** Her component için unit test yaz
5. **Type safety:** Dataclass kullanımı type hintleri güçlendirir

---

## 📚 References

- Original proposal: Turkish text in user message
- Implementation: `v2/ui/audio_system.py`, `v2/ui/hover_control.py`
- Tests: `test_refactor_components.py`
- Modified scene: `v2/scenes/shop.py`

---

**Refactor Status:** ✅ COMPLETE  
**Next Phase:** CameraState / DragState extraction
