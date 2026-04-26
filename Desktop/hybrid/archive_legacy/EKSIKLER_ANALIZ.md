# run_game2.py Hybrid Architecture - Kapsamlı Eksikler Analizi (REVİZE)

## 🎯 Orijinal Tasarım Prensibi

**Scene'ler sadece görsel katman, döngü kontrolü run_game2.py'de.**

- run_game2.py: Game nesnesini yönetir, kendi loop'unu çalıştırır
- Modal wrapper'lar: Scene'leri modal olarak çağırır, içerde CoreGameState bridge yapar
- Scene'ler: CoreGameState ve AssetLoader bekler (scene sistemi böyle kurulmuş)

## 📊 Mevcut Durum

### ✅ Tamamlanmış Bileşenler

1. **Modal Wrapper'lar**
   - ✅ `ShopSceneModal` (scenes/shop_scene_modal.py)
   - ✅ `CombatSceneModal` (scenes/combat_scene_modal.py)
   - Her ikisi de CoreGameState ve AssetLoader bekliyor

2. **CoreGameState Bridge**
   - ✅ `CoreGameState` sınıfı mevcut (core/core_game_state.py)
   - Game instance'ını wrap ediyor
   - view_player_index, fast_mode, locked_coords_per_player yönetiyor

3. **Tam Özellikli Scene Sistemi**
   - ✅ `GameLoopScene` - Turn orchestration, AI turns, combat triggering
   - ✅ `ShopScene` - Kart satın alma UI'ı
   - ✅ `CombatScene` - Combat visualization
   - ✅ `LobbyScene` - Strategy selection
   - ✅ `GameOverScene` - Winner display
   - ✅ `SceneManager` - Scene transitions

4. **run_game2.py Temel Yapı**
   - ✅ pygame init, window, fonts
   - ✅ HybridGameState dataclass
   - ✅ build_game() fonksiyonu
   - ✅ render_main_screen() - BoardRenderer, hand panel, HUD
   - ✅ Game over detection ve display_game_over()
   - ✅ Restart functionality (R key)

### ❌ Eksik/Sorunlu Bileşenler

## 1. **Wrapper'lar CoreGameState Bridge Yapmıyor**

### Sorun:
- Mevcut wrapper'lar `CoreGameState` parametresi bekliyor
- Ama run_game2.py sadece `Game` nesnesini yönetiyor
- Wrapper'ın görevi: Game → CoreGameState bridge yapmak, dışarıya sızdırmamak

### Gerekli Değişiklikler:
```python
# ŞU AN (YANLIŞ):
class ShopSceneModal:
    @staticmethod
    def run_modal(core_game_state: CoreGameState, ...):
        # CoreGameState dışarıdan geliyor

# OLMASI GEREKEN:
class ShopSceneModal:
    @staticmethod
    def run_modal(game: Game, player: Player, screen, asset_loader, fonts):
        # İçerde CoreGameState oluştur
        core_game_state = CoreGameState(game)
        core_game_state.view_player_index = player.pid
        
        # Scene'i çağır
        scene = ShopScene(
            core_game_state=core_game_state,
            asset_loader=asset_loader,
            fonts=fonts
        )
        # ... modal loop
        
        # Dışarıya sadece sonuç döndür, CoreGameState sızdırma
        return {'purchased': [...], 'gold_spent': ...}
```

### Etkilenen Dosyalar:
- scenes/shop_scene_modal.py (signature değişikliği)
- scenes/combat_scene_modal.py (signature değişikliği)

---

## 2. **AssetLoader Initialization Eksik**

### Sorun:
- ShopScene ve CombatScene `AssetLoader` **zorunlu** bekliyor (ValueError fırlatır)
- run_game2.py'de AssetLoader instance'ı yok
- AssetLoader kart görsellerini yönetiyor

### Gerekli Değişiklikler:
```python
# run_game2.py'de ekle:
from scenes.asset_loader import AssetLoader

def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    
    # AssetLoader'ı başlat
    asset_loader = AssetLoader()
    asset_loader.load_all_card_images()  # Startup'ta yükle
    
    fonts = initialize_fonts()
    game = build_game()
    
    # main_game_loop'a asset_loader'ı geçir
    main_game_loop(game, screen, fonts, asset_loader)
```

### Etkilenen Dosyalar:
- run_game2.py (AssetLoader init ve main_game_loop signature)

---

## 3. **Modal Sahnelerin Çağrılmaması**

### Sorun:
- `step_turn_hybrid()` içinde ShopSceneModal.run_modal() çağrılmıyor (TODO)
- `step_turn_hybrid()` içinde CombatSceneModal.run_modal() çağrılmıyor (TODO)
- Oyuncu shop ve combat UI'larını göremez

### Gerekli Değişiklikler:
```python
def step_turn_hybrid(game: Game, state: HybridGameState, 
                     screen: pygame.Surface, fonts: dict, 
                     asset_loader: AssetLoader) -> None:
    # ...
    player = game.players[state.view_player]
    
    # Phase 1: Shop modal
    if player.alive:
        player.income()
        
        shop_result = ShopSceneModal.run_modal(
            game=game,
            player=player,
            screen=screen,
            asset_loader=asset_loader,
            fonts=fonts
        )
        
        # Interest zaten ShopScene.on_exit()'te uygulanıyor
        # player.apply_interest() - ÇAĞIRMA (duplicate olur)
    
    # Phase 2-4: Turn increment, AI turns, combat
    # ...
    
    # Phase 5: Combat modal
    combat_result = CombatSceneModal.run_modal(
        game=game,
        screen=screen,
        asset_loader=asset_loader,
        last_combat_results=game.last_combat_results
    )
```

### Etkilenen Dosyalar:
- run_game2.py (step_turn_hybrid fonksiyonu)
- scenes/shop_scene_modal.py (signature değişikliği)
- scenes/combat_scene_modal.py (signature değişikliği)

---

## 4. **Kart Yerleştirme (Placement) Sistemi Eksik**

### Sorun:
- Mouse ile hex'e tıklayıp kart yerleştirme yok
- Seçili kartı board'a koyma logic'i eksik
- Locked coordinates kontrolü eksik
- BoardRenderer'da hex click detection yok

### Gerekli Değişiklikler:

#### A. Hex Click Detection
```python
def get_clicked_hex(mouse_pos, board_origin, hex_size=40):
    """Mouse pozisyonundan tıklanan hex koordinatını bul.
    
    BoardRenderer'ın hex layout'unu kullanarak mouse pozisyonunu
    hex koordinatına çevir.
    """
    from ui.board_renderer_v3 import BoardRendererV3
    # BoardRenderer'ın hex_to_pixel metodunun tersini kullan
    # Tüm hex'leri iterate et, mouse ile collision check yap
    for q, r in BOARD_COORDS:
        hex_center = BoardRendererV3.hex_to_pixel(q, r, board_origin, hex_size)
        # Point-in-hexagon check
        if point_in_hexagon(mouse_pos, hex_center, hex_size):
            return (q, r)
    return None

def point_in_hexagon(point, center, size):
    """Bir noktanın hexagon içinde olup olmadığını kontrol et."""
    # Hexagon collision detection
    # Distance check veya vertex-based check
    dx = point[0] - center[0]
    dy = point[1] - center[1]
    return (dx*dx + dy*dy) <= (size * size)
```

#### B. Card Placement Logic
```python
def handle_card_placement(events, state, game, renderer):
    """Kart yerleştirme input'unu handle et."""
    player = game.players[state.view_player]
    
    for event in events:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Eğer kart seçiliyse
            if state.selected_hand_idx is not None:
                hex_coord = get_clicked_hex(event.pos, renderer.origin)
                
                if hex_coord and is_valid_placement(hex_coord, player, state):
                    # Kartı yerleştir
                    card = player.hand.pop(state.selected_hand_idx)
                    player.board.place_card(card, hex_coord, state.pending_rotation)
                    
                    # Locked coords'a ekle
                    state.locked_coords_per_player[player.pid].add(hex_coord)
                    
                    # Placement counter'ı artır
                    state.placed_this_turn += 1
                    
                    # Selection'ı temizle
                    state.selected_hand_idx = None
                    state.pending_rotation = 0
                    
                    print(f"✓ Card placed at {hex_coord}, rotation {state.pending_rotation}")
```

#### C. Placement Validation
```python
def is_valid_placement(hex_coord, player, state):
    """Yerleştirme geçerli mi kontrol et."""
    # Hex board'da mı?
    if hex_coord not in BOARD_COORDS:
        return False
    
    # Hex boş mu?
    if player.board.get_card_at(hex_coord):
        return False
    
    # Locked değil mi?
    if hex_coord in state.locked_coords_per_player.get(player.pid, set()):
        return False
    
    # Placement limit aşılmadı mı?
    if state.placed_this_turn >= PLACE_PER_TURN:
        return False
    
    return True
```

### Etkilenen Dosyalar:
- run_game2.py (handle_input fonksiyonu - placement logic ekle)
- run_game2.py (yeni helper fonksiyonlar: get_clicked_hex, point_in_hexagon, is_valid_placement)

---

## 5. **Placement Preview Eksik**

### Sorun:
- Seçili kart ile mouse hareket ettiğinde preview gösterilmiyor
- Hangi hex'e yerleştireceğini görmek zor

### Gerekli Değişiklikler:
```python
def render_main_screen(...):
    # ... normal rendering
    
    # Eğer kart seçiliyse ve mouse board üzerindeyse
    if state.selected_hand_idx is not None:
        mouse_pos = pygame.mouse.get_pos()
        hovered_hex = get_clicked_hex(mouse_pos, renderer.origin)
        
        if hovered_hex:
            # Preview kartı çiz (yarı saydam)
            card = player.hand[state.selected_hand_idx]
            
            # Geçerli yerleştirme mi kontrol et
            is_valid = is_valid_placement(hovered_hex, player, state)
            preview_color = (0, 255, 0, 100) if is_valid else (255, 0, 0, 100)
            
            # Hex highlight çiz
            hex_center = renderer.hex_to_pixel(*hovered_hex, renderer.origin)
            draw_hex_highlight(screen, hex_center, renderer.hex_size, preview_color)
            
            # Kart preview çiz (optional - daha advanced)
            # draw_card_preview(screen, card, hex_center, state.pending_rotation, alpha=128)
```

### Etkilenen Dosyalar:
- run_game2.py (render_main_screen - preview logic ekle)
- run_game2.py (yeni helper: draw_hex_highlight)

---

## 6. **handle_input Fonksiyonu Placement Logic Eksik**

### Sorun:
- Şu anki handle_input sadece TAB, 1-8, R, ESC, SPACE handle ediyor
- Mouse click ile kart yerleştirme logic'i yok
- Mouse click ile hand card selection var ama placement yok

### Gerekli Değişiklikler:
```python
def handle_input(events, state, game, renderer, screen, fonts):
    """Handle keyboard and mouse input."""
    player = game.players[state.view_player]
    
    for event in events:
        if event.type == pygame.KEYDOWN:
            # ... mevcut keyboard handling
            pass
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            
            # Left click
            if event.button == 1:
                # Önce hand card selection check et
                clicked_idx = _get_clicked_hand_card(mouse_pos, len(player.hand))
                if clicked_idx is not None:
                    # Toggle selection
                    if state.selected_hand_idx == clicked_idx:
                        state.selected_hand_idx = None
                        state.pending_rotation = 0
                    else:
                        state.selected_hand_idx = clicked_idx
                        state.pending_rotation = 0
                else:
                    # Hand'e tıklanmadı, board'a tıklandı mı?
                    if state.selected_hand_idx is not None:
                        hex_coord = get_clicked_hex(mouse_pos, renderer.origin)
                        if hex_coord and is_valid_placement(hex_coord, player, state):
                            # Kartı yerleştir
                            card = player.hand.pop(state.selected_hand_idx)
                            player.board.place_card(card, hex_coord, state.pending_rotation)
                            state.locked_coords_per_player[player.pid].add(hex_coord)
                            state.placed_this_turn += 1
                            state.selected_hand_idx = None
                            state.pending_rotation = 0
            
            # Right click: Rotate selected card
            elif event.button == 3:
                if state.selected_hand_idx is not None:
                    state.pending_rotation = (state.pending_rotation + 1) % 6
```

### Etkilenen Dosyalar:
- run_game2.py (handle_input fonksiyonu - mouse click logic genişlet)

---

## 📋 Öncelik Sırası (REVİZE)

### 🔴 Kritik (Oyun Oynanamaz)
1. **Wrapper Signature Değişikliği** - Game nesnesini alsın, içerde CoreGameState bridge yapsın
2. **AssetLoader Initialization** - run_game2.py'de AssetLoader başlat
3. **Modal Sahnelerin Çağrılması** - ShopSceneModal ve CombatSceneModal'ı step_turn_hybrid'de çağır
4. **Kart Yerleştirme Sistemi** - Mouse ile hex'e kart yerleştirme (hex click detection, placement logic, validation)

### 🟡 Önemli (Kullanılabilirlik)
5. **Placement Preview** - Seçili kart ile mouse preview (hex highlight)
6. **handle_input Genişletme** - Mouse click ile placement logic ekle

### 🟢 İyileştirme (Nice-to-have)
7. **Fast Mode** - Shop skip, AI auto-play
8. **Player Switching UI Feedback** - Active player highlight

### ⚪ Kapsam Dışı (Sonraki Spec)
- CyberRenderer proper kullanımı (optional parametre, şimdilik None geçilebilir)
- InputState abstraction (wrapper içinde InputState oluşturulabilir)
- Scene-based architecture migration (büyük refactor, ayrı spec gerekir)

---

## 🎯 Önerilen Yeni Spec

### Spec Adı: "run_game2-playable-integration"

### Kapsam:
1. **Wrapper Refactor** - Game → CoreGameState bridge (içerde yap, dışarıya sızdırma)
2. **AssetLoader Setup** - run_game2.py'de initialization
3. **Modal Integration** - ShopSceneModal ve CombatSceneModal çağrıları
4. **Placement System** - Hex click detection, placement logic, validation, preview

### Çıkarılanlar (Sonraki Spec'e):
- Scene-based architecture full migration (büyük refactor)
- Fast mode implementation (test feature)
- Advanced UI polish (nice-to-have)
- CyberRenderer integration (optional, şimdilik None)
- InputState abstraction (wrapper içinde handle edilebilir)

---

## 📝 Kritik Karar: Wrapper Signature

### Mevcut (YANLIŞ):
```python
class ShopSceneModal:
    @staticmethod
    def run_modal(core_game_state: CoreGameState, 
                  screen: pygame.Surface,
                  asset_loader: 'AssetLoader',
                  renderer: 'CyberRenderer' = None,
                  fonts: dict = None) -> Dict[str, Any]:
```

### Olması Gereken (DOĞRU):
```python
class ShopSceneModal:
    @staticmethod
    def run_modal(game: Game,
                  player: Player,
                  screen: pygame.Surface,
                  asset_loader: 'AssetLoader',
                  fonts: dict = None) -> Dict[str, Any]:
        # İçerde CoreGameState oluştur
        core_game_state = CoreGameState(game)
        core_game_state.view_player_index = player.pid
        
        # Scene'i çağır (scene CoreGameState bekliyor)
        scene = ShopScene(
            core_game_state=core_game_state,
            asset_loader=asset_loader,
            fonts=fonts
        )
        # ... modal loop
```

Bu yaklaşımla:
- ✅ run_game2.py temiz kalır (sadece Game kullanır)
- ✅ Wrapper bridge görevi yapar (Game → CoreGameState)
- ✅ Scene'ler değişmez (CoreGameState beklerler)
- ✅ Orijinal tasarım prensibi korunur (scene'ler sadece görsel katman)

---

## 📝 Notlar

### Orijinal Tasarım Prensibi (KORUNMALI)
- **Scene'ler sadece görsel katman** - UI rendering ve input handling
- **Döngü kontrolü run_game2.py'de** - Game loop, turn flow, state management
- **Wrapper'lar bridge görevi yapar** - Game → CoreGameState dönüşümü içerde
- **run_game2.py Game nesesiyle çalışır** - CoreGameState'i bilmez

### Mevcut Spec'in Durumu
- Task 1-6: ✅ Tamamlandı (temel yapı)
- Task 7: ✅ Tamamlandı (game over)
- **Ama**: Modal sahneler entegre edilmedi (TODO olarak bırakıldı)

### Neden TODO Bırakıldı?
- Spec'te "CoreGameState bridge" detaylandırılmamış
- AssetLoader dependency fark edilmemiş
- Placement sistemi detaylandırılmamış
- Wrapper signature'ı yanlış tasarlanmış (CoreGameState dışarıdan bekliyor)

### Kritik Fark: Wrapper'ın Rolü
**YANLIŞ Yaklaşım** (mevcut):
```
run_game2.py → CoreGameState oluştur → Wrapper'a geçir → Scene
```
Bu yaklaşımda run_game2.py CoreGameState'i bilmek zorunda.

**DOĞRU Yaklaşım** (olması gereken):
```
run_game2.py → Game → Wrapper → [içerde CoreGameState oluştur] → Scene
```
Bu yaklaşımda run_game2.py sadece Game'i bilir, wrapper bridge yapar.

### Sonuç
Yeni bir spec gerekli. Mevcut spec temel iskeleyi kurdu, ama:
1. Wrapper signature'ı yanlış (refactor gerekli)
2. AssetLoader eksik (initialization gerekli)
3. Modal çağrıları eksik (integration gerekli)
4. Placement sistemi eksik (implementation gerekli)

Bu eksikler tamamlanınca oyun oynanabilir hale gelecek.
