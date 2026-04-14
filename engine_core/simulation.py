"""
================================================================
|         AUTOCHESS HYBRID - Simulation Module                 |
|  Simulation runner and statistics reporting                  |
================================================================

This module contains the simulation runner that executes multiple games
and aggregates statistics, along with result printing and logging.
"""

import random
import os as _os
from collections import defaultdict
from typing import Dict, List

# Log dosyasının sabit konumu (CWD'den bağımsız)
_LOG_DIR  = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'output', 'logs')
_LOG_PATH = _os.path.join(_LOG_DIR, 'simulation_log.txt')

# Import dependencies
try:
    from .game import Game
    from .player import Player
    from .constants import STRATEGIES
    from .passive_trigger import trigger_passive, get_passive_trigger_log, clear_passive_trigger_log
    from .card import get_card_pool
    from .strategy_logger import init_strategy_logger, get_strategy_logger
except ImportError:
    from game import Game
    from player import Player
    from constants import STRATEGIES
    from passive_trigger import trigger_passive, get_passive_trigger_log, clear_passive_trigger_log
    from card import get_card_pool
    try:
        from strategy_logger import init_strategy_logger, get_strategy_logger
    except ImportError:
        def init_strategy_logger(*a, **kw): return None
        def get_strategy_logger(): return None


# ===================================================================
# GAME LOGGING
# ===================================================================

def write_game_log(game: "Game", game_num: int, winner: "Player"):
    """Append a per-game summary block to simulation_log.txt."""
    _passive_trigger_log = get_passive_trigger_log()
    
    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"  GAME {game_num+1} | {game.turn} turns | Winner: P{winner.pid} ({winner.strategy}) HP={winner.hp}")
    lines.append(f"{'='*60}")
    
    # --- Evolution summary ---
    lines.append("\n  [EVOLUTIONS]")
    any_evo = False
    for p in game.players:
        if p.evolved_card_names:
            any_evo = True
            evo_details = ", ".join(f"{name} (turn {turn})"
                                   for name, turn in zip(p.evolved_card_names, p.evolution_turns))
            lines.append(f"    P{p.pid} ({p.strategy}): {evo_details} — {len(p.evolved_card_names)} total")
    if not any_evo:
        lines.append("    None")
    
    # --- Opponent board checks ---
    lines.append("\n  [OPPONENT BOARD CHECKS]")
    for p in game.players:
        checks = p.stats.get("opponent_board_checks", 0)
        lines.append(f"    P{p.pid} ({p.strategy}): {checks} checks")
    
    # Build set of card names that have real passives
    passive_card_names = {c.name for c in get_card_pool() if c.passive_type != "none"}
    # Also include evolved cards (they inherit passives)
    passive_card_names |= {f"Evolved {c.name}" for c in get_card_pool() if c.passive_type != "none"}
    
    # --- Passive trigger counts ---
    lines.append("\n  [PASSIVE TRIGGERS] (card -> trigger: count)")
    if _passive_trigger_log:
        for card_name in sorted(_passive_trigger_log.keys()):
            if card_name not in passive_card_names:
                continue
            triggers = _passive_trigger_log[card_name]
            trigger_str = ", ".join(f"{t}:{n}" for t, n in sorted(triggers.items()))
            lines.append(f"    {card_name}: {trigger_str}")
    else:
        lines.append("    None")
    
    # --- Combat win/loss ratio ---
    lines.append("\n  [COMBAT WIN RATE] (cards with 3+ combats, sorted by win rate)")
    ratio_rows = []
    for card_name, triggers in _passive_trigger_log.items():
        wins = triggers.get("combat_win", 0)
        losses = triggers.get("combat_lose", 0)
        total = wins + losses
        if total < 3:
            continue
        rate = wins / total
        ratio_rows.append((card_name, wins, losses, rate))
    ratio_rows.sort(key=lambda x: x[3], reverse=True)
    for card_name, wins, losses, rate in ratio_rows:
        bar = "#" * int(rate * 20)
        lines.append(f"    {card_name:<35} {wins}W {losses}L  {rate*100:.0f}%  {bar}")
    if not ratio_rows:
        lines.append("    No cards with 3+ combats")
    
    # --- Card survival ---
    lines.append("\n  [CARD SURVIVAL] (avg turns alive on board, per player)")
    for p in game.players:
        if not p.card_turns_alive:
            continue
        lines.append(f"    P{p.pid} ({p.strategy}):")
        sorted_cards = sorted(p.card_turns_alive.items(), key=lambda x: x[1], reverse=True)
        for card_name, turns in sorted_cards[:8]:  # top 8 longest-lived cards
            lines.append(f"      {card_name:<35} {turns} turns")
    
    _os.makedirs(_LOG_DIR, exist_ok=True)
    with open(_LOG_PATH, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ===================================================================
# SIMULATION RUNNER
# ===================================================================

def run_simulation(n_games: int = 100, n_players: int = 4,
                   verbose: bool = False, seed: int = None,
                   strategies: list = None, combat_phase_fn=None,
                   enable_strategy_logging: bool = False) -> dict:
    """Run N games and aggregate statistics.
    
    Args:
        n_games: Number of games to simulate
        n_players: Number of players per game
        verbose: Whether to print detailed logs
        seed: Random seed for reproducibility
        strategies: List of strategies to use (defaults to STRATEGIES)
        combat_phase_fn: Combat phase function (injected dependency)
        enable_strategy_logging: True → parametre bazlı strategy analytics aktif
        
    Returns:
        Dictionary with aggregated statistics
    """
    if seed is not None:
        random.seed(seed)
    rng = random.Random(seed)

    # ── Strategy Logger başlat ────────────────────────────────────────────────
    slogger = init_strategy_logger(
        enabled=enable_strategy_logging,
        output_dir="output/strategy_logs"
    )

    results = {
        "games":         n_games,
        "n_players":     n_players,
        "wins":          defaultdict(int),
        "avg_turns":     [],
        "avg_damage":    defaultdict(list),
        "avg_kills":     defaultdict(list),
        "avg_final_hp":  defaultdict(list),
        "avg_synergy":   defaultdict(list),
        "avg_eco_efficiency": defaultdict(list),
    }

    for game_num in range(n_games):
        # Clear log file at start of first game
        if game_num == 0:
            _os.makedirs(_LOG_DIR, exist_ok=True)
            open(_LOG_PATH, "w").close()
        # FIX 1: assign strategies randomly each game (not pure rotation).
        # If n_players <= len(STRATEGIES), shuffle gives diverse assignment;
        # if more players, still shuffle before cycling.
        shuffled = (strategies if strategies else STRATEGIES)[:]
        rng.shuffle(shuffled)
        players = []
        for i in range(n_players):
            strat = shuffled[i % len(shuffled)]
            players.append(Player(pid=i, strategy=strat))

        game = Game(players, verbose=(verbose and game_num == 0), rng=rng,
                    trigger_passive_fn=trigger_passive, 
                    combat_phase_fn=combat_phase_fn,
                    card_pool=get_card_pool())

        # ── Logger: oyun başlangıcı ───────────────────────────────────────
        if slogger is not None:
            slogger.begin_game(game_id=game_num)

        # ── Oyunu çalıştır ────────────────────────────────────────────────
        # Game.run() içindeki her turn'de set_turn çağrısı yapmak için
        # game.turn'ü preparation_phase sonrası logger'a bildiriyoruz.
        # Bunu için minimal bir monkey-patch yerine, logger turn'ü
        # end_game'deki board snapshot'dan alır; yeterlidir.
        winner = game.run()
        
        # ── Logger: oyun sonu ────────────────────────────────────────────
        if slogger is not None:
            slogger.end_game(game, winner)

        # Write game log and clear passive trigger log
        write_game_log(game, game_num, winner)
        clear_passive_trigger_log()

        results["wins"][winner.strategy] += 1
        results["avg_turns"].append(game.turn)

        for p in players:
            s = p.strategy
            results["avg_damage"][s].append(p.stats["damage_dealt"])
            results["avg_kills"][s].append(p.stats["kills"])
            results["avg_final_hp"][s].append(p.hp)
            
            # Synergy average per turn
            avg_synergy = (p.stats["synergy_sum"] / max(1, p.stats["synergy_turns"])) if p.stats["synergy_turns"] > 0 else 0
            results["avg_synergy"][s].append(avg_synergy)
            
            # Economy efficiency: gold earned / gold spent
            gold_earned = p.stats["gold_earned"]
            gold_spent = p.stats["gold_spent"]
            eco_efficiency = (gold_earned / max(1, gold_spent)) if gold_spent > 0 else 1.0
            results["avg_eco_efficiency"][s].append(eco_efficiency)

        if (game_num + 1) % 50 == 0 and not verbose:
            print(f"  {game_num+1}/{n_games} games completed...")

    # ── Logger: tüm simülasyon bitti, flush + özet ────────────────────────
    if slogger is not None:
        slogger.flush()
        slogger.print_summary(n_games=n_games)

    return results


# ===================================================================
# RESULTS PRINTER
# ===================================================================

def print_results(res: dict):
    """Print simulation results in a formatted table."""
    n = res["games"]
    strats = list(set(res["wins"].keys()) | set(res["avg_damage"].keys()))

    print(f"\n{'='*60}")
    print(f"  AUTOCHESS HYBRID - Simulation Results v0.6")
    print(f"  {n} games  |  {res['n_players']} players/game")
    print(f"{'='*60}")

    # Win rates
    print(f"\n{'-'*40}")
    print(f"  WIN RATES")
    print(f"{'-'*40}")
    for s in STRATEGIES:
        wins = res["wins"].get(s, 0)
        games_played = len(res["avg_damage"].get(s, []))
        if games_played == 0:
            continue
        rate = wins / (n / res["n_players"] * len(STRATEGIES)) * 100
        # simpler: wins / (n/player_per_strat)
        rate2 = wins / max(1, n // max(1, res["n_players"] // len(STRATEGIES))) * 100
        bar = "#" * int(wins / max(1, max(res["wins"].values())) * 20)
        print(f"  {s:<12} {wins:>4} wins  {rate2:5.1f}%  {bar}")

    # Averages
    print(f"\n{'-'*60}")
    print(f"  {'Strategy':<14} {'Avg Dmg':>12} {'Avg Kill':>10} {'Avg HP':>10}")
    print(f"{'-'*60}")
    for s in STRATEGIES:
        dmgs  = res["avg_damage"].get(s, [0])
        kills = res["avg_kills"].get(s, [0])
        hps   = res["avg_final_hp"].get(s, [0])
        def avg(lst): return sum(lst)/len(lst) if lst else 0
        print(f"  {s:<14} {avg(dmgs):>12.1f} {avg(kills):>10.1f} {avg(hps):>10.1f}")

    # Synergy & economy
    print(f"\n{'-'*60}")
    print(f"  {'Strategy':<14} {'Avg Synergy':>14} {'Eco eff.':>15}")
    print(f"{'-'*60}")
    for s in STRATEGIES:
        synergy = res["avg_synergy"].get(s, [0])
        eco = res["avg_eco_efficiency"].get(s, [0])
        def avg(lst): return sum(lst)/len(lst) if lst else 0
        syn_avg = avg(synergy)
        eco_avg = avg(eco)
        print(f"  {s:<14} {syn_avg:>14.2f} {eco_avg:>14.2f}x")

    # Game length
    turns = res["avg_turns"]
    if turns:
        print(f"\n{'-'*40}")
        print(f"  GAME LENGTH")
        print(f"{'-'*40}")
        print(f"  Average turns: {sum(turns)/len(turns):.1f}")
        print(f"  Shortest game: {min(turns)} turns")
        print(f"  Longest game : {max(turns)} turns")

    print(f"\n{'='*60}\n")
