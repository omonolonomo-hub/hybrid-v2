# 🎯 Sinerji-Delta Tabanlı AI Yerleştirme Sistemi

**Tarih:** 2026-05-07  
**Durum:** ✅ Tamamlandı ve Entegre Edildi  
**Modül:** `engine_core/ai/synergy_placement.py`

---

## 📋 Özet

Autochess Hybrid projesinde yapay zeka botlarına **sinerji odaklı kart yerleştirme** yeteneği kazandırıldı. Botlar artık sadece bireysel kart gücüne değil, tahtadaki **sinerji gruplarından kazanacakları puan artışına (Synergy Delta)** bakarak karar veriyor.

---

## 🎯 Problem

**Önceki Durum:**

- AI botları kart yerleştirirken sadece `card.total_power()` değerine bakıyordu
- Tahtadaki BFS tabanlı sinerji gruplarını (CONNECTION, SPEED, POWER vb.) göz ardı ediyordu
- Zayıf yerleştirme kararları → düşük sinerji puanları → kayıp

**Hedef:**

- Yerleştirme öncesi ve sonrası sinerji farkını (ΔSynergy) hesaplamak
- En yüksek sinerji katkısını sağlayan koordinatı seçmek
- Oyunun aşamasına göre (erken/orta/geç) sinerji ağırlığını dinamik ayarlamak

---

## 🏗️ Mimari Tasarım

### Single Source of Truth (SST)

```
engine_core/synergy.py
  └─ compute_synergy()          [Tek yetkili BFS hesaplayıcısı]
       ↑
       │
engine_core/ai/synergy_placement.py
  ├─ compute_delta_synergy()    [ΔSynergy = after - before]
  ├─ score_placement()          [Score = base_power + W × ΔSynergy]
  ├─ best_coord_for_card()      [En iyi koordinat seçimi]
  └─ place_cards_synergy_aware() [Tam pipeline]
       ↑
       │
engine_core/ai/strategies/*.py
  └─ place_cards()              [Her strateji bu pipeline'ı çağırır]
```

### Güvenlik Garantileri

✅ **Board Mutasyonu Yok**

- Geçici `dict` kopyası kullanılır (`fake_grid`)
- `Board.place()` / `Board.remove()` çağrılmaz
- StateStore cache desync riski **sıfır**

✅ **Rollback Gerekmez**

- Simülasyon ana board'u etkilemez
- Her koordinat denemesi bağımsız

---

## 📐 Skor Formülü

```python
Score = (base_power_weight × card.total_power()) + (W_synergy(turn) × ΔSynergy)
```

### Parametreler

| Parametre           | Açıklama                               | Varsayılan |
| ------------------- | -------------------------------------- | ---------- |
| `base_power_weight` | Kart gücü ağırlığı                     | 1.0        |
| `W_synergy(turn)`   | Sinerji ağırlığı (oyun aşamasına göre) | 1.5 - 3.0  |
| `ΔSynergy`          | Sinerji değişimi (after - before)      | Hesaplanır |

### Oyun Aşaması Ağırlıkları

```python
@dataclass
class SynergyWeightSchedule:
    early_turns:  int   = 6      # Greed phase
    mid_turns:    int   = 15     # Spike phase
    weight_early: float = 1.5    # Tahta kurulum
    weight_mid:   float = 2.0    # Sinerji etkin
    weight_late:  float = 3.0    # Sinerji belirleyici
```

---

## 🎮 Strateji Bazlı Ağırlıklar

Her strateji için özelleştirilmiş ağırlık çizelgeleri:

| Strateji        | Erken | Orta | Geç | Karakter            |
| --------------- | ----- | ---- | --- | ------------------- |
| **Warrior**     | 1.0   | 1.5  | 2.0 | Bireysel güç odaklı |
| **Builder**     | 2.0   | 2.5  | 3.5 | Combo master        |
| **Economist**   | 1.2   | 2.0  | 2.5 | Dengeli             |
| **Balancer**    | 1.5   | 2.5  | 4.0 | Geç oyun agresif    |
| **Tempo**       | 1.0   | 1.8  | 2.8 | Erken baskı         |
| **Evolver**     | 1.5   | 2.0  | 3.0 | Evrim zincirleri    |
| **Rare Hunter** | 1.0   | 1.5  | 2.5 | Nadir kart gücü     |
| **Random**      | 1.5   | 2.0  | 3.0 | Varsayılan          |

---

## 🔧 Kullanım Örnekleri

### 1. Basit Kullanım (Herhangi Bir Stratejiden)

```python
from engine_core.ai.synergy_placement import place_cards_synergy_aware

def place_cards(self, player, rng=None, **kwargs):
    place_cards_synergy_aware(player)
```

### 2. Özelleştirilmiş Ağırlıklar

```python
from engine_core.ai.synergy_placement import (
    place_cards_synergy_aware,
    SynergyWeightSchedule
)

def place_cards(self, player, rng=None, **kwargs):
    schedule = SynergyWeightSchedule(
        weight_early=1.0,
        weight_mid=2.5,
        weight_late=4.0
    )
    place_cards_synergy_aware(player, schedule=schedule)
```

### 3. Strateji Bazlı Otomatik Seçim

```python
from engine_core.ai.synergy_placement import (
    place_cards_synergy_aware,
    schedule_for
)

def place_cards(self, player, rng=None, **kwargs):
    schedule = schedule_for(player.strategy)  # Otomatik
    place_cards_synergy_aware(player, schedule=schedule)
```

### 4. Sadece Delta Hesabı

```python
from engine_core.ai.synergy_placement import compute_delta_synergy

delta = compute_delta_synergy(player.board, coord, card)
if delta > 10:
    print(f"Bu yerleşim +{delta} sinerji kazandırır!")
```

### 5. Batch Hesaplama (Performans)

```python
from engine_core.ai.synergy_placement import compute_delta_synergy_batch

free_coords = player.board.free_coords()
deltas = compute_delta_synergy_batch(player.board, card, free_coords)

best_coord = max(deltas, key=deltas.get)
print(f"En iyi koordinat: {best_coord} (Δ={deltas[best_coord]})")
```

---

## 📊 Performans Optimizasyonları

### 1. Batch Hesaplama

- `synergy_before` bir kez hesaplanır
- Tüm koordinatlar aynı baseline'ı kullanır
- **O(N)** yerine **O(1)** baseline hesabı

### 2. Koordinat Limiti

```python
place_cards_synergy_aware(player, max_coord_check=10)
```

- İlk 10 boş koordinatı dener
- Büyük tahtalar için hız/kalite dengesi

### 3. Geçici Dict Kopyası

```python
temp_grid = dict(current_grid)  # Shallow copy
temp_grid[coord] = card         # Simülasyon
```

- Deep copy gerekmez (Card immutable)
- Hafıza ve CPU tasarrufu

---

## 🧪 Test Kapsamı

**Test Dosyası:** `tests/test_synergy_placement.py`

### Test Kategorileri

1. **Delta Hesaplama**
   - Boş tahta → delta = 0
   - Komşu eşleşmesi → delta > 0
   - Board mutasyonu yok

2. **Batch Hesaplama**
   - Çoklu koordinat
   - `synergy_before` parametresi

3. **Skor Fonksiyonu**
   - Formül doğrulaması
   - Ağırlık etkisi

4. **En İyi Koordinat**
   - Sinerji önceliği
   - `max_check` limiti

5. **Pipeline Entegrasyonu**
   - Kart yerleştirme
   - `place_limit` kontrolü
   - Özel çizelge

6. **Ağırlık Çizelgesi**
   - Oyun aşaması geçişleri
   - İnterpolasyon
   - Strateji bazlı

7. **StateStore Güvenliği**
   - Grid mutasyonu yok
   - coord_index korunuyor

8. **Edge Cases**
   - Boş el
   - Dolu tahta
   - Boş koordinat listesi

### Test Çalıştırma

```bash
# Tüm testler
pytest tests/test_synergy_placement.py -v

# Sadece delta testleri
pytest tests/test_synergy_placement.py -k "delta" -v

# Coverage raporu
pytest tests/test_synergy_placement.py --cov=engine_core.ai.synergy_placement
```

---

## 🔄 Entegre Edilen Stratejiler

Tüm AI stratejileri yeni sisteme geçirildi:

### ✅ Güncellenmiş Stratejiler

1. **Warrior** → `schedule_for("warrior")`
2. **Builder** → `schedule_for("builder")` + synergy_matrix
3. **Economist** → `schedule_for("economist")`
4. **Balancer** → `schedule_for("balancer")`
5. **Tempo** → `schedule_for("tempo")`
6. **Evolver** → `schedule_for("evolver")`
7. **Rare Hunter** → `schedule_for("rare_hunter")`
8. **Random** → `schedule_for("random")`

### Özel Durum: Builder

Builder stratejisi ek olarak `BuilderSynergyMatrix` kullanır:

```python
def place_cards(self, player, rng=None, **kwargs):
    from engine_core.ai.synergy_placement import place_cards_synergy_aware, schedule_for
    schedule = schedule_for("builder")
    place_cards_synergy_aware(player, schedule=schedule)

    # Builder'a özel: geçmiş combo hafızası
    sm = getattr(player, "synergy_matrix", None)
    if sm is not None:
        sm.update_from_board(player.board)
        sm.decay()
```

---

## 📈 Beklenen İyileştirmeler

### Sinerji Puanları

- **Önceki:** Rastgele yerleştirme → düşük sinerji
- **Sonrası:** Delta-aware yerleştirme → %30-50 daha yüksek sinerji

### Strateji Karakteri

- **Warrior:** Düşük ağırlık → bireysel güç korunuyor
- **Builder:** Yüksek ağırlık → combo master kimliği güçleniyor
- **Balancer:** Geç oyun patlaması → 4.0 ağırlık

### Oyun Aşaması Adaptasyonu

- **Erken (1-6):** Tahta kurulum, düşük ağırlık
- **Orta (7-15):** Sinerji etkin, orta ağırlık
- **Geç (16+):** Sinerji belirleyici, yüksek ağırlık

---

## 🛠️ Gelecek Geliştirmeler

### 1. Lookahead (2-Adım)

```python
def _lookahead_score(coord, card, remaining_hand):
    """Bu kartı koyarsak eldeki diğer kartlar ne kadar sinerji kazanır?"""
    # Builder'da zaten var, diğer stratejilere eklenebilir
```

### 2. Passive Uyum Bonusu

```python
def _passive_neighbor_score(coord, card):
    """Aynı kategorili komşular → passive zincir potansiyeli"""
    # Builder'da var, genelleştirilebilir
```

### 3. Pozisyon Bonusları

```python
def _position_bonus(coord):
    """Merkez ring, kenar, köşe bonusları"""
    # Tempo'da var (center_coords), genelleştirilebilir
```

### 4. Dinamik Ağırlık Ayarı

```python
def adaptive_weight(player, turn):
    """Oyuncunun mevcut durumuna göre ağırlık ayarla"""
    if player.board.alive_count() < 5:
        return weight_early  # Tahta boş, güç öncelikli
    else:
        return weight_for_turn(turn)  # Normal çizelge
```

---

## 📚 Bağımlılık Ağacı

```
engine_core/synergy.py
  └─ compute_synergy()          [SST — BFS hesaplayıcısı]
       ↑
       │
engine_core/ai/synergy_placement.py
  ├─ compute_delta_synergy()
  ├─ score_placement()
  ├─ best_coord_for_card()
  └─ place_cards_synergy_aware()
       ↑
       │
engine_core/ai/strategies/*.py
  └─ place_cards()
       ↑
       │
engine_core/ai/base.py
  └─ AI.place_cards()
       ↑
       │
engine_core/game.py
  └─ place_phase()
```

**Döngüsel Bağımlılık:** ❌ Yok  
**Modülerlik:** ✅ Yüksek  
**Test Edilebilirlik:** ✅ Kolay

---

## 🎓 Öğrenilen Dersler

### 1. Board Mutasyonu Riski

**Problem:** `Board.place()` → StateStore cache desync  
**Çözüm:** Geçici dict kopyası, simülasyon ana state'i etkilemez

### 2. Performans vs Kalite

**Problem:** Tüm koordinatları denemek yavaş  
**Çözüm:** `max_coord_check` parametresi, batch hesaplama

### 3. Strateji Kimliği

**Problem:** Tüm stratejiler aynı ağırlıkla aynı davranır  
**Çözüm:** Strateji bazlı önceden tanımlanmış çizelgeler

### 4. Oyun Aşaması Adaptasyonu

**Problem:** Erken oyunda sinerji az önemli, geç oyunda kritik  
**Çözüm:** `SynergyWeightSchedule` ile dinamik ağırlık

---

## ✅ Checklist

- [x] `engine_core/ai/synergy_placement.py` modülü oluşturuldu
- [x] `compute_delta_synergy()` fonksiyonu
- [x] `compute_delta_synergy_batch()` fonksiyonu
- [x] `score_placement()` formülü
- [x] `best_coord_for_card()` seçici
- [x] `place_cards_synergy_aware()` pipeline
- [x] `SynergyWeightSchedule` dataclass
- [x] Strateji bazlı ağırlık çizelgeleri
- [x] Tüm stratejiler entegre edildi
- [x] Test dosyası oluşturuldu (`tests/test_synergy_placement.py`)
- [x] Dokümantasyon tamamlandı
- [x] Board mutasyonu güvenliği doğrulandı
- [x] SST entegrasyonu (`engine_core/synergy.py`)

---

## 🚀 Sonuç

Autochess Hybrid AI botları artık **sinerji-aware** kararlar veriyor!

**Önceki:** "En güçlü kartı rastgele bir yere koy"  
**Şimdi:** "Bu kartı buraya koyarsam +15 sinerji kazanırım, oraya koyarsam +3. Buraya koyuyorum!"

Sistem modüler, test edilebilir ve güvenli. Her strateji kendi karakterini korurken sinerji avantajından faydalanıyor.

---

**Geliştirici:** Kiro AI  
**Tarih:** 2026-05-07  
**Versiyon:** 1.0.0  
**Durum:** ✅ Production Ready
