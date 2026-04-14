"""Meta analysis runner - does not modify gameplay."""
import json
import random
import re
from collections import defaultdict
from statistics import mean, pstdev
from typing import Any, Dict, List, Tuple

from autochess_sim_v06 import Game, Player, STRATEGIES


def _board_rare_share(p: Player) -> float:
    n = len(p.board.grid)
    if n == 0:
        return 0.0
    hi = sum(1 for c in p.board.grid.values() if c.rarity in ("4", "5"))
    return hi / n


_COMBO_SEG = re.compile(r"P(\d+)=\d+ \(kill=\d+ combo=(\d+) synergy=\d+\)")


def _combo_from_log(lines: List[str], pid: int) -> int:
    total = 0
    for line in lines:
        for m in _COMBO_SEG.finditer(line):
            if int(m.group(1)) == pid:
                total += int(m.group(2))
    return total


def _infer_archetype(players: List[Player], log_lines: List[str]) -> Dict[int, str]:
    """Data-relative tagging within each game (no fixed outcome assumptions)."""
    n = len(players)
    spends = [p.stats.get("gold_spent", 0) for p in players]
    earns = [p.stats.get("gold_earned", 0) for p in players]
    damages = [p.stats.get("damage_dealt", 0) for p in players]
    kills = [p.stats.get("kills", 0) for p in players]
    synergy_avgs = [
        p.stats.get("synergy_sum", 0) / max(1, p.stats.get("synergy_turns", 0)) for p in players
    ]
    rare_shares = [_board_rare_share(p) for p in players]
    combos = [_combo_from_log(log_lines, p.pid) for p in players]
    total_buys = [sum(p.copies.values()) for p in players]
    finals_gold = [p.gold for p in players]

    def rank(vals: List[float], reverse: bool = True) -> List[int]:
        order = sorted(range(n), key=lambda i: vals[i], reverse=reverse)
        r = [0] * n
        for idx, i in enumerate(order):
            r[i] = idx
        return r

    r_spend = rank([float(x) for x in spends])
    r_earn = rank([float(x) for x in earns])
    r_dmg = rank([float(x) for x in damages])
    r_syn = rank([float(x) for x in synergy_avgs])
    r_rare = rank([float(x) for x in rare_shares])
    r_combo = rank([float(x) for x in combos])
    r_buysize = rank([float(x) for x in total_buys])
    r_gold_end = rank([float(x) for x in finals_gold])
    eco_eff = [
        earns[i] / max(1, spends[i]) for i in range(n)
    ]
    r_eco = rank(eco_eff)

    tags: Dict[int, str] = {}
    for i, p in enumerate(players):
        scores = {
            "economist": 0.0,
            "aggressive": 0.0,
            "combo_builder": 0.0,
            "high_rarity": 0.0,
            "balanced": 1.0,
        }
        # economist: strong end-gold / eco efficiency, not top spender
        if r_gold_end[i] <= 1:
            scores["economist"] += 2
        if r_eco[i] <= 1:
            scores["economist"] += 2
        if r_spend[i] >= n - 2:
            scores["economist"] -= 1.5

        # aggressive: high spend, damage, buys
        if r_spend[i] <= 1:
            scores["aggressive"] += 2
        if r_dmg[i] <= 1:
            scores["aggressive"] += 1.5
        if r_buysize[i] <= 1:
            scores["aggressive"] += 1

        # combo_builder
        if r_combo[i] <= 1:
            scores["combo_builder"] += 2.5
        if r_syn[i] <= 1:
            scores["combo_builder"] += 1.5

        # high_rarity
        if r_rare[i] <= 1:
            scores["high_rarity"] += 3

        best = max(scores, key=lambda k: scores[k])
        if scores[best] < 2.5:
            best = "balanced"
        tags[p.pid] = best
    return tags


def run_batch(games: int, n_players: int, seed: int) -> Dict[str, Any]:
    random.seed(seed)
    per_tag: Dict[str, List[Dict]] = defaultdict(list)
    per_ai: Dict[str, List[Dict]] = defaultdict(list)
    game_lens: List[int] = []

    for g in range(games):
        shuffled = STRATEGIES[:]
        random.shuffle(shuffled)
        players = [
            Player(pid=i, strategy=shuffled[i % len(shuffled)])
            for i in range(n_players)
        ]
        game = Game(players, verbose=False)
        winner = game.run()
        game_lens.append(game.turn)
        log_lines = game.log

        ranked = sorted(players, key=lambda p: (p.hp, p.total_pts), reverse=True)
        place = {p.pid: idx + 1 for idx, p in enumerate(ranked)}
        tags = _infer_archetype(players, log_lines)

        final_turn = game.turn
        for p in players:
            damage = p.stats.get("damage_dealt", 0)
            gold_gen = p.stats.get("gold_earned", 0)
            combo_pts = _combo_from_log(log_lines, p.pid)
            row = {
                "game_id": g,
                "placement": place[p.pid],
                "won": int(p.pid == winner.pid),
                "damage": damage,
                "combos": combo_pts,
                "kills": p.stats.get("kills", 0),
                "gold_generated": gold_gen,
                "ai_strategy": p.strategy,
                "behavior_tag": tags[p.pid],
                "game_length": final_turn,
            }
            per_tag[row["behavior_tag"]].append(row)
            per_ai[p.strategy].append(row)

    def summarize(rows: List[Dict]) -> Dict[str, Any]:
        if not rows:
            return {}
        wins = sum(r["won"] for r in rows)
        n = len(rows)
        win_rate = wins / n if n else 0
        won_rows = [r for r in rows if r["won"]]
        return {
            "appearances": n,
            "wins": wins,
            "win_rate": win_rate,
            "avg_placement": mean(r["placement"] for r in rows),
            "avg_damage": mean(r["damage"] for r in rows),
            "avg_combos": mean(r["combos"] for r in rows),
            "avg_kills": mean(r["kills"] for r in rows),
            "avg_gold_generated": mean(r["gold_generated"] for r in rows),
            "avg_game_length_on_win": mean(r["game_length"] for r in won_rows) if won_rows else 0.0,
            "placement_stdev": pstdev([r["placement"] for r in rows]) if n > 1 else 0.0,
        }

    tag_summary = {t: summarize(rows) for t, rows in per_tag.items()}
    ai_summary = {t: summarize(rows) for t, rows in per_ai.items()}

    return {
        "games": games,
        "players": n_players,
        "seed": seed,
        "avg_game_length": mean(game_lens),
        "behavior_tags": tag_summary,
        "ai_strategies": ai_summary,
    }


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=500)
    ap.add_argument("--players", type=int, default=4)
    ap.add_argument("--seed", type=int, default=424242)
    args = ap.parse_args()
    out = run_batch(args.games, args.players, args.seed)
    print(json.dumps(out, ensure_ascii=False, indent=2))
