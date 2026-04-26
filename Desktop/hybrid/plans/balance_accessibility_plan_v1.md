# ⚖️ Plan 5: Denge ve Erişilebilirlik Sertleştirme Planı

Bu plan, kullanıcının belirttiği dengesiz puanlama, görünmez pasifler ve tahta üzerindeki etkileşim eksikliklerini gidermek için hazırlanmış kapsamlı bir "Siberpunk Stabilite" paketidir.

## 🛠 Kullanıcı İncelemesi Gerektiren Konular
> [!IMPORTANT]
> **Puanlama Değişimi:** Yerleşim (Placement) puanının hasara doğrudan etki etmesi sağlanacaktır. Bu, "saf güç" yerine "stratejik yerleşim"in maçları bitirebilmesini sağlayacak köklü bir denge değişikliğidir.

---

## 📋 Önerilen Değişiklikler

### 1. Yerleşim Sinerjisi Puanlama Takviyesi (Balance)
*   **Sorun:** Kenar eşleşmeleri savaşı kazandırsa da skora (hasara) etkisi çok düşük.
*   **Çözüm:** `engine_core/board.py` içindeki `calculate_damage` fonksiyonuna, kazanılan her kenar eşleşmesi (synergy) için ek çarpan/bonus eklenmesi.
*   **Hedef:** 10 puanlık yerleşim başarısını, toplam skorda hissedilir bir ağırlığa (örn. +30/40) çekmek.

### 2. Board Kategori Takip Paneli (HUD)
*   **Sorun:** Tahtada hangi kategoriden kaç kart var (Void, Mage vb.) takip edilemiyor.
*   **Çözüm:** Ekranın sol veya sağ üst köşesine, o an tahtada bulunan kartların kategorilerini ve sayılarını listeleyen dikey bir HUD eklenmesi.
*   **Teknik:** `GameState.get_board_cards()` her değiştiğinde bu paneli senkronize etmek.

### 3. Pasif Aktivasyon Akışı (Combat Toast)
*   **Sorun:** Pasiflerin ne zaman tetiklendiği veya neden çalışmadığı anlaşılmıyor.
*   **Çözüm:** Pasif tetiklendiğinde kartın üzerinde yüzen metin (Floating Text) veya ekranın altında saniyelik "Hologram Uyarı" mesajı belirmesi.
*   **Örn:** *"Phoenix: Reborn!"* veya *"Gravity: Pulling!"*

### 4. Tahta Kart Etkileşimi (Hover Tooltips)
*   **Sorun:** Kart tahtaya konduktan sonra "bilgi kutusu" (InfoBox) bir daha açılmıyor.
*   **Çözüm:** `HexGrid` ve `ShopScene` olay döngüsünün, tahtadaki kartlar üzerinde hover/click tespit ettiğinde `InfoBox`'u o kartın bilgileriyle güncellemesi.

### 5. Kalıcı Kenar Stat Görünürlüğü (On-Board Stats)
*   **Sorun:** Kart yerleştikten sonra kenar değerleri görünmüyor, planlama zorlaşıyor.
*   **Çözüm:** Tahtadaki kartların üzerine gelindiğinde (hover) veya sürekli olarak (opsiyonel), 6 kenar değerinin heksagonun köşelerinde mini sayılar olarak görünmesi.

### 6. Gelişmiş Savaş terminali (Analytics 2.0)
*   **Sorun:** Terminal çok kısıtlı bilgi veriyor.
*   **Çözüm:** Savaş günlüğünün; çarpışan her iki kartın adını, kullanılan kenar statlarını, kazanan kenar sayısını ve o çatışmadan gelen pasif tetiklenmelerini detaylıca dökmesi.

### 7. Beraberlik Bozucu Mekanizma (Draw Breaker)
*   **Sorun:** Çoğu maçın berabere bitmesi gelişimi engelliyor.
*   **Çözüm:** Puanların eşit olduğu durumlarda; daha yüksek rariteye sahip olan tarafın veya tahta toplam gücü (Total Power) yüksek olanın 1 HP farkla kazanması.

### 8. Hologram Yerleşim VFX (User Suggestion)
*   **Sorun:** Kartlar tahtaya aniden belirerek konuyor.
*   **Çözüm:** Kart tahtaya bırakıldığı an, 500ms süren bir "Hologram Tarama" animasyonu ile belirmesi.

### 9. Pasif Durum Göstergeleri (Ready/Cooldown)
*   **Sorun:** Hangi kartın pasifi "hazır" veya "kullanıldı" belli değil.
*   **Çözüm:** Pasifi olan kartların üzerinde küçük bir ikon veya kart çerçevesinde özel bir ışık (Glow) efekti. Pasif kullanıldığında bu ışığın sönmesi.

### 10. Tahta Kartı Açıklama Sistemi (Detailed Descriptions)
*   **Sorun:** Yerleştirilen kartların özel yetenek metinleri bir daha okunamıyor.
*   **Çözüm:** `CardDatabase` entegrasyonu ile tahtadaki kartlara tıklandığında sol panelde kartın tam açıklamasının (Flavor text + Ability) belirmesi.

---

## 🔍 Doğrulama Planı

### Otomatik Testler
*   `tests/test_balance.py`: Yeni puanlama sisteminin draws (beraberlik) oranını %30 ve altına düşürdüğünü doğrula.
*   `tests/test_ui_interactivity.py`: Tahtadaki kartlara mouse ile dokunulduğunda `InfoBox`'un güncellendiğini doğrula.

### Manuel Doğrulama
1.  Bir maç boyunca pasif tetiklenmelerini yüzen metinlerle takip et.
2.  Tahtaya kart koyarken Hologram efektini gözlemle.
3.  Farklı kategorilerde kartlar koyarak sol üstteki Sayacın (Counter) doğru çalıştığını onayla.
