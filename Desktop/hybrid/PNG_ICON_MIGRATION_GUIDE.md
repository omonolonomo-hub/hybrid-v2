# PNG İkon Geçiş Rehberi

Font Awesome (TTF) ikonlarından PNG ikonlarına geçiş için adım adım rehber.

## 1. Hazırlık

### İkon Klasörünü Oluşturun

```bash
mkdir -p v2/assets/icons
```

### PNG İkonlarınızı Ekleyin

Gönderdiğiniz science ikonunu ve diğer kategori ikonlarını `v2/assets/icons/` klasörüne ekleyin:

- `science.png` ✅ (gönderdiğiniz ikon)
- `mythology.png`
- `art.png`
- `nature.png`
- `cosmos.png`
- `history.png`

## 2. Kod Değişiklikleri

### A) info_box_new1.py Güncellemesi

**Dosya:** `v2/ui/info_box_new1.py`

**Satır ~450 civarı - ÖNCEKİ KOD:**

```python
try:
    icon_font = font_cache.icons(cat_icon_sz)
    icon_char = font_cache.ICONS.get(cat_icon_key, "?")
    shadow_surf = icon_font.render(icon_char, True, (0, 0, 0))
    shadow_surf.set_alpha(int(255 * self._alpha))
    surface.blit(shadow_surf, (inner.x + 1, icy + 1))
    icon_surf = icon_font.render(icon_char, True, cat_color)
    icon_surf.set_alpha(int(255 * self._alpha))
    surface.blit(icon_surf, (inner.x, icy))
except pygame.error:
    pass
```

**YENİ KOD:**

```python
from v2.ui import icon_loader

# PNG ikon çiz
icon_surf = icon_loader.get_icon(card.category, cat_icon_sz, is_category=True)
if icon_surf:
    icon_surf = icon_surf.copy()
    icon_surf.set_alpha(int(255 * self._alpha))
    # Gölge
    shadow_surf = icon_surf.copy()
    shadow_surf.fill((0, 0, 0, 128), special_flags=pygame.BLEND_RGBA_MULT)
    surface.blit(shadow_surf, (inner.x + 1, icy + 1))
    # Ana ikon
    surface.blit(icon_surf, (inner.x, icy))
```

### B) lobby_panel.py Güncellemesi

**Dosya:** `v2/ui/lobby_panel.py`

**Satır ~220 civarı - ÖNCEKİ KOD:**

```python
icon_char = font_cache.ICONS.get(icon_name, "?")
icon_size_hd = int(avatar_size_hd * 0.32)
icon_font = font_cache.icons(icon_size_hd)
icon_surf = icon_font.render(icon_char, True, rank_col)
icon_rect = icon_surf.get_rect(center=(center_hd, int(center_hd * 0.68)))
```

**YENİ KOD:**

```python
from v2.ui import icon_loader

icon_size_hd = int(avatar_size_hd * 0.32)
icon_surf = icon_loader.get_icon(icon_name, icon_size_hd, is_category=False)
if icon_surf:
    # Renk tonu uygula
    icon_surf = icon_surf.copy()
    icon_surf.fill(rank_col + (255,), special_flags=pygame.BLEND_RGBA_MULT)
    icon_rect = icon_surf.get_rect(center=(center_hd, int(center_hd * 0.68)))
    avatar_hd.blit(icon_surf, icon_rect)
```

## 3. Import Eklemeleri

Her dosyanın başına şunu ekleyin:

```python
from v2.ui import icon_loader
```

## 4. Test

### Basit Test Scripti

```python
import pygame
from v2.ui import icon_loader

pygame.init()
screen = pygame.display.set_mode((800, 600))

# Science ikonunu test et
icon_loader.render_icon(
    surface=screen,
    icon_name="Science",
    size=64,
    pos=(100, 100),
    is_category=True,
    shadow=True
)

pygame.display.flip()
pygame.time.wait(3000)
pygame.quit()
```

## 5. Fallback Mekanizması

Eğer PNG dosyası bulunamazsa, sistem otomatik olarak "?" karakteri gösterir. Bu sayede eksik ikonlar oyunu çökertmez.

## 6. Performans

PNG ikonlar cache'lenir, yani her ikon sadece bir kez yüklenir ve bellekte tutulur. Bu sayede performans kaybı olmaz.

## 7. Eski Font Awesome Kodunu Kaldırma (Opsiyonel)

Tüm PNG ikonları ekledikten sonra:

1. `v2/constants.py` içindeki `FONT_ICONS = "fa-solid.otf"` satırını kaldırabilirsiniz
2. `v2/ui/font_cache.py` içindeki `icons()` fonksiyonunu kaldırabilirsiniz
3. `v2/assets/fonts/fa-solid.otf` dosyasını silebilirsiniz

**UYARI:** Önce tüm kullanımları PNG'ye çevirdiğinizden emin olun!

## 8. Kategori İkon Eşlemeleri

`icon_loader.py` içinde tanımlı:

```python
CATEGORY_ICONS = {
    "Mythology & Gods": "mythology.png",
    "Art & Culture": "art.png",
    "Nature & Creatures": "nature.png",
    "Cosmos": "cosmos.png",
    "Science": "science.png",  # ✅ Gönderdiğiniz ikon
    "History & Civilizations": "history.png",
}
```

## 9. Yeni İkon Ekleme

Yeni bir kategori veya ikon eklemek için:

1. PNG dosyasını `v2/assets/icons/` klasörüne ekleyin
2. `icon_loader.py` içindeki ilgili sözlüğe ekleyin:
   ```python
   CATEGORY_ICONS["Yeni Kategori"] = "yeni_kategori.png"
   ```

## 10. Renk Tonu Uygulama

PNG ikonlarına renk tonu uygulamak için:

```python
icon_loader.render_icon(
    surface=surface,
    icon_name="Science",
    size=32,
    pos=(100, 100),
    is_category=True,
    color_tint=(0, 174, 210),  # Cyan ton
    shadow=True
)
```

## Özet

✅ `icon_loader.py` oluşturuldu
✅ PNG ikonlar için klasör yapısı hazır
✅ Kullanım örnekleri hazır
✅ Fallback mekanizması var
✅ Cache sistemi var

**Şimdi yapmanız gereken:**

1. PNG ikonlarınızı `v2/assets/icons/` klasörüne ekleyin
2. İlgili dosyalardaki kodu güncelleyin
3. Test edin!
