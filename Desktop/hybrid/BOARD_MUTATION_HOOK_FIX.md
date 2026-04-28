# Board Mutation Hook Fix - StateStore Desenkronizasyon Çözümü

## Problem

StateStore'daki `_board_names` ve `_board_rotations` sözlükleri `Player.board.grid`'den bağımsız yaşıyordu. `Board.place()` ve `Board.remove()` çağrıldığında StateStore otomatik güncellenmiyordu, bu da UI'ın bazen gerçek board durumundan farklı bir snapshot göstermesine neden oluyordu.

## Çözüm Yaklaşımı

İki olası çözüm vardı:

1. **Board.place() ve Board.remove() içine StateStore.update_board() çağrısı gömmek**
2. **StateStore'daki board önbelleğini tamamen kaldırıp build_public_state() sırasında doğrudan Player.board.grid'i okumak**

**Seçilen çözüm:** İkinci yaklaşım (daha yavaş ama garantili güvenli)

## Uygulanan Değişiklikler

### 1. StateStore'dan Board Önbelleği Kaldırıldı (Zaten Yapılmıştı - H3-5)

`v2/core/state_store.py` içindeki `_board_names` ve `_board_rotations` sözlükleri zaten kaldırılmıştı. Board verisi artık `PublicState.active_player` üzerinden erişiliyor.

### 2. Board Mutation Callback Mekanizması Eklendi

`engine_core/board.py` içinde zaten mevcut olan `_mutation_callback` mekanizması GameState'e bağlandı:

```python
class Board:
    def __init__(self):
        # ...
        self._mutation_callback = None  # GameState tarafından set edilir
    
    def place(self, coord, card):
        # ... placement logic ...
        if self._mutation_callback is not None:
            self._mutation_callback()
    
    def remove(self, coord):
        # ... removal logic ...
        if self._mutation_callback is not None:
            self._mutation_callback()
    
    def clear_all(self):
        # ... clear logic ...
        if self._mutation_callback is not None:
            self._mutation_callback()
```

### 3. GameState'e Callback Hook Eklendi

`v2/core/game_state.py` içine yeni metodlar eklendi:

```python
class GameState:
    def hook_engine(self, engine):
        self._adapter = EngineAdapter(engine)
        self._attach_engine_signals()
        self._attach_board_mutation_callbacks()  # YENİ
    
    def _attach_board_mutation_callbacks(self):
        """Hook Board._mutation_callback to invalidate cache on direct board mutations."""
        if not self._adapter:
            return
        game = getattr(self._adapter, "_engine", None)
        if game is None:
            return
        
        # Hook mutation callback for all player boards
        for player in game.players:
            board = getattr(player, "board", None)
            if board is not None:
                # Bind callback that emits board_mutated signal
                board._mutation_callback = lambda pid=player.pid: self._on_direct_board_mutation(pid)
    
    def _on_direct_board_mutation(self, pid: int):
        """Handle direct board mutations (Board.place/remove called outside GameState).
        
        Emits board_mutated signal to ensure cache invalidation and UI updates.
        """
        if not self._adapter:
            return
        game = getattr(self._adapter, "_engine", None)
        if game is None or not hasattr(game, "signals"):
            # Fallback: direct cache invalidation if signals unavailable
            self._on_board_mutated(pid=pid)
            return
        
        # Emit signal to trigger normal invalidation flow
        game.signals.board_mutated.emit(pid=pid)
```

### 4. Cleanup Mekanizması Eklendi

Memory leak'leri önlemek için cleanup metoduna callback temizleme eklendi:

```python
def cleanup(self):
    """Explicitly cleanup resources. Call before discarding GameState instance."""
    self._detach_board_mutation_callbacks()  # YENİ
    self._detach_engine_signals()
    self._cached_public_state = None
    self._adapter = None

def _detach_board_mutation_callbacks(self):
    """Unhook Board._mutation_callback to prevent memory leaks."""
    if not self._adapter:
        return
    game = getattr(self._adapter, "_engine", None)
    if game is None:
        return
    
    # Clear mutation callbacks for all player boards
    for player in game.players:
        board = getattr(player, "board", None)
        if board is not None:
            board._mutation_callback = None
```

## Çalışma Prensibi

1. **GameState.hook_engine()** çağrıldığında, her oyuncunun board'una bir mutation callback atanır
2. **Board.place()** veya **Board.remove()** çağrıldığında, callback tetiklenir
3. Callback **board_mutated** sinyalini emit eder (pid ile birlikte)
4. Sinyal **GameState._on_board_mutated()** metodunu tetikler
5. Bu metod **UIAdapter** ve **GameState** cache'lerini invalidate eder
6. Bir sonraki **get_public_state()** çağrısı fresh data döner

## Avantajlar

✅ **Garantili Senkronizasyon** - Board mutasyonları her zaman cache invalidation tetikler  
✅ **Sinyal Bazlı Mimari** - Mevcut sinyal sistemine entegre  
✅ **Player-Specific Invalidation** - Sadece ilgili oyuncunun cache'i invalidate edilir  
✅ **Memory Leak Koruması** - Cleanup mekanizması ile callback'ler temizlenir  
✅ **Backward Compatible** - Mevcut kod değişmeden çalışmaya devam eder  

## Test Sonuçları

### Test 1: Board Mutation Callback Integration
```
✓ Player 0 board callback attached
✓ Player 1 board callback attached
✓ Initial board card count: 0
✓ Board count updated: 0 → 1
✓ New card visible in PublicState at (0, 0)
✓ Board count restored: 1 → 0
✓ Removed card no longer in PublicState
✓ Player 0 board callback cleaned up
✓ Player 1 board callback cleaned up
```

### Test 2: Signal Emission on Board Mutation
```
✓ Signal emitted with correct PID (place)
✓ Signal emitted with correct PID (remove)
✓ Signal emitted on clear_all
✓ Player 0 cache not invalidated by Player 1 mutation
Total signals emitted: 7
```

## Performans Notları

- **Board mutasyonları** artık sinyal emit eder (minimal overhead)
- **Cache invalidation** sadece ilgili oyuncu için yapılır
- **BFS hesabı** sadece board_mutated sinyalinde tetiklenir (economy_changed, inventory_changed gibi sinyaller BFS tetiklemez)
- **Granular cache invalidation** sayesinde gereksiz hesaplamalar önlenir

## Gelecek İyileştirmeler

1. **Batch Mutations** - Birden fazla board mutasyonunu tek bir sinyal ile gruplamak
2. **Diff-Based Updates** - Sadece değişen kartları UI'a göndermek
3. **Lazy Synergy Computation** - Synergy hesabını sadece gerektiğinde yapmak

## İlgili Dosyalar

- `engine_core/board.py` - Board sınıfı ve mutation callback
- `v2/core/game_state.py` - GameState ve callback hook mekanizması
- `v2/core/state_store.py` - StateStore (board önbelleği kaldırıldı)
- `v2/core/ui_adapter.py` - UIAdapter (granular cache invalidation)
- `test_board_mutation_hook.py` - Integration test
- `test_signal_integration.py` - Signal emission test
