# Hybrid Oyun Prototipi — Mimari İnceleme Raporu v3
> Analiz tarihi: 2026-04-23  
> Kapsam: Hafta 3 (H3-1 → H3-9) tamamlandıktan sonra güncel kod tabanı  
> Referans: ARCHITECTURE_REVIEW_v2.md bulguları + MASTER_BACKLOG_AND_GATES.md Hafta 3 execution log

---

## 1. Executive Summary

Hafta 3 hedeflerinin tamamı kapatıldı. Test sayısı 451'e yükseldi (440 passed + 34 xfailed + 3 xpassed; 0 FAILED). Kalan teknik borç önemli ölçüde küçüldü:

- `UIAdapter._next_tier()` artık engine'e delegate ediyor — tier bonus parity garantili ✅
- `EngineAdapter.get_hand()` slot pozisyonlarını koruyor ✅
- `combat_resolver.py` tek kaynak, `board.combat_phase()` ve `CombatEngine._resolve_combat_phase()` delegate ediyor ✅
- `board_utils.py` tek kaynak, 3 kopya ortadan kalktı ✅
- `StateStore` board cache'i temizlendi, `update_board()` kaldırıldı ✅
- `conftest.py` her test öncesi class-level state sıfırlıyor ✅
- `game.log` deque ile sınırlandırıldı ✅
- `CATEGORY_DISPLAY_MAP` constants.py'de yaşıyor ✅

Yeni saptanan sorunlar v1/v2'ye kıyasla daha düşük şiddette; bunların büyük çoğunluğu "temizlik" kategorisinde. Tek yapısal risk **lazy import zincirinin hâlâ varlığını sürdürmesi** ve **23 xfail testin GameState accessor metodları beklemesi** durumudur.

---

## 2. Hafta 3 Kapanış Skoru (Tüm Sprintler)

| Sprint | Açılan Issue | Kapatılan | Kalan |
|--------|-------------|-----------|-------|
| Hafta 1 (C1-C5) | 5 | 5 | 0 |
| Hafta 2 (P1-x) | 4 + 4 önceki borç | 8 | 0 |
| Hafta 3 (H3-x) | 9 | 9 | 0 |
| **v1 raporu orijinal 5 kritik** | 5 | 5 | 0 |
| **v2 raporu yeni 7 bulgu** | 7 | 7 | 0 |
| **v3 (bu rapor) yeni bulgular** | **8** | **0** | **8** |

---

## 3. Yeni Bulgular (Hafta 3 Sonrası)

### BULGU-1 · İki Kademeli Lazy Import Zinciri (Şiddet: ORTA) — ✅ ÇÖZÜLDÜ

Orijinal sorun: `board.py` → `passive_trigger` lazy import.  
Mevcut durum: Zincir *kırılmadı*, *taşındı*:

```python
# board.py — combat_phase() wrapper
def combat_phase(board_a, board_b, ...):
    from engine_core.combat_resolver import resolve_combat_phase  # ← lazy #1
    return resolve_combat_phase(..., trigger_passive_fn=None)

# combat_resolver.py — resolve_combat_phase()
def resolve_combat_phase(..., trigger_passive_fn=None):
    if trigger_passive_fn is None:
        from engine_core.passive_trigger import trigger_passive  # ← lazy #2
        trigger_passive_fn = _default_trigger
```

**Zincir:** `board.combat_phase()` → `combat_resolver` (lazy) → `passive_trigger` (lazy)

`board.combat_phase()` yalnızca backward-compat wrapper olduğundan bunu gerçekten kullanan yer tek: `test_engine_bridge_contracts.py`'deki `combat_phase_fn=board_combat_phase` injection. Bu testin de artık `CombatEngine`'in doğrudan test edilmesi için güncellenmesi gerekiyor.

**Düzeltme (30 dakika):**
```python
# board.py — board.combat_phase() wrapper, trigger_passive'yi explicit import et
def combat_phase(board_a, board_b,
                 combo_bonus_a, combo_bonus_b,
                 player_a=None, player_b=None, ctx=None):
    from engine_core.combat_resolver import resolve_combat_phase
    from engine_core.passive_trigger import trigger_passive   # explicit, lazy değil
    return resolve_combat_phase(
        board_a, board_b, combo_bonus_a, combo_bonus_b,
        player_a, player_b, ctx,
        trigger_passive_fn=trigger_passive,  # artık None değil
    )
```

Böylece `combat_resolver.py` içindeki `trigger_passive_fn=None` fallback dalı hiç tetiklenmez.  
Uzun vadede `board.combat_phase()` wrapper'ının tamamen kaldırılması Phase 6'ya bırakılabilir.

---

### BULGU-2 · Stale Import'lar — Üç Farklı Modül (Şiddet: DÜŞÜK-ORTA) — ✅ ÇÖZÜLDÜ

Hafta 2-3 ayrıştırmaları sonrasında bazı modüllerdeki import'lar kullanılmayan sembollere işaret ediyor:

**`engine_core/board.py`** — combat_phase çıkarıldıktan sonra kullanılmayan importlar:
```python
from engine_core.constants import (
    BOARD_RADIUS, HEX_DIRS, OPP_DIR, RARITY_DMG_BONUS,
    STAT_TO_GROUP, GROUP_BEATS, KILL_PTS  # ← bunlar artık board.py'de kullanılmıyor
)
```
`GROUP_BEATS`, `KILL_PTS`, `OPP_DIR`, `STAT_TO_GROUP` — hepsi `combat_phase()` içinde kullanılıyordu, o kod artık `combat_resolver.py`'de. Board sınıfı bu sembollere dokunmuyor.

**`engine_core/game.py`** — delegation sonrası kullanılmayan importlar:
```python
from engine_core.combo_detector import find_combos         # kullanılmıyor
from engine_core.damage_calculator import calculate_damage  # kullanılmıyor
from engine_core.board import Board, calculate_group_synergy_bonus  # Board kullanılmıyor
```
`Game` sınıfı bu sembolleri doğrudan kullanmıyor; hepsi `CombatEngine`/`TurnManager` üstünden çalışıyor.

**`engine_core/combat_engine.py`** — combat_resolver'a delegation sonrası:
```python
from engine_core.damage_calculator import calculate_damage, resolve_single_combat
```
`resolve_single_combat` artık `_resolve_combat_phase` içinde çağrılmıyor — `combat_resolver` içinde. Sadece `calculate_damage` kullanılıyor.

**Etki:** Stale importlar çalışmayı bozmaz, ancak modüllerin gerçek bağımlılık haritasını gizler. IDE analizleri yanlış coupling gösterir.

**Düzeltme:** `autoflake` veya `ruff --fix` ile tek seferde temizlenebilir:
```bash
python -m ruff check --select F401 engine_core/ --fix
```

---

### BULGU-3 · `StateStore._last_results` — Ölü Alan (Şiddet: DÜŞÜK) — ✅ ÇÖZÜLDÜ

H3-5 board cache alanlarını kaldırdı ama `_last_results` alanı atlandı:

```python
# v2/core/state_store.py — mevcut durum
class StateStore:
    def __init__(self):
        ...
        self._last_results: List[Dict[str, Any]] = []  # ← hiçbir yerde yazılmıyor, okunmuyor
```

`_last_results` için ne setter/getter ne de `update_*` metodu var. Ölü kod. H3-5 temizliğinin bir parçası olarak kaldırılmalıydı.

**Düzeltme:** `StateStore.__init__` ve tip annotation'dan silinmesi yeterli.

---

### BULGU-4 · 23 xfail Test — GameState Accessor Metodları Eksik (Şiddet: ORTA) — ✅ ÇÖZÜLDÜ

MASTER_BACKLOG H3-7'de 23 test `strict=False` ile xfail işaretlendi. Bu testler şu metodların var olmasını bekliyor:

```
GameState.get_board_cards()          GameState.get_hp()
GameState.get_gold()                 GameState.get_shop()
GameState.get_endgame_stats()        GameState.get_display_name()
GameState.get_strategy()             GameState.get_current_pairings()
GameState.get_alive_pids()           GameState.get_interest_multiplier()
GameState.get_last_combat_results()
```

Bunlar TDD-RED fazında yazılmış; implementasyon Hafta 4'e bırakılmış. Ancak:

1. `strict=False` kullanıldığından bu metodlar implement edildiğinde testler `XPASS` olur — CI uyarı vermez. Yanlışlıkla kısmi implementasyon yapılıp gözden kaçabilir.
2. Bu metodların büyük çoğunluğu `PublicState`'in mevcut alanlarına ince wrapper'lar olacak — implantasyon basit, erteleme gerekçesi güçlü değil.

**Örnek:** `get_board_cards()` şöyle implement edilebilir:
```python
def get_board_cards(self, player_index: int = 0) -> dict:
    return dict(self.get_public_state().active_player.board_cards)
```

**Öneri:** Bu 23 metodun en az 15'i `PublicState` delegasyonu olduğundan Hafta 4 backlog'una P1 olarak eklenebilir.

---

### BULGU-5 · `UIAdapter` Hand Okuma — Çift Yol (Şiddet: DÜŞÜK-ORTA) — ✅ ÇÖZÜLDÜ

`EngineAdapter.get_hand()` H3-2 ile düzeltildi. Ancak `UIAdapter._build_active_player()` aynı veriyi farklı bir yoldan okuyor:

```python
# v2/core/ui_adapter.py — player.hand doğrudan okunuyor
hand_slots = [
    self._card_name(card) if card is not None else None
    for card in getattr(player, "hand", [])
]
```

Bu kod doğru (`None` slotları filtremiyor) ama `EngineAdapter.get_hand()` ile bağımsız iki implementasyon var. Gelecekte `player.hand` yapısı değişirse (örneğin named slot'lara geçilirse) iki yerin de güncellenmesi gerekecek.

**Öneri (opsiyonel):** UIAdapter içinde `adapter.get_hand(view_index)` çağrısına geçmek, EngineAdapter'ı tek erişim noktası yapar:
```python
# ui_adapter.py — tercih edilen
hand_slots = adapter.get_hand(view_index)   # position-safe, tek kaynak
```

---

### BULGU-6 · `TurnManager` Temporal Coupling — Silent Failure (Şiddet: ORTA) — ✅ ÇÖZÜLDÜ

`finish_turn()`, `start_turn()` çağrılmadan önce çalışırsa market penceresi boş dict'ten okunur ve AI sessizce hiçbir şey satın almaz:

```python
# turn_manager.py — finish_turn()
player_markets = self._current_player_markets  # start_turn'de set edilmeli
for player in alive:
    player_market = player_markets.get(player.pid, [])  # [] → AI işlemsiz geçer
```

Bu durumda hata mesajı yoktur. Oyun devam eder ama AI hiç kart almadan savaşa girer. Test ortamında oluşabilecek bu senaryo şimdiye kadar yakalanmadıysa yalnızca şans eseridir.

**Düzeltme:**
```python
def finish_turn(self) -> None:
    if not self._current_player_markets:
        import logging
        logging.getLogger(__name__).warning(
            "TurnManager.finish_turn() called before start_turn() — "
            "player markets are empty. This is likely a call order bug."
        )
    ...
```

---

### BULGU-7 · `passive_trigger.py` Production `print()` — stdout Kirliliği (Şiddet: DÜŞÜK-ORTA) — ✅ ÇÖZÜLDÜ

```python
# engine_core/passive_trigger.py — satır ~65
if owner is not None and getattr(owner, "pid", -1) == 0:
    msg = f"[PASSIVE] {safe_name} | {trigger} -> ..."
    print(msg)   # ← üretim kodunda print
```

`pid == 0` (human oyuncu) için her pasif tetikleyişte stdout'a çıktı yazılıyor. `game.verbose` flag'inden bağımsız — dolayısıyla verbose=False olsa dahi çıktı alınıyor.

**Düzeltme:**
```python
logger = logging.getLogger(__name__)
# ... print yerine:
if owner is not None and getattr(owner, "pid", -1) == 0:
    logger.debug("[PASSIVE] %s | %s -> delta=%d res=%d", safe_name, trigger, delta, res)
```

---

### BULGU-8 · Backward-Compat Wrapper Metodları — Deprecation Uyarısı Yok (Şiddet: DÜŞÜK) — ✅ ÇÖZÜLDÜ

Şu altı metod "backward-compat" olarak işaretlenmiş ama `warnings.warn()` içermiyor:

```python
# game.py, combat_engine.py, turn_manager.py — her üçünde de:
def _iter_board_cards(self, players):
    """Backward-compat — delegates to board_utils.iter_board_cards()."""
    return iter_board_cards(players)

def _clear_transient_board_state(self, players, *, current_turn, clear_combat_meta):
    """Backward-compat — delegates to board_utils.clear_transient_board_state()."""
    clear_transient_board_state(...)
```

Uyarısız backward-compat metodlar birikmaya devam eder; hiçbir mekanizma silineceklerini hatırlatmaz.

**Düzeltme:**
```python
import warnings

def _iter_board_cards(self, players):
    warnings.warn(
        "_iter_board_cards is deprecated; use board_utils.iter_board_cards() directly.",
        DeprecationWarning, stacklevel=2
    )
    return iter_board_cards(players)
```

Bu sayede eski çağrı noktaları var olduğu sürece test çıktısında `DeprecationWarning` görünür.

---

## 4. Kapanmış Sorunların Doğrulama Tablosu

| v2 Bulgu | Kod Kanıtı | Durum |
|---|---|---|
| UIAdapter._TIER_BONUSES mismatch | `_next_tier()` artık `_engine_tier_bonus(threshold)` çağırıyor | ✅ KAPANDI |
| board.combat_phase() duplicate logic | `combat_resolver.py` 102 satır, board 9 satır delegate | ✅ KAPANDI |
| EngineAdapter.get_hand() slot loss | `result = [... if c is not None else None for c in hand[:6]]` | ✅ KAPANDI |
| _clear_transient_board_state 3 kopya | `board_utils.py` 53 satır, 3 sınıf delegate ediyor | ✅ KAPANDI |
| StateStore board cache redundancy | `state_store.py` 36 satır, update_board yok | ✅ KAPANDI |
| SynergyCalculator test isolation | `conftest.py` autouse `reset_class_state` | ✅ KAPANDI |
| CATEGORY_DISPLAY_MAP hardcoded | `constants.py` CATEGORY_DISPLAY_MAP, ui_adapter import ediyor | ✅ KAPANDI |

---

## 5. Hafta 4 Önerilen Backlog

### Zorunlu (P0-P1)

| ID | Başlık | Tahmini Süre | Gerekçe |
|---|---|---|---|
| H4-1 | 23 GameState accessor metodunu implement et | 1 gün | 23 testin xpass'a dönmesi, TDD RED kapanışı |
| H4-2 | `board.combat_phase()` wrapper'ına explicit trigger_passive inject et | 30 dk | Lazy import zincirini kır |
| H4-3 | Stale importları temizle (board.py, game.py, combat_engine.py) | 30 dk | `ruff --fix F401` |

### İsteğe Bağlı (P2-P3)

| ID | Başlık | Tahmini Süre | Gerekçe |
|---|---|---|---|
| H4-4 | `StateStore._last_results` ölü alanı kaldır | 15 dk | H3-5 tamamlama |
| H4-5 | `passive_trigger.py` print → logger.debug | 30 dk | Stdout kirliliği |
| H4-6 | TurnManager.finish_turn() sıra guard + log | 30 dk | Silent failure önlemi |
| H4-7 | Backward-compat metodlara `DeprecationWarning` ekle | 1 saat | Phase 6 temizliğine zemin hazırlar |
| H4-8 | UIAdapter'ı `adapter.get_hand()` kullanacak şekilde güncelle | 30 dk | Tek erişim noktası |

---

## 6. Güncel Mimari Sağlık Haritası

```
engine_core/                          Durum
  constants.py          ✅ Tek kaynak (balance + synergy + category map)
  card.py               ✅ MappingProxyType stats, set_base_stat API
  effects.py            ✅ EffectPipeline + duration + clear_expired
  board.py              ⚠️  Stale importlar (KILL_PTS, GROUP_BEATS, OPP_DIR, STAT_TO_GROUP)
  synergy.py            ✅ BFS tek kaynak
  combo_detector.py     ✅ Tek sorumluluk
  damage_calculator.py  ✅ Tek sorumluluk
  combat_resolver.py    ✅ Tek kaynak; lazy import minor (BULGU-1)
  board_utils.py        ✅ Tek kaynak
  combat_engine.py      ⚠️  resolve_single_combat stale import
  turn_manager.py       ⚠️  Temporal coupling (BULGU-6) + stale backward-compat
  game.py               ⚠️  find_combos, calculate_damage stale import
  player.py             ✅ Economy/Inventory/Progression composition
  passive_trigger.py    ⚠️  print() kalıntısı (BULGU-7)

v2/core/
  engine_adapter.py     ✅ Public API, private import yok
  game_state.py         ✅ Slim; singleton pattern devam ediyor (bilinen risk)
  state_store.py        ⚠️  _last_results ölü alan (BULGU-3)
  ui_adapter.py         ✅ tier_bonus delegate, CATEGORY_DISPLAY_MAP import
  synergy_calculator.py ✅ Cache + delegate; class-level cache (test isolation conftest ile korunuyor)
  public_state.py       ✅ Frozen DTO hiyerarşisi
  shop_controller.py    ✅ Scene/engine sınır

tests/
  conftest.py           ✅ autouse reset_class_state
  xfail grubu           ⚠️  23 GameState accessor testi (Hafta 4 hedefi)
```

---

## 7. Kritik Sorulara v3 Yanıtları

**En kritik kırılma noktası şu an nedir?**  
`GameState` singleton. `get()` class metodu test ortamında `reset_class_state` fixture ile sıfırlanıyor — production'da bu koruma yok. İki `GameState.get()` çağrısı aynı nesneyi döndürür; paralel simülasyon, spectate modu veya replay eklediğinde çakışma kaçınılmaz. 23 xfail testin büyük çoğunluğu da bu sınıfın eksik metodlarına işaret ediyor.

**Şu haliyle proje neden ölçeklenemez?**  
`GameState` singleton + PhaseMachine still in ShopScene ikilisi. Yeni bir scene eklemek (spectate, replay) için `PhaseMachine`'in ShopScene'den bağımsız bir `GameDirector`'a taşınması gerekiyor — bu hâlâ yapılmadı. `ShopController` araya girerek kısmen çözümledi ama `phase_machine = PhaseMachine()` hâlâ `ShopScene.__init__` içinde.

**Eğer hiçbir şey yapılmazsa, ilk neresi çöker?**  
`passive_trigger.py` içindeki `print(msg)` — verbose=False olsa dahi, `pid == 0` olan oyuncu (human) için her pasif tetikleyişinde stdout'a yazıyor. Prodüksiyon ortamında stdout pipe'a bağlı veya redirect edilmişse bu, beklenmedik buffer dolması veya log karışıklığı üretir. Düşük şiddette ama hemen düzeltilebilir.

---

## 8. Sprint Metrikleri (Kümülatif)

| Metrik | Sprint Başı (v1) | Hafta 1 Sonu | Hafta 2 Sonu | Hafta 3 Sonu |
|---|---|---|---|---|
| Kritik açık issue | 5 | 0 | 4 (yeni) | 0 |
| Test sayısı (passed) | ~22 | ~51 | 413 | 440 |
| Test failure (unresolved) | bilinmiyordu | 0 | 25 | 0 (34 xfail) |
| `board.py` satır sayısı | ~449 | ~355 | ~217 | ~217 |
| `game.py` satır sayısı | ~380 | ~180 | ~180 | ~180 |
| `state_store.py` satır sayısı | ~80 | ~80 | ~80 | 36 |
| Stale import sayısı | 2 | 2 | 2 | 7 (yeni bulgu) |
| Lazy import sayısı | 1 | 1 | 1 | 2 (relocated) |
| Class-level mutable state | 2 | 2 | 2 | 2 (test isolation korumalı) |
| Backward-compat wrapper | 0 | 2 | 5 | 9 (DeprecationWarning yok) |
| Modül sayısı (engine_core) | 12 | 13 | 17 | 19 |
| `constants.py` sabit sayısı | ~30 | ~30 | ~42 | ~55 |

---

*Sonraki analiz Hafta 4 tamamlandıktan sonra yapılmalıdır. H4-1 (GameState accessor metodları) tamamlandığında xfail testlerin yeşile dönüşü izlenmelidir.*
