# Pasif Açıklama Font Güncellemesi

## Özet

Kart hover info box'ındaki pasif açıklamalar için **Philosopher-Italic** fontu uygulandı ve punto/satır aralığı optimize edildi.

## Yapılan Değişiklikler

### 1. Typography Constants (`v2/constants.py`)

- Yeni font tanımı eklendi: `FONT_PASSIVE_DESC = "Philosopher-Italic.ttf"`
- Bu font, pasif açıklamaların daha zarif ve okunabilir görünmesi için özel olarak seçildi

### 2. Font Cache (`v2/ui/font_cache.py`)

- Yeni font fonksiyonu eklendi: `passive_description(size: int)`
- Bu fonksiyon, Philosopher-Italic fontunu yükler ve cache'ler

### 3. InfoBox Render (`v2/ui/info_box_new1.py`)

Pasif açıklama render kodunda şu optimizasyonlar yapıldı:

#### Font Değişikliği

- **Önceki:** `font_cache.stat_passive()` (99_percent_OCCUPY.ttf)
- **Yeni:** `font_cache.passive_description()` (Philosopher-Italic.ttf)

#### Punto Boyutu

- **Önceki:** `max(15, int(17 * s))` piksel
- **Yeni:** `max(16, int(18 * s))` piksel
- Philosopher-Italic'in karakteristik yapısı için optimize edildi

#### Satır Aralığı (Line Gap)

- **Önceki:** `max(13 * s, int(14 * s))` piksel
- **Yeni:** `max(15 * s, int(17 * s))` piksel
- Daha geniş aralık, italic fontun okunabilirliğini artırır

#### Label-Açıklama Arası Boşluk

- **Önceki:** `int(1.5 * s)` piksel
- **Yeni:** `int(2 * s)` piksel
- Pasif label ile açıklama metni arasında daha net ayrım

#### Metin Rengi

- **Önceki:** `(228, 230, 242)` RGB
- **Yeni:** `(235, 237, 248)` RGB
- Hafif daha parlak renk, Philosopher-Italic'in zarafetini vurgular

## Görsel İyileştirmeler

### Okunabilirlik

- Philosopher-Italic'in karakteristik eğik yapısı, pasif açıklamaları daha zarif gösterir
- Artırılmış satır aralığı, uzun açıklamaların daha rahat okunmasını sağlar
- Optimize edilmiş punto boyutu, hem küçük hem büyük ekranlarda net görünüm sunar

### Estetik

- Italic font, pasif açıklamalara "açıklayıcı not" karakteri katar
- Stat değerleri (99_percent_OCCUPY) ile pasif açıklamalar (Philosopher-Italic) arasında net tipografik hiyerarşi
- Daha parlak renk, info box'ın karanlık arka planında daha iyi kontrast sağlar

## Teknik Detaylar

### Render Scale Desteği

Tüm boyut değerleri `s` (render scale) parametresi ile çarpılır:

- `s = 1` → Normal çözünürlük
- `s = 2` → 2x yüksek çözünürlük (varsayılan)
- Bu sayede farklı ekran boyutlarında tutarlı görünüm

### Wrap Text Uyumluluğu

`_wrap_text()` fonksiyonu, Philosopher-Italic'in karakter genişliklerini doğru hesaplar:

- Font değişikliği, mevcut wrap algoritmasıyla tam uyumlu
- Uzun kelimeler otomatik olarak yeni satıra geçer
- Maksimum satır sayısı korunur (6 veya 4, yüksekliğe göre)

## Test Sonuçları

```
tests/test_info_box.py::test_wrap_text_splits_long_text_to_fit_max_width PASSED
tests/test_info_box.py::test_infobox_render_handles_independent_card_without_synergy_group PASSED
tests/test_info_box.py::test_stat_color_varies_by_group_and_value_threshold PASSED
```

Tüm testler başarıyla geçti ✓

## Kullanım

Değişiklikler otomatik olarak aktif. Oyunu başlattığınızda:

1. Shop veya Hand panelinde bir kartın üzerine gelin (hover)
2. Info box açılacak
3. Pasif açıklamalar artık Philosopher-Italic fontuyla görünecek

## Notlar

- Font dosyası zaten mevcuttu: `v2/assets/fonts/Philosopher-Italic.ttf`
- Geriye dönük uyumluluk korundu (eski kod çalışmaya devam eder)
- Performans etkisi minimal (font cache kullanımı sayesinde)
