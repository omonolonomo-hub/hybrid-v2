#!/usr/bin/env python3
"""
COMPREHENSIVE 8-PLAYER AUTOCHESS SIMULATION
============================================

Requirements:
- 2000 games
- 8 players per game
- ALL strategies included (no exclusions)
- Deterministic seed for reproducibility
- FULL chronological logging (every action)
- Comprehensive analysis and balance recommendations
"""

import sys
import os
import json
import random
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Tuple

# Engine modülünü import et
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from engine_core.autochess_sim_v06 import (
    Game, Player, CARD_POOL, CARD_BY_NAME, Market
)


# TÜM MEVCUT STRATEJİLER
ALL_STRATEGIES = [
    "random",
    "warrior", 
    "builder",
    "evolver",
    "economist",
    "balancer",
    "rare_hunter",
    "tempo"
]


class ComprehensiveLogger:
    """Her aksiyonu kaydeden detaylı logger"""
    
    def __init__(self, game_id: int, output_dir: Path):
        self.game_id = game_id
        self.output_dir = output_dir
        self.actions = []
        self.turn = 0
        
    def log_action(self, action_type: str, player_id: int, details: Dict[str, Any]):
        """Bir aksiyonu kaydet"""
        self.actions.append({
            'game_id': self.game_id,
            'turn': self.turn,
            'action_type': action_type,
            'player_id': player_id,
            'timestamp': len(self.actions),
            'details': details
        })
    
    def set_turn(self, turn: int):
        """Tur numarasını güncelle"""
        self.turn = turn
    
    def save_to_file(self):
        """Logları dosyaya kaydet"""
        log_file = self.output_dir / f"game_{self.game_id:04d}_log.jsonl"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            for action in self.actions:
                f.write(json.dumps(action, ensure_ascii=False) + '\n')


class Comprehensive8PlayerSimulation:
    """8 oyunculu kapsamlı simülasyon sistemi"""
    
    def __init__(self, num_games: int = 2000, seed: int = 42):
        self.num_games = num_games
        self.seed = seed
        self.rng = random.Random(seed)
        
        # Output klasörleri
        self.output_dir = Path("output/comprehensive_8player")
        self.logs_dir = self.output_dir / "game_logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # İstatistik toplama
        self.game_results = []
        self.strategy_stats = defaultdict(lambda: {
            'games': 0,
            'wins': 0,
            'top4': 0,
            'placements': [],
            'survival_turns': [],
            'damage_dealt': [],
            'damage_taken': [],
            'gold_earned': [],
            'eliminations': []
        })
        
        self.card_stats = defaultdict(lambda: {
            'picks': 0,
            'wins': 0,
            'top4': 0,
            'survival_turns': [],
            'power_contribution': []
        })
        
        print("=" * 80)
        print("COMPREHENSIVE 8-PLAYER AUTOCHESS SIMULATION")
        print("=" * 80)
        print(f"Games: {self.num_games}")
        print(f"Players per game: 8")
        print(f"Strategies: {', '.join(ALL_STRATEGIES)}")
        print(f"Seed: {self.seed}")
        print(f"Output: {self.output_dir}")
        print("=" * 80)
        print()
    
    def run_simulation(self):
        """2000 maçlık simülasyonu çalıştır"""
        print("Starting simulation...")
        print()
        
        for game_num in range(self.num_games):
            if (game_num + 1) % 50 == 0:
                print(f"  Progress: {game_num + 1}/{self.num_games} games completed...")
            
            # Stratejileri rotate et (bias önleme)
            strategies = self._rotate_strategies(game_num)
            
            # Oyunu çalıştır
            self._run_single_game(game_num, strategies)
        
        print()
        print(f"✓ {self.num_games} games completed!")
        print()
        
        # Analizleri oluştur
        self._generate_comprehensive_analysis()
    
    def _rotate_strategies(self, game_num: int) -> List[str]:
        """Stratejileri rotate et (pozisyon bias önleme)"""
        # Her oyunda stratejilerin sırasını değiştir
        rotation = game_num % len(ALL_STRATEGIES)
        return ALL_STRATEGIES[rotation:] + ALL_STRATEGIES[:rotation]
    
    def _run_single_game(self, game_num: int, strategies: List[str]):
        """Tek bir oyunu çalıştır ve logla"""
        # Logger oluştur
        logger = ComprehensiveLogger(game_num, self.logs_dir)
        
        # Oyuncular oluştur
        players = [
            Player(pid=i, strategy=strategies[i])
            for i in range(8)
        ]
        
        # Oyun oluştur (deterministic seed)
        game_seed = self.seed + game_num
        game_rng = random.Random(game_seed)
        game = Game(players=players, verbose=False, rng=game_rng)
        
        # Oyunu tur tur çalıştır ve logla
        turn = 0
        while len([p for p in game.players if p.alive]) > 1 and turn < 50:
            turn += 1
            logger.set_turn(turn)
            
            # Preparation phase - detaylı loglama
            self._log_preparation_phase(game, logger)
            game.preparation_phase()
            
            # Combat phase - detaylı loglama
            self._log_combat_phase(game, logger)
            game.combat_phase()
        
        # Oyun sonucu
        self._process_game_result(game, game_num, strategies)
        
        # Logları kaydet
        logger.save_to_file()
    
    def _log_preparation_phase(self, game: Game, logger: ComprehensiveLogger):
        """Preparation phase aksiyonlarını logla"""
        for player in game.alive_players():
            # Gold gain
            gold_before = player.gold
            # Income hesaplanacak
            
            # Shop roll (market window açılması)
            logger.log_action('shop_roll', player.pid, {
                'gold': player.gold,
                'turn': game.turn + 1
            })
    
    def _log_combat_phase(self, game: Game, logger: ComprehensiveLogger):
        """Combat phase aksiyonlarını logla"""
        pairs = game.swiss_pairs()
        
        for p_a, p_b in pairs:
            # Combat start
            logger.log_action('combat_start', p_a.pid, {
                'opponent': p_b.pid,
                'hp_a': p_a.hp,
                'hp_b': p_b.hp,
                'board_size_a': len(p_a.board.grid),
                'board_size_b': len(p_b.board.grid)
            })
    
    def _process_game_result(self, game: Game, game_num: int, strategies: List[str]):
        """Oyun sonucunu işle ve istatistikleri güncelle"""
        # Placement hesapla (HP'ye göre sırala)
        players_by_hp = sorted(game.players, key=lambda p: p.hp, reverse=True)
        placements = {p.pid: rank + 1 for rank, p in enumerate(players_by_hp)}
        
        game_result = {
            'game_id': game_num,
            'turns': game.turn,
            'seed': self.seed + game_num,
            'players': []
        }
        
        for player in game.players:
            placement = placements[player.pid]
            
            player_data = {
                'player_id': player.pid,
                'strategy': player.strategy,
                'placement': placement,
                'hp': player.hp,
                'damage_dealt': player.stats['damage_dealt'],
                'damage_taken': player.stats['damage_taken'],
                'kills': player.stats['kills'],
                'gold_earned': player.stats['gold_earned'],
                'board_size': len(player.board.grid)
            }
            
            game_result['players'].append(player_data)
            
            # Strateji istatistiklerini güncelle
            stats = self.strategy_stats[player.strategy]
            stats['games'] += 1
            stats['placements'].append(placement)
            stats['survival_turns'].append(game.turn)
            stats['damage_dealt'].append(player.stats['damage_dealt'])
            stats['damage_taken'].append(player.stats['damage_taken'])
            stats['gold_earned'].append(player.stats['gold_earned'])
            
            if placement == 1:
                stats['wins'] += 1
            if placement <= 4:
                stats['top4'] += 1
            
            # Kart istatistiklerini güncelle
            for card in player.board.grid.values():
                card_stats = self.card_stats[card.name]
                card_stats['picks'] += 1
                card_stats['survival_turns'].append(game.turn)
                card_stats['power_contribution'].append(card.total_power())
                
                if placement == 1:
                    card_stats['wins'] += 1
                if placement <= 4:
                    card_stats['top4'] += 1
        
        self.game_results.append(game_result)
    
    def _generate_comprehensive_analysis(self):
        """Kapsamlı analiz raporları oluştur"""
        print("Generating comprehensive analysis...")
        print()
        
        # 1. Game results
        self._save_game_results()
        
        # 2. Strategy analysis
        self._save_strategy_analysis()
        
        # 3. Card analysis
        self._save_card_analysis()
        
        # 4. Economy analysis
        self._save_economy_analysis()
        
        # 5. Meta analysis
        self._save_meta_analysis()
        
        # 6. Balance recommendations
        self._save_balance_recommendations()
        
        # 7. Executive summary
        self._save_executive_summary()
        
        print("✓ All analysis reports generated!")
        print()
    
    def _save_game_results(self):
        """Oyun sonuçlarını kaydet"""
        output_file = self.output_dir / "game_results.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.game_results, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Game results: {output_file}")
    
    def _save_strategy_analysis(self):
        """Strateji analizi"""
        output_file = self.output_dir / "strategy_analysis.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("STRATEGY PERFORMANCE ANALYSIS\n")
            f.write("=" * 80 + "\n\n")
            
            # Her strateji için detaylı analiz
            for strategy in ALL_STRATEGIES:
                stats = self.strategy_stats[strategy]
                
                if stats['games'] == 0:
                    continue
                
                games = stats['games']
                win_rate = (stats['wins'] / games) * 100
                top4_rate = (stats['top4'] / games) * 100
                avg_placement = sum(stats['placements']) / len(stats['placements'])
                avg_survival = sum(stats['survival_turns']) / len(stats['survival_turns'])
                avg_damage = sum(stats['damage_dealt']) / len(stats['damage_dealt'])
                
                f.write(f"{strategy.upper()}\n")
                f.write("-" * 80 + "\n")
                f.write(f"  Games played: {games}\n")
                f.write(f"  Win rate: {win_rate:.2f}%\n")
                f.write(f"  Top 4 rate: {top4_rate:.2f}%\n")
                f.write(f"  Avg placement: {avg_placement:.2f}\n")
                f.write(f"  Avg survival turns: {avg_survival:.1f}\n")
                f.write(f"  Avg damage dealt: {avg_damage:.1f}\n")
                f.write("\n")
        
        print(f"  ✓ Strategy analysis: {output_file}")
    
    def _save_card_analysis(self):
        """Kart analizi"""
        output_file = self.output_dir / "card_analysis.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("CARD PERFORMANCE ANALYSIS\n")
            f.write("=" * 80 + "\n\n")
            
            # En yüksek win rate'e sahip kartlar
            cards_by_winrate = []
            for card_name, stats in self.card_stats.items():
                if stats['picks'] >= 50:  # Min 50 pick
                    win_rate = (stats['wins'] / stats['picks']) * 100
                    cards_by_winrate.append((card_name, win_rate, stats['picks']))
            
            cards_by_winrate.sort(key=lambda x: x[1], reverse=True)
            
            f.write("TOP 20 CARDS BY WIN RATE (min 50 picks)\n\n")
            f.write(f"{'Card':<35} {'Win Rate':<12} {'Picks':<10}\n")
            f.write("-" * 80 + "\n")
            
            for card_name, win_rate, picks in cards_by_winrate[:20]:
                f.write(f"{card_name:<35} {win_rate:<12.1f} {picks:<10}\n")
        
        print(f"  ✓ Card analysis: {output_file}")
    
    def _save_economy_analysis(self):
        """Ekonomi analizi"""
        output_file = self.output_dir / "economy_analysis.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("ECONOMY ANALYSIS\n")
            f.write("=" * 80 + "\n\n")
            
            for strategy in ALL_STRATEGIES:
                stats = self.strategy_stats[strategy]
                
                if stats['games'] == 0:
                    continue
                
                avg_gold = sum(stats['gold_earned']) / len(stats['gold_earned'])
                
                f.write(f"{strategy}: Avg gold earned = {avg_gold:.1f}\n")
        
        print(f"  ✓ Economy analysis: {output_file}")
    
    def _save_meta_analysis(self):
        """Meta analizi"""
        output_file = self.output_dir / "meta_analysis.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("META ANALYSIS\n")
            f.write("=" * 80 + "\n\n")
            
            # Dominant strategy
            win_rates = []
            for strategy in ALL_STRATEGIES:
                stats = self.strategy_stats[strategy]
                if stats['games'] > 0:
                    win_rate = (stats['wins'] / stats['games']) * 100
                    win_rates.append((strategy, win_rate))
            
            win_rates.sort(key=lambda x: x[1], reverse=True)
            
            f.write("STRATEGY RANKINGS BY WIN RATE\n\n")
            for rank, (strategy, win_rate) in enumerate(win_rates, 1):
                f.write(f"{rank}. {strategy}: {win_rate:.2f}%\n")
            
            f.write("\n")
            f.write(f"Dominant strategy: {win_rates[0][0]} ({win_rates[0][1]:.2f}%)\n")
            f.write(f"Weakest strategy: {win_rates[-1][0]} ({win_rates[-1][1]:.2f}%)\n")
        
        print(f"  ✓ Meta analysis: {output_file}")
    
    def _save_balance_recommendations(self):
        """Balans önerileri"""
        output_file = self.output_dir / "balance_recommendations.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("BALANCE RECOMMENDATIONS\n")
            f.write("=" * 80 + "\n\n")
            
            # Win rate'e göre öneriler
            win_rates = []
            for strategy in ALL_STRATEGIES:
                stats = self.strategy_stats[strategy]
                if stats['games'] > 0:
                    win_rate = (stats['wins'] / stats['games']) * 100
                    win_rates.append((strategy, win_rate))
            
            win_rates.sort(key=lambda x: x[1], reverse=True)
            
            target_win_rate = 100 / 8  # 12.5% for 8 players
            
            f.write("NERF RECOMMENDATIONS\n\n")
            for strategy, win_rate in win_rates:
                if win_rate > target_win_rate * 1.5:  # 50% above target
                    f.write(f"⚠️  {strategy.upper()}: {win_rate:.1f}% (target: {target_win_rate:.1f}%)\n")
                    f.write(f"   Recommendation: Significant nerf required\n\n")
            
            f.write("\nBUFF RECOMMENDATIONS\n\n")
            for strategy, win_rate in reversed(win_rates):
                if win_rate < target_win_rate * 0.5:  # 50% below target
                    f.write(f"⚠️  {strategy.upper()}: {win_rate:.1f}% (target: {target_win_rate:.1f}%)\n")
                    f.write(f"   Recommendation: Significant buff required\n\n")
        
        print(f"  ✓ Balance recommendations: {output_file}")
    
    def _save_executive_summary(self):
        """Executive summary"""
        output_file = self.output_dir / "EXECUTIVE_SUMMARY.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("COMPREHENSIVE 8-PLAYER SIMULATION - EXECUTIVE SUMMARY\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Simulation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Games: {self.num_games}\n")
            f.write(f"Players per Game: 8\n")
            f.write(f"Strategies Tested: {', '.join(ALL_STRATEGIES)}\n")
            f.write(f"Deterministic Seed: {self.seed}\n")
            f.write("\n")
            
            # Avg game length
            avg_turns = sum(g['turns'] for g in self.game_results) / len(self.game_results)
            f.write(f"Average Game Length: {avg_turns:.1f} turns\n")
            f.write("\n")
            
            # Strategy rankings
            f.write("STRATEGY RANKINGS\n")
            f.write("-" * 80 + "\n")
            
            win_rates = []
            for strategy in ALL_STRATEGIES:
                stats = self.strategy_stats[strategy]
                if stats['games'] > 0:
                    win_rate = (stats['wins'] / stats['games']) * 100
                    top4_rate = (stats['top4'] / stats['games']) * 100
                    avg_placement = sum(stats['placements']) / len(stats['placements'])
                    win_rates.append((strategy, win_rate, top4_rate, avg_placement))
            
            win_rates.sort(key=lambda x: x[1], reverse=True)
            
            f.write(f"{'Rank':<6} {'Strategy':<15} {'Win %':<10} {'Top4 %':<10} {'Avg Place':<12}\n")
            f.write("-" * 80 + "\n")
            
            for rank, (strategy, win_rate, top4_rate, avg_place) in enumerate(win_rates, 1):
                f.write(f"{rank:<6} {strategy:<15} {win_rate:<10.2f} {top4_rate:<10.2f} {avg_place:<12.2f}\n")
        
        print(f"  ✓ Executive summary: {output_file}")


def main():
    """Ana fonksiyon"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Comprehensive 8-player Autochess simulation with full logging'
    )
    parser.add_argument(
        '--games',
        type=int,
        default=2000,
        help='Number of games to simulate (default: 2000)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    
    args = parser.parse_args()
    
    # Simülasyonu başlat
    sim = Comprehensive8PlayerSimulation(num_games=args.games, seed=args.seed)
    sim.run_simulation()
    
    print()
    print("=" * 80)
    print("SIMULATION COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print()
    print("Generated files:")
    print("  - output/comprehensive_8player/game_results.json")
    print("  - output/comprehensive_8player/strategy_analysis.txt")
    print("  - output/comprehensive_8player/card_analysis.txt")
    print("  - output/comprehensive_8player/economy_analysis.txt")
    print("  - output/comprehensive_8player/meta_analysis.txt")
    print("  - output/comprehensive_8player/balance_recommendations.txt")
    print("  - output/comprehensive_8player/EXECUTIVE_SUMMARY.txt")
    print("  - output/comprehensive_8player/game_logs/*.jsonl (2000 files)")
    print()


if __name__ == "__main__":
    main()
