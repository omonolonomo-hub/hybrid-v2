#!/usr/bin/env python3
"""
Verify that passive_efficiency_kpi.jsonl is consumable by learning systems
"""

import json
import os

kpi_file = "output/strategy_logs/passive_efficiency_kpi.jsonl"

print("="*70)
print("  LEARNING SYSTEM CONSUMABILITY TEST")
print("="*70)

if not os.path.exists(kpi_file):
    print(f"✗ File not found: {kpi_file}")
    exit(1)

print(f"✓ File exists: {kpi_file}")
print(f"  Size: {os.path.getsize(kpi_file):,} bytes")

# Load all records
records = []
with open(kpi_file, 'r', encoding='utf-8') as f:
    for line in f:
        records.append(json.loads(line))

print(f"  Total records: {len(records):,}")

# Analyze data
strategies = set(r["strategy"] for r in records)
passive_types = set(r["passive_type"] for r in records)
games = set(r["game_id"] for r in records)
wins = sum(1 for r in records if r["game_won"])

print(f"\n  Data Analysis:")
print(f"    Unique strategies: {len(strategies)}")
print(f"    Unique passive types: {len(passive_types)}")
print(f"    Unique games: {len(games)}")
print(f"    Records with wins: {wins} ({wins/len(records)*100:.1f}%)")

# Check field completeness
required_fields = [
    "game_id", "strategy", "card_name", "passive_type",
    "total_triggers", "raw_value", "normalized_value",
    "efficiency_score", "game_won"
]

print(f"\n  Field Validation:")
all_complete = True
for field in required_fields:
    missing = sum(1 for r in records if field not in r)
    if missing > 0:
        print(f"    ✗ {field}: {missing} records missing")
        all_complete = False
    else:
        print(f"    ✓ {field}: complete")

# Check value ranges
print(f"\n  Value Range Analysis:")
print(f"    Efficiency scores: {min(r['efficiency_score'] for r in records):.4f} to {max(r['efficiency_score'] for r in records):.4f}")
print(f"    Normalized values: {min(r['normalized_value'] for r in records):.2f} to {max(r['normalized_value'] for r in records):.2f}")
print(f"    Total triggers: {min(r['total_triggers'] for r in records)} to {max(r['total_triggers'] for r in records)}")

# Show top efficiency passives
print(f"\n  Top 5 Most Efficient Passives (by efficiency_score):")
sorted_records = sorted(records, key=lambda r: r['efficiency_score'], reverse=True)
for i, rec in enumerate(sorted_records[:5], 1):
    print(f"    {i}. {rec['card_name']} ({rec['passive_type']})")
    print(f"       Strategy: {rec['strategy']}, Efficiency: {rec['efficiency_score']:.4f}, Triggers: {rec['total_triggers']}")

# Verify learning system can group by strategy
print(f"\n  Strategy Aggregation Test:")
from collections import defaultdict
strategy_stats = defaultdict(lambda: {"total_triggers": 0, "total_normalized": 0.0, "count": 0})
for rec in records:
    s = strategy_stats[rec["strategy"]]
    s["total_triggers"] += rec["total_triggers"]
    s["total_normalized"] += rec["normalized_value"]
    s["count"] += 1

print(f"    Strategy-level aggregation successful:")
for strat in sorted(strategy_stats.keys()):
    s = strategy_stats[strat]
    avg_norm = s["total_normalized"] / s["count"]
    print(f"      {strat}: {s['count']} records, avg_normalized={avg_norm:.2f}")

print(f"\n{'='*70}")
if all_complete:
    print("  ✅ VERIFICATION PASSED")
    print("  - File is correctly formatted")
    print("  - All required fields present")
    print("  - Data is consumable by learning systems")
    print("  - Aggregation and filtering work correctly")
else:
    print("  ❌ VERIFICATION FAILED")
    print("  - Some fields are missing")
print("="*70)
