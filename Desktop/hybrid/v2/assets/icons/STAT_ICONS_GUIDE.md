# Stat İkonları Rehberi

## 📊 12 Stat İkonu

Oyunda kullanılan 12 stat için PNG ikonlar:

### EXISTENCE Grubu (Kırmızı Tonlar)

1. **Power (Güç)** - `stat_power.png`
   - Font Awesome: FIST (Yumruk)
   - Renk: Kırmızı tonları
   - Açıklama: Fiziksel güç, saldırı gücü

2. **Durability (Dayanıklılık)** - `stat_durability.png`
   - Font Awesome: SHIELD (Kalkan)
   - Renk: Kırmızı tonları
   - Açıklama: Savunma, dayanıklılık

3. **Size (Boyut)** - `stat_size.png`
   - Font Awesome: EXPAND (Genişleme)
   - Renk: Kırmızı tonları
   - Açıklama: Fiziksel boyut, alan kontrolü

4. **Speed (Hız)** - `stat_speed.png`
   - Font Awesome: BOLT (Şimşek)
   - Renk: Kırmızı tonları
   - Açıklama: Hareket hızı, çeviklik

### MIND Grubu (Mavi Tonlar)

5. **Meaning (Anlam)** - `stat_meaning.png`
   - Font Awesome: BOOK (Kitap)
   - Renk: Mavi tonları
   - Açıklama: Anlam, bilgi derinliği

6. **Secret (Sır)** - `stat_secret.png`
   - Font Awesome: LOCK (Kilit)
   - Renk: Mavi tonları
   - Açıklama: Gizli bilgi, sır

7. **Intelligence (Zeka)** - `stat_intelligence.png`
   - Font Awesome: GEAR (Dişli)
   - Renk: Mavi tonları
   - Açıklama: Zeka, strateji

8. **Trace (İz)** - `stat_trace.png`
   - Font Awesome: FOOTPRINT (Ayak izi)
   - Renk: Mavi tonları
   - Açıklama: İz sürme, takip

### CONNECTION Grubu (Yeşil Tonlar)

9. **Gravity (Çekim)** - `stat_gravity.png`
   - Font Awesome: MAGNET (Mıknatıs)
   - Renk: Yeşil tonları
   - Açıklama: Çekim gücü, etki alanı

10. **Harmony (Uyum)** - `stat_harmony.png`
    - Font Awesome: MUSIC (Müzik notu)
    - Renk: Yeşil tonları
    - Açıklama: Uyum, sinerji

11. **Spread (Yayılma)** - `stat_spread.png`
    - Font Awesome: BROADCAST (Yayın)
    - Renk: Yeşil tonları
    - Açıklama: Yayılma, etki genişliği

12. **Prestige (Prestij)** - `stat_prestige.png`
    - Font Awesome: GEM (Mücevher)
    - Renk: Yeşil tonları
    - Açıklama: Prestij, değer

## 🎨 Tasarım Önerileri

### Stil

- **Tutarlı stil:** Tüm ikonlar aynı çizim stilinde olmalı
- **Basit ve net:** 24px boyutunda bile anlaşılır olmalı
- **Sembolik:** Stat'ın anlamını temsil etmeli

### Renk

- **Şeffaf arka plan:** PNG alpha channel kullanın
- **Tek renk veya tam renkli:** İkisi de çalışır
- **Kod içinde renklendirme:** Sistem otomatik renk uygulayabilir

### Boyut

- **Kaynak:** 512x512 piksel (önerilen)
- **Minimum:** 64x64 piksel
- **Kullanım:** 22-24px (otomatik ölçeklenir)

## 📁 Dosya Adları

```
v2/assets/icons/
├── stat_power.png       ✓ Power
├── stat_durability.png  ✓ Durability
├── stat_size.png        ✓ Size
├── stat_speed.png       ✓ Speed
├── stat_meaning.png     ✓ Meaning
├── stat_secret.png      ✓ Secret
├── stat_intelligence.png ✓ Intelligence
├── stat_trace.png       ✓ Trace
├── stat_gravity.png     ✓ Gravity
├── stat_harmony.png     ✓ Harmony
├── stat_spread.png      ✓ Spread
└── stat_prestige.png    ✓ Prestige
```

## 🔧 Kod Entegrasyonu

Kod zaten hazır! İkonları ekledikten sonra otomatik çalışacak:

```python
# v2/ui/icon_loader.py içinde tanımlı:
GENERAL_ICONS = {
    "FIST": "stat_power.png",
    "SHIELD": "stat_durability.png",
    "EXPAND": "stat_size.png",
    "BOLT": "stat_speed.png",
    "BOOK": "stat_meaning.png",
    "LOCK": "stat_secret.png",
    "GEAR": "stat_intelligence.png",
    "FOOTPRINT": "stat_trace.png",
    "MAGNET": "stat_gravity.png",
    "MUSIC": "stat_harmony.png",
    "BROADCAST": "stat_spread.png",
    "GEM": "stat_prestige.png",
}
```

## 🎯 Öncelik Sırası

Eğer tüm ikonları birden hazırlamak zor geliyorsa, öncelik sırası:

### Yüksek Öncelik (En çok kullanılan)

1. **Power** - En temel stat
2. **Durability** - Savunma
3. **Intelligence** - Zeka
4. **Speed** - Hız

### Orta Öncelik

5. **Gravity** - Çekim
6. **Harmony** - Uyum
7. **Spread** - Yayılma
8. **Meaning** - Anlam

### Düşük Öncelik

9. **Size** - Boyut
10. **Secret** - Sır
11. **Trace** - İz
12. **Prestige** - Prestij

## 🧪 Test

İkonları ekledikten sonra test edin:

```bash
# Hızlı kontrol
python quick_icon_test.py

# Görsel test
python test_png_icons.py

# Oyunda test
python v2/main.py
```

## 💡 İpuçları

1. **Batch işlem:** Tüm ikonları aynı anda hazırlayın
2. **Tutarlılık:** Aynı çizgi kalınlığı ve stil kullanın
3. **Kontrast:** Arka plandan ayrılmalı
4. **Test:** Her ikonu 24px boyutunda test edin

## 🎨 Örnek İkon Fikirleri

### Power (Güç)

- Yumruk
- Kas
- Patlama
- Enerji dalgası

### Durability (Dayanıklılık)

- Kalkan
- Zırh
- Kale
- Duvar

### Intelligence (Zeka)

- Beyin
- Ampul
- Dişli
- Devre

### Gravity (Çekim)

- Mıknatıs
- Kara delik
- Çekim alanı
- Gezegen

## 📝 Notlar

- Eksik ikonlar için Font Awesome fallback var
- Oyun çökmez, eski ikonları gösterir
- İkonları istediğiniz sırayla ekleyebilirsiniz
- Her ikon bağımsız çalışır
