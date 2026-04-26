# MinimapHUD Optimization Log - 2026-04-17

## Problem
MinimapHUD'da hex grid kategori listesinin arkasında kalıyordu. Orantı hatası vardı.

## Solution
Passive COM-LOG'u kısaltıp MinimapHUD'a daha fazla alan açtık.

## Changes Made

### 1. SynergyHud Passive Feed Reduction
**File**: `v2/ui/synergy_hud.py`
- **Before**: `feed_h = 320px`
- **After**: `feed_h = 240px`
- **Gain**: 80px vertical space

### 2. MinimapHUD Position & Size Adjustment
**File**: `v2/ui/minimap_hud.py`

**Position**:
- **Before**: `anchor_y = 700`
- **After**: `anchor_y = 620`
- **Change**: 80px higher

**Size**:
- **Before**: `340x380px`
- **After**: `340x460px`
- **Gain**: 80px more height

**Proportions**:
- **Before**: 60% hex grid, 40% categories
- **After**: 65% hex grid, 35% categories
- **Hex Size**: 22px → 24px (9% larger)

### 3. Category Dashboard Refinements
- **Padding**: 8px → 10px (more breathing room)
- **Icon Size**: 14px → 16px (more visible)
- **Font Size**: 
  - Abbr: 10 → 11 (more readable)
  - Count: 16 → 18 (more prominent)
- **Border Radius**: 4px → 5px (smoother)
- **Alpha Values**: Increased for better contrast

## Layout Breakdown

```
BEFORE (v13):
┌─────────────────────┐
│ PlayerHub (150px)   │
├─────────────────────┤
│ SynergyHud Groups   │ 204px
├─────────────────────┤
│ Passive Feed        │ 320px ← TOO TALL
├─────────────────────┤ y=700
│ MinimapHUD          │
│  - Hex Grid         │ 228px (60%)
│  - Categories       │ 152px (40%)
└─────────────────────┘ 380px total

AFTER (v14):
┌─────────────────────┐
│ PlayerHub (150px)   │
├─────────────────────┤
│ SynergyHud Groups   │ 204px
├─────────────────────┤
│ Passive Feed        │ 240px ← COMPACT
├─────────────────────┤ y=620
│ MinimapHUD          │
│  - Header           │ 28px
│  - Hex Grid         │ 299px (65%) ← SPACIOUS
│  - Separator        │ 2px
│  - Categories       │ 161px (35%) ← BALANCED
└─────────────────────┘ 460px total
```

## Visual Improvements

### Hex Grid
- ✅ 24px hexes (vs 22px) - 9% larger
- ✅ More vertical space (299px vs 228px) - 31% more
- ✅ Better centered in section
- ✅ No overlap with categories

### Category Dashboard
- ✅ Larger icons (16px vs 14px)
- ✅ Bigger count numbers (18px vs 16px)
- ✅ More padding (10px vs 8px)
- ✅ Better contrast (higher alpha values)
- ✅ Smoother borders (5px radius)

### Passive Feed
- ✅ Still shows 10-12 log entries
- ✅ More compact but readable
- ✅ Freed up 80px for minimap

## Result
✅ Hex grid no longer overlaps with categories
✅ Better visual hierarchy
✅ More balanced proportions
✅ Improved readability across all sections
