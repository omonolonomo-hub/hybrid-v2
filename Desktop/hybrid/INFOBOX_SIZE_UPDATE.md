# Info Box Boyut Güncellemesi

## ✅ Yapılan Değişiklikler

### 1. Passive Bölümü Büyütüldü

#### Passive Label (◈ COMBAT WIN)

**Önceki:** 12-14.5 punto
**Yeni:** 16-18 punto (+33%)

```python
lbl_fs = max(16, int(18 * s))  # Önceden: max(12, int(14.5 * s))
```

#### Passive Açıklama Metni

**Önceki:** 11-13.5 punto
**Yeni:** 15-17 punto (+36%)

```python
p_font = font_cache.stat_passive(max(15, int(17 * s)))  # Önceden: max(11, int(13.5 * s))
```

### 2. Stat Bölümü Büyütüldü

#### Stat İkonları

**Önceki:** 22-24 piksel
**Yeni:** 28-30 piksel (+27%)

```python
icon_sz = max(int(28 * s), int(30 * s))  # Önceden: max(int(22 * s), int(24 * s))
```

#### Stat Label (POW:, DUR:, vb.)

**Önceki:** 16-18 punto
**Yeni:** 20-22 punto (+25%)

```python
mono_sz = max(int(20 * s), int(22 * s))  # Önceden: max(int(16 * s), int(18 * s))
```

#### Stat Değerleri (Sayılar)

**Önceki:** 18-20 punto
**Yeni:** 24-26 punto (+33%)

```python
val_sz = max(int(24 * s), int(26 * s))  # Önceden: max(int(18 * s), int(20 * s))
```

#### Stat Satır Yüksekliği

**Önceki:** 32-36 piksel
**Yeni:** 38-42 piksel (+19%)

```python
stat_row_h = max(int(38 * s), int(42 * s))  # Önceden: max(int(32 * s), int(36 * s))
```

## 📊 Boyut Karşılaştırması

| Öğe               | Önceki    | Yeni    | Artış |
| ----------------- | --------- | ------- | ----- |
| **Passive Label** | 12-14.5pt | 16-18pt | +33%  |
| **Passive Text**  | 11-13.5pt | 15-17pt | +36%  |
| **Stat İkon**     | 22-24px   | 28-30px | +27%  |
| **Stat Label**    | 16-18pt   | 20-22pt | +25%  |
| **Stat Value**    | 18-20pt   | 24-26pt | +33%  |
| **Stat Row**      | 32-36px   | 38-42px | +19%  |

## 🎨 Görsel Etki

### Passive Bölümü

- ✅ Açıklama metni daha okunabilir
- ✅ Label daha belirgin
- ✅ 99_percent_OCCUPY fontu daha iyi görünür

### Stat Bölümü

- ✅ İkonlar daha net ve büyük
- ✅ Stat isimleri (POW:, DUR:) daha okunabilir
- ✅ Sayılar daha belirgin
- ✅ Genel olarak daha dengeli görünüm

## 🎮 Test

```bash
python v2/main.py
```

Bir kartın üzerine gelin ve Info Box'ta:

- Passive bölümünde daha büyük yazılar
- Stat bölümünde daha büyük ikonlar, yazılar ve sayılar göreceksiniz!

## 🔧 Daha Fazla Büyütmek İsterseniz

### Passive Bölümü

**Dosya:** `v2/ui/info_box_new1.py`

```python
# Passive label (satır ~541)
lbl_fs = max(18, int(20 * s))  # Daha da büyük

# Passive text (satır ~525)
p_font = font_cache.stat_passive(max(17, int(19 * s)))  # Daha da büyük
```

### Stat Bölümü

**Dosya:** `v2/ui/info_box_new1.py`

```python
# İkonlar (satır ~583)
icon_sz = max(int(32 * s), int(34 * s))  # Daha da büyük

# Label (satır ~612)
mono_sz = max(int(22 * s), int(24 * s))  # Daha da büyük

# Value (satır ~613)
val_sz = max(int(26 * s), int(28 * s))  # Daha da büyük

# Satır yüksekliği (satır ~582)
stat_row_h = max(int(42 * s), int(46 * s))  # Daha da büyük
```

## 📝 Notlar

- Tüm boyutlar render scale (`s`) ile çarpılır
- Render scale genellikle 2'dir (yüksek çözünürlük için)
- `max()` fonksiyonu minimum boyutu garanti eder
- Boyutlar piksel ve punto cinsindendir

## 🎯 Sonuç

✅ Passive bölümü %33-36 büyütüldü
✅ Stat bölümü %25-33 büyütüldü
✅ Daha okunabilir ve net görünüm
✅ 99_percent_OCCUPY fontu daha iyi görünür
