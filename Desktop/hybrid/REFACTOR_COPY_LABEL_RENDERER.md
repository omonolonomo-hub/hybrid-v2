# Copy Label Renderer Refactoring

## Summary

Successfully extracted copy label rendering logic from `ShopScene` into a dedicated `CopyLabelRenderer` class, reducing coupling and improving code organization.

## Changes Made

### 1. Created `v2/ui/copy_label_renderer.py`

A new dedicated renderer class with the following features:

- **Encapsulated rendering logic**: All copy label rendering is now in one place
- **Cache management**: Internal `_cache` dictionary for rendered text surfaces
- **Simple API**: 
  - `render()` - Renders labels for a list of card slots
  - `invalidate()` - Clears the cache when card data changes
- **No coupling**: Doesn't depend on `ShopScene`, `ShopPanel`, or `HandPanel` internals
- **Flexible**: Works with any list of rects, names, and copy counts

### 2. Refactored `v2/scenes/shop.py`

**Removed:**
- `_copy_label_cache` instance variable (~30 lines)
- `_render_copy_labels()` method (~45 lines of duplicated logic)
- Manual cache management in `on_exit()` and `sync_view()`

**Added:**
- Import of `CopyLabelRenderer`
- `_copy_renderer` instance variable
- Single delegated call in `draw()` method

**Before:**
```python
def _render_copy_labels(self, surface: pygame.Surface) -> None:
    font = font_cache.mono(9)
    copies_by_name = self._current_public_state().active_player.copies_by_name
    
    # Render shop copy labels
    for slot_rect, name in zip(self.shop_panel.card_rects, self.shop_panel.get_card_names()):
        if name:
            count = copies_by_name.get(name, 0)
            cache_key = (name, count)
            if cache_key not in self._copy_label_cache:
                text = f"Copies: {count}/3"
                color = Colors.GOLD_TEXT if count >= 3 else (200, 205, 230)
                self._copy_label_cache[cache_key] = font.render(text, True, color)
            text_surf = self._copy_label_cache[cache_key]
            # ... blit logic
    
    # Render hand copy labels (duplicate logic)
    for slot_rect, name in zip(self.hand_panel.card_rects, self.hand_panel.get_card_names()):
        # ... same logic repeated
```

**After:**
```python
# In draw() method:
copies_by_name = self._current_public_state().active_player.copies_by_name
self._copy_renderer.render(
    surface,
    self.shop_panel.card_rects + self.hand_panel.card_rects,
    self.shop_panel.get_card_names() + self.hand_panel.get_card_names(),
    copies_by_name
)
```

### 3. Created `tests/test_copy_label_renderer.py`

Comprehensive test suite with 8 tests covering:
- Initialization and cache management
- Rendering with empty/filled/mixed slots
- Cache reuse and invalidation
- Handling missing copy counts
- Multiple cards with same/different counts

**All tests pass ✓**

## Benefits

1. **Reduced coupling**: `ShopScene` no longer needs to know about rendering details
2. **Single responsibility**: Copy label rendering is now isolated in one class
3. **Eliminated duplication**: Shop and hand labels use the same code path
4. **Easier testing**: Renderer can be tested independently
5. **Better maintainability**: Changes to label rendering only affect one file
6. **Cleaner code**: ~75 lines removed from `ShopScene`, replaced with ~5 lines

## Verification

- ✅ All new tests pass (8/8)
- ✅ Existing integration tests pass (5/5)
- ✅ No syntax errors
- ✅ Successful import and instantiation
- ✅ No breaking changes to public API

## Architecture

```
ShopScene
    ├── ShopPanel (provides card_rects, card_names)
    ├── HandPanel (provides card_rects, card_names)
    └── CopyLabelRenderer (renders labels for both)
            ↓
        Receives: rects, names, copies_by_name
        Renders: "Copies: N/3" labels with caching
```

The renderer is now a pure rendering component that doesn't need to know about the scene structure or panel internals.

## Future Improvements

Potential enhancements (not implemented):
- Configurable font size/style
- Configurable label position offset
- Animation support for count changes
- Different label formats (e.g., "2/3" instead of "Copies: 2/3")
