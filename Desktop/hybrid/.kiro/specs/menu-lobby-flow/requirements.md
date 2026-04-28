# Gereksinimler Dokümanı

## Giriş

Bu doküman, oyun başlatma akışının menü-lobi-shop sıralamasına dönüştürülmesi için gereksinimleri tanımlar. Mevcut sistemde oyun direkt shop sahnesinde başlarken, yeni akışta kullanıcı önce menü ekranını görür, lobi ekranında rakiplerini inceler ve ardından oyunu başlatır.

## Sözlük

- **System**: Oyun uygulamasının tamamı (pygame tabanlı)
- **MenuScene**: İlk açılış ekranı, "YENİ OYUN" butonu içerir
- **LobbyScene**: Oyuncu listesi ve "OYUNA BAŞLA" butonu içeren ekran
- **ShopScene**: Oyunun ana shop ekranı (mevcut)
- **SceneManager**: Sahneler arası geçişleri yöneten singleton sınıf
- **_bootstrap()**: GameState ve engine'i başlatan module-level fonksiyon
- **GameState**: Oyun durumunu tutan ana nesne
- **Lazy Init**: Bir kaynağın ilk kullanımda yüklenmesi (erken yükleme yerine)
- **Fade Transition**: Sahneler arası yumuşak geçiş animasyonu

## Gereksinimler

### Gereksinim 1: Uygulama Başlatma

**Kullanıcı Hikayesi:** Bir oyuncu olarak, oyunu başlattığımda direkt shop yerine menü ekranını görmek isterim, böylece oyuna hazırlanabilirim.

#### Kabul Kriterleri

1. WHEN uygulama başlatıldığında, THE System SHALL pygame'i initialize etmeli
2. WHEN pygame initialize edildikten sonra, THE System SHALL SceneManager singleton'ını oluşturmalı
3. WHEN SceneManager oluşturulduktan sonra, THE System SHALL ilk sahne olarak MenuScene'i set etmeli
4. THE System SHALL main() fonksiyonu içinde _bootstrap() fonksiyonunu çağırmamalı

### Gereksinim 2: Menü Ekranı Görüntüleme

**Kullanıcı Hikayesi:** Bir oyuncu olarak, menü ekranında oyun başlığını ve başlatma butonunu görmek isterim, böylece ne yapacağımı bilirim.

#### Kabul Kriterleri

1. WHEN MenuScene aktif olduğunda, THE System SHALL siyah arka plan render etmeli
2. WHEN MenuScene render edildiğinde, THE System SHALL "AUTOCHESS HYBRID" başlığını ekran ortasının üst bölgesinde göstermeli
3. WHEN MenuScene render edildiğinde, THE System SHALL "YENİ OYUN" butonunu başlığın 120px altında göstermeli
4. WHEN MenuScene render edildiğinde, THE System SHALL buton koordinatlarını _btn_rect alanına kaydetmeli
5. THE MenuScene SHALL fontları lazy init ile yüklemeli (pygame başlamadan önce değil)

### Gereksinim 3: Menüden Lobiye Geçiş

**Kullanıcı Hikayesi:** Bir oyuncu olarak, "YENİ OYUN" butonuna tıkladığımda lobi ekranına geçmek isterim, böylece rakiplerimi görebilirim.

#### Kabul Kriterleri

1. WHEN kullanıcı "YENİ OYUN" butonuna tıkladığında, THE System SHALL LobbyScene'e fade geçişi başlatmalı
2. WHEN kullanıcı buton dışı bir alana tıkladığında, THE System SHALL sahne geçişi yapmamalı
3. WHEN sahne geçişi başlatıldığında, THE SceneManager SHALL MenuScene.on_exit() metodunu çağırmalı
4. WHEN LobbyScene aktif olduğunda, THE SceneManager SHALL LobbyScene.on_enter() metodunu çağırmalı

### Gereksinim 4: Lobi Ekranı Görüntüleme

**Kullanıcı Hikayesi:** Bir oyuncu olarak, lobi ekranında tüm oyuncuları (7 AI + ben) görmek isterim, böylece kiminle oynayacağımı bilirim.

#### Kabul Kriterleri

1. WHEN LobbyScene aktif olduğunda, THE System SHALL siyah arka plan render etmeli
2. WHEN LobbyScene render edildiğinde, THE System SHALL sol üstte "LOBİ" başlığını göstermeli
3. WHEN LobbyScene render edildiğinde, THE System SHALL 7 AI oyuncu satırını göstermeli
4. WHEN AI oyuncu satırları render edildiğinde, THE System SHALL her satırda "AI {numara} — {strateji}" formatını kullanmalı
5. WHEN LobbyScene render edildiğinde, THE System SHALL 8. satırda insan oyuncuyu "► SEN — {isim}" formatında göstermeli
6. WHEN LobbyScene render edildiğinde, THE System SHALL sağ altta "OYUNA BAŞLA" butonunu göstermeli
7. THE LobbyScene SHALL fontları lazy init ile yüklemeli

### Gereksinim 5: Lobiden Oyuna Geçiş

**Kullanıcı Hikayesi:** Bir oyuncu olarak, "OYUNA BAŞLA" butonuna tıkladığımda oyunun başlamasını isterim, böylece shop ekranında kartlarımı seçebilirim.

#### Kabul Kriterleri

1. WHEN kullanıcı "OYUNA BAŞLA" butonuna tıkladığında, THE System SHALL _bootstrap() fonksiyonunu lazy import ile çağırmalı
2. WHEN _bootstrap() çağrıldığında, THE System SHALL GameState nesnesi oluşturmalı
3. WHEN GameState oluşturulduktan sonra, THE System SHALL ShopScene'e fade geçişi başlatmalı
4. WHEN ShopScene geçişi başlatıldığında, THE System SHALL GameState nesnesini ShopScene constructor'ına parametre olarak geçmeli
5. WHEN kullanıcı buton dışı bir alana tıkladığında, THE System SHALL _bootstrap() çağırmamalı

### Gereksinim 6: Engine Lazy Loading

**Kullanıcı Hikayesi:** Bir geliştirici olarak, ağır engine başlatma işleminin sadece gerektiğinde yapılmasını isterim, böylece menü açılışı hızlı olur.

#### Kabul Kriterleri

1. THE _bootstrap() fonksiyonu SHALL module-level fonksiyon olarak kalmalı
2. THE _bootstrap() fonksiyonu SHALL main() içinden çağrılmamalı
3. WHEN _bootstrap() çağrıldığında, THE System SHALL AssetLoader singleton'ını initialize etmeli
4. WHEN _bootstrap() çağrıldığında, THE System SHALL CardDatabase singleton'ını initialize etmeli
5. WHEN _bootstrap() çağrıldığında, THE System SHALL build_game() fonksiyonunu çağırmalı
6. WHEN _bootstrap() tamamlandığında, THE System SHALL GameState nesnesi döndürmeli

### Gereksinim 7: Font Lazy Initialization

**Kullanıcı Hikayesi:** Bir geliştirici olarak, fontların pygame başlamadan önce oluşturulmamasını isterim, böylece başlatma hataları önlenir.

#### Kabul Kriterleri

1. WHEN bir Scene nesnesi oluşturulduğunda, THE System SHALL font alanlarını None olarak initialize etmeli
2. WHEN Scene.draw() veya Scene._init_fonts() çağrıldığında, THE System SHALL fontları yüklemeli
3. WHEN fontlar zaten yüklenmiş ise, THE System SHALL tekrar yükleme yapmamalı
4. IF pygame.font.SysFont() istenen fontu bulamazsa, THEN THE System SHALL varsayılan font kullanmalı

### Gereksinim 8: Sahne Geçiş Animasyonları

**Kullanıcı Hikayesi:** Bir oyuncu olarak, sahneler arası yumuşak geçişler görmek isterim, böylece deneyim daha profesyonel hissedilir.

#### Kabul Kriterleri

1. WHEN MenuScene'den LobbyScene'e geçiş yapılırken, THE SceneManager SHALL fade animasyonu kullanmalı
2. WHEN LobbyScene'den ShopScene'e geçiş yapılırken, THE SceneManager SHALL fade animasyonu kullanmalı
3. WHEN ilk sahne set edilirken (main başlangıcı), THE SceneManager SHALL fade animasyonu kullanmamalı
4. THE SceneManager SHALL varsayılan fade süresini 200ms olarak kullanmalı

### Gereksinim 9: Kaynak Temizliği

**Kullanıcı Hikayesi:** Bir geliştirici olarak, sahneler arası geçişlerde kaynakların düzgün temizlenmesini isterim, böylece bellek sızıntısı olmaz.

#### Kabul Kriterleri

1. WHEN LobbyScene.on_exit() çağrıldığında, THE System SHALL _audio_loader referansını None yapmalı
2. WHEN bir sahne on_exit() çağrıldığında, THE System SHALL o sahneye ait tüm geçici kaynakları serbest bırakmalı

### Gereksinim 10: Hata Yönetimi

**Kullanıcı Hikayesi:** Bir geliştirici olarak, hataların uygun şekilde ele alınmasını isterim, böylece kullanıcı deneyimi bozulmaz.

#### Kabul Kriterleri

1. IF _bootstrap() sırasında AssetLoader hatası oluşursa, THEN THE System SHALL AutochessException fırlatmalı
2. IF pygame.font.SysFont() istenen fontu bulamazsa, THEN THE System SHALL varsayılan font ile devam etmeli
3. IF handle_event() çağrıldığında _btn_rect None ise, THEN THE System SHALL tıklamayı sessizce yoksaymalı
4. WHEN bir hata oluştuğunda, THE System SHALL kullanıcıya anlamlı hata mesajı göstermeli

### Gereksinim 11: Buton Etkileşim Güvenliği

**Kullanıcı Hikayesi:** Bir geliştirici olarak, buton tıklamalarının güvenli şekilde işlenmesini isterim, böylece race condition'lar önlenir.

#### Kabul Kriterleri

1. WHEN handle_event() çağrıldığında, THE System SHALL _btn_rect'in None olup olmadığını kontrol etmeli
2. WHEN _btn_rect None ise, THE System SHALL tıklama kontrolü yapmamalı
3. WHEN draw() en az bir kez çağrılmadan handle_event() tetiklenirse, THE System SHALL güvenli şekilde başarısız olmalı
4. WHEN bir buton tıklaması işlendiğinde, THE System SHALL sadece sol fare butonu (button=1) için yanıt vermeli

