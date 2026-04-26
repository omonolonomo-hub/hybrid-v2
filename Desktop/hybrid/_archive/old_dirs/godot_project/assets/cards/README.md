# Card Assets - Kart Görselleri

Bu klasöre kart görsellerini koy.

## Klasör Yapısı

```
assets/cards/
├── fronts/          # Ön yüz görselleri (altıgen)
│   ├── card_001_front.png
│   ├── card_002_front.png
│   └── ...
├── backs/           # Arka yüz görselleri (altıgen)
│   ├── card_001_back.png
│   ├── card_002_back.png
│   └── ...
└── README.md
```

## Dosya Adlandırma

### Ön Yüz (Front)
- Format: `{card_name}_front.png`
- Örnek: `Yggdrasil_front.png`
- Boyut: Önerilen 512x512 (altıgen içine sığacak)

### Arka Yüz (Back)
- Format: `{card_name}_back.png`
- Örnek: `Yggdrasil_back.png`
- Boyut: Önerilen 512x512

## cards.json Güncellemesi

`assets/data/cards.json` dosyasında her kart için:

```json
{
  "name": "Yggdrasil",
  "category": "Nature",
  "rarity": "5",
  "stats": {...},
  "passive_type": "synergy",
  "image_front": "res://assets/cards/fronts/Yggdrasil_front.png",
  "image_back": "res://assets/cards/backs/Yggdrasil_back.png"
}
```

## Otomatik Yükleme

BoardRenderer.gd otomatik olarak:
1. `card.image_front` varsa ön yüzü çizer
2. Yoksa sadece hex frame + stats çizer

## Test

1. Bir kart görseli ekle: `assets/cards/fronts/test_front.png`
2. `cards.json`'da ilgili kartın `image_front` alanını güncelle
3. Oyunu çalıştır - görsel hex içinde görünmeli

## Görsel Gereksinimleri

- **Format**: PNG (transparency destekli)
- **Boyut**: 512x512 veya 1024x1024
- **Şekil**: Kare (altıgen içine fit edilecek)
- **Arka plan**: Transparent veya solid color
- **DPI**: 72-150 (oyun için yeterli)

## Toplu İçe Aktarma

Eğer çok sayıda kart varsa, Python script ile otomatik:

```python
import json
import os

# cards.json oku
with open('assets/data/cards.json', 'r', encoding='utf-8') as f:
    cards = json.load(f)

# Her kart için image path ekle
for card in cards:
    name = card['name'].replace(' ', '_')
    card['image_front'] = f"res://assets/cards/fronts/{name}_front.png"
    card['image_back'] = f"res://assets/cards/backs/{name}_back.png"

# Kaydet
with open('assets/data/cards.json', 'w', encoding='utf-8') as f:
    json.dump(cards, f, indent=2, ensure_ascii=False)
```

## Placeholder Görseller

Eğer henüz görseller yoksa, placeholder kullan:
- Rarity renginde solid background
- Ortada kart adı
- Photoshop/GIMP ile hızlıca oluşturulabilir
