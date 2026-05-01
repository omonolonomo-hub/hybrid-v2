# PNG İkonlar Klasörü

Bu klasör, oyunda kullanılan PNG formatındaki ikonları içerir.

## Kategori İkonları

Aşağıdaki kategori ikonlarını bu klasöre eklemeniz gerekiyor:

- `science.png` - Science kategorisi için
- `mythology.png` - Mythology & Gods kategorisi için
- `art.png` - Art & Culture kategorisi için
- `nature.png` - Nature & Creatures kategorisi için
- `cosmos.png` - Cosmos kategorisi için
- `history.png` - History & Civilizations kategorisi için

## Genel İkonlar

Oyunda kullanılan diğer ikonlar:

- `heart.png` - Can (HP)
- `gold.png` - Para / Altın
- `skull.png` - Ölüm
- `bolt.png` - Enerji
- `sword.png` - Saldırı
- `shield.png` - Savunma
- `fire.png` - Win-streak
- `crown.png` - 1. sıra
- `medal.png` - 2. sıra
- `award.png` - 3. sıra
- `fist.png` - Power
- `expand.png` - Size
- `magnet.png` - Gravity
- `music.png` - Harmony
- `broadcast.png` - Spread
- `gem.png` - Prestige

## İkon Özellikleri

- **Format:** PNG (şeffaf arka plan)
- **Boyut:** Minimum 64x64 piksel (daha büyük olabilir, otomatik ölçeklendirilir)
- **Renk:** Tam renkli veya tek renk (kod içinde renk tonu uygulanabilir)
- **Arka Plan:** Şeffaf (alpha channel)

## Kullanım

```python
from v2.ui import icon_loader

# Kategori ikonu çiz
icon_loader.render_icon(
    surface=my_surface,
    icon_name="Science",
    size=32,
    pos=(100, 100),
    is_category=True,
    shadow=True
)

# Genel ikon çiz
icon_loader.render_icon(
    surface=my_surface,
    icon_name="HEART",
    size=24,
    pos=(200, 200),
    is_category=False,
    color_tint=(255, 0, 0),  # Kırmızı ton
    shadow=True
)
```

## Gönderdiğiniz İkonu Kullanma

Gönderdiğiniz resmi (bilim/science ikonu) şu şekilde kullanabilirsiniz:

1. Resmi `science.png` olarak bu klasöre kaydedin
2. Kod otomatik olarak bu ikonu "Science" kategorisi için kullanacak
3. İkon otomatik olarak gerekli boyuta ölçeklendirilecek

## Font Awesome'dan PNG'ye Geçiş

Eski kod Font Awesome (TTF) kullanıyordu:

```python
icon_font = font_cache.icons(size)
icon_char = font_cache.ICONS.get("ATOM", "?")
icon_surf = icon_font.render(icon_char, True, color)
```

Yeni kod PNG kullanıyor:

```python
icon_loader.render_icon(surface, "Science", size, pos, is_category=True)
```

## Avantajlar

✅ Daha estetik ve özelleştirilebilir ikonlar
✅ Tam renkli ve detaylı grafikler
✅ Font bağımlılığı yok
✅ Kolay değiştirme ve güncelleme
