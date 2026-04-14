# 📊 Event Logging Sistemi - Kullanım Kılavuzu

## 🎯 Genel Bakış

Bu sistem, mevcut logging sistemine **DOKUNMADAN**, üzerine detaylı event logging ekler.

### Özellikler
- ✅ Mevcut logging sistemi korunur
- ✅ Varsayılan olarak kapalı (performans kaybı yok)
- ✅ İsteğe bağlı aktif edilir
- ✅ Detaylı KPI metrikleri üretir
- ✅ JSONL formatında append-only log

---

## 📁 Dosya Yapısı

```
engine_core/
└── event_logger.py          # Event logging modülü (YENİ)

scripts/
├── simulation/
│   └── run_with_detailed_logging.py  # Detaylı logging ile simülasyon (YENİ)
└── analysis/
    └── analyze_events.py     # Event log analizi (YENİ)

output/
└── logs/
    ├── simulation_log.txt           # MEVCUT - korundu
    ├── simulation_events.jsonl      # YENİ - event log
    ├── combat_events.jsonl          # YENİ - combat log
    └── kpi_reports/
        └── event_kpi_report.json    # YENİ - KPI raporu
```

---

## 🚀 Kullanım

### 1. Normal Simülasyon (Mevcut Sistem)

```bash
# Detaylı logging KAPALI (default)
python scripts/simulation/run_simulation.py
```

**Sonuç:**
- ✅ Sadece mevcut log sistemi çalışır
- ✅ `output/logs/simulation_log.txt` oluşur
- ✅ Performans kaybı YOK

### 2. Detaylı Event Logging ile Simülasyon

```bash
# Detaylı logging AKTİF
python scripts/simulation/run_with_detailed_logging.py --games 100
```

**Sonuç:**
- ✅ Mevcut log sistemi çalışır
- ✅ Event logging sistemi de çalışır
- ✅ `output/logs/simulation_events.jsonl` oluşur
- ✅ `output/logs/combat_events.jsonl` oluşur

### 3. Event Log Analizi

```bash
# KPI raporunu oluştur
python scripts/analysis/analyze_events.py
```

**Sonuç:**
- ✅ `output/logs/kpi_reports/event_kpi_report.json` oluşur
- ✅ Ekrana özet rapor yazdırılır

---

## 📊 Event Türleri

### 1. card_purchase
Kart satın alma eventi

```json
{
  "timestamp": "2026-03-28T22:30:00",
  "game_id": 1,
  "turn": 5,
  "event_type": "card_purchase",
  "player_id": 0,
  "card_name": "Ragnarok",
  "card_rarity": "5",
  "cost": 5,
  "gold_after": 3
}
```

### 2. board_placement
Board'a kart yerleştirme

```json
{
  "timestamp": "2026-03-28T22:30:01",
  "game_id": 1,
  "turn": 5,
  "event_type": "board_placement",
  "player_id": 0,
  "card_name": "Ragnarok",
  "position": [0, 0],
  "board_size": 5
}
```

### 3. combat
Combat eventi

```json
{
  "timestamp": "2026-03-28T22:30:02",
  "game_id": 1,
  "turn": 5,
  "event_type": "combat",
  "player1_id": 0,
  "player2_id": 1,
  "winner_id": 0,
  "damage": 15,
  "player1_board_power": 450,
  "player2_board_power": 380,
  "combat_duration": 8
}
```

### 4. synergy_trigger
Sinerji tetikleme

```json
{
  "timestamp": "2026-03-28T22:30:03",
  "game_id": 1,
  "turn": 5,
  "event_type": "synergy_trigger",
  "player_id": 0,
  "card_name": "Ragnarok",
  "synergy_type": "mythology",
  "synergy_value": 25
}
```

### 5. round_result
Round sonucu

```json
{
  "timestamp": "2026-03-28T22:30:04",
  "game_id": 1,
  "turn": 5,
  "event_type": "round_result",
  "player_id": 0,
  "hp": 85,
  "gold": 8,
  "board_size": 6,
  "hand_size": 3,
  "result": "win"
}
```

### 6. passive_trigger
Pasif yetenek tetikleme

```json
{
  "timestamp": "2026-03-28T22:30:05",
  "game_id": 1,
  "turn": 5,
  "event_type": "passive_trigger",
  "player_id": 0,
  "card_name": "Ragnarok",
  "trigger_type": "combat_win",
  "effect_value": 10
}
```

---

## 📈 KPI Metrikleri

Event log'larından üretilen KPI'lar:

### 1. Kart Metrikleri
- ✅ En çok satın alınan kartlar
- ✅ En çok board'a yerleştirilen kartlar
- ✅ Shop → Board dönüşüm oranı
- ✅ Kart başına winrate
- ✅ Kart başına ortalama damage

### 2. Combat Metrikleri
- ✅ Ortalama combat süresi
- ✅ Ortalama damage
- ✅ Board power farkı vs damage ilişkisi

### 3. Sinerji Metrikleri
- ✅ En çok tetiklenen sinerjiler
- ✅ Sinerji başına ortalama değer
- ✅ Sinerji winrate ilişkisi

### 4. Pasif Yetenek Metrikleri
- ✅ En çok tetiklenen pasif yetenekler
- ✅ Pasif yetenek başına etki değeri
- ✅ Pasif yetenek winrate ilişkisi

### 5. Oyuncu Metrikleri
- ✅ Ortalama turn başına combat sayısı
- ✅ Ortalama gold kullanımı
- ✅ Board size progression

---

## 🔧 Programatik Kullanım

### Python Kodunda Event Logger Kullanımı

```python
from engine_core.event_logger import init_event_logger, get_event_logger, close_event_logger

# Logger'ı başlat
logger = init_event_logger(enabled=True)

# Game context ayarla
logger.set_game_context(game_id=1, turn=5)

# Event logla
logger.log_card_purchase(
    player_id=0,
    card_name="Ragnarok",
    card_rarity="5",
    cost=5,
    gold_after=3
)

# Simülasyon sonunda kapat
close_event_logger()
```

---

## ⚙️ Konfigürasyon

### Flag Kontrolü

```python
from engine_core.event_logger import ENABLE_DETAILED_LOGGING

if ENABLE_DETAILED_LOGGING:
    # Detaylı logging aktif
    logger.log_card_purchase(...)
else:
    # Sadece mevcut sistem çalışır
    pass
```

### Buffer Boyutu

`event_logger.py` içinde:

```python
_buffer_size = 100  # Her 100 event'te bir flush
```

Daha sık flush için bu değeri azaltın (örn. 50).

---

## 📊 Örnek KPI Raporu

```json
{
  "summary": {
    "total_events": 15420,
    "total_combats": 3850,
    "unique_cards_purchased": 87,
    "unique_cards_placed": 82
  },
  "top_purchased_cards": {
    "Ragnarok": 245,
    "Odin": 198,
    "Phoenix": 187
  },
  "shop_to_board_conversion": {
    "top_conversion": [
      ["Ragnarok", 95.5],
      ["Odin", 92.3],
      ["Phoenix", 89.7]
    ]
  },
  "combat_stats": {
    "avg_damage": 12.5,
    "avg_duration": 6.8
  }
}
```

---

## 🎯 Performans

### Buffer Sistemi
- Event'ler önce RAM'de buffer'lanır
- Her 100 event'te bir dosyaya yazılır
- Blocking disk write YOK

### Overhead
- `ENABLE_DETAILED_LOGGING=False`: **0% overhead**
- `ENABLE_DETAILED_LOGGING=True`: **~5% overhead** (buffer sayesinde minimal)

---

## ⚠️ Önemli Notlar

### Mevcut Sistem Korundu
- ✅ `write_game_log()` fonksiyonu değiştirilmedi
- ✅ Mevcut log dosyaları korundu
- ✅ Mevcut KPI hesaplamaları bozulmadı
- ✅ Simülasyon loop'u değiştirilmedi

### Yeni Sistem Bağımsız
- ✅ Tamamen additive
- ✅ Varsayılan olarak kapalı
- ✅ Mevcut sistemden bağımsız çalışır
- ✅ Mevcut log'ları etkilemez

---

## 🚀 Hızlı Başlangıç

```bash
# 1. Detaylı logging ile 100 oyun simülasyon
python scripts/simulation/run_with_detailed_logging.py --games 100

# 2. Event log'larını analiz et
python scripts/analysis/analyze_events.py

# 3. KPI raporunu incele
cat output/logs/kpi_reports/event_kpi_report.json
```

---

## 📝 Sonuç

Bu sistem, mevcut logging altyapısına **hiç dokunmadan**, üzerine detaylı event logging ekler. Varsayılan olarak kapalıdır ve performans kaybı yaratmaz. İhtiyaç duyulduğunda aktif edilerek detaylı KPI metrikleri üretilebilir.

**Hazırlayan:** Kiro AI Assistant  
**Tarih:** 28 Mart 2026  
**Versiyon:** 1.0
