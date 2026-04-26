# HYBRID OYUN - 4-HAFTA UYGULANABILIR PLAN (QUICK REFERENCE)

**Status:** 🟢 READY TO EXECUTE  
**Team Size:** 2-3 devs + 1 QA  
**Duration:** 4 weeks (106 hours)  
**Release Target:** v0.7 (Hafta 4 Cuma)

---

## 🎯 HAFTA-HAFTA SUMMARY

### HAFTA 1: KRITIK SORUNLAR (22h code + 16h test)
| Task | Owner | Time | Status |
|------|-------|------|--------|
| **P0-1:** Board state desync | Dev A | 4h | Not started |
| **P0-2:** Synergy BFS duplication | Dev A | 6h | Not started |
| **P0-4:** Dual cards_bought state | Dev B | 2h | Not started |
| **P0-5:** Error handling | Dev B | 2h | Not started |
| **Testing & Integration** | Test | 16h | Not started |

**Hafta 1 Target:** ✅ All 5 critical fixes done, 0 regressions

---

### HAFTA 2: REFACTORING (16h code + 8h test)
| Task | Owner | Time | Status |
|------|-------|------|--------|
| **P1-1:** Board god object split | Dev A | 12h | Blocked on P0-2 |
| **P1-4:** AI config error handling | Dev B | 2h | Blocked on P0-5 |
| **Balance config extraction** | Dev B | 2h | Blocked on P0-5 |
| **Testing & Integration** | Test | 8h | Blocked on code |

**Hafta 2 Target:** ✅ 3 classes (Board, ComboDetector, DamageCalculator), +80% test coverage

---

### HAFTA 3: OPTIMIZATION (12h code + 8h test)
| Task | Owner | Time | Status |
|------|-------|------|--------|
| **P1-3:** Game.log rotation | Dev B | 2h | Blocked on Hafta 2 |
| **P1-5:** Documentation | Dev A | 6h | Blocked on Hafta 2 |
| **P1-2:** Synergy BFS caching | Dev A | 3h | Blocked on P0-2 |
| **Code audit** | Dev B | 1h | Blocked on Hafta 2 |
| **Testing & Regression** | Test | 8h | Blocked on code |

**Hafta 3 Target:** ✅ Architecture docs done, +10% performance, 0 memory leaks

---

### HAFTA 4: RELEASE (Staging + QA)
| Task | Owner | Time | Status |
|------|-------|------|--------|
| **Staging deployment** | All | 1 day | Blocked on Hafta 3 |
| **Manual QA (100 games)** | Test | 2 days | Blocked on staging |
| **Release candidate build** | Dev A | 1 day | Blocked on QA |
| **Production rollout** | All | 1 day | Blocked on RC |

**Hafta 4 Target:** ✅ v0.7 released, 0 production issues in 24h

---

## 📊 CRITICAL PATH

```
P0-1 (4h) 
  → Board tested (4h)
     → P0-2 (6h)
        → Synergy tested (4h)
           → P1-1 (12h) ← LONGEST PATH
              → Full regression (8h)
                 → Hafta 4 QA
```

**Total Critical Path:** ~38 hours  
**Can Parallelize:** P0-4, P0-5, P1-3, P1-4 = 8 hours  
**Finish Line:** Thu Hafta 2 (if no blockers)

---

## ⚠️ TOP 3 BLOCKERS TO WATCH

| Blocker | Impact | Mitigation |
|---------|--------|-----------|
| **P0-2 Synergy BFS Deletion Breaks Tests** | Hafta 2 delay | Diff all 3 implementations, keep old code in branch |
| **P1-1 Board Refactoring Cascades** | Hafta 2 delay | Extract ComboDetector first (low risk), DamageCalculator second |
| **Timing Slip** | Release delay | Cap scope at these 5 critical + 8 strategic, no new features |

---

## 📋 DAILY STANDUP (15 min, 10:00 AM)

**Questions for Each Dev:**
1. ✅ What completed yesterday?
2. 📍 What's today's plan?
3. 🚨 Any blockers?

**Example Hafta 1 Standups:**

```
MON 10:00
  Dev A: "Analyzed board cache, found hook point. Today: implement StateStore callback."
  Dev B: "Regression test suite ready. Today: dual state fix."
  Test: "Baseline tests passing. Today: add new unit tests."

TUE 10:00
  Dev A: "Board desync done + tested. Today: start P0-2 (synergy BFS diff)."
  Dev B: "Dual state done. Today: error handling."

WED 10:00
  Dev A: "Synergy BFS duplication found (3 places). Today: delete + redirect."
  Dev B: "Error handling done. Today: support Dev A on synergy tests."

THU 10:00
  Dev A: "Synergy single source done. Today: full regression test run."
  Dev B: "All P0 tasks complete. Today: support testing."

FRI 10:00
  All: "Week 1 critical fixes: ✅ COMPLETE. 0 regressions. Ready for Week 2."
```

---

## 🎯 ACCEPTANCE CRITERIA (Hafta sonu kontrol listesi)

### Hafta 1 END
```
✓ 5 critical issues fixed and tested
✓ All 8 original tests pass
✓ 15+ new unit tests added
✓ 50-game simulation no crashes
✓ Code review passed
```

### Hafta 2 END
```
✓ Board split into 3 classes (Board, ComboDetector, DamageCalculator)
✓ Synergy cache hitrate >80%
✓ 35+ new tests pass
✓ 50-game simulation no crashes
✓ Performance stable (no regression)
```

### Hafta 3 END
```
✓ Architecture.md complete (readable by junior dev in <1h)
✓ Game.log bounded (no memory growth)
✓ +10% UI performance (synergy cache)
✓ 100-game simulation <100 MB memory
✓ All docstrings present
```

### Hafta 4 END
```
✓ Staging deployment successful
✓ 100 manual games QA pass
✓ v0.7 release notes written
✓ Release candidate built
✓ Production deployment approved
```

---

## 🔗 DEPENDENCY GRAPH (Which must finish before what)

```
HAFTA 1 (Must all finish before Hafta 2):
  ├─ P0-1 (4h) ┐
  ├─ P0-2 (6h) ├─ Testing (16h) ─→ GO TO HAFTA 2
  ├─ P0-4 (2h) ┤
  └─ P0-5 (2h) ┘

HAFTA 2 (Must all finish before Hafta 3):
  ├─ P1-1 (12h, depends on P0-2) ┐
  ├─ P1-4 (2h, depends on P0-5) ├─ Testing (8h) ─→ GO TO HAFTA 3
  ├─ Balance config (2h) ────────┤
  └─ Sync testing (2h) ──────────┘

HAFTA 3 (Must all finish before Hafta 4):
  ├─ P1-3 (2h) ┐
  ├─ P1-5 (6h) ├─ Full Regression (8h) ─→ GO TO HAFTA 4
  ├─ P1-2 (3h) ┤
  └─ Code audit (1h) ┘

HAFTA 4 (Staging + Release):
  Staging deployment → Manual QA → RC Build → Production rollout
```

---

## 💻 DEVELOPER TASK CARDS

### DEV A CARD (Lead, 52 hours total)

**Hafta 1:**
- [ ] MON 08:00-12:00: Board state desync (P0-1) - 4h
- [ ] MON 13:00-17:00 + TUE 09:00-12:00: Synergy BFS duplication (P0-2) - 6h
- [ ] WED-FRI: Integration testing + buffer - 8h
- **Hafta 1 Total:** 18h

**Hafta 2:**
- [ ] MON-TUE 09:00-17:00: Board god object split (P1-1) - 12h
- [ ] WED 13:00-17:00: Synergy cache implementation (P1-2) - 3h
- [ ] THU-FRI: Testing + code review - 8h
- **Hafta 2 Total:** 23h

**Hafta 3:**
- [ ] MON 08:00-12:00 + TUE 09:00-13:00: Documentation (P1-5) - 6h
- [ ] THU-FRI: Full regression + perf - 8h
- **Hafta 3 Total:** 14h

**Hafta 4:**
- [ ] Staging + Release coordination - 8h
- **Hafta 4 Total:** 8h

**TOTAL: 63 hours** (was 52, added buffer for debugging)

---

### DEV B CARD (Supporting, 32 hours total)

**Hafta 1:**
- [ ] TUE 13:00-15:00: Dual cards_bought state (P0-4) - 2h
- [ ] TUE 15:00-17:00 + WED 09:00-11:00: Error handling (P0-5) - 2h
- [ ] WED-FRI: Testing + support Dev A - 8h
- **Hafta 1 Total:** 12h

**Hafta 2:**
- [ ] TUE 09:00-13:00: AI config error handling (P1-4) - 2h
- [ ] TUE 13:00-17:00 + WED 09:00-12:00: Balance config (2h)
- [ ] THU-FRI: Testing + support - 8h
- **Hafta 2 Total:** 12h

**Hafta 3:**
- [ ] MON: Game.log rotation (P1-3) - 2h
- [ ] TUE-WED: Code audit - 4h
- [ ] THU-FRI: Testing - 4h
- **Hafta 3 Total:** 10h

**Hafta 4:**
- [ ] Staging + Release support - 6h
- **Hafta 4 Total:** 6h

**TOTAL: 40 hours**

---

## 📞 ESCALATION PROTOCOL

**If blocker > 1 hour:**
1. Call ad-hoc standup (5 min)
2. Lead decision: Unblock or defer
3. Document in risk log

**If regression found:**
1. Pause work
2. Root cause analysis
3. Fix + test
4. Resume

**If timeline at risk:**
1. Scope cut: Remove P1-5 (docs can be deferred)
2. Parallelize: More QA resources
3. Compress: Hafta 3 + 4 merged if needed

---

## ✅ SIGN-OFF CHECKLIST (Hafta 4 Cuma)

```
Pre-Release:
  □ All 50+ tests pass
  □ 100-game manual QA pass
  □ Performance +10%
  □ Zero memory leaks
  □ Docs complete
  □ Team trained
  □ Release notes ready
  □ Rollback plan documented

Signatures:
  Dev A (Lead): _________________ Date: _______
  Dev B (Support): ______________ Date: _______
  QA Lead: ______________________ Date: _______
  Manager: ______________________ Date: _______
  
GO/NO-GO DECISION: ____
```

---

## 📂 RELATED DOCUMENTS

- **SENIOR_ARCHITECT_REPORT.md** - Full details of all 5 critical + 8 strategic issues
- **IMPLEMENTATION_PLAN_EXECUTABLE.md** - This document (detailed task breakdown)
- **CODEBASE_ARCHITECTURE_ANALYSIS.md** - Technical deep-dive for reference
- **ARCHITECT_REPORT_EXECUTIVE_SUMMARY.md** - 1-page overview

---

**Created:** 22 Nisan 2026  
**Status:** 🟢 READY FOR EXECUTION  
**Last Updated:** [Team to update daily]

**Print this page and keep it on the wall! 📌**
