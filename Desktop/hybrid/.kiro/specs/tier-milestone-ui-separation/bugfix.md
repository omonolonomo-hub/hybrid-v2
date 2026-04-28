# Bugfix Requirements Document

## Introduction

The `_check_tier_milestones()` method in `v2/scenes/shop.py` violates separation of concerns by placing game logic (milestone checking) in the UI layer. This method is called every frame during `update()`, which is inefficient and architecturally incorrect. Milestone checking should occur in the ShopController's Command pattern flow and emit signals through the SignalBus system, allowing the UI to respond reactively rather than polling every frame.

This bug affects the maintainability, testability, and performance of the milestone system. The fix will align milestone handling with the existing signal-based architecture used for `board_mutated`, `economy_changed`, and other game events.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the ShopScene `update()` method executes THEN the system calls `_check_tier_milestones()` in the UI layer every frame

1.2 WHEN milestone conditions are met (tier thresholds or copy milestones) THEN the system performs game logic checks directly in the UI layer

1.3 WHEN milestone detection occurs THEN the system spawns floating text directly without going through the SignalBus event system

1.4 WHEN ShopController actions complete (buy, place, etc.) THEN the system does not check for or emit milestone events through the ActionResult flow

### Expected Behavior (Correct)

2.1 WHEN ShopController actions complete (buy, place, reroll, etc.) THEN the system SHALL check for milestone conditions in the controller layer

2.2 WHEN milestone conditions are met THEN the system SHALL emit a `milestone_reached` signal through the SignalBus with milestone type and data

2.3 WHEN the `milestone_reached` signal is emitted THEN the ShopScene SHALL listen to the signal and spawn floating text in response

2.4 WHEN the ShopScene `update()` method executes THEN the system SHALL NOT perform any game logic checks for milestones

### Unchanged Behavior (Regression Prevention)

3.1 WHEN tier milestones are reached (e.g., 3 cards of same tier) THEN the system SHALL CONTINUE TO display floating text with tier name and bonus points

3.2 WHEN copy milestones are reached (2-copy or 3-copy power-ups) THEN the system SHALL CONTINUE TO display "2-COPY POWER UP" or "3-COPY POWER UP" floating text

3.3 WHEN floating text is spawned for milestones THEN the system SHALL CONTINUE TO position it at the board center with appropriate colors and font sizes

3.4 WHEN the same milestone is reached multiple times THEN the system SHALL CONTINUE TO prevent duplicate floating text using the existing tracking mechanism

3.5 WHEN `board_mutated` signal is emitted THEN the system SHALL CONTINUE TO trigger cache invalidation handlers in ShopScene

3.6 WHEN other SignalBus signals are emitted (`economy_changed`, `inventory_changed`, etc.) THEN the system SHALL CONTINUE TO function as they currently do
