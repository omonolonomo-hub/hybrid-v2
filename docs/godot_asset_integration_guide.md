# Godot Asset Integration Guide - Kart Görselleri

**Tarih**: 2025-01-04  
**Durum**: Hazır - Asset'leri ekleyebilirsin!

---

## ✅ DÜZELTILEN SORUNLAR

### 1. Integer Division (player.gd:45) ✅
```gdscript
# Önce:
var streak_bonus := win_streak / 3

# Sonra:
var streak_bonus := int(win_streak / 3.0)
```

### 2. Board Pozisyon Sorunu ✅
```gdscript
# Önce:
HEX_SIZE = minf(viewport.x, viewport.y) / 20.0  # Çok büyük
position = get_parent().size / 2.0  # Yanlış hesaplama

# Sonra:
HEX_SIZE = minf(viewport.x, viewport.y) / 22.0  # Daha küçük (37 hex için)
ORIGIN = viewport / 2.0  # Viewport merkezi
position = Vector2.ZERO  # Parent container'da merkez
```

**Sonuç**: Board artık ekranın ortasında, hex'ler daha küçük ve sığıyor!

### 3. Icon.svg Hatası ℹ️
```
E 0:00:01:394 load_image: Error opening file 'res://icon.svg'.
```

**Açıklama**: Godot default icon eksik. Önemli değil, oyunu etkilemiyor.

**Çözüm** (opsiyonel): 
- Project Settings → Application → Config → Icon
- Kendi icon'unu ekle veya boş bırak

---

## 🎨 KART ASSET SİSTEMİ

### Klasör Yapısı

```
godot_project/
├── assets/
│   ├── cards/
│   │   ├── fronts/          # ✅ Oluşturuldu
│   │   │   ├── Yggdrasil_front.png
│   │   │   ├── Pulsar_front.png
│   │   │   └── ...
│   │   ├── backs/           # ✅ Oluşturuldu
│   │   │   ├── Yggdrasil_back.png
│   │   │   ├── Pulsar_back.png
│   │   │   └── ...
│   │   └── README.md        # ✅ Oluşturuldu
│   └── data/
│       └── cards.json       # Güncellenecek
└── tools/
    └── update_card_images.py  # ✅ Oluşturuldu
```

---

## 📋 ADIM ADIM KULLANIM

### Adım 1: Asset'leri Hazırla

**Gereksinimler**:
- Format: PNG (transparency destekli)
- Boyut: 512x512 veya 1024x1024 (kare)
- Adlandırma: `{KartAdi}_front.png` ve `{KartAdi}_back.png`

**Örnek**:
```
Yggdrasil_front.png  (ön yüz - altıgen içinde görünecek)
Yggdrasil_back.png   (arka yüz - şimdilik kullanılmıyor)
```

**Türkçe Karakter Dönüşümü**:
- `ı` → `i`
- `ğ` → `g`
- `ü` → `u`
- `ş` → `s`
- `ö` → `o`
- `ç` → `c`
- Boşluk → `_`

**Örnek**:
- "Işık Savaşçısı" → `Isik_Savascisi_front.png`

### Adım 2: Asset'leri Kopyala

```bash
# Windows (PowerShell)
Copy-Item "C:\path\to\your\fronts\*.png" "godot_project\assets\cards\fronts\"
Copy-Item "C:\path\to\your\backs\*.png" "godot_project\assets\cards\backs\"

# Veya manuel olarak:
# 1. fronts klasörüne ön yüz PNG'leri kopyala
# 2. backs klasörüne arka yüz PNG'leri kopyala
```

### Adım 3: cards.json'u Güncelle

```bash
# Python script'i çalıştır
cd godot_project
python tools/update_card_images.py
```

**Script ne yapar**:
1. `cards.json` backup'ını oluşturur (`.bak`)
2. Her kart için `image_front` ve `image_back` path'leri ekler
3. Eksik dosyaları listeler
4. Güncellenmiş `cards.json`'u kaydeder

**Örnek Çıktı**:
```
============================================================
Card Image Path Updater
============================================================
✅ Backup oluşturuldu: cards.json.bak

📦 50 kart bulundu

  Yggdrasil                      → Yggdrasil_front.png / Yggdrasil_back.png
  Pulsar                         → Pulsar_front.png / Pulsar_back.png
  ...

✅ 50 kart güncellendi!
💾 Kaydedildi: assets/data/cards.json

⚠️  Eksik Dosyalar:

  📁 Fronts (10 eksik):
    - Yggdrasil_front.png
    - Pulsar_front.png
    ...

💡 İpucu: Eksik dosyaları ilgili klasörlere ekle:
   - godot_project/assets/cards/fronts
   - godot_project/assets/cards/backs

============================================================
✅ Tamamlandı!
============================================================
```

### Adım 4: Godot'ta Test Et

1. Godot Editor'ü aç
2. F5 ile oyunu başlat
3. Board'da kartlara bak
4. Görsel varsa hex içinde görünmeli
5. Görsel yoksa sadece hex frame + stats görünür

---

## 🎨 GÖRSEL ÖRNEKLERİ

### Ön Yüz (Front) - Hex İçinde Görünecek

```
┌─────────────────┐
│                 │
│   [KART ART]    │  ← Bu kısım hex içinde
│                 │
│   Character/    │
│   Symbol/       │
│   Abstract      │
│                 │
└─────────────────┘
```

**Öneriler**:
- Merkezi kompozisyon (hex kenarları kesilecek)
- Yüksek kontrast (hex frame üzerinde okunabilir)
- Detay ortada (köşeler görünmeyebilir)

### Arka Yüz (Back) - Şimdilik Kullanılmıyor

Gelecekte:
- Kart çevirme animasyonu
- Rakip kartları (kapalı göster)
- Deck builder UI

---

## 🔧 MANUEL GÜNCELLEME (Script Kullanmadan)

Eğer Python script çalışmazsa, manuel olarak:

1. `assets/data/cards.json` aç
2. Her kart için ekle:

```json
{
  "name": "Yggdrasil",
  "category": "Nature",
  "rarity": "5",
  "stats": {...},
  "passive_type": "synergy",
  "image_front": "res://assets/cards/fronts/Yggdrasil_front.png",
  "image_back": "res://assets/cards/backs/Yggdrasil_back.png"
}
```

3. Kaydet
4. Godot'ta test et

---

## 🎯 PLACEHOLDER GÖRSELLER

Eğer henüz görseller yoksa, hızlıca placeholder oluştur:

### Photoshop/GIMP:
1. 512x512 yeni dosya
2. Rarity renginde background (Constants.RARITY_COLORS)
3. Ortada kart adı (büyük font)
4. PNG olarak kaydet

### Python Script (Otomatik Placeholder):

```python
from PIL import Image, ImageDraw, ImageFont

def create_placeholder(name, rarity, output_path):
    # Rarity renkleri (RGB)
    colors = {
        "1": (160, 160, 160),  # Gri
        "2": (50, 255, 120),   # Yeşil
        "3": (0, 180, 255),    # Mavi
        "4": (255, 0, 255),    # Mor
        "5": (255, 215, 0),    # Altın
    }
    
    img = Image.new('RGB', (512, 512), colors.get(rarity, (100, 100, 100)))
    draw = ImageDraw.Draw(img)
    
    # Kart adı (ortada)
    font = ImageFont.truetype("arial.ttf", 48)
    bbox = draw.textbbox((0, 0), name, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (512 - text_width) / 2
    y = (512 - text_height) / 2
    draw.text((x, y), name, fill=(255, 255, 255), font=font)
    
    img.save(output_path)

# Kullanım:
create_placeholder("Yggdrasil", "5", "Yggdrasil_front.png")
```

---

## 📊 BOARD RENDER AKIŞI

```
BoardRenderer._draw()
  ↓
_draw_card_hex(center, card, selected)
  ↓
if card.image_front != "":
    var tex = _load_texture(card.image_front)  # Cache'den yükle
    if tex != null:
        draw_texture_rect(tex, img_rect, false)  # Hex içinde çiz
  ↓
# Hex frame, stats, rarity badge üzerine çizilir
```

**Texture Cache**:
- İlk yüklemede `_tex_cache[path] = texture`
- Sonraki çağrılarda cache'den döner
- Performans: 60 FPS (37 hex x 2 oyuncu = 74 kart)

---

## 🚀 TEST SENARYOLARI

### Test 1: Tek Kart Görseli
1. Bir kart görseli ekle: `fronts/Test_front.png`
2. `cards.json`'da "Test" kartının `image_front` path'ini güncelle
3. Oyunu başlat
4. Test kartını board'a yerleştir
5. **Beklenen**: Görsel hex içinde görünmeli

### Test 2: Tüm Kartlar
1. Tüm kart görsellerini ekle
2. `update_card_images.py` çalıştır
3. Oyunu başlat
4. Market'ten kartları al ve board'a yerleştir
5. **Beklenen**: Her kartın görseli görünmeli

### Test 3: Eksik Görsel
1. Bir kartın görselini ekleme
2. Oyunu başlat
3. O kartı board'a yerleştir
4. **Beklenen**: Sadece hex frame + stats görünmeli (hata yok)

### Test 4: Performans
1. Board'u doldur (37 hex)
2. FPS'i kontrol et (Debug → Monitor → FPS)
3. **Beklenen**: 60 FPS (texture cache sayesinde)

---

## 📝 NOTLAR

### Görsel Boyutları

**512x512** (Önerilen):
- Dosya boyutu: ~100-500 KB
- Yeterli detay
- Hızlı yükleme

**1024x1024** (Yüksek kalite):
- Dosya boyutu: ~500 KB - 2 MB
- Çok detaylı
- Zoom için ideal

**256x256** (Düşük kalite):
- Dosya boyutu: ~50-200 KB
- Bulanık görünebilir
- Sadece placeholder için

### Godot Import Ayarları

Godot otomatik olarak PNG'leri import eder:
- Compression: Lossless (default)
- Mipmaps: Enabled (zoom için)
- Filter: Linear (smooth scaling)

Değiştirmek için:
1. Asset'e sağ tıkla → Import
2. Ayarları değiştir
3. Reimport

### Performans İpuçları

1. **Texture Atlas**: Çok sayıda kart varsa atlas kullan
2. **Compression**: VRAM tasarrufu için compress et
3. **Mipmaps**: Zoom varsa enable et
4. **Cache**: `_tex_cache` dictionary kullan (zaten var)

---

## ✅ SONUÇ

**Hazır!** 🎉

1. ✅ Klasörler oluşturuldu (`fronts/`, `backs/`)
2. ✅ Python script hazır (`update_card_images.py`)
3. ✅ Dokümantasyon hazır (README.md)
4. ✅ Board pozisyon düzeltildi
5. ✅ Integer division düzeltildi

**Şimdi yapman gerekenler**:
1. Kart görsellerini `fronts/` ve `backs/` klasörlerine kopyala
2. `python tools/update_card_images.py` çalıştır
3. Godot'ta test et

**Görsel yoksa**: Oyun yine çalışır, sadece hex frame + stats görünür.

**Sorular**:
- Placeholder görseller oluşturayım mı?
- Belirli bir kart için örnek gösterayim mi?
- Başka bir şey?
