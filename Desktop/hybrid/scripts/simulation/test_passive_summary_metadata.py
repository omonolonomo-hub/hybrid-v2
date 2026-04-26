#!/usr/bin/env python3
"""
Test script to verify passive_summary.json metadata update
Tests that the file includes reference to passive_efficiency_kpi.jsonl
"""

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from engine_core.strategy_logger import StrategyLogger
from collections import Counter


def test_passive_summary_metadata():
    """Test that passive_summary.json includes metadata referencing KPI file"""
    print("="*60)
    print("🧪 PASSIVE SUMMARY METADATA TEST")
    print("="*60)
    
    # Create a test logger
    print("\n1️⃣ Creating test StrategyLogger...")
    output_dir = "output/test_strategy_logs"
    logger = StrategyLogger(enabled=True, output_dir=output_dir)
    print(f"   ✅ Logger created with output_dir: {output_dir}")
    
    # Populate some test data in _passive_card
    print("\n2️⃣ Populating test passive data...")
    logger._passive_card["TestCard1"] = {
        "triggers": Counter({"economy": 5, "combat": 3}),
        "delta_sum": 80,
        "strategies_using": Counter({"economist": 3, "warrior": 2})
    }
    logger._passive_card["TestCard2"] = {
        "triggers": Counter({"survival": 2}),
        "delta_sum": 30,
        "strategies_using": Counter({"balancer": 2})
    }
    print("   ✅ Test data populated")
    
    # Write passive summary
    print("\n3️⃣ Writing passive_summary.json...")
    logger._write_passive_summary()
    print("   ✅ passive_summary.json written")
    
    # Read and verify the file
    print("\n4️⃣ Verifying file contents...")
    summary_path = Path(output_dir) / "passive_summary.json"
    
    if not summary_path.exists():
        print(f"   ❌ File not found: {summary_path}")
        return False
    
    with open(summary_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Check for metadata
    if "_metadata" not in data:
        print("   ❌ Missing _metadata field")
        return False
    
    metadata = data["_metadata"]
    
    # Verify metadata fields
    required_fields = ["description", "detailed_kpi_file", "note"]
    for field in required_fields:
        if field not in metadata:
            print(f"   ❌ Missing metadata field: {field}")
            return False
    
    # Verify detailed_kpi_file value
    if metadata["detailed_kpi_file"] != "passive_efficiency_kpi.jsonl":
        print(f"   ❌ Incorrect detailed_kpi_file: {metadata['detailed_kpi_file']}")
        return False
    
    # Verify passive_cards field exists
    if "passive_cards" not in data:
        print("   ❌ Missing passive_cards field")
        return False
    
    # Verify passive_cards contains expected data
    passive_cards = data["passive_cards"]
    if len(passive_cards) != 2:
        print(f"   ❌ Expected 2 passive cards, got {len(passive_cards)}")
        return False
    
    print("   ✅ All metadata fields present and correct")
    print(f"\n   📋 Metadata:")
    print(f"      - description: {metadata['description']}")
    print(f"      - detailed_kpi_file: {metadata['detailed_kpi_file']}")
    print(f"      - note: {metadata['note']}")
    print(f"\n   📊 Passive cards: {len(passive_cards)} entries")
    
    # Display the structure
    print("\n5️⃣ File structure:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    print("\n" + "="*60)
    print("✅ TEST PASSED")
    print("="*60)
    
    print(f"\n📁 Generated file: {summary_path}")
    print("\n💡 The passive_summary.json now includes:")
    print("   - _metadata section with KPI file reference")
    print("   - passive_cards section with aggregated statistics")
    
    return True


if __name__ == "__main__":
    success = test_passive_summary_metadata()
    sys.exit(0 if success else 1)
