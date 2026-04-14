# Plan: Unified Deep-Zoom Grid (Final Technical Specification)

Bu plan, arka plan petek dokusunu (void_hex) doğrudan "Board" yapısının kendisi haline getirerek, sonsuz bir petek evreninde sadece merkezdeki 37 hücrenin "aktif/board" özellik kazandığı, koordinat titremesi (jitter) ve girdi çakışması (input conflict) risklerini minimize eden bir mühendislik modeli sunar.

## 1. Mimari Temel: Unified Coordinate System
- **BackgroundManager Revizyonu**: `void_hex` artık statik bir resim değil, `CameraState`'i (offset_x, offset_y, zoom) baz alarak petekleri dinamik çizen bir sisteme dönüşecek.
- **GridMath Senkronizasyonu**: `axial_to_pixel` ve `pixel_to_axial` fonksiyonları, ekranın statik merkezini değil, kameranın dinamik `(offset, zoom)` değerlerini referans alacak. 
- **Snapping & Jitter**: Titremeyi önlemek için tüm `World -> Screen` dönüşümleri float hassasiyetinde yapılacak, sadece blit aşamasında `int()` cast uygulanacak.

## 2. Etkileşim Hiyerarşisi (Input Sink)
Aynı anda gerçekleşebilecek 3 farklı girdi türü şu öncelik sırasına göre yönetilecek:
1. **Card Drag (Highest)**: Eğer fare bir kartın (Hand/Shop) üzerindeyse ve sürükleme başladıysa, Board Drag kilitlenir.
2. **Ghost Preview**: Eğer bir kart sürükleniyorsa ve fare bir "Aktif Hex" (`VALID_HEX_COORDS`) üzerindeyse, yerleştirme önizlemesi tetiklenir.
3. **World Drag (Lowest)**: Yukarıdakiler aktif değilse, boş petekler üzerinden fare ile (Sol/Orta tık) tüm evren kaydırılır.

## 3. A2 Premium Görselleştirme (Active vs Passive)
- **Passive Cells (Background)**: `void_hex` içindeki petekler düşük alpha (18-30) ve sadece stroke ile çizilir.
- **Active Cells (Board)**: `VALID_HEX_COORDS` içindeki 37 hücre, zoom seviyesine göre "aktifleşir":
  - `UIUtils.create_gradient_panel` ile cam dokusu (Glass Inset).
  - Kenarlarda `create_glow` ile neon parlaması.
  - Kart yerleştirildiğinde hücrenin derinlik algısının korunması.

## 4. Uygulama ve Güvenlik Sırası
1. **Phase A (State Infrastructure)**: `v2/constants.py` içine `CameraState` sınıfı ve global `camera` objesini ekle. `GridMath`'i bu objeye bağla.
2. **Phase B (Dynamic BG)**: `BackgroundManager`'ı petekleri kamera state'ine göre (infinite tiled logic) çizecek şekilde refactor et.
3. **Phase C (Interaction)**: `ShopScene.handle_event` içine mouse-wheel zoom ve world-drag lojiğini ekle.
4. **Phase D (Board UI)**: `HexGrid.render` metodunu yeni premium görsellerle (Glass Inset) güncelle.
5. **Phase E (Validation)**: 104+ testin geçmesi + `main.py` üzerinde zoom-scroll akıcılığının onayı.

## 5. Kritik Risk Analizi
- **Scale-Up Blur**: Zoom arttıkça petek çizgilerinin kalınlaşması ve çirkinleşmesi. *Önlem*: Zoom seviyesine göre çizgi kalınlığını (width) dinamik ayarla.
- **Coordinate Drift**: Uzun süre sürüklendikten sonra koordinatların kayması. *Önlem*: `axial_to_pixel` fonksiyonuna birim testleri ekle.
- **UI Overflow**: Board'un sürüklenerek yan panellerin (Shop/Hand) altına girmesi. *Önlem*: Render sırasında clip-rect kullanarak board'un sadece orta bölgede görünmesini sağla.
