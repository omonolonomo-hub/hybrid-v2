# HexGridConfig Reset Eksikliği Düzeltmesi

**Tarih:** 2026-04-26  
**Identifier:** PATTERN MISMATCH  
**Durum:** ✅ Düzeltildi

## Sorun Tanımı

`HexGridConfig._DEFAULT_CONFIG` singleton pattern'i kullanıyor ancak `CardPool`'un aksine `reset()` metodu eksikti. Bu durum:

1. **Test isolation sorunu:** Aynı process içinde farklı `BOARD_RADIUS` değerleriyle test yazmak imkânsız
2. **Frozen binding sorunu:** `ShopScene._drop_dragged_card` ve `MinimapHUD._draw_hex_grid` içindeki `from v2.ui.hex_grid import VALID_HEX_COORDS` import'u, çağrı anında frozenset'i bağlıyor
3. **Dinamik config desteği bozuk:** `HexGridConfig.from_custom()` ile farklı config oluşturulsa bile, eski import'lar bunu görmez

### Örnek Sorun Senaryosu

```python
# ShopScene._drop_dragged_card içinde:
from v2.ui.hex_grid import VALID_HEX_COORDS, pixel_to_axial

# Bu import __getattr__ üzerinden get_default_config().valid_coords döndürüyor
# ve çağrı anında o değeri frozenset olarak bağlıyor.

# Daha sonra HexGridConfig.from_custom() ile farklı bir config oluşturulsa bile
# _drop_dragged_card bunu görmez — eski frozenset'i tutar.
```

## Düzeltme Protokolü

### 1. `hex_grid_config.py` - Reset Fonksiyonu Eklendi

```python
def reset_default_config() -> None:
    """
    Reset the default configuration singleton.
    
    This is primarily for test isolation — allows tests to run with
    different BOARD_RADIUS values in the same process without cross-contamination.
    
    Example:
        # In test teardown or setup
        reset_default_config()
        # Next call to get_default_config() will re-initialize from engine
    """
    global _DEFAULT_CONFIG
    _DEFAULT_CONFIG = None
```

### 2. `ShopScene` - Instance-Based Config

**Değişiklikler:**

```python
# Import eklendi
from v2.ui.hex_grid_config import HexGridConfig

# __init__ içinde instance oluşturuldu
def __init__(self, game_state: Optional[GameState] = None):
    super().__init__()
    self._game_state = game_state
    self._hex_config = HexGridConfig.from_engine()  # ← YENİ
    # ... rest of init

# _drop_dragged_card içinde lazy import kaldırıldı
def _drop_dragged_card(self) -> None:
    # HAYIR: from v2.ui.hex_grid import VALID_HEX_COORDS
    # EVET:
    if self.drag_state["source_panel"] != "hand":
        # ...
        return

    src_idx = self.drag_state["source_index"]
    drop_pos = self.drag_state["mouse_pos"]
    coord = pixel_to_axial(*drop_pos, self.camera)
    if coord in self._hex_config.valid_coords:  # ← Instance kullanımı
        # ...
```

### 3. `MinimapHUD` - Instance-Based Config

**Değişiklikler:**

```python
# Import eklendi
from v2.ui.hex_grid_config import HexGridConfig

# __init__ içinde instance oluşturuldu
def __init__(self, screen_w=Screen.W, screen_h=Screen.H):
    # ... existing init
    self._hex_config = HexGridConfig.from_engine()  # ← YENİ
    # ... rest of init

# _draw_hex_grid içinde lazy import kaldırıldı
def _draw_hex_grid(self, surface, cx, cy, size):
    # HAYIR: from v2.ui.hex_grid import VALID_HEX_COORDS
    # EVET:
    for q, r in self._hex_config.valid_coords:  # ← Instance kullanımı
        # ...
```

## Faydalar

### ✅ Test Isolation
```python
# Test setup
from v2.ui.hex_grid_config import reset_default_config

def test_with_custom_radius():
    reset_default_config()
    # Yeni BOARD_RADIUS ile test yap
    # Diğer testlerle çakışma yok
```

### ✅ Dinamik Hex Invalidation
```python
# "Wind card" örneği - runtime'da hex'leri devre dışı bırakma
base_config = HexGridConfig.from_engine()
disabled_hex = (1, 2)
new_coords = base_config.valid_coords - {disabled_hex}
wind_config = HexGridConfig.from_custom(base_config.board_radius, new_coords)

# ShopScene artık instance-based olduğu için:
shop_scene._hex_config = wind_config  # Dinamik değişim mümkün
```

### ✅ Tutarlı Pattern
`CardPool` ile aynı singleton pattern ve reset mekanizması:
- `CardPool.reset()` → `reset_default_config()`
- Her ikisi de test isolation için gerekli
- Her ikisi de aynı process içinde farklı config'lerle çalışabilir

## Etkilenen Dosyalar

1. ✅ `v2/ui/hex_grid_config.py` - `reset_default_config()` eklendi
2. ✅ `v2/scenes/shop.py` - Instance-based config kullanımı
3. ✅ `v2/ui/minimap_hud.py` - Instance-based config kullanımı

## Geriye Dönük Uyumluluk

- `__getattr__` backward compatibility layer korundu
- Eski kod `from v2.ui.hex_grid import VALID_HEX_COORDS` hâlâ çalışır
- Ancak yeni kod instance-based pattern kullanmalı

## Test Önerileri

```python
def test_reset_default_config():
    """Test that reset_default_config clears the singleton."""
    from v2.ui.hex_grid_config import get_default_config, reset_default_config
    
    # First call creates singleton
    config1 = get_default_config()
    
    # Reset clears it
    reset_default_config()
    
    # Next call creates new instance
    config2 = get_default_config()
    
    # They should be different instances
    assert config1 is not config2

def test_shop_scene_uses_instance_config():
    """Test that ShopScene uses instance-based config."""
    from v2.scenes.shop import ShopScene
    
    scene = ShopScene()
    assert hasattr(scene, '_hex_config')
    assert scene._hex_config is not None
```

## Sonuç

Bu düzeltme ile:
- ✅ Test isolation sağlandı
- ✅ Dinamik hex invalidation API'si çalışır hale geldi
- ✅ `CardPool` ile tutarlı pattern uygulandı
- ✅ Frozen binding sorunu çözüldü
- ✅ Runtime'da config değişimi mümkün

**Pattern:** Singleton + Reset + Instance-Based Access = Test-Friendly & Dynamic
