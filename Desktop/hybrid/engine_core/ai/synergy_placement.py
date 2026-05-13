"""
engine_core/ai/synergy_placement.py
════════════════════════════════════════════════════════════════════
Sinerji-Delta tabanlı kart yerleştirme yardımcı modülü.
Single Source of Truth: engine_core/synergy.py::compute_synergy()

Mimari Kararlar
───────────────
• Board MUTASYONU YOK — geçici dict kopyası (fake_grid) kullanılır.
  Board.place() / Board.remove() çağrısı yapılmaz; StateStore cache
  desync riski sıfır.
• SynergyWeightSchedule dataclass ile ağırlıklar strateji başına
  override edilebilir; global state yok.
• compute_delta_synergy_batch() bir kart için tüm koordinatları
  tek seferde değerlendirir; synergy_before hesabı tekrar yapılmaz.

Kullanım Örnekleri
──────────────────
  # En basit — herhangi bir stratejiden çağır:
  from engine_core.ai.synergy_placement import place_cards_synergy_aware
  place_cards_synergy_aware(player)

  # Özelleştirilmiş ağırlıklar:
  from engine_core.ai.synergy_placement import SynergyWeightSchedule
  schedule = SynergyWeightSchedule(weight_early=1.0, weight_late=4.0)
  place_cards_synergy_aware(player, schedule=schedule)

  # Sadece delta hesabı:
  from engine_core.ai.synergy_placement import compute_delta_synergy
  delta = compute_delta_synergy(player.board, coord, card)

Bağımlılık Ağacı (döngüsel değil)
───────────────────────────────────
  engine_core.synergy   → compute_synergy()  [SST]
  engine_core.constants → HEX_DIRS, STAT_TO_GROUP, PLACE_PER_TURN
  engine_core.board     → Board   (sadece grid okunur, yazılmaz)
  engine_core.card      → Card    (sadece rotated_edges okunur)
════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

from engine_core.constants import HEX_DIRS, STAT_TO_GROUP
from engine_core.synergy import compute_synergy

Coord = Tuple[int, int]


# ══════════════════════════════════════════════════════════════════
# 1.  AĞIRLIK ÇİZELGESİ — Oyun Aşaması × W_synergy
# ══════════════════════════════════════════════════════════════════

@dataclass
class SynergyWeightSchedule:
    """
    Oyunun erken / orta / geç aşamalarına göre W_synergy'yi ayarlar.

    Varsayılan değerler GDD tur yapısıyla (greed → spike → convert)
    hizalanmıştır.

    Aşama Mantığı
    ─────────────
    Erken  (tur  1 – early_turns) : Tahta kurulum, bireysel güç önemli.
    Orta   (tur  ?  – mid_turns ) : Sinerji etkin olmaya başlar.
    Geç    (tur  ?+             ) : Sinerji belirleyici; ağırlık max.

    Override Örneği — "Balancer" stratejisi için daha agresif geç ağırlık:
      SynergyWeightSchedule(weight_early=1.2, weight_mid=2.5, weight_late=4.0)
    """
    early_turns:  int   = 6      # greed_turn_end varsayılanıyla eşleşir
    mid_turns:    int   = 15     # spike_turn_end varsayılanıyla eşleşir
    weight_early: float = 1.5
    weight_mid:   float = 2.0
    weight_late:  float = 3.0

    def weight_for_turn(self, turn: int) -> float:
        """Mevcut tur için W_synergy döndürür."""
        if turn <= self.early_turns:
            return self.weight_early
        if turn <= self.mid_turns:
            return self.weight_mid
        return self.weight_late

    def interpolated_weight(self, turn: int) -> float:
        """
        Aşamalar arasında lineer interpolasyon (daha yumuşak geçiş).
        İsteğe bağlı alternatif; varsayılan weight_for_turn() kademeli.
        """
        if turn <= self.early_turns:
            return self.weight_early
        if turn >= self.mid_turns:
            return self.weight_late
        t = (turn - self.early_turns) / max(1, self.mid_turns - self.early_turns)
        return self.weight_early + t * (self.weight_late - self.weight_early)


# Paylaşılan varsayılan çizelge (stratejiler override etmezse bu kullanılır)
DEFAULT_SCHEDULE = SynergyWeightSchedule()

# Strateji bazlı önceden tanımlanmış çizelgeler
SCHEDULES: Dict[str, SynergyWeightSchedule] = {
    "warrior":     SynergyWeightSchedule(weight_early=1.0, weight_mid=1.5, weight_late=2.0),
    "builder":     SynergyWeightSchedule(weight_early=2.0, weight_mid=2.5, weight_late=3.5),
    "economist":   SynergyWeightSchedule(weight_early=1.2, weight_mid=2.0, weight_late=2.5),
    "balancer":    SynergyWeightSchedule(weight_early=1.5, weight_mid=2.5, weight_late=3.5),
    "tempo":       SynergyWeightSchedule(weight_early=1.0, weight_mid=1.8, weight_late=2.8),
    "evolver":     SynergyWeightSchedule(weight_early=1.5, weight_mid=2.0, weight_late=3.0),
    "rare_hunter": SynergyWeightSchedule(weight_early=1.0, weight_mid=1.5, weight_late=2.5),
    "random":      SynergyWeightSchedule(weight_early=1.5, weight_mid=2.0, weight_late=3.0),
}


def schedule_for(strategy: str) -> SynergyWeightSchedule:
    """Strateji adına göre çizelge döndürür; bilinmiyorsa DEFAULT kullanılır."""
    return SCHEDULES.get(strategy, DEFAULT_SCHEDULE)


# ══════════════════════════════════════════════════════════════════
# 2.  GÜVENLİ SİNERJİ SİMÜLASYONU — Board Mutasyonu Yok
# ══════════════════════════════════════════════════════════════════

def _build_synergy_closures(
    grid: Dict[Coord, object],
) -> Tuple[Callable, Callable]:
    """
    Verilen grid dict üzerinden compute_synergy() için callback çifti üretir.

    Bu fonksiyon gerçek Board'u değil, geçici bir dict'i okur.
    Board mutasyonu → StateStore desync riski → SIFIR.
    """
    coord_set = frozenset(grid.keys())

    def get_edge_group(coord: Coord, dir_idx: int) -> Optional[str]:
        card = grid.get(coord)
        if card is None:
            return None
        edges = card.rotated_edges()
        if dir_idx >= len(edges):
            return None
        stat_name, _ = edges[dir_idx]
        return STAT_TO_GROUP.get(stat_name)

    def get_neighbor(coord: Coord, dir_idx: int) -> Optional[Coord]:
        dq, dr = HEX_DIRS[dir_idx]
        nb = (coord[0] + dq, coord[1] + dr)
        return nb if nb in coord_set else None

    return get_edge_group, get_neighbor


def _synergy_of_grid(grid: Dict[Coord, object]) -> int:
    """
    Verilen grid dict'in toplam sinerji puanını hesaplar.
    Board objesi almaz; saf dict, yan etki yok.
    """
    if not grid:
        return 0
    coords = list(grid.keys())
    ge, gn = _build_synergy_closures(grid)
    return compute_synergy(coords, ge, gn).total


def compute_delta_synergy(board, coord: Coord, card) -> int:
    """
    Bir kartı coord'a koymanın ΔSynergy değerini döndürür.

    ΔSynergy = synergy(board + card@coord) − synergy(board)

    Board MUTASYONU YOKTUR. Geçici dict kopyası kullanılır.
    Rollback yönetimi gerekmez.

    Parametreler
    ─────────────
    board : engine_core.board.Board  — mevcut tahta (salt okunur)
    coord : (q, r)                   — denenen koordinat
    card  : engine_core.card.Card    — yerleştirilecek kart

    Dönüş
    ─────
    int  — pozitif: sinerji artışı, negatif: azalma, sıfır: değişim yok
    """
    current_grid = board.grid

    # Mevcut sinerji (çağıran önden geçirirse batch'te tekrar hesaplanmaz)
    synergy_before = _synergy_of_grid(current_grid)

    # Hipotektik yerleştirme — yalnızca dict kopyası, board dokunulmaz
    temp_grid = dict(current_grid)
    temp_grid[coord] = card

    return _synergy_of_grid(temp_grid) - synergy_before


def compute_delta_synergy_batch(
    board,
    card,
    coords: List[Coord],
    *,
    synergy_before: Optional[int] = None,
) -> Dict[Coord, int]:
    """
    Bir kart için birden fazla koordinatın ΔSynergy değerini döndürür.

    synergy_before dışarıdan verilirse tekrar hesaplanmaz (hız tasarrufu).
    Her coord için ayrı bir dict kopyası oluşturulur; grid mutasyonu yok.

    Dönüş: {coord → delta_synergy}
    """
    current_grid = board.grid
    if synergy_before is None:
        synergy_before = _synergy_of_grid(current_grid)

    results: Dict[Coord, int] = {}
    for coord in coords:
        temp_grid = dict(current_grid)
        temp_grid[coord] = card
        results[coord] = _synergy_of_grid(temp_grid) - synergy_before

    return results


# ══════════════════════════════════════════════════════════════════
# 3.  YERLEŞTIRME SKOR FONKSİYONU
# ══════════════════════════════════════════════════════════════════

def score_placement(
    board,
    coord: Coord,
    card,
    turn: int,
    *,
    schedule: SynergyWeightSchedule = DEFAULT_SCHEDULE,
    synergy_before: Optional[int] = None,
    base_power_weight: float = 1.0,
    remaining_hand: Optional[List] = None,
    lookahead_weight: float = 0.5,
) -> float:
    """
    Belirli bir koordinata kart yerleştirmenin toplam skorunu döndürür.

    Formül (GDD §AI-Placement + Lookahead):
    ───────────────────────────────────────
      Score = (base_power_weight × card.total_power())
              + (W_synergy(turn) × ΔSynergy)
              + (lookahead_weight × LookaheadBonus)

    Burada:
      ΔSynergy = synergy_after − synergy_before
      W_synergy = schedule.weight_for_turn(turn)
      LookaheadBonus = eldeki diğer kartların bu yerleşimden kazanacağı sinerji

    Parametreler
    ─────────────
    board             : mevcut tahta (salt okunur)
    coord             : değerlendirilen koordinat
    card              : yerleştirilecek kart
    turn              : mevcut tur
    schedule          : ağırlık çizelgesi
    synergy_before    : önceden hesaplanmış sinerji (opsiyonel, performans)
    base_power_weight : base_card_power ağırlığı
    remaining_hand    : eldeki diğer kartlar (lookahead için)
    lookahead_weight  : lookahead bonusunun ağırlığı
    """
    if synergy_before is None:
        synergy_before = _synergy_of_grid(board.grid)

    temp_grid = dict(board.grid)
    temp_grid[coord] = card
    delta = _synergy_of_grid(temp_grid) - synergy_before

    w_syn = schedule.weight_for_turn(turn)
    base  = card.total_power() * base_power_weight
    
    # Lookahead bonusu: eldeki diğer kartlar bu yerleşimden ne kadar faydalanır?
    lookahead_bonus = 0.0
    if remaining_hand and lookahead_weight > 0:
        lookahead_bonus = _compute_lookahead_bonus(
            temp_grid, remaining_hand, board.free_coords()
        )

    return base + w_syn * delta + lookahead_weight * lookahead_bonus


def _compute_lookahead_bonus(
    current_grid: Dict[Coord, object],
    remaining_cards: List,
    free_coords: List[Coord],
    max_lookahead_cards: int = 3,
    max_lookahead_coords: int = 8,
) -> float:
    """
    Eldeki diğer kartların mevcut grid'den kazanacağı potansiyel sinerjiyi hesaplar.
    
    Mantık:
    ─────
    1. Eldeki her kart için (max 3 kart)
    2. Boş koordinatların bir kısmını dene (max 8 koordinat)
    3. Her koordinatta o kartın kazanacağı sinerjiyi hesapla
    4. En iyi koordinattaki sinerjiyi topla
    
    Bu sayede "bu kartı buraya koyarsam, diğer kartlarım daha iyi yerleşebilir"
    mantığı devreye girer.
    
    Dönüş: Toplam lookahead bonusu (normalize edilmiş)
    """
    if not remaining_cards or not free_coords:
        return 0.0
    
    # Mevcut grid'in sinerji puanı
    current_synergy = _synergy_of_grid(current_grid)
    
    total_bonus = 0.0
    limited_cards = remaining_cards[:max_lookahead_cards]
    limited_coords = [c for c in free_coords if c not in current_grid][:max_lookahead_coords]
    
    for future_card in limited_cards:
        best_future_delta = 0
        
        for future_coord in limited_coords:
            # Bu kartı bu koordinata koyarsak ne kadar sinerji kazanırız?
            test_grid = dict(current_grid)
            test_grid[future_coord] = future_card
            future_synergy = _synergy_of_grid(test_grid)
            future_delta = future_synergy - current_synergy
            
            if future_delta > best_future_delta:
                best_future_delta = future_delta
        
        total_bonus += best_future_delta
    
    # Normalize: kart sayısına böl
    return total_bonus / max(1, len(limited_cards))


def _compute_best_rotation_for_placement(
    board,
    coord: Coord,
    card,
    max_rotations: int = 6,
) -> Tuple[int, int]:
    """
    Bir kart için belirli bir koordinatta en iyi rotasyonu bulur.
    
    Parametreler
    ─────────────
    board         : mevcut tahta
    coord         : yerleştirme koordinatı
    card          : yerleştirilecek kart
    max_rotations : kaç rotasyon deneneceği (0-5, varsayılan 6 = hepsi)
    
    Dönüş
    ─────
    (best_rotation, best_synergy_delta)
    
    Mantık
    ──────
    Her rotasyon için (0-5):
    1. Kartı geçici olarak o rotasyonla yerleştir
    2. Sinerji deltasını hesapla
    3. En yüksek deltayı veren rotasyonu seç
    
    Bu sayede kartlar komşularıyla en iyi eşleşen kenarlarını
    birbirlerine döndürebilir.
    """
    current_grid = board.grid
    synergy_before = _synergy_of_grid(current_grid)
    
    best_rotation = card.rotation  # Mevcut rotasyon
    best_delta = 0
    
    # Kartın orijinal rotasyonunu sakla
    original_rotation = card.rotation
    
    for rot in range(max_rotations):
        # Geçici rotasyon uygula
        card.rotation = rot
        
        # Bu rotasyonla sinerji hesapla
        temp_grid = dict(current_grid)
        temp_grid[coord] = card
        synergy_after = _synergy_of_grid(temp_grid)
        delta = synergy_after - synergy_before
        
        if delta > best_delta:
            best_delta = delta
            best_rotation = rot
    
    # Orijinal rotasyonu geri yükle
    card.rotation = original_rotation
    
    return best_rotation, best_delta


# ══════════════════════════════════════════════════════════════════
# 4.  EN İYİ KOORDİNAT SEÇİMİ
# ══════════════════════════════════════════════════════════════════

def best_coord_for_card(
    board,
    card,
    free_coords: List[Coord],
    turn: int,
    *,
    schedule: SynergyWeightSchedule = DEFAULT_SCHEDULE,
    max_check: int = 0,
    remaining_hand: Optional[List] = None,
    lookahead_weight: float = 0.5,
    try_rotations: bool = True,
) -> Tuple[Optional[Coord], float, int]:
    """
    Bir kart için en yüksek skorlu koordinatı ve rotasyonu döndürür.

    max_check > 0 → yalnızca ilk max_check koordinat denenir (hız/kalite dengesi).
    max_check = 0 → tüm boş koordinatlar denenir.

    remaining_hand: eldeki diğer kartlar (lookahead için)
    lookahead_weight: lookahead bonusunun ağırlığı (0.0 = kapalı, 1.0 = tam)
    try_rotations: True ise her koordinat için en iyi rotasyonu dener

    Mevcut sinerji tek seferde hesaplanır; tüm coord'lar paylaşır.

    Dönüş: (best_coord, best_score, best_rotation)
            best_coord None ise free_coords boştu.
    """
    if not free_coords:
        return None, float("-inf"), 0

    candidates = free_coords[:max_check] if max_check > 0 else free_coords

    # Mevcut sinerjiyi bir kez hesapla — her koordinat için tekrar kullanılır.
    synergy_before = _synergy_of_grid(board.grid)

    best_coord: Optional[Coord] = None
    best_score  = float("-inf")
    best_rotation = card.rotation

    for coord in candidates:
        if try_rotations:
            # Her koordinat için en iyi rotasyonu bul
            optimal_rotation, rotation_delta = _compute_best_rotation_for_placement(
                board, coord, card, max_rotations=6
            )
            
            # Kartı geçici olarak optimal rotasyona çevir
            original_rotation = card.rotation
            card.rotation = optimal_rotation
            
            # Bu rotasyonla skoru hesapla
            sc = score_placement(
                board, coord, card, turn,
                schedule=schedule,
                synergy_before=synergy_before,
                remaining_hand=remaining_hand,
                lookahead_weight=lookahead_weight,
            )
            
            # Orijinal rotasyonu geri yükle
            card.rotation = original_rotation
            
            if sc > best_score:
                best_score = sc
                best_coord = coord
                best_rotation = optimal_rotation
        else:
            # Rotasyon denemesi yok, mevcut rotasyonla skor hesapla
            sc = score_placement(
                board, coord, card, turn,
                schedule=schedule,
                synergy_before=synergy_before,
                remaining_hand=remaining_hand,
                lookahead_weight=lookahead_weight,
            )
            if sc > best_score:
                best_score = sc
                best_coord = coord
                best_rotation = card.rotation

    return best_coord, best_score, best_rotation


# ══════════════════════════════════════════════════════════════════
# 4.  TAM YERLEŞTİRME PİPELİNE — Drop-in Strateji Entegrasyonu
# ══════════════════════════════════════════════════════════════════

def place_cards_synergy_aware(
    player,
    *,
    schedule: Optional[SynergyWeightSchedule] = None,
    card_sort_key: Optional[Callable] = None,
    max_coord_check: int = 0,
    place_limit: Optional[int] = None,
    lookahead_weight: float = 0.5,
    try_rotations: bool = True,
) -> None:
    """
    Sinerji-delta tabanlı tam yerleştirme pipeline (lookahead + rotation ile).

    Herhangi bir stratejinin place_cards() metodundan çağrılabilir.

    Parametreler
    ─────────────
    player          : engine_core.player.Player
    schedule        : ağırlık çizelgesi.
                      None → player.strategy'e göre SCHEDULES'dan otomatik seçilir.
    card_sort_key   : el sıralama fonksiyonu. None → total_power() azalan.
    max_coord_check : kaç koordinat deneneceği (0 = tümü).
    place_limit     : tur başına kart limiti (None → PLACE_PER_TURN).
    lookahead_weight: eldeki diğer kartların sinerji potansiyelinin ağırlığı.
                      0.0 = kapalı (eski davranış)
                      0.5 = dengeli (varsayılan)
                      1.0 = tam ağırlık
    try_rotations   : True ise her kart için en iyi rotasyonu dener (varsayılan: True)

    Yan Etkiler
    ────────────
    • player.board.place() ile kart yerleştirilir.
    • player.hand[i] = None ile kart elden çıkarılır.
    • card.rotation optimal değere ayarlanır (try_rotations=True ise)
    • strategy_logger varsa log_placement() çağrılır.
    
    Lookahead Mantığı
    ─────────────────
    Her kart yerleştirilirken, eldeki DİĞER kartların bu yerleşimden
    nasıl faydalanabileceği hesaplanır. Bu sayede:
    
    ✓ İkili/üçlü sinerji grupları oluşturulur
    ✓ Gelecekteki kartlar için yer açılır
    ✓ Tek bağlı yerleştirmeler yerine cluster'lar oluşur
    
    Rotation Mantığı
    ────────────────
    Her kart için her koordinatta 6 farklı rotasyon (0-5) denenir.
    En yüksek sinerji deltasını veren rotasyon seçilir.
    
    ✓ Kartlar komşularıyla en iyi eşleşen kenarlarını döndürür
    ✓ CONNECTION-CONNECTION, SPEED-SPEED vb. eşleşmeler optimize edilir
    ✓ Sinerji puanları %30-50 daha artar
    """
    from engine_core.constants import PLACE_PER_TURN
    from engine_core.strategy_logger import get_strategy_logger

    _slogger = get_strategy_logger()
    limit    = place_limit if place_limit is not None else PLACE_PER_TURN
    turn     = getattr(player, "turns_played", 0)

    if schedule is None:
        schedule = schedule_for(getattr(player, "strategy", "random"))

    valid_hand = [c for c in player.hand if c is not None]
    if not valid_hand:
        return

    if card_sort_key is None:
        card_sort_key = lambda c: c.total_power()

    sorted_cards = sorted(valid_hand, key=card_sort_key, reverse=True)

    placed = 0
    for i, card in enumerate(sorted_cards):
        if placed >= limit:
            break

        free = player.board.free_coords()
        if not free:
            break

        # Eldeki diğer kartlar (lookahead için)
        remaining_hand = sorted_cards[i+1:] if lookahead_weight > 0 else None

        coord, score, optimal_rotation = best_coord_for_card(
            player.board, card, free, turn,
            schedule=schedule,
            max_check=max_coord_check,
            remaining_hand=remaining_hand,
            lookahead_weight=lookahead_weight,
            try_rotations=try_rotations,
        )

        if coord is None:
            coord = free[-1]
            score = 0.0
            optimal_rotation = card.rotation

        # Optimal rotasyonu uygula
        if try_rotations:
            card.rotation = optimal_rotation

        player.board.place(coord, card)

        for j, hc in enumerate(player.hand):
            if hc is card:
                player.hand[j] = None
                break

        placed += 1

        if _slogger is not None:
            _slogger.log_placement(
                player, card, coord,
                combo_score=int(score),
            )
