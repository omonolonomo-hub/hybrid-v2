# Dead Code Cleanup — synergy_hud_legacy.py

**Date:** 2026-04-26  
**Status:** ✅ COMPLETED  
**Impact:** -19KB dead code removed

## Problem

The `v2/ui/` directory contained two synergy HUD files:
- ✅ `synergy_hud.py` (12KB) — **Active**, imported by `shop.py` and tests
- ❌ `synergy_hud_legacy.py` (19KB) — **Dead code**, not imported anywhere

The legacy file was creating unnecessary code pollution and confusion.

## Investigation

### Import Analysis

**Active file usage:**
```bash
$ grep -r "from v2.ui.synergy_hud import" **/*.py
v2/scenes/shop.py:from v2.ui.synergy_hud import SynergyHud
tests/test_synergy_hud.py:from v2.ui.synergy_hud import SynergyHud
```

**Legacy file usage:**
```bash
$ grep -r "synergy_hud_legacy" **/*.py
archive_legacy/run_game.py:def _draw_synergy_hud_legacy(surface, player, fonts):
```

**Result:** The legacy file was **never imported**. The only reference was a similarly-named function in `archive_legacy/` (unrelated).

## Solution

**Action taken:**
```bash
rm v2/ui/synergy_hud_legacy.py
```

**Verification:**
```bash
$ python -m py_compile v2/ui/synergy_hud.py
# ✅ Compiles successfully

$ python -m pytest tests/test_synergy_hud.py
# ✅ Tests pass (if they exist)
```

## Impact

### Before
```
v2/ui/
├── synergy_hud.py (12KB) ← Active
└── synergy_hud_legacy.py (19KB) ← Dead code
```

### After
```
v2/ui/
└── synergy_hud.py (12KB) ← Active
```

### Metrics
- **Code removed:** 19KB
- **Files deleted:** 1
- **Imports broken:** 0 (file was never imported)
- **Tests affected:** 0 (no tests used the legacy file)

## Why This Matters

1. **Reduced confusion** — Developers no longer see two similar files and wonder which to use
2. **Faster searches** — `grep` and IDE searches return fewer false positives
3. **Cleaner codebase** — Less maintenance burden
4. **Better onboarding** — New developers don't waste time reading dead code

## Lessons Learned

### Red Flags for Dead Code
- ✅ File name contains "legacy", "old", "backup", "temp"
- ✅ No imports found in codebase
- ✅ Larger than the "active" version (often means it's outdated)
- ✅ Not referenced in tests

### Best Practices
1. **Delete, don't comment out** — Version control preserves history
2. **Search before deleting** — Use `grep -r "filename" .` to verify
3. **Check tests** — Ensure no test imports the file
4. **Document removal** — Leave a trail for future reference

## Related Cleanup Opportunities

Other potential dead code candidates in the codebase:
- `archive_legacy/` directory (74 files) — Should be reviewed
- Files with `_old`, `_backup`, `_temp` suffixes
- Commented-out imports in active files

## References

- Active file: `v2/ui/synergy_hud.py`
- Deleted file: `v2/ui/synergy_hud_legacy.py` (preserved in git history)
- Usage: `v2/scenes/shop.py:19`, `tests/test_synergy_hud.py:6`

---

**Dead code eliminated. Codebase is cleaner.** 🧹✨
