# Figma Design Specification: Lobby Panel Row Component

**Kaynak Kod:** `v2/ui/lobby_panel.py`  
**Tarih:** 23 Nisan 2026  
**Tasarımcı:** Özhan Bagırgan

---

## 📐 Genel Bakış

Bu doküman, Pygame tabanlı lobby panel UI'ının Figma'da birebir karşılığını oluşturmak için gerekli tüm tasarım detaylarını içerir.

### Ana Bileşen
- **İsim:** `LobbyPanelRow`
- **Tip:** Component with Variants
- **Boyut:** 160px × 80px
- **Kullanım:** Oyuncu listesi satırı (8 oyuncu için dikey sıralama)

---

## 🎨 Renk Paleti (Color Styles)

Aşağıdaki renkleri Figma'da **Local Color Styles** olarak kaydedin:

| Stil Adı | Hex Kodu | RGB | Kullanım |
|----------|----------|-----|----------|
| `Category/MYTHOLOGY` | `#F8DE22` | (248, 222, 34) | Mitoloji kategorisi |
| `Category/ART` | `#F03C6E` | (240, 60, 110) | Sanat kategorisi |
| `Category/NATURE` | `#3CFF50` | (60, 255, 80) | Doğa kategorisi |
| `Category/COSMOS` | `#8C50FF` | (140, 80, 255) | Kozmos kategorisi |
| `Category/SCIENCE` | `#03BEF0` | (3, 190, 240) | Bilim kategorisi |
| `Category/HISTORY` | `#FF7828` | (255, 120, 40) | Tarih kategorisi |

### Sistem Renkleri

| Renk Adı | Hex/RGB | Kullanım |
|----------|---------|----------|
| `Text/Primary` | `#DCE6FF` | Normal oyuncu isimleri |
| `Text/Self` | `#00F2FF` | Kendi oyuncu ismi |
| `Text/Rank/Gold` | `#FFD700` | 1. sıra rank badge |
| `HP/Healthy` | `#00FF78` | HP > 40% |
| `HP/Critical` | `#FF3C3C` | HP ≤ 40% |
| `Border/Threat/Safe` | `#32A0D2` | HP yüksek |
| `Border/Threat/Danger` | `#FA3232` | HP düşük |
| `Glow/Hover` | `#00C8FF` @ 30% opacity | Hover efekti |
| `Overlay/Eliminated` | `#1E0505` @ 82% opacity | Ölü oyuncu |

---

## 🏗️ Component Yapısı

### Ana Frame: `LobbyPanelRow`
```
Frame Properties:
├─ Width: 160px (Fixed)
├─ Height: 80px (Fixed)
├─ Fill: Linear Gradient (varsayılan)
├─ Border Radius: 8px
├─ Border: 1px solid
└─ Auto Layout: OFF (manuel positioning)
```

---

## 🔀 Component Variants (Properties)

### Property 1: **State** (4 değer)

#### 1.1 Normal
- **Arkaplan Gradient:**
  - Top: `#232630` (RGB: 35, 38, 48)
  - Bottom: `#0C0E14` (RGB: 12, 14, 20)
- **Border:** 1px, `#2A3A5C` (RGB: 42, 58, 92)
- **Scale:** 100%
- **Efekt:** Yok

#### 1.2 Hover
- **Arkaplan:** Normal ile aynı
- **Border:** Normal ile aynı
- **Scale:** 103% (tüm frame)
- **Efekt:** 
  - Inner glow: `#00C8FF` @ 30% opacity
  - Blur: 4px
  - Spread: 2px

#### 1.3 Self (Kendi Oyuncu)
- **Arkaplan Gradient:**
  - Top: `#1E2D41` (RGB: 30, 45, 65)
  - Bottom: `#0A0F19` (RGB: 10, 15, 25)
- **Border:** 2px, `#00FFFF` (Cyan)
- **Scale:** 100%
- **Efekt:** Subtle outer glow (cyan, 2px)

#### 1.4 Eliminated (Ölü)
- **Arkaplan:** Normal gradient + overlay
- **Overlay Layer:**
  - Fill: `#1E0505` @ 82% opacity
  - Blend Mode: Normal
- **Border:** 1px, `#FF3C3C`
- **Text Overlay:** "ELIMINATED" (merkez, bold 12px, `#FF3C3C`)

---

### Property 2: **Rank** (4 değer)

#### 2.1 Default
- Normal gradient (yukarıda tanımlı)

#### 2.2 Top1 (Gold)
- **Arkaplan Gradient:**
  - Top: `#413714` (RGB: 65, 55, 20)
  - Bottom: `#190F05` (RGB: 25, 15, 5)
- **Border:** 1px, `#C8B432` (RGB: 200, 180, 50) @ 70% opacity

#### 2.3 Top2 (Silver)
- **Arkaplan Gradient:**
  - Top: `#323C3C` (RGB: 50, 50, 60)
  - Bottom: `#0F0F14` (RGB: 15, 15, 20)
- **Border:** 1px, `#96A0B4` (RGB: 150, 160, 180) @ 70% opacity

#### 2.4 Top3 (Bronze)
- **Arkaplan Gradient:**
  - Top: `#371E14` (RGB: 55, 30, 20)
  - Bottom: `#140A05` (RGB: 20, 10, 5)
- **Border:** 1px, `#B46432` (RGB: 180, 100, 50) @ 70% opacity

---

### Property 3: **HP_Level** (3 değer)

Bu property sadece HP Bar segmentlerinin görünürlüğünü kontrol eder:

- **Full:** 30/30 segment görünür
- **Half:** 15/30 segment görünür
- **Low:** 8/30 segment görünür

---

## 📦 İçerik Katmanları (Layers)

### Layer Hiyerarşisi
```
LobbyPanelRow (Component)
├─ Background (Gradient Fill)
├─ Border (Stroke)
├─ Hover Glow (Effect Layer - conditional)
├─ Rank Badge (Text)
├─ Player Name (Text)
├─ HP Number (Text)
├─ HP Bar Container (Frame)
│  ├─ Background (Dark fill)
│  └─ Segments (Auto Layout)
│     ├─ Segment 1 (Rectangle)
│     ├─ Segment 2 (Rectangle)
│     └─ ... (30 total)
├─ Category Strips (Frame - Auto Layout)
│  ├─ MYTHOLOGY Strip (Rectangle)
│  ├─ ART Strip (Rectangle)
│  └─ ... (dynamic)
└─ Eliminated Overlay (conditional)
   └─ "ELIMINATED" Text
```

---

## 📝 Text Layers

### 1. Rank Badge
```
Position: X: 8px, Y: 12px
Size: 24px × 20px
Font: Inter Bold (veya SF Pro Bold)
Size: 10px
Color: #FFFFFF (default) / #FFD700 (rank 1)
Alignment: Center (horizontal & vertical)
Content: "#1", "#2", "#3", etc.
```

### 2. Player Name
```
Position: X: 40px, Y: 6px
Size: 120px × 18px
Font: Inter Bold
Size: 11px
Color: #DCE6FF (normal) / #00F2FF (self)
Alignment: Left
Content: "YOU", "Player Name", etc.
```

### 3. HP Number
```
Position: X: 120px (right-aligned), Y: 6px
Size: 30px × 16px
Font: JetBrains Mono (veya Roboto Mono)
Size: 9px
Color: #FFFFFF
Alignment: Right
Content: "150", "75", "0", etc.
```

### 4. Eliminated Text (Conditional)
```
Position: Center of frame
Font: Inter Bold
Size: 12px
Color: #FF3C3C
Alignment: Center (horizontal & vertical)
Content: "ELIMINATED"
```

---

## 🩹 HP Bar (Segmented Health Bar)

### Container Frame
```
Position: X: 40px, Y: 26px
Size: 110px × 7px
Fill: #0F141E (dark background)
Border Radius: 2px
Auto Layout: Horizontal
Gap: 1px
Padding: 0px
```

### Segment Specifications
```
Total Segments: 30
Segment Size: 3.5px × 7px (width auto-calculated)
Gap Between: 1px
Border Radius: 1px
Fill Color: 
  - #00FF78 (HP > 40%)
  - #FF3C3C (HP ≤ 40%)
```

### Segment Grouping (Visual Hint)
Her 5 segmentte bir 2px gap ekleyerek bloklar oluşturun:
```
[■■■■■] [■■■■■] [■■■■■] [■■■■■] [■■■■■] [■■■■■]
  5       10      15      20      25      30
```

**Figma'da Uygulama:**
1. Auto Layout frame oluştur (horizontal, gap: 1px)
2. 30 adet rectangle ekle (3.5×7px)
3. Her 5. segmentten sonra 1px extra spacing ekle (Auto Layout spacing override)

---

## 🎨 Category Strips (Kategori Göstergeleri)

### Container Frame
```
Position: X: 40px, Y: 36px (HP bar'ın 3px altı)
Size: 110px × 3px
Auto Layout: Horizontal
Gap: 2px
Padding: 0px
```

### Strip Specifications
```
Height: 3px (sabit)
Width: Dinamik (orantılı)
Border Radius: 1px
Fill: Category color (yukarıdaki renk paletinden)
```

### Genişlik Hesaplama
Her kategori strip'inin genişliği, o kategorideki kart sayısına göre orantılıdır:

**Örnek:**
- MYTHOLOGY: 10 kart → 40% genişlik → 44px
- ART: 5 kart → 20% genişlik → 22px
- NATURE: 10 kart → 40% genişlik → 44px
- **Total:** 25 kart → 110px (gap'ler hariç)

**Figma'da Uygulama:**
1. Auto Layout frame (horizontal, gap: 2px)
2. Her kategori için rectangle ekle
3. Width'i manuel ayarla veya Figma plugin kullan

---

## 🎭 Interaction States

### Hover Behavior
```
Trigger: Mouse over
Effect:
  1. Scale frame to 103%
  2. Add inner glow (#00C8FF @ 30%)
  3. Smooth transition (200ms ease-out)
```

### Click Behavior
```
Trigger: Mouse click
Action: Select player (highlight border)
Visual: Border color changes to #00FFFF (2px)
```

### Low HP Pulse (Animasyon)
```
Condition: HP < 30% AND HP > 0
Effect: HP bar outer glow pulses
Color: #FF3232
Opacity: 40% → 80% → 40% (loop)
Duration: 1.5s per cycle
```

**Not:** Figma'da animasyon için prototype veya plugin kullanın.

---

## 📏 Spacing & Layout

### Vertical Spacing (8 oyuncu için)
```
Row Height: 80px
Gap Between Rows: 8px
Total Height: (80 × 8) + (8 × 7) = 696px
Vertical Centering: (Screen Height - 696px) / 2
```

### Horizontal Margins
```
Sidebar Width: 180px
Margin Left/Right: 10px
Row Width: 160px
```

---

## 🔧 Figma Best Practices

### 1. Component Organization
```
📁 Lobby Panel
  ├─ 🎨 Color Styles
  │  ├─ Category/MYTHOLOGY
  │  ├─ Category/ART
  │  └─ ...
  ├─ 📝 Text Styles
  │  ├─ Rank Badge
  │  ├─ Player Name
  │  └─ HP Number
  └─ 🧩 Components
     ├─ LobbyPanelRow (Master)
     ├─ HP Bar Segment
     └─ Category Strip
```

### 2. Naming Convention
```
Component: LobbyPanelRow
Variants: State=Normal, Rank=Default, HP=Full
Instance: LobbyPanelRow/Normal/Default/Full
```

### 3. Auto Layout Kullanımı
- HP Bar: Horizontal Auto Layout (gap: 1px)
- Category Strips: Horizontal Auto Layout (gap: 2px)
- Segment grouping için spacing override kullanın

### 4. Responsive Considerations
- Width: Fixed (160px)
- Height: Fixed (80px)
- Scale: Hover'da 103% (transform origin: center)

---

## 🧪 Test Scenarios

Aşağıdaki varyant kombinasyonlarını test edin:

| # | State | Rank | HP Level | Beklenen Görünüm |
|---|-------|------|----------|------------------|
| 1 | Normal | Default | Full | Standart gri gradient, 30 yeşil segment |
| 2 | Hover | Default | Full | 103% scale, cyan glow |
| 3 | Self | Default | Half | Mavi gradient, cyan border, 15 segment |
| 4 | Normal | Top1 | Full | Gold gradient, gold border |
| 5 | Normal | Top2 | Half | Silver gradient, 15 segment |
| 6 | Normal | Top3 | Low | Bronze gradient, 8 kırmızı segment |
| 7 | Eliminated | Default | Low | Kırmızı overlay, "ELIMINATED" text |
| 8 | Self | Top1 | Full | Gold + cyan border (2 border layer) |

---

## 📸 Reference Screenshots

Koddan çıkarılan görsel referanslar:

### Normal State
```
┌─────────────────────────────────────┐
│ #1  Player Name              150    │
│     ████████████████████████████    │ ← HP Bar (30 segments)
│     ████▓▓▓▓░░░░                    │ ← Category strips
└─────────────────────────────────────┘
```

### Hover State
```
┌─────────────────────────────────────┐ ← 103% scale
│ #1  Player Name              150  ◄─┼─ Cyan glow
│     ████████████████████████████    │
│     ████▓▓▓▓░░░░                    │
└─────────────────────────────────────┘
```

### Self State
```
┌═════════════════════════════════════┐ ← Cyan border (2px)
║ #1  YOU                      150    ║
║     ████████████████████████████    ║
║     ████▓▓▓▓░░░░                    ║
└═════════════════════════════════════┘
```

### Eliminated State
```
┌─────────────────────────────────────┐
│                                     │
│         🔴 ELIMINATED 🔴            │ ← Red overlay
│                                     │
└─────────────────────────────────────┘
```

---

## 🚀 Implementation Checklist

- [ ] Renk stillerini oluştur (6 kategori + sistem renkleri)
- [ ] Text stillerini oluştur (3 tip: rank, name, hp)
- [ ] Ana component frame'i oluştur (160×80px)
- [ ] Arkaplan gradientlerini ayarla (5 varyant)
- [ ] Border stillerini ekle (normal, self, top1-3)
- [ ] Rank badge text layer'ı ekle
- [ ] Player name text layer'ı ekle
- [ ] HP number text layer'ı ekle
- [ ] HP bar container + 30 segment oluştur
- [ ] Category strips container + dinamik strips ekle
- [ ] Eliminated overlay + text ekle
- [ ] Component variants oluştur (State × Rank × HP)
- [ ] Hover efektini prototype'a ekle
- [ ] Test senaryolarını kontrol et

---

## 📞 İletişim

**Sorular için:**
- Kod: `v2/ui/lobby_panel.py`
- Tasarımcı: Özhan Bagırgan
- Email: doflamino@gmail.com

**Versiyon:** 1.0  
**Son Güncelleme:** 23 Nisan 2026

---

## 🎯 Sonuç

Bu spec dokümanı, `lobby_panel.py` kodunun Figma'da birebir karşılığını oluşturmak için gereken tüm detayları içerir. Tüm renkler, boyutlar, spacing değerleri ve interaction state'leri koddan çıkarılmıştır.

**Önemli Notlar:**
1. Gradient değerleri RGB formatında verilmiştir, Figma'da hex'e çevirirken dikkat edin
2. HP bar segmentleri için Auto Layout kullanımı önerilir
3. Category strips dinamik genişlikte olmalı (orantılı)
4. Hover animasyonu için Figma prototype veya plugin gereklidir
5. Low HP pulse efekti için After Effects veya Lottie entegrasyonu düşünülebilir

**Başarılar!** 🎨✨
