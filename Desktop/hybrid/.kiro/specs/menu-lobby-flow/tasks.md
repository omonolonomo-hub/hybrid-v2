# Implementation Plan: menu-lobby-flow

## Overview

Bu plan, oyun başlatma akışını menü → lobi → shop sıralamasına dönüştürür. MenuScene yeni oluşturulacak, LobbyScene komple yeniden yazılacak ve main.py güncellenecek. Engine başlatma (_bootstrap) lazy loading ile LobbyScene'de yapılacak.

## Tasks

- [ ] 1. MenuScene oluştur ve temel render implementasyonu
  - [x] 1.1 v2/scenes/menu.py dosyasını oluştur
    - MenuScene sınıfını Scene'den türet
    - Constructor'da font alanlarını None olarak initialize et (_font_title, _font_button, _btn_rect)
    - _Requirements: 2.5, 7.1_
  
  - [x] 1.2 MenuScene._init_fonts() metodunu implement et
    - pygame.font.SysFont("Arial", 72) ile _font_title oluştur
    - pygame.font.SysFont("Arial", 36) ile _font_button oluştur
    - Idempotent olmalı (zaten yüklenmişse tekrar yükleme yapma)
    - _Requirements: 7.2, 7.3, 7.4_
  
  - [x] 1.3 MenuScene.draw() metodunu implement et
    - Siyah arka plan (BLACK = (0, 0, 0))
    - "AUTOCHESS HYBRID" başlığını ekran ortası üst bölgede render et (W/2, H/3)
    - "YENİ OYUN" butonunu başlığın 120px altında render et (240x60 boyutunda, border_radius=8)
    - _btn_rect'i güncelle
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  
  - [ ]* 1.4 MenuScene için unit testler yaz
    - draw() sonrası _btn_rect None olmamalı
    - draw() birden fazla çağrılsa da _btn_rect aynı konumda kalmalı
    - _Requirements: 2.4_

- [ ] 2. MenuScene event handling ve geçiş mantığı
  - [x] 2.1 MenuScene.handle_event() metodunu implement et
    - MOUSEBUTTONDOWN ve button=1 kontrolü
    - _btn_rect None kontrolü (guard clause)
    - collidepoint() ile tıklama kontrolü
    - LobbyScene'e transition_to() çağrısı (lazy import)
    - _Requirements: 3.1, 3.2, 11.1, 11.2, 11.3, 11.4_
  
  - [ ]* 2.2 Property test: Buton içi tıklama geçişi tetikler
    - **Property 2: Buton içi tıklama sahne geçişi tetikler**
    - **Validates: Requirements 3.1**
    - ∀ pos ∈ btn_rect.collidepoint → transition_to tam bir kez çağrılır
  
  - [ ]* 2.3 Property test: Buton dışı tıklama geçişi tetiklemez
    - **Property 3: Buton dışı tıklama sahne geçişi tetiklemez**
    - **Validates: Requirements 3.2**
    - ∀ pos ∉ btn_rect.collidepoint → transition_to çağrılmaz
  
  - [ ]* 2.4 Property test: Güvenli buton tıklama işleme
    - **Property 8: Güvenli buton tıklama işleme**
    - **Validates: Requirements 10.3, 11.1, 11.2, 11.3**
    - _btn_rect None iken handle_event() exception fırlatmaz

- [x] 3. Checkpoint - MenuScene tamamlandı
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. LobbyScene'i komple yeniden yaz
  - [x] 4.1 v2/scenes/lobby.py dosyasını yeniden oluştur
    - LobbyScene sınıfını Scene'den türet
    - Constructor'da alanları initialize et:
      - _strategies: 7 AI stratejisi listesi ["random", "warrior", "builder", "evolver", "economist", "balancer", "rare_hunter"]
      - _human_name: "HUMAN"
      - Font alanları: _font_title, _font_row, _font_button (None)
      - _btn_rect: None
      - _audio_loader: None
    - _Requirements: 4.7, 7.1_
  
  - [x] 4.2 LobbyScene._init_fonts() metodunu implement et
    - pygame.font.SysFont("Arial", 48) ile _font_title
    - pygame.font.SysFont("Arial", 28) ile _font_row
    - pygame.font.SysFont("Arial", 32) ile _font_button
    - Idempotent olmalı
    - _Requirements: 7.2, 7.3_
  
  - [x] 4.3 LobbyScene.draw() metodunu implement et
    - Siyah arka plan
    - Sol üstte "LOBİ" başlığı (40, 30)
    - 7 AI satırı: "AI {i+1} — {strategy}" formatında, GRAY renk (160, 160, 160), her biri 60px aralıklı
    - 8. satır: "► SEN — {_human_name}" formatında, CYAN renk (0, 255, 255)
    - Sağ alt "OYUNA BAŞLA" butonu (W-280, H-100, 240x60, border_radius=8)
    - _btn_rect'i güncelle
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_
  
  - [ ]* 4.4 Property test: AI oyuncu format doğruluğu
    - **Property 6: AI oyuncu format doğruluğu**
    - **Validates: Requirements 4.4**
    - ∀ strategy → render edilen satır "AI {numara} — {strateji}" formatında
  
  - [ ]* 4.5 Property test: İnsan oyuncu format doğruluğu
    - **Property 7: İnsan oyuncu format doğruluğu**
    - **Validates: Requirements 4.5**
    - ∀ oyuncu ismi → render edilen satır "► SEN — {isim}" formatında

- [ ] 5. LobbyScene event handling ve _bootstrap çağrısı
  - [x] 5.1 LobbyScene.handle_event() metodunu implement et
    - MOUSEBUTTONDOWN ve button=1 kontrolü
    - _btn_rect None kontrolü (guard clause)
    - collidepoint() ile tıklama kontrolü
    - "from v2.main import _bootstrap" lazy import
    - gs = _bootstrap() çağrısı
    - ShopScene(gs)'e transition_to() çağrısı (lazy import)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_
  
  - [x] 5.2 LobbyScene.on_exit() metodunu implement et
    - _audio_loader = None (kaynak temizliği)
    - _Requirements: 9.1_
  
  - [ ]* 5.3 Property test: Sadece sol fare butonu yanıt verir
    - **Property 9: Sadece sol fare butonu yanıt verir**
    - **Validates: Requirements 11.4**
    - ∀ button != 1 → buton rect içinde tıklama yapılsa bile geçiş tetiklenmez
  
  - [ ]* 5.4 Property test: LobbyScene kaynak temizliği
    - **Property 10: LobbyScene kaynak temizliği**
    - **Validates: Requirements 9.1**
    - on_exit() sonrası _audio_loader None olmalı

- [x] 6. Checkpoint - LobbyScene tamamlandı
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. main.py'yi güncelle
  - [x] 7.1 v2/main.py'de main() fonksiyonunu güncelle
    - "from v2.scenes.menu import MenuScene" import ekle
    - "gs = _bootstrap()" satırını SİL
    - "sm.set_scene(ShopScene(gs))" satırını "sm.set_scene(MenuScene())" ile DEĞİŞTİR
    - _bootstrap() fonksiyonunu module-level olarak koru (silme)
    - _Requirements: 1.3, 1.4, 6.1, 6.2_
  
  - [ ]* 7.2 Unit test: main() içinde _bootstrap() çağrısı yok
    - AST analizi ile main() fonksiyonunda _bootstrap() çağrısı olmadığını doğrula
    - _Requirements: 1.4, 6.2_

- [ ] 8. Lazy initialization property testleri
  - [ ]* 8.1 Property test: draw() çağrısı buton rect'i initialize eder
    - **Property 1: draw() çağrısı buton rect'i initialize eder**
    - **Validates: Requirements 2.4**
    - ∀ Scene (MenuScene veya LobbyScene) → draw() sonrası _btn_rect None değil
  
  - [ ]* 8.2 Property test: Lazy font initialization
    - **Property 4: Lazy font initialization**
    - **Validates: Requirements 2.5, 4.7, 7.1, 7.2**
    - ∀ Scene → constructor sonrası fontlar None, draw() sonrası None değil
  
  - [ ]* 8.3 Property test: Font initialization idempotence
    - **Property 5: Font initialization idempotence**
    - **Validates: Requirements 7.3**
    - ∀ Scene → _init_fonts() N kez çağrılsa da font nesneleri aynı kalır

- [ ]* 9. Integration testler: Tam akış
  - [ ]* 9.1 Integration test: Menu → Lobby geçişi
    - MenuScene oluştur, "YENİ OYUN" tıklamasını simüle et
    - SceneManager.current_scene_name == "LobbyScene" olmalı
    - _Requirements: 3.1, 3.3, 3.4_
  
  - [ ]* 9.2 Integration test: Lobby → Shop geçişi
    - LobbyScene oluştur, "OYUNA BAŞLA" tıklamasını simüle et
    - _bootstrap() çağrıldığını doğrula
    - SceneManager.current_scene_name == "ShopScene" olmalı
    - ShopScene'e GameState geçildiğini doğrula
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  
  - [ ]* 9.3 Integration test: Tam akış (main → Menu → Lobby → Shop)
    - main() başlatıldığında current_scene_name == "MenuScene"
    - "YENİ OYUN" simüle edildiğinde current_scene_name == "LobbyScene"
    - "OYUNA BAŞLA" simüle edildiğinde current_scene_name == "ShopScene"
    - _Requirements: 1.1, 1.2, 1.3, 3.1, 5.1_

- [x] 10. Final checkpoint - Tüm testler geçmeli
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- `*` ile işaretli tasklar optional (hızlı MVP için atlanabilir)
- Her task spesifik gereksinimlere referans verir (traceability)
- Property testler design dokümanındaki Correctness Properties'i doğrular
- Unit testler spesifik örnekleri ve edge case'leri doğrular
- Integration testler end-to-end akışı doğrular
- Checkpointler incremental validation sağlar
- _bootstrap() lazy loading ile sadece gerektiğinde çağrılır
- Font initialization lazy olarak yapılır (pygame başlamadan önce değil)
