# Hex Card Flip Animation Implementation

## Overview

ShopScene'de **SADECE hex card görselleri** kullanılıyor. Tüm dikdörtgen çizimler kaldırıldı ve kartlar tamamen hex placeholder'lar veya asset'lerden yüklenen hex görseller ile render ediliyor.

## Critical Design Decision

**NO RECTANGLES POLICY**: ShopCard.draw metodu artık hiçbir pygame.draw.rect çağrısı içermiyor. Sadece hex card surface'leri flip animasyonu ile çiziliyor.

## Implementation Details

### 1. Asset Loading (`_load_card_assets`)

```python
def _load_card_assets(self):
    """Load or create hex card front/back assets."""
```

- `assets/images/card_front.png` ve `card_back.png` dosyalarını yüklemeye çalışır
- Dosyalar bulunamazsa, otomatik olarak **detaylı** placeholder hex kartlar oluşturur
- Placeholder kartlar:
  - Front: Cyan neon çerçeveli altıgen (glow efekti ile)
  - Back: Magenta/Pink neon çerçeveli altıgen (glow efekti ile)
  - Her ikisi de "FRONT" / "BACK" etiketi + "HEX CARD" alt yazısı
  - Köşe dekorasyonları
  - İç içe hex desenler

### 2. Enhanced Placeholder Creation (`_create_hex_placeholder`)

```python
def _create_hex_placeholder(self, color: tuple, label: str) -> pygame.Surface:
    """Create a placeholder hexagonal card surface with detailed design."""
```

Özellikler:
- Çoklu hex border'lar (glow efekti)
- İç hex deseni
- Text glow efekti
- Köşe dekorasyonları (neon circles)
- Gradient-like alpha blending

### 3. Modernized Draw Method (`ShopCard.draw`)

**CRITICAL CHANGES:**

```python
# OLD (REMOVED): pygame.draw.rect calls
# NEW: Only hex surface rendering

# Full 180-degree flip
scale_x = abs(math.cos(flip_value * math.pi))  # NOT math.pi/2!

# Center-based positioning
center_x = draw_rect.centerx
center_y = draw_rect.centery
scaled_x = center_x - scaled_width // 2
scaled_y = center_y - original_height // 2
```

**Key Features:**
- No fallback to rectangles
- Emergency warning if hex assets missing
- Center-based positioning (no edge sliding)
- Full 180-degree rotation feel
- Fade alpha support

### 4. UIState Extensions

`on_enter()` metodunda yeni alanlar:

```python
self.ui_state.hovered_card_idx = None  # Hangi kart hover ediliyor
self.ui_state.card_flip_states = []    # Her kart için flip değeri (0.0-1.0)
```

### 5. Flip Animation Logic (`update`)

```python
flip_speed = 0.1  # Flip hızı per frame

for idx in range(len(self.ui_state.card_flip_states)):
    if idx == self.ui_state.hovered_card_idx:
        target = 1.0  # Arka yüz
    else:
        target = 0.0  # Ön yüz
    
    # Yumuşak interpolasyon
    current = self.ui_state.card_flip_states[idx]
    self.ui_state.card_flip_states[idx] += (target - current) * flip_speed
```

## Animation Phases (Full 180°)

1. **flip_value = 0.0**: Tam ön yüz görünür (scale_x = 1.0)
2. **flip_value = 0.25**: Kart daralıyor (scale_x = 0.707)
3. **flip_value = 0.5**: Kart en dar noktada, yüz değişimi (scale_x = 0.0)
4. **flip_value = 0.75**: Kart genişliyor (scale_x = 0.707)
5. **flip_value = 1.0**: Tam arka yüz görünür (scale_x = 1.0)

**Math Formula:**
```python
scale_x = abs(math.cos(flip_value * π))
```

Bu formül tam 180 derece dönüş hissi verir (π/2 değil, π kullanılıyor).

## Visual Result

### Without Assets (Placeholder Mode)
- Cyan hex kartlar (FRONT)
- Magenta hex kartlar (BACK)
- Glow efektleri
- Köşe dekorasyonları
- Smooth flip animasyonu

### With Assets
- Custom hex card images
- Same flip animation
- Same center-based positioning

## File Structure

```
scenes/
  shop_scene.py          # Ana implementasyon (NO RECTANGLES!)
assets/
  images/
    card_front.png       # (Opsiyonel) Ön yüz hex görseli
    card_back.png        # (Opsiyonel) Arka yüz hex görseli
test_hex_cards.py        # Test scripti (180° rotation)
docs/
  HEX_CARD_FLIP_IMPLEMENTATION.md  # Bu dosya
```

## Testing

Test scripti ile animasyonu test etmek için:

```bash
python test_hex_cards.py
```

Kontroller:
- Fare ile kartın üzerine gelin → Full 180° flip animasyonu başlar
- ESC → Çıkış

Ana oyunu test etmek için:

```bash
python main.py
```

Shop sahnesinde kartların üzerine gelin → Hex kartlar flip olacak

## Error Handling

- `FileNotFoundError`: Asset dosyaları bulunamazsa otomatik placeholder oluşturulur
- `os.path.exists()`: Dosya varlığı kontrol edilir
- `try-except`: Asset yükleme hataları yakalanır ve loglanır
- Minimum genişlik kontrolü: `scaled_width < 1` durumunda 1'e ayarlanır
- **Emergency fallback**: Hex assets yoksa "NO HEX ASSETS" uyarısı gösterilir

## Performance Notes

- Flip animasyonları her frame'de güncellenir
- Smooth interpolation kullanılır (ani geçişler yok)
- Sadece hover edilen kart flip olur, diğerleri 0.0'a döner
- Asset'ler bir kez yüklenir ve cache'lenir
- Placeholder'lar init sırasında oluşturulur

## Removed Features

❌ **Kaldırılan (Artık Yok):**
- `pygame.draw.rect` çağrıları
- Dikdörtgen çerçeveler
- Renderer fallback'leri (dikdörtgen için)
- Rarity color borders (dikdörtgen)
- Standard card rendering

✅ **Yeni (Sadece Bunlar Var):**
- Hex surface rendering
- Flip animation
- Center-based positioning
- Placeholder hex cards
- Full 180° rotation

## Integration with Action System

Flip animasyonları UI state'te tutulur (THROWAWAY):
- Scene transition'da sıfırlanır
- CoreGameState'i etkilemez
- Sadece görsel feedback sağlar

## Compatibility

- ✅ Asset'ler yoksa: Placeholder'lar otomatik oluşturulur
- ✅ Renderer parametresi: Artık kullanılmıyor (hex only)
- ✅ Backward compatible: Eski kod çalışmaya devam eder (hex ile)
- ❌ Rectangle rendering: Tamamen kaldırıldı

## Future Improvements

1. Kart içeriği ön yüzde gösterilebilir (card name, stats)
2. Arka yüzde farklı bilgiler (lore, description)
3. Particle effects on flip completion
4. Sound effects on flip
5. Multiple flip modes (vertical, diagonal)
6. Custom hex shapes per rarity

## Visual Comparison

### Before (Old Rectangle System)
```
┌─────────────┐
│  CARD NAME  │  ← Rectangle
│  Stats...   │
└─────────────┘
```

### After (New Hex System)
```
    ╱─────╲
   ╱       ╲
  │  FRONT  │  ← Hexagon
   ╲       ╱
    ╲─────╱
```

## Code Example

```python
# Draw hex card with flip
shop_card.draw(
    surf=screen,
    fonts=self.fonts,
    player=player,
    timer=self.ui_state.time,
    fade_alpha=255,
    flip_value=0.7,  # 70% flipped
    card_front_img=self.card_front_img,  # Hex image
    card_back_img=self.card_back_img,    # Hex image
    renderer=None  # Not used anymore
)
```

Result: Hex card at 70% flip, showing back side, centered, no rectangles!
