#!/usr/bin/env python3
"""
5000 Maçlık Simülasyon Sonuçları - Detaylı Analiz ve Görselleştirme
"""

import json
import csv
from pathlib import Path
from collections import defaultdict
from typing import Dict, List

def load_json(filepath: str) -> dict:
    """JSON dosyasını yükle"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_strategy_matchups():
    """Strateji karşılaşmalarını analiz et"""
    game_results = load_json('output/detailed_simulation/game_results.json')
    
    # Strateji vs strateji kazanma matrisi
    matchup_matrix = defaultdict(lambda: defaultdict(lambda: {'wins': 0, 'total': 0}))
    
    for game in game_results:
        winner_strategy = game['winner_strategy']
        
        for player in game['players']:
            if player['strategy'] != winner_strategy:
                # Kazanan vs kaybeden
                matchup_matrix[winner_strategy][player['strategy']]['wins'] += 1
                matchup_matrix[winner_strategy][player['strategy']]['total'] += 1
    
    return matchup_matrix

def analyze_card_synergies():
    """Kart sinerjilerini analiz et"""
    game_results = load_json('output/detailed_simulation/game_results.json')
    card_performance = load_json('output/detailed_simulation/card_performance.json')
    
    # En yüksek kazanma oranına sahip kartlar
    top_cards = sorted(
        card_performance.items(),
        key=lambda x: x[1]['win_rate'],
        reverse=True
    )[:20]
    
    return top_cards

def generate_comprehensive_report():
    """Kapsamlı analiz raporu oluştur"""
    output_file = Path('output/detailed_simulation/comprehensive_analysis.txt')
    
    # Verileri yükle
    strategy_perf = load_json('output/detailed_simulation/strategy_performance.json')
    card_perf = load_json('output/detailed_simulation/card_performance.json')
    game_results = load_json('output/detailed_simulation/game_results.json')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("5000 MAÇLIK SİMÜLASYON - KAPSAMLI ANALİZ RAPORU\n")
        f.write("=" * 80 + "\n\n")
        
        # 1. STRATEJİ ANALİZİ
        f.write("-" * 80 + "\n")
        f.write("1. STRATEJİ PERFORMANS ANALİZİ\n")
        f.write("-" * 80 + "\n\n")
        
        # Stratejileri kazanma oranına göre sırala
        sorted_strategies = sorted(
            strategy_perf.items(),
            key=lambda x: x[1]['win_rate'],
            reverse=True
        )
        
        f.write(f"{'Sıra':<6} {'Strateji':<15} {'Kazanma %':<12} {'Ort. Hasar':<12} {'Ort. HP':<12}\n")
        f.write("-" * 80 + "\n")
        
        for rank, (strategy, stats) in enumerate(sorted_strategies, 1):
            f.write(f"{rank:<6} {strategy:<15} {stats['win_rate']:<12.2f} "
                   f"{stats['avg_damage']:<12.1f} {stats['avg_hp_remaining']:<12.1f}\n")
        
        f.write("\n")
        
        # Strateji güçlü/zayıf yönleri
        f.write("Strateji Değerlendirmesi:\n\n")
        
        for strategy, stats in sorted_strategies:
            f.write(f"{strategy.upper()}:\n")
            f.write(f"  • Kazanma oranı: {stats['win_rate']:.1f}%\n")
            f.write(f"  • Ortalama hasar: {stats['avg_damage']:.1f}\n")
            f.write(f"  • Ortalama kill: {stats['avg_kills']:.1f}\n")
            f.write(f"  • Hayatta kalma HP: {stats['avg_hp_remaining']:.1f}\n")
            
            # Değerlendirme
            if stats['win_rate'] > 40:
                f.write(f"  ⭐ ÇOK GÜÇLÜ - Meta dominant strateji\n")
            elif stats['win_rate'] > 25:
                f.write(f"  ✓ GÜÇLÜ - Rekabetçi strateji\n")
            elif stats['win_rate'] > 15:
                f.write(f"  ~ ORTA - Duruma göre değişken\n")
            else:
                f.write(f"  ✗ ZAYIF - Buff gerektirebilir\n")
            
            f.write("\n")
        
        # 2. KART ANALİZİ
        f.write("\n" + "-" * 80 + "\n")
        f.write("2. KART PERFORMANS ANALİZİ\n")
        f.write("-" * 80 + "\n\n")
        
        # En yüksek kazanma oranına sahip kartlar (min 100 satın alma)
        high_winrate_cards = [
            (name, stats) for name, stats in card_perf.items()
            if stats['times_purchased'] >= 100
        ]
        high_winrate_cards.sort(key=lambda x: x[1]['win_rate'], reverse=True)
        
        f.write("EN YÜKSEK KAZANMA ORANINA SAHİP KARTLAR (min 100 satın alma):\n\n")
        f.write(f"{'Kart':<35} {'Kazanma %':<12} {'Satın Alma':<12} {'Ort. Güç':<12}\n")
        f.write("-" * 80 + "\n")
        
        for name, stats in high_winrate_cards[:15]:
            f.write(f"{name:<35} {stats['win_rate']:<12.1f} "
                   f"{stats['times_purchased']:<12} {stats['avg_power_contributed']:<12.1f}\n")
        
        f.write("\n")
        
        # En popüler kartlar
        popular_cards = sorted(
            card_perf.items(),
            key=lambda x: x[1]['times_purchased'],
            reverse=True
        )[:15]
        
        f.write("EN POPÜLER KARTLAR:\n\n")
        f.write(f"{'Kart':<35} {'Satın Alma':<12} {'Kazanma %':<12} {'Ort. Tur':<12}\n")
        f.write("-" * 80 + "\n")
        
        for name, stats in popular_cards:
            f.write(f"{name:<35} {stats['times_purchased']:<12} "
                   f"{stats['win_rate']:<12.1f} {stats['avg_survival_turns']:<12.1f}\n")
        
        f.write("\n")
        
        # 3. OYUN DİNAMİKLERİ
        f.write("\n" + "-" * 80 + "\n")
        f.write("3. OYUN DİNAMİKLERİ ANALİZİ\n")
        f.write("-" * 80 + "\n\n")
        
        # Tur sayısı dağılımı
        turn_counts = [game['turns'] for game in game_results]
        avg_turns = sum(turn_counts) / len(turn_counts)
        min_turns = min(turn_counts)
        max_turns = max(turn_counts)
        
        # Tur aralıklarına göre dağılım
        turn_ranges = {
            '11-15': 0,
            '16-20': 0,
            '21-25': 0,
            '26-30': 0,
            '31-35': 0,
            '36+': 0
        }
        
        for turns in turn_counts:
            if turns <= 15:
                turn_ranges['11-15'] += 1
            elif turns <= 20:
                turn_ranges['16-20'] += 1
            elif turns <= 25:
                turn_ranges['21-25'] += 1
            elif turns <= 30:
                turn_ranges['26-30'] += 1
            elif turns <= 35:
                turn_ranges['31-35'] += 1
            else:
                turn_ranges['36+'] += 1
        
        f.write("Oyun Uzunluğu İstatistikleri:\n\n")
        f.write(f"  Ortalama: {avg_turns:.1f} tur\n")
        f.write(f"  En kısa: {min_turns} tur\n")
        f.write(f"  En uzun: {max_turns} tur\n\n")
        
        f.write("Tur Dağılımı:\n\n")
        for range_name, count in turn_ranges.items():
            percentage = (count / len(turn_counts)) * 100
            bar = "█" * int(percentage / 2)
            f.write(f"  {range_name:<10} {count:>5} maç ({percentage:>5.1f}%)  {bar}\n")
        
        f.write("\n")
        
        # 4. ÖNERİLER
        f.write("\n" + "-" * 80 + "\n")
        f.write("4. BALANS ÖNERİLERİ\n")
        f.write("-" * 80 + "\n\n")
        
        # Builder çok dominant
        builder_stats = strategy_perf['builder']
        if builder_stats['win_rate'] > 50:
            f.write("⚠️  BUILDER STRATEJİSİ ÇOK DOMINANT:\n")
            f.write(f"   • Kazanma oranı: {builder_stats['win_rate']:.1f}% (hedef: ~25%)\n")
            f.write(f"   • Öneriler:\n")
            f.write(f"     - Board boyutu limitini azalt\n")
            f.write(f"     - Kart maliyetlerini artır\n")
            f.write(f"     - Tempo stratejisine buff ver\n\n")
        
        # Zayıf stratejiler
        weak_strategies = [
            (name, stats) for name, stats in strategy_perf.items()
            if stats['win_rate'] < 15
        ]
        
        if weak_strategies:
            f.write("⚠️  ZAYIF STRATEJİLER:\n\n")
            for name, stats in weak_strategies:
                f.write(f"   {name.upper()}:\n")
                f.write(f"     • Kazanma oranı: {stats['win_rate']:.1f}%\n")
                f.write(f"     • Öneriler: Strateji-spesifik buff gerekli\n\n")
        
        # Kart balansı
        f.write("KART BALANS ÖNERİLERİ:\n\n")
        
        # Çok güçlü kartlar (>45% kazanma oranı, >500 satın alma)
        overpowered_cards = [
            (name, stats) for name, stats in card_perf.items()
            if stats['win_rate'] > 45 and stats['times_purchased'] > 500
        ]
        
        if overpowered_cards:
            f.write("   Çok Güçlü Kartlar (nerf düşünülebilir):\n")
            for name, stats in sorted(overpowered_cards, key=lambda x: x[1]['win_rate'], reverse=True)[:5]:
                f.write(f"     • {name}: {stats['win_rate']:.1f}% kazanma oranı\n")
            f.write("\n")
        
        # Çok zayıf kartlar (<15% kazanma oranı, >500 satın alma)
        underpowered_cards = [
            (name, stats) for name, stats in card_perf.items()
            if stats['win_rate'] < 15 and stats['times_purchased'] > 500
        ]
        
        if underpowered_cards:
            f.write("   Zayıf Kartlar (buff düşünülebilir):\n")
            for name, stats in sorted(underpowered_cards, key=lambda x: x[1]['win_rate'])[:5]:
                f.write(f"     • {name}: {stats['win_rate']:.1f}% kazanma oranı\n")
            f.write("\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("RAPOR SONU\n")
        f.write("=" * 80 + "\n")
    
    print(f"✓ Kapsamlı analiz raporu oluşturuldu: {output_file}")

def main():
    """Ana fonksiyon"""
    print("=" * 80)
    print("5000 MAÇLIK SİMÜLASYON SONUÇLARI - DETAYLI ANALİZ")
    print("=" * 80)
    print()
    
    print("Analiz yapılıyor...")
    print()
    
    # Kapsamlı rapor oluştur
    generate_comprehensive_report()
    
    print()
    print("=" * 80)
    print("ANALİZ TAMAMLANDI!")
    print("=" * 80)
    print()
    print("Oluşturulan dosya:")
    print("  - output/detailed_simulation/comprehensive_analysis.txt")
    print()

if __name__ == "__main__":
    main()
