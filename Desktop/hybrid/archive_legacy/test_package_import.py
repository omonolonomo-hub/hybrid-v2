#!/usr/bin/env python
"""Test engine_core package import"""

print("=" * 60)
print("STEP 2 — Verify package import works")
print("=" * 60)

import engine_core
print(f"✓ version: {engine_core.__version__}")
print(f"✓ exports: {engine_core.__all__}")

print("\n" + "=" * 60)
print("STEP 3 — Verify each export is accessible")
print("=" * 60)

from engine_core import Card, get_card_pool, Board, Player, Market, Game, run_simulation

# Test Card
pool = get_card_pool()
print(f"✓ Card pool: {len(pool)} cards")
print(f"✓ First card: {pool[0].name}")

# Test Board
board = Board()
board.place(pool[0].clone(), (0, 0))
print(f"✓ Board alive: {len(board.alive_cards())} cards")

# Test Market
market = Market(pool)
market.refresh(pool)
print(f"✓ Market cards: {len(market.cards)} cards")

# Test Player
player = Player(pid=0, strategy='warrior')
print(f"✓ Player: {player.name} (strategy: {player.strategy})")

# Test Game
print(f"✓ Game class: {Game.__name__}")

# Test run_simulation
print(f"✓ run_simulation function: {run_simulation.__name__}")

print("\n" + "=" * 60)
print("✓ All exports OK")
print("=" * 60)
