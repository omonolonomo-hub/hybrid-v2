#!/usr/bin/env python3
"""
Analyze which cards received micro-buff and verify the logic.
"""
import json
import os

def load_cards():
    """Load cards from JSON."""
    json_path = os.path.join(os.path.dirname(__file__), "..", "assets", "data", "cards.json")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_card_stats(card_entry):
    """Extract stats from card entry."""
    # Stats are in the "stats" object with keys like Power, Durability, etc.
    if "stats" in card_entry:
        return card_entry["stats"]
    return {}

def main():
    cards = load_cards()
    
    # Calculate global average
    total_stats = 0
    total_count = 0
    card_data = []
    
    for card in cards:
        stats = get_card_stats(card)
        if stats:
            card_avg = sum(stats.values()) / len(stats)
            card_data.append({
                "name": card["name"],
                "stats": stats,
                "avg": card_avg,
                "total": sum(stats.values())
            })
            total_stats += sum(stats.values())
            total_count += len(stats)
    
    global_avg = total_stats / total_count
    threshold = global_avg - 1
    
    print("=" * 60)
    print("MICRO-BUFF ANALYSIS")
    print("=" * 60)
    print(f"Global average stat: {global_avg:.2f}")
    print(f"Buff threshold: {threshold:.2f}")
    print()
    
    # Find cards that would be buffed
    buffed_cards = [c for c in card_data if c["avg"] < threshold]
    buffed_cards.sort(key=lambda x: x["avg"])
    
    print(f"Cards receiving micro-buff: {len(buffed_cards)}/{len(card_data)}")
    print()
    print("-" * 60)
    print(f"{'Card Name':<30} {'Avg':<8} {'Total':<8} {'Stats'}")
    print("-" * 60)
    
    for card in buffed_cards:
        stats_str = ", ".join(f"{k}:{v}" for k, v in card["stats"].items())
        print(f"{card['name']:<30} {card['avg']:<8.2f} {card['total']:<8} {stats_str}")
    
    print()
    print("=" * 60)
    print("VERIFICATION")
    print("=" * 60)
    print(f"Expected buffed count: {len(buffed_cards)}")
    print("This should match the simulation output: '[MICRO-BUFF] Applied to X/101 cards'")

if __name__ == "__main__":
    main()
