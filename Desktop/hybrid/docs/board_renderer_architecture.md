# BoardRenderer Architecture

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        ShopScene                             │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Before Refactoring                                 │    │
│  │  ─────────────────                                  │    │
│  │  • _board_flips: dict[coord, CardFlip]             │    │
│  │  • _add_board_flip(coord, state, card_data)        │    │
│  │  • _fallback_card_surface(color, w, h)             │    │
│  │  • update(): ~40 lines of flip management          │    │
│  │  • draw(): manual flip rendering loop              │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  After Refactoring                                  │    │
│  │  ────────────────                                   │    │
│  │  • board_renderer: BoardRenderer                    │    │
│  │  • update(): 2 lines (sync + update)               │    │
│  │  • draw(): 1 line (board_renderer.draw)            │    │
│  └────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           │ delegates to                     │
│                           ▼                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │              BoardRenderer                          │    │
│  │              ──────────────                         │    │
│  │  Public API:                                        │    │
│  │  • sync(board_cards, state, cam_state)             │    │
│  │  • update(dt_ms, cam_state, mouse_pos)             │    │
│  │  • draw(surface)                                    │    │
│  │  • get_hover_coord(pos) -> coord | None            │    │
│  │  • clear()                                          │    │
│  │  • remove(coord)                                    │    │
│  │                                                      │    │
│  │  Internal:                                          │    │
│  │  • _flips: dict[coord, CardFlip]                   │    │
│  │  • _add_board_flip(coord, board_cards, state, cam) │    │
│  │  • _fallback_card_surface(color, w, h)             │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### Frame Update Cycle

```
┌──────────────┐
│  ShopScene   │
│   .update()  │
└──────┬───────┘
       │
       │ 1. Get current board state
       ▼
┌──────────────────────────────────────┐
│  state = self._current_public_state()│
│  current_board = active_player.board │
│  cam_state = self.camera.get_state() │
└──────┬───────────────────────────────┘
       │
       │ 2. Sync board renderer
       ▼
┌──────────────────────────────────────┐
│  self.board_renderer.sync(           │
│      current_board,                   │
│      state,                           │
│      cam_state                        │
│  )                                    │
└──────┬───────────────────────────────┘
       │
       │ 3. Update animations & hover
       ▼
┌──────────────────────────────────────┐
│  self.board_renderer.update(         │
│      dt_ms,                           │
│      cam_state,                       │
│      pygame.mouse.get_pos()           │
│  )                                    │
└───────────────────────────────────────┘
```

### Render Cycle

```
┌──────────────┐
│  ShopScene   │
│   .draw()    │
└──────┬───────┘
       │
       │ 1. Render background & grid
       ▼
┌──────────────────────────────────────┐
│  BackgroundManager.render()          │
│  render_hex_grid_cached()            │
└──────┬───────────────────────────────┘
       │
       │ 2. Render all board cards
       ▼
┌──────────────────────────────────────┐
│  self.board_renderer.draw(surface)   │
│                                       │
│  Internally:                          │
│  • Sorts flips by hover_progress     │
│  • Renders each flip.render(surface) │
└──────┬───────────────────────────────┘
       │
       │ 3. Render synergy lines & UI
       ▼
┌──────────────────────────────────────┐
│  render_synergy_lines_cached()       │
│  shop_panel.render()                 │
│  hand_panel.render()                 │
│  ...                                  │
└───────────────────────────────────────┘
```

## BoardRenderer State Machine

```
┌─────────────────────────────────────────────────────────┐
│                    BoardRenderer                         │
│                                                          │
│  _flips: dict[coord, CardFlip]                          │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  sync(board_cards, state, cam_state)           │    │
│  │  ────────────────────────────────────           │    │
│  │  1. Remove stale coords                        │    │
│  │     for coord in _flips:                       │    │
│  │         if coord not in board_cards:           │    │
│  │             del _flips[coord]                  │    │
│  │                                                 │    │
│  │  2. Add missing coords                         │    │
│  │     for coord in board_cards:                  │    │
│  │         if coord not in _flips:                │    │
│  │             _add_board_flip(coord, ...)        │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  update(dt_ms, cam_state, mouse_pos)           │    │
│  │  ────────────────────────────────────           │    │
│  │  for coord, flip in _flips.items():            │    │
│  │      1. Update dest_rect (camera transform)    │    │
│  │      2. Check hover (collidepoint)             │    │
│  │         if hover: flip.hover_start()           │    │
│  │         else: flip.hover_end()                 │    │
│  │      3. Update animation: flip.update(dt_ms)   │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  draw(surface)                                  │    │
│  │  ─────────────                                  │    │
│  │  for _, flip in sorted(_flips.items(),         │    │
│  │                        key=hover_progress):     │    │
│  │      flip.render(surface)                      │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Benefits Summary

### 1. **Separation of Concerns**
- ShopScene: High-level scene orchestration
- BoardRenderer: Low-level card flip management

### 2. **Reduced Complexity**
- ShopScene.update(): 40 lines → 2 lines
- ShopScene.draw(): Manual loop → 1 line call

### 3. **Improved Testability**
- BoardRenderer can be tested in isolation
- Mock dependencies easily
- 11 comprehensive unit tests

### 4. **Better Maintainability**
- Clear API boundaries
- Self-documenting method names
- Easier to extend/modify

### 5. **Reusability**
- BoardRenderer can be used in other scenes
- Combat scene, replay viewer, etc.

## Performance Characteristics

### Memory
- **Before**: ~N CardFlip objects in ShopScene._board_flips
- **After**: ~N CardFlip objects in BoardRenderer._flips
- **Impact**: No change (same objects, different container)

### CPU
- **Before**: Manual loops in update() and draw()
- **After**: Same loops, encapsulated in BoardRenderer
- **Impact**: No change (same operations, better organization)

### Future Optimizations
- Spatial partitioning for hover detection
- Dirty flag for flip updates
- Batch rendering optimizations
- All can be done in BoardRenderer without touching ShopScene

## API Reference

### BoardRenderer.sync()
```python
def sync(
    board_cards: dict[tuple[int, int], dict],
    state: PublicState,
    cam_state: CameraState,
) -> None:
    """Synchronize flip dict with current board state."""
```

### BoardRenderer.update()
```python
def update(
    dt_ms: float,
    cam_state: CameraState,
    mouse_pos: tuple[int, int]
) -> None:
    """Update all flip animations and hover states."""
```

### BoardRenderer.draw()
```python
def draw(surface: pygame.Surface) -> None:
    """Render all flips in sorted order."""
```

### BoardRenderer.get_hover_coord()
```python
def get_hover_coord(pos: tuple[int, int]) -> Optional[tuple[int, int]]:
    """Get the coordinate of the card at the given position."""
```

### BoardRenderer.clear()
```python
def clear() -> None:
    """Clear all flips (useful for view sync)."""
```

### BoardRenderer.remove()
```python
def remove(coord: tuple[int, int]) -> None:
    """Remove a specific flip by coordinate."""
```
