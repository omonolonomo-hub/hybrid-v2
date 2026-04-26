# Autochess Hybrid — Cursor Başlangıç Rehberi

Bu dosyayı Cursor'da aç ve chat'e şunu yaz:
**"@CURSOR_BASLANGIC.md dosyasını oku, projeyi anla"**

---

## Proje Dosyaları

| Dosya | Açıklama |
|---|---|
| `autochess_sim_v06.py` | Simülasyon motoru — ana çalışma dosyası |
| `Autochess_Hybrid_GDD_v06.md` | Game Design Document |
| `Autochess_Kartlar_v01.md` | 101 kartın tüm stat ve pasif verileri |
| `CURSOR_BASLANGIC.md` | Bu dosya |

---

## Simülasyonu Çalıştırma

```bash
# Temel çalıştırma
python autochess_sim_v06.py

# 700 oyun, 8 oyuncu
python autochess_sim_v06.py --games 700 --players 8

# Tur tur detay (1 oyun)
python autochess_sim_v06.py --games 1 --verbose

# Kart havuzu doğrulama
python autochess_sim_v06.py --verify
```

---

## Mevcut Durum (v0.5 Simülasyon Sonuçları)

700 oyun, 8 oyuncu:

| Strateji | Kazanma % | Durum |
|---|---|---|
| Tempo | **%30.6** | ⚠️ Dominant — dengelenmeli |
| Savaşçı | %17.4 | ✅ Stabil |
| Evrimci | %12.0 | ✅ Güçlendirildi |
| Ekonomist | %11.9 | ✅ Güçlendirildi |
| İnşacı | %9.1 | ✅ Combo düzeltildi |
| Balansçı | %8.4 | ✅ Dengeli |
| Nadir-avcı | %6.4 | ⚠️ Zayıf, geliştirilebilir |
| Rastgele | %4.1 | Referans |

---

## Öncelikli Geliştirme Görevleri

### 🔴 GÖREV 1 — Tempo Dengelemesi
**Hedef:** %30.6 → %15-20 aralığına çek

Bakılacak fonksiyon: `AI._place_aggressive()` (satır ~780)
- `center_coords` bonusu azaltılabilir
- `total_power >= 35` eşiği yükseltilebilir (→ 42?)
- Veya tempo'nun tur başına max alım sayısı kısıtlanabilir

Simüle et → sonuç %20 altına indiyse tamam.

---

### 🔴 GÖREV 2 — Pasif Yetenekler (En Büyük Eksik)
**Durum:** 101 kartın tümünde `passive_type` tanımlı ama **hiçbiri çalışmıyor.**

`Autochess_Kartlar_v01.md` dosyasında her kartın pasifi yazıyor.

**Öneri — 3 pasif tipiyle başla:**

```python
# 1. combat pasifi — combat_phase() içinde, kill sonrası tetikle
#    Örnek: Ragnarök — "combat kazanılırsa rakibin rastgele kartının en yüksek kenarı -1"

# 2. ekonomi pasifi — Player.income() içinde tetikle
#    Örnek: Midas — "2 tur üst üste kazanılırsa +1 altın"

# 3. sinerjik_alan — find_combos() veya combat öncesinde
#    Örnek: Odin — "komşu Mitoloji kartlarına +1 Anlam"
```

**Implementasyon yapısı önerisi:**
```python
def trigger_passive(card: Card, trigger: str, context: dict) -> dict:
    """
    trigger: "combat_win" | "combat_lose" | "income" | "board_start"
    context: {"board": Board, "player": Player, "opponent": Player, ...}
    returns: {"gold": 0, "stat_bonus": {}, "puan": 0, ...}
    """
    if card.passive_type == "none":
        return {}
    # Her kart için özel mantık buraya
    ...
```

---

### 🟡 GÖREV 3 — Zenginleştirilmiş Simülasyon Çıktısı
Şu an eksik olan istatistikler:

```python
# Player.stats dict'ine ekle:
"first_kill_turn": 0,        # İlk kill kaçıncı turda?
"avg_board_size": [],        # Ortalama kart sayısı/tur
"copy_upgrades": 0,          # Kaç kez kopya güçlenmesi tetiklendi?
"passive_triggers": 0,       # Pasif kaç kez çalıştı? (Görev 2 sonrası)
```

Bu veri gelince strateji analizi çok daha isabetli olur.

---

## Kod Mimarisi Özeti

```
CARD_POOL (101 kart)
    ↓
Game.__init__()
    → _deal_starting_hands()  # Her oyuncuya 3×◆ kart
    ↓
Game.run() döngüsü:
    → preparation_phase()
        → Player.income()
        → Market.get_cards_for_player()
        → AI.buy_cards()        # Strateji tipine göre alım
        → AI.place_cards()      # Strateji tipine göre yerleşim
        → check_copy_strengthening()
    → combat_phase()
        → swiss_pairs()         # HP bazlı eşleştirme
        → find_combos()         # Kart-grup bazlı combo
        → calculate_group_synergy_bonus()
        → combat_phase()        # Kenar karşılaştırması
        → calculate_damage()    # Hasar formülü
```

---

## Önemli Sabitler (autochess_sim_v06.py, satır ~39-73)

```python
CARD_COSTS    = {"◆":1, "◆◆":2, "◆◆◆":3, "◆◆◆◆":8, "◆◆◆◆◆":10}
STARTING_HP   = 150
KILL_PTS      = 8
BASE_INCOME   = 3
MAX_INTEREST  = 5
COPY_THRESH   = [4, 7]   # Normal kopya eşikleri
COPY_THRESH_C = [3, 6]   # Catalyst aktifken
```

---

## Cursor Chat Prompt Örnekleri

```
# Tempo dengelemesi için:
"@autochess_sim_v06.py AI._place_aggressive fonksiyonunu oku.
 Tempo stratejisinin kazanma oranını %30'dan %18'e indirmek için
 ne değiştirmemi önerirsin? GDD'ye göre merkez hex avantajı korunmalı."

# Pasif implementasyonu için:
"@autochess_sim_v06.py @Autochess_Kartlar_v01.md
 combat tipindeki pasifler için trigger_passive() fonksiyonu yaz.
 Ragnarök ve Cerberus'tan başla."

# Yeni istatistik için:
"@autochess_sim_v06.py run_simulation fonksiyonuna first_kill_turn
 ve avg_board_size istatistiklerini ekle, print_results'ta göster."
```

---

*Son güncelleme: Mart 2026 — autochess_sim_v06.py + GDD v0.6 baz alınarak hazırlandı.*
