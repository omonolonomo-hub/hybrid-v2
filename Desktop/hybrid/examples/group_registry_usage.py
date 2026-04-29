"""
examples/group_registry_usage.py
═══════════════════════════════════════════════════════════════════
GroupRegistry kullanım örnekleri.

Bu dosya, GroupRegistry API'sinin nasıl kullanılacağını gösterir.
═══════════════════════════════════════════════════════════════════
"""

from engine_core.group_registry import GroupRegistry, GROUPS, STAT_TO_GROUP, GROUP_BEATS


def example_1_get_all_groups():
    """Tüm grup isimlerini al."""
    print("=== Örnek 1: Tüm Gruplar ===")
    groups = GroupRegistry.all_groups()
    print(f"Gruplar: {groups}")
    print(f"Grup sayısı: {len(groups)}")
    print()


def example_2_get_group_details():
    """Bir grubun detaylarını al."""
    print("=== Örnek 2: Grup Detayları ===")
    mind = GroupRegistry.get("MIND")
    print(f"Grup adı: {mind.name}")
    print(f"Stat'lar: {mind.stats}")
    print(f"Yendiği grup: {mind.beats}")
    print(f"Renk: {mind.color}")
    print()


def example_3_stat_to_group_mapping():
    """Stat'tan gruba mapping."""
    print("=== Örnek 3: Stat → Grup Mapping ===")
    stats = ["Power", "Meaning", "Gravity", "Unknown"]
    for stat in stats:
        group = GroupRegistry.stat_to_group(stat)
        print(f"{stat:15} → {group or 'N/A'}")
    print()


def example_4_combat_advantage():
    """Combat avantajı kontrolü (rock-paper-scissors)."""
    print("=== Örnek 4: Combat Avantajı ===")
    
    # MIND vs EXISTENCE
    if GroupRegistry.beats("MIND", "EXISTENCE"):
        print("✓ MIND beats EXISTENCE (+1 combat bonus)")
    
    # CONNECTION vs MIND
    if GroupRegistry.beats("CONNECTION", "MIND"):
        print("✓ CONNECTION beats MIND (+1 combat bonus)")
    
    # EXISTENCE vs CONNECTION
    if GroupRegistry.beats("EXISTENCE", "CONNECTION"):
        print("✓ EXISTENCE beats CONNECTION (+1 combat bonus)")
    
    print()


def example_5_get_winner():
    """İki grup arasında kazananı bul."""
    print("=== Örnek 5: Kazanan Belirleme ===")
    
    matchups = [
        ("MIND", "EXISTENCE"),
        ("CONNECTION", "MIND"),
        ("EXISTENCE", "CONNECTION"),
        ("MIND", "MIND"),  # Draw
    ]
    
    for group_a, group_b in matchups:
        winner = GroupRegistry.get_winner(group_a, group_b)
        if winner:
            print(f"{group_a:12} vs {group_b:12} → Winner: {winner}")
        else:
            print(f"{group_a:12} vs {group_b:12} → Draw")
    
    print()


def example_6_backward_compatibility():
    """Eski API ile uyumluluk."""
    print("=== Örnek 6: Backward Compatibility ===")
    
    # Eski stil: GROUPS tuple
    print(f"GROUPS tuple: {GROUPS}")
    
    # Eski stil: STAT_TO_GROUP dict
    print(f"Power → {STAT_TO_GROUP['Power']}")
    
    # Eski stil: GROUP_BEATS dict
    print(f"MIND beats → {GROUP_BEATS['MIND']}")
    
    print()


def example_7_iterate_all_groups():
    """Tüm gruplar üzerinde iterasyon."""
    print("=== Örnek 7: Tüm Gruplar Üzerinde İterasyon ===")
    
    for group_name in GroupRegistry.all_groups():
        group_def = GroupRegistry.get(group_name)
        print(f"\n{group_def.name}:")
        print(f"  Stats: {', '.join(group_def.stats)}")
        print(f"  Beats: {group_def.beats}")
        print(f"  Color: {group_def.color}")


def example_8_combat_simulation():
    """Combat simülasyonu örneği."""
    print("\n=== Örnek 8: Combat Simülasyonu ===")
    
    # İki kartın edge'lerinde hangi gruplar var?
    card_a_edge = "Meaning"  # MIND grubu
    card_b_edge = "Power"    # EXISTENCE grubu
    
    group_a = GroupRegistry.stat_to_group(card_a_edge)
    group_b = GroupRegistry.stat_to_group(card_b_edge)
    
    print(f"Card A edge: {card_a_edge} ({group_a})")
    print(f"Card B edge: {card_b_edge} ({group_b})")
    
    # Combat avantajı var mı?
    if GroupRegistry.beats(group_a, group_b):
        print(f"✓ {group_a} beats {group_b} → Card A gets +1 bonus!")
    elif GroupRegistry.beats(group_b, group_a):
        print(f"✓ {group_b} beats {group_a} → Card B gets +1 bonus!")
    else:
        print("No combat advantage")


def example_9_complete_cycle():
    """Rock-paper-scissors döngüsünü göster."""
    print("\n=== Örnek 9: Rock-Paper-Scissors Döngüsü ===")
    
    print("MIND → beats → EXISTENCE")
    print("EXISTENCE → beats → CONNECTION")
    print("CONNECTION → beats → MIND")
    print("\n(Complete cycle: her grup bir diğerini yener)")


if __name__ == "__main__":
    example_1_get_all_groups()
    example_2_get_group_details()
    example_3_stat_to_group_mapping()
    example_4_combat_advantage()
    example_5_get_winner()
    example_6_backward_compatibility()
    example_7_iterate_all_groups()
    example_8_combat_simulation()
    example_9_complete_cycle()
    
    print("\n" + "="*60)
    print("Tüm örnekler tamamlandı!")
    print("="*60)
