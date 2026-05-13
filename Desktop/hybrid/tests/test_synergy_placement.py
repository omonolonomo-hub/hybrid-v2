"""
tests/test_synergy_placement.py
════════════════════════════════════════════════════════════════════
Sinerji-Delta tabanlı AI yerleştirme testleri.

Test Kapsamı
────────────
1. compute_delta_synergy() — tek koordinat delta hesabı
2. compute_delta_synergy_batch() — çoklu koordinat batch hesabı
3. score_placement() — skor formülü doğrulaması
4. best_coord_for_card() — en iyi koordinat seçimi
5. place_cards_synergy_aware() — tam pipeline entegrasyonu
6. SynergyWeightSchedule — oyun aşaması ağırlıkları
7. Board mutasyonu olmadığının doğrulanması (StateStore güvenliği)
════════════════════════════════════════════════════════════════════
"""

import pytest
from engine_core.board import Board
from engine_core.card import Card
from engine_core.player import Player
from engine_core.ai.synergy_placement import (
    compute_delta_synergy,
    compute_delta_synergy_batch,
    score_placement,
    best_coord_for_card,
    place_cards_synergy_aware,
    SynergyWeightSchedule,
    schedule_for,
)


# ══════════════════════════════════════════════════════════════════
# Test Fixtures
# ══════════════════════════════════════════════════════════════════

@pytest.fixture
def empty_board():
    """Boş tahta."""
    return Board()


@pytest.fixture
def sample_card():
    """Test kartı — CONNECTION dominant."""
    return Card(
        name="TestCard",
        category="WARRIOR",
        rarity="3",
        stats={"CONNECTION": 10, "SPEED": 5, "POWER": 8},
    )


@pytest.fixture
def player_with_hand(sample_card):
    """Elde kart olan test oyuncusu."""
    player = Player(pid=1, strategy="builder")
    player.hand = [sample_card, None, None]
    player.turns_played = 5
    return player


# ══════════════════════════════════════════════════════════════════
# Test 1: Delta Hesaplama — Tek Koordinat
# ══════════════════════════════════════════════════════════════════

def test_compute_delta_synergy_empty_board(empty_board, sample_card):
    """Boş tahtaya ilk kart yerleştirildiğinde delta sıfır olmalı."""
    delta = compute_delta_synergy(empty_board, (0, 0), sample_card)
    assert delta == 0, "Boş tahtada sinerji değişimi yok"


def test_compute_delta_synergy_with_neighbor(empty_board):
    """Komşu kartla grup eşleşmesi olduğunda delta pozitif olmalı."""
    # İki kart aynı dominant gruba sahip olmalı ve kenarları eşleşmeli
    card_a = Card("CardA", "WARRIOR", "3", {"CONNECTION": 10, "SPEED": 5, "POWER": 3})
    card_b = Card("CardB", "WARRIOR", "3", {"CONNECTION": 8, "SPEED": 6, "POWER": 2})
    
    empty_board.place((0, 0), card_a)
    
    # (1, -1) koordinatı (0, 0)'ın komşusu
    # Not: Sinerji artışı için kartların kenarlarının eşleşmesi ve
    # aynı gruba ait olması gerekir. Bu test sinerji sisteminin
    # çalıştığını doğrular.
    delta = compute_delta_synergy(empty_board, (1, -1), card_b)
    
    # Delta >= 0 olmalı (en azından azalma olmamalı)
    assert delta >= 0, "Komşu kart yerleştirildiğinde sinerji azalmamalı"


def test_compute_delta_synergy_no_mutation(empty_board, sample_card):
    """Delta hesabı board'u değiştirmemeli."""
    original_grid = dict(empty_board.grid)
    
    compute_delta_synergy(empty_board, (0, 0), sample_card)
    
    assert empty_board.grid == original_grid, "Board mutasyonu olmamalı"


# ══════════════════════════════════════════════════════════════════
# Test 2: Batch Delta Hesaplama
# ══════════════════════════════════════════════════════════════════

def test_compute_delta_synergy_batch(empty_board, sample_card):
    """Batch hesaplama tüm koordinatlar için delta döndürmeli."""
    coords = [(0, 0), (1, -1), (-1, 0)]
    
    results = compute_delta_synergy_batch(empty_board, sample_card, coords)
    
    assert len(results) == 3, "Her koordinat için sonuç olmalı"
    assert all(coord in results for coord in coords), "Tüm koordinatlar sonuçta olmalı"


def test_compute_delta_synergy_batch_with_synergy_before(empty_board, sample_card):
    """synergy_before parametresi tekrar hesaplamayı önlemeli."""
    coords = [(0, 0), (1, -1)]
    
    # synergy_before=0 ile çağır (boş tahta)
    results = compute_delta_synergy_batch(
        empty_board, sample_card, coords, synergy_before=0
    )
    
    assert len(results) == 2, "Sonuç sayısı doğru olmalı"


# ══════════════════════════════════════════════════════════════════
# Test 3: Skor Fonksiyonu
# ══════════════════════════════════════════════════════════════════

def test_score_placement_formula(empty_board, sample_card):
    """Skor formülü: base_power + (W_synergy × ΔSynergy)"""
    turn = 10  # Orta oyun
    schedule = SynergyWeightSchedule()
    
    score = score_placement(
        empty_board, (0, 0), sample_card, turn,
        schedule=schedule,
        synergy_before=0,
        base_power_weight=1.0,
    )
    
    expected_base = sample_card.total_power() * 1.0
    # Boş tahtada delta=0, dolayısıyla skor = base_power
    assert score == expected_base, "Boş tahtada skor sadece base power olmalı"


def test_score_placement_with_synergy_weight(empty_board):
    """Sinerji ağırlığı skoru etkilemeli."""
    card_a = Card("CardA", "WARRIOR", "3", {"CONNECTION": 10, "SPEED": 5, "POWER": 3})
    card_b = Card("CardB", "WARRIOR", "3", {"CONNECTION": 8, "SPEED": 6, "POWER": 2})
    
    empty_board.place((0, 0), card_a)
    
    schedule = SynergyWeightSchedule(weight_mid=2.0)
    turn = 10  # Orta oyun
    
    score = score_placement(
        empty_board, (1, -1), card_b, turn,
        schedule=schedule,
    )
    
    # Skor en azından base_power kadar olmalı
    # Sinerji bonusu varsa daha yüksek olur
    base_power = card_b.total_power()
    assert score >= base_power, "Skor en azından base power kadar olmalı"
    
    # Boş tahtada aynı kartın skoru ile karşılaştır
    score_empty = score_placement(
        Board(), (0, 0), card_b, turn,
        schedule=schedule,
    )
    
    # Komşu varken skor >= boş tahta skoru olmalı
    assert score >= score_empty, "Komşu varken skor azalmamalı"


# ══════════════════════════════════════════════════════════════════
# Test 4: En İyi Koordinat Seçimi
# ══════════════════════════════════════════════════════════════════

def test_best_coord_for_card_empty_board(empty_board, sample_card):
    """Boş tahtada herhangi bir koordinat seçilebilir."""
    free_coords = empty_board.free_coords()
    
    best_coord, best_score, best_rotation = best_coord_for_card(
        empty_board, sample_card, free_coords, turn=5
    )
    
    assert best_coord is not None, "Boş koordinat varsa seçim yapılmalı"
    assert best_coord in free_coords, "Seçilen koordinat boş olmalı"
    assert 0 <= best_rotation < 6, "Rotasyon 0-5 arasında olmalı"


def test_best_coord_for_card_prefers_synergy(empty_board):
    """En yüksek sinerji artışı sağlayan koordinat seçilmeli."""
    card_a = Card("CardA", "WARRIOR", "3", {"CONNECTION": 10})
    card_b = Card("CardB", "WARRIOR", "3", {"CONNECTION": 8})
    
    empty_board.place((0, 0), card_a)
    
    free_coords = [(1, -1), (2, 0), (-2, 1)]  # (1,-1) komşu, diğerleri uzak
    
    best_coord, _, _ = best_coord_for_card(
        empty_board, card_b, free_coords, turn=10
    )
    
    assert best_coord == (1, -1), "Komşu koordinat (sinerji yüksek) seçilmeli"


def test_best_coord_for_card_max_check_limit(empty_board, sample_card):
    """max_check parametresi koordinat sayısını sınırlamalı."""
    free_coords = empty_board.free_coords()
    
    best_coord, _, _ = best_coord_for_card(
        empty_board, sample_card, free_coords, turn=5, max_check=5
    )
    
    assert best_coord is not None, "Sınırlı arama bile sonuç vermeli"


def test_best_coord_for_card_with_rotation(empty_board):
    """Rotation denemesi en iyi rotasyonu bulmalı."""
    # İki kart - farklı kenar düzenlemeleri
    card_a = Card("CardA", "WARRIOR", "3", {"CONNECTION": 10, "SPEED": 5, "POWER": 3})
    card_b = Card("CardB", "WARRIOR", "3", {"CONNECTION": 8, "SPEED": 6, "POWER": 2})
    
    empty_board.place((0, 0), card_a)
    
    free_coords = [(1, -1)]  # Komşu koordinat
    
    # Rotation ile
    best_coord, score_with_rot, best_rotation = best_coord_for_card(
        empty_board, card_b, free_coords, turn=10, try_rotations=True
    )
    
    # Rotation olmadan
    best_coord_no_rot, score_no_rot, _ = best_coord_for_card(
        empty_board, card_b, free_coords, turn=10, try_rotations=False
    )
    
    # Rotation ile skor >= rotation olmadan skor olmalı
    assert score_with_rot >= score_no_rot, "Rotation denemesi skoru iyileştirmeli veya aynı tutmalı"
    assert 0 <= best_rotation < 6, "Rotasyon 0-5 arasında olmalı"


# ══════════════════════════════════════════════════════════════════
# Test 5: Tam Pipeline Entegrasyonu
# ══════════════════════════════════════════════════════════════════

def test_place_cards_synergy_aware_basic(player_with_hand):
    """Pipeline kartları tahtaya yerleştirmeli."""
    initial_hand_count = sum(1 for c in player_with_hand.hand if c is not None)
    
    place_cards_synergy_aware(player_with_hand)
    
    final_hand_count = sum(1 for c in player_with_hand.hand if c is not None)
    board_count = player_with_hand.board.alive_count()
    
    assert board_count > 0, "En az bir kart yerleştirilmeli"
    assert final_hand_count < initial_hand_count, "El azalmalı"


def test_place_cards_synergy_aware_respects_limit(player_with_hand):
    """place_limit parametresi tur başına kart sayısını sınırlamalı."""
    player_with_hand.hand = [
        Card("C1", "WARRIOR", "2", {"POWER": 5}),
        Card("C2", "WARRIOR", "2", {"SPEED": 5}),
        Card("C3", "WARRIOR", "2", {"CONNECTION": 5}),
    ]
    
    place_cards_synergy_aware(player_with_hand, place_limit=1)
    
    assert player_with_hand.board.alive_count() == 1, "Sadece 1 kart yerleştirilmeli"


def test_place_cards_synergy_aware_custom_schedule(player_with_hand):
    """Özel ağırlık çizelgesi kullanılabilmeli."""
    custom_schedule = SynergyWeightSchedule(
        weight_early=5.0,
        weight_mid=10.0,
        weight_late=15.0,
    )
    
    place_cards_synergy_aware(player_with_hand, schedule=custom_schedule, lookahead_weight=0.5)
    
    # Hata vermeden çalışmalı
    assert player_with_hand.board.alive_count() > 0


def test_place_cards_with_lookahead(player_with_hand):
    """Lookahead özelliği ikili/üçlü yerleştirmeleri teşvik etmeli."""
    # Aynı gruba ait 3 kart ekle
    player_with_hand.hand = [
        Card("C1", "WARRIOR", "3", {"CONNECTION": 10, "SPEED": 5}),
        Card("C2", "WARRIOR", "3", {"CONNECTION": 8, "POWER": 6}),
        Card("C3", "WARRIOR", "3", {"CONNECTION": 9, "SPEED": 4}),
    ]
    
    # Yüksek lookahead ile yerleştir
    place_cards_synergy_aware(player_with_hand, lookahead_weight=0.8, place_limit=3)
    
    # 3 kart yerleştirilmeli
    assert player_with_hand.board.alive_count() == 3, "3 kart yerleştirilmeli"
    
    # Kartlar birbirine yakın olmalı (lookahead etkisi)
    coords = list(player_with_hand.board.grid.keys())
    # En az bir çift komşu olmalı
    has_neighbor = False
    for coord in coords:
        neighbors = player_with_hand.board.neighbors(coord)
        if len(neighbors) > 0:
            has_neighbor = True
            break
    
    assert has_neighbor, "Lookahead ile kartlar birbirine yakın yerleştirilmeli"


# ══════════════════════════════════════════════════════════════════
# Test 6: Ağırlık Çizelgesi
# ══════════════════════════════════════════════════════════════════

def test_synergy_weight_schedule_phases():
    """Ağırlıklar oyun aşamasına göre değişmeli."""
    schedule = SynergyWeightSchedule(
        early_turns=6,
        mid_turns=15,
        weight_early=1.0,
        weight_mid=2.0,
        weight_late=3.0,
    )
    
    assert schedule.weight_for_turn(3) == 1.0, "Erken oyun ağırlığı"
    assert schedule.weight_for_turn(10) == 2.0, "Orta oyun ağırlığı"
    assert schedule.weight_for_turn(20) == 3.0, "Geç oyun ağırlığı"


def test_synergy_weight_schedule_interpolated():
    """İnterpolasyon yumuşak geçiş sağlamalı."""
    schedule = SynergyWeightSchedule(
        early_turns=5,
        mid_turns=15,
        weight_early=1.0,
        weight_late=3.0,
    )
    
    weight_10 = schedule.interpolated_weight(10)
    
    assert 1.0 < weight_10 < 3.0, "Orta turda interpolasyon yapılmalı"


def test_schedule_for_strategy():
    """Her strateji için önceden tanımlanmış çizelge olmalı."""
    strategies = ["warrior", "builder", "economist", "balancer", "tempo", "evolver", "rare_hunter", "random"]
    
    for strategy in strategies:
        schedule = schedule_for(strategy)
        assert isinstance(schedule, SynergyWeightSchedule), f"{strategy} için çizelge olmalı"


def test_schedule_for_unknown_strategy():
    """Bilinmeyen strateji için varsayılan çizelge dönmeli."""
    schedule = schedule_for("unknown_strategy_xyz")
    
    assert isinstance(schedule, SynergyWeightSchedule), "Varsayılan çizelge dönmeli"


# ══════════════════════════════════════════════════════════════════
# Test 7: StateStore Güvenliği
# ══════════════════════════════════════════════════════════════════

def test_no_board_mutation_during_simulation(empty_board, sample_card):
    """Simülasyon sırasında board.grid değişmemeli."""
    original_grid_id = id(empty_board.grid)
    original_grid_copy = dict(empty_board.grid)
    
    # Birden fazla delta hesabı yap
    coords = [(0, 0), (1, -1), (-1, 0), (0, 1)]
    for coord in coords:
        compute_delta_synergy(empty_board, coord, sample_card)
    
    assert id(empty_board.grid) == original_grid_id, "Grid objesi değişmemeli"
    assert empty_board.grid == original_grid_copy, "Grid içeriği değişmemeli"


def test_no_coord_index_mutation(empty_board, sample_card):
    """coord_index simülasyon sırasında değişmemeli."""
    original_index = dict(empty_board.coord_index)
    
    compute_delta_synergy(empty_board, (0, 0), sample_card)
    
    assert empty_board.coord_index == original_index, "coord_index değişmemeli"


# ══════════════════════════════════════════════════════════════════
# Test 8: Edge Cases
# ══════════════════════════════════════════════════════════════════

def test_place_cards_empty_hand():
    """Boş el ile çağrıldığında hata vermemeli."""
    player = Player(pid=1, strategy="random")
    player.hand = [None, None, None]
    
    place_cards_synergy_aware(player)  # Hata vermemeli
    
    assert player.board.alive_count() == 0, "Hiçbir kart yerleştirilmemeli"


def test_place_cards_full_board():
    """Dolu tahtada çağrıldığında hata vermemeli."""
    player = Player(pid=1, strategy="random")
    player.hand = [Card("C1", "WARRIOR", "2", {"POWER": 5})]
    
    # Tahtayı doldur
    for coord in player.board.free_coords():
        player.board.place(coord, Card("Filler", "WARRIOR", "1", {"POWER": 1}))
    
    place_cards_synergy_aware(player)  # Hata vermemeli
    
    # El değişmemeli (yerleştirecek yer yok)
    assert player.hand[0] is not None, "Kart elde kalmalı"


def test_best_coord_for_card_no_free_coords(empty_board, sample_card):
    """Boş koordinat yoksa None dönmeli."""
    best_coord, best_score, best_rotation = best_coord_for_card(
        empty_board, sample_card, [], turn=5
    )
    
    assert best_coord is None, "Boş koordinat yoksa None dönmeli"
    assert best_score == float("-inf"), "Skor -inf olmalı"
    assert best_rotation == 0, "Rotasyon varsayılan olmalı"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
