# 🔤 Lobi Ekranı - Font Güncellemesi

## 🔄 Değişiklikler (v1.4)

### **1. Başlık Metni: "LOBİ" → "LOBBY"** ✅

**Önceki:**
```
LOBİ
```

**Yeni:**
```
LOBBY
```

**Sebep:** İngilizce daha evrensel ve profesyonel

### **2. Font Değişiklikleri** ✅

| Element | Önceki Font | Yeni Font | Boyut Değişimi |
|---------|-------------|-----------|----------------|
| **Başlık (LOBBY)** | BitcountGridDoubleInk | BitcountGridDoubleInk | 48pt (aynı) |
| **Alt Başlık** | BitcountGridDoubleInk 18pt | broken-strings.regular | 18pt → 16pt |
| **AI Satırları** | BitcountGridDoubleInk 28pt | broken-strings.regular | 28pt → 24pt |
| **Human Satırı** | BitcountGridDoubleInk 28pt | broken-strings.regular | 28pt → 24pt |
| **Dropdown Items** | BitcountGridDoubleInk 22pt | broken-strings.regular | 22pt → 20pt |
| **Alt Bilgi** | BitcountGridDoubleInk 14pt | broken-strings.regular | 14pt → 13pt |
| **Start Butonu** | minimap_category_names | minimap_category_names | 32pt (aynı) |

### **3. Font Kullanım Stratejisi** ✅

**BitcountGridDoubleInk (Kalın, Vurgulu):**
- ✅ Başlık: "LOBBY"
- ✅ Kullanım: Sadece ana başlık

**broken-strings.regular (Şık, Okunabilir):**
- ✅ Alt başlık: "8 Players • 7 AI Strategies"
- ✅ AI satırları: "AI 1 — WARRIOR"
- ✅ Human satırı: "► SEN — HUMAN"
- ✅ Dropdown items: Strateji listesi
- ✅ Alt bilgi: "Click OYUNA BAŞLA to initialize..."

**minimap_category_names (Buton):**
- ✅ Start butonu: "OYUNA BAŞLA"
- ✅ Kullanım: Sadece buton metni

## 🎨 Görsel Karşılaştırma

### **Önceki (BitcountGridDoubleInk Her Yerde):**
```
╔════════════════════════════╗
║ LOBİ                       ║  ← BitcountGridDoubleInk (kalın)
║ 8 Players • 7 AI Strategies║  ← BitcountGridDoubleInk (kalın)
╠════════════════════════════╣
║ AI 1 — WARRIOR          ●  ║  ← BitcountGridDoubleInk (kalın)
║ AI 2 — BUILDER          ●  ║  ← BitcountGridDoubleInk (kalın)
╚════════════════════════════╝
```

### **Yeni (broken-strings.regular Satırlar):**
```
╔════════════════════════════╗
║ LOBBY                      ║  ← BitcountGridDoubleInk (kalın)
║ 8 Players • 7 AI Strategies║  ← broken-strings.regular (şık)
╠════════════════════════════╣
║ AI 1 — WARRIOR          ●  ║  ← broken-strings.regular (şık)
║ AI 2 — BUILDER          ●  ║  ← broken-strings.regular (şık)
╚════════════════════════════╝
```

## 🎯 Tasarım Felsefesi

### **Neden broken-strings.regular?**

1. **Okunabilirlik** ✅
   - BitcountGridDoubleInk çok kalın ve vurgulu
   - broken-strings daha şık ve okunabilir
   - Uzun metinler için daha uygun

2. **Hiyerarşi** ✅
   - Başlık: Kalın ve vurgulu (BitcountGridDoubleInk)
   - İçerik: Şık ve okunabilir (broken-strings)
   - Buton: Özel font (minimap_category_names)

3. **Görsel Denge** ✅
   - Başlık dikkat çeker (kalın)
   - Satırlar rahat okunur (şık)
   - Buton öne çıkar (özel)

4. **Profesyonellik** ✅
   - Font çeşitliliği profesyonel görünüm
   - Her element kendi karakterini korur
   - Tutarlı ama monoton değil

### **Font Boyutu Ayarlamaları**

**Neden Küçültüldü?**
- broken-strings.regular BitcountGridDoubleInk'ten daha geniş
- Aynı boyutta daha fazla yer kaplar
- 2-4pt küçültme daha dengeli görünüm sağlar

**Boyut Tablosu:**
```
BitcountGridDoubleInk 28pt ≈ broken-strings.regular 24pt
BitcountGridDoubleInk 22pt ≈ broken-strings.regular 20pt
BitcountGridDoubleInk 18pt ≈ broken-strings.regular 16pt
BitcountGridDoubleInk 14pt ≈ broken-strings.regular 13pt
```

## 🔧 Teknik Detaylar

### **Font Yükleme:**
```python
def _init_fonts(self) -> None:
    font_dir = Path("v2/assets/fonts")
    
    # Başlık (kalın, vurgulu)
    self._font_title = pygame.font.Font(
        str(font_dir / "BitcountGridDoubleInk.ttf"), 48
    )
    
    # Satırlar (şık, okunabilir)
    self._font_row = pygame.font.Font(
        str(font_dir / "broken-strings.regular.ttf"), 24
    )
    
    # Buton (özel)
    self._font_button = pygame.font.Font(
        str(font_dir / "minimap_category_names.ttf"), 32
    )
    
    # Dropdown (şık, küçük)
    self._font_dropdown = pygame.font.Font(
        str(font_dir / "broken-strings.regular.ttf"), 20
    )
```

### **Font Kullanım Yerleri:**

**self._font_title (BitcountGridDoubleInk 48pt):**
- Başlık: "LOBBY"

**self._font_row (broken-strings.regular 24pt):**
- AI numaraları: "AI 1", "AI 2", ...
- Ayırıcılar: "—"
- Strateji adları: "WARRIOR", "BUILDER", ...
- Human satırı: "►", "SEN", "HUMAN"

**self._font_button (minimap_category_names 32pt):**
- Start butonu: "OYUNA BAŞLA"

**self._font_dropdown (broken-strings.regular 20pt):**
- Dropdown items: Strateji listesi
- Checkmark: "✓"

**Dinamik fontlar (broken-strings.regular):**
- Alt başlık: 16pt
- Alt bilgi: 13pt

## 📊 Font Karşılaştırması

### **BitcountGridDoubleInk:**
```
ABCDEFGHIJKLMNOPQRSTUVWXYZ
0123456789
Kalın, Vurgulu, Dikkat Çekici
```

### **broken-strings.regular:**
```
ABCDEFGHIJKLMNOPQRSTUVWXYZ
0123456789
Şık, Okunabilir, Modern
```

### **minimap_category_names:**
```
ABCDEFGHIJKLMNOPQRSTUVWXYZ
0123456789
Özel, Buton İçin Optimize
```

## 🎨 Görsel Hiyerarşi

```
┌─────────────────────────────────┐
│                                 │
│  LOBBY  ← BitcountGridDoubleInk │  En Büyük, En Vurgulu
│  (48pt, Kalın)                  │
│                                 │
│  8 Players • 7 AI Strategies    │  Orta, Şık
│  ← broken-strings.regular       │
│  (16pt)                         │
│                                 │
├─────────────────────────────────┤
│                                 │
│  AI 1 — WARRIOR              ●  │  Orta, Okunabilir
│  ← broken-strings.regular       │
│  (24pt)                         │
│                                 │
│  ► SEN — HUMAN                  │  Orta, Vurgulu
│  ← broken-strings.regular       │
│  (24pt)                         │
│                                 │
├─────────────────────────────────┤
│                                 │
│  ┌─────────────────────┐        │
│  │  OYUNA BAŞLA        │        │  Büyük, Özel
│  │  ← minimap_category │        │
│  │  (32pt)             │        │
│  └─────────────────────┘        │
│                                 │
│  Click OYUNA BAŞLA to...        │  Küçük, Detay
│  ← broken-strings.regular       │
│  (13pt)                         │
│                                 │
└─────────────────────────────────┘
```

## 📝 Sonuç

Font güncellemesi tamamlandı:
- ✅ Başlık: "LOBİ" → "LOBBY" (İngilizce)
- ✅ Satırlar: BitcountGridDoubleInk → broken-strings.regular
- ✅ Dropdown: BitcountGridDoubleInk → broken-strings.regular
- ✅ Alt başlık: BitcountGridDoubleInk → broken-strings.regular
- ✅ Alt bilgi: BitcountGridDoubleInk → broken-strings.regular
- ✅ Başlık ve buton: Aynı kaldı (vurgu için)

**Sonuç:** Daha okunabilir, daha şık, daha profesyonel! 🔤

---

**Güncelleme:** 2026-04-30
**Versiyon:** 1.4 (Font Update)
**Durum:** ✅ Tamamlandı ve Test Edildi
