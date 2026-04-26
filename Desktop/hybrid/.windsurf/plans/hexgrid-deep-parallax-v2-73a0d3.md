# Plan: Deep Parallax & Mouse-Centered Board Interaction

Bu plan, HexGrid sistemini sadece statik bir render olmaktan çıkarıp, fare odaklı dinamik zoom, sürüklenebilir (draggable) dünya koordinatları ve çok katmanlı premium görsel efektlerle donatılmış bir "Living Universe" yapısına dönüştürmeyi hedefler.

## 1. Matematiksel Model: World-to-Screen Transformation
Board ve arka plan nesneleri artık ekran koordinatlarında değil, bir "World Space" içinde yaşayacak.
- **Dinamik State**: `camera_pos` (x, y) ve `zoom_level` (0.5 - 2.0) değerleri tutulacak.
- **Mouse-Centered Zoom**: Zoom yapıldığında fare imlecinin altındaki "Dünya Koordinatı" sabit kalacak şekilde `camera_pos` otomatik kompanze edilecek.
- **Board Drag (Sürükleme)**: Sağ tık veya orta tık (veya boş alanda sol tık) ile dünya koordinatları `camera_pos` üzerinden kaydırılabilecek.

## 2. Çok Katmanlı Parallax Arka Plan (BackgroundManager)
Derinlik hissini artırmak için 3 ana katman kullanılacak:
- **Katman 0 (Deep Void)**: En altta, çok yavaş hareket eden nebula/yıldız tozları (static-ish).
- **Katman 1 (Floating Hexes)**: `void_hex` içindeki petekler, kameradan farklı bir hızda (parallax ratio: 0.5) kayarak derinlik katacak.
- **Katman 2 (Active Board)**: 37 hex ve üzerindeki kartlar, tam kamera hızıyla (ratio: 1.0) hareket edecek.

## 3. A2 Premium "Glass Inset" & Dynamic Lighting
- **Glass Effect**: Her hex hücresi `UIUtils` kullanılarak içe göçük, kenarları ışık kıran (refraction-like) bir cam dokusuyla çizilecek.
- **Dynamic Glow**: Fare bir hex üzerine geldiğinde sadece o hücre değil, komşu hücrelerin kenarları da hafifçe aydınlanacak (proximity lighting).

## 4. Kritik Riskler ve Mühendislik Engelleri
- **Input Conflict**: Kart sürükleme (Hand Drag) ile Board sürükleme (Scene Drag) çakışabilir. 
  - *Çözüm*: Eğer fare bir kartın üzerindeyse "Card Drag", boşluktaysa "Board Drag" tetiklenecek şekilde bir öncelik sırası (Input Sink) kurulacak.
- **Coordinate Jitter**: Zoom seviyesi değiştikçe peteklerin ve kartların "titremesi".
  - *Çözüm*: Tüm matematik `float` hassasiyetinde tutulacak ve `pygame.transform.smoothscale` (veya pre-rendered mipmaps) kullanılacak.
- **Clipping**: Board'un ekran dışına veya panellerin altına çok fazla kayması.
  - *Çözüm*: `camera_pos` için yumuşak sınırlar (bounds with elastic pull-back) eklenecek.

## 5. Uygulama Sırası
1. **Infrastructure**: `GridMath`'i dinamik zoom/offset destekli hale getir.
2. **Camera System**: `ShopScene` içine Mouse-centered zoom ve drag lojiğini ekle.
3. **Background**: `BackgroundManager`'ı çok katmanlı parallax desteğiyle revize et.
4. **Hex Renderer**: Yeni "Glass Inset" görselini ve dynamic highlight sistemini uygula.
5. **Validation**: 104+ test + Jitter-free visual confirmation.
