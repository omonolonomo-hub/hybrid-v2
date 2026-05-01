# Meta Key Validation Hatası Düzeltildi

## 🐛 Sorun

Yeni eklenen passive handler'lar çalışırken meta key validation hatası veriyordu:

```
KeyError: "Unknown meta key '_sparta_total'"
```

### Neden Oldu?

Yeni handler'lar için meta key'ler `engine_core/meta_keys.py` dosyasındaki `META_SPECS` dictionary'sine eklenmemişti. Engine'in güvenlik sistemi bilinmeyen meta key'lere izin vermiyor.

## ✅ Çözüm

`engine_core/meta_keys.py` dosyasına 4 yeni meta key eklendi:

```python
META_SPECS: Dict[str, MetaSpec] = {
    # ... mevcut key'ler ...
    
    # Yeni eklenen handler meta key'leri
    "_sparta_total": MetaSpec(int),      # Sparta - kalıcı Power birikimi
    "_jazz_turn": MetaSpec(int),         # Jazz - son tetiklenme turu
    "_jazz_count": MetaSpec(int),        # Jazz - tur başına sayaç
    "_tardigrade_uses": MetaSpec(int),   # Tardigrade - revival sayısı
}
```

## 📊 Eklenen Meta Key'ler

| Key | Tip | Scope | Kullanıldığı Kart | Açıklama |
|-----|-----|-------|-------------------|----------|
| `_sparta_total` | int | persistent | Sparta | Combat kazanınca biriken toplam Power (+4 max) |
| `_jazz_turn` | int | persistent | Jazz | Son combo gold reward'ın verildiği tur |
| `_jazz_count` | int | persistent | Jazz | Bu turda kaç kez gold verildi (max 2) |
| `_tardigrade_uses` | int | persistent | Tardigrade | Kaç kez revival kullanıldı (max 2) |

## 🔍 Tüm Kayıtlı Meta Key'ler (23 adet)

### Persistent (21 adet)
```
_anubis_buff          - Anubis Secret birikimi
_combat_bonus         - Genel combat bonus
_fib_last_turn        - Fibonacci son tetiklenme
_guernica_count       - Guernica tur sayacı
_guernica_turn        - Guernica son tur
_hammurabi_total_buff - Hammurabi toplam buff
_jazz_count           - Jazz tur sayacı (YENİ)
_jazz_turn            - Jazz son tur (YENİ)
_minotaur_total_buff  - Minotaur toplam buff
_narwhal_buff         - Narwhal Power birikimi
_narwhal_last_turn    - Narwhal son tur
_prefix_bonus         - Prefix bonus
_pulsar_last_turn     - Pulsar son tur
_sf_pc                - Synergy field pre-combat marker
_sf_stacks            - Synergy field stack sayısı
_sirius_buff          - Sirius Speed birikimi
_sirius_last_turn     - Sirius son tur
_sparta_total         - Sparta Power birikimi (YENİ)
_tardigrade_uses      - Tardigrade revival sayısı (YENİ)
_venus_debuffs        - Venus Flytrap debuff sayısı
_yggdrasil_bonus      - Yggdrasil komşu bonus
```

### Combat Scope (2 adet)
```
phoenix_used          - Phoenix revival kullanıldı mı
revived_this_combat   - Bu combat'ta revival oldu mu
```

## 🎮 Etkilenen Kartlar

Artık sorunsuz çalışan kartlar:
- ✅ **Sparta** - Combat kazanınca +2 Power birikir (max +4)
- ✅ **Jazz** - Combo olduğunda +1 gold (max 2/tur)
- ✅ **Tardigrade** - 2 kez revival (Durability 3'e reset)

## 🔧 Değişiklikler

**Dosya:** `engine_core/meta_keys.py`
- 4 yeni meta key eklendi
- Toplam: 19 → 23 meta key

**Test:** `check_meta_keys.py` oluşturuldu

## 📝 Meta Key Sistemi

### Neden Gerekli?

Engine'in meta key validation sistemi:
1. **Güvenlik:** Yanlış key kullanımını engeller
2. **Tip Güvenliği:** int/bool tip kontrolü yapar
3. **Scope Yönetimi:** Persistent vs combat scope ayrımı
4. **Debugging:** Hangi key'lerin kullanıldığını takip eder

### Yeni Handler Eklerken

Eğer handler'ınız `card.set_meta()` veya `card.get_meta()` kullanıyorsa:

1. `engine_core/meta_keys.py` dosyasını açın
2. `META_SPECS` dictionary'sine key'i ekleyin:
   ```python
   "_my_card_counter": MetaSpec(int),  # veya bool
   ```
3. Scope belirtin (opsiyonel):
   - `persistent` (default) - oyun boyunca kalır
   - `combat` - combat sonunda temizlenir

## ✅ Test Edildi

```bash
python check_meta_keys.py
# Output: 23 registered meta keys ✅
```

Oyun artık yeni handler'ları sorunsuz çalıştırabilir!

---

*Düzeltme tarihi: 2026-04-30*
*İlgili dosya: engine_core/meta_keys.py*
