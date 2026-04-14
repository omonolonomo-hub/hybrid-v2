# Plan: Unified Deep-Zoom Grid & Mouse-Centered Interaction

Bu plan, arka plan petek dokusunu (void_hex) doğrudan "Board" yapısının kendisi haline getirerek, sonsuz bir petek evreninde sadece merkezdeki 37 hücrenin "aktif/board" özellik kazandığı, fare odaklı derinlikli bir etkileşim modeli kurmayı hedefler.

## 1. Bütünsel Görsel Yapı: "The Grid is the Board"
- **Tek Katmanlı Zemin**: Arka plan petekleri ve Board hücreleri artık ayrı katmanlar değil, aynı matematiksel gridin parçalarıdır. 
- **Aktifleşme (Board Mode)**: Arka plandaki silik petekler, merkezdeki 37 koordinata (`|q+r| <= 3`) yaklaştıkça veya zoom yapıldığında "Glass Inset" ve "Neon Glow" özelliklerini kazanarak kart yerleştirilebilir hale gelir.
- **Deep-Zoom**: Zoom yapıldığında tüm evren (arka plan + aktif board) fare imlecinin etrafında bütünsel olarak büyür.

## 2. Matematiksel Model & Navigasyon
- **Camera State**: `camera_offset` (x, y) ve `zoom_level` (0.5 - 2.5) değerleri `BackgroundManager` veya `GridMath` içinde tutulacak.
- **Mouse-Centered Zoom**: `zoom_level` değiştiğinde, farenin altındaki dünya koordinatının (axial q, r) ekrandaki piksel pozisyonu sabit kalacak şekilde `camera_offset` güncellenecek.
- **World Drag**: Boş petekler üzerinde (aktif board dışı alanlar dahil) sol tık veya orta tık ile sürükleme yapıldığında `camera_offset` değişerek tüm grid kaydırılabilecek.

## 3. A2 Premium Render & Interaction
- **Unified Hex Render**: Tüm petekler aynı temel üzerine çizilir, ancak `VALID_HEX_COORDS` içindekiler `UIUtils` ile derinlik kazanır.
- **Interaction Sink**: 
  1. Fare kartın üzerindeyse -> **Card Drag (Hand)**
  2. Fare aktif board hücresi üzerindeyse -> **Ghost Preview / Place**
  3. Fare boş grid üzerindeyse -> **World Drag (Camera)**

## 4. Kritik Riskler ve Önlemler
- **Coordinate Drift**: Zoom/Scroll sırasında axial-to-pixel dönüşümünün hassasiyetini kaybetmesi. 
  - *Önlem*: Tüm transformasyonlar float hassasiyetinde yapılacak, render anında pixel-perfect snapping uygulanacak.
- **Visual Banding**: Zoom yapılmış arka planın piksellenmesi. 
  - *Önlem*: `BackgroundManager` petekleri dinamik olarak çizmek yerine, yüksek çözünürlüklü bir pre-render üzerinden `smoothscale` ile işleyecek.
- **Negative Space Korunumu**: Zoom ne kadar artarsa artsın, panellerle (Shop/Hand) olan 15px güvenlik koridoru her zaman korunacak.

## 5. Uygulama Sırası
1. **Core Math**: `GridMath`'i `camera_offset` ve `zoom` parametrelerini global olarak okuyacak şekilde revize et.
2. **Global Controller**: `ShopScene` içine kamera kontrol (scroll wheel zoom + mouse drag) lojiğini entegre et.
3. **Unified BG**: `BackgroundManager`'ı peteklerin Board koordinatlarıyla tam çakıştığı tek katmanlı yapıya geçir.
4. **Active Cells**: `VALID_HEX_COORDS` içindeki hücrelere dinamik "aktifleşme" (glow/inset) efektlerini ekle.
5. **Validation**: 104+ testin korunması ve "Sonsuz Grid" hissiyatının gözle onayı.
