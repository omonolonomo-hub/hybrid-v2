# Synergy Lines Kaybolma Sorunu - Çözüldü

**Tarih:** 2026-04-28  
**Sorun:** Hexgrid üzerindeki synergy lineları kart yerleştirmeden sonra kayboluyordu.

## Sorunun Kök Nedeni

`BoardSurfaceCache` sınıfında cache invalidation mantığında bir yarış durumu (race condition) vardı:

1. Kart yerleştirildiğinde `board_mutated` sinyali tetikleniyor
2. Signal handler `mark_board_dirty()` çağırıyor → `_board_dirty = True`
3. Render döngüsünde:
   - `render_hex_grid_cached()` → `get_grid()` çağrılıyor
   - `get_grid()` board'u yeniden çiziyor ve `_last_board_key` güncelleniyor
   - `_board_dirty` ve `_camera_dirty` flag'leri temizleniyor
   - `render_synergy_lines_cached()` → `get_synergy_geom()` çağrılıyor
   - `get_synergy_geom()` kontrol ediyor:
     - `board_key == _last_board_key` (✓ eşit, çünkü `get_grid()` güncelledi)
     - `_board_dirty == False` (✓ False, çünkü `get_grid()` temizledi)
     - Sonuç: Synergy geometry yeniden oluşturulmuyor!

## Çözüm

`BoardSurfaceCache` içinde grid ve synergy geometry için **ayrı cache key'leri** kullanmak:

### Değişiklikler

**v2/ui/board_surface_cache.py:**

1. Yeni slot'lar eklendi:
   ```python
   "_last_synergy_board_key",
   "_last_synergy_cam_key",
   ```

2. `__init__` metodunda başlatıldı:
   ```python
   self._last_synergy_board_key: Optional[frozenset[Coord]] = None
   self._last_synergy_cam_key: Optional[Tuple[float, float, float]] = None
   ```

3. `get_synergy_geom()` metodu güncellendi:
   - `_last_cam_key` yerine `_last_synergy_cam_key` kullanıyor
   - `_last_board_key` yerine `_last_synergy_board_key` kullanıyor
   - Kendi key'lerini güncelliyor
   - Dirty flag'leri temizliyor

## Sonuç

Artık `get_grid()` ve `get_synergy_geom()` birbirinden bağımsız cache key'leri kullanıyor. Bu sayede:

- `get_grid()` çağrıldığında grid cache'i güncelleniyor
- `get_synergy_geom()` çağrıldığında synergy geometry cache'i bağımsız olarak güncelleniyor
- Her iki metod da dirty flag'leri kontrol edebiliyor
- Synergy line'ları kart yerleştirmeden sonra kaybolmuyor

## Test

Düzeltme minimal bir test ile doğrulandı:
- Kart yerleştirme simüle edildi
- `get_grid()` ve `get_synergy_geom()` sırayla çağrıldı
- Synergy geometry'nin doğru şekilde yeniden oluşturulduğu doğrulandı

✅ Sorun çözüldü!
