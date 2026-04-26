#!/usr/bin/env python3
"""
Event Log Analizi - KPI Üretimi
Yeni event loglarından detaylı KPI metrikleri üretir.
Mevcut KPI sistemine DOKUNMAZ.
"""

import json
import os
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Any
from statistics import mean, median


class EventAnalyzer:
    """Event log'larından KPI metrikleri üretir"""
    
    def __init__(self, event_log_path: str = "output/logs/simulation_events.jsonl",
                 combat_log_path: str = "output/logs/combat_events.jsonl"):
        self.event_log_path = event_log_path
        self.combat_log_path = combat_log_path
        
        self.events: List[Dict] = []
        self.combat_events: List[Dict] = []
        
        # KPI data structures
        self.card_purchases: Counter = Counter()
        self.card_placements: Counter = Counter()
        self.card_wins: Counter = Counter()
        self.card_losses: Counter = Counter()
        self.card_damages: defaultdict = defaultdict(list)
        self.synergy_triggers: Counter = Counter()
        self.passive_triggers: Counter = Counter()
        
        self.shop_to_board: Dict[str, Dict] = {}  # card -> {purchased, placed}
        self.combat_stats: List[Dict] = []
        
    def load_events(self):
        """Event log'larını yükle"""
        print("📂 Event log'ları yükleniyor...")
        
        # Main events
        if os.path.exists(self.event_log_path):
            with open(self.event_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        self.events.append(event)
                    except:
                        pass
        
        # Combat events
        if os.path.exists(self.combat_log_path):
            with open(self.combat_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        self.combat_events.append(event)
                    except:
                        pass
        
        print(f"  ✅ {len(self.events)} event yüklendi")
        print(f"  ✅ {len(self.combat_events)} combat event yüklendi")
    
    def analyze_card_purchases(self):
        """Kart satın alma analizleri"""
        print("\n📊 Kart satın alma analizi...")
        
        for event in self.events:
            if event['event_type'] == 'card_purchase':
                card_name = event['card_name']
                self.card_purchases[card_name] += 1
                
                # Shop to board tracking
                if card_name not in self.shop_to_board:
                    self.shop_to_board[card_name] = {'purchased': 0, 'placed': 0}
                self.shop_to_board[card_name]['purchased'] += 1
    
    def analyze_board_placements(self):
        """Board yerleştirme analizleri"""
        print("📊 Board yerleştirme analizi...")
        
        for event in self.events:
            if event['event_type'] == 'board_placement':
                card_name = event['card_name']
                self.card_placements[card_name] += 1
                
                # Shop to board tracking
                if card_name not in self.shop_to_board:
                    self.shop_to_board[card_name] = {'purchased': 0, 'placed': 0}
                self.shop_to_board[card_name]['placed'] += 1
    
    def analyze_combats(self):
        """Combat analizleri"""
        print("📊 Combat analizi...")
        
        for event in self.combat_events:
            if event['event_type'] == 'combat':
                self.combat_stats.append({
                    'damage': event['damage'],
                    'power_diff': abs(event['player1_board_power'] - event['player2_board_power']),
                    'duration': event['combat_duration']
                })
    
    def analyze_synergies(self):
        """Sinerji analizleri"""
        print("📊 Sinerji analizi...")
        
        for event in self.events:
            if event['event_type'] == 'synergy_trigger':
                synergy_type = event['synergy_type']
                self.synergy_triggers[synergy_type] += 1
    
    def analyze_passives(self):
        """Pasif yetenek analizleri"""
        print("📊 Pasif yetenek analizi...")
        
        for event in self.events:
            if event['event_type'] == 'passive_trigger':
                card_name = event['card_name']
                trigger_type = event['trigger_type']
                
                key = f"{card_name}:{trigger_type}"
                self.passive_triggers[key] += 1
    
    def calculate_shop_to_board_conversion(self) -> Dict[str, float]:
        """Shop → Board dönüşüm oranı"""
        conversion_rates = {}
        
        for card_name, stats in self.shop_to_board.items():
            purchased = stats['purchased']
            placed = stats['placed']
            
            if purchased > 0:
                conversion_rates[card_name] = (placed / purchased) * 100
        
        return conversion_rates
    
    def generate_kpi_report(self) -> Dict[str, Any]:
        """Tüm KPI'ları içeren rapor oluştur"""
        print("\n📊 KPI raporu oluşturuluyor...")
        
        # Shop to board conversion
        conversion_rates = self.calculate_shop_to_board_conversion()
        
        # Combat stats
        avg_damage = mean([c['damage'] for c in self.combat_stats]) if self.combat_stats else 0
        avg_combat_duration = mean([c['duration'] for c in self.combat_stats]) if self.combat_stats else 0
        
        report = {
            'summary': {
                'total_events': len(self.events),
                'total_combats': len(self.combat_events),
                'unique_cards_purchased': len(self.card_purchases),
                'unique_cards_placed': len(self.card_placements),
            },
            
            'top_purchased_cards': dict(self.card_purchases.most_common(20)),
            'top_placed_cards': dict(self.card_placements.most_common(20)),
            
            'shop_to_board_conversion': {
                'top_conversion': sorted(
                    [(k, v) for k, v in conversion_rates.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:20],
                'low_conversion': sorted(
                    [(k, v) for k, v in conversion_rates.items()],
                    key=lambda x: x[1]
                )[:20]
            },
            
            'combat_stats': {
                'total_combats': len(self.combat_stats),
                'avg_damage': round(avg_damage, 2),
                'avg_duration': round(avg_combat_duration, 2),
            },
            
            'top_synergies': dict(self.synergy_triggers.most_common(20)),
            'top_passive_triggers': dict(self.passive_triggers.most_common(20)),
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], output_path: str = "output/logs/kpi_reports/event_kpi_report.json"):
        """Raporu kaydet"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ KPI raporu kaydedildi: {output_path}")
    
    def print_summary(self, report: Dict[str, Any]):
        """Özet raporu ekrana yazdır"""
        print("\n" + "="*60)
        print("📊 EVENT LOG KPI RAPORU")
        print("="*60)
        
        print(f"\n📈 Genel İstatistikler:")
        print(f"  - Toplam Event: {report['summary']['total_events']:,}")
        print(f"  - Toplam Combat: {report['summary']['total_combats']:,}")
        print(f"  - Unique Kart (Satın Alınan): {report['summary']['unique_cards_purchased']}")
        print(f"  - Unique Kart (Yerleştirilen): {report['summary']['unique_cards_placed']}")
        
        print(f"\n🛒 En Çok Satın Alınan Kartlar (Top 10):")
        for i, (card, count) in enumerate(list(report['top_purchased_cards'].items())[:10], 1):
            print(f"  {i}. {card}: {count}")
        
        print(f"\n🎯 En Çok Board'a Yerleştirilen Kartlar (Top 10):")
        for i, (card, count) in enumerate(list(report['top_placed_cards'].items())[:10], 1):
            print(f"  {i}. {card}: {count}")
        
        print(f"\n📊 Shop → Board Dönüşüm Oranı (Top 10):")
        for i, (card, rate) in enumerate(report['shop_to_board_conversion']['top_conversion'][:10], 1):
            print(f"  {i}. {card}: {rate:.1f}%")
        
        print(f"\n⚔️  Combat İstatistikleri:")
        print(f"  - Ortalama Damage: {report['combat_stats']['avg_damage']}")
        print(f"  - Ortalama Combat Süresi: {report['combat_stats']['avg_duration']}")
        
        print(f"\n✨ En Çok Tetiklenen Sinerjiler (Top 10):")
        for i, (synergy, count) in enumerate(list(report['top_synergies'].items())[:10], 1):
            print(f"  {i}. {synergy}: {count}")
        
        print(f"\n🎭 En Çok Tetiklenen Pasif Yetenekler (Top 10):")
        for i, (passive, count) in enumerate(list(report['top_passive_triggers'].items())[:10], 1):
            print(f"  {i}. {passive}: {count}")
    
    def run(self):
        """Tüm analizleri çalıştır"""
        self.load_events()
        
        if not self.events and not self.combat_events:
            print("\n⚠️  Event log bulunamadı. ENABLE_DETAILED_LOGGING=True ile simülasyon çalıştırın.")
            return
        
        self.analyze_card_purchases()
        self.analyze_board_placements()
        self.analyze_combats()
        self.analyze_synergies()
        self.analyze_passives()
        
        report = self.generate_kpi_report()
        self.save_report(report)
        self.print_summary(report)


if __name__ == "__main__":
    analyzer = EventAnalyzer()
    analyzer.run()
