# Evolved Kart Asset Hatası Düzeltildi

## 🐛 Sorun

Oyun "Evolved" kartların arka yüz görsellerini yüklemeye çalışırken hata veriyordu:

```
FileNotFoundError: [AssetLoader] Eksik sprite: 
C:\Users\Özhan\Desktop\hybrid\v2\assets\sprites\cards/Evolved Pop Art_back.png
```

### Neden Oldu?

Evolved kartlar için ayrı görsel dosyaları yok. Örneğin:
- ❌ `Evolved Pop Art_back.png` (yok)
- ✅ `Pop Art_back.png` (var)

AssetLoader "Evolved Pop Art" ismini olduğu gibi kullanmaya çalışıyordu.

## ✅ Çözüm

`v2/assets/loader.py` dosyasında `get_card_front()` ve `get_card_back()` fonksiyonları güncellendi:

### Öncesi
```python
def get_card_back(self, card_name: str) -> pygame.Surface:
    file_name = _CARD_NAME_OVERRIDES.get(card_name, card_name)
    return self.get_sprite(f"cards/{file_name}_back.png")
```

### Sonrası
```python
def get_card_back(self, card_name: str) -> pygame.Surface:
    # Evolved kartlar için base kartın arka yüzünü kullan
    if card_name.startswith("Evolved "):
        base_name = card_name[8:]  # "Evolved " prefix'ini kaldır
        file_name = _CARD_NAME_OVERRIDES.get(base_name, base_name)
    else:
        file_name = _CARD_NAME_OVERRIDES.get(card_name, card_name)
    return self.get_sprite(f"cards/{file_name}_back.png")
```

## 🎯 Mantık

1. Kart ismi "Evolved " ile başlıyorsa → prefix'i kaldır
2. Base kart ismini kullanarak görseli yükle
3. Örnek: "Evolved Pop Art" → "Pop Art" → `Pop Art_back.png`

## ✅ Test Edildi

```python
✅ Evolved Pop Art      -> Pop Art
✅ Evolved Odin         -> Odin
✅ Evolved Isaac Newton -> Isaac Newton
✅ Pop Art              -> Pop Art (değişmez)
✅ Odin                 -> Odin (değişmez)
```

## 📝 Etkilenen Kartlar

Tüm evolved kartlar artık doğru görselleri yükleyecek:
- Evolved Pop Art
- Evolved Odin
- Evolved Isaac Newton
- Evolved Fibonacci Sequence
- ... ve diğer tüm evolved kartlar

## 🔧 Değişiklikler

**Dosya:** `v2/assets/loader.py`
- `get_card_front()` güncellendi
- `get_card_back()` güncellendi
- Toplam: ~10 satır değişiklik

**Test:** `test_evolved_card_assets.py` oluşturuldu

## 🎮 Oyun Etkisi

- ✅ Evolved kartlar artık board'da görüntülenebilir
- ✅ Kart flip animasyonları çalışır
- ✅ FileNotFoundError hatası düzeltildi
- ✅ Oyun akışı kesintisiz devam eder

---

*Düzeltme tarihi: 2026-04-30*
*İlgili dosya: v2/assets/loader.py*
