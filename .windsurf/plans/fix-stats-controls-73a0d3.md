# Plan: Fix Edge Stats, Zoom Bounds, and Keyboard Controls

Bu plan, Ghost Preview'daki stat/renk hatalarını gidermeyi, zoom seviyesini güvenli sınırlar içine almayı ve klavye ile kamera kontrolü eklemeyi hedefler.

## 1. Ghost Preview & Edge Stats Düzeltmesi
- **Sorun**: Statların '0' ve beyaz görünmesi. 
- **Neden**: `CardDatabase` mock verilerindeki stat yapısı ile renderer arasındaki uyumsuzluk veya verinin yüklenememesi.
- **Çözüm**: 
  - `CardDatabase.lookup` dönüşünü ve içindeki `stats` dict yapısını (`"Power"`, `"Durability"` vs. yerine `0-5` arası indexler) kontrol edip, eğer veri yoksa fallback değerler (Mock statlar) üretmek.
  - Sinerji grubu (MIND, CONNECTION, EXISTENCE) eşleşmesini doğrulamak.

## 2. Zoom Sınırları (Clamp) & Keyboard Controls
- **Zoom Bounds**: Zoom seviyesini `0.5` (en uzak) ile `2.5` (en yakın) arasında sınırlamak (Constants'a taşınacak).
- **Keyboard Camera**: 
  - `W, A, S, D`: Kamerayı (offset) kaydır.
  - `Q, E` veya `+, -`: Zoom in/out.
  - `R`: Kamerayı sıfırla (Reset camera).

## 3. Test Disiplini Hakkında Açıklama
- 104 test sayısı, `tests/` dizinindeki mevcut tüm test dosyalarındaki (`test_shop_panel.py`, `test_hex_grid.py` vb.) test senaryolarının toplamıdır.
- Her değişiklikten sonra `pytest` çalıştırılarak, yeni eklenen özelliklerin (örneğin kamera sistemi) mevcut lojiği (örneğin dükkan alımları) bozmadığı doğrulanmaktadır.

## 4. Uygulama Adımları
1. `hex_grid.py` içinde `render_ghost_preview` lojiğini revize et (stat ve renk fix).
2. `ShopScene.handle_event` içine `pygame.KEYDOWN` kontrollerini ekle (W,A,S,D,Q,E,R).
3. Zoom clamp lojiğini `0.5 - 2.5` aralığında sabitle.
4. `pytest` ile tüm sistemin (104+ test) stabilitesini doğrula.
5. `v2/main.py` üzerinden canlı onay al.
