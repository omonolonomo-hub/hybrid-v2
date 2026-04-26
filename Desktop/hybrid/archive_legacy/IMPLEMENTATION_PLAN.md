# run_game2.py Playable Integration - Implementation Plan

## 🎯 Hedef
run_game2.py'yi oynanabilir hale getirmek - ShopScene ve CombatScene modal olarak çalışsın, oyuncu kart satın alıp yerleştirebilsin.

## 📋 Üç Adımlı Plan

### ✅ Adım 1: AssetLoader Durumu (TAMAMLANDI)

**Sonuç**: AssetLoader ZORUNLU, ama initialization kolay.

```python
# ShopScene.__init__ ve CombatScene.__init__ her ikisi de:
if asset_loader is None:
    raise ValueError("asset_loader is required")
```

**Initialization**:
```python
from scenes.asset_loader import AssetLoader
asset_loader = AssetLoader("assets/cards")  # Tek satır!
```

---

### 🔧 Adım 2: Wrapper Dosyalarını Yeniden Yaz

#### A. ShopSceneModal Signature

**Mevcut (YANLIŞ)**:
```python
def run_modal(core_game_state: CoreGameState, 
              screen: pygame.Surface,
              asset_loader: 'AssetLoader',
              renderer: 'CyberRenderer' = None,
              fonts: dict = None) -> Dict[str, Any]:
```

**Yeni (DOĞRU)**:
```python
def run_modal(game: Game,
              player: Player, 
              screen: pygame.Surface,
              asset_loader: 'AssetLoader',
              fonts: dict = None) -> Dict[str, Any]:
    """Run shop scene as modal dialog.
    
    Args:
        game: Game instance (NOT CoreGameState)
        player: Current player
        screen: Pygame surface for rendering
        asset_loader: AssetLoader instance (REQUIRED)
        fonts: Optional font dictionary
        
    Returns:
        {
            'purchased': List[str],  # Card names bought
            'gold_spent': int,
            'completed': bool
        }
    """
    # İçerde CoreGameState oluştur (bridge)
    core_game_state = CoreGameState(game)
    core_game_state.view_player_index = player.pid
    
    # Scene'i oluştur
    scene = ShopScene(
        core_game_state=core_game_state,
        action_system=None,  # Modal'da gerekmez
        animation_system=None,
        asset_loader=asset_loader,
        renderer=None,  # Scene içinde oluşturulur
        fonts=fonts
    )
    
    # Mock SceneManager
    modal_done = {'value': False}
    def mock_request_transition(target_scene: str):
        modal_done['value'] = True
    scene.scene_manager = SimpleNamespace(request_transition=mock_request_transition)
    
    # on_enter() çağır
    scene.on_enter()
    
    # Modal loop
    clock = pygame.time.Clock()
    while not modal_done['value']:
        dt = clock.tick(60)
        events = pygame.event.get()
        
        # Quit check
        for event in events:
            if event.type == pygame.QUIT:
                modal_done['value'] = True
                break
        
        if modal_done['value']:
            break
        
        # InputState oluştur (wrapper içinde)
        from core.input_state import InputState
        input_state = InputState(events)
        
        # Scene update
        scene.handle_input(input_state)
        scene.update(dt)
        scene.draw(screen)
        pygame.display.flip()
    
    # on_exit() çağır (interest burada uygulanır)
    scene.on_exit()
    
    # Sonuçları hesapla ve döndür
    # ... (mevcut kod)
```

#### B. CombatSceneModal Signature

**Mevcut (YANLIŞ)**:
```python
def run_modal(core_game_state: CoreGameState,
              screen: pygame.Surface,
              asset_loader: 'AssetLoader',
              last_combat_results: list = None) -> Dict[str, Any]:
```

**Yeni (DOĞRU)**:
```python
def run_modal(game: Game,
              screen: pygame.Surface,
              asset_loader: 'AssetLoader',
              last_combat_results: list = None) -> Dict[str, Any]:
    """Run combat scene as modal dialog.
    
    Args:
        game: Game instance (NOT CoreGameState)
        screen: Pygame surface for rendering (1600x960)
        asset_loader: AssetLoader instance (REQUIRED)
        last_combat_results: Combat results data
        
    Returns:
        {
            'viewed': bool,
            'skipped': bool
        }
    """
    # İçerde CoreGameState oluştur (bridge)
    core_game_state = CoreGameState(game)
    
    # Temporary surface for CombatScene (1920x1080)
    combat_surface = pygame.Surface((1920, 1080))
    
    # Scene'i oluştur
    scene = CombatScene(
        core_game_state=core_game_state,
        action_system=None,
        animation_system=None,
        asset_loader=asset_loader
    )
    
    # Mock SceneManager
    def mock_request_transition(target_scene: str):
        pass  # No-op for modal
    scene.scene_manager = SimpleNamespace(request_transition=mock_request_transition)
    
    # on_enter() çağır
    scene.on_enter()
    
    # Modal loop
    clock = pygame.time.Clock()
    modal_done = False
    viewed = True
    skipped = False
    
    while not modal_done:
        dt = clock.tick(60)
        events = pygame.event.get()
        
        # Exit checks
        for event in events:
            if event.type == pygame.QUIT:
                modal_done = True
                skipped = True
                break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    modal_done = True
                    break
                elif event.key == pygame.K_ESCAPE:
                    modal_done = True
                    skipped = True
                    break
        
        if modal_done:
            break
        
        # InputState oluştur
        from core.input_state import InputState
        input_state = InputState(events)
        
        # Scene update
        scene.handle_input(input_state)
        scene.update(dt)
        scene.draw(combat_surface)
        
        # Scale down to 1600x960
        scaled = pygame.transform.scale(combat_surface, (1600, 960))
        screen.blit(scaled, (0, 0))
        pygame.display.flip()
    
    # on_exit() çağır
    scene.on_exit()
    
    return {'viewed': viewed, 'skipped': skipped}
```

---

### 🎮 Adım 3: run_game2.py'de Değişiklikler

#### A. main() Fonksiyonu - AssetLoader Ekle

```python
def main():
    """Entry point for run_game2.py"""
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption(TITLE)
    
    # Initialize fonts once
    fonts = initialize_fonts()
    
    # Initialize AssetLoader (REQUIRED for modal scenes)
    from scenes.asset_loader import AssetLoader
    asset_loader = AssetLoader("assets/cards")
    
    # Build game
    game = build_game()
    
    # Run main loop (asset_loader parametresi ekle)
    main_game_loop(game, screen, fonts, asset_loader)
    
    sys.exit()
```

#### B. main_game_loop() Signature Değişikliği

```python
def main_game_loop(game: Game, screen: pygame.Surface, fonts: dict, 
                   asset_loader: 'AssetLoader') -> None:
    """Main hybrid game loop combining run_game.py logic with modal scenes."""
    # ... (mevcut kod)
    
    # handle_input çağrısına asset_loader ekle
    if not game_over:
        handle_input(events, state, game, renderer, screen, fonts, asset_loader)
```

#### C. handle_input() Signature Değişikliği

```python
def handle_input(events: list, state: HybridGameState, game: Game,
                 renderer: BoardRenderer, screen: pygame.Surface, fonts: dict,
                 asset_loader: 'AssetLoader') -> None:
    """Handle keyboard and mouse input."""
    # ... (mevcut kod)
    
    # SPACE key handler'da asset_loader geçir
    if event.key == pygame.K_SPACE:
        step_turn_hybrid(game, state, screen, fonts, asset_loader)
```

#### D. step_turn_hybrid() - Modal Çağrıları Ekle

```python
def step_turn_hybrid(game: Game, state: HybridGameState, 
                     screen: pygame.Surface, fonts: dict,
                     asset_loader: 'AssetLoader') -> None:
    """Execute one complete turn with modal scene integration."""
    
    # Reset turn state
    state.selected_hand_idx = None
    state.pending_rotation = 0
    state.placed_this_turn = 0
    
    # Check game over before turn
    alive = [p for p in game.players if p.alive]
    if len(alive) <= 1 or game.turn >= 50:
        return
    
    # Phase 1: Shop modal
    clear_passive_trigger_log()
    
    player = game.players[state.view_player]
    if player.alive:
        # Give income
        player.income()
        
        # ✅ SHOP MODAL ÇAĞRISI (TODO kaldırıldı)
        from scenes.shop_scene_modal import ShopSceneModal
        shop_result = ShopSceneModal.run_modal(
            game=game,
            player=player,
            screen=screen,
            asset_loader=asset_loader,
            fonts=fonts
        )
        
        # Interest zaten ShopScene.on_exit()'te uygulandı
        # player.apply_interest() - ÇAĞIRMA!
        
        # Check copy strengthening
        player.check_copy_strengthening(
            game.turn + 1, trigger_passive_fn=trigger_passive
        )
    
    # Phase 2: Increment turn
    game.turn += 1
    
    # Phase 3: AI player turns
    from engine_core.ai import AI
    for p in game.players:
        if not p.alive or p.pid == state.view_player:
            continue
        
        # ... (mevcut AI logic)
    
    # Phase 4: Combat phase
    game.combat_phase()
    
    # Phase 5: Combat modal
    # ✅ COMBAT MODAL ÇAĞRISI (TODO kaldırıldı)
    from scenes.combat_scene_modal import CombatSceneModal
    combat_result = CombatSceneModal.run_modal(
        game=game,
        screen=screen,
        asset_loader=asset_loader,
        last_combat_results=game.last_combat_results
    )
    
    # Phase 6: Cleanup
    for pid in state.locked_coords_per_player:
        state.locked_coords_per_player[pid] = set()
```

---

## 📝 Değişiklik Özeti

### Dosyalar:
1. `scenes/shop_scene_modal.py` - Signature değişikliği, CoreGameState bridge içerde
2. `scenes/combat_scene_modal.py` - Signature değişikliği, CoreGameState bridge içerde
3. `run_game2.py` - 4 fonksiyon değişikliği:
   - `main()` - AssetLoader init
   - `main_game_loop()` - asset_loader parametresi
   - `handle_input()` - asset_loader parametresi
   - `step_turn_hybrid()` - Modal çağrıları ekle

### Satır Sayısı:
- Wrapper'lar: ~150 satır (her biri ~75 satır)
- run_game2.py: ~20 satır değişiklik

### Süre Tahmini:
- Adım 2 (Wrapper'lar): 15 dakika
- Adım 3 (run_game2.py): 10 dakika
- Test: 5 dakika
- **Toplam: 30 dakika**

---

## ⚠️ Kritik Notlar

1. **CoreGameState Bridge**: Wrapper içinde yapılır, dışarıya sızdırılmaz
2. **Interest Duplicate**: ShopScene.on_exit() zaten interest uygular, step_turn_hybrid'de ÇAĞIRMA
3. **InputState**: Wrapper içinde oluşturulur, run_game2.py bilmez
4. **AssetLoader**: Zorunlu, ama initialization kolay (tek satır)
5. **Renderer**: None geçilebilir, scene içinde oluşturulur

---

## 🚀 Sonraki Adım: Placement System

Bu değişikliklerden sonra oyun çalışır ama kart yerleştirme eksik olur.
Placement system ayrı bir task olarak paralel yazılabilir.
