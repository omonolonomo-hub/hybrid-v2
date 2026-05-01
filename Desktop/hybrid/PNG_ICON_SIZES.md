# PNG İkon Boyutları

## 📏 Güncel Boyutlar

### Info Box (Kart Detay Paneli)

- **Kategori İkonu:** 20-22px (önceden 16px)
- **Stat İkonları:** 22-24px (önceden 16-18px)

### Minimap (Sol Panel)

- **Kategori İkonları:** 24px (önceden 18px)

### Lobby Panel

- **Rank İkonları:** 24-32px (değişmedi)

## 🎨 Kaynak Dosya Boyutu

**Önerilen:** 512x512 piksel

Bu boyut:

- ✅ Tüm kullanım alanları için yeterli
- ✅ Otomatik ölçeklendirmede keskin görünüm
- ✅ Performans açısından optimal
- ✅ Dosya boyutu makul (science.png: 38KB)

## 📊 Boyut Karşılaştırması

| Konum               | Eski Boyut | Yeni Boyut | Artış |
| ------------------- | ---------- | ---------- | ----- |
| Info Box (Kategori) | 16px       | 20-22px    | +37%  |
| Info Box (Stat)     | 16-18px    | 22-24px    | +33%  |
| Minimap             | 18px       | 24px       | +33%  |

## 🔧 Boyut Ayarlama

İkonlar hala küçük/büyük geliyorsa:

### Info Box - Kategori İkonu

**Dosya:** `v2/ui/info_box_new1.py`
**Satır:** ~448

```python
cat_icon_sz = max(20, int(22 * s))  # Bu değerleri artır/azalt
```

### Info Box - Stat İkonları

**Dosya:** `v2/ui/info_box_new1.py`
**Satır:** ~583

```python
icon_sz = max(int(22 * s), int(24 * s))  # Bu değerleri artır/azalt
```

### Minimap - Kategori İkonları

**Dosya:** `v2/ui/minimap_hud.py`
**Satır:** ~262

```python
icon_size = 24  # Bu değeri artır/azalt
```

## 💡 İpuçları

1. **Daha büyük ikonlar için:** Değerleri +4 veya +6 artırın
2. **Daha küçük ikonlar için:** Değerleri -2 veya -4 azaltın
3. **Test edin:** Her değişiklikten sonra oyunu başlatıp kontrol edin
4. **Oran koruyun:** Tüm yerlerde benzer oranda değişiklik yapın

## 🎯 Örnek Değişiklikler

### Çok Daha Büyük İkonlar İçin

```python
# Info Box Kategori
cat_icon_sz = max(28, int(30 * s))  # +40%

# Info Box Stat
icon_sz = max(int(28 * s), int(32 * s))  # +40%

# Minimap
icon_size = 32  # +33%
```

### Biraz Daha Büyük İkonlar İçin

```python
# Info Box Kategori
cat_icon_sz = max(24, int(26 * s))  # +20%

# Info Box Stat
icon_sz = max(int(26 * s), int(28 * s))  # +20%

# Minimap
icon_size = 28  # +17%
```

## 📝 Notlar

- `s` değişkeni render scale'i temsil eder (genellikle 2)
- `max()` fonksiyonu minimum boyutu garanti eder
- Boyutlar piksel cinsindendir
- PNG ikonlar otomatik olarak smooth scale ile ölçeklenir
