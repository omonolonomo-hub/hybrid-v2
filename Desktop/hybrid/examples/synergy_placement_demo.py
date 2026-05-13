"""
examples/synergy_placement_demo.py
════════════════════════════════════════════════════════════════════
Sinerji-Delta tabanlı AI yerleştirme sistemi demo.

Bu dosya yeni sinerji-aware yerleştirme sisteminin nasıl kullanılacağını
gösterir ve farklı stratejilerin davranışlarını karşılaştırır.
════════════════════════════════════════════════════════════════════
"""

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


def demo_basic_delta():
    """Demo 1: Temel delta hesaplama."""
    print("=" * 70)
    print("DEMO 1: Temel Sinerji Delta Hesaplama")
    print("=" * 70)
    
    board = Board()
    
    # İlk kart: CONNECTION dominant
    card_a = Card("Warrior Alpha", "WARRIOR", "3", {"CONNECTION": 10, "SPEED": 5, "POWER": 8})
    board.place((0, 0), card_a)
    
    # İkinci kart: CONNECTION dominant (eşleşecek)
    card_b = Card("Warrior Beta", "WARRIOR", "3", {"CONNECTION": 8, "SPEED": 6, "POWER": 7})
    
    # Farklı koordinatlarda delta hesapla
    coords_to_test = [
        (1, -1),   # (0,0)'ın komşusu
        (2, 0),    # Uzak
        (-1, 1),   # (0,0)'ın komşusu
        (3, -2),   # Çok uzak
    ]
    
    print(f"\nMevcut tahta: {card_a.name} @ (0, 0)")
    print(f"Yerleştirilecek kart: {card_b.name}")
    print(f"Dominant grup: CONNECTION\n")
    
    for coord in coords_to_test:
        delta = compute_delta_synergy(board, coord, card_b)
        distance = abs(coord[0]) + abs(coord[1])
        print(f"  Koordinat {coord:>10} (uzaklık={distance}) → ΔSynergy = {delta:>3}")
    
    print("\n✓ Komşu koordinatlar daha yüksek delta üretiyor!\n")


def demo_batch_calculation():
    """Demo 2: Batch hesaplama performansı."""
    print("=" * 70)
    print("DEMO 2: Batch Delta Hesaplama (Performans)")
    print("=" * 70)
    
    board = Board()
    
    # Tahtaya birkaç kart yerleştir
    cards_on_board = [
        (Card("Card1", "WARRIOR", "3", {"CONNECTION": 10}), (0, 0)),
        (Card("Card2", "MAGE", "3", {"SPEED": 8}), (1, -1)),
        (Card("Card3", "TANK", "3", {"POWER": 9}), (-1, 0)),
    ]
    
    for card, coord in cards_on_board:
        board.place(coord, card)
    
    # Yeni kart
    new_card = Card("NewCard", "WARRIOR", "3", {"CONNECTION": 8, "SPEED": 6})
    
    # Tüm boş koordinatlar için batch hesaplama
    free_coords = board.free_coords()[:10]  # İlk 10 koordinat
    
    print(f"\nTahta: {len(cards_on_board)} kart yerleştirilmiş")
    print(f"Yeni kart: {new_card.name}")
    print(f"Test edilecek koordinat sayısı: {len(free_coords)}\n")
    
    deltas = compute_delta_synergy_batch(board, new_card, free_coords)
    
    # En iyi 5 koordinatı göster
    sorted_coords = sorted(deltas.items(), key=lambda x: x[1], reverse=True)[:5]
    
    print("En iyi 5 koordinat:")
    for i, (coord, delta) in enumerate(sorted_coords, 1):
        print(f"  {i}. {coord:>10} → ΔSynergy = {delta:>3}")
    
    print("\n✓ Batch hesaplama ile tüm koordinatlar tek seferde değerlendirildi!\n")


def demo_score_formula():
    """Demo 3: Skor formülü ve ağırlık etkisi."""
    print("=" * 70)
    print("DEMO 3: Skor Formülü ve Ağırlık Etkisi")
    print("=" * 70)
    
    board = Board()
    card_a = Card("BaseCard", "WARRIOR", "3", {"CONNECTION": 10})
    board.place((0, 0), card_a)
    
    card_b = Card("TestCard", "WARRIOR", "3", {"CONNECTION": 8, "POWER": 6})
    coord = (1, -1)  # Komşu koordinat
    
    # Farklı ağırlıklarla skor hesapla
    schedules = [
        ("Erken Oyun (W=1.5)", SynergyWeightSchedule(weight_early=1.5), 3),
        ("Orta Oyun (W=2.0)", SynergyWeightSchedule(weight_mid=2.0), 10),
        ("Geç Oyun (W=3.0)", SynergyWeightSchedule(weight_late=3.0), 20),
    ]
    
    print(f"\nKart: {card_b.name} (güç={card_b.total_power()})")
    print(f"Koordinat: {coord} (komşu)\n")
    
    for label, schedule, turn in schedules:
        score = score_placement(board, coord, card_b, turn, schedule=schedule)
        weight = schedule.weight_for_turn(turn)
        print(f"  {label:25} → Skor = {score:>6.1f} (W={weight})")
    
    print("\n✓ Geç oyunda sinerji ağırlığı arttıkça skor yükseliyor!\n")


def demo_best_coord_selection():
    """Demo 4: En iyi koordinat seçimi."""
    print("=" * 70)
    print("DEMO 4: En İyi Koordinat Seçimi")
    print("=" * 70)
    
    board = Board()
    
    # Merkeze CONNECTION cluster oluştur
    center_cards = [
        (Card("C1", "WARRIOR", "3", {"CONNECTION": 10}), (0, 0)),
        (Card("C2", "WARRIOR", "3", {"CONNECTION": 8}), (1, -1)),
        (Card("C3", "WARRIOR", "3", {"CONNECTION": 9}), (-1, 0)),
    ]
    
    for card, coord in center_cards:
        board.place(coord, card)
    
    # Yeni CONNECTION kartı
    new_card = Card("NewConnection", "WARRIOR", "3", {"CONNECTION": 7, "SPEED": 5})
    
    free_coords = board.free_coords()[:15]
    
    print(f"\nTahta: CONNECTION cluster (3 kart)")
    print(f"Yeni kart: {new_card.name} (CONNECTION dominant)")
    print(f"Boş koordinat sayısı: {len(free_coords)}\n")
    
    best_coord, best_score = best_coord_for_card(
        board, new_card, free_coords, turn=10
    )
    
    print(f"Seçilen koordinat: {best_coord}")
    print(f"Skor: {best_score:.1f}")
    
    # Delta'yı göster
    delta = compute_delta_synergy(board, best_coord, new_card)
    print(f"ΔSynergy: {delta}")
    
    print("\n✓ Sistem CONNECTION cluster'a en yakın koordinatı seçti!\n")


def demo_strategy_comparison():
    """Demo 5: Farklı stratejilerin ağırlık karşılaştırması."""
    print("=" * 70)
    print("DEMO 5: Strateji Bazlı Ağırlık Karşılaştırması")
    print("=" * 70)
    
    strategies = ["warrior", "builder", "economist", "balancer", "tempo"]
    turns = [5, 10, 20]  # Erken, orta, geç
    
    print("\nStrateji Ağırlıkları (W_synergy):\n")
    print(f"{'Strateji':<15} | {'Tur 5 (Erken)':<15} | {'Tur 10 (Orta)':<15} | {'Tur 20 (Geç)':<15}")
    print("-" * 70)
    
    for strategy in strategies:
        schedule = schedule_for(strategy)
        weights = [schedule.weight_for_turn(t) for t in turns]
        print(f"{strategy:<15} | {weights[0]:<15.1f} | {weights[1]:<15.1f} | {weights[2]:<15.1f}")
    
    print("\n✓ Her strateji kendi karakterine uygun ağırlıklar kullanıyor!")
    print("  • Warrior: Düşük ağırlık → bireysel güç odaklı")
    print("  • Builder: Yüksek ağırlık → combo master")
    print("  • Balancer: Geç oyun patlaması → 4.0 ağırlık\n")


def demo_full_pipeline():
    """Demo 6: Tam pipeline entegrasyonu."""
    print("=" * 70)
    print("DEMO 6: Tam Pipeline Entegrasyonu")
    print("=" * 70)
    
    # Oyuncu oluştur
    player = Player(pid=1, strategy="builder")
    player.turns_played = 10
    
    # Ele kart ekle
    player.hand = [
        Card("Card1", "WARRIOR", "3", {"CONNECTION": 10, "SPEED": 5}),
        Card("Card2", "WARRIOR", "3", {"CONNECTION": 8, "POWER": 6}),
        Card("Card3", "MAGE", "2", {"SPEED": 7, "POWER": 5}),
    ]
    
    print(f"\nOyuncu: {player.name}")
    print(f"Strateji: {player.strategy}")
    print(f"Tur: {player.turns_played}")
    print(f"Eldeki kart sayısı: {len([c for c in player.hand if c is not None])}\n")
    
    # Pipeline çalıştır
    schedule = schedule_for(player.strategy)
    place_cards_synergy_aware(player, schedule=schedule)
    
    print(f"Yerleştirme sonrası:")
    print(f"  Tahtadaki kart sayısı: {player.board.alive_count()}")
    print(f"  Eldeki kart sayısı: {len([c for c in player.hand if c is not None])}")
    
    # Tahtadaki kartları göster
    print(f"\nTahtadaki kartlar:")
    for coord, card in player.board.grid.items():
        print(f"  {coord:>10} → {card.name}")
    
    print("\n✓ Pipeline kartları sinerji-aware şekilde yerleştirdi!\n")


def demo_custom_schedule():
    """Demo 7: Özelleştirilmiş ağırlık çizelgesi."""
    print("=" * 70)
    print("DEMO 7: Özelleştirilmiş Ağırlık Çizelgesi")
    print("=" * 70)
    
    # Agresif geç oyun stratejisi
    custom_schedule = SynergyWeightSchedule(
        early_turns=5,
        mid_turns=12,
        weight_early=1.0,   # Erken: bireysel güç
        weight_mid=3.0,     # Orta: sinerji önemli
        weight_late=5.0,    # Geç: sinerji kritik!
    )
    
    print("\nÖzel Çizelge: 'Agresif Geç Oyun'")
    print(f"  Erken (1-5):   W = {custom_schedule.weight_early}")
    print(f"  Orta (6-12):   W = {custom_schedule.weight_mid}")
    print(f"  Geç (13+):     W = {custom_schedule.weight_late}\n")
    
    # Farklı turlarda ağırlık göster
    test_turns = [3, 8, 15, 20]
    print("Tur bazlı ağırlıklar:")
    for turn in test_turns:
        weight = custom_schedule.weight_for_turn(turn)
        print(f"  Tur {turn:>2} → W = {weight}")
    
    # Interpolasyon ile yumuşak geçiş
    print("\nİnterpolasyon ile yumuşak geçiş:")
    for turn in range(4, 14):
        weight = custom_schedule.interpolated_weight(turn)
        print(f"  Tur {turn:>2} → W = {weight:.2f}")
    
    print("\n✓ Özel çizelgeler ile strateji davranışı ince ayarlanabilir!\n")


def main():
    """Tüm demoları çalıştır."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "SİNERJİ-DELTA YERLEŞTİRME SİSTEMİ" + " " * 20 + "║")
    print("║" + " " * 25 + "DEMO PROGRAMI" + " " * 30 + "║")
    print("╚" + "═" * 68 + "╝")
    print("\n")
    
    demos = [
        demo_basic_delta,
        demo_batch_calculation,
        demo_score_formula,
        demo_best_coord_selection,
        demo_strategy_comparison,
        demo_full_pipeline,
        demo_custom_schedule,
    ]
    
    for i, demo in enumerate(demos, 1):
        demo()
        if i < len(demos):
            input("Devam etmek için Enter'a basın...")
            print("\n")
    
    print("=" * 70)
    print("TÜM DEMOLAR TAMAMLANDI!")
    print("=" * 70)
    print("\nSinerji-Delta sistemi başarıyla entegre edildi.")
    print("AI botları artık sinerji-aware kararlar veriyor! 🎯\n")


if __name__ == "__main__":
    main()
