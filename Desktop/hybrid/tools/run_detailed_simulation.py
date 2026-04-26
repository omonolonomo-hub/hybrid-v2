#!/usr/bin/env python3
"""
Detaylı 5000 Maç Simülasyonu ve Analiz Sistemi

Bu script:
1. 5000 maç simülasyonu çalıştırır
2. Her maç için detaylı event logging yapar
3. Kapsamlı istatistikler ve analizler üretir
4. JSON/CSV formatında raporlar oluşturur
"""

import sys
import os
import json
import csv
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any

# Engine modülünü import et
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from engine_core.autochess_sim_v06 import (
    Game, Player, CARD_POOL, CARD_BY_NAME, AI
)
from engine_core.event_logger import init_event_logger, close_event_logger


class DetailedSimulation:
    """5000 maçlık detaylı simülasyon yöneticisi"""
    
    def __init__(self, num_games: int = 5000):
        self.num_games = num_games
        self.output_dir = Path("output/detailed_simulation")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # İstatistik toplama
        self.game_results = []
        self.strategy_stats = defaultdict(lambda: {
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'total_damage': 0,
            'total_kills': 0,
            'total_hp_remaining': 0,
            'total_synergy': 0,
            'total_gold_earned': 0,
            'games_played': 0,
            'total_turns_survived': 0
        })
        
        self.card_stats = defaultdict(lambda: {
            'times_purchased': 0,
            'times_on_winning_board': 0,
            'times_on_losing_board': 0,
            'total_survival_turns': 0,
            'total_power_contributed': 0
        })
        
        # Event logger'ı başlat
        self.logger = init_event_logger(enabled=True)
        
        print("=" * 70)
        print("DETAYLI SİMÜLASYON SİSTEMİ")
        print("=" * 70)
        print(f"Toplam maç sayısı: {self.num_games}")
        print(f"Output klasörü: {self.output_dir}")
        print(f"Event logging: AKTIF")
        print()
    
    def run_simulation(self):
        """5000 maç simülasyonu çalıştır"""
        print("Simülasyon başlatılıyor...")
        print()
        
        strategies = ["builder", "evolver", "economist", "balancer", 
                     "rare_hunter", "tempo"]
        
        for game_num in range(self.num_games):
            # İlerleme göster
            if (game_num + 1) % 100 == 0:
                print(f"  {game_num + 1}/{self.num_games} maç tamamlandı...")
            
            # Oyuncular oluştur
            players = [
                Player(pid=i, strategy=strategies[i % len(strategies)])
                for i in range(4)
            ]
            
            # Oyun oluştur
            game = Game(
                players=players,
                verbose=False  # Konsol çıktısını kapat
            )
            
            # Logger context'i ayarla
            self.logger.set_game_context(game_num, 0)
            
            # Oyunu çalıştır ve kaydet
            self._run_and_log_game(game, game_num)
        
        print()
        print(f"✓ {self.num_games} maç tamamlandı!")
        print()
        
        # Logger'ı kapat
        close_event_logger()
        
        # Analizleri çalıştır
        self._generate_reports()
    
    def _run_and_log_game(self, game: Game, game_num: int):
        """Tek bir oyunu çalıştır ve logla"""
        # Oyunu çalıştır
        winner = game.run()
        
        # Oyun sonucu kaydet
        winner_idx = winner.pid
        
        game_result = {
            'game_id': game_num,
            'turns': game.turn,
            'winner_strategy': winner.strategy,
            'players': []
        }
        
        for i, player in enumerate(game.players):
            player_data = {
                'player_id': i,
                'strategy': player.strategy,
                'final_hp': player.hp,
                'damage_dealt': player.stats['damage_dealt'],
                'kills': player.stats['kills'],
                'board_size': len(player.board.grid),
                'is_winner': (i == winner_idx)
            }
            
            game_result['players'].append(player_data)
            
            # Strateji istatistiklerini güncelle
            stats = self.strategy_stats[player.strategy]
            stats['games_played'] += 1
            stats['total_damage'] += player.stats['damage_dealt']
            stats['total_kills'] += player.stats['kills']
            stats['total_hp_remaining'] += player.hp
            stats['total_turns_survived'] += game.turn
            
            if i == winner_idx:
                stats['wins'] += 1
            elif player.hp <= 0:
                stats['losses'] += 1
            else:
                stats['draws'] += 1
            
            # Kart istatistiklerini güncelle
            for card in player.board.grid.values():
                card_stats = self.card_stats[card.name]
                card_stats['times_purchased'] += 1
                card_stats['total_survival_turns'] += game.turn
                card_stats['total_power_contributed'] += card.total_power()
                
                if i == winner_idx:
                    card_stats['times_on_winning_board'] += 1
                else:
                    card_stats['times_on_losing_board'] += 1
        
        self.game_results.append(game_result)
    
    def _generate_reports(self):
        """Kapsamlı raporlar oluştur"""
        print("Raporlar oluşturuluyor...")
        print()
        
        # 1. Oyun sonuçları (JSON)
        self._save_game_results()
        
        # 2. Strateji performans raporu (JSON + CSV)
        self._save_strategy_report()
        
        # 3. Kart performans raporu (JSON + CSV)
        self._save_card_report()
        
        # 4. Özet istatistikler (TXT)
        self._save_summary_report()
        
        print("✓ Tüm raporlar oluşturuldu!")
        print()
        print(f"Raporlar: {self.output_dir}/")
    
    def _save_game_results(self):
        """Tüm oyun sonuçlarını JSON'a kaydet"""
        output_file = self.output_dir / "game_results.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.game_results, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Oyun sonuçları: {output_file}")
    
    def _save_strategy_report(self):
        """Strateji performans raporunu kaydet"""
        # JSON formatı
        json_file = self.output_dir / "strategy_performance.json"
        
        strategy_report = {}
        for strategy, stats in self.strategy_stats.items():
            games = stats['games_played']
            if games == 0:
                continue
            
            strategy_report[strategy] = {
                'games_played': games,
                'wins': stats['wins'],
                'losses': stats['losses'],
                'draws': stats['draws'],
                'win_rate': round(stats['wins'] / games * 100, 2),
                'avg_damage': round(stats['total_damage'] / games, 1),
                'avg_kills': round(stats['total_kills'] / games, 1),
                'avg_hp_remaining': round(stats['total_hp_remaining'] / games, 1),
                'avg_turns_survived': round(stats['total_turns_survived'] / games, 1)
            }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(strategy_report, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Strateji performansı (JSON): {json_file}")
        
        # CSV formatı
        csv_file = self.output_dir / "strategy_performance.csv"
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Strategy', 'Games', 'Wins', 'Losses', 'Draws', 
                'Win Rate %', 'Avg Damage', 'Avg Kills', 'Avg HP', 'Avg Turns'
            ])
            
            for strategy, data in sorted(strategy_report.items()):
                writer.writerow([
                    strategy,
                    data['games_played'],
                    data['wins'],
                    data['losses'],
                    data['draws'],
                    data['win_rate'],
                    data['avg_damage'],
                    data['avg_kills'],
                    data['avg_hp_remaining'],
                    data['avg_turns_survived']
                ])
        
        print(f"  ✓ Strateji performansı (CSV): {csv_file}")
    
    def _save_card_report(self):
        """Kart performans raporunu kaydet"""
        # JSON formatı
        json_file = self.output_dir / "card_performance.json"
        
        card_report = {}
        for card_name, stats in self.card_stats.items():
            purchases = stats['times_purchased']
            if purchases == 0:
                continue
            
            wins = stats['times_on_winning_board']
            losses = stats['times_on_losing_board']
            total_games = wins + losses
            
            card_report[card_name] = {
                'times_purchased': purchases,
                'times_on_winning_board': wins,
                'times_on_losing_board': losses,
                'win_rate': round(wins / total_games * 100, 2) if total_games > 0 else 0,
                'avg_survival_turns': round(stats['total_survival_turns'] / purchases, 1),
                'avg_power_contributed': round(stats['total_power_contributed'] / purchases, 1)
            }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(card_report, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Kart performansı (JSON): {json_file}")
        
        # CSV formatı (en popüler 50 kart)
        csv_file = self.output_dir / "card_performance_top50.csv"
        
        # Satın alma sayısına göre sırala
        sorted_cards = sorted(
            card_report.items(),
            key=lambda x: x[1]['times_purchased'],
            reverse=True
        )[:50]
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Card Name', 'Purchases', 'On Winning Board', 'On Losing Board',
                'Win Rate %', 'Avg Survival Turns', 'Avg Power'
            ])
            
            for card_name, data in sorted_cards:
                writer.writerow([
                    card_name,
                    data['times_purchased'],
                    data['times_on_winning_board'],
                    data['times_on_losing_board'],
                    data['win_rate'],
                    data['avg_survival_turns'],
                    data['avg_power_contributed']
                ])
        
        print(f"  ✓ Kart performansı (CSV, Top 50): {csv_file}")
    
    def _save_summary_report(self):
        """Özet istatistikler raporu"""
        output_file = self.output_dir / "summary_report.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("DETAYLI SİMÜLASYON ÖZET RAPORU\n")
            f.write("=" * 70 + "\n")
            f.write(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Toplam maç sayısı: {self.num_games}\n")
            f.write("\n")
            
            # Strateji özeti
            f.write("-" * 70 + "\n")
            f.write("STRATEJİ PERFORMANSI\n")
            f.write("-" * 70 + "\n")
            f.write(f"{'Strateji':<15} {'Maç':<8} {'Galibiyet':<10} {'Oran %':<10} {'Ort. HP':<10}\n")
            f.write("-" * 70 + "\n")
            
            for strategy, stats in sorted(self.strategy_stats.items()):
                games = stats['games_played']
                if games == 0:
                    continue
                
                win_rate = stats['wins'] / games * 100
                avg_hp = stats['total_hp_remaining'] / games
                
                f.write(f"{strategy:<15} {games:<8} {stats['wins']:<10} "
                       f"{win_rate:<10.1f} {avg_hp:<10.1f}\n")
            
            f.write("\n")
            
            # Oyun uzunluğu istatistikleri
            turn_counts = [game['turns'] for game in self.game_results]
            avg_turns = sum(turn_counts) / len(turn_counts)
            min_turns = min(turn_counts)
            max_turns = max(turn_counts)
            
            f.write("-" * 70 + "\n")
            f.write("OYUN UZUNLUĞU İSTATİSTİKLERİ\n")
            f.write("-" * 70 + "\n")
            f.write(f"Ortalama tur sayısı: {avg_turns:.1f}\n")
            f.write(f"En kısa oyun: {min_turns} tur\n")
            f.write(f"En uzun oyun: {max_turns} tur\n")
            f.write("\n")
            
            # En popüler kartlar
            f.write("-" * 70 + "\n")
            f.write("EN POPÜLER 10 KART\n")
            f.write("-" * 70 + "\n")
            
            sorted_cards = sorted(
                self.card_stats.items(),
                key=lambda x: x[1]['times_purchased'],
                reverse=True
            )[:10]
            
            f.write(f"{'Kart':<30} {'Satın Alma':<15} {'Kazanma Oranı %':<20}\n")
            f.write("-" * 70 + "\n")
            
            for card_name, stats in sorted_cards:
                purchases = stats['times_purchased']
                wins = stats['times_on_winning_board']
                losses = stats['times_on_losing_board']
                total = wins + losses
                win_rate = (wins / total * 100) if total > 0 else 0
                
                f.write(f"{card_name:<30} {purchases:<15} {win_rate:<20.1f}\n")
            
            f.write("\n")
            f.write("=" * 70 + "\n")
        
        print(f"  ✓ Özet rapor: {output_file}")


def main():
    """Ana fonksiyon"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='5000 maçlık detaylı simülasyon ve analiz sistemi'
    )
    parser.add_argument(
        '--games',
        type=int,
        default=5000,
        help='Toplam maç sayısı (varsayılan: 5000)'
    )
    
    args = parser.parse_args()
    
    # Simülasyonu başlat
    sim = DetailedSimulation(num_games=args.games)
    sim.run_simulation()
    
    print()
    print("=" * 70)
    print("SİMÜLASYON TAMAMLANDI!")
    print("=" * 70)
    print()
    print("Oluşturulan dosyalar:")
    print("  - output/detailed_simulation/game_results.json")
    print("  - output/detailed_simulation/strategy_performance.json")
    print("  - output/detailed_simulation/strategy_performance.csv")
    print("  - output/detailed_simulation/card_performance.json")
    print("  - output/detailed_simulation/card_performance_top50.csv")
    print("  - output/detailed_simulation/summary_report.txt")
    print("  - output/logs/simulation_events.jsonl")
    print("  - output/logs/combat_events.jsonl")
    print()


if __name__ == "__main__":
    main()
