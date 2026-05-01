# Minimap Görsel Güncellemesi

## 🎯 Amaç

Minimap kategori bölümünü daha okunabilir ve görsel olarak daha belirgin hale getirmek.

## ✅ Yapılan Değişiklikler

### 1. İkon Boyutu Artırıldı

**Önceki:** 24 piksel
**Yeni:** 28 piksel (+17%)

```python
icon_size = 28  # Önceden: 24
```

### 2. Kategori İsimleri (Kısaltmalar) Büyütüldü

**Önceki:** 13 punto
**Yeni:** 16 punto (+23%)

```python
abbr_font = font_cache.minimap_cat(16)  # Önceden: 13
```

### 3. Sayılar Büyütüldü

**Önceki:** 18 punto
**Yeni:** 22 punto (+22%)

```python
font_cache.bold(22)  # Önceden: 18
```

### 4. Arka Plan Renkleri Daha Belirgin

**Aktif Kartlar (count > 0):**

- Opaklık: 90 → **140** (+56%)
- Kategori rengine hafif ton eklendi
- Kenarlık kalınlığı: 1px → **2px**
- Kenarlık opaklığı: 120 → **180** (+50%)

**Pasif Kartlar (count = 0):**

- Opaklık: 40 → **70** (+75%)

```python
# Aktif
b_alpha = 140  # Önceden: 90
bg_color = tuple(int(c * 0.15 + 18 * 0.85) for c in color) + (b_alpha,)
pygame.draw.rect(surface, (*color, 180), bg_rect, width=2, border_radius=5)

# Pasif
b_alpha = 70  # Önceden: 40
```

### 5. Gölge Efektleri Eklendi

- ✅ Kategori isimleri için gölge
- ✅ Sayılar için gölge
- Daha iyi kontrast ve okunabilirlik

```python
# Gölge render
shadow_color = (0, 0, 0, int(t_alpha * 0.6))
shadow_rect = pygame.Rect(abbr_x + 1, py + 1, abbr_w, row_h)
```

### 6. Boşluk Optimizasyonu

**İkon-Text Arası Boşluk:**

- Önceki: 8 piksel
- Yeni: 6 piksel (-25%)

Daha büyük ikonlar için alan açıldı.

## 📊 Boyut Karşılaştırması

| Öğe                 | Önceki         | Yeni           | Artış       |
| ------------------- | -------------- | -------------- | ----------- |
| **İkon**            | 24px           | 28px           | +17%        |
| **Kategori İsmi**   | 13pt           | 16pt           | +23%        |
| **Sayı**            | 18pt           | 22pt           | +22%        |
| **Aktif Arka Plan** | 90 alpha       | 140 alpha      | +56%        |
| **Pasif Arka Plan** | 40 alpha       | 70 alpha       | +75%        |
| **Kenarlık**        | 1px, 120 alpha | 2px, 180 alpha | +100%, +50% |

## 🎨 Görsel Etki

### Arka Plan

- ✅ Aktif kategoriler daha belirgin
- ✅ Kategori rengine hafif ton - daha renkli
- ✅ Daha kalın ve parlak kenarlıklar
- ✅ Pasif kategoriler bile daha görünür

### İçerik

- ✅ İkonlar %17 daha büyük - daha net
- ✅ Kategori isimleri %23 daha büyük - daha okunabilir
- ✅ Sayılar %22 daha büyük - daha belirgin
- ✅ Gölge efektleri - daha iyi kontrast

### Genel

- ✅ Daha profesyonel görünüm
- ✅ Daha kolay okunabilir
- ✅ Daha belirgin kategori ayrımı
- ✅ Daha modern ve şık

## 🎮 Test

```bash
python v2/main.py
```

Oyunda sol paneldeki minimap'e bakın:

- ✅ Daha büyük ikonlar
- ✅ Daha okunabilir kategori isimleri
- ✅ Daha belirgin arka planlar
- ✅ Daha net sayılar

## 🔧 Daha Fazla Büyütmek İsterseniz

### İkonları Daha Da Büyütmek

**Dosya:** `v2/ui/minimap_hud.py` (~262. satır)

```python
icon_size = 32  # Daha da büyük (28->32)
```

### Kategori İsimlerini Daha Da Büyütmek

**Dosya:** `v2/ui/minimap_hud.py` (~300. satır)

```python
abbr_font = font_cache.minimap_cat(18)  # Daha da büyük (16->18)
```

### Sayıları Daha Da Büyütmek

**Dosya:** `v2/ui/minimap_hud.py` (~318. satır)

```python
font_cache.bold(24)  # Daha da büyük (22->24)
```

### Arka Planı Daha Da Belirgin Yapmak

**Dosya:** `v2/ui/minimap_hud.py` (~253. satır)

```python
# Aktif
b_alpha = 160  # Daha opak (140->160)
bg_color = tuple(int(c * 0.25 + 18 * 0.75) for c in color) + (b_alpha,)  # Daha renkli

# Kenarlık
pygame.draw.rect(surface, (*color, 220), bg_rect, width=3, border_radius=5)  # Daha kalın ve parlak
```

## 📝 Notlar

- Tüm değişiklikler minimap'in sol alt panelinde görünür
- Kategori renkleri korundu (MYTHOLOGY: sarı, ART: kırmızı, vb.)
- Gölge efektleri performansı minimal etkiler
- Arka plan tonları kategori renklerine göre dinamik

## 🎯 Sonuç

✅ İkonlar %17 büyütüldü
✅ Kategori isimleri %23 büyütüldü
✅ Sayılar %22 büyütüldü
✅ Arka planlar %56-75 daha belirgin
✅ Gölge efektleri eklendi
✅ Daha okunabilir ve profesyonel görünüm
