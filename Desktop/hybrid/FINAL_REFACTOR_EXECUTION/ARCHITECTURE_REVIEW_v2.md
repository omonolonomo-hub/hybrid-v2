# Hybrid Oyun Prototipi — Mimari İnceleme Raporu v2
> Analiz tarihi: 2026-04-23  
> Kapsam: Hafta 1 (C1-C5) + Hafta 2 (P1-1, P1-2, P1-4, P1-5) tamamlandıktan sonra güncel kod tabanı  
> Referans: önceki rapor (v1) + MASTER_BACKLOG_AND_GATES.md

---

## 1. Executive Summary

Hafta 1 ve Hafta 2 refactorları ciddi ve doğru adımlardı. İki sprint boyunca yapılanlar:

- `card.stats` artık `MappingProxyType` → sessiz write kayıpları kapatıldı ✅
- `EffectPipeline.clear_expired()` tamamlandı ✅
- `board.py` 355 → 217 satıra indi; `ComboDetector` ve `DamageCalculator` ayrıştırıldı ✅
- `synergy.py` tek kaynak, `board.py` ve `SynergyCalculator` delegate ediyor ✅
- `TurnManager` ve `CombatEngine` ayrıştırıldı; `game.py` yalnızca delege ediyor ✅
- `PublicState` ve frozen DTO hiyerarşisi oluşturuldu ✅
- `ShopController` ile UI orchestration scene'den ayrıştırıldı ✅

**Yeni durum:** v1 raporundaki 3 kritik bulgudan ikisi kapatıldı (card.stats write loss + board god object). `test_engine_bridge_contracts.py` stale fixture sorunu da giderildi. Ancak refactor sürecinde üretilen yeni teknik borç ve 4 **yeni kritik sorun** saptandı.

En acil yeni sorun: `UIAdapter._TIER_BONUSES` listesi, `engine_core/synergy.py::tier_bonus()` formülüyle uyuşmuyor. Oyuncuya gösterilen "bir sonraki tier bonusu" değerleri yanlış — N=3 için +7 gösteriyor ama engine +9 veriyor.

---

## 2. Hafta 1 + 2 Kapanış Testi (Ne Çözüldü, Ne Kaldı)

| v1 Bulgu | Durum | Not |
|---|---|---|
| `card.stats` silent write loss | ✅ KAPANDI | `MappingProxyType` + `set_base_stat` / `add_base_stat` |
| `test_engine_bridge_contracts.py` stale fixture | ✅ KAPANDI | Fixture tamamen yeniden yazıldı |
| `ShopScene._cleanup_dead_cards` board.grid erişimi | ✅ KAPANDI | `ShopController.cleanup_dead_cards()` + `adapter.get_eliminated_coords()` |
| `_rarity_weight` private import | ✅ KAPANDI | `adapter.get_rarity_weight()` public proxy eklendi |
| `board.py` circular import (lazy) | ⚠️ KISMI | Lazy import hâlâ `combat_phase()` wrapper'ında var (aşağıda) |
| `GameState` god object | ⚠️ KISMI | `UIAdapter`, `ShopController`, `PublicState` ile zayıflatıldı; ama singleton kaldı |
| `EffectPipeline` duration desteği | ✅ KAPANDI | `clear_expired()` artık dolu implementasyon |
| 25 pre-existing test failure | ❌ AÇIK | Hafta 2 sonunda "pre-existing" olarak bırakıldı |
| Phase management scene-driven | ⚠️ KISMI | `ShopController` araya girdi ama `PhaseMachine` hâlâ `ShopScene`'de |

---

## 3. Yeni Kritik Bulgular (Kanıtlı)

### YENI-1 · `UIAdapter._TIER_BONUSES` — Yanlış UI Değerleri (Şiddet: KRİTİK)

`ui_adapter.py` satır ~34–35:
```python
_TIER_THRESHOLDS = [2, 3, 4, 5, 6]
_TIER_BONUSES    = [3, 7, 11, 16, 18]   # ❌ engine ile uyuşmuyor
```

Oysa `engine_core/synergy.py::tier_bonus()`:
```python
N=2 → 3   # ✅ eşleşiyor
N=3 → 9   # ❌ UIAdapter 7 gösteriyor
N=4 → 16  # ✅ eşleşiyor
N=5 → 16  # ✅ eşleşiyor
N=6 → 25  # ❌ UIAdapter 18 gösteriyor
N=7 → 28  # ❌ UIAdapter'ın listesinde yok
```

**Etki:** Oyuncu "MIND 3/3 → +7" görür ama gerçekte +9 kazanır. Tier 6'da +18 görür, +25 alır. Oyun mekanikleri çalışıyor ama UI yalan söylüyor. Bu, oyuncunun karar verme sürecini yanlış yönlendirir.

**Kök neden:** `_TIER_BONUSES` listesi `constants.py::SYNERGY_TIER_*` sabitlerinden türetilmeden elle yazıldı ve sonradan `synergy.py` formülü güncellendi (P1-5 sprint'inde), UIAdapter güncellenmedi.

**Düzeltme (~15 dakika):**
```python
# v2/core/ui_adapter.py — _next_tier() metodunu değiştir
from engine_core.synergy import tier_bonus as _engine_tier_bonus

@classmethod
def _next_tier(cls, count: int) -> tuple[int | None, int | None]:
    for threshold in [2, 3, 4, 5, 6]:
        if count < threshold:
            return threshold, _engine_tier_bonus(threshold)
    return None, None
```

`_TIER_BONUSES` hardcoded listesini tamamen kaldır.

---

### YENI-2 · `board.combat_phase()` Wrapper — Duplicate Logic, Stale Lazy Import (Şiddet: YÜKSEK)

`board.py` satır ~152–214 (backward-compat wrapper):
```python
def combat_phase(board_a, board_b, ...):
    from engine_core.passive_trigger import trigger_passive   # ❌ hâlâ lazy import
    ...
    # ~55 satır tam combat döngüsü kodu
    for coord in shared_coords:
        ...
        from engine_core.damage_calculator import resolve_single_combat as _resolve  # iç içe import!
```

`combat_engine.py::_resolve_combat_phase()` ise aynı ~55 satırın birebir kopyası. İki implementasyon eş zamanlı yaşıyor:

```
board.combat_phase()              → tam implementasyon (stale)
CombatEngine._resolve_combat_phase() → tam implementasyon (güncel)
```

`test_engine_bridge_contracts.py` şu anda `board_combat_phase` wrapper'ı `combat_phase_fn` olarak inject ediyor:
```python
from engine_core.board import combat_phase as board_combat_phase
...
game = Game(..., combat_phase_fn=board_combat_phase)
```

Bu, testlerin `CombatEngine._resolve_combat_phase()`'i test etmediği anlamına geliyor. Wrapper'a bir bug eklense, testler yakalamaz.

**Düzeltme:**
```python
# engine_core/board.py — wrapper'ı gerçekten delegate et
def combat_phase(board_a, board_b,
                 combo_bonus_a, combo_bonus_b,
                 player_a=None, player_b=None, ctx=None):
    """Backward-compat wrapper — delegates to CombatEngine."""
    from engine_core.combat_engine import CombatEngine
    engine = CombatEngine.__new__(CombatEngine)  # hafif instance, players vs inject gerekmez
    # ← Bu yaklaşım çalışmaz; CombatEngine standalone çalışamaz
```

Doğru yaklaşım: `_resolve_combat_phase`'i standalone fonksiyona taşımak:
```python
# engine_core/combat_resolver.py — yeni
from engine_core.damage_calculator import resolve_single_combat
from engine_core.constants import KILL_PTS

def resolve_combat_phase(board_a, board_b, combo_bonus_a, combo_bonus_b,
                         player_a=None, player_b=None, ctx=None,
                         trigger_passive_fn=None):
    """Tek yetkili implementasyon. Board.combat_phase ve CombatEngine buraya delege eder."""
    ...
```

---

### YENI-3 · `EngineAdapter.get_hand()` Slot Pozisyonu Kaybı (Şiddet: YÜKSEK)

`engine_adapter.py` satır ~218–223:
```python
def get_hand(self, player_index: int = 0) -> list:
    hand = self._engine.players[player_index].hand
    names = [c.name for c in hand if c is not None]  # ❌ None slotları filtreler
    return names + [None] * (6 - len(names))           # trailing None'lar oluşturur
```

`perform_placement()` içindeki `preserve_slots=True` dalı:
```python
if preserve_slots:
    hand[hand_index] = None   # slot pozisyonu korunuyor
    player.hand = hand
```

Senaryo: Oyuncu 6 kartlı elde, slot 2'yi oynuyor.
- `player.hand` → `[A, B, None, D, E, F]`
- `get_hand()` → `[A, B, D, E, F, None]`  ← slot pozisyonları kaydı

Oyuncu slot 2'den sürüklemeye devam ederse (`drag_state.source_index = 2`), aslında `D` kartı oynanır. Bu, drag-drop etkileşiminde görsel ile veri arasında kayma üretir.

**Düzeltme:**
```python
def get_hand(self, player_index: int = 0) -> list:
    """Slot pozisyonlarını koruyarak 6-elemanlı liste döndür."""
    if player_index >= len(self._engine.players):
        return [None] * 6
    hand = self._engine.players[player_index].hand
    # None dahil tüm slotları koru; position integrity bozulmasın
    result = [
        (c.name if hasattr(c, "name") else None) if c is not None else None
        for c in hand[:6]
    ]
    return result + [None] * max(0, 6 - len(result))
```

`UIAdapter._build_active_player()` içindeki hand slot oluşturma da aynı hatayı içeriyor:
```python
hand_slots = [
    self._card_name(card) if card is not None else None
    for card in getattr(player, "hand", [])
]
```
Bu doğru — None'ları atlamamıyor. Ancak `get_hand()` ile uyumsuz.

---

### YENI-4 · `_clear_transient_board_state` — 3 Kopyalı Metod (Şiddet: ORTA-YÜKSEK)

Aynı metod `game.py`, `combat_engine.py` ve `turn_manager.py` içinde üç kez var:

```python
# game.py satır ~97
def _clear_transient_board_state(self, players, *, current_turn, clear_combat_meta): ...

# combat_engine.py satır ~48
def _clear_transient_board_state(self, players, *, current_turn, clear_combat_meta): ...

# turn_manager.py satır ~77
def _clear_transient_board_state(self, players, *, current_turn, clear_combat_meta): ...
```

`_iter_board_cards` da üç kopyalı. Birinde bir değişiklik (örn. `clear_meta_scope` scopeunu değiştirmek) diğerlerine yayılmaz.

**Düzeltme:** `engine_core/board_utils.py` yardımcı modülü:
```python
# engine_core/board_utils.py — yeni
def iter_board_cards(players):
    for player in players:
        for card in tuple(player.board.grid.values()):
            yield card

def clear_transient_board_state(players, *, current_turn: int, clear_combat_meta: bool) -> None:
    for card in iter_board_cards(players):
        card.clear_expired_effects(current_turn)
        if clear_combat_meta:
            card.clear_meta_scope("combat")
```

Her üç sınıf bu modülü import eder.

---

### YENI-5 · `SynergyCalculator` Class-Level Cache — Test İzolasyon Riski (Şiddet: ORTA)

```python
# v2/core/synergy_calculator.py
class SynergyCalculator:
    _last_board_hash: Optional[int] = None   # ❌ class variable
    _cached_result: Optional[SynergyComputeResult] = None  # ❌ class variable
```

Class-level cache tüm instance'lar ve tüm testler arasında paylaşılır. `GameState._instance = None` ile GameState sıfırlansa da `SynergyCalculator._last_board_hash` ve `_cached_result` kalmaya devam eder.

Test senaryosu:
```python
# Test A: 3 kartlı board, synergy=12 → cache'e yazıldı
# Test B: Board'u temizleyip yeni board kurdu → hash farklı → hesaplandı
# Test C: Aynı koordinatlarda farklı kartlar AMA aynı isimler → hash AYNI → stale cache
```

Hash `frozenset((k, name, rotation))` kullanıyor. Aynı isimli ama farklı `_pipeline` state'li kartlar aynı hash üretir.

**Düzeltme:**
```python
@classmethod
def invalidate_cache(cls) -> None:
    cls._last_board_hash = None
    cls._cached_result = None
```

Bu metod zaten var — ama test `conftest.py` her test öncesi çağırmıyor. Çözüm iki adımlı:
1. `conftest.py`'ye `SynergyCalculator.invalidate_cache()` ekle
2. Ya da cache'i instance-level'e taşı (daha doğru çözüm)

---

### YENI-6 · `StateStore._board_names/_board_rotations` — Gereksiz İkili Yazma (Şiddet: DÜŞÜK-ORTA)

`UIAdapter.build_public_state()`:
```python
if view_index == 0:
    store.update_board(0, active_player.board_cards)  # board'u store'a yazıyor
```

`PublicState.active_player.board_cards` zaten bu veriyi içeriyor. `StateStore._board_names` ve `_board_rotations` okundukları tek yer `StateStore.get_board_names/rotations()`'dır ve bunlara yalnızca eski UI kodundan erişiliyordu. Şu an `PublicState` mevcut olduğundan bu cache alanları artık kullanılmıyor.

**Etki:** Her `build_public_state()` çağrısında fazladan dict yazma. Daha önemlisi, potential desync: `store._board_names` ve `active_player.board_cards` arasındaki ayrım bir sonraki editörü karıştırır.

**Düzeltme:**
1. `StateStore`'dan `_board_names`, `_board_rotations`, `update_board()`, `get_board_names()`, `get_board_rotations()` kaldır
2. `UIAdapter`'dan `store.update_board(0, ...)` satırını kaldır
3. `board_rotations` ihtiyacı duyan UI kodu `PublicState.active_player.board_rotations`'ı kullansın

---

### YENI-7 · `UIAdapter._build_player_composition` — Hardcoded Kategori Mapper (Şiddet: DÜŞÜK-ORTA)

```python
# ui_adapter.py satır ~185
mapper = {
    "Mythology & Gods": "MYTHOLOGY",
    "Art & Culture": "ART",
    "Nature & Biology": "NATURE",
    "Nature & Creatures": "NATURE",
    "Cosmos & Space": "COSMOS",
    "Cosmos": "COSMOS",
    "Science": "SCIENCE",
    "Science & Technology": "SCIENCE",
    "History": "HISTORY",
    "History & Civilizations": "HISTORY",
}
```

`cards.json`'daki kategori string'leri değişirse bu mapper sessizce bozulur — `counts[category]` beklenmeyen bir key alır ve lobby paneli yanlış veya eksik görünür.

**Düzeltme:** `engine_core/constants.py`'ye taşı:
```python
# engine_core/constants.py
CATEGORY_DISPLAY_MAP: Dict[str, str] = {
    "Mythology & Gods": "MYTHOLOGY",
    "Art & Culture": "ART",
    ...
}
```

---

## 4. Mevcut 25 Pre-Existing Test Failure Analizi

MASTER_BACKLOG "413 passed, 25 failed (pre-existing)" diyor. Bu 25 testin kaynağı aşağıdaki gruplardır:

### Grup A: Spectate TDD (test_spectate_tdd.py)
Bu testler `spectate` özelliğini test ediyor; `GameState.set_spectate_mode()`, `get_spectate_public_state()` gibi metodlar henüz yok. Bunlar bilinçli olarak "TDD first" yazılmış, implantasyon bekliyor.

### Grup B: Phase 5 Integration (test_phase5_integration.py)
Faz 5 özelliklerini bekliyor. Kapsam dışı.

### Grup C: Shop Scene Master Integration
`test_shop_scene_master_integration.py` → `GameState` metodlarına (örneğin `get_player_composition`) erişiyor olabilir. `PublicState` migration sonrası bu test güncellenmemiş.

### Grup D: Dynamic Board Stats (test_engine_bridge_contracts.py ya da benzer)
`test_dynamic_board_stats_returned_by_adapter` — bu test hâlâ `get_board_cards()` gibi artık olmayan bir metod çağırıyor olabilir.

**Önerilen eylem:** Bu 25 testi `pytest -v --tb=short 2>&1 | grep FAILED` ile listele; hangi metodun eksik olduğunu tespit et. Çoğunlukla:
1. `GameState` method rename / removal
2. `UIAdapter`'a taşınan hesaplamalar

---

## 5. Root Cause Özeti (Güncellenmiş)

### A. Tek Yönlü Değişiklik Problemi (P1-5'ten Kaynaklı)
P1-5 sprint'inde `constants.py`'ye `SYNERGY_TIER_*` sabitleri eklendi ve `synergy.py::tier_bonus()` bunları kullandı. Ancak `UIAdapter._TIER_BONUSES` bundan habersiz — elle yazılmış liste güncellenmedi. Bu, "constants refactor" yapılırken **tüm consumers'ların taranmadığını** gösteriyor.

**Sistematik çözüm:** Bir sabit değiştiğinde "Bu sabit nerede okunuyor?" kontrolü yapılmalı. `grep -r "SYNERGY_TIER\|_TIER_BONUS"` bu boşluğu ortaya koyardı.

### B. Backward-Compat Wrapperların Yaşam Döngüsü Yok
`board.combat_phase()` wrapper'ı bir "migration completed" tarihi ya da deprecation uyarısı içermiyor. Her refactor döngüsünde bu wrapper'lar birikmektedir — şu an 4 wrapper var (`combat_phase`, `find_combos` re-export, `CombatResult` re-export, `resolve_single_combat` re-export). Bunlar için silinme planı yoksa teknik borç olarak kalır.

### C. GameState Singleton'ı Test İzolasyonunu Zedeliyor
`GameState._instance`, `SynergyCalculator._last_board_hash/_cached_result` — bunların tümü class-level state. Bir testte bırakılan state sonraki testi etkiler. `conftest.py` minimal ve yalnızca pygame'i ayarlıyor; class-level state'leri sıfırlamıyor.

---

## 6. Hafta 3 Refactor Stratejisi (Risk Sıralı)

### Adım 1 — UIAdapter._TIER_BONUSES Düzelt (30 dakika, Risk: Sıfır)

```python
# v2/core/ui_adapter.py — değiştirilecek
from engine_core.synergy import tier_bonus as _engine_tier_bonus

@classmethod
def _next_tier(cls, count: int) -> tuple[int | None, int | None]:
    for threshold in [2, 3, 4, 5, 6]:
        if count < threshold:
            return threshold, _engine_tier_bonus(threshold)
    return None, None
```

`_TIER_THRESHOLDS` ve `_TIER_BONUSES` class variable'larını kaldır.

**Test:** `test_synergy_cache.py` içine UI-engine tier bonus parity testi ekle:
```python
def test_ui_adapter_tier_bonus_matches_engine(synergy_result):
    adapter = UIAdapter()
    for count in [2, 3, 4, 5, 6]:
        _, ui_bonus = adapter._next_tier(count - 1)
        engine_bonus = tier_bonus(count)
        assert ui_bonus == engine_bonus, f"count={count}: UI={ui_bonus} != engine={engine_bonus}"
```

---

### Adım 2 — `combat_phase` Wrapper'ını Gerçek Delegate'e Dönüştür (1-2 gün)

`engine_core/combat_resolver.py` yeni modülü oluştur:
```python
# engine_core/combat_resolver.py
from engine_core.damage_calculator import resolve_single_combat
from engine_core.constants import KILL_PTS

def resolve_combat_phase(
    board_a, board_b,
    combo_bonus_a, combo_bonus_b,
    player_a=None, player_b=None,
    ctx=None,
    trigger_passive_fn=None,
) -> tuple[int, int, int]:
    """Tek yetkili combat phase implementasyonu."""
    ...  # mevcut ~55 satır buraya taşınır
```

`board.py::combat_phase` wrapper ve `combat_engine.py::_resolve_combat_phase` her ikisi de bu fonksiyona delege eder:
```python
# board.py
def combat_phase(board_a, board_b, ...):
    from engine_core.combat_resolver import resolve_combat_phase
    return resolve_combat_phase(board_a, board_b, ..., trigger_passive_fn=trigger_passive)

# combat_engine.py
def _resolve_combat_phase(self, board_a, board_b, ...):
    from engine_core.combat_resolver import resolve_combat_phase
    return resolve_combat_phase(board_a, board_b, ..., trigger_passive_fn=self._trigger_passive)
```

**Test:** `test_engine_bridge_contracts.py` içinde `board_combat_phase` injection yerine `CombatEngine`'e doğrudan test ekle.

---

### Adım 3 — `EngineAdapter.get_hand()` Slot Pozisyonu Düzelt (30 dakika)

Bkz. YENI-3 düzeltme bloğu. Ek olarak `UIAdapter._build_active_player()` içindeki hand_slots oluşturma ile tutarlılık sağla.

---

### Adım 4 — `_clear_transient_board_state` Tek Kaynak (1 gün)

`engine_core/board_utils.py` oluştur, üç kopyayı merge et. Game, CombatEngine, TurnManager'ı güncelle.

**Test:** `pytest -k "transient"` → mevcut testlerin geçmesi yeterli.

---

### Adım 5 — `StateStore` Board Cache Temizliği (yarım gün)

`_board_names`, `_board_rotations`, `update_board()`, `get_board_names()`, `get_board_rotations()` kaldır.
`UIAdapter`'dan `store.update_board(0, ...)` satırını kaldır.
Her tüketici `PublicState.active_player.board_rotations`'a yönlendir.

---

### Adım 6 — Test İzolasyon Güvenlik Ağı (yarım gün)

`conftest.py`'yi güncelle:
```python
# tests/conftest.py — eklenecek fixture
@pytest.fixture(autouse=True)
def reset_class_state():
    """Her test öncesi class-level state'leri temizle."""
    from v2.core.game_state import GameState
    from v2.core.synergy_calculator import SynergyCalculator
    GameState._instance = None
    SynergyCalculator.invalidate_cache()
    yield
    GameState._instance = None
    SynergyCalculator.invalidate_cache()
```

Bu, flaky testlerin büyük çoğunluğunu önler.

---

### Adım 7 — 25 Pre-Existing Failure Triage (1 gün)

```bash
python -m pytest --tb=short 2>&1 | grep -A 5 "FAILED"
```

Her failing test için:
- `NameError` / `AttributeError` → renamed method → testte güncelle
- `AssertionError` → behavior değişti → ya test ya kod güncellenecek
- `ImportError` → yeni modül yapısına uyarla

Tahmin: ~20/25 test birkaç satır güncellemesiyle geçer; kalan 5 spectate/phase5 scope dışı.

---

## 7. Hedef Mimari (Güncellenmiş)

### Eklenecek Modüller

```
engine_core/
  combat_resolver.py   ← YENİ: resolve_combat_phase() tek yetkili implementasyon
  board_utils.py       ← YENİ: iter_board_cards(), clear_transient_board_state()
  (combo_detector.py)  ← VAR ✅
  (damage_calculator.py) ← VAR ✅
  (synergy.py)         ← VAR ✅
  (turn_manager.py)    ← VAR ✅
  (combat_engine.py)   ← VAR ✅

v2/core/
  (public_state.py)    ← VAR ✅ — frozen DTO hiyerarşisi
  (ui_adapter.py)      ← VAR ✅ — tier_bonus düzeltmesi bekliyor
  (shop_controller.py) ← VAR ✅
  (synergy_calculator.py) ← VAR ✅ — cache isolation düzeltmesi bekliyor
  state_store.py       ← board cache alanları kaldırılacak

tests/
  conftest.py          ← class-level state reset eklenecek
```

### Kaldırılacaklar (Backward-Compat Temizliği — Phase 6)

```
engine_core/board.py:
  - combat_phase() wrapper → combat_resolver.py
  - find_combos re-export → doğrudan combo_detector import
  - CombatResult, resolve_single_combat, calculate_damage re-exportlar → kaldır
  - calculate_group_synergy_bonus() wrapper → kaldır

v2/core/state_store.py:
  - _board_names
  - _board_rotations
  - update_board()
  - get_board_names()
  - get_board_rotations()

v2/core/ui_adapter.py:
  - _TIER_THRESHOLDS hardcoded list
  - _TIER_BONUSES hardcoded list
  - _build_player_composition category mapper → constants.py'ye taşı
```

---

## 8. Kritik Sorulara Güncellenmiş Yanıtlar

**Bu sistemin şu anki en kritik kırılma noktası nedir?**  
`UIAdapter._TIER_BONUSES` mismatch. Synergy mekanikleri engine'de doğru çalışıyor, ama UI'da yanlış hedef değerleri gösteriyor. Oyuncu karar verirken `+7` görerek `+9` kazanır — bu bir "lucky bug" ama gelecekte bonus formülü değişirse tersine dönebilir. 30 dakikada kapanabilecek bu sorunun açık kalması kabul edilemez.

**Şu haliyle proje neden ölçeklenemez?**  
`GameState` singleton + `SynergyCalculator` class-level cache: spectate modu, replay, veya paralel simülasyon eklendiğinde bu iki singleton birbirini karıştırır. `GameState` DI (dependency injection) ile singleton'dan çıkarılmadıkça multi-game context imkânsız.

**Eğer hiçbir şey yapılmazsa, ilk neresi çöker?**  
İlk çökme `board.combat_phase()` wrapper'ından gelir. Wrapper'ın içindeki `from engine_core.damage_calculator import resolve_single_combat` ve `from engine_core.passive_trigger import trigger_passive` lazy importları, Python import sırası değiştiğinde ya da test isolation sorunu olduğunda `ImportError` veya stale state üretir. Özellikle `combat_phase_fn=board_combat_phase` inject eden tüm testler bu riske maruz.

---

## 9. Metrikler (Güncel)

| Metrik | v1 (Sprint Öncesi) | Şu An |
|---|---|---|
| `board.py` satır sayısı | ~449 | ~217 |
| `synergy_calculator.py` satır sayısı | ~226 | ~93 |
| `game.py` satır sayısı | ~380 | ~180 (delegeler) |
| Test sayısı | ~22 | 451 (413+38) |
| Kritik açık issue | 5 | 4 (yeni, farklı) |
| Test failure (pre-existing) | 0 (bilinmiyordu) | 25 |
| Circular import | 1 (lazy) | 1 (hâlâ lazy, wrapper'da) |
| Class-level mutable state | 0 saptanmış | 2 (GameState._instance, SynergyCalculator cache) |

---

*Bu raporun kendisi de bir snapshot'tır — kod tabanı değiştiğinde güncellenmelidir.*
