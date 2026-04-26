# Board Class ve İlgili Fonksiyonlar - Bağımlılık Analizi

## Genel Bakış
Bu doküman `engine_core/autochess_sim_v06.py` dosyasındaki Board class ve board-related fonksiyonların bağımlılıklarını analiz eder ve `board.py` modülüne güvenli taşıma planı sunar.

---

## 1. Board Class Tespiti

### Konum
- Dosya: `engine_core/autochess_sim_v06.py`
- Satırlar: 117-165

### Board Class Yapısı
```python
class Board:
    def __init__(self)
    def place(self, coord, card)
    def remove(self, coord)
    def free_coords(self) -> List[Tuple[int,int]]
    def neighbors(self, coord) -> List[Tuple[Tuple[int,int], int]]
    def alive_cards(self) -> List[Card]
    def alive_count(self) -> int
    def rarity_bonus(self) -> int
```

### Board Instance Attributes
- `self.grid: Dict[Tuple[int,int], Card]` - Koordinat -> Card mapping
- `self.coord_index: Dict[int, Tuple[int,int]]` - Card ID -> Koordinat (O(1) lookup)
- `self.square_card: Optional[Card]` - Catalyst veya Eclipse kartı
- `self.has_catalyst: bool` - Catalyst aktif mi?
- `self.has_eclipse: bool` - Eclipse aktif mi?

---

## 2. Board ile Direkt İlişkili Fonksiyonlar

### 2.1 Helper Fonksiyonlar (Board Utility)
| Fonksiyon | Satır | Açıklama |
|-----------|-------|----------|
| `hex_coords(radius)` | 82-98 | Hex koordinatları oluşturur |
| `_find_coord(board, c)` | 486-489 | Card instance'ın board'daki koordinatını bulur |
| `_neighbor_cards(board, coord)` | 491-494 | Bir koordinattaki komşu kartları döndürür |

### 2.2 Board Operasyon Fonksiyonları
| Fonksiyon | Satır | Açıklama |
|-----------|-------|----------|
| `find_combos(board)` | 331-368 | Board'daki combo eşleşmelerini bulur |
| `calculate_group_synergy_bonus(board)` | 370-428 | Board'daki grup sinerji bonusunu hesaplar |
| `calculate_damage(winner_pts, loser_pts, winner_board, turn)` | 432-483 | Kazanan board'a göre hasar hesaplar |

### 2.3 Combat Fonksiyonları
| Fonksiyon | Satır | Açıklama |
|-----------|-------|----------|
| `resolve_single_combat(card_a, card_b, bonus_a, bonus_b)` | 180-224 | İki kart arasında tek combat çözümler |
| `combat_phase(board_a, board_b, combo_bonus_a, combo_bonus_b, ...)` | 227-328 | İki board arasında tam combat phase'i çözümler |

### 2.4 Data Classes
| Class | Satır | Açıklama |
|-------|-------|----------|
| `CombatResult` | 170-178 | Combat sonuç verisi (şu an kullanılmıyor gibi görünüyor) |

---

## 3. Detaylı Bağımlılık Analizi

### 3.1 Board Class Methodları

| Method | Global Değişken | Kullanılan Class | Card Bağımlılığı | Constants Bağımlılığı | Diğer Modül |
|--------|----------------|------------------|------------------|----------------------|-------------|
| `__init__()` | - | - | Card (type hint) | - | typing |
| `place()` | - | - | Card (parametre) | - | - |
| `remove()` | - | - | - | - | - |
| `free_coords()` | BOARD_COORDS | - | - | - | - |
| `neighbors()` | - | - | - | HEX_DIRS | - |
| `alive_cards()` | - | - | Card (return) | - | - |
| `alive_count()` | - | - | - | - | - |
| `rarity_bonus()` | - | - | Card (grid values) | RARITY_DMG_BONUS | - |

### 3.2 Helper Fonksiyonlar

| Fonksiyon | Global Değişken | Kullanılan Class | Card Bağımlılığı | Constants Bağımlılığı | Diğer Modül |
|-----------|----------------|------------------|------------------|----------------------|-------------|
| `hex_coords()` | - | - | - | - | typing |
| `_find_coord()` | - | Board | - | - | - |
| `_neighbor_cards()` | - | Board | Card (return) | - | - |

### 3.3 Board Operasyon Fonksiyonları

| Fonksiyon | Global Değişken | Kullanılan Class | Card Bağımlılığı | Constants Bağımlılığı | Diğer Modül |
|-----------|----------------|------------------|------------------|----------------------|-------------|
| `find_combos()` | - | Board | Card.dominant_group() | OPP_DIR | typing |
| `calculate_group_synergy_bonus()` | - | Board | Card.get_group_composition() | - | typing, math |
| `calculate_damage()` | - | Board | - | - | typing |

### 3.4 Combat Fonksiyonları

| Fonksiyon | Global Değişken | Kullanılan Class | Card Bağımlılığı | Constants Bağımlılığı | Diğer Modül |
|-----------|----------------|------------------|------------------|----------------------|-------------|
| `resolve_single_combat()` | - | - | Card.stats, Card.edges | STAT_TO_GROUP, GROUP_BEATS | typing |
| `combat_phase()` | - | Board, Player (optional) | Card.lose_highest_edge(), Card.is_eliminated() | KILL_PTS | typing |

**ÖNEMLİ NOT**: `combat_phase()` fonksiyonu `trigger_passive()` fonksiyonunu çağırıyor (satır 283, 285, 289, 295, 297, 301). Bu fonksiyon passive ability sisteminin parçası ve Board modülüne ait değil.

---

## 4. Global Değişken Bağımlılıkları

### 4.1 BOARD_COORDS
- **Tanım**: Satır 99
- **Değer**: `hex_coords(BOARD_RADIUS)`
- **Kullanım**: `Board.free_coords()` methodunda
- **Taşıma Stratejisi**: `board.py` modülüne taşınmalı

### 4.2 Constants Modülünden Kullanılanlar
| Constant | Kullanıldığı Yer | Açıklama |
|----------|------------------|----------|
| `BOARD_RADIUS` | `hex_coords()` çağrısı | Board yarıçapı (3 = 37 hex) |
| `HEX_DIRS` | `Board.neighbors()` | Hex yön vektörleri |
| `OPP_DIR` | `find_combos()` | Karşıt yön mapping |
| `RARITY_DMG_BONUS` | `Board.rarity_bonus()` | Rarity hasar bonusu (şu an boş dict) |
| `STAT_TO_GROUP` | `resolve_single_combat()` | Stat -> Group mapping |
| `GROUP_BEATS` | `resolve_single_combat()` | Group avantaj sistemi |
| `KILL_PTS` | `combat_phase()` | Kill başına puan (8) |

---

## 5. Card Class Bağımlılıkları

### 5.1 Board Class'ta Kullanılan Card Özellikleri
- `Card` type (type hints)
- `card.rarity` (rarity_bonus methodunda)

### 5.2 Board Fonksiyonlarında Kullanılan Card Methodları
| Fonksiyon | Kullanılan Card Method/Attribute |
|-----------|----------------------------------|
| `find_combos()` | `card.dominant_group()` |
| `calculate_group_synergy_bonus()` | `card.get_group_composition()` |
| `resolve_single_combat()` | `card.stats`, `card.edges` |
| `combat_phase()` | `card.lose_highest_edge()`, `card.is_eliminated()` |

---

## 6. Player/Board Bağımlılıkları

### 6.1 Board Class
**BAĞIMSIZ** - Board class hiçbir Player bağımlılığı yok.

### 6.2 combat_phase() Fonksiyonu
**PLAYER BAĞIMLILIĞI VAR** - Opsiyonel parametreler:
- `player_a` (optional)
- `player_b` (optional)
- `ctx` (optional) - Game context dictionary
- `passive_log` (optional) - Passive trigger log

Bu parametreler sadece `trigger_passive()` fonksiyonuna iletiliyor. Board operasyonları için gerekli değil.

---

## 7. Diğer Modül Bağımlılıkları

### 7.1 Standard Library
| Modül | Kullanıldığı Yer |
|-------|------------------|
| `typing` | Type hints (Dict, List, Tuple, Optional, Callable) |
| `dataclasses` | CombatResult dataclass |
| `math` | calculate_group_synergy_bonus() (math.pow) |

### 7.2 Passive System Bağımlılığı
**KRITIK**: `combat_phase()` fonksiyonu `trigger_passive()` fonksiyonunu çağırıyor. Bu fonksiyon passive ability sisteminin parçası ve board modülüne ait değil.

**Çözüm Seçenekleri**:
1. `trigger_passive()` fonksiyonunu parametre olarak al (dependency injection)
2. `combat_phase()` fonksiyonunu board modülünde bırakma, game modülünde tut
3. Passive trigger'ları callback olarak implement et

---

## 8. Board ile Direkt İlişkili OLMAYAN Fonksiyonlar

Bu fonksiyonlar Board parametresi alıyor ama board modülüne ait değil:

| Fonksiyon | Neden Board Modülüne Ait Değil |
|-----------|--------------------------------|
| `combat_phase()` | Player, passive system, game context bağımlılıkları var |
| `trigger_passive()` | Passive ability sistemi, Player bağımlılığı var |

---

## 9. Güvenli Taşıma Planı

### Faz 1: Temel Board Modülü (GÜVENLI)
**Taşınacaklar**:
```python
# board.py modülüne taşınacak
- hex_coords() fonksiyonu
- BOARD_COORDS global değişkeni
- Board class (tüm methodlar)
- _find_coord() helper
- _neighbor_cards() helper
- CombatResult dataclass (kullanılmıyorsa kaldırılabilir)
```

**Gerekli İmportlar**:
```python
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Card modülünden
from .card import Card

# Constants modülünden
from .constants import (
    BOARD_RADIUS,
    HEX_DIRS,
    RARITY_DMG_BONUS
)
```

**Risk Seviyesi**: ✅ ÇOK DÜŞÜK - Hiçbir circular dependency yok

---

### Faz 2: Board Utility Fonksiyonları (GÜVENLI)
**Taşınacaklar**:
```python
# board.py modülüne taşınacak
- find_combos() fonksiyonu
- calculate_group_synergy_bonus() fonksiyonu
- calculate_damage() fonksiyonu
```

**Ek İmportlar**:
```python
import math  # calculate_group_synergy_bonus için

# Constants modülünden
from .constants import OPP_DIR
```

**Risk Seviyesi**: ✅ DÜŞÜK - Sadece Board ve Card bağımlılıkları var

---

### Faz 3: Combat Fonksiyonları (ORTA RİSK)
**Taşınacaklar**:
```python
# board.py modülüne taşınacak
- resolve_single_combat() fonksiyonu
```

**Ek İmportlar**:
```python
# Constants modülünden
from .constants import (
    STAT_TO_GROUP,
    GROUP_BEATS
)
```

**Risk Seviyesi**: ✅ DÜŞÜK - Card bağımlılığı var ama circular dependency yok

---

### Faz 4: Combat Phase (YÜKSEK RİSK - TAŞINMAMALI)
**TAŞINMAMALI**:
```python
# autochess_sim_v06.py'de kalmalı
- combat_phase() fonksiyonu
```

**Neden Taşınmamalı**:
1. `trigger_passive()` fonksiyonuna bağımlı (passive system)
2. Player class'a bağımlı (optional ama kullanılıyor)
3. Game context'e bağımlı (ctx dictionary)
4. Passive log'a bağımlı
5. Bu fonksiyon game logic'in parçası, board utility değil

**Alternatif**: Game modülünde tutulmalı veya combat modülüne taşınmalı

**Risk Seviyesi**: ⚠️ YÜKSEK - Çok fazla bağımlılık, circular dependency riski

---

## 10. Import Planı

### 10.1 board.py Modülü İçin
```python
"""
================================================================
|         AUTOCHESS HYBRID - Board Module                      |
|  Board class and board-related utility functions             |
================================================================
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import math

# Try relative import first (when used as a module)
try:
    from .card import Card
    from .constants import (
        BOARD_RADIUS,
        HEX_DIRS,
        OPP_DIR,
        RARITY_DMG_BONUS,
        STAT_TO_GROUP,
        GROUP_BEATS
    )
except ImportError:
    # Fall back to absolute import (when run as a script)
    from card import Card
    from constants import (
        BOARD_RADIUS,
        HEX_DIRS,
        OPP_DIR,
        RARITY_DMG_BONUS,
        STAT_TO_GROUP,
        GROUP_BEATS
    )
```

### 10.2 autochess_sim_v06.py İçin (Taşıma Sonrası)
```python
# Board modülünden import
try:
    from .board import (
        Board,
        hex_coords,
        BOARD_COORDS,
        find_combos,
        calculate_group_synergy_bonus,
        calculate_damage,
        resolve_single_combat,
        _find_coord,
        _neighbor_cards,
        CombatResult  # eğer kullanılıyorsa
    )
except ImportError:
    from board import (
        Board,
        hex_coords,
        BOARD_COORDS,
        find_combos,
        calculate_group_synergy_bonus,
        calculate_damage,
        resolve_single_combat,
        _find_coord,
        _neighbor_cards,
        CombatResult
    )
```

---

## 11. Bağımlılık Hiyerarşisi

```
constants.py
    ↓
card.py
    ↓
board.py
    ├── Board class
    ├── hex_coords()
    ├── BOARD_COORDS
    ├── find_combos()
    ├── calculate_group_synergy_bonus()
    ├── calculate_damage()
    ├── resolve_single_combat()
    ├── _find_coord()
    └── _neighbor_cards()
    ↓
autochess_sim_v06.py
    ├── combat_phase() (Board kullanır ama board modülüne ait değil)
    ├── Player class
    ├── AI class
    ├── Market class
    └── Game class
```

---

## 12. Kritik Notlar

### ✅ Güvenli Taşıma (Circular Dependency Yok)
1. Board class tamamen bağımsız
2. Board utility fonksiyonları sadece Board ve Card'a bağımlı
3. resolve_single_combat() sadece Card'a bağımlı
4. Hiçbir Player/Game bağımlılığı yok (combat_phase hariç)

### ⚠️ Dikkat Edilmesi Gerekenler
1. **combat_phase() Fonksiyonu**: Bu fonksiyon board modülüne taşınmamalı çünkü:
   - trigger_passive() bağımlılığı var
   - Player class bağımlılığı var
   - Game context bağımlılığı var
   - Bu fonksiyon game logic'in parçası

2. **BOARD_COORDS Global Değişkeni**: Module-level initialization
   - board.py'ye taşındığında otomatik olarak oluşturulacak
   - Diğer modüller `from board import BOARD_COORDS` ile kullanabilir

3. **CombatResult Dataclass**: Kodda kullanılmıyor gibi görünüyor
   - Taşınabilir ama gereksiz olabilir
   - Kullanım yerlerini kontrol et

### 🎯 Önerilen Taşıma Sırası
1. **İlk**: hex_coords(), BOARD_COORDS, Board class
2. **İkinci**: _find_coord(), _neighbor_cards()
3. **Üçüncü**: find_combos(), calculate_group_synergy_bonus(), calculate_damage()
4. **Dördüncü**: resolve_single_combat()
5. **TAŞINMAMALI**: combat_phase() (game modülünde kalmalı)

---

## 13. Özet

### Taşıma Karmaşıklığı: **DÜŞÜK**
- Circular dependency yok
- Temiz ayrım mevcut
- Minimal refactoring gerekli

### Risk Seviyesi: **MİNİMAL**
- Board class bağımsız
- Utility fonksiyonlar sadece Board/Card'a bağımlı
- combat_phase() hariç hiçbir game logic bağımlılığı yok

### Taşınacak Toplam Satır: ~350 satır
- Board class: ~48 satır
- Helper fonksiyonlar: ~20 satır
- Utility fonksiyonlar: ~150 satır
- Combat fonksiyonlar: ~50 satır
- CombatResult: ~10 satır

### Taşınmayacak: ~100 satır
- combat_phase(): ~100 satır (game modülünde kalmalı)
