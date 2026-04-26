# Coupling Breach Refactor - COMPLETED

## Problem (DEBT ACCRUAL - Bulgu 5)

`shop.py` was directly accessing private attributes (`_card_names`, `_flips`) from `HandPanel` and `ShopPanel` in four locations:

1. **`_handle_mouse_down()`** - Line 354: `self.hand_panel._card_names[idx]`
2. **`draw()` drag rendering** - Line 569: `self.hand_panel._card_names[src_idx]` and `self.shop_panel._card_names[src_idx]`
3. **`draw()` flip access** - Line 612: `self.hand_panel._flips[idx]`
4. **`_render_copy_labels()`** - Lines 685, 706: `self.shop_panel._card_names` and `self.hand_panel._card_names`

This created fragile coupling that would break at runtime (not compile-time) if the internal storage strategy changed (e.g., switching from `_card_names` to `_slots: list[SlotState]`).

## Solution

Added public getter methods to both `HandPanel` and `ShopPanel` to encapsulate internal state:

### HandPanel Public API (v2/ui/hand_panel.py)
```python
def get_card_name(self, slot_idx: int) -> str | None:
    """Public getter for card name at slot index."""
    
def get_flip(self, slot_idx: int):
    """Public getter for CardFlip at slot index."""
    
def get_card_names(self) -> list[str | None]:
    """Public getter for all card names."""
```

### ShopPanel Public API (v2/ui/shop_panel.py)
```python
def get_card_name(self, slot_idx: int) -> str | None:
    """Public getter for card name at slot index."""
    
def get_card_names(self) -> list[str | None]:
    """Public getter for all card names."""
```

## Changes Made

### 1. v2/ui/hand_panel.py
- Added 3 public getter methods after `_is_evolved_card()`
- No breaking changes to existing functionality

### 2. v2/ui/shop_panel.py
- Added 2 public getter methods after `_is_evolved_card()`
- No breaking changes to existing functionality

### 3. v2/scenes/shop.py
- **Line 354**: `_card_names[idx]` → `get_card_name(idx)`
- **Line 569**: `_card_names[src_idx]` → `get_card_name(src_idx)` (both panels)
- **Line 612**: `_flips[idx]` → `get_flip(idx)` with null check
- **Line 685, 706**: `_card_names` → `get_card_names()` (both panels)

### 4. tests/test_shop_scene_master_integration.py
- Updated `_first_filled_hand_slot()` helper to use `get_card_names()`
- Updated assertions to use `get_card_names()` instead of `_card_names`
- Updated drag test to use `get_card_name(slot_idx)`

### 5. tests/test_ghost_and_drag_edge.py
- Updated flip access to use `get_flip(0)` instead of `_flips[0]`

## Verification

✅ All files compile without syntax errors
✅ No remaining private attribute access from external files
✅ Tests updated to use public API
✅ Encapsulation properly enforced

## Benefits

1. **Maintainability**: Internal storage can now be refactored without breaking external code
2. **Type Safety**: Public API provides clear contract
3. **Testability**: Tests use public interface, making them more robust
4. **Future-Proof**: Easy to add validation, caching, or logging in getters

## Time Spent

~30 minutes (as estimated)

## Status

✅ **DEBT CLEARED** - Coupling breach eliminated
