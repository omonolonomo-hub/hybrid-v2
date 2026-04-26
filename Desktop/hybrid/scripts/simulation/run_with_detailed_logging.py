#!/usr/bin/env python3
"""
Detaylı Event Logging ile Simülasyon
Bu script mevcut simülasyon sistemine DOKUNMAZ.
Sadece event logging'i aktif ederek çalıştırır.
"""

import sys
import os

# Root path'i ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from engine_core import autochess_sim_v06 as sim
from engine_core.event_logger import init_event_logger, close_event_logger

def run_simulation_with_logging(n_games: int = 100, verbose: bool = False):
    """
    Detaylı event logging ile simülasyon çalıştır.
    
    Args:
        n_games: Oyun sayısı
        verbose: Verbose output
    """
    print("="*60)
    print("🎮 DETAYLI EVENT LOGGING İLE SİMÜLASYON")
    print("="*60)
    print(f"\n📊 Ayarlar:")
    print(f"  - Oyun Sayısı: {n_games}")
    print(f"  - Detaylı Logging: ✅ AKTİF")
    print(f"  - Verbose: {'✅' if verbose else '❌'}")
    
    # Event logger'ı başlat (ENABLE_DETAILED_LOGGING=True)
    logger = init_event_logger(enabled=True)
    print(f"\n✅ Event logger başlatıldı")
    print(f"  - Event log: output/logs/simulation_events.jsonl")
    print(f"  - Combat log: output/logs/combat_events.jsonl")
    
    # Mevcut simülasyon sistemini çalıştır (DEĞİŞTİRMEDEN)
    print(f"\n🚀 Simülasyon başlıyor...")
    
    try:
        result = sim.run_simulation(
            n_games=n_games,
            n_players=8,
            verbose=verbose
        )
        
        print(f"\n✅ Simülasyon tamamlandı!")
        
        # Logger'ı kapat ve buffer'ları flush et
        close_event_logger()
        print(f"✅ Event log'ları kaydedildi")
        
        # Sonuçları göster
        print(f"\n📊 Sonuçlar:")
        print(f"  - Toplam Oyun: {result['total_games']}")
        print(f"  - Ortalama Turn: {result['avg_turns']:.1f}")
        print(f"  - Ortalama HP: {result['avg_hp']:.1f}")
        
        print(f"\n📁 Log Dosyaları:")
        print(f"  - Mevcut log: output/logs/simulation_log.txt")
        print(f"  - Event log: output/logs/simulation_events.jsonl")
        print(f"  - Combat log: output/logs/combat_events.jsonl")
        
        print(f"\n💡 KPI Analizi için:")
        print(f"  python scripts/analysis/analyze_events.py")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        close_event_logger()
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Detaylı event logging ile simülasyon')
    parser.add_argument('--games', type=int, default=100, help='Oyun sayısı (default: 100)')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    run_simulation_with_logging(n_games=args.games, verbose=args.verbose)
