# Font Güncellemesi - 99_percent_OCCUPY

## ✅ Tamamlanan Değişiklikler

### 1. Font Tanımı Eklendi

**Dosya:** `v2/constants.py`

```python
FONT_STAT_PASSIVE: str = "99_percent_OCCUPY.ttf"  # Stat ve passive bölümü için
```

### 2. Font Cache Fonksiyonu Eklendi

**Dosya:** `v2/ui/font_cache.py`

```python
def stat_passive(size: int) -> pygame.font.Font:
    return get(Typography.FONT_STAT_PASSIVE, size)
```

### 3. Info Box Güncellemeleri

**Dosya:** `v2/ui/info_box_new1.py`

#### Stat Bölümü:

- ✅ **Stat Label** (POW:, DUR:, vb.) → `font_cache.stat_passive()`
- ✅ **Stat Value** (sayılar) → `font_cache.stat_passive()`

#### Passive Bölümü:

- ✅ **Passive Label** (◈ COMBAT WIN) → `font_cache.stat_passive()`
- ✅ **Passive Text** (açıklama metni) → `font_cache.stat_passive()`

## 🎨 Kullanım Alanları

### Info Box'ta Görünecek Yerler:

1. **Stat İsimleri:**

   ```
   POW: 5
   DUR: 4
   SIZ: 3
   SPE: 6
   ```

2. **Stat Değerleri:**

   ```
   5, 4, 3, 6, vb.
   ```

3. **Passive Label:**

   ```
   ◈ COMBAT WIN
   ◈ INCOME
   ◈ SYNERGY FIELD
   ```

4. **Passive Açıklama:**
   ```
   Win: strongest enemy loses highest edge.
   Income: +1 gold each turn.
   ```

## 📊 Font Özellikleri

- **Font Adı:** 99_percent_OCCUPY
- **Dosya:** `v2/assets/fonts/99_percent_OCCUPY.ttf`
- **Stil:** Özel, karakteristik
- **Kullanım:** Stat ve passive bölümleri

## 🎮 Test

Oyunu başlatın ve bir kartın üzerine gelin:

```bash
python v2/main.py
```

Info Box'ta stat ve passive bölümlerinde yeni font görünecek!

## 🔧 Boyut Ayarları

Eğer font boyutlarını değiştirmek isterseniz:

### Stat Label Boyutu

**Dosya:** `v2/ui/info_box_new1.py` (~612. satır)

```python
mono_sz = max(int(16 * s), int(18 * s))  # Bu değerleri değiştirin
```

### Stat Value Boyutu

**Dosya:** `v2/ui/info_box_new1.py` (~614. satır)

```python
val_sz = max(int(18 * s), int(20 * s))  # Bu değerleri değiştirin
```

### Passive Label Boyutu

**Dosya:** `v2/ui/info_box_new1.py` (~542. satır)

```python
lbl_fs = max(12, int(14.5 * s))  # Bu değerleri değiştirin
```

### Passive Text Boyutu

**Dosya:** `v2/ui/info_box_new1.py` (~525. satır)

```python
p_font = font_cache.stat_passive(max(11, int(13.5 * s)))  # Bu değerleri değiştirin
```

## 📝 Notlar

- Font otomatik olarak yüklenir
- Fallback mekanizması var (font bulunamazsa sistem fontu kullanılır)
- Tüm boyutlar render scale'e göre otomatik ayarlanır
- Font cache sistemi performansı korur

## 🎯 Sonuç

✅ Stat ve passive bölümleri artık 99_percent_OCCUPY fontu kullanıyor!
✅ Daha karakteristik ve özel bir görünüm
✅ Info Box'ta daha belirgin ve okunabilir
