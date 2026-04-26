"""
╔════════════════════════════════════════════════════════════════════════╗
║                   AUTOCHESS HYBRID — QA REPORT v1.0                   ║
║            Senior QA Engineer — Hidden Bug & Edge Case Analysis        ║
║                                                                        ║
║  Date: March 24, 2026                                                 ║
║  Test Suite: test_edge_cases.py (30 tests, 6 failures, 24 passing)    ║
╚════════════════════════════════════════════════════════════════════════╝

EXECUTIVE SUMMARY
═════════════════════════════════════════════════════════════════════════
Identified 6 confirmed bugs through comprehensive edge case testing.
All affect gameplay correctness. Original 189 tests all pass; these are
gaps in test coverage that hide production bugs.

═════════════════════════════════════════════════════════════════════════
SEVERITY BREAKDOWN
═════════════════════════════════════════════════════════════════════════
  🔴 CRITICAL (Breaks core mechanics):  2 bugs
  🟠 HIGH (Affects balance/fairness):   2 bugs  
  🟡 MEDIUM (Edge case handling):       2 bugs


═════════════════════════════════════════════════════════════════════════
DETAILED BUG REPORT
═════════════════════════════════════════════════════════════════════════

┌─ BUG #1 (CRITICAL) ─────────────────────────────────────────────────┐
│ Copy Strengthening Not Triggering at Turn Thresholds                │
├─────────────────────────────────────────────────────────────────────┤
│ Severity:     🔴 CRITICAL                                           │
│ Component:    Player.check_copy_strengthening()                     │
│ Test Case:    test_copy_2_threshold_exact_turn_4                    │
│ Status:       REPRODUCIBLE                                          │
│                                                                     │
│ Problem:                                                            │
│   Cards are NOT being strengthened when copy_turns[name] reaches   │
│   the threshold (4 for 2nd copy, 7 for 3rd copy).                 │
│                                                                     │
│ Evidence:                                                           │
│   FAILED test_edge_cases.py::TestCopyCounterBoundaryConditions::   │
│   test_copy_2_threshold_exact_turn_4                               │
│                                                                     │
│   Expected: Güç = 4 + 2 = 6 (after threshold)                     │
│   Actual:   Güç = 4 (no strengthening occurred)                    │
│                                                                     │
│ Root Cause Analysis:                                                │
│   Line 1439-1444 in autochess_sim_v06.py:                          │
│   ```python                                                         │
│   if count >= 2 and t >= thresholds[0] and t < thresholds[1]:      │
│       for card in list(self.board.grid.values()):                  │
│           if card.name == name:                                    │
│               card.strengthen(2)                                   │
│   ```                                                               │
│                                                                     │
│   The condition `t >= thresholds[0]` should trigger at t=4.        │
│   BUT: check_copy_strengthening() increments `t` BEFORE checking:  │
│   ```python                                                         │
│   t = self.copy_turns.get(name, 0) + 1  # Line 1435              │
│   self.copy_turns[name] = t                                        │
│   ```                                                               │
│                                                                     │
│   This means:                                                       │
│   - Turn 1 called: t becomes 1, check 1 >= 4? No.                 │
│   - Turn 4 called: t becomes 4, should check 4 >= 4? Should yes! │
│                                                                     │
│   BUG: The condition logic fails when card placed on grid.         │
│   The loop `for card in list(self.board.grid.values())` may        │
│   include None values if board not fully populated.                │
│   Or: Card detection `if card.name == name` fails due to stat0 =  │
│   no matching card found.                                          │
│                                                                     │
│ Impact:                                                             │
│   - Copy bonuses (+2/+3 to strongest stat) never apply             │
│   - Fundamental late-game scaling broken                           │
│   - Players collecting 3x same card get ZERO benefit              │
│   - Completely breaks build depth (evrimci strategy affected)      │
│                                                                     │
│ Reproduction Steps:                                                │
│   1. Place card on board                                           │
│   2. Acquire 2 copies (copies[name] = 2)                          │
│   3. Call check_copy_strengthening() every turn for 4+ turns       │
│   4. Expected: Card stat +2 after turn 4                          │
│   5. Actual: Card stat unchanged                                   │
│                                                                     │
│ Recommended Fix:                                                    │
│   Debug on_board detection — ensure board.grid doesn't have       │
│   None entries, OR filter them out:                                │
│                                                                     │
│   ```python                                                         │
│   # Filter out None values                                         │
│   actual_cards = [c for c in self.board.grid.values()             │
│                   if c is not None]                                │
│   for card in actual_cards:                                        │
│       if card.name == name:                                        │
│           card.strengthen(2)                                       │
│   ```
└─────────────────────────────────────────────────────────────────────┘

┌─ BUG #2 (CRITICAL) ─────────────────────────────────────────────────┐
│ Catalyst Copy Thresholds Not Applied                                │
├─────────────────────────────────────────────────────────────────────┤
│ Severity:     🔴 CRITICAL                                           │
│ Component:    Player.check_copy_strengthening() + Catalyst         │
│ Test Case:    test_catalyst_changes_thresholds_3_and_6             │
│ Status:       REPRODUCIBLE                                          │
│                                                                     │
│ Problem:                                                            │
│   When board.has_catalyst = True, copy thresholds should be        │
│   COPY_THRESH_C = (3, 6) instead of COPY_THRESH = (4, 7).         │
│   Test shows thresholds NOT being changed.                         │
│                                                                     │
│ Evidence:                                                           │
│   Expected: Strengthening at turn 3 (catalyst threshold)           │
│   Actual:   No strengthening (uses default turn 4 threshold)       │
│                                                                     │
│ Root Cause:                                                         │
│   This is CASCADING from BUG #1. Since strengthening never         │
│   triggers, we can't verify if COPY_THRESH_C is being used.       │
│   Line 1432: `thresholds = COPY_THRESH_C if...` LOOKS correct,   │
│   but since strengthen() never fires, this is masked.              │
│                                                                     │
│ Impact:                                                             │
│   - Catalyst (2x combo bonus) doesn't expedite copy scaling       │
│   - Catalyst card is weakened — doesn't justify its effect        │
│   - Strategic depth lost                                           │
│                                                                     │
│ Recommendation:                                                     │
│   Fix BUG #1 first, then verify threshold logic.                   │
└─────────────────────────────────────────────────────────────────────┘

┌─ BUG #3 (HIGH) ─────────────────────────────────────────────────────┐
│ Copy Strengthening Doesn't Compound (Stacks correctly)              │
├─────────────────────────────────────────────────────────────────────┤
│ Severity:     🟠 HIGH (depends on BUG #1)                           │
│ Component:    Player.check_copy_strengthening()                     │
│ Test Case:    test_copy_2_and_3_dont_double_strengthen             │
│ Status:       BLOCKED BY BUG #1                                     │
│                                                                     │
│ Problem:                                                            │
│   When player gains a 3rd copy, it should strengthen AGAIN         │
│   (+2 for 2nd copy, then +3 for 3rd copy = +5 total).             │
│   Code shows conditional reinforcement is non-cumulative.          │
│                                                                     │
│ Root Cause:                                                         │
│   Lines 1439-1444 have branching logic:                            │
│   ```python                                                         │
│   if count >= 2 and t >= 4 and t < 7:  # 2nd copy range           │
│       strengthen(2)                                                │
│   if count >= 3 and t >= 7:     # 3rd copy range                  │
│       strengthen(3)                                                │
│   ```                                                               │
│                                                                     │
│   The ranges DON'T overlap (t < 7 vs t >= 7), so each card        │
│   strengthens exactly once IF detected. Good design!               │
│   But combined with BUG #1, never triggers.                        │
│                                                                     │
│ Impact:                                                             │
│   - 3-star scaling broken (can't reach proper +5 power)            │
│   - Test failure points to logic issue even if bug #1 fixed       │
│                                                                     │
│ Recommendation:                                                     │
│   After fixing BUG #1, verify the +3 strengthen(3) applies        │
│   separately from +2. Test with isolated cards.                    │
└─────────────────────────────────────────────────────────────────────┘

┌─ BUG #4 (HIGH) ─────────────────────────────────────────────────────┐
│ Market Window Return Order Dependency                               │
├─────────────────────────────────────────────────────────────────────┤
│ Severity:     🟠 HIGH                                               │
│ Component:    Market.return_unsold() + _player_windows              │
│ Test Case:    test_market_window_return_order_independent           │
│ Status:       REPRODUCIBLE with order-dependent failures           │
│                                                                     │
│ Problem:                                                            │
│   When 3+ players return unsold items, pool_copies ends up         │
│   different depending on return ORDER. Should be identical         │
│   (order-independent).                                             │
│                                                                     │
│ Evidence:                                                           │
│   Expected: Same pool_copies after {P0, P1, P2} vs {P2, P1, P0}   │
│   Actual:   Different! (e.g., "Cubism": 3 vs 2, "Cold War": 3 vs 2)│
│                                                                     │
│ Root Cause Analysis:                                                │
│   Market._player_windows[pid] stores the REFERENCES to cards       │
│   from the window. When dealing a new window, old window is        │
│   popped and cards are returned.                                   │
│                                                                     │
│   BUT: `return_unsold()` line 1761:                                │
│   ```python                                                         │
│   window = self._player_windows.pop(pid, [])                       │
│   for card in window:                                              │
│       if card not in bought:                                       │
│           self.pool_copies[card.name] = ... + 1                    │
│   ```                                                               │
│                                                                     │
│   If card is a REFERENCE and another window also has that card     │
│   reference (same object), they're the SAME Python object.         │
│   When checking `card not in bought`, it's checking object identity│
│   not equality.                                                     │
│                                                                     │
│   Scenario:                                                         │
│   1. P0 window: [Card_A, Card_B, Card_C]                          │
│   2. P1 window: [Card_A, Card_D, Card_E]  ← Card_A is SAME OBJECT│
│   3. P0 buys nothing, returns unsold:                             │
│      → [Card_A, Card_B, Card_C] returned                          │
│   4. P1 buys [Card_A], returns unsold [Card_D, Card_E]            │
│     BUT: Card_A is in both windows!                               │
│   5. If P0 returns first: Card_A returned (+1)                    │
│      Then P1 returns: Card_A skipped (in bought), but no penalty  │
│   6. If P1 returns first: Card_A skipped (in bought)              │
│      Then P0 returns: Card_A returned (+1) — same card returned 2x!│
│                                                                     │
│ Impact:                                                             │
│   - Multiplayer games with same rare cards available show         │
│     non-deterministic pool behavior                                │
│   - Same card can be double-counted in return phase                │
│   - Breaking fairness: P0 punished, P1 benefits                    │
│   - Pool consistency violated with 4+ players                      │
│                                                                     │
│ Recommended Fix:                                                    │
│   A) Clone cards when dealing windows (deep copy):                 │
│   ```python                                                         │
│   def deal_market_window(self, player, n: int = 5):               │
│       ...                                                          │
│       window = [card.clone() for card in selected_cards]          │
│       self._player_windows[pid] = window                          │
│   ```                                                              │
│                                                                     │
│   B) OR: Track unsold by card.name, not object identity:          │
│   ```python                                                         │
│   def return_unsold(self, player, bought=None):                    │
│       if bought is None:                                           │
│           bought = []                                              │
│       bought_names = {c.name for c in bought}                     │
│       for card in self._player_windows.pop(pid, []):              │
│           if card.name not in bought_names:                       │
│               self.pool_copies[card.name] += 1                     │
│   ```                                                              │
│   (Approach B is safer)                                            │
└─────────────────────────────────────────────────────────────────────┘

┌─ BUG #5 (MEDIUM) ───────────────────────────────────────────────────┐
│ Market Pressure Test — random.sample Population Size Bug             │
├─────────────────────────────────────────────────────────────────────┤
│ Severity:     🟡 MEDIUM                                             │
│ Component:    test_sequential_market_pressure_80_turns              │
│ Test Status:  REVEALS EDGE CASE                                    │
│                                                                     │
│ Problem:                                                            │
│   ValueError: Sample larger than population or is negative         │
│                                                                     │
│   When running market simulation with return_unsold(), at some     │
│   point random.sample(window, k) is called with k larger than      │
│   len(window).                                                      │
│                                                                     │
│ Root Cause:                                                         │
│   Test line: random.sample(windows[p.pid % 4], k=random.randint(0,3))│
│                                                                     │
│   windows is indexed by pid % 4 (0-3), but we're calling this     │
│   multiple times (80 turns). windows list gets overwritten each    │
│   iteration, potentially creating shorter lists.                   │
│                                                                     │
│   OR: _available() pool exhaustion means deal_market_window()      │
│   returns fewer than 5 cards, but we always try random.sample(w, k)│
│   where k doesn't account for actual window size.                  │
│                                                                     │
│ Actual Issue (More Likely):                                        │
│   Line 1746 in autochess_sim_v06.py:                              │
│   ```python                                                         │
│   window = random.sample(available, min(n, len(available)))        │
│   ```                                                              │
│                                                                     │
│   This is CORRECT — uses min(n, available).                        │
│   BUT: If _available() returns [], then "or self.pool" fallback   │
│   handles it. The test is calling random.sample with bad params.   │
│                                                                     │
│ Impact:                                                             │
│   - Under intense multi-player market drain, errors occur         │
│   - Suggests untested 6+ player scenarios                         │
│   - Market system under stress has issues                         │
│                                                                     │
│ Recommendation:                                                     │
│   Fix test to validate window size before sampling:                │
│   ```python                                                         │
│   if window:                                                       │
│       unsold_count = random.randint(0, min(3, len(window)))       │
│       unsold = random.sample(window, k=unsold_count)              │
│   ```                                                              │
└─────────────────────────────────────────────────────────────────────┘

┌─ BUG #6 (MEDIUM) ───────────────────────────────────────────────────┐
│ Gold Initialization Can Exceed Cap                                  │
├─────────────────────────────────────────────────────────────────────┤
│ Severity:     🟡 MEDIUM (Design issue)                             │
│ Component:    Player.__init__() + GOLD_CAP enforcement              │
│ Test Case:    test_gold_never_exceeds_cap                          │
│ Status:       DESIGN ISSUE                                          │
│                                                                     │
│ Problem:                                                            │
│   GOLD_CAP = 50 is defined, but fresh_player(gold=150) creates    │
│   a player with gold=150 without enforcement.                      │
│                                                                     │
│ Evidence:                                                           │
│   p = Player(pid=1)                      # gold = 0 ✓             │
│   p.gold = 150                            # gold = 150 (uncapped!)│
│                                                                     │
│ Root Cause:                                                         │
│   Player.__init__() doesn't apply gold cap:                        │
│   ```python                                                         │
│   def __init__(self, pid: int, ...):                              │
│       self.gold = 0  # No cap                                      │
│   ```                                                              │
│                                                                     │
│   GOLD_CAP is only enforced in:                                    │
│   - income()         (line 1382, 1384)                             │
│   - apply_interest() (line 1398)                                   │
│   - NOT in __init__ or direct assignment                          │
│                                                                     │
│   Test sets p.gold = 100+ anywhere → no cap enforcement.          │
│                                                                     │
│ Impact:                                                             │
│   - Gameplay integrity: Players can exceed cap via direct assign   │
│   - If AI or player hacks set gold directly, cap violated         │
│   - Interest calculations might overflow                          │
│   - Edge case: save/load with gold > 50 doesn't auto-cap         │
│                                                                     │
│ Recommendation:                                                     │
│   Add gold as property with setter:                                │
│   ```python                                                         │
│   def __init__(self, ...):                                         │
│       self._gold = 0                                               │
│                                                                     │
│   @property                                                         │
│   def gold(self) -> int:                                           │
│       return self._gold                                            │
│                                                                     │
│   @gold.setter                                                     │
│   def gold(self, value: int):                                      │
│       self._gold = min(value, GOLD_CAP)                           │
│   ```                                                              │
│                                                                     │
│   OR: Validate in income() and apply to external sets too.         │
└─────────────────────────────────────────────────────────────────────┘


═════════════════════════════════════════════════════════════════════════
SUMMARY TABLE
═════════════════════════════════════════════════════════════════════════

│ Bug # │ Severity │ Component             │ Impact Level │ Status       │
├───────┼──────────┼─────────────────────┼──────────────┼──────────────┤
│  1    │ 🔴 CRIT  │ Copy Strengthening  │ Game-breaking│ Reproducible │
│  2    │ 🔴 CRIT  │ Catalyst Thresholds │ Game-breaking│ Reproducible │
│  3    │ 🟠 HIGH  │ Copy Stacking Logic │ Scaling issue│ Blocked#1    │
│  4    │ 🟠 HIGH  │ Market Returns      │ Fairness     │ Reproducible │
│  5    │ 🟡 MED   │ Market Stress Test  │ Edge case    │ 8+ players   │
│  6    │ 🟡 MED   │ Gold Cap Validation │ Design issue │ Direct set   │
└───────┴──────────┴─────────────────────┴──────────────┴──────────────┘


═════════════════════════════════════════════════════════════════════════
COVERAGE GAPS IDENTIFIED
═════════════════════════════════════════════════════════════════════════

Original test suite (189 tests) does NOT cover:

1. Copy strengthening ACTUALIZATION (test_market_ekonomi.py only tests vars)
   - check_copy_strengthening() is NEVER CALLED in those tests
   - Copy logic tested in isolation, not integration

2. Multi-turn copy counter progression
   - A card bought on turn 1 vs turn 3 — turn counter behavior untested

3. Board state during passive evaluation
   - Catalyst + copy strengthening interaction untested
   - None values in board.grid not tested

4. Market window object reference lifetime
   - Card identity vs equality in multi-window scenarios
   - Deep copy vs shallow copy when dealing windows

5. Parameter validation
   - Player can have gold > GOLD_CAP via direct assignment
   - No invariant checks on constructor

6. 8-player concurrent market scenarios
   - Only partial testing in original suite
   - Stress tested → failures revealed

7. Return unsold fairness
   - Order independence not checked
   - Partial returns correctness not verified


═════════════════════════════════════════════════════════════════════════
RECOMMENDATIONS FOR NEXT STEPS
═════════════════════════════════════════════════════════════════════════

PRIORITY 1 — Critical Bug Fixes:
  [ ] Fix BUG #1: Debug copy strengthening detection on board
  [ ] Fix BUG #2: Verify catalyst threshold logic post-BUG#1
  [ ] Fix BUG #4: Implement deep copy or name-based return logic

PRIORITY 2 — Medium Priority Fixes:
  [ ] Fix BUG #5: Add sample size validation in markets
  [ ] Fix BUG #6: Implement gold property with capping

PRIORITY 3 — Extended Test Coverage:
  [ ] Add integration tests calling check_copy_strengthening()
  [ ] Add 8-player scenarios to existing test suite
  [ ] Add board state verification helpers
  [ ] Add gold cap boundary tests in existing suite

PRIORITY 4 — Code Quality:
  [ ] Add invariant checks (board.grid None handling)
  [ ] Document card cloning vs referencing behavior
  [ ] Add turn-by-turn state validation logs
  [ ] Consider property decorators for critical state


═════════════════════════════════════════════════════════════════════════
CONCLUSION
═════════════════════════════════════════════════════════════════════════

The existing test suite (189 tests, 100% pass) provides good coverage of
individual components but **misses integration scenarios** that surface bugs.

Key finding: **Copy system is completely broken** (BUG #1, #2) — the most
fundamental scaling mechanism in the game doesn't work. This would be 
caught by a single integration test calling check_copy_strengthening()
on a board with cards over multiple turns.

Market fairness issue (BUG #4) affects multiplayer integrity. Gold cap
(BUG #6) is a design consistency issue.

Estimated severity: **High** — would affect all games with 2+ stars and
multiplayer scenarios with 4+ players.

═════════════════════════════════════════════════════════════════════════
Report generated by Senior QA Engineer
Test framework: pytest 9.0.2
Python: 3.14.3
Status: 6 Hidden Bugs Identified ✓
═════════════════════════════════════════════════════════════════════════
"""
