# Walkthrough - Passive Log Synchronization & UI Stability

Final summary of changes made to resolve redundant logging and ghost passive notifications.

## 🛠️ Engine Improvements
- **Duplicate Guard (Once Per Turn):** Added `_last_turn` tracking to `Fibonacci Sequence`, `Sirius`, and `Narwhal` in `engine_core/passives/combat.py`. These cards now only trigger and log once per turn, even in multi-encounter combat phases.
- **Ghost Log Prevention:** Modified `engine_core/passive_trigger.py` to strictly verify if a passive handler exists before recording a log entry. This prevents unimplemented cards (like Baroque) from appearing as "ghost" entries during income/market phases.
- **Logging Consolidation:** Removed manual log appends in `engine_core/player.py`. All passive events now flow through the central `trigger_passive` system, ensuring consistent filtering and preventing double-logging of copy-strengthening events.
- **Turn Ignition Fix:** Removed the redundant `game.start_turn()` in `main.py`. The initial turn is now handled correctly by the `ShopScene` without skipping turn counts.

## 🖥️ UI & HUD Enhancements
- **Dynamic Log Sync:** `SynergyHud` now detects when the engine log is cleared (via `GameState.reset_turn()`) and resets its tracking index accordingly. This ensures a fresh feed every turn without historical baggage.
- **Historical Replay Fix:** Initialized `_feed_seen_count` in the `SynergyHud` constructor to match the current log length, preventing old logs from "playing back" on scene transitions.
- **Duplicate Entry Guard:** Implemented a 100ms time-based duplicate guard in `SynergyHud.add_log` to filter out identical entries arriving in the same frame.

## ✅ Verification Results
- **Fibonacci Test:** Confirmed that wins only generate one log entry per turn.
- **Baroque Test:** Ghost logs for unimplemented passives are now suppressed.
- **Turn Start Test:** Initial turn logs no longer appear twice.
- **Stability:** Fixed a `NameError` in the logging logic to ensure crash-free combat phases.
