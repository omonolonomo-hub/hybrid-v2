# HYBRID OYUN - UYGULANABILIR IMPLEMENTATION PLAN
**Planlama Tarihi:** 22 Nisan 2026  
**Bağlam:** Senior Architect Analizi + 3 Rapor verileri  
**Önemli Not:** 4. synergy tipi ASLA eklenmeyecek → KRİTİK-3 önceliği yeniden değerlendirildi

---

## 📊 PLANI ŞEKİLLENDİREN FAKTÖRLER

### ✅ Sabitler (Değişmeyecek)
- ❌ Yeni synergy tipi ekleme: **DEĞİL** → KRİTİK-3 önceliği düşer (ama Code Smell kalır)
- ✅ 100 yeni kart ekleme: **Desteklenecek**
- ✅ Yeni AI stratejiler: **Desteklenecek**
- ✅ Production release: **Mayıs başında hedef**

### ⚠️ Değişkenler
- Dev team size: Varsayılan 2-3 kişi
- Testing capacity: Otomatik test + manual regression
- Timeline: 4 hafta (CRITICAL sızlıyor)

---

## 🎯 REVISED PRIORITY (Synergy Extensibility Out)

| Sıra | Görev | Severity | Effort | Block? |
|------|-------|----------|--------|--------|
| **P0-1** | Board state desync fix | CRITICAL | 4h | YES - UI crash |
| **P0-2** | Synergy BFS duplication | CRITICAL | 6h | YES - logic divergence |
| **P0-3** | 3-group parameterization | STRATEGIC | 4h | NO - not needed (downgraded from 8h) |
| **P0-4** | cards_bought dual source | CRITICAL | 2h | YES - state corruption |
| **P0-5** | Error handling | CRITICAL | 2h | YES - debugging hell |
| **P1-1** | Board god object split | STRATEGIC | 12h | NO - refactoring |
| **P1-2** | Synergy BFS O(n²) cache | STRATEGIC | 3h | NO - optimization |
| **P1-3** | Game.log rotation | STRATEGIC | 2h | NO - memory leak |
| **P1-4** | AI config error handling | STRATEGIC | 2h | NO - robustness |
| **P1-5** | Documentation | STRATEGIC | 6h | NO - maintenance |

### KRİTİK-3 DOWNGRADE JUSTIFICATION
```
Eski: "3-group hardcoded IMPOSSIBLE to extend"
Yeni: "3-group hardcoded ama 4. synergy asla eklenmeyecek"

Effort: 8h → 4h (sadece Code Smell cleanup, generalization değil)
Reason: Optimize for current scope (3 group = final design)
```

---

## 📅 HAFTA-HAFTA PLAN (WEEK 1-4)

---

## **HAFTA 1: KRITIK SORUNLAR (Mon-Fri)**

### **Team Setup (Mon 08:00)**
```
Dev A: Board state desync + synergy BFS duplication
Dev B: Dual state + error handling + supporting
Test: Regression test suite setup
```

### **MON - P0-1: Board State Desync** (4h, 08:00-12:00)

**Dev A Task:**
```
Dosya: v2/core/state_store.py, v2/core/game_state.py
Görev:
  1. StateStore._board_names cache'i kaldır (veya auto-sync et)
  2. Player.board.grid'i hook et → StateStore'a notify et
  3. Place/remove() çağrılarında _invalidate_cache() tetikle
  
Detay:
  - v2/core/state_store.py:36-44 oku (state cache)
  - engine_core/board.py:place(), remove() oku (mutasyon noktaları)
  - Hook pattern: Player.board'a state_store callback pass et
  
Test:
  - Unit test: Board.place() → state invalidated?
  - Unit test: StateStore._build_board_view() live sync yapıyor mu?
```

**Code Pattern:**
```python
# v2/core/state_store.py
class StateStore:
    def __init__(self, callback=None):
        self._invalidate_callback = callback
    
    def notify_board_mutation(self):
        self._cached_public_state = None  # Invalidate cache
    
# Player initialization:
player.board._mutation_callback = state_store.notify_board_mutation
```

**Verification:**
```
✓ Mevcut 8 test: test_game_state_engine_contract.py hepsı pass
✓ Yeni test: test_board_state_sync.py (3 test case)
```

---

### **MON (Afternoon 13:00-17:00) & TUE Morning: P0-2: Synergy BFS Duplication** (6h total)

**Dev A Task:**
```
Dosya: engine_core/board.py, v2/core/ui_adapter.py, v2/core/synergy_calculator.py
Görev:
  1. Tüm BFS implementations'ı karşılaştır (diff)
  2. v2/core/synergy_calculator.py'ı audit et (correct implementation?)
  3. board.py ve ui_adapter.py'daki BFS'i sil
  4. Tüm consumers'ı synergy_calculator.py'a yönlendir
  
Schedule:
  Mon 13:00-14:00: Code diff + analysis
  Mon 14:00-16:00: Delete + redirect
  Mon 16:00-17:00: Compile test
  Tue 09:00-12:00: Full regression test
  
Detay:
  - engine_core/board.py:198-241 (`calculate_group_synergy_bonus()`)
  - v2/core/synergy_calculator.py:77-145 (`SynergyCalculator.compute()`)
  - v2/core/ui_adapter.py (grep için: BFS / visited / groups)
  
Test:
  - Unit test: SynergyCalculator.compute() same result as board.calculate_group_synergy_bonus()?
  - Integration test: UI shows correct synergy bonus
  - Regression: All 8 tests pass
```

---

### **TUE Afternoon-WED Morning: P0-4 & P0-5** (4h total)

**Dev B Task (TUE 13:00-15:00): Dual cards_bought State** (2h)
```
Dosya: engine_core/player.py
Görev:
  1. cards_bought_this_turn private convert et
  2. stats dict'e computed property yap
  3. buy_card() single source ile update et
  4. reset_turn_state() add et
  
Code:
  - Remove: player.cards_bought_this_turn = 0 (direct init)
  - Add: @property cards_bought_this_turn → return self._cards_bought_this_turn
  - Update: buy_card() → self._cards_bought_this_turn += 1; self.stats[...] = ...
  - Add: reset_turn_state() → reset both to 0
  
Test:
  - Unit test: Dual update consistency
```

**Dev B Task (TUE 15:00-17:00 + WED 09:00-11:00): Error Handling** (2h)
```
Dosya: v2/core/engine_adapter.py, engine_core/strategy_logger.py
Görev:
  1. Create EngineAdapterError exceptions
  2. Replace bare except: with specific types
  3. Add logging context
  
Code:
  - v2/core/engine_adapter.py:30-35 → PlayerNotFoundError
  - v2/core/engine_adapter.py:52-61 → Replace None with exceptions
  - strategy_logger.py:329, 513 → Add logger.error() context
  
Test:
  - Unit test: get_player(999) raises PlayerNotFoundError?
```

---

### **WED Afternoon-THU: Testing & Integration** (8h)

**Dev A + B + Test:**
```
WED 13:00-17:00: Integration testing
  - All 5 critical fixes + regression suite
  - Board state + synergy + dual state + error handling
  
THU 09:00-17:00: Full regression + edge cases
  - 100 game simulations with assertions
  - State consistency checks every turn
  - Error path validation
  
Result:
  ✓ All 8 existing tests pass
  ✓ 15+ new unit tests added
  ✓ No regression in AI, combat, passives
```

---

### **FRI: Code Review + Buffer**

```
FRI 09:00-12:00: Peer review
  - Code quality check
  - Architecture consistency
  - Test coverage
  
FRI 13:00-17:00: Buffer time
  - Any blockers fixed
  - Documentation updated
  - Ready for week 2
```

---

## **HAFTA 2: STRATEJİK REFACTORS (Mon-Fri)**

### **Team Allocation**
```
Dev A: Board god object split (ComboDetector, DamageCalculator)
Dev B: Config system + balance constants extraction
Test: Refactor test suite updates
```

---

### **MON-TUE: P1-1 Board God Object Split** (12h, Dev A)

**Phase 1: ComboDetector Extract (Mon 08:00-12:00, 4h)**
```
Dosya: engine_core/board.py, engine_core/combo_detector.py (new)
Görev:
  1. New file: combo_detector.py
  2. find_combos() + supporting functions move
  3. Board.find_combos() → ComboDetector.find_combos(board) delegate
  4. All tests update
  
Code Movement:
  - engine_core/board.py:296-325 → combo_detector.py:find_combos()
  - Board.find_combos() → return ComboDetector.find_combos(self)
  
Test:
  - Unit test: ComboDetector.find_combos() returns same as before
  - Integration: Combat still works (combos detected correctly)
```

**Phase 2: DamageCalculator Extract (Mon 13:00-17:00, 4h)**
```
Dosya: engine_core/board.py, engine_core/damage_calculator.py (new)
Görev:
  1. New file: damage_calculator.py
  2. calculate_damage() + resolve_single_combat() extract (if possible)
  3. Hardcoded formulas → DamageCalculator methods
  4. Turn multiplier → get_turn_damage_multiplier(turn)
  
Code Movement:
  - engine_core/board.py:348-375 → damage_calculator.py
  - board.py:139-178 (resolve_single_combat) → damage_calculator.py?
    (May be too coupled, keep in board.py for now)
  
Test:
  - Unit test: DamageCalculator.calculate_damage() accurate
```

**Phase 3: Integration & Testing (TUE 09:00-17:00, 8h combined with Dev B)**
```
TUE 09:00-12:00: Dev A completes extraction
TUE 13:00-17:00: Full test suite run + edge cases
```

---

### **TUE-WED: P1-4 & Balance Config** (4h, Dev B)

**TUE 09:00-13:00: AI Config Error Handling** (2h)
```
Dosya: engine_core/ai.py
Görev:
  1. AIConfigError exception class create
  2. load_strategy_params() → raise on missing file
  3. Add logging + context
  
Code:
  - Replace bare except
  - JSON decode errors → wrap with context
  
Test:
  - Unit test: Missing file raises AIConfigError
  - Unit test: Invalid JSON raises descriptive error
```

**TUE 13:00-17:00 + WED 09:00-12:00: Balance Constants Extract** (2h)
```
Dosya: engine_core/constants.py, engine_core/game_balance.py (new)
Görev:
  1. New: game_balance.py (or expand constants.py)
  2. Move hardcoded values:
     - Synergy tier bonuses: [3, 9, 16, 25]
     - Damage multipliers: [0.5, 1.0, 5, 15]
     - Synergy bonus cap: 0.30
  3. Load from game_balance.yaml (optional, but future-proof)
  
Code:
  - board.py:228 (bonus_level_1, etc) → SYNERGY_TIERS
  - board.py:333 (0.30 cap) → SYNERGY_BONUS_CAP
  - damage_calculator.py → use constants
  
Test:
  - Unit test: Constants loaded correctly
  - Integration: Damage formula uses constants
```

---

### **WED-THU: P1-2 Synergy BFS O(n²) Caching** (3h, Dev A)

**WED 13:00-17:00: Implement Board Hash + Cache** (3h)
```
Dosya: v2/core/synergy_calculator.py
Görev:
  1. Add board hash detection
  2. Cache SynergyViewState between calls
  3. Invalidate on board change
  
Code Pattern:
  ```python
  class SynergyCalculator:
      def __init__(self):
          self._last_board_hash = None
          self._cached_result = None
      
      def compute(self, board: Board) -> SynergyViewState:
          board_hash = hash(tuple(sorted(board.grid.items())))
          
          if board_hash == self._last_board_hash and self._cached_result:
              return self._cached_result
          
          result = self._compute_bfs(board)
          self._last_board_hash = board_hash
          self._cached_result = result
          return result
  ```
  
Test:
  - Unit test: Same board hash → cached result
  - Unit test: Board changed → recalculated
  - Perf test: 60 FPS maintained (no lag)
```

---

### **THU-FRI: Week 2 Integration & Testing** (8h)

**THU 09:00-17:00: Regression + Performance**
```
- ComboDetector isolated tests
- DamageCalculator accuracy tests
- Balance constants loaded correctly
- Synergy cache hitrate >80%
- All 8 original tests still pass
- New 20+ unit tests for refactored code
```

**FRI: Code Review + Perf Profiling**
```
FRI 09:00-12:00: Performance baseline
  - Measure synergy BFS time (before cache)
  - Compare with cache enabled
  - Expected: 10-15% improvement in UI render time
  
FRI 13:00-17:00: Code review + cleanup
```

---

## **HAFTA 3: OPTIMIZATION + DOCS (Mon-Fri)**

### **MON: P1-3 Game.log Rotation** (2h, Dev B)

```
Dosya: engine_core/game.py
Görev:
  1. Replace list with deque(maxlen=10000)
  2. Automatic old entries popped on append
  3. Add config for max_log_size
  
Code:
  ```python
  from collections import deque
  
  class Game:
      def __init__(self, max_log_size: int = 10000):
          self.log: Deque[str] = deque(maxlen=max_log_size)
      
      def _log(self, msg: str):
          self.log.append(msg)
  ```
  
Test:
  - Unit test: Log max size enforced
  - Memory test: 1000 game log < 50 MB
```

---

### **MON-TUE: P1-5 Documentation** (6h, Dev A)

**MON 08:00-12:00: Architecture Docs** (4h)
```
Dosya: docs/ARCHITECTURE.md (create)
Başlıklar:
  1. Module dependency graph (ASCII diagram)
  2. State management flow (StateStore → PublicState)
  3. Board responsibilities (now split):
     - Board (hex grid + placement)
     - ComboDetector (combo detection)
     - DamageCalculator (damage resolution)
  4. Synergy system (BFS algorithm explanation)
  5. Passive trigger system (timing + hooks)
  6. AI strategy system (config-based)
  
Hedef: New dev hire can understand architecture in 1 hour
```

**MON 13:00-17:00 + TUE 09:00-13:00: Code Comments + API Docs** (2h)
```
Dosya: Tüm .py files (docstrings update)
Görev:
  1. Add docstrings to public methods
  2. Type hints completion
  3. Inline comments for complex logic
  
Pattern:
  ```python
  def calculate_damage(attacker_pts: int, defender_pts: int, synergy_bonus: float) -> int:
      """Calculate combat damage resolution.
      
      Args:
          attacker_pts: Attacker's total point value
          defender_pts: Defender's total point value
          synergy_bonus: Synergy damage multiplier (0.0-0.30 capped)
      
      Returns:
          Final damage dealt (0 or positive)
      """
  ```
```

---

### **TUE-WED: Code Quality Audit** (4h, Dev B)

```
TUE 13:00-17:00 + WED 09:00-12:00: Exception Handling Audit
  - Replace any remaining bare except:
  - Add logger context to all error paths
  - Type hint completeness check
  
WED 13:00-17:00: Magic Number Audit
  - Extract remaining hardcoded values
  - Verify all constants in constants.py or game_balance.py
```

---

### **THU-FRI: Full Regression + Performance** (8h)

```
THU 09:00-17:00: Comprehensive testing
  - Run full test suite (50+ tests)
  - Manual gameplay (20 games, different strategies)
  - Memory profiling (no leaks)
  - Performance baseline (FPS stable at 60)
  
FRI 09:00-12:00: Performance report
  - Synergy BFS: X ms (was Y ms, -Z%)
  - Turn processing: A ms (was B ms, -C%)
  - Memory: D MB stable
  
FRI 13:00-17:00: Release readiness check
```

---

## **HAFTA 4: QA + RELEASE PREP (Mon-Fri)**

### **MON: Staging Deployment** (1 day)

```
Dev A + Dev B:
  1. Deploy to staging environment
  2. Run full test suite on staging
  3. Manual smoke test (5 complete games)
  4. Verify all fixes in place
  
Checklist:
  ✓ Board state sync working
  ✓ Synergy BFS single source
  ✓ No crashes on 100 game simulation
  ✓ UI responsive (60 FPS)
  ✓ Error messages descriptive
```

---

### **TUE-WED: Manual Testing + Edge Cases** (2 days)

```
Test Plan:
  1. 50 game simulations (all strategies)
     - Check no crashes
     - Check AI behaves normally
     - Check state consistency
  
  2. Edge cases:
     - Player placed card on all hex coords
     - High synergy board (all connected)
     - Low synergy board (isolated cards)
     - Combat with various edge combinations
  
  3. Passive system edge cases:
     - All passive triggers fire correctly
     - Copy milestones tracked accurately
     - Buff log integrity
  
  4. UI edge cases:
     - Fast clicking (multiple actions)
     - Reroll spam
     - Shop lock/unlock rapid
```

---

### **THU: Release Candidate Build** (1 day)

```
Dev A + Release Manager:
  1. Tag version v0.7 (Fixes Release)
  2. Build release candidate
  3. Run full smoke test
  4. Create release notes:
     - 5 critical bugs fixed
     - 8 strategic improvements
     - 15+ new tests added
     - Performance +10%
  
Release Notes Template:
  ## v0.7 - Architecture Hardening Release
  
  ### 🔧 Critical Fixes
  - Board state desynchronization fixed
  - Synergy calculation unified (single source of truth)
  - State consistency improved
  - Error handling improved (descriptive errors)
  
  ### ⚡ Performance
  - Synergy BFS caching: +15% UI performance
  - Log rotation: Memory bounded
  
  ### 📚 Developer Experience
  - Architecture documentation (docs/ARCHITECTURE.md)
  - Refactored god object (Board → Board + ComboDetector + DamageCalculator)
  - Config system for balance tuning
```

---

### **FRI: Go/No-Go Decision + Rollout**

```
FRI 09:00-12:00: Final decision
  - Pass all acceptance criteria?
  - Team sign-off?
  - Risk assessment?
  
FRI 13:00-17:00: Release rollout (if GO)
  - Deploy to production
  - Monitor error rates (should ↓)
  - Monitor performance (should ↑)
  - Monitor uptime (should stay 100%)
  
Post-Release:
  - 24h monitoring (on-call available)
  - If bugs found: hotfix process
```

---

## 📊 RESOURCE ALLOCATION

### Dev Team (2-3 people, 4 weeks)

| Role | Person | Week 1 | Week 2 | Week 3 | Week 4 |
|------|--------|--------|--------|--------|--------|
| **Dev A** (Lead) | Senior | P0-1,2 | P1-1 | P1-2,5 (docs) | Staging + Rollout |
| **Dev B** | Mid | Support + P0-4,5 | P1-4 + Balance | P1-3 + QA | QA + Rollout |
| **QA/Test** | Contractor | Regression setup | Test suite | Full regression | Manual testing |

### Effort Breakdown
```
Week 1: 22h critical fixes + 16h testing = 38h total
Week 2: 16h refactoring + 8h testing = 24h total
Week 3: 12h optimization + docs + 8h testing = 20h total
Week 4: 8h staging + 16h QA + release = 24h total

TOTAL: 106 hours (2 devs × 4 weeks + contractor support)
```

---

## 🚨 RISK MITIGATION

### Risk 1: P0-1 Board Desync Breaks UI
**Mitigation:**
- Implement hook pattern (non-invasive)
- Unit test before integration
- Staged rollout in test suite first
- Rollback plan: Revert hook, use StateStore rebuild instead

### Risk 2: Synergy BFS Deletion Causes Logic Bug
**Mitigation:**
- Diff all 3 implementations (line by line)
- Keep old code in branch for reference
- Run 100 game simulations before deletion
- Peer review before merging

### Risk 3: Board Refactoring Breaks Combat
**Mitigation:**
- Extract ComboDetector (low coupling to combat)
- Keep DamageCalculator as wrapper initially
- Extensive combat testing (50+ game simulations)
- Revert plan: Undo extraction, keep god object

### Risk 4: Config System Failure
**Mitigation:**
- YAML optional (defaults embedded in Python)
- Fallback mechanism if config missing
- Validation tests for config loading
- Clear error messages if invalid

### Risk 5: Timeline Slip (Scope Creep)
**Mitigation:**
- Strict scope: Only these 5 critical + 8 strategic
- No new features during fix period
- Daily standup (15 min) to catch blockers
- Buffer time in Week 4

---

## ✅ ACCEPTANCE CRITERIA

### Week 1 (Critical Fixes)
```
✓ All 5 critical issues resolved
✓ All 8 existing tests pass
✓ 15+ new unit tests added
✓ No regressions vs baseline
✓ Manual 50-game simulation OK
```

### Week 2 (Strategic Refactors)
```
✓ Board split into 3 classes (Board, ComboDetector, DamageCalculator)
✓ Synergy cache hitrate >80%
✓ Balance config working
✓ AI config errors handled
✓ All 8 original + 35+ new tests pass
```

### Week 3 (Optimization + Docs)
```
✓ Game.log bounded (max_log_size working)
✓ Architecture.md complete (readable by junior dev)
✓ All docstrings present
✓ Performance baseline: +10% UI FPS
✓ No memory leaks (100 game sim <100 MB)
```

### Week 4 (Release)
```
✓ Staging deployment successful
✓ 100 game manual QA pass
✓ Edge cases tested and pass
✓ Release notes written
✓ v0.7 tagged and ready
```

---

## 📋 DAILY STANDUP TEMPLATE

**Duration:** 15 minutes  
**Participants:** Dev A, Dev B, QA, Lead  
**Format:**
```
Each dev:
  1. What did you complete yesterday?
  2. What are you doing today?
  3. Any blockers?
  
Example (Mon standup):
  
Dev A: "Analyzed board state cache, identified hook point.
         Today: Implement StateStore callback. No blockers."
         
Dev B: "Setup regression test suite.
        Today: Implement dual state fix. Blocked: Need board.place() location."
        
QA:    "Test infrastructure ready.
        Today: Implement new test cases. No blockers."
```

---

## 📞 ESCALATION PROTOCOL

**If blocker > 1 hour:**
1. Stop work
2. Call standup (ad-hoc)
3. Lead decision: Unblock or defer to Week 4
4. Document in risk log

**If regression found:**
1. Immediate pause
2. Root cause analysis
3. Fix + regression test
4. Resume

---

## 🎯 SUCCESS METRICS (Hafta 4 End)

| Metric | Target | Current | After |
|--------|--------|---------|-------|
| Crashes per 100 games | <1 | ~3 | 0 |
| Error message quality | "Readable" | "AttributeError" | "Specific context" |
| Synergy sync issues | 0 | ~5% | 0 |
| Test coverage | >80% | ~70% | >85% |
| Docs (% of codebase) | >40% | ~20% | >50% |
| FPS stability | 60 ± 2 | 55-60 | 60-62 |
| Memory usage (100 games) | <100 MB | ~500 MB | <100 MB |

---

## 📅 TIMELINE AT A GLANCE

```
WEEK 1
Mon-Tue: Board state desync + synergy BFS (10h)
Wed-Thu: Dual state + error handling (4h)
Fri: Integration testing (8h)

WEEK 2
Mon-Tue: Board god object split (12h)
Tue-Wed: Config + AI error handling (4h)
Thu: Synergy cache (3h)
Fri: Regression testing (8h)

WEEK 3
Mon: Game.log rotation (2h)
Mon-Tue: Documentation (6h)
Tue-Wed: Code audit (4h)
Thu-Fri: Full regression + perf (8h)

WEEK 4
Mon: Staging deployment
Tue-Wed: Manual QA + edge cases
Thu: Release candidate build
Fri: Go/No-go + rollout
```

---

## 📝 NOTES FOR TEAM

### For Dev A (Lead Dev)
- You own P0-1, P0-2 (critical)
- Mentor Dev B on patterns
- Do all code reviews (quality gate)
- Decide P0-3 priority (can defer if needed)

### For Dev B (Supporting Dev)
- You own P0-4, P0-5 (error handling, state)
- Learn the architecture (read SENIOR_ARCHITECT_REPORT.md first)
- Ask questions early (don't assume)
- Support Dev A on P0-1 debugging

### For QA/Test
- Set up automated regression suite (Week 1 priority)
- Manual testing plan (Week 4 detailed)
- Document all edge cases found
- Performance baseline before/after measurements

### For Lead Manager
- Daily standup (15 min)
- Friday review (assess week progress)
- Escalate blockers immediately
- Risk log updated weekly

---

## 🔗 DEPENDENCIES BETWEEN TASKS

```
P0-1 (Board desync)
  ↓
P0-2 (Synergy BFS)
  ↓
P1-1 (Board split) - Wait until P0-2 done
  ↓
P1-2 (Synergy cache)

P0-4 (Dual state) - Independent
P0-5 (Errors) - Independent (except uses P0-1 patterns)

P1-3 (Log rotation) - Independent
P1-4 (AI config) - Independent
P1-5 (Docs) - Dependent on all other refactors done
```

**Critical Path:** P0-1 → P0-2 → P1-1 → P1-2 = 25 hours  
**Parallel Path:** P0-4, P0-5, P1-3, P1-4 = 8 hours

---

## ✨ GO LIVE CHECKLIST (Week 4 Friday)

```
□ All 5 critical fixes deployed
□ Zero regressions vs baseline
□ 50+ manual tests pass
□ Performance +10% (FPS)
□ Memory stable (<100 MB)
□ Error messages descriptive
□ Docs complete
□ Team trained
□ Release notes ready
□ Rollback plan documented
□ On-call schedule set

SIGN-OFF:
  Dev A: ____________
  Dev B: ____________
  QA: ________________
  Lead: _____________
```

---

**Plan Owner:** Senior Game Architect  
**Last Updated:** 22 Nisan 2026  
**Status:** 📋 READY FOR EXECUTION
