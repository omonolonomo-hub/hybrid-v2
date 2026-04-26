# Combat-Shop Critical Fixes Bugfix Design

## Overview

This bugfix addresses three critical runtime errors that crash the game during normal gameplay. The errors are caused by incorrect attribute names and API method calls that don't match the actual implementations in the codebase. All fixes are straightforward corrections:

1. **combat_scene_alternative.py line 1904**: Change `hex_card.card` to `hex_card.card_data` to match the HexCard dataclass definition
2. **shop_scene.py line 546**: Replace non-existent `market.refresh_window()` with correct Market API: `market._return_window(player.pid)` followed by `market.deal_market_window(player, n=5)`
3. **Verification**: Confirm that asset_loader.py constants are correctly imported (already working)

These are simple attribute/method name corrections with no algorithmic changes required.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - when code attempts to access non-existent attributes or methods
- **Property (P)**: The desired behavior - code should access the correct attributes/methods that actually exist in the implementation
- **Preservation**: All other card rendering, market operations, and asset loading functionality must remain unchanged
- **HexCard**: Dataclass in combat_scene.py and combat_scene_alternative.py that stores card rendering information with attribute `card_data` (not `card`)
- **Market**: Class in engine_core/market.py that manages card pool with methods `_return_window(pid)` and `deal_market_window(player, n)` (not `refresh_window()`)
- **AssetLoader**: Class in scenes/asset_loader.py that provides SHOP_CARD_SIZE and CARD_SIZE constants

## Bug Details

### Bug Condition

The bugs manifest when specific user interactions trigger code paths that attempt to access non-existent attributes or call non-existent methods. The system crashes with AttributeError exceptions.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type UserInteraction
  OUTPUT: boolean
  
  RETURN (input.action == "hover_card" AND input.file == "combat_scene_alternative.py")
         OR (input.action == "click_refresh" AND input.file == "shop_scene.py")
         OR (input.action == "import_constants" AND input.file == "main.py")
END FUNCTION
```

### Examples

- **Bug 1**: User hovers over a placed card in combat_scene_alternative.py → System crashes with `AttributeError: 'HexCard' object has no attribute 'card'` at line 1904
- **Bug 2**: User clicks the refresh button in shop_scene.py → System crashes with `AttributeError: 'Market' object has no attribute 'refresh_window'` at line 546
- **Bug 3**: main.py imports SHOP_CARD_SIZE and CARD_SIZE from scenes/asset_loader.py → System successfully imports (no bug, verification only)
- **Edge case**: Multiple rapid hovers in combat scene → Each hover triggers the same AttributeError

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- All other HexCard attribute accesses (card_data, front_image, back_image, position, hex_size, rotation, etc.) must continue to work
- All other Market methods (deal_market_window, _return_window, return_unsold, get_cards_for_player) must continue to work
- All other AssetLoader functionality (loading card images, preloading assets) must continue to work
- Card rendering in combat_scene.py (which already uses correct card_data) must continue to work
- All card property accesses through card_data (rotated_edges(), dominant_group(), passive_type, total_power()) must continue to work

**Scope:**
All code paths that do NOT involve the three specific bug locations should be completely unaffected by this fix. This includes:
- Other combat scene rendering code
- Other shop scene functionality (buying cards, displaying hand, etc.)
- Other market operations (dealing windows, returning cards)
- All asset loading operations

## Hypothesized Root Cause

Based on the bug description and code analysis, the root causes are:

1. **Incorrect Attribute Name in combat_scene_alternative.py**: The code uses `hex_card.card` but the HexCard dataclass defines the attribute as `card_data`
   - Line 1904 in combat_scene_alternative.py: `hovered_card = hex_card.card`
   - Should be: `hovered_card = hex_card.card_data`
   - Note: combat_scene.py already has the correct code at line 2010

2. **Non-existent Method Call in shop_scene.py**: The code calls `market.refresh_window()` but the Market class does not have this method
   - Line 546 in shop_scene.py: `self.core_game_state.game.market.refresh_window()`
   - The Market class provides: `_return_window(pid)` and `deal_market_window(player, n=5)`
   - Should be: `market._return_window(player.pid)` followed by `market.deal_market_window(player, n=5)`

3. **AssetLoader Constants**: No bug exists - imports are working correctly
   - main.py successfully imports SHOP_CARD_SIZE and CARD_SIZE from scenes/asset_loader.py
   - This is verification only, no fix needed

## Correctness Properties

Property 1: Bug Condition - Attribute and Method Name Corrections

_For any_ code execution where the bug condition holds (user hovers over card in combat_scene_alternative.py OR user clicks refresh in shop_scene.py), the fixed code SHALL access the correct attribute names (`hex_card.card_data`) and call the correct Market API methods (`_return_window` and `deal_market_window`) instead of crashing with AttributeError.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - Existing Functionality Unchanged

_For any_ code execution where the bug condition does NOT hold (all other combat scene rendering, shop operations, market operations, and asset loading), the fixed code SHALL produce exactly the same behavior as the original code, preserving all existing functionality for non-buggy code paths.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## Fix Implementation

### Changes Required

The fixes are straightforward attribute name and method call corrections:

**File**: `scenes/combat_scene_alternative.py`

**Function**: `_draw_priority_popup` (around line 1904)

**Specific Changes**:
1. **Attribute Name Correction**: Change `hex_card.card` to `hex_card.card_data`
   - Line 1904: `hovered_card = hex_card.card`
   - Change to: `hovered_card = hex_card.card_data`
   - This matches the HexCard dataclass definition which uses `card_data` attribute

**File**: `scenes/shop_scene.py`

**Function**: `_request_refresh` (around line 546)

**Specific Changes**:
2. **Market API Correction**: Replace `market.refresh_window()` with correct Market API calls
   - Line 546: `self.core_game_state.game.market.refresh_window()`
   - Change to:
     ```python
     market = self.core_game_state.game.market
     market._return_window(player.pid)
     market.deal_market_window(player, n=5)
     ```
   - This uses the actual Market class methods that exist in engine_core/market.py

**File**: `main.py` and `scenes/asset_loader.py`

**Verification Only**:
3. **AssetLoader Constants**: No changes needed
   - Imports of SHOP_CARD_SIZE and CARD_SIZE are already working correctly
   - This is verification only to ensure no regression

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bugs on unfixed code, then verify the fixes work correctly and preserve existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bugs BEFORE implementing the fix. Confirm the root cause analysis by observing the exact AttributeError exceptions.

**Test Plan**: Write tests that trigger the bug conditions (hover over card, click refresh button) on the UNFIXED code to observe the AttributeError failures and confirm the exact error messages match the bug description.

**Test Cases**:
1. **Combat Scene Hover Test**: Simulate hovering over a placed card in combat_scene_alternative.py (will fail on unfixed code with `AttributeError: 'HexCard' object has no attribute 'card'`)
2. **Shop Refresh Test**: Simulate clicking the refresh button in shop_scene.py (will fail on unfixed code with `AttributeError: 'Market' object has no attribute 'refresh_window'`)
3. **AssetLoader Import Test**: Verify that SHOP_CARD_SIZE and CARD_SIZE can be imported from scenes/asset_loader.py (should pass on unfixed code - verification only)
4. **Combat Scene (Correct) Test**: Verify that combat_scene.py (not alternative) correctly handles hover (should pass on unfixed code - it already uses card_data)

**Expected Counterexamples**:
- AttributeError when accessing `hex_card.card` in combat_scene_alternative.py
- AttributeError when calling `market.refresh_window()` in shop_scene.py
- Possible causes: typo in attribute name, incorrect API method name, missing method implementation

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed code produces the expected behavior (no crashes, correct attribute/method access).

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := execute_fixed_code(input)
  ASSERT no_attribute_error(result)
  ASSERT correct_behavior(result)
END FOR
```

**Test Cases**:
1. **Fixed Combat Scene Hover**: Hover over card in combat_scene_alternative.py should access card_data successfully
2. **Fixed Shop Refresh**: Click refresh button should call _return_window and deal_market_window successfully
3. **Multiple Rapid Hovers**: Rapidly hover over multiple cards to ensure no race conditions or edge cases

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed code produces the same result as the original code.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT original_code(input) = fixed_code(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all non-buggy code paths

**Test Plan**: Observe behavior on UNFIXED code first for non-buggy interactions (other combat rendering, other shop operations), then write property-based tests capturing that behavior.

**Test Cases**:
1. **Other HexCard Attributes**: Verify that accessing other HexCard attributes (front_image, back_image, position, hex_size, rotation) continues to work
2. **Other Market Methods**: Verify that calling other Market methods (return_unsold, get_cards_for_player) continues to work
3. **Combat Scene (Correct File)**: Verify that combat_scene.py (not alternative) continues to work with card_data
4. **Shop Buy Operations**: Verify that buying cards in shop_scene.py continues to work
5. **Card Property Access**: Verify that accessing card properties through card_data (rotated_edges(), dominant_group(), passive_type, total_power()) continues to work

### Unit Tests

- Test HexCard attribute access for all attributes (card_data, front_image, back_image, position, hex_size, rotation)
- Test Market API methods (_return_window, deal_market_window, return_unsold, get_cards_for_player)
- Test AssetLoader constant imports (SHOP_CARD_SIZE, CARD_SIZE)
- Test edge cases (null checks, empty market windows, missing cards)

### Property-Based Tests

- Generate random card hover sequences and verify no AttributeError occurs
- Generate random market refresh sequences and verify correct API calls
- Generate random card placements and verify card_data access works
- Test that all non-buggy code paths produce identical results before and after fix

### Integration Tests

- Test full combat scene flow with card hover in both combat_scene.py and combat_scene_alternative.py
- Test full shop scene flow with market refresh and card purchases
- Test switching between combat and shop scenes
- Test that visual feedback (tooltips, card flips) occurs correctly after fixes
