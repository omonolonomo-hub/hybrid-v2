# ✨ UI Cila, Rötuş ve İnce Ayar Raporu (v1.0)

Bu rapor, mevcut **Autochess Hybrid** arayüzünün "premium" bir hissiyata ulaşması için gereken estetik dokunuşları, animasyon iyileştirmelerini ve kullanıcı deneyimi (UX) rötüşlarını kapsamaktadır. Mevcut tasarımın üzerine eklenecek bu "cila" katmanı, uygulamanın profesyonel bir oyun seviyesine taşınmasını hedeflemektedir.

---

## 1. CardFlip: Easing Fonksiyonları ve "Parlaklık" Efekti
Mevcut kart çevirme animasyonu doğrusal (linear) bir geçişe sahip. Bu durum animasyonun biraz mekanik hissedilmesine neden oluyor.

*   **Mevcut Durum:** `lerp` ile sabit hızda çevirme.
*   **Cila Önerisi:** Kart çevirme işlemine `Ease-Out Cubic` veya `Ease-Out Sine` eğrisi eklenmeli. Kart tam olarak "yüzünü" gösterdiğinde (flip_progress=1.0), üzerinden saniyelik bir beyaz "parlama" (shine) efekti geçmeli.
*   **Teknik Uygulama:** `update` fonksiyonundaki `diff * FLIP_SPEED` yerine, zamana dayalı bir katsayı (`progress_t`) kullanılarak eğri uygulanmalı. Parlama efekti için `pygame.BLEND_ADD` modunda bir Surface kartın üzerinden `rect.x` boyunca kaydırılmalı.

## 2. PlayerHub: "Rolling Numbers" (Yuvarlanan Sayılar)
Altın ve HP değerleri şu an anlık olarak değişiyor (`10 -> 12` gibi).

*   **Mevcut Durum:** Statik metin güncellemesi.
*   **Cila Önerisi:** Değer değiştiğinde, sayının artışını veya azalışını gösteren hızlı bir "dönme" animasyonu. Eğer altın artıyorsa yeşil, azalıyorsa kırmızı bir "flaş" ile desteklenmeli.
*   **Teknik Uygulama:** `self._display_gold` değişkeni, gerçek `self._gold` değerine her frame %10 yaklaşacak şekilde (lerp) güncellenmeli. `round()` edilerek ekrana basılmalı.

## 3. LobbyPanel: Aktif İzleyici Odak Işıması
Spectate modunda hangi oyuncunun izlendiği şu an sadece statik bir çerçeveyle belli.

*   **Mevcut Durum:** Basit bir renkli çerçeve.
*   **Cila Önerisi:** İzlenen oyuncu satırının (`view_index`) kenarlarında, siberpunk estetiğine uygun, yavaşça atan (alpha pulse) bir neon ışığı.
*   **Teknik Uygulama:** `LobbyPanel.render` içinde `hp == GameState.get().view_index` olan satır için `math.sin(time.time() * 3) * 50 + 200` şeklinde bir alpha değeri ile `UIUtils.create_glow` yüzeyi blit edilmeli.

## 4. ShopPanel: Reroll ve Lock Buton Hissiyatı (Haptic Feedback)
Butonlara tıklandığında fiziksel bir geri bildirim eksikliği hissediliyor.

*   **Mevcut Durum:** Tıklanınca olay tetikleniyor ama görsel değişim minimal.
*   **Cila Önerisi:** "Depress" efekti. Butona basıldığı an, buton görseli 2-3 piksel aşağı kaymalı ve üzerindeki ikon hafifçe parlamalı. Reroll sonrasında dükkan slotları "soluktan canlıya" (fade-in) bir geçişle gelmeli.
*   **Teknik Uygulama:** Buton rect'ine `_is_pressed` flag'i eklenmeli. `handle_event` içinde `MOUSEBUTTONDOWN` olduğunda `rect.y += 2` yapılmalı.

## 5. SynergyHUD: Tier-Up Patlama Efekti (Burst)
Bir sinerji grubu yeni bir seviyeye (S→SS gibi) ulaştığında bu, oyunun en önemli anlarından biridir.

*   **Mevcut Durum:** Seviye yazısı değişiyor.
*   **Cila Önerisi:** Yeni seviyeye geçildiği an, sinerji ikonunun arkasından dışarı doğru yayılan dairesel bir ışık patlaması (Radial Burst).
*   **Teknik Uygulama:** `SynergyHud` içinde her grup için `_last_tier` takibi yapılmalı. Eğer `current_tier > _last_tier` ise, ikon koordinatında bir `ExpandingCircle` (partikül) oluşturulmalı.

## 6. HexGrid: Kamera Yumuşatma (Camera Lerp)
Kamera hareketleri (W, A, S, D) şu an çok keskin.

*   **Mevcut Durum:** `offset_x += speed` ile sert geçiş.
*   **Cila Önerisi:** Kameranın hedeflenen noktaya "akarak" gitmesi. Zoom (yakınlaştırma) işlemi sırasında merkeze doğru yavaşça durma (Slow decay).
*   **Teknik Uygulama:** `GridMath.camera` içine `target_offset` ve `current_offset` ayrımı getirilmeli. Her frame `current = current + (target - current) * 0.15` formülüyle kamera hareket ettirilmeli.

## 7. HandPanel: Rotasyon Görselleştirme (Rotation Wheel)
Kartı "R" ile döndürürken hangi aşamada olduğunu anlamak bazen zor olabiliyor.

*   **Mevcut Durum:** Kart asset'i anlık 60 derece dönüyor.
*   **Cila Önerisi:** Kart dönerken çevresinde saniyelik bir dairesel derece cetveli (Rotation Wheel) belirmeli. Kartın "ana stat"ı parlayan bir ok ile vurgulanmalı.
*   **Teknik Uygulama:** `rotation` değeri değiştiğinde, kartın merkezini baz alan 6 noktalı bir heksagon şablonu (şeffaf) kartın altında görünmeli.

## 8. InfoBox/Tooltip: Yumuşak Giriş ve Çıkış
Kart detay panelleri şu an "pat" diye beliriyor.

*   **Mevcut Durum:** Instant visibility.
*   **Cila Önerisi:** Panelin 100ms içinde alttan yukarı doğru hafifçe kayarak ve yüzde 0'dan 100'e alpha (saydamlık) artışı ile gelmesi (Slide-up Fade).
*   **Teknik Uygulama:** `InfoBox` sınıfına `_alpha` ve `_current_y_offset` değişkenleri eklenmeli. `active` olduğunda bu değerler hedeflerine doğru lerp edilmeli.

## 9. Board Presence: Mıknatıs Efektli Slot Işığı
Kartı tahtaya yerleştirmeye çalışırken hangi hex'e düşeceği daha net olmalı.

*   **Mevcut Durum:** Sadece ghost preview (hayalet görüntü).
*   **Cila Önerisi:** Kart bir hex'e yaklaştığında, o hex'in zemininde o kartın dominant rengine (`dominant_group`) uygun bir "Vakum/Mıknatıs" ışığı yanmalı.
*   **Teknik Uygulama:** `ShopScene.handle_event` içinde mouse pozisyonuna en yakın hex mesafesi `< 30px` ise o hex'in `render_grid` fonksiyonuna `is_highlighted=True` gönderilmeli.

## 10. Atmosferik "Nefes Alma" (Global Breathing)
Arayüz elementlerinin statikliği siberpunk temasını zayıflatıyor.

*   **Mevcut Durum:** Sabit arka planlar ve ayıraçlar.
*   **Cila Önerisi:** Panellerin çerçeve ışıkları (border glow) ve tablolardaki ayraç çizgileri, yavaş bir frekansta (0.5Hz) nefes alıyormuş gibi parlayıp sönmeli.
*   **Teknik Uygulama:** `ui_utils.py` içindeki `create_gradient_panel` fonksiyonunda kullanılan sınır rengi, ana döngüdeki bir `global_pulse` katsayısı ile çarpılmalı.

---

> [!IMPORTANT]
> **Uygulama Notu:** Bu iyileştirmelerin hiçbiri motorun matematiksel mantığını etkilemez; tamamen "Görsel Katman" (Layer 0) üzerinde gerçekleşir. Bu sayede oyunun performansı korunurken kullanıcı deneyimi çağ atlamış olur.
