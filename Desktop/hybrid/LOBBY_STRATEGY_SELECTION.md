# 🎮 Lobi Ekranı - AI Strateji Seçimi

## ✨ Yeni Özellik

Lobi ekranında artık her AI oyuncusu için strateji seçimi yapabilirsiniz!

## 🐛 Düzeltilen Sorunlar (v1.2)

### **5. Satır Arka Plan Orantısı** ✅
- **Sorun:** Satır arka planındaki şerit orantısızdı, yazılar şeridin üstünde kalıyordu
- **Çözüm:** Sabit yükseklik ve ortalanmış pozisyon:
  - AI satırları: 40px yükseklik, yazılar ortada (Y - 4px)
  - Human satırı: 44px yükseklik, yazılar ortada (Y - 6px)

## 🐛 Düzeltilen Sorunlar (v1.1)

### **1. Dropdown Event Handling** ✅
- **Sorun:** Dropdown tıklarken altındaki AI'ın dropdown'u açılıyordu
- **Çözüm:** Event handling öncelik sırası düzeltildi (dropdown items → strategy buttons)

### **2. Render Sırası** ✅
- **Sorun:** Human satırı dropdown'ların üstüne çiziliyordu
- **Çözüm:** Dropdown render sırası en sona alındı (human row → dropdown)

### **3. Renk Çakışması** ✅
- **Sorun:** Strateji renkleri oyundaki synergy renkleriyle çakışıyordu
- **Çözüm:** Özel renk paleti oluşturuldu:
  - 🔴 **WARRIOR** - Parlak kırmızı (220, 60, 60)
  - 🟢 **BUILDER** - Açık yeşil (80, 180, 100)
  - 🟣 **EVOLVER** - Parlak mor (160, 90, 220)
  - 🟡 **ECONOMIST** - Parlak altın (255, 200, 50)
  - 🔵 **BALANCER** - Açık mavi (100, 150, 255)
  - 💜 **RARE_HUNTER** - Açık mor/pembe (200, 160, 255)
  - ⚫ **RANDOM** - Açık gri (140, 140, 140)

### **4. Layout Orantısı** ✅
- **Sorun:** Satır başlıklarındaki yazı yerleşimi orantısızdı
- **Çözüm:** Sabit piksel pozisyonları kullanıldı:
  - AI numarası: `x + 20`
  - Ayırıcı: `x + 100`
  - Strateji adı: `x + 150`
  - İkon: `x + content_width * 0.85`

## 🎯 Nasıl Kullanılır?

### 1. **Strateji Dropdown'unu Açma**
- Her AI satırında strateji adının yanında **▼** işareti var
- Strateji adına veya ok işaretine tıklayın
- Dropdown menü açılır

### 2. **Strateji Seçimi**
- Dropdown'da 7 farklı strateji listelenir:
  - **RANDOM** - Rastgele kart satın alma
  - **WARRIOR** - Agresif savaş odaklı
  - **BUILDER** - Sinerji oluşturma stratejisi
  - **EVOLVER** - Evrim odaklı oynanış
  - **ECONOMIST** - Altın optimizasyonu
  - **BALANCER** - Dengeli yaklaşım
  - **RARE_HUNTER** - Nadir kartları hedefler

### 3. **Seçimi Onaylama**
- İstediğiniz stratejiye tıklayın
- Dropdown otomatik kapanır
- Yeni strateji AI satırında görünür

### 4. **Oyunu Başlatma**
- Tüm AI stratejilerini ayarladıktan sonra
- **OYUNA BAŞLA** butonuna tıklayın
- Seçtiğiniz stratejilerle oyun başlar

## 🎨 Görsel Özellikler

### **Hover Efektleri**
- Strateji butonunun üzerine gelince hafif highlight
- Dropdown itemlerinin üzerine gelince renkli vurgu

### **Renkli Stratejiler**
Her strateji oyundaki diğer elementlerle çakışmayan özel renkle gösterilir:
- 🔴 **WARRIOR** - Parlak kırmızı (saldırgan)
- 🟢 **BUILDER** - Açık yeşil (bağlantı)
- 🟣 **EVOLVER** - Parlak mor (evrimleşen)
- 🟡 **ECONOMIST** - Parlak altın (ekonomi)
- 🔵 **BALANCER** - Açık mavi (dengeli)
- 💜 **RARE_HUNTER** - Açık mor/pembe (nadir)
- ⚫ **RANDOM** - Açık gri (nötr)

### **Seçili Strateji İşareti**
- Dropdown'da seçili strateji yanında **✓** işareti
- Strateji ikonları (küçük renkli kareler) sağda

### **Animasyonlar**
- Dropdown açılma/kapanma: smooth fade
- Hover efektleri: yumuşak geçişler
- Gölge efektleri: 3 katmanlı derinlik

## 🔧 Teknik Detaylar

### **Veri Yapısı**
```python
self._ai_strategies = [
    "random",    # AI 1
    "warrior",   # AI 2
    "builder",   # AI 3
    "evolver",   # AI 4
    "economist", # AI 5
    "balancer",  # AI 6
    "rare_hunter"# AI 7
]
```

### **Bootstrap Entegrasyonu**
Seçilen stratejiler `_bootstrap()` fonksiyonuna iletilir:
```python
gs = _bootstrap(ai_strategies=self._ai_strategies)
```

### **Dropdown State Management**
- `_active_dropdown`: Hangi AI'ın dropdown'u açık (0-6 veya None)
- `_dropdown_rects`: Her strateji butonunun tıklanabilir alanı
- `_dropdown_item_rects`: Dropdown itemlerinin tıklanabilir alanları
- `_hovered_strategy_btn`: Hover edilen strateji butonu
- `_hovered_dropdown_item`: Hover edilen dropdown item

## 📝 Kullanım Senaryoları

### **Senaryo 1: Tüm AI'lar Warrior**
Agresif bir oyun için tüm AI'ları warrior yapın:
```
AI 1 — WARRIOR
AI 2 — WARRIOR
AI 3 — WARRIOR
AI 4 — WARRIOR
AI 5 — WARRIOR
AI 6 — WARRIOR
AI 7 — WARRIOR
```

### **Senaryo 2: Dengeli Karışım**
Farklı stratejilerle dengeli bir oyun:
```
AI 1 — WARRIOR
AI 2 — BUILDER
AI 3 — EVOLVER
AI 4 — ECONOMIST
AI 5 — BALANCER
AI 6 — RARE_HUNTER
AI 7 — RANDOM
```

### **Senaryo 3: Ekonomi Odaklı**
Ekonomi stratejilerini test etmek için:
```
AI 1 — ECONOMIST
AI 2 — ECONOMIST
AI 3 — ECONOMIST
AI 4 — BUILDER
AI 5 — BALANCER
AI 6 — RARE_HUNTER
AI 7 — RANDOM
```

## 🐛 Bilinen Davranışlar

1. **Dropdown Dışına Tıklama**: Dropdown otomatik kapanır
2. **Aynı Stratejiye Tıklama**: Dropdown kapanır, değişiklik olmaz
3. **Başka Dropdown Açma**: Önceki dropdown otomatik kapanır
4. **Oyun Başlatma**: Seçilen stratejiler oyun motoruna iletilir

## 🎯 Gelecek İyileştirmeler (Opsiyonel)

- [ ] Tooltip ile strateji açıklamaları (hover'da)
- [ ] Strateji istatistikleri (kazanma oranı, vb.)
- [ ] Preset strategi kombinasyonları (kolay/orta/zor)
- [ ] Strateji önizlemesi (hangi kartları tercih eder)
- [ ] Rastgele strateji atama butonu
- [ ] Strateji kopyalama (bir AI'dan diğerine)

## 📚 İlgili Dosyalar

- `v2/scenes/lobby.py` - Lobi ekranı implementasyonu
- `v2/main.py` - Bootstrap fonksiyonu
- `engine_core/game_factory.py` - Oyun motoru oluşturma
- `LOBBY_STRATEGY_SELECTION.md` - Bu dokümantasyon

---

**Son Güncelleme:** 2026-04-30
**Versiyon:** 1.5 (Layout Fix)
**Durum:** ✅ Tamamlandı ve Test Edildi

## 📋 Değişiklik Geçmişi

### v1.5 (2026-04-30)
- ✅ LOBBY başlığı satırlarla aynı hizaya getirildi (sol taraf)
- ✅ Başlık pozisyonu: Golden ratio → Sabit (row_start_x + 20, 50px)
- ✅ Satır aralıkları: Dinamik → Sabit (55px)
- ✅ Human satırı aralıkları genişletildi (üst üste binme düzeltildi)
- ✅ Human ayırıcı rengi: CYAN → GRAY (daha az vurgulu)
- ✅ Tutarlı ve düzenli layout

### v1.4 (2026-04-30)
- ✅ Başlık metni: "LOBİ" → "LOBBY" (İngilizce)
- ✅ Satır fontları: BitcountGridDoubleInk → broken-strings.regular
- ✅ Dropdown fontları: BitcountGridDoubleInk → broken-strings.regular
- ✅ Alt başlık fontu: BitcountGridDoubleInk → broken-strings.regular
- ✅ Alt bilgi fontu: BitcountGridDoubleInk → broken-strings.regular
- ✅ Font boyutları optimize edildi (24pt, 20pt, 16pt, 13pt)
- ✅ Font hiyerarşisi oluşturuldu (başlık kalın, içerik şık, buton özel)

### v1.3 (2026-04-30)
- ✅ Strateji göstergeleri küpten daireye dönüştürüldü (yumuşak, glow + highlight)
- ✅ Tüm border radius değerleri artırıldı (daha yumuşak köşeler)
- ✅ AI satır arka planı: 6px → 12px
- ✅ Human satır arka planı: 8px → 14px
- ✅ Dropdown köşeleri: 8px → 14px
- ✅ Start buton köşeleri: 10px → 16px
- ✅ Dropdown ikonları dairelere dönüştürüldü

### v1.2 (2026-04-30)
- ✅ Satır arka plan yüksekliği sabit değere çevrildi (40px AI, 44px human)
- ✅ Yazılar şeridin ortasına hizalandı (negatif Y offset)
- ✅ Human satırı AI satırlarından biraz daha yüksek yapıldı

### v1.1 (2026-04-30)
- ✅ Dropdown event handling öncelik sırası düzeltildi
- ✅ Render sırası düzeltildi (dropdown en üstte)
- ✅ Renk paleti oyundaki elementlerle çakışmayacak şekilde güncellendi
- ✅ Satır layout'u sabit piksel pozisyonlarıyla orantılandı
- ✅ Dropdown boyutu ve padding'i iyileştirildi

### v1.0 (2026-04-30)
- ✨ İlk versiyon: Dropdown strateji seçimi eklendi
- ✨ 7 farklı AI stratejisi desteği
- ✨ Hover efektleri ve animasyonlar
- ✨ Bootstrap entegrasyonu
