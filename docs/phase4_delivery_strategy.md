# Phase 4 Delivery Strategy

This document converts the Phase 4 analysis into an execution strategy.
It is planning-only. It does not authorize implementation to begin, and it
must be used together with `implementation_plan_v2.md`.

## Purpose

The remaining Phase 4 work is integration-heavy, not feature-discovery-heavy.
The main risk is silent mismatch between `engine_core` combat truth and what the
UI chooses to display. To reduce that risk, work must be split into small,
reviewable units and each unit must end with explicit test updates.

## Binding Guardrails

1. One deliverable per task. Do not auto-continue from `VersusScene` to
   `CombatTerminal`, or from `CombatTerminal` to `CombatScene`, in the same
   approval cycle.
2. QA Sandbox is mandatory. Every task must end with the relevant
   `test_*.py` files being created or updated before the task is considered
   complete.
3. "Gormedigim koda onay vermem" is a hard rule. Each task must stop after
   showing the production diff and the related test diff.
4. `v2/` remains UI-facing. `engine_core` must continue to be reached through
   `GameState` or a dedicated bridge/adapter layer, not imported directly from
   scene/widgets.
5. `passive_buff_log` is supplemental combat context, not the sole source of
   combat truth.
6. Scenes and widgets should consume normalized UI payloads. Raw engine
   objects, live boards, and score buckets should be adapted once in
   `GameState` or a formatter/bridge layer, then passed down as display-ready
   data.

## Test Layering Before Phase 4

The existing `MockGame`-based UI tests remain valuable, but they are no longer
enough on their own. Before Phase 4 feature work begins, the repo should use a
3-layer test strategy:

1. UI/widget tests:
   Keep using `MockGame` for fast, deterministic rendering and interaction
   checks.
2. Adapter/contract tests:
   Use the real `engine_core` to verify that `GameState` exposes stable UI
   contracts for pairing, identity, combat snapshots, `_prefix`, and
   elimination ordering.
3. Real-engine smoke tests:
   Add a few narrow end-to-end flow checks for preparation, pairing, combat,
   turn progression, and elimination. These are not full scene tests; they are
   correctness gates around the bridge layer.

Recommended initial files:
- `tests/test_game_state_engine_contract.py`
- `tests/test_engine_combat_contract.py`
- `tests/test_engine_turn_flow_smoke.py`

Rule:
- For new Phase 4 work, a widget/UI diff without the matching contract or smoke
  test update should be treated as incomplete QA.

## Target Data Flow

```text
ShopScene Ready / prep commit
  -> GameState phase wrapper
  -> engine.preparation_phase()
  -> GameState stores pairings / turn snapshot
  -> SceneManager.transition_to(VersusScene)

VersusScene
  -> reads pairing, hp, labels, turn from GameState only
  -> no combat resolution
  -> dismiss on timeout or input
  -> SceneManager.transition_to(CombatScene)

CombatScene.on_enter()
  -> GameState combat wrapper
  -> engine.combat_phase()
  -> engine.last_combat_results populated
  -> player.passive_buff_log populated
  -> GameState accessors expose raw combat snapshot
  -> Combat formatter converts raw data into terminal lines + footer
  -> CombatTerminal streams lines at 80 ms/line
  -> post-combat transition logic decides ShopScene vs EndgameScene
```

## Current Blocking Gaps

1. `v2/ui/combat_terminal.py` is a stub, so Phase 4 has no terminal surface yet.
2. `v2/scenes/combat.py` is a stub, so there is no place where combat snapshot,
   formatter, stream timing, and post-combat transition can live.
3. `v2/scenes/versus_splash.py` is only partially initialized and does not yet
   implement the planned scene contract.
4. `v2/core/game_state.py` still lacks several Phase 4 orchestration methods:
   `sync_state()`, `commit_human_turn()`, `run_ai_turns()`, `get_combat_log()`,
   and `get_prefix_bonus()`.
5. `v2/mock/engine_mock.py` does not yet provide realistic Phase 4 pairing and
   identity data. Today it lacks `swiss_pairs()`, per-player `strategy`, and a
   combat fixture suitable for terminal replay.
6. Identity schema differs across engines:
   Mock side exposes `name` but not `strategy`; real engine exposes `strategy`
   and `pid`, but not a dedicated `name` field.
7. The current Shop scene still contains hardcoded right-panel player data, so
   some scene transitions would visually bypass live engine state if Phase 4 is
   implemented on top of it without cleanup.
8. `v2/core/scene_manager.py` currently provides fade sequencing but no
   explicit Phase 4 transition-graph validation. Without contract tests,
   `Shop -> Versus -> Combat -> Shop/Endgame` drift can slip in silently.
9. `v2/ui/synergy_hud.py` currently reads `kill_a` / `kill_b` as if they were
   pure kill points, while live combat resolution still mixes some combat
   passive points into those buckets. The meaning of those fields is not frozen
   yet.

## Spec Clarifications Required By The Analysis

1. The current plan text says CombatTerminal should filter
   `entry.trigger == "combat"`. Actual engine triggers are
   `pre_combat`, `combat_win`, `combat_lose`, `card_killed`, `copy_2`,
   and `copy_3`. Until a normalization layer is added, the formatter must treat
   "combat-relevant triggers" as a set, not a single literal trigger value.
2. `passive_buff_log` only records entries when a passive changes card power.
   Some combat passives award points without increasing stats, so those events
   can be missing from the log even though they changed the score.
3. The footer damage equation in the current plan is incomplete if it is
   presented as exact engine math. Real engine damage also applies turn-based
   scaling and an early-game cap. Any displayed equation must either:
   - reflect the full calculation, or
   - clearly state it is a partial breakdown plus final post-scaling damage.
4. `_prefix` handling is also easy to misread. Combat resolution distributes
   hidden `_prefix` bonuses per card during edge comparison, while the planned
   UI footer wants a board-level display term. That display term must be treated
   as a UI summary, not assumed to be the exact internal application order.
5. `kill_a` / `kill_b` are not currently reliable "pure kill" fields. In the
   live engine they also absorb certain combat passive point returns before the
   total is written into `last_combat_results`. Until engine semantics are
   split, any UI that consumes them must label them carefully or normalize them
   first.
6. Phase 4 needs an explicit scene graph contract. The intended path is
   `ShopScene -> VersusScene -> CombatScene -> ShopScene` for normal flow, with
   `CombatScene -> EndgameScene` only after post-combat elimination/game-over
   checks. Skips and duplicate combat entry should be treated as bugs, not
   optional behavior.

## Recommended Task Decomposition

### Task A - VersusScene Only

Scope:
- Build only the matchup splash scene.
- Read only pairing, hp, turn, and player label data.
- Do not resolve combat and do not implement terminal streaming here.

Exit criteria:
- Dismiss-on-timeout works.
- Dismiss-on-click or SPACE works.
- Scene displays a single pairing without depending on combat data.

QA Sandbox:
- Update or create the relevant scene tests first-class, not as an afterthought.
- Expected tests: `tests/test_versus_scene.py` plus any required
  `tests/test_game_state.py` contract additions.

### Task B - CombatTerminal Only

Scope:
- Build `CombatTerminal` as a pure presentation widget.
- Input contract should be deterministic: preformatted `lines` plus a final
  `footer` string or structured footer payload.
- The widget must not call the engine directly.

Exit criteria:
- 80 ms per-line streaming works.
- Auto-scroll works.
- Newest line lands at the bottom.
- Final footer appears only after line streaming completes.

QA Sandbox:
- Update or create widget-focused terminal tests.
- Expected tests: `tests/test_combat_terminal.py`.

### Task C - CombatScene Only

Scope:
- Hook combat resolution to the scene entry point.
- Read `get_last_combat_results()` and `get_passive_buff_log(pid)`.
- Normalize them into terminal payloads for `CombatTerminal`.
- Handle wait-after-stream and transition-out timing.

Exit criteria:
- Combat is resolved exactly once on scene entry.
- Terminal input comes from one formatter path, not spread across widget code.
- Scene chooses next state cleanly after replay.

QA Sandbox:
- Update or create combat scene integration tests.
- Expected tests: `tests/test_combat_scene.py`.

### Task D - Endgame And Elimination Separately

Scope:
- Do not bundle elimination visuals and Endgame screen into the terminal task.
- Add them only after combat replay flow is stable.

Exit criteria:
- Newly eliminated players appear correctly in the UI.
- Endgame trigger is validated after combat resolution, not before.

QA Sandbox:
- Update or create dedicated tests for endgame/elimination behavior.
- Expected tests: `tests/test_endgame_scene.py` and any related lobby tests.

## Additional QA Coverage From The Second Scan

1. Scene transition validation:
   Pin the intended Phase 4 path and reject or ignore accidental skips,
   duplicate transitions, and invalid direct jumps deterministically.
2. Combat trigger single-fire coverage:
   Entering `CombatScene` should resolve combat exactly once even if
   `update()` runs multiple frames before exit.
3. Replay state capture:
   Verify `last_combat_results` is frozen before UI replay formatting and is
   not recomputed from later live board state.
4. Timer and stream lifecycle:
   Verify terminal stream timing, post-stream wait timing, and any replay/popup
   timer start and decrement as expected.
5. Turn cleanup contract:
   Verify turn increments, locked coordinates are cleared, and post-combat
   cleanup happens after replay data is captured.
6. Score semantics coverage:
   Add an explicit test for passive combat points versus real kill points so
   `CombatTerminal` and `SynergyHud` do not mislabel one as the other.
7. Pairing snapshot coverage:
   Verify `get_current_pairings()` reads the stored snapshot for the current
   turn instead of rerunning `swiss_pairs()` during rendering.
8. Identity bridge coverage:
   Verify `get_display_name(pid)` and `get_strategy(pid)` hide the schema drift
   between mock and real engines.
9. `_prefix` bridge coverage:
   Verify `get_prefix_bonus(pid)` behaves consistently for zero and non-zero
   states before footer rendering depends on it.

## Risk Register

### Risk 1 - Silent Math Desync In Footer

Cause:
- Recomputing damage from a mutated live board after combat removes cards or
  changes stats.

Mitigation:
- Freeze a combat snapshot immediately after `engine.combat_phase()` and derive
  terminal footer data from that snapshot, not from a later live board read.

### Risk 2 - Incomplete Combat Narrative

Cause:
- Using `passive_buff_log` as the only narrative source.

Mitigation:
- Treat `last_combat_results` as authoritative scoreboard truth.
- Treat `passive_buff_log` as supplemental flavor/context only.

### Risk 3 - Mock And Real Engine Drift

Cause:
- Mock schema does not yet expose the same pairing and identity contract needed
  by Versus and Combat scenes.

Mitigation:
- Add or document a minimal Phase 4 fixture contract before implementing the
  scenes.

### Risk 4 - Scope Creep Across Tasks

Cause:
- Trying to "finish the whole combat stack" in one pass.

Mitigation:
- Hard stop after each task.
- Review diff, test diff, and risk notes before opening the next task.

### Risk 5 - Hidden Spec Mismatch

Cause:
- Plan text and real engine behavior already diverge in trigger naming and
  damage presentation.

Mitigation:
- Lock the clarifications above into the main implementation plan before any
  production code starts.

### Risk 6 - Kill Bucket Semantics Are Misleading

Cause:
- `kill_a` / `kill_b` currently blend real kills with certain combat passive
  returns, but multiple UI surfaces read them as pure kill output.

Mitigation:
- Freeze and document field semantics before reusing them in Phase 4 UI.
- Ideally split passive combat points from kill points at the engine or bridge
  layer and add tests for both paths.

### Risk 7 - Scene Flow Drift Or Double Combat

Cause:
- The current `SceneManager` does not enforce a validated Phase 4 transition
  graph by itself.

Mitigation:
- Add scene-flow tests that pin `Shop -> Versus -> Combat -> Shop/Endgame`
  behavior and verify combat resolution is single-fire.

## Agent Checklist For Every Future Task

1. State the exact files owned by the task before editing.
2. Keep the task boundary narrow and stop after the requested deliverable.
3. Update the relevant `test_*.py` files in the same task.
4. Show the production diff and the test diff together.
5. Do not ask for approval to move to the next deliverable until the current
   one is fully visible and reviewed.
6. If the task touches scene flow or score presentation, update the transition
   and score-semantics tests in the same review cycle.
7. If the task depends on `GameState` bridge semantics, update the relevant
   real-engine contract tests in the same task.
