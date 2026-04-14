# Bug Düzeltmeleri Özet Raporu

**Tarih:** 29 Mart 2026  
**Toplam Düzeltme:** 13 adet  
**Test Durumu:** Tüm düzeltmeler test edildi ve doğrulandı  
**Simülasyon:** 1000 oyun başarıyla tamamlandı  

---

## Düzeltilen Buglar

### 1. Draw Count Reporting (Double Counting)
**Dosya:** `engine_core/autochess_sim_v06.py` (~2308-2320)

**Problem:** Beraberlik durumunda `stats["draws"]` her oyuncu için ayrı artırılıyordu, toplam raporlarda 2 katı görünüyordu.

**Çözüm:** Raporlama katmanında `match_draws = sum(res["draws"].values()) // 2` hesaplaması eklendi.

**Sonuç:** Gerçek beraberlik sayısı doğru raporlanıyor.

---

### 2. Combo Context for Passive Abilities
**Dosya:** `engine_core/autochess_sim_v06.py` (~2010-2075)

**Problem:** Athena, Ballet, Nebula, Albert Einstein pasifleri combo context'e bakıyordu ama `_ctx` sadece `{"turn": _turn}` içeriyordu.

**Çözüm:** Combat phase'de combo hesaplaması pre_combat trigger'larından ÖNCE yapılıyor ve context'e ekleniyor:
- `combo_count`: combo puanları
- `combo_group`: dominant grup
- `combo_target_category`: en yaygın kategori

**Sonuç:** Combo-based pasifler doğru tetikleniyor.

---

### 3. Ragnarök Encoding Issue
**Dosya:** `engine_core/autochess_sim_v06.py` (~1189-1190, ~1255-1285)

**Problem:** `Ragnarök` (ö harfi) Windows console'da `Ragnark`'a dönüşüyordu, handler lookup başarısız oluyordu.

**Çözüm:** Dual approach:
1. `trigger_passive()` içinde ASCII-safe fallback
2. Handler hem `"Ragnarök"` hem `"Ragnark"` altında kayıtlı

**Sonuç:** Özel karakterli kartlar doğru çalışıyor.

---

### 4. GOLD_CAP Dead Code
**Dosya:** `engine_core/autochess_sim_v06.py`, `tools/`, `tests/`

**Problem:** `GOLD_CAP = 50` tanımlıydı ama hiçbir yerde kullanılmıyordu.

**Çözüm:** GOLD_CAP tamamen kaldırıldı, tüm referanslar temizlendi.

**Sonuç:** Unlimited gold economy açıkça belgelendi.

---

### 5. _deal_starting_hands Pool Tracking
**Dosya:** `engine_core/autochess_sim_v06.py` (~1922-1938)

**Problem:** Başlangıç kartları dağıtılırken `market.pool_copies` düşürülmüyordu.

**Çözüm:** Kartlar tek tek dağıtılıyor, her kart için pool_copies düşürülüyor, 3-kopya limiti respekt ediliyor.

**Sonuç:** Pool inventory doğru takip ediliyor, erken oyunda kopya limiti aşılmıyor.

---

### 6. passive_type="none" Log Noise
**Dosya:** `engine_core/autochess_sim_v06.py` (~1244-1254)

**Problem:** `trigger_passive()` her pasif için loglama yapıyordu, `passive_type="none"` kartlar da dahil.

**Çözüm:** Early return guard eklendi: `if card.passive_type == "none": return 0`

**Sonuç:** Log gürültüsü önemli ölçüde azaldı, sadece gerçek pasifler loglanıyor.

---

### 7. Board.place coord_index Cleanup
**Dosya:** `engine_core/autochess_sim_v06.py` (~332-338)

**Problem:** `Board.place()` eski kartın `coord_index` kaydını temizlemiyordu, evolution sırasında memory leak oluşuyordu.

**Çözüm:** 
```python
old = self.grid.get(coord)
if old is not None:
    self.coord_index.pop(id(old), None)
```

**Sonuç:** `_find_coord()` kullanan pasifler (Odin, Yggdrasil, Fungus, etc.) doğru çalışıyor.

---

### 8. Evolution Copy Tracking Reset
**Dosya:** `engine_core/autochess_sim_v06.py` (~1520-1523)

**Problem:** Evolution sonrasında `copy_applied` ve `copy_turns` temizlenmiyordu, aynı karttan tekrar toplandığında copy strengthening çalışmıyordu.

**Çözüm:**
```python
self.copy_applied.pop(base_name, None)
self.copy_turns.pop(base_name, None)
```

**Sonuç:** Evolution sonrası copy mekanizması yeniden çalışabiliyor.

---

### 9. return_unsold Hand Overflow
**Dosya:** `engine_core/autochess_sim_v06.py` (~2012-2014)

**Problem:** `newly_bought = player.hand[hand_before_count:]` slice'ı hand overflow durumunda yanlış kartları içeriyordu.

**Çözüm:** `_window_bought` tracking kullanılıyor: `_market.return_unsold(player)`

**Sonuç:** Hand overflow durumunda doğru kartlar pool'a geri dönüyor.

---

### 10. combo_group Calculation
**Dosya:** `engine_core/autochess_sim_v06.py` (~2069-2108)

**Problem:** `combo_group = alive_a[0].dominant_group()` sadece ilk kartın grubunu alıyordu.

**Çözüm:** Counter ile frekans hesabı:
```python
groups = [c.dominant_group() for c in alive]
combo_group = Counter(groups).most_common(1)[0][0]
```

**Sonuç:** Athena ve Ballet pasifleri doğru tetikleniyor.

---

### 11. Fibonacci Sequence win_streak Fix
**Dosya:** `engine_core/autochess_sim_v06.py` (~682-695)

**Problem:** `combat_win` trigger'ı çağrıldığında `win_streak` henüz güncellenmemişti, ilk kazançta 0 veriyordu.

**Çözüm:** `current_streak = streak + 1` kullanılıyor (mevcut kazanç sayılıyor).

**Sonuç:** 
- İlk kazanç: 1 puan (önceden 0)
- İkinci ardışık kazanç: 2 puan
- Üçüncü+ ardışık kazanç: 3 puan (cap)

---

### 12. Yggdrasil and _ Prefix Bonuses in Combat
**Dosya:** `engine_core/autochess_sim_v06.py` (~387-430)

**Problem:** Yggdrasil ve diğer `_` prefix'li bonuslar (`_yggdrasil_bonus`, `_narwhal_buff`, `_sirius_buff`, etc.) combat'ta kullanılmıyordu. `total_power()` bu bonusları kasıtlı olarak hariç tutuyordu.

**Çözüm:** `resolve_single_combat()` içinde `_` prefix'li bonuslar toplanıp 6 edge'e eşit dağıtılıyor:
```python
bonus_total = sum(v for k, v in card.stats.items() if str(k).startswith("_") and isinstance(v, int))
bonus_per_edge = bonus_total // 6
```

**Sonuç:** 
- Yggdrasil komşu kartlara verdiği bonus artık combat'ta etkili
- Narwhal, Sirius, Pulsar gibi buff veren pasifler combat'a katkı sağlıyor
- Bonuslar tüm edge'lere eşit dağıtılıyor

---

### 13. Warrior Strategy Differentiation
**Dosya:** `engine_core/autochess_sim_v06.py` (~1630-1690)

**Problem:** Warrior ve tempo stratejileri identikti - ikisi de `_buy_warrior()` kullanıyordu ve sadece `total_power()` bazlı kart seçiyordu.

**Çözüm:** Warrior için yeni, sofistike bir strateji:
- EXISTENCE grubu odaklı (Power, Durability, Size, Speed)
- Power/Durability dengesi gözeten scoring
- Board composition'a göre adaptif (offense vs defense ihtiyacı)
- Rarity bonusları ile daha akıllı seçim

**Scoring Formülü:**
```python
score = total_power * 1.0 + existence_stats * 0.5 + balance_bonus + rarity_bonus
```

**Sonuç:** 
- Warrior artık tempo'dan farklı bir strateji
- EXISTENCE grubuna odaklanıyor
- Power/Durability dengesini optimize ediyor
- Daha taktiksel kart seçimi yapıyor

---

## Test Sonuçları

### Unit Tests
Tüm düzeltmeler için özel test senaryoları yazıldı ve başarıyla geçti.

### Integration Test
1000 oyunluk simülasyon hatasız tamamlandı:
- **Log Dosyası:** `output/logs/simulation_log.txt` (~15.8 MB)
- **Oyuncu Sayısı:** 8
- **Seed:** 2024
- **Sonuç:** Tüm düzeltmeler stabil çalışıyor

---

## Etki Analizi

### Performans
- Log boyutu optimize edildi (passive_type="none" düzeltmesi)
- Memory leak önlendi (coord_index temizleme)

### Gameplay
- Combo-based pasifler artık çalışıyor (Athena, Ballet)
- Fibonacci Sequence dengeli hale geldi
- Pool tracking doğru (market ekonomisi sağlıklı)

### Kod Kalitesi
- Dead code temizlendi (GOLD_CAP)
- Encoding sorunları çözüldü (Ragnarök)
- Belgelendirme iyileştirildi

---

## Sonuç

13 kritik bug düzeltildi ve test edildi. Simülasyon motoru artık daha stabil, doğru ve belgelenmiş durumda. Tüm düzeltmeler production-ready.

**Son Güncelleme:** 29 Mart 2026
