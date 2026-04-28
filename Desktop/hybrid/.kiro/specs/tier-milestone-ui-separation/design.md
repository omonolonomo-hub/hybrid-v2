# Tier Milestone UI Separation Bugfix Design

## Overview

The current implementation violates separation of concerns by placing milestone checking logic (`_check_tier_milestones()`) in the UI layer (ShopScene). This method is called every frame during `update()`, which is inefficient and architecturally incorrect. The fix will move milestone detection to the ShopController's command flow and use the SignalBus event system to notify the UI layer, aligning with the existing signal-based architecture used for `board_mutated`, `economy_changed`, and other game events.

The fix involves:
1. Adding a `milestone_reached` signal to SignalBus
2. Moving milestone detection logic from ShopScene to ShopController
3. Emitting signals when milestones are reached during controller actions
4. Converting ShopScene's `_check_tier_milestones()` into a signal handler

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - when milestone checking logic executes in the UI layer during every frame update
- **Property (P)**: The desired behavior - milestone checking occurs in the controller layer and emits signals that the UI layer responds to
- **Preservation**: Existing milestone display behavior (floating text, colors, positioning, deduplication) that must remain unchanged by the fix
- **ShopController**: The controller in `v2/core/shop_controller.py` that handles game actions (buy, place, reroll) following the Command pattern
- **SignalBus**: The event bus in `engine_core/signals.py` that decouples state mutation (engine) from state observation (UI/Cache)
- **_check_tier_milestones()**: The method in `v2/scenes/shop.py` that currently performs milestone checking in the UI layer
- **Tier Milestone**: When a player reaches 2, 3, 4, 5, or 6 cards of the same synergy group (MIND, CONNECTION, EXISTENCE)
- **Copy Milestone**: When a player reaches 2 or 3 copies of the same card on the board at specific turns

## Bug Details

### Bug Condition

The bug manifests when the ShopScene `update()` method executes every frame. The `_check_tier_milestones()` method is called in the UI layer, performing game logic checks (comparing current synergy counts to previous counts, checking copy milestones) that should occur in the controller layer.

**Formal Specification:**
```
FUNCTION isBugCondition(execution_context)
  INPUT: execution_context of type ExecutionContext
  OUTPUT: boolean
  
  RETURN execution_context.method == "_check_tier_milestones"
         AND execution_context.layer == "UI"
         AND execution_context.caller == "ShopScene.update()"
         AND execution_context.frequency == "every_frame"
END FUNCTION
```

### Examples

- **Example 1**: Player buys a third MIND card → `_check_tier_milestones()` detects the milestone during the next frame update (not immediately after the buy action) → floating text spawns
  - **Expected**: Milestone detection occurs in `ShopController.handle_shop_action()` immediately after the buy action completes
  
- **Example 2**: Player places a card from hand → `_check_tier_milestones()` detects tier milestone during the next frame update → floating text spawns
  - **Expected**: Milestone detection occurs in `ShopController.place_card_from_hand()` immediately after placement

- **Example 3**: Player reaches a 2-copy milestone → `_check_tier_milestones()` detects it during frame update → floating text spawns
  - **Expected**: Milestone detection occurs in the controller action that triggered the milestone

- **Edge Case**: Player performs multiple actions in rapid succession (buy + place) → milestones are detected on the next frame update, potentially missing intermediate states
  - **Expected**: Each action checks for milestones independently and emits signals immediately

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Tier milestone floating text must continue to display with format: `"{TIER_SHORT} +{bonus}pts UP"` (e.g., "MIND +3pts UP")
- Copy milestone floating text must continue to display "2-COPY POWER UP" or "3-COPY POWER UP"
- Floating text positioning must remain at board center with camera offset adjustments
- Tier milestone colors must remain: MIND (Colors.MIND), CONNECTION (Colors.CONNECTION), EXISTENCE (Colors.EXISTENCE)
- Copy milestone color must remain Colors.PLATINUM
- Font sizes must remain: tier milestones (13), copy milestones (15)
- Milestone deduplication must continue to work (no duplicate floating text for the same milestone)
- All existing SignalBus signals (`board_mutated`, `economy_changed`, `inventory_changed`, `turn_started`, `combat_finished`) must continue to function

**Scope:**
All UI rendering, camera positioning, floating text management, and other game logic that does NOT involve milestone detection should be completely unaffected by this fix. This includes:
- Board rendering and hex grid display
- Shop panel, hand panel, and other UI components
- Camera controls and zoom
- Drag-and-drop functionality
- Combat overlays and phase transitions

## Hypothesized Root Cause

Based on the bug description and code analysis, the root causes are:

1. **Architectural Misplacement**: The `_check_tier_milestones()` method was placed in ShopScene (UI layer) instead of ShopController (controller layer), violating the separation of concerns principle established by the SignalBus architecture.

2. **Polling Instead of Event-Driven**: The method is called every frame in `update()` rather than being triggered by specific game actions (buy, place, reroll), resulting in inefficient polling and potential timing issues.

3. **Missing Signal Integration**: The milestone system was not integrated with the SignalBus event system, unlike other game events (`board_mutated`, `economy_changed`, etc.), creating architectural inconsistency.

4. **State Tracking Location**: The milestone tracking state (`_prev_group_counts`, `_seen_copy_milestones`) is stored in the UI layer, making it difficult to test and maintain independently of the UI.

## Correctness Properties

Property 1: Bug Condition - Milestone Detection in Controller Layer

_For any_ controller action (buy, place, reroll) that results in a milestone condition being met (tier threshold reached or copy milestone achieved), the fixed system SHALL detect the milestone in the ShopController layer and emit a `milestone_reached` signal through the SignalBus, rather than detecting it in the UI layer during frame updates.

**Validates: Requirements 2.1, 2.2**

Property 2: Preservation - Milestone Display Behavior

_For any_ milestone that is reached, the fixed system SHALL produce the same floating text display (text content, positioning, colors, font sizes) as the original system, preserving all visual feedback and deduplication logic.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File 1**: `engine_core/signals.py`

**Changes**:
1. **Add milestone_reached Signal**: Add `self.milestone_reached = Signal()` to the `SignalBus.__init__()` method
   - Follows the pattern of existing signals (`board_mutated`, `economy_changed`, etc.)
   - Signal will carry milestone data: type (tier/copy), group/card name, bonus points, etc.

**File 2**: `v2/core/shop_controller.py`

**Function**: `handle_shop_action()`, `place_card_from_hand()`

**Specific Changes**:
1. **Add Milestone Detection Method**: Create a new private method `_check_and_emit_milestones()` that:
   - Compares current synergy state to previous state (stored in controller or GameState)
   - Detects tier milestones (2, 3, 4, 5, 6 cards of same group)
   - Detects copy milestones (2-copy or 3-copy power-ups)
   - Emits `milestone_reached` signal with appropriate data

2. **Integrate with Action Methods**: Call `_check_and_emit_milestones()` after state-mutating actions:
   - In `handle_shop_action()` after "buy" action completes successfully
   - In `place_card_from_hand()` after card placement succeeds
   - Potentially in other methods that can trigger milestones (if any)

3. **State Tracking**: Add milestone tracking state to ShopController:
   - `_prev_group_counts: Dict[str, int]` - tracks previous synergy counts
   - `_seen_copy_milestones: Set[Tuple[str, str]]` - tracks seen copy milestones
   - Initialize in `__init__()` method
   - Update after each milestone check

4. **Signal Access**: Access the SignalBus through `self._game_state._adapter._engine.signals` (following the pattern used in GameState)

**File 3**: `v2/scenes/shop.py`

**Function**: `_check_tier_milestones()`, `on_enter()`, `on_exit()`, `update()`

**Specific Changes**:
1. **Convert to Signal Handler**: Rename `_check_tier_milestones()` to `_on_milestone_reached()` and convert it to a signal handler:
   - Accept `**kwargs` parameter containing milestone data from signal
   - Remove state comparison logic (now handled in controller)
   - Keep floating text spawning logic
   - Use signal data to determine text content, position, color

2. **Connect Signal in on_enter()**: Add signal connection in `on_enter()` method:
   - Connect `milestone_reached` signal to `_on_milestone_reached()` handler
   - Follow the pattern used for `board_mutated` signal connection

3. **Disconnect Signal in on_exit()**: Add signal disconnection in `on_exit()` method:
   - Disconnect `milestone_reached` signal from `_on_milestone_reached()` handler
   - Follow the pattern used for `board_mutated` signal disconnection

4. **Remove Frame-Based Call**: Remove `self._check_tier_milestones()` call from `update()` method

5. **Remove State Tracking**: Remove `_prev_group_counts` and `_seen_copy_milestones` from ShopScene initialization (now in controller)

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code (milestone checking in UI layer), then verify the fix works correctly (milestone checking in controller layer) and preserves existing behavior (floating text display).

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm that milestone checking occurs in the UI layer during frame updates rather than in the controller layer during actions.

**Test Plan**: Write tests that instrument the code to track where milestone checking occurs. Run these tests on the UNFIXED code to observe that `_check_tier_milestones()` is called from `ShopScene.update()` rather than from controller action methods.

**Test Cases**:
1. **Frame-Based Detection Test**: Verify that `_check_tier_milestones()` is called during `ShopScene.update()` on unfixed code (will pass on unfixed code, fail on fixed code)
2. **Controller Action Test**: Verify that milestone detection does NOT occur in `ShopController.handle_shop_action()` on unfixed code (will pass on unfixed code, fail on fixed code)
3. **Signal Emission Test**: Verify that `milestone_reached` signal is NOT emitted on unfixed code (will pass on unfixed code, fail on fixed code)
4. **Timing Test**: Verify that milestone detection occurs on the frame AFTER the action, not immediately (will pass on unfixed code, fail on fixed code)

**Expected Counterexamples**:
- Milestone checking occurs in UI layer (`ShopScene._check_tier_milestones()`)
- Milestone checking is called every frame in `update()` method
- No `milestone_reached` signal is emitted
- Milestone detection is delayed until the next frame update

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds (milestone checking in UI layer), the fixed function produces the expected behavior (milestone checking in controller layer with signal emission).

**Pseudocode:**
```
FOR ALL action WHERE action.can_trigger_milestone() DO
  # Execute action in controller
  result := controller.execute_action(action)
  
  # Verify milestone detection occurs in controller layer
  ASSERT milestone_checked_in_controller(action)
  
  # Verify signal is emitted if milestone reached
  IF action.reaches_milestone() THEN
    ASSERT signal_emitted("milestone_reached", milestone_data)
  END IF
  
  # Verify UI layer does NOT perform milestone checking
  ASSERT NOT milestone_checked_in_ui_layer()
END FOR
```

**Test Cases**:
1. **Buy Action Milestone**: Buy a card that triggers a tier milestone → verify milestone detected in `handle_shop_action()` → verify signal emitted
2. **Place Action Milestone**: Place a card that triggers a tier milestone → verify milestone detected in `place_card_from_hand()` → verify signal emitted
3. **Copy Milestone**: Trigger a 2-copy or 3-copy milestone → verify detected in controller → verify signal emitted
4. **No Milestone**: Perform action that doesn't trigger milestone → verify no signal emitted

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold (milestone display behavior), the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL milestone_event WHERE milestone_event.is_valid() DO
  # Capture original floating text behavior
  original_text := capture_floating_text(original_system, milestone_event)
  
  # Capture fixed floating text behavior
  fixed_text := capture_floating_text(fixed_system, milestone_event)
  
  # Verify identical display
  ASSERT original_text.content == fixed_text.content
  ASSERT original_text.position == fixed_text.position
  ASSERT original_text.color == fixed_text.color
  ASSERT original_text.font_size == fixed_text.font_size
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across different milestone scenarios
- It catches edge cases that manual unit tests might miss (e.g., different synergy groups, multiple milestones in sequence)
- It provides strong guarantees that display behavior is unchanged for all milestone types

**Test Plan**: Observe floating text behavior on UNFIXED code first for various milestone scenarios, then write property-based tests capturing that behavior and verify it continues after the fix.

**Test Cases**:
1. **Tier Milestone Display**: Verify tier milestone floating text (content, position, color, font size) is identical before and after fix
2. **Copy Milestone Display**: Verify copy milestone floating text is identical before and after fix
3. **Deduplication**: Verify duplicate milestone prevention continues to work (same milestone doesn't spawn multiple floating texts)
4. **Camera Offset**: Verify floating text positioning adjusts correctly with camera offset
5. **Multiple Milestones**: Verify multiple milestones in sequence display correctly
6. **Other Signals**: Verify `board_mutated`, `economy_changed`, and other signals continue to function

### Unit Tests

- Test `SignalBus.milestone_reached` signal can be connected, emitted, and disconnected
- Test `ShopController._check_and_emit_milestones()` detects tier milestones correctly
- Test `ShopController._check_and_emit_milestones()` detects copy milestones correctly
- Test `ShopController._check_and_emit_milestones()` does not emit signal when no milestone reached
- Test `ShopScene._on_milestone_reached()` spawns correct floating text for tier milestones
- Test `ShopScene._on_milestone_reached()` spawns correct floating text for copy milestones
- Test signal connection in `ShopScene.on_enter()` and disconnection in `on_exit()`

### Property-Based Tests

- Generate random sequences of buy/place actions and verify milestones are detected correctly
- Generate random synergy states and verify tier milestone detection logic
- Generate random copy counts and verify copy milestone detection logic
- Generate random milestone events and verify floating text display is preserved

### Integration Tests

- Test full game flow: buy cards → reach tier milestone → verify floating text appears
- Test full game flow: place cards → reach copy milestone → verify floating text appears
- Test multiple milestones in sequence (tier + copy) → verify both display correctly
- Test milestone deduplication across multiple actions
- Test that other SignalBus signals (`board_mutated`, etc.) continue to work alongside `milestone_reached`
