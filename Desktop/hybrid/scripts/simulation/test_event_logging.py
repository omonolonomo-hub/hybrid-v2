#!/usr/bin/env python3
"""
Event Logging Test Scripti
Mevcut sisteme dokunmadan event logging'i test eder.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from engine_core.event_logger import init_event_logger, get_event_logger, close_event_logger


def test_event_logger():
    """Event logger'ı test et"""
    print("="*60)
    print("🧪 EVENT LOGGER TEST")
    print("="*60)
    
    # Logger'ı başlat
    print("\n1️⃣ Logger başlatılıyor...")
    logger = init_event_logger(enabled=True)
    print("   ✅ Logger başlatıldı")
    
    # Game context ayarla
    print("\n2️⃣ Game context ayarlanıyor...")
    logger.set_game_context(game_id=1, turn=1)
    print("   ✅ Game context ayarlandı (game_id=1, turn=1)")
    
    # Test event'leri
    print("\n3️⃣ Test event'leri oluşturuluyor...")
    
    # Card purchase
    logger.log_card_purchase(
        player_id=0,
        card_name="Test Card",
        card_rarity="3",
        cost=3,
        gold_after=5
    )
    print("   ✅ card_purchase eventi loglandı")
    
    # Board placement
    logger.log_board_placement(
        player_id=0,
        card_name="Test Card",
        position=(0, 0),
        board_size=1
    )
    print("   ✅ board_placement eventi loglandı")
    
    # Combat
    logger.log_combat(
        player1_id=0,
        player2_id=1,
        winner_id=0,
        damage=10,
        player1_board_power=100,
        player2_board_power=90,
        combat_duration=5
    )
    print("   ✅ combat eventi loglandı")
    
    # Synergy trigger
    logger.log_synergy_trigger(
        player_id=0,
        card_name="Test Card",
        synergy_type="test_synergy",
        synergy_value=25
    )
    print("   ✅ synergy_trigger eventi loglandı")
    
    # Round result
    logger.log_round_result(
        player_id=0,
        hp=100,
        gold=8,
        board_size=5,
        hand_size=3,
        result="win"
    )
    print("   ✅ round_result eventi loglandı")
    
    # Passive trigger
    logger.log_passive_trigger(
        player_id=0,
        card_name="Test Card",
        trigger_type="combat_win",
        effect_value=10
    )
    print("   ✅ passive_trigger eventi loglandı")
    
    # Logger'ı kapat
    print("\n4️⃣ Logger kapatılıyor...")
    close_event_logger()
    print("   ✅ Logger kapatıldı, buffer'lar flush edildi")
    
    # Dosyaları kontrol et
    print("\n5️⃣ Log dosyaları kontrol ediliyor...")
    
    event_log = "output/logs/simulation_events.jsonl"
    combat_log = "output/logs/combat_events.jsonl"
    
    if os.path.exists(event_log):
        with open(event_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"   ✅ {event_log} oluşturuldu ({len(lines)} event)")
    else:
        print(f"   ❌ {event_log} bulunamadı")
    
    if os.path.exists(combat_log):
        with open(combat_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"   ✅ {combat_log} oluşturuldu ({len(lines)} event)")
    else:
        print(f"   ❌ {combat_log} bulunamadı")
    
    print("\n" + "="*60)
    print("✅ TEST TAMAMLANDI")
    print("="*60)
    
    print("\n📁 Oluşturulan dosyalar:")
    print(f"  - {event_log}")
    print(f"  - {combat_log}")
    
    print("\n💡 Event'leri görmek için:")
    print(f"  cat {event_log}")
    print(f"  cat {combat_log}")


if __name__ == "__main__":
    test_event_logger()
