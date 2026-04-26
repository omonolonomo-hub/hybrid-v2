#!/usr/bin/env python3
"""
Analyze all batch files and create comprehensive summary.
"""

import os
import re
from collections import defaultdict

def parse_batch_file(filename):
    """Parse a batch file and extract strategy performance."""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find batch analysis section
    batch_section = re.search(r'BATCH \d+ ANALYSIS.*?BEST STRATEGY:', content, re.DOTALL)
    if not batch_section:
        return {}
    
    section_text = batch_section.group(0)
    
    # Extract strategy wins
    strategy_wins = {}
    for match in re.finditer(r'(\w+):\s+Wins: (\d+)', section_text):
        strategy = match.group(1)
        wins = int(match.group(2))
        strategy_wins[strategy] = wins
    
    return strategy_wins

def main():
    """Analyze all batch files."""
    batch_files = [
        'output/logs/kpi_baseline/sim_results_1_100.txt',
        'output/logs/kpi_baseline/sim_results_101_200.txt',
        'output/logs/kpi_baseline/sim_results_201_300.txt',
        'output/logs/kpi_baseline/sim_results_301_400.txt',
        'output/logs/kpi_baseline/sim_results_401_500.txt',
    ]
    
    total_wins = defaultdict(int)
    batch_results = []
    
    print("\n" + "="*80)
    print("  COMPREHENSIVE BATCH ANALYSIS - All 500 Games")
    print("="*80 + "\n")
    
    for i, filename in enumerate(batch_files, 1):
        if not os.path.exists(filename):
            print(f"  ⚠️  Batch {i} file not found: {filename}")
            continue
        
        wins = parse_batch_file(filename)
        batch_results.append((i, wins))
        
        print(f"Batch {i} (Games {(i-1)*100+1}-{i*100}):")
        sorted_wins = sorted(wins.items(), key=lambda x: x[1], reverse=True)
        for strategy, count in sorted_wins[:3]:
            total_wins[strategy] += count
            print(f"  {strategy:12} {count:3} wins ({count}%)")
        print()
        
        for strategy, count in wins.items():
            total_wins[strategy] += count
    
    # Overall summary
    print("="*80)
    print("  OVERALL SUMMARY (500 Games)")
    print("="*80 + "\n")
    
    sorted_total = sorted(total_wins.items(), key=lambda x: x[1], reverse=True)
    
    print("Strategy Performance:")
    print("-"*80)
    for strategy, wins in sorted_total:
        win_rate = (wins / 500) * 100
        bar = "█" * int(win_rate / 2)
        print(f"  {strategy:12} {wins:4} wins  {win_rate:5.1f}%  {bar}")
    
    print("\n" + "="*80)
    print(f"  Best Strategy: {sorted_total[0][0]} ({sorted_total[0][1]} wins, {(sorted_total[0][1]/500)*100:.1f}%)")
    print("="*80 + "\n")
    
    # Write to file
    with open('output/logs/kpi_baseline/OVERALL_SUMMARY.txt', 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("  AUTOCHESS HYBRID - OVERALL KPI SUMMARY\n")
        f.write("  500 Games Comprehensive Analysis\n")
        f.write("="*80 + "\n\n")
        
        f.write("STRATEGY WIN RATES:\n")
        f.write("-"*80 + "\n")
        for strategy, wins in sorted_total:
            win_rate = (wins / 500) * 100
            f.write(f"  {strategy:12} {wins:4} wins  {win_rate:5.1f}%\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write(f"  BEST STRATEGY: {sorted_total[0][0]}\n")
        f.write(f"  Total Wins: {sorted_total[0][1]}/500 ({(sorted_total[0][1]/500)*100:.1f}%)\n")
        f.write("="*80 + "\n\n")
        
        f.write("BATCH-BY-BATCH BREAKDOWN:\n")
        f.write("-"*80 + "\n")
        for batch_num, wins in batch_results:
            f.write(f"\nBatch {batch_num} (Games {(batch_num-1)*100+1}-{batch_num*100}):\n")
            sorted_wins = sorted(wins.items(), key=lambda x: x[1], reverse=True)
            for strategy, count in sorted_wins:
                f.write(f"  {strategy:12} {count:3} wins\n")
    
    print("  ✓ Overall summary saved to output/logs/kpi_baseline/OVERALL_SUMMARY.txt\n")

if __name__ == '__main__':
    main()
