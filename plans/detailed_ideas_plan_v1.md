# 🚀 Detaylı Entegrasyon Planı: 10 Devrimsel UI/Engine Fikri

Bu belge, **Autochess Hybrid** motorunun derinliklerindeki verileri oyuncuya görsel ve dokunsal birer deneyim olarak sunmak için hazırlanan teknolojik uygulama planıdır.

---

## 1. AI Strateji Rozetleri ve Dinamik Araç İpuçları
AI'nın internal "kişiliğini" (`ai.py` -> `ParameterizedAI`) oyuncuya deşifre eder.

*   **Motor Bağlantısı:** `Player.strategy` ve `TRAINED_PARAMS` içindeki `greed_gold_thresh` veya `power_weight` gibi eşik değerler.
*   **Görsel Temsil:** Lobby panelinde oyuncu adının yanında parlayan neon rozetler (Örn: Altın sikke, Kırmızı kılıç).
*   **Uygulama Yöntemi:**
    1.  `LobbyPanel.render` içine her `pid` için `gs.get_strategy(pid)` çağrısı ekle.
    2.  `STRATEGY_THEMES` sözlüğü oluştur (Renkler ve ikonlar).
    3.  Mouse ile lobby satırı üzerine gelindiğinde `InfoBox` içinde AI'nın şu anki önceliğini (Örn: "Faiz biriktiriyor") göster.

## 2. Hex Etki Alanı ve "Baskı" Işımaları
Bir kartın yerleştirildiği hex çevresindeki "tehditini" (`board.py` -> `neighbors`) görselleştirir.

*   **Motor Bağlantısı:** `Board.neighbors()` ve kartın `total_power()` metodu.
*   **Görsel Temsil:** Kart drag (sürükleme) halindeyken, hedef hex'in etrafındaki 6 komşu hex'in zemininde kartın gücüyle orantılı siberpunk bir "nabız" efekti.
*   **Uygulama Yöntemi:**
    1.  `ShopScene.render` içindeki `render_ghost_preview` fonksiyonuna `draw_influence_ring` parametresi ekle.
    2.  Güç değerine göre `(0, 255, 255)` renginin alpha (yarı saydamlık) değerini `math.sin` ile titreştir.

## 3. Grup Stabilite ve Elenme Riski Bayrakları
Kartların yok olma krizini (`card.py` -> `is_eliminated`) anlık hissettirir.

*   **Motor Bağlantısı:** `Card.stats` içindeki gruplanmış değerlerin (EXISTENCE, MIND, CONNECTION) 0'a yakınlığı.
*   **Görsel Temsil:** Kartın alt kenarında üç küçük dikey bar. Eğer bir gruptaki tüm stat'lar 0'a inerse o bar kırmızı yanıp sönmeye başlar.
*   **Uygulama Yöntemi:**
    1.  `CardFlip.render` metoduna `draw_stability_bars(card_stats)` çağrısı ekle.
    2.  Her grup için `min(stats_in_group)` değerini kontrol et; 0 ise `Colors.HP_LOW` ile "CRITICAL" uyarısı bas.

## 4. Pasif Zincir "Rezonans" Hatları
Ardışık tetiklenen pasifleri (`passive_trigger.py`) birbirine bağlar.

*   **Motor Bağlantısı:** `trigger_passive` sırasında oluşan zincirleme fonksiyon çağrıları.
*   **Görsel Temsil:** İki kart arasında saniyelik, elektrik akımı şeklinde bir çizgi.
*   **Uygulama Yöntemi:**
    1.  `GameState` içinde `current_resonance_vfx` listesi tut.
    2.  `PassiveTrigger` bir buff verdiğinde, kaynak ve hedef koordinatları bu listeye ekle.
    3.  `ShopScene.render` her frame bu listedeki hatları `pygame.draw.aalines` ile çizip alpha değerini düşürsün.

## 5. Pazar Kıtlığı ve "Mistik Şans" Efekti
Havuzdaki nadirliği (`market.py` -> `pool_copies` & `_rarity_weight`) vurgular.

*   **Motor Bağlantısı:** `Market.pool_copies` ve tur bazlı ağırlık katsayısı.
*   **Görsel Temsil:** Havuzda son 3 adet kalmış kartlar için dükkanda "SCARCE" (Kıt) damgası. Çok düşük ihtimalle gelen (Rarity-5) kartların etrafında "Mistik Işıma".
*   **Uygulama Yöntemi:**
    1.  `ShopPanel.sync` sırasında `gs.get_pool_count(card_name)` değerini al.
    2.  Eğer sayı 3'ün altındaysa `CardFlip` üzerine özel bir overlay surface yapıştır.
    3.  Rarity-5 kartlar için `CardFlip`'e `is_mystic=True` flag'i ekle ve render sırasında particle emisyonu yap.

## 6. Savaş "Kenar Galibiyeti" Parçacık Efektleri
Savaş sonucunun (`resolve_single_combat` -> `edge_wins`) mikro detaylarını gösterir.

*   **Motor Bağlantısı:** `CombatResult` nesnesindeki `points_a` ve `points_b` farkı.
*   **Görsel Temsil:** İki kart çarpıştığında, kazanan tarafın kenarından rakibe doğru fırlayan neon partikülleri.
*   **Uygulama Yöntemi:**
    1.  `CombatOverlay` içindeki loglar okunurken `points > 5` olan satırlar için koordinat hesapla.
    2.  `ParticleManager` (yeni class) üzerinden çarpışma noktasına `Explosion` efekti spawn et.

## 7. Dinamik Evrim "Aurası" ve Gerilim
3. kopyanın beklendiği anlardaki heyecanı (`gs.get_copies()`) artırır.

*   **Motor Bağlantısı:** `Player.hand` ve `Player.board` toplamında aynı karttan 2 adet olması.
*   **Görsel Temsil:** Elinizdeki veya tahtanızdaki o kartın 3. kopyası dükkana düştüğünde, eldeki kartın "titremesi" ve mor bir ışık yayması.
*   **Uygulama Yöntemi:**
    1.  `ShopPanel` dükkanı yenilediğinde, oyuncunun elindeki kartlarla dükkandakileri karşılaştır.
    2.  Eğer "Dükkanda 3. kopya var" ise ilgili `CardFlip` nesnesine `set_vibration(True)` komutu gönder.

## 8. Gelir Detay Dökümü (Hover Breakdown)
Gelir matematiğini (`BASE_INCOME`, `MAX_INTEREST`) şeffaf hale getirir.

*   **Motor Bağlantısı:** `Player.gold`, tur başı kazanç mantığı.
*   **Görsel Temsil:** Mouse ile `PlayerHub`'daki altın göstergesi üzerine gelindiğinde açılan floating panel.
*   **Uygulama Yöntemi:**
    1.  `PlayerHub` içinde `income_rect` tanımla.
    2.  `gs.get_income_details()` metodunu yaz (Temel + Faiz + Seri dökümü).
    3.  `ShopScene` içindeki hover logic'ine `PlayerHub` gelir detaylarını ekle.

## 9. Tarihsel "Husumet" (Grudge) İşaretleri
Maç geçmişini (`last_combat_results`) kişiselleştirir.

*   **Motor Bağlantısı:** Son 3 turdaki mağlubiyetlerin hangi `pid`'den geldiği.
*   **Görsel Temsil:** Lobby'deki o AI oyuncusunun isminin kırmızı bir yanma efektiyle (Fire) vurgulanması.
*   **Uygulama Yöntemi:**
    1.  `GameState`'te `history_matrix` tut.
    2.  `LobbyPanel.render` sırasında "Eğer bu oyuncu beni az önce yendiyse" kontrolü yap.
    3.  Neon kırmızı dış çerçeve (glow) ekle.

## 10. Oyun Sonu KPI Anlatısı ve MVP Vitrini
Maç özetini (`kpi_aggregator.py`) görsel bir sergiye dönüştürür.

*   **Motor Bağlantısı:** `KPI_Aggregator`'daki `passive_delta` / `turn` oranı en yüksek kart.
*   **Görsel Temsil:** "MAÇIN KAHRAMANI" başlığı altında, o kartın devasa bir görseli ve maç boyu kazandırdığı toplam puan.
*   **Uygulama Yöntemi:**
    1.  `EndgameOverlay`'e `set_hero_card(card_name, stats)` metodu ekle.
    2.  `gs.get_endgame_stats()` içinden en verimli kartın `uid`'sini çek ve render et.

---

### Doğrulama Planı
1.  **Birim Testleri:** Her motor bağlantısının (`gs.get_...`) doğru veriyi döndürdüğü Pytest ile doğrulanacak.
2.  **Performans:** `ParticleManager` ve `Glow` efektlerinin FPS'i 60'ın altına düşürmediği test edilecek.
3.  **Görsel Uyum:** Tüm neon renklerin siberpunk estetiğine uygunluğu USER onayıyla kontrol edilecek.
