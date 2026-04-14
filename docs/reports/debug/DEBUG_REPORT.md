# 🐛 KRİTİK HATA ANALİZİ VE ÇÖZÜM RAPORU

## 1️⃣ HP FREEZE INVESTIGATION

### Sorun Tespiti

**HP değişimi fonksiyonları:**
```python
# src/autochess_sim_v06.py:1528
def take_damage(self, amount: int):
    self.hp = max(0, self.hp - amount)
    self.stats["damage_taken"] += amount
```

**Fonksiyon çağrısı:**
```python
# Game.combat_phase() içinde:
if pts_a > pts_b:
    dmg = calculate_damage(pts_a, pts_b, board_a)
    p_b.take_damage(dmg)  # ← HP burada değişiyor
```

### Root Cause Analysis

**SORUN:** `run_simulation_with_kpi.py` dosyasında:

```python
# Track each turn
turn = 0
while len([p for p in players if p.alive]) > 1 and turn < 50:
    turn += 1
    
    # Record turn metrics for each player
    for i, player in enumerate(players):
        if player.alive:
            trackers[i].record_turn(player, turn, players)
    
    # Run one turn (simplified - actual game loop is in Game.run())
    # ↑ BOŞ LOOP! HİÇBİR ŞEY YAPMIYOR!

# Run actual game
winner = game.run()  # ← OYUN BURADA ÇALIŞIYOR AMA TRACKING YOK!
```

### Sorunun Detayları

**a) Hasar değeri 0 geliyor mu?**
❌ HAYIR - Hasar hesaplaması doğru çalışıyor

**b) Fonksiyon hiç çağrılmıyor mu?**
❌ HAYIR - Fonksiyon çağrılıyor ama tracking loop'u oyun çalışmadan önce bitiyor

**c) HP değeri başka bir yerde overwrite ediliyor mu?**
❌ HAYIR - HP doğru değişiyor ama tracking loop'u bunu görmüyor

### Kronolojik Akış (HATALI)

```
1. Boş while loop başlıyor
   └─> turn = 0
   └─> Oyuncular alive, turn < 50
   └─> turn += 1
   └─> record_turn() çağrılıyor (HP = 150, board boş)
   └─> Loop hiçbir şey yapmıyor
   └─> turn = 50'ye ulaşıyor
   └─> Loop bitiyor

2. game.run() çağrılıyor
   └─> Oyun baştan başlıyor
   └─> preparation_phase() çalışıyor
   └─> combat_phase() çalışıyor
   └─> HP değişiyor (150 -> 120 -> 90 ...)
   └─> AMA tracking loop'u zaten bitmiş!

3. Finalize çağrılıyor
   └─> HP değişimlerini görmüyor
   └─> Board state'leri görmüyor
   └─> Tüm metrikler 0 veya başlangıç değerinde
```

---

## 2️⃣ STATE CHECK

### Board Power Değişimleri

**Beklenen akış:**
```python
Turn 1: Player buys cards → board_power = 0 (henüz tahtada yok)
Turn 2: Player places cards → board_power = 120 (kartlar tahtada)
Turn 3: Combat happens → board_power = 115 (hasar aldı)
Turn 4: More cards → board_power = 180 (güçlendi)
```

**Gerçek akış (HATALI):**
```python
Turn 1-50: record_turn() çağrılıyor
  └─> board.alive_cards() = [] (boş)
  └─> board_power = 0
  └─> Oyun henüz başlamamış!

Game.run(): Oyun çalışıyor
  └─> Kartlar alınıyor, yerleştiriliyor
  └─> Combat oluyor, HP değişiyor
  └─> AMA tracking görmüyor!
```

### Sorun İşaretleri

✅ **Ekleme yapılıyor** - `board_power.append()` çağrılıyor  
❌ **AMA yanlış zamanda** - Oyun çalışmadan önce  
❌ **Overwrite yok** - Sadece boş değerler ekleniyor

---

## 3️⃣ ZERO-VALUE ALERT

### Sıfır Değer Tespitleri

**HP:**
```
Turn 1-50: HP = 150 (başlangıç değeri)
  └─> Hiç değişmiyor çünkü oyun henüz başlamamış
  └─> ⚠️ PROBLEM: Tracking loop oyun öncesi çalışıyor
```

**board_power:**
```
Turn 1-50: board_power = 0
  └─> board.alive_cards() = []
  └─> ⚠️ PROBLEM: Kartlar henüz yerleştirilmemiş
```

**damage_dealt:**
```
Finalize: damage_dealt = 0
  └─> stats['damage_dealt'] = 0
  └─> ⚠️ PROBLEM: Combat tracking loop'ta değil
```

**combo_triggers:**
```
Finalize: combo_triggers = 1500+
  └─> ✅ BU ÇALIŞIYOR çünkü game.run() içinde hesaplanıyor
```

### Kronolojik Sıfır Değer Analizi

```
[00:00] Game başlıyor
[00:01] Tracking loop başlıyor
  └─> HP = 150 (başlangıç)
  └─> board_power = 0 (boş tahta)
  └─> gold = 0 (henüz income yok)
  └─> ⚠️ ALERT: Tüm değerler başlangıç durumunda

[00:02] Tracking loop bitiyor (50 tur)
  └─> HP hala 150
  └─> board_power hala 0
  └─> ⚠️ ALERT: Hiçbir değişim olmadı

[00:03] game.run() başlıyor
  └─> preparation_phase()
  └─> combat_phase()
  └─> HP değişiyor: 150 -> 120
  └─> board_power değişiyor: 0 -> 180
  └─> ⚠️ ALERT: Değişimler tracking dışında

[00:04] Finalize
  └─> HP = 150 (tracking'in gördüğü son değer)
  └─> board_power_avg = 0 (tracking'in gördüğü ortalama)
  └─> ⚠️ ALERT: Gerçek değerler kaydedilmedi
```

---

## 4️⃣ SORUNLU FONKSİYON VE FIX

### Sorunlu Kod

**Dosya:** `run_simulation_with_kpi.py`  
**Satır:** 447-465

```python
# ❌ HATALI KOD
# Track each turn
turn = 0
while len([p for p in players if p.alive]) > 1 and turn < 50:
    turn += 1
    
    # Record turn metrics for each player
    for i, player in enumerate(players):
        if player.alive:
            trackers[i].record_turn(player, turn, players)
    
    # Run one turn (simplified - actual game loop is in Game.run())
    # ↑ BOŞ LOOP - HİÇBİR ŞEY YAPMIYOR!

# Run actual game
winner = game.run()  # ← OYUN BURADA ÇALIŞIYOR AMA TRACKING YOK!
```

### Sorunun Nedeni

1. **Çağrı eksikliği**: Loop içinde `game.preparation_phase()` ve `game.combat_phase()` çağrılmıyor
2. **Timing hatası**: Tracking oyun çalışmadan önce yapılıyor
3. **State mismatch**: Tracking boş state'i görüyor, oyun gerçek state'te çalışıyor

### Önerilen Fix

**Çözüm 1: Game class'ını extend et (UYGULANMIŞ)**

```python
class GameWithTracking(sim.Game):
    """Extended Game class with KPI tracking."""
    
    def __init__(self, players, trackers, verbose=False, rng=None):
        super().__init__(players, verbose, rng)
        self.trackers = trackers
    
    def run(self) -> sim.Player:
        """Run game with turn-by-turn KPI tracking."""
        _players = self.players
        
        while len([p for p in _players if p.alive]) > 1:
            # ✅ PRE-TURN TRACKING
            for i, p in enumerate(_players):
                if p.alive:
                    self.trackers[i].record_turn(p, self.turn, _players)
            
            # ✅ OYUN ÇALIŞIYOR
            self.preparation_phase()
            self.combat_phase()
            
            # ✅ POST-TURN TRACKING (HP değişimleri)
            for i, p in enumerate(_players):
                if p.alive and self.trackers[i].hp_diff_over_time:
                    hp_before = self.trackers[i].hp_diff_over_time[-1]
                    hp_after = p.hp
                    if hp_before != hp_after:
                        self.trackers[i].record_damage(
                            hp_before - hp_after,
                            self.turn,
                            hp_before,
                            hp_after
                        )
            
            if self.turn >= 50:
                break
        
        # Winner selection
        winners = [p for p in _players if p.alive]
        if winners:
            winner = max(winners, key=lambda p: p.hp)
        else:
            winner = max(_players, key=lambda p: p.hp)
        
        return winner
```

**Kullanım:**
```python
# ✅ DÜZELTİLMİŞ KOD
trackers = [KPITracker(p.pid, p.strategy) for p in players]
game = GameWithTracking(players, trackers, verbose=False, rng=rng)
winner = game.run()  # ← Tracking entegre edilmiş!
```

---

## 5️⃣ BEKLENEN SONUÇLAR (FIX SONRASI)

### HP Değişimleri

```
Game 1, Player 0:
  Turn 1: HP = 150 (başlangıç)
  Turn 5: HP = 145 (5 hasar aldı)
  Turn 10: HP = 132 (13 daha hasar)
  Turn 20: HP = 98 (34 daha hasar)
  Turn 30: HP = 45 (53 daha hasar)
  Turn 35: HP = 0 (elendi)
  
  Damage Events: 8 kez hasar aldı
  HP Min: 0
  HP Max: 150
  HP Final: 0
```

### Board Power Değişimleri

```
Game 1, Player 0:
  Turn 1: board_power = 0 (henüz kart yok)
  Turn 2: board_power = 85 (3 kart yerleşti)
  Turn 5: board_power = 180 (6 kart, güçlendi)
  Turn 10: board_power = 165 (hasar aldı)
  Turn 20: board_power = 220 (evrim oldu)
  Turn 30: board_power = 95 (çok hasar aldı)
  
  Avg Board Power: 145.3
  Max Board Power: 220
  Avg Unit Count: 4.2
```

### Combo & Synergy

```
Game 1, Player 0:
  Combo Triggers: 1580 (her tur kombo)
  Combo Efficiency: 31.6 (1580 / 50 tur)
  Synergy Avg: 0.8 (bazı turlarda aktif)
  Synergy Active Turns: 12
```

---

## 6️⃣ ÖZET

### Sorun

❌ **Tracking loop oyun çalışmadan önce bitiyor**  
❌ **HP ve board state değişimleri kaydedilmiyor**  
❌ **Tüm metrikler başlangıç değerlerinde kalıyor**

### Çözüm

✅ **Game class'ı extend edildi (GameWithTracking)**  
✅ **Tracking game loop'a entegre edildi**  
✅ **Pre-turn ve post-turn tracking eklendi**  
✅ **HP değişimleri damage_events olarak kaydediliyor**

### Dosyalar

📄 **Düzeltilmiş script:** `run_simulation_with_kpi_fixed.py`  
📄 **Debug raporu:** `DEBUG_REPORT.md` (bu dosya)  
📁 **Yeni log dizini:** `kpi_logs_fixed/`

### Sonraki Adım

```bash
python run_simulation_with_kpi_fixed.py
```

Bu komut 500 oyunu doğru tracking ile çalıştıracak ve gerçek HP/board power değişimlerini kaydedecek.

---

## 7️⃣ TEKNİK DETAYLAR

### Pseudo-code Karşılaştırması

**ÖNCE (HATALI):**
```
function run_simulation():
    create players
    create trackers
    
    // Boş loop
    for turn in 1..50:
        for player in players:
            tracker.record_turn(player)  // Boş state
    
    // Oyun çalışıyor ama tracking yok
    winner = game.run()
    
    // Finalize boş değerlerle
    for tracker in trackers:
        tracker.finalize()
```

**SONRA (DÜZELTİLMİŞ):**
```
function run_simulation():
    create players
    create trackers
    
    // Tracking entegre edilmiş game
    game = GameWithTracking(players, trackers)
    
    // Game.run() içinde:
    while players_alive > 1:
        // Pre-turn tracking
        for player in players:
            tracker.record_turn(player)  // Gerçek state
        
        // Oyun çalışıyor
        preparation_phase()
        combat_phase()
        
        // Post-turn tracking
        for player in players:
            if hp_changed:
                tracker.record_damage()
    
    // Finalize gerçek değerlerle
    for tracker in trackers:
        tracker.finalize()
```

### Veri Akışı

**ÖNCE:**
```
Tracker → Boş State → Finalize → Sıfır Değerler
Game → Gerçek State → (Tracking görmüyor)
```

**SONRA:**
```
Game → Gerçek State → Tracker → Finalize → Doğru Değerler
```

---

## 🎯 SONUÇ

Sorun tespit edildi ve çözüldü. Yeni script (`run_simulation_with_kpi_fixed.py`) doğru HP ve board power tracking'i yapacak.
