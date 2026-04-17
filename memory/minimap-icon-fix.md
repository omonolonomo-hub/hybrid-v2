# MinimapHUD Icon Fix - 2026-04-17

## Issue
COSMOS kategorisi için kullanılan "PLANET" ikonu hatalıydı veya uygun değildi.

## Solution
COSMOS ikonu "PLANET" → "STAR" olarak değiştirildi.

## Change Made

**File**: `v2/ui/minimap_hud.py`

```python
# BEFORE:
"COSMOS": {"color": (140, 80, 255), "abbr": "COSM", "icon": "PLANET"},

# AFTER:
"COSMOS": {"color": (140, 80, 255), "abbr": "COSM", "icon": "STAR"},
```

## Rationale
- STAR (⭐ yıldız) ikonu kozmos/uzay teması için daha uygun
- Font Awesome'da STAR ikonu daha yaygın ve güvenilir
- PLANET ikonu bazı font versiyonlarında eksik olabilir
- Görsel olarak daha net ve tanınabilir

## Category Icons Summary

| Category   | Icon      | Unicode | Description        |
|------------|-----------|---------|-------------------|
| MYTHOLOGY  | ANKH      | \uf669  | Ankh sembolü      |
| ART        | PALETTE   | \uf53f  | Sanat paleti      |
| NATURE     | SEEDLING  | \uf4d8  | Filiz/bitki       |
| COSMOS     | STAR      | \uf005  | Yıldız ⭐         |
| SCIENCE    | ATOM      | \uf5d2  | Atom sembolü      |
| HISTORY    | LANDMARK  | \uf66f  | Tarihi anıt       |

## Result
✅ COSMOS ikonu artık doğru görünüyor
✅ Tüm kategoriler tutarlı ikonlara sahip
✅ Font Awesome 7 Free ile tam uyumlu
