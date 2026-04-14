#!/usr/bin/env python3
"""
Mini Autochess Simulation for Testing Copy-Applied Logic and Unlimited Gold Economy
- Uses patched autochess_sim_v06.py
- Reproducible with random.seed(42)
- 3 players, 8 turns simulation
- Logs turn-by-turn: gold, copy triggers, pool counts, anomalies
"""

import random
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from engine_core.card import get_card_pool, Card
from engine_core.player import Player
from engine_core.market import Market
from engine_core.constants import (
    CARD_COSTS, COPY_THRESH, COPY_THRESH_C,
    BASE_INCOME, INTEREST_STEP, MAX_INTEREST, STARTING_HP,
)

CARD_BY_NAME = {c.name: c for c in get_card_pool()}

# Set seed for reproducibility
random.seed(42)

# ANSI color codes for visual clarity
GREEN = '\033[92m'  # Copy-applied triggers
YELLOW = '\033[93m'  # Gold increases
RED = '\033[91m'    # Anomalies
RESET = '\033[0m'

def log(msg, color=None):
    """Print with optional color."""
    if color:
        print(f"{color}{msg}{RESET}")
    else:
        print(msg)

def simulate_mini_game():
    """Run 8-turn simulation with 3 players."""
    log("=== AUTOCHESS MINI-GAME SIMULATION ===")
    log("Testing: Copy-Applied Logic & Unlimited Gold Economy")
    log("Players: 3 | Turns: 8 | Seed: 42\n")

    # Initialize market
    market = Market(get_card_pool())

    # Create 3 players with high initial gold (to test unlimited accumulation)
    players = []
    player_names = ["Alice", "Bob", "Charlie"]
    strategies = ["random", "economist", "random"]  # Mix strategies

    for i, name in enumerate(player_names):
        p = Player(pid=i, strategy=strategies[i])
        p.gold = 100  # High initial gold to test unlimited
        p.hp = STARTING_HP  # Full HP
        p.win_streak = 0  # No streak initially

        # Manually set initial decks with cards that can trigger copy thresholds
        # Alice: focus on rarity-1 (cheap, easy to buy multiples)
        # Bob/Charlie: mix of tiers for variety
        initial_cards = {
            "Alice": ["Frida Kahlo", "Sparta", "Industrial Revolution"],
            "Bob": ["Betelgeuse", "Fibonacci Sequence", "Higgs Boson"],
            "Charlie": ["Age of Discovery", "Exoplanet", "Cerberus"],
        }

        for card_name in initial_cards[name]:
            card = CARD_BY_NAME[card_name].clone()
            p.hand.append(card)
            p.copies[card_name] = p.copies.get(card_name, 0) + 1
            # Place on board for copy logic
            free = p.board.free_coords()
            if free:
                coord = free[0]
                p.board.place(coord, card)
                p.hand.remove(card)

        players.append(p)

    # Track initial pool counts for key cards
    key_cards = ["Frida Kahlo", "Sparta", "Betelgeuse", "Fibonacci Sequence", "Age of Discovery"]
    initial_pool = {name: market.pool_copies.get(name, 0) for name in key_cards}

    log(f"Initial Pool Counts: {initial_pool}")
    log(f"Initial Player Golds: {[p.gold for p in players]}\n")

    # Simulate 8 turns
    for turn in range(1, 9):
        log(f"--- TURN {turn} ---")

        # Deal market windows
        windows = {}
        for p in players:
            windows[p.pid] = market.deal_market_window(p, n=5)
            log(f"  {player_names[p.pid]} window: {[c.name for c in windows[p.pid]]}")

        # Players buy cards (simulate buying 1-3 cards each, preferring their theme)
        bought_this_turn = {}
        for p in players:
            bought = []
            window = windows[p.pid]
            # Simple buy logic: buy up to 2 cards if affordable
            for card in window[:2]:
                cost = CARD_COSTS[card.rarity]
                if p.gold >= cost:
                    p.buy_card(card)
                    bought.append(card)
            bought_this_turn[p.pid] = bought
            log(f"  {player_names[p.pid]} bought: {[c.name for c in bought]} (gold: {p.gold})")

        # Return unsold
        for p in players:
            market.return_unsold(p, bought=bought_this_turn[p.pid])

        # Apply income and interest
        for p in players:
            gold_before = p.gold
            p.income()  # Includes HP bonus if applicable
            p.apply_interest()
            gold_after = p.gold
            log(f"{YELLOW}  {player_names[p.pid]} gold: {gold_before} -> {gold_after} (+{gold_after - gold_before}){RESET}")

        # Check copy strengthening (simulate turn progression)
        for p in players:
            p.check_copy_strengthening(turn)
            # Log any copy-applied triggers
            for name, applied in p.copy_applied.items():
                if applied["2"] or applied["3"]:
                    triggers = []
                    if applied["2"]: triggers.append("2-copy")
                    if applied["3"]: triggers.append("3-copy")
                    log(f"{GREEN}  {player_names[p.pid]} copy-applied: {name} ({', '.join(triggers)}){RESET}")

        # Update win streaks (simulate random wins for variety)
        for p in players:
            if random.random() > 0.5:  # 50% chance to win
                p.win_streak += 1
            else:
                p.win_streak = 0

        # Log pool counts for key cards
        current_pool = {name: market.pool_copies.get(name, 0) for name in key_cards}
        log(f"  Pool Counts: {current_pool}")

        # Check for anomalies
        anomalies = []
        for p in players:
            if p.gold < 100:  # Gold should only increase or stay
                anomalies.append(f"{player_names[p.pid]} gold decreased")
            # Check copy-applied not triggered multiple times (but since we reset per turn, hard to check here)
        if anomalies:
            log(f"{RED}  Anomalies: {anomalies}{RESET}")

        log("")  # Blank line between turns

    log("=== SIMULATION COMPLETE ===")
    log(f"Final Golds: {[p.gold for p in players]}")
    log(f"Final Pool Counts: { {name: market.pool_copies.get(name, 0) for name in key_cards} }")

if __name__ == "__main__":
    simulate_mini_game()