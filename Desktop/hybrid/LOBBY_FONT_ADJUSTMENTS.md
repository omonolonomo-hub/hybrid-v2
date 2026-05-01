# 🔤 Lobi Ekranı - Font Ayarlamaları

## 🔄 Değişiklikler (v1.7)

broken-strings.regular fontu için tüm layout, spacing ve hover efektleri yeniden ayarlandı.

### **1. Font Boyutları** ✅

| Font | Önceki | Yeni | Değişim |
|------|--------|------|---------|
| **Satır Fontu** | 24pt | 26pt | +2pt |
| **Dropdown Fontu** | 20pt | 22pt | +2pt |

**Sebep:** broken-strings.regular daha ince, biraz büyütmek okunabilirliği artırıyor

### **2. Satır Arka Planları** ✅

#### **AI Satırları:**
| Özellik | Önceki | Yeni | Değişim |
|---------|--------|------|---------|
| **Yükseklik** | 40px | 44px | +4px |
| **Y Offset** | -4px | -6px | +2px |

**Sebep:** Daha büyük font için daha yüksek arka plan gerekli

#### **Human Satırı:**
| Özellik | Önceki | Yeni | Değişim |
|---------|--------|------|---------|
| **Yükseklik** | 44px | 48px | +4px |
| **Y Offset** | -6px | -8px | +2px |

**Sebep:** Human satırı AI'dan biraz daha belirgin olmalı

### **3. Satır Aralıkları** ✅

#### **AI Satırları:**
| Element | Önceki | Yeni | Değişim |
|---------|--------|------|---------|
| **AI Numarası** | 20px | 20px | - |
| **Ayırıcı** | 100px | 105px | +5px |
| **Strateji** | 150px | 160px | +10px |

**Sebep:** Daha büyük font için daha geniş aralıklar

#### **Human Satırı:**
| Element | Önceki | Yeni | Değişim |
|---------|--------|------|---------|
| **►** | 20px | 20px | - |
| **SEN** | 55px | 60px | +5px |
| **Ayırıcı** | 115px | 125px | +10px |
| **HUMAN** | 160px | 175px | +15px |

**Sebep:** Üst üste binmeyi önlemek için daha geniş aralıklar

### **4. Dropdown Boyutları** ✅

| Özellik | Önceki | Yeni | Değişim |
|---------|--------|------|---------|
| **Genişlik** | 240px | 250px | +10px |
| **Item Yüksekliği** | 34px | 36px | +2px |
| **X Pozisyonu** | 150 - 4 | 160 - 6 | +10px |
| **Y Pozisyonu** | +35px | +38px | +3px |

**Sebep:** Daha büyük font için daha geniş ve yüksek dropdown

### **5. Dropdown Item Pozisyonları** ✅

| Element | Önceki | Yeni | Değişim |
|---------|--------|------|---------|
| **Checkmark Y** | +5px | +6px | +1px |
| **Text X (seçili)** | +35px | +38px | +3px |
| **Text X (normal)** | +15px | +16px | +1px |
| **Text Y** | +7px | +8px | +1px |

**Sebep:** Daha büyük font için daha iyi hizalama

### **6. Hover Efektleri** ✅

| Özellik | Önceki | Yeni | Değişim |
|---------|--------|------|---------|
| **Alpha** | 30 | 35 | +5 |
| **Border Radius** | 8px | 10px | +2px |
| **Button Width** | +40px | +45px | +5px |
| **Button Height** | +4px | +6px | +2px |

**Sebep:** Daha büyük font için daha belirgin hover efekti

## 📊 Karşılaştırma

### **Önceki (24pt Font):**
```
┌────────────────────────────────┐
│ AI 1 — WARRIOR              ●  │  40px yükseklik
└────────────────────────────────┘
     ↑    ↑      ↑
    20  100    150  ← Pozisyonlar
```

### **Yeni (26pt Font):**
```
┌────────────────────────────────┐
│                                │
│ AI 1 — WARRIOR                 │  44px yükseklik
│                                │
└────────────────────────────────┘
     ↑    ↑      ↑
    20  105    160  ← Pozisyonlar (daha geniş)
```

## 🎨 Görsel Hiyerarşi

### **Font Boyutları:**
```
LOBBY (48pt)           ← En büyük (BitcountGridDoubleInk)
  ↓
Alt Başlık (16pt)      ← Küçük (broken-strings.regular)
  ↓
AI Satırları (26pt)    ← Orta (broken-strings.regular)
  ↓
Dropdown (22pt)        ← Orta-Küçük (broken-strings.regular)
  ↓
Start Buton (32pt)     ← Büyük (minimap_category_names)
  ↓
Alt Bilgi (13pt)       ← En küçük (broken-strings.regular)
```

### **Arka Plan Yükseklikleri:**
```
AI Satırı:     44px  ← Standart
Human Satırı:  48px  ← Biraz daha yüksek (vurgulu)
Dropdown Item: 36px  ← Orta
```

## 🔧 Teknik Detaylar

### **Font Yükleme:**
```python
# Satır fontu (26pt)
self._font_row = pygame.font.Font(
    str(font_dir / "broken-strings.regular.ttf"), 26
)

# Dropdown fontu (22pt)
self._font_dropdown = pygame.font.Font(
    str(font_dir / "broken-strings.regular.ttf"), 22
)
```

### **Satır Arka Planı:**
```python
# AI satırları
row_bg_height = 44  # 40 → 44
row_bg_y = row_y - 6  # -4 → -6

# Human satırı
human_bg_height = 48  # 44 → 48
human_bg_y = human_y - 8  # -6 → -8
```

### **Dropdown Boyutları:**
```python
dropdown_w = 250  # 240 → 250
item_h = 36  # 34 → 36
dropdown_x = content_padding + 160 - 6  # 150 - 4 → 160 - 6
dropdown_y = row_y + 38  # 35 → 38
```

### **Hover Efekti:**
```python
# Dropdown button hover
dropdown_btn_w = strategy_surf.get_width() + 45  # 40 → 45
dropdown_btn_h = strategy_surf.get_height() + 6  # 4 → 6
pygame.draw.rect(hover_surf, (*strategy_color, 35), 
               hover_surf.get_rect(), border_radius=10)  # 30 → 35, 8 → 10
```

## 📐 Pozisyon Tablosu

### **AI Satırları:**
| Element | X Pozisyonu | Değişim |
|---------|-------------|---------|
| AI Numarası | `row_start_x + 20` | - |
| Ayırıcı | `row_start_x + 105` | +5px |
| Strateji | `row_start_x + 160` | +10px |

### **Human Satırı:**
| Element | X Pozisyonu | Değişim |
|---------|-------------|---------|
| ► | `row_start_x + 20` | - |
| SEN | `row_start_x + 60` | +5px |
| Ayırıcı | `row_start_x + 125` | +10px |
| HUMAN | `row_start_x + 175` | +15px |

### **Dropdown:**
| Element | Değer | Değişim |
|---------|-------|---------|
| Genişlik | 250px | +10px |
| Item Yüksekliği | 36px | +2px |
| X Offset | 160 - 6 | +10px |
| Y Offset | +38px | +3px |

## 📝 Sonuç

Font ayarlamaları tamamlandı:
- ✅ Font boyutları: 24pt → 26pt (satır), 20pt → 22pt (dropdown)
- ✅ Satır arka planları: 40px → 44px (AI), 44px → 48px (human)
- ✅ Satır aralıkları: +5px ~ +15px genişletildi
- ✅ Dropdown boyutları: 240px → 250px genişlik, 34px → 36px yükseklik
- ✅ Hover efektleri: Daha belirgin (alpha 35, radius 10px)
- ✅ Tüm pozisyonlar yeni font boyutuna göre ayarlandı

**Sonuç:** broken-strings.regular fontu için mükemmel hizalama ve okunabilirlik! 🔤

---

**Güncelleme:** 2026-04-30
**Versiyon:** 1.7 (Font Adjustments)
**Durum:** ✅ Tamamlandı ve Test Edildi
