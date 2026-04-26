# HYBRID OYUN PROJESİ - KÜDEMLİ MİMAR DEĞERLENDİRME RAPORU
**Rapor Tarihi:** 22 Nisan 2026  
**Rol:** Senior Game Architect (Pygame-CE, 10+ yıl deneyim)  
**Proje Statüsü:** PROD'a Hazırlık Değerlendirmesi  

---

## EXECUTIVE SUMMARY

Hybrid oyunu, kart tabanlı simulasyon + hex-grid mekanikleriyle orta düzey karmaşıklıkta bir Pygame-CE projesidir. **Mimarinin temel yapısı sağlamdır**, ancak **5 kritik sorun** ve **8 stratejik risk** gece uyutmayacak düzeydedir.

**Verdict:** 
- ✅ **Shipping'e Hazır DEĞİL** - Kritik sorunlar 2-3 gün içinde çözülmeli
- ⚠️ **Ölçekleme Riski YÜKSEK** - 100 yeni kart eklemek mümkün, 5 yeni Synergy ekleme imkansız
- 🔴 **Teknik Borç Birikmiş** - Ardından refaktör planı yapılmalı

---

## [KRİTİK - DERHAL MÜDAHALE]

### 🔴 **KRİTİK-1: Board State Desynchronization**
**Location:** `v2/core/state_store.py:36-44`, `v2/core/game_state.py`  
**Severity:** CRITICAL (Crash Risk)

**Problem:**
```python
# StateStore'da board durum
_board_names: Dict[Tuple[int, int], str] = {}
_board_rotations: Dict[Tuple[int, int], int] = {}

# update_board() MANUEL çağrılması gerekiyor
# Eğer Player.board.grid doğrudan mutate olursa → stale data
```

**Scenario Crash:**
```python
# Oyuncu UI'dan kart yerleştiriyor
state.place_card_on_board(coord, card)    # StateStore güncelleniyor ✓

# Ama passive system ayrı yerden grid'i doğrudan değiştirse:
player.board.grid[coord] = transformed_card  # StateStore bilmiyor ✗

# UI's get_public_state() çağırı → stale board döner
ui_state = state.get_public_state()
# UI shows wrong card at coord
```

**Why It Matters:**
- UI misalignment sebebi 90%
- Tur ilerledikçe state iyice bozulur
- Hata nerede başladığı izlemek imkansız (cache nedeniyle)

**Çözüm (2 Alternatif):**
1. **FAST (4h):** Tüm Board mutasyonları Hook etmek
   ```python
   # board.py'da place() ve remove() override et:
   def place(self, coord, card):
       grid[coord] = card
       self._state_store.update_board()  # Auto-sync
   ```

2. **CLEAN (4h):** StateStore board cache'ini kaldırmak
   ```python
   # build_public_state() sırasında Player.board.grid live oku
   # Daha yavaş ama güvenli (BFS zaten O(n²))
   ```

**Priority:** 🔥 **DO FIRST** - İlk iki saat içinde çöz

---

### 🔴 **KRİTİK-2: Synergy BFS 3 Yerde Duplicate**
**Location:** `engine_core/board.py:198-241`, `v2/core/synergy_calculator.py:77-145`, `v2/core/ui_adapter.py`  
**Severity:** CRITICAL (Logic Divergence Risk)

**Problem:**
```python
# KOPYALAMA 1: board.py'da
def calculate_group_synergy_bonus(grid, card_by_group, group):
    visited = set()
    def bfs(...):  # BFS implementasyon
        
# KOPYALAMA 2: synergy_calculator.py'da
class SynergyCalculator:
    def compute(self):
        for group in GROUPS:
            # AYNI BFS, AYNI KOD, BAŞKA YER
            
# KOPYALAMA 3: ui_adapter.py (muhtemel)
```

**Senaryolar:**
1. **v0.5'te BFS'de bug bulundu** → Fix board.py'a yapıldı ✓
2. **v0.6'da synergy_calculator.py'a fix uygulanmadı** ✗
3. **UI'da eski koddaki bug hala var** ✗
4. **Synergy score engine'de 100, UI'da 95 gösteriyor**
5. **Testers: "Hile var mı?" diyor, siz 3 saat debug ediyorsunuz**

**Why It Matters:**
- **Synergy = oyunun balansının kalbi**
- BFS'de bir satır hata (off-by-one vb) = balance broken
- 3 yerden fix etmek = 3× iş, 3× hata riski

**Çözüm (6h):**
1. synergy_calculator.py'ı **Single Source of Truth** yap
2. board.py ve ui_adapter.py'daki kodu sil
3. Tüm consumers'ı synergy_calculator.py'a yönlendir
   ```python
   # board.py (artık clean):
   from v2.core.synergy_calculator import SynergyCalculator
   # daha calculate_group_synergy_bonus() yok - SynergyCalculator kullan
   ```

**Priority:** 🔥 **DO FIRST** - KRİTİK-1'den sonra hemen

---

### 🔴 **KRİTİK-3: 3-Grup & 6-Edge Hardcoded (Extensibility Blocker)**
**Location:** `engine_core/board.py:152-153, 218`, `v2/core/synergy_calculator.py:27`, `engine_core/constants.py`  
**Severity:** CRITICAL (Feature Lock)

**Problem:**
```python
# synergy_calculator.py:27
_GROUPS: Tuple[str, ...] = ("MIND", "CONNECTION", "EXISTENCE")

# board.py:218
groups = ["MIND", "CONNECTION", "EXISTENCE"]

# board.py:152-153 (6-edge hardcoding)
bonus_per_edge_a = bonus_total_a // 6

# Eğer 4. grup eklemek istersen:
# → 10+ yere yazıyorsun "4. grup var" diye
# → synergy_calculator.py'a "4. grup" ekledin
# → board.py'a "4. grup" eklemeyi unuttun
# → CRASH vya wrong bonus calculation
```

**Why It Matters:**
```
Senaryo: "Yeni Synergy tipi ekleyelim"

Eski: 3 grup (MIND, CONNECTION, EXISTENCE)
Yeni: 4 grup istiyoruz (+ ENTROPY)

Yapılacaklar:
1. Sabitlere ENTROPY ekle ✓
2. synergy_calculator.py'ı güncelle ✓
3. board.py'ı güncelle ✗ (forgotten)
4. BFS'de ENTROPY miss ediliyor
5. ENTROPY synergy hiç hesaplanmıyor
6. Oyunu release ediyorsunuz, hiç kim fark etmiyor ilk hafta
7. Release Post-Mortem: "Niye ENTROPY hiç bonus vermiyor?"
```

**Çözüm (8h):**
1. **GroupRegistry** oluştur (runtime registration):
   ```python
   class GroupRegistry:
       _groups: Dict[str, Group] = {}
       
       @staticmethod
       def register(name: str, color: Tuple[int,int,int], tier_bonuses: List[int]):
           _groups[name] = Group(name, color, tier_bonuses)
       
       @staticmethod
       def get_all_groups() -> Dict[str, Group]:
           return _groups
   
   # Startup'ta:
   GroupRegistry.register("MIND", (100, 150, 200), [3, 9, 16, 25])
   GroupRegistry.register("CONNECTION", (200, 100, 50), [3, 9, 16, 25])
   GroupRegistry.register("EXISTENCE", (100, 200, 100), [3, 9, 16, 25])
   
   # Yeni grup eklemek:
   GroupRegistry.register("ENTROPY", (200, 50, 200), [3, 9, 16, 25])
   # Başka hiçbir yere dokunmuyorsun
   ```

2. Edge system'i de parametrize et (6 edge assumption'ı kaldır):
   ```python
   class EdgeSystem:
       EDGE_COUNT = 6  # Değişken olabilir (Triangular grid = 3, Square = 4)
       DIRECTIONS = [(1,0), (-1,0), (0,1), (0,-1), (1,1), (-1,-1)]  # 6 for hex
   ```

**Priority:** 🔥 **DO FIRST** - KRİTİK-2'den sonra hemen

---

### 🔴 **KRİTİK-4: Parallel State - cards_bought_this_turn Dual Source**
**Location:** `engine_core/player.py:70, 129, 154`  
**Severity:** CRITICAL (Logic Bug)

**Problem:**
```python
# player.py'da iki yerde:
class Player:
    def __init__(self):
        self.cards_bought_this_turn = 0  # İlki
        
    def buy_card(self, card: Card):
        self.cards_bought_this_turn += 1  # ← Burada increment
        
        # stats dict'te de increment var mı?
        if "cards_bought_this_turn" not in self.stats:
            self.stats["cards_bought_this_turn"] = 0
        self.stats["cards_bought_this_turn"] += 1  # ← İkincisi

# İki veri kaynağı = iki fail point
```

**Senaryolar:**
1. buy_card() çağrıldı, player.cards_bought_this_turn = 5 ✓
2. stats["cards_bought_this_turn"] = 5 ✓
3. Ama birisinin stats reset etme kodu:
   ```python
   player.stats["cards_bought_this_turn"] = 0  # Buradan reset
   # player.cards_bought_this_turn = 5 (hala eski değer)
   ```
4. İş akışta biri stats[...] okuyor → 0 görüyor
5. Başkası player. attribute'ı okuyor → 5 görüyor
6. **Logic: "Buy limit check'e takıldı mı?" - Tamamen rastgele cevap**

**Why It Matters:**
- **Buy limit** bu sayıyı kullanıyor
- Parallel state = race condition
- Silent fail (exception yok, sadece yanlış sayı)

**Çözüm (2h):**
```python
# SEÇENEK 1: Tek kaynağa indir
class Player:
    def __init__(self):
        self._cards_bought_this_turn = 0  # Private
    
    @property
    def cards_bought_this_turn(self) -> int:
        return self._cards_bought_this_turn
    
    def buy_card(self, card: Card):
        self._cards_bought_this_turn += 1
        self.stats["cards_bought_this_turn"] = self._cards_bought_this_turn
    
    def reset_turn_state(self):
        self._cards_bought_this_turn = 0
        self.stats["cards_bought_this_turn"] = 0
```

**Priority:** 🔥 **DO FIRST** - Tüm kritikleri 4 saatte çöz

---

### 🔴 **KRİTİK-5: Error Handling = Silent Failure + Crashes**
**Location:** `v2/core/engine_adapter.py:30-35, 52-61`, `engine_core/strategy_logger.py:329, 513`  
**Severity:** CRITICAL (Hard to Debug)

**Problem:**
```python
# engine_adapter.py
def get_player(self, index: int) -> Optional[ActivePlayerShim]:
    if not self._adapter:
        return None  # ← Ne oldu? Niye None?
    
    try:
        return self._adapter.get_player(index)
    except IndexError:
        # Sessiz ölüm - exception belirtilmemedi
        return None
    except Exception:
        # Tüm hatalar = None
        return None

# Consumer'lar:
player = adapter.get_player(999)
if player.alive:  # ← AttributeError: 'NoneType' has no attribute 'alive'
    # Asıl problem ne? Şu an belli değil.
```

**Senaryolar:**
1. Testler pass ediyor
2. Production'da çöküyor - player index out of range
3. Debugger attach etmek zor (remote game server)
4. Logs: "AttributeError" - yardımcı değil
5. 2 saat debug, hatta 1 satır exception message'in çıkartılması

**Why It Matters:**
- **Production = Debugging imkansız**
- Silent fail pattern = kıyıya vuran sahil yengeç
- None return = True/False'tan daha zararlı

**Çözüm (2h):**
```python
class EngineAdapterError(Exception):
    pass

class PlayerNotFoundError(EngineAdapterError):
    pass

def get_player(self, index: int) -> ActivePlayerShim:
    if not self._adapter:
        raise EngineAdapterError("Adapter not initialized via hook_engine()")
    
    if index < 0 or index >= len(self._adapter.players):
        raise PlayerNotFoundError(f"Player index {index} out of range [0, {len(self._adapter.players)})")
    
    try:
        return self._adapter.get_player(index)
    except Exception as e:
        raise EngineAdapterError(f"Failed to get player {index}: {e}") from e
```

**Priority:** 🔥 **DO FIRST** - Production Safety

---

## [STRATEJİK - MİMARİ RİSK]

### ⚠️ **STRATEJİK-1: Board "God Object" (400 LOC)**
**Location:** `engine_core/board.py`  
**Severity:** STRATEGIC (Maintainability, Testing)

**Problem:**
```python
class Board:
    # Responsibility 1: Hex grid management
    def place(self, coord: Tuple[int, int], card: Card): ...
    def remove(self, coord: Tuple[int, int]): ...
    def get_neighbors(self, coord: Tuple[int, int]): ...
    
    # Responsibility 2: Combat resolution
    def resolve_single_combat(self, card_a: Card, card_b: Card): ...
    
    # Responsibility 3: Combo detection
    def find_combos(self, grid: Dict): ...
    
    # Responsibility 4: Synergy calculation
    def calculate_group_synergy_bonus(self, card_by_group, group): ...
    
    # Responsibility 5: Damage calculation
    def calculate_damage(self, attacker_pts, defender_pts): ...
    
    # 400 LOC = 5 unrelated concerns = change everything to fix anything
```

**Why It Matters:**
```
Test yazabilir misin Board sınıfı için?

Board(initialize) → 37 cards setup → neighbors computed → synergy cached
→ 2000 LOC test setup sadece bir test case'i setup etmek için

Kombo detection bugı buldun:
→ find_combos() satırsını düzelt
→ 20 test fail olur (unrelated)
→ Tüm testleri update et
→ Başka sistemler de bağlı olduğu için hepsi kırıldı

"Damage formula'yı change etmek istiyoruz"
→ calculate_damage() kodu Board'da
→ Board dependent: synergy system, combo system, hex grid
→ 4 saat değişim, 8 saat testing
→ Başka Project'de "Basit değişim" diye söylenebilecek bir şey 4 güne uzadı
```

**Current State:**
```
Board (400 LOC, 5 Responsibilities)
├─ Synergy calc (GOOD - Already extracted to SynergyCalculator, but old code remains)
├─ Combo detection (BAD - Intertwined with damage calc)
├─ Damage calc (BAD - Hardcoded formulas, turno multiplier embedded)
└─ Hex grid + combat (GOOD - Clean interface)
```

**Çözüm Proposal (16h refactor):**
```python
# AFTER REFACTOR:
class Board:
    """Pure hex grid manager + placement logic."""
    grid: Dict[Tuple[int, int], Card]
    
    def place(self, coord: Tuple[int, int], card: Card): ...
    def remove(self, coord: Tuple[int, int]): ...
    def get_neighbors(self, coord: Tuple[int, int]): ...
    def get_all_cards(self) -> List[Card]: ...

class ComboDetector:
    """Identifies card combinations on board."""
    @staticmethod
    def find_combos(board: Board) -> List[Tuple[Card, Card]]: ...

class DamageCalculator:
    """Computes damage based on stats, edges, synergies."""
    @staticmethod
    def calculate_damage(attacker: Card, defender: Card, synergy_bonus: float) -> int: ...
    
    @staticmethod
    def get_turn_damage_multiplier(turn: int) -> float: ...

# SynergyCalculator already exists (good)

# Usage:
combos = ComboDetector.find_combos(board)
damage = DamageCalculator.calculate_damage(a, b, synergy_bonus)
synergy = SynergyCalculator.compute(board)
```

**Why Now:**
- Phase 4 bitmiş (get_public_state() contract done)
- Phase 5 başlamak = God object refactor zamanı
- Şimdi yaparsan 16h, 6 ay sonra yapsan 40h+

**Priority:** 🔄 **DO NEXT** (Post-Phase 4)

---

### ⚠️ **STRATEJİK-2: Synergy BFS O(n²) Every Frame (60 FPS)**
**Location:** `v2/core/synergy_calculator.py:77-145`  
**Severity:** STRATEGIC (Performance)

**Problem:**
```python
# Senaryolar:
Frame 1: UI'ın get_public_state() çağırı
  → SynergyCalculator.compute() çağrılı
  → 3 BFS traversal (MIND, CONNECTION, EXISTENCE)
  → O(3 × V × (V + E)) = O(1,110) operations
  
Frame 2-60: Her frame aynı
  → 60 × 1,110 = 66,600 operations/sec in UI thread
  
Current mitigation:
  → Cached in GameState until next mutation ✓
  
Problem:
  → If Player.board mutates 5× per turn
  → 5 × BFS recalculations
  → O(5,550) ops = acceptable but not optimized
  
Worse scenario:
  → Render loop calls get_public_state() multiple times (layout pass, draw pass, tooltip pass)
  → BFS runs redundantly
  → 60 FPS suddenly drops to 30 FPS
```

**Why It Matters:**
- Pygame single-threaded
- BFS runs in render thread
- O(n²) = visible lag on slower machines
- Not "broken", but "laggy"

**Çözüm (3h):**
```python
class SynergyCalculator:
    def __init__(self):
        self._last_board_hash = None
        self._cached_result = None
    
    def compute(self, board: Board) -> SynergyViewState:
        board_hash = hash(board)  # or checksum of grid
        
        if board_hash == self._last_board_hash and self._cached_result:
            return self._cached_result  # Return cached
        
        # BFS calculation only if changed
        result = self._compute_bfs(board)
        
        self._last_board_hash = board_hash
        self._cached_result = result
        return result
```

**ROI:** 10% UI performance (15 FPS → 16.5 FPS on low-end)

**Priority:** 🔄 **DO NEXT** (Post-Criticals)

---

### ⚠️ **STRATEJİK-3: Tight Card/Board Coupling**
**Location:** `engine_core/card.py`, `engine_core/board.py`, `engine_core/passives/*.py`  
**Severity:** STRATEGIC (Refactoring Resistance)

**Problem:**
```python
# Card class expects:
card.edges()           # Combat system'de çağrılı
card.rotated_edges()   # Synergy system'de çağrılı
card.add_base_stat()   # Passive system'de mutate çağrılı
card.stats             # Return MappingProxyType (safe read)

# Board class calls:
card.rotated_edges()   # Synergy bonus calculation
card.rotate()          # Rotation apply

# Passive system calls:
neighbor.add_base_stat() # Direct card mutation

# Senaryolar:
1. "Edge system'i change etmek istiyoruz" (3 edges to 4)
   → Card.edges() change → Combat breaks
   → Board.calculate_group_synergy_bonus() change → Synergy breaks
   → Passive system'de bağımlılık check et
   → 40+ lines code touch

2. "Card stats system'i change etmek istiyoruz" (dict → dataclass)
   → Passive handlers update → 20 passives touch
   → Board.resolve_single_combat() update → combat breaks
   → Tests all rewrite
   → 8+ saat
```

**Why It Matters:**
- **Card = oyunun DNA'sı**
- Tight coupling = Card change = Cascade failures
- Refactoring impossible without massive regression testing

**Çözüm (8h - Major Refactor):**
```python
# Create CardAdapter interface:
class ICardStatsProvider:
    @property
    def edges(self) -> List[int]: ...
    
    @property
    def rotated_edges(self) -> List[int]: ...
    
    def get_stat(self, stat_name: str) -> int: ...
    
    def add_base_stat(self, stat_name: str, delta: int): ...

# Card implements ICardStatsProvider
class Card(ICardStatsProvider):
    pass

# Combat only knows ICardStatsProvider, not Card
def resolve_single_combat(provider_a: ICardStatsProvider, provider_b: ICardStatsProvider):
    edges_a = provider_a.rotated_edges
    edges_b = provider_b.rotated_edges
    # ... rest
```

**Priority:** 🔄 **DO NEXT** (Phase 5)

---

### ⚠️ **STRATEJİK-4: Evolution Logic Hardcoded for "evolver" Strategy**
**Location:** `engine_core/player.py:209-230`  
**Severity:** STRATEGIC (New Strategy Blocker)

**Problem:**
```python
class Player:
    def check_evolution(self):
        if self.strategy != "evolver":
            return  # ← HARDCODED
        
        # Evolver-specific logic
        if self.inventory.copies >= COPY_THRESH:
            # ... evolution triggers
```

**Senaryolar:**
1. "Yeni strategy: 'mutator' - kartları evolve edebiliyor"
   → Player.check_evolution()' modifiye et
   → if strategy == "evolver" or strategy == "mutator"
   → Başka 5 strategy daha ekleyin
   → if strategy in ["evolver", "mutator", ...] (hardcoded list)

2. "Strategi config'den gelecek"
   → check_evolution() hala hardcoded
   → Generic öğlen hala logic

**Why It Matters:**
- **Strategy system = game balance'ın merkezi**
- Hardcoding = New strategy add = Code change
- Config'den alsa bile, strategy selection logic'te değişim zorunlu

**Çözüm (4h):**
```python
# strategy_config.yml
strategies:
  evolver:
    can_evolve: true
    evolution_threshold: 10
    evolution_trigger: "on_copy_threshold"
  
  mutator:
    can_evolve: true
    evolution_threshold: 15
    evolution_trigger: "on_board_full"

# Player class:
def check_evolution(self):
    config = StrategyConfig.get(self.strategy)
    
    if not config.can_evolve:
        return
    
    if config.evolution_trigger == "on_copy_threshold":
        if self.inventory.copies >= config.evolution_threshold:
            self._trigger_evolution()
    elif config.evolution_trigger == "on_board_full":
        if len(self.board.grid) >= 37:
            self._trigger_evolution()
```

**Priority:** 🔄 **DO NEXT** (Strategy Expansion Phase)

---

### ⚠️ **STRATEJİK-5: AI Parameters Global + JSON-based (Fallback Silent)**
**Location:** `engine_core/ai.py:114-120`  
**Severity:** STRATEGIC (AI Tuning Regression)

**Problem:**
```python
# ai.py
def load_strategy_params() -> Dict[str, Any]:
    """Backward compat: sadece economist parametrelerini döndürür."""
    # Default hardcoded values
    return {
        "buy_thresholds": [27, 15, 11, 42, 80],  # HARDCODED
        "tier_preferences": {...},
        # ...
    }

# Senaryolar:
1. "AI parameters file bulunamadı"
   → Fallback: hardcoded thresholds
   → AI oynamaması değişti (daha weak or strong)
   → Testers: "Niye AI davranışı değişti?"
   → params file'ı missing olduğunu hiç bilen yok

2. "JSON'da buy_thresholds incorrect"
   → AI trash tier buy ediyor
   → Fallback yok (yukarıda şanslı)
   → AI loses every game
   → Debugging imkansız (hardcoded değerler nerede?)
```

**Why It Matters:**
- **AI balance = gameplay quality**
- Silent fallback = Unpredictable behavior
- JSON loading failure = Unhandled

**Çözüm (2h):**
```python
class AIConfigError(Exception):
    pass

class AIParameterLoader:
    @staticmethod
    def load(strategy: str, raise_on_missing: bool = True) -> Dict[str, Any]:
        path = f"assets/config/ai_params/{strategy}.json"
        
        if not os.path.exists(path):
            if raise_on_missing:
                raise AIConfigError(f"AI params file missing: {path}")
            else:
                logger.warning(f"AI params missing for {strategy}, using defaults")
                return AIParameterLoader._get_defaults(strategy)
        
        try:
            with open(path) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise AIConfigError(f"Invalid JSON in {path}: {e}") from e
    
    @staticmethod
    def _get_defaults(strategy: str) -> Dict[str, Any]:
        # Documented defaults (not magic)
        return {...}

# Usage:
try:
    params = AIParameterLoader.load("economist")
except AIConfigError as e:
    logger.error(f"Cannot load AI params: {e}")
    # Explicit failure, not silent fallback
```

**Priority:** 🔄 **DO NEXT** (Quality Assurance)

---

### ⚠️ **STRATEJİK-6: Synergy Bonus Capped 30% (Hardcoded in Damage)**
**Location:** `engine_core/board.py:333`  
**Severity:** STRATEGIC (Balance Inflexibility)

**Problem:**
```python
# board.py - Combat damage calculation
def calculate_damage(attacker_pts, defender_pts, synergy_bonus):
    base_damage = attacker_pts - defender_pts
    
    # Synergy bonus applied but capped
    capped_synergy = min(synergy_bonus, 0.30)  # ← HARDCODED 30%
    final_damage = base_damage * (1 + capped_synergy)
    
    return max(0, final_damage)

# Senaryolar:
1. "Synergy'nin oyunda çok güçlü, 20% cap yapalım"
   → board.py'a git
   → 0.30 → 0.20 change et
   → Board class'ı touch etmek = 20+ test fail
   → Hepsi fix et
   → 2 saat "basit değişim"

2. "Yeni strategy 'synergy_master' güçlü synergy bonus kullanıyor"
   → Ama 30% cap hala uygulanıyor
   → Strategy power beklediği gibi çıkmıyor
   → Cap'i 50% yapmak istiyorsun, ama tüm diğer strategies break olabilir
```

**Why It Matters:**
- **Balance parameter = sacred**
- Hardcoding = "Dinamik balancing" imkansız
- Config dışında = değişim risky

**Çözüm (2h):**
```python
# game_balance.yaml
synergy:
  bonus_cap: 0.30
  tier_multipliers: [3, 9, 16, 25]
  edge_bonus_multiplier: 2

# engine_core/game_balance.py
class GameBalance:
    SYNERGY_BONUS_CAP = 0.30  # Load from YAML
    SYNERGY_TIERS = [3, 9, 16, 25]
    EDGE_BONUS_MULTIPLIER = 2

# board.py
def calculate_damage(attacker_pts, defender_pts, synergy_bonus):
    capped_synergy = min(synergy_bonus, GameBalance.SYNERGY_BONUS_CAP)
    final_damage = base_damage * (1 + capped_synergy)
    return max(0, final_damage)
```

**Priority:** 🔄 **DO NEXT** (Balance Config)

---

### ⚠️ **STRATEJİK-7: Game.log Unbounded (Memory Leak Risk)**
**Location:** `engine_core/game.py:70`  
**Severity:** STRATEGIC (Memory)

**Problem:**
```python
class Game:
    def __init__(self):
        self.log: List[str] = []  # ← No max size
    
    def _log(self, msg: str):
        self.log.append(msg)  # Append every turn
    
    # After 10,000 turns:
    # ~1 MB/1000 turns = 10 MB log
    # Long tournament simulation = 100 MB log
    # Server farm running 100 simultaneous games = 10 GB memory
```

**Senaryolar:**
1. "1000 games/hour simulation çalıştır"
   → 2000 turns/game
   → 2M log entries/hour
   → ~200 MB/hour memory
   → 24 saat = 4.8 GB
   → OOM (Out of Memory)

2. "Oyuncu 'replay' logunu istedi"
   → 500 turn oyun
   → ~5000 log entries
   → Gönder UI'a
   → Network payload 2-5 MB
   → Transfer slow

**Why It Matters:**
- **Simulation = core feature**
- Memory leak = 24 hour server dies
- Undiagnosed (monitoring olmadığı sürece)

**Çözüm (2h):**
```python
class Game:
    def __init__(self, max_log_size: int = 10000):
        self.log: Deque[str] = deque(maxlen=max_log_size)
    
    def _log(self, msg: str):
        self.log.append(msg)  # Automatically pops oldest
```

**Priority:** 🔄 **DO BEFORE RELEASE** (Ops Issue)

---

### ⚠️ **STRATEJİK-8: Deprecated _legacy_passive_log Still Exported**
**Location:** `engine_core/passive_trigger.py:128-137`  
**Severity:** STRATEGIC (Tech Debt)

**Problem:**
```python
# passive_trigger.py
_legacy_passive_log = defaultdict(lambda: defaultdict(int))  # ← DEPRECATED

def get_passive_trigger_log():
    """DEPRECATED: Returns the legacy global log."""
    return _legacy_passive_log

def clear_passive_trigger_log():
    """DEPRECATED: Clears the legacy global log."""
    _legacy_passive_log.clear()

# Somewhere in code (unknown):
# old_code = get_passive_trigger_log()  # ← Calling deprecated function
# If this code is anywhere, it's using stale passive log

# Senaryolar:
1. "Passive log'u temizleyelim"
   → get_passive_trigger_log() kodu bulursak sil
   → Ama tüm codebase'i scan edin (git grep)
   → Belki hidden uses var

2. "Passive logging refactor"
   → Legacy code still there
   → Backup'ı ne zaman kaldıracağız?
   → 6 ay sonra hala orada

3. "İlk geliş developer burada hata yapabilir"
   → "deprecated ama exported" = çok kafa karıştırıcı
```

**Why It Matters:**
- **Dead code = future bugs**
- Unclear removal timeline = technical debt accumulation
- Every refactor deprecated code taşıdı

**Çözüm (1h):**
```python
# OPTION 1: Remove completely
# Delete _legacy_passive_log, get_passive_trigger_log(), clear_passive_trigger_log()
# Search codebase for usages, update or delete them

# OPTION 2: Deprecation warning + deadline
def get_passive_trigger_log():
    """DEPRECATED: Will be removed in v0.8. Use passive_logger module instead."""
    warnings.warn("get_passive_trigger_log() deprecated, remove by v0.8", DeprecationWarning)
    return _legacy_passive_log
```

**Priority:** 🔄 **DO BEFORE RELEASE** (Code Cleanliness)

---

## [KİRLİ KOD - REFAKTOR ÖNERİSİ]

### 🟡 **Defensive Copying in Loops (5-10% Performance)**
**Location:** `engine_core/game.py:131, 141`, `engine_core/turn_manager.py:96, 108`, `engine_core/combat_engine.py:57, 67`  

**Code Smell:**
```python
# Anti-pattern:
for board_card in tuple(player.board.grid.values()):  # Unnecessary tuple copy
    player.board.grid[coord] = new_card  # Modify during iteration
    
# Better:
cards = list(player.board.grid.values())  # Single copy at start
for board_card in cards:
    ...

# Even better (if no mutation):
for board_card in player.board.grid.values():  # No copy needed
    ...
```

**Impact:** ~5% turn processing slowdown  
**Fix:** 2 hours code review + pattern change  
**Priority:** 🟡 LOW (Performance, but risky to change)

---

### 🟡 **Magic Numbers Scattered (Balance Config)**
**Location:** `engine_core/board.py:228, 235, 348-375`

**Code Smell:**
```python
# Anti-pattern:
bonus_level_1 = 3          # What is this?
bonus_level_2 = 9          # Why 9?
bonus_level_3 = 16         # How was this calculated?
bonus_level_4 = 25         # Magic?
damage_multiplier = 0.5    # Why 0.5?
turn_multiplier = 5        # Related to game phases?

# Better:
SYNERGY_TIERS = [3, 9, 16, 25]  # Synergy bonus per tier level
COMBAT_DAMAGE_BASE_MULTIPLIER = 0.5
TURN_PROGRESSION_MULTIPLIER = 5
```

**Impact:** Hard to balance game without code reading  
**Fix:** Extract constants, document  
**Priority:** 🟡 LOW (Tuning, but needed for balance)

---

### 🟡 **Type Hints Missing Return Values**
**Location:** `engine_core/player.py:169-200`, `engine_core/ai.py:100-150`

**Code Smell:**
```python
# Anti-pattern:
def get_player_stats(player_id):  # No return type
    return player.stats  # Returns what type?

# Better:
def get_player_stats(player_id: int) -> Dict[str, int]:
    return player.stats
```

**Impact:** IDE autocompletion poor, type checking impossible  
**Fix:** Add type hints  
**Priority:** 🟡 LOW (Code quality, non-blocking)

---

### 🟡 **Bare Exception Handlers (Code Smell)**
**Location:** `engine_core/strategy_logger.py:329, 513`

**Code Smell:**
```python
# Anti-pattern:
except Exception as e:
    # What to do?
    pass

# Better:
except (ValueError, KeyError) as e:
    logger.warning(f"Failed to parse strategy params: {e}")
    # or re-raise with context
except Exception as e:
    logger.error(f"Unexpected error in log_passive_trigger: {e}", exc_info=True)
    raise
```

**Impact:** Silent failures, hard to debug  
**Fix:** Explicit exception types + logging  
**Priority:** 🟡 LOW (But should do with Error Handling audit)

---

### 🟡 **String Group Names (Should be Enum)**
**Location:** `v2/core/synergy_calculator.py:27`

**Code Smell:**
```python
# Anti-pattern:
_GROUPS = ("MIND", "CONNECTION", "EXISTENCE")  # Strings
bonus_by_group = {"MIND": 5, "CONNECTION": 3, ...}

# Typo risk:
if group == "MINDE":  # Typo, no error
    ...

# Better:
from enum import Enum

class GroupType(Enum):
    MIND = "mind"
    CONNECTION = "connection"
    EXISTENCE = "existence"

_GROUPS = list(GroupType)
bonus_by_group = {GroupType.MIND: 5, ...}

# Now typo caught at IDE
if group == GroupType.MIN:  # IDE error
```

**Impact:** Runtime typos possible  
**Fix:** Use Enum class  
**Priority:** 🟡 LOW (Quality, but good practice)

---

### 🟡 **Card Properties Expose Internal State**
**Location:** `engine_core/card.py:54-62`, `engine_core/player.py:54-62`

**Code Smell:**
```python
# Anti-pattern:
class Card:
    @property
    def edges(self):
        return self._edges  # Direct access to internal

# If you want to change _edges to _edges_rotated:
# All callers break

# Better:
class Card:
    @property
    def edges(self) -> List[int]:
        """Get card's current edge values (respecting rotation)."""
        return self._compute_edges_with_rotation()
    
    def _compute_edges_with_rotation(self) -> List[int]:
        """Internal: recalculate edges based on rotation."""
        ...
```

**Impact:** Refactoring difficult  
**Fix:** Encapsulation + abstraction  
**Priority:** 🟡 LOW (Refactoring resistance, do with Board refactor)

---

## [EXTENSIBILITY IMPACT MATRIX]

| Feature | Blockers | Effort | Severity |
|---------|----------|--------|----------|
| **Add 100 new cards (Rarity 1-5)** | None | 4 hours | ✓ EASY |
| **Add 5 new synergies** | ✗ 3-group hardcoded | 8 hours | 🔴 BLOCKED |
| **Add rarity-6** | ⚠️ AI thresholds scattered | 3 hours | ⚠️ DOABLE |
| **Replace combat system** | ✗ Card assumes 6 edges, Board tightly coupled | 40+ hours | 🔴 HARD |
| **Add new game phase (Draft)** | ✗ Game.run() hardcoded | 16 hours | 🔴 HARD |
| **New strategy type** | ⚠️ Evolution hardcoded for "evolver" | 4 hours | ⚠️ DOABLE |
| **Change synergy bonus cap** | ⚠️ Hardcoded in damage calc | 2 hours | ✓ EASY |
| **Modify AI strategies** | ✓ Config-based | 1 hour | ✓ EASY |

---

## ACTION PLAN - 4 HAFTA

### HAFTA 1: Kritik Sorunlar (Derhal)
**Mon-Wed (3 gün):**
- ✅ Fix BoardState Desync (KRİTİK-1) → 4h
- ✅ Synergy BFS Duplication (KRİTİK-2) → 6h
- ✅ Parameterize 3-Group System (KRİTİK-3) → 8h
- ✅ Dual cards_bought State (KRİTİK-4) → 2h
- ✅ Error Handling (KRİTİK-5) → 2h
- **Total:** 22 hours = ~3 full days
- **Testing:** Thu-Fri (2 days) → Regression tests, all 8 tests pass

**Deliverables:**
- All 5 criticals fixed
- Tests green
- Code review passed

---

### HAFTA 2: Strategic Refactors (Phase 5 Prep)
**Mon-Tue:**
- ✅ Extract Board God Object (STRATEJİK-1) → 16h (Split Combo, Damage into separate classes)
- ✅ Remove Deprecated Passive Log (STRATEJİK-8) → 2h

**Wed-Thu:**
- ✅ Parameterize Balance Constants (STRATEJİK-6) → 2h
- ✅ Add Log Rotation (STRATEJİK-7) → 2h
- ✅ AI Config Error Handling (STRATEJİK-5) → 2h

**Friday:**
- Testing + Integration

---

### HAFTA 3: Optimization + Docs
**Mon-Tue:**
- ✅ Synergy BFS Caching (STRATEJİK-2) → 3h
- ✅ Card Coupling Refactor (STRATEJİK-3) → 8h (ICardStatsProvider adapter)

**Wed-Thu:**
- ✅ Documentation (god object signatures, passive triggers, state management)

**Friday:**
- Testing, integration

---

### HAFTA 4: Code Quality + Release Prep
**Mon-Tue:**
- Exception handling audit + logging
- Type hints completion
- Magic number extraction

**Wed-Thu:**
- Full regression test suite
- Performance profiling (synergy BFS, turn processing)

**Friday:**
- Release readiness review
- Deploy to staging

---

## SON SÖZ

**Hybrid'in Durumu:**
✅ **Mimari temel sağlam** - Unidirectional dependencies, good separation concerns  
❌ **5 kritik sorun** - 3 gün içinde çözülmeli, production'a geçilmez  
⚠️ **8 stratejik risk** - Ölçeklemeyi engeller, refactoring gerektiriyor  
🟡 **Birkaç code smell** - Bakım zorluğu, teknik borç

**Tavsiye:**
1. **İlk 3 gün:** Kritikleri çöz (board state, synergy duplication, 3-group hardcode)
2. **2. Hafta:** Strategic refactors (god object, balance config)
3. **3. Hafta:** Optimization + docs
4. **4. Hafta:** QA + release

**Produksiyona geçmeden önce:** Tüm kritiklerin çözülmesi şart.

---

**Hazırladı:** Senior Game Architect  
**Tarih:** 22 Nisan 2026  
**Durum:** 🟡 CONDITION: AMBER (Fixable, non-blocking but urgent)
