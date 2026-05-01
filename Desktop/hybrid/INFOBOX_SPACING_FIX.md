# Info Box Boşluk Düzenlemesi

## 🎯 Problem

Stat bölümündeki son sıra ikonları info box'ın alt kenarına değiyordu.

## ✅ Çözüm

Passive ve stat bölümleri arasındaki boşluğu azaltarak stat bölümüne daha fazla alan verildi.

## 📐 Yapılan Değişiklikler

### 1. Stat Alanı Toplam Yüksekliği Artırıldı

**Önceki:** 110-115 piksel
**Yeni:** 125-130 piksel (+13%)

```python
h_stats = max(125 * s, int(130 * s))  # Önceden: max(110 * s, int(115 * s))
```

### 2. Passive-Stat Arası Boşluk Azaltıldı

**Önceki:** `max(2 * s, gap // 3)`
**Yeni:** `max(1 * s, gap // 6)` (-50%)

```python
bottom_divider_y = stats_top - max(1 * s, gap // 6)  # Önceden: max(2 * s, gap // 3)
```

### 3. Stat Başlangıç Padding'i Azaltıldı

**Önceki:** 3 _ s
**Yeni:** 2 _ s (-33%)

```python
stats_start_y = stats_top + int(2 * s)  # Önceden: int(3 * s)
```

## 📊 Etki

### Stat Bölümü

- ✅ +15 piksel daha fazla yükseklik
- ✅ Alt kenara değme sorunu çözüldü
- ✅ İkonlar için daha fazla alan
- ✅ Daha rahat görünüm

### Passive Bölümü

- ✅ Minimal etki (sadece alt boşluk azaldı)
- ✅ İçerik alanı aynı kaldı
- ✅ Okunabilirlik korundu

## 🎨 Görsel Sonuç

```
┌─────────────────────────┐
│   Kart İsmi & Kategori  │
├─────────────────────────┤
│                         │
│   Passive Bölümü        │
│   ◈ COMBAT WIN          │
│   Win: strongest...     │
│                         │
├─────────────────────────┤ ← Boşluk azaltıldı
│                         │
│   POW: 5  ⚡  MEA: 4    │
│   DUR: 4  🔒  SEC: 3    │
│   SIZ: 3  🧠  INT: 5    │
│   SPE: 6  👣  TRA: 2    │
│   GRA: 4  🎵  HAR: 3    │
│   SPR: 5  💎  PRE: 4    │
│                         │ ← Daha fazla alan
└─────────────────────────┘
```

## 🎮 Test

```bash
python v2/main.py
```

Bir kartın üzerine gelin ve Info Box'ta:

- ✅ Son sıra stat ikonları alt kenara değmiyor
- ✅ Tüm statlar rahatça görünüyor
- ✅ Passive bölümü hala okunabilir

## 🔧 Daha Fazla Alan Gerekirse

### Stat Alanını Daha Da Büyütmek

**Dosya:** `v2/ui/info_box_new1.py` (~396. satır)

```python
h_stats = max(135 * s, int(140 * s))  # Daha da büyük
```

### Passive-Stat Boşluğunu Daha Da Azaltmak

**Dosya:** `v2/ui/info_box_new1.py` (~508. satır)

```python
bottom_divider_y = stats_top - max(0 * s, gap // 8)  # Minimum boşluk
```

### Stat Satır Yüksekliğini Azaltmak

**Dosya:** `v2/ui/info_box_new1.py` (~582. satır)

```python
stat_row_h = max(int(36 * s), int(40 * s))  # Daha kompakt (38->36, 42->40)
```

## 📝 Notlar

- Tüm değişiklikler render scale (`s`) ile çarpılır
- Render scale genellikle 2'dir
- Değişiklikler otomatik olarak tüm çözünürlüklere uyum sağlar
- Golden ratio (\_PHI) korundu

## 🎯 Sonuç

✅ Stat bölümü +15 piksel daha yüksek
✅ Passive-stat arası boşluk %50 azaldı
✅ Alt kenara değme sorunu çözüldü
✅ Daha dengeli görünüm
