import argparse
import json
import random
import statistics
import traceback
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Tuple

from autochess_sim_v06 import (
    BOARD_COORDS,
    Game,
    Player,
    STARTING_HP,
    STRATEGIES,
)


@dataclass
class QAConfig:
    games: int = 300
    players: int = 4
    seed: int = 1337
    determinism_repeats: int = 3
    log_path: str = "qa_game_logs.jsonl"
    verbose: bool = False


def _build_players(n_players: int) -> List[Player]:
    shuffled = STRATEGIES[:]
    random.shuffle(shuffled)
    players: List[Player] = []
    for i in range(n_players):
        strategy = shuffled[i % len(shuffled)]
        players.append(Player(pid=i, strategy=strategy))
    return players


def _snapshot_game_state(game: Game) -> Dict:
    players_state = []
    for p in game.players:
        board_cards = []
        for coord, card in p.board.grid.items():
            board_cards.append(
                {
                    "coord": coord,
                    "name": card.name,
                    "rarity": card.rarity,
                    "power": card.total_power(),
                }
            )
        players_state.append(
            {
                "pid": p.pid,
                "strategy": p.strategy,
                "hp": p.hp,
                "alive": p.alive,
                "gold": p.gold,
                "hand_count": len(p.hand),
                "board_count": len(p.board.grid),
                "board_cards": board_cards,
                "stats": dict(p.stats),
            }
        )
    return {"turn": game.turn, "players": players_state}


def _validate_card_state(card) -> List[str]:
    errs: List[str] = []
    for stat_name, stat_val in card.stats.items():
        if isinstance(stat_val, (int, float)) and stat_val < 0:
            errs.append(f"negative_stat:{card.name}:{stat_name}:{stat_val}")
    for stat_name, edge_val in card.edges:
        if edge_val < 0:
            errs.append(f"negative_edge:{card.name}:{stat_name}:{edge_val}")
        if card.stats.get(stat_name, None) != edge_val:
            errs.append(f"edge_mismatch:{card.name}:{stat_name}:{edge_val}:{card.stats.get(stat_name, None)}")
    return errs


def _validate_game_state(game: Game) -> List[str]:
    anomalies: List[str] = []
    coord_set = set(BOARD_COORDS)

    for p in game.players:
        if p.hp < 0:
            anomalies.append(f"hp_negative:p{p.pid}:{p.hp}")
        if p.hp > STARTING_HP:
            anomalies.append(f"hp_above_start:p{p.pid}:{p.hp}")
        if p.gold < 0:
            anomalies.append(f"gold_negative:p{p.pid}:{p.gold}")

        seen_coords = set()
        for coord, card in p.board.grid.items():
            if coord not in coord_set:
                anomalies.append(f"invalid_coord:p{p.pid}:{coord}")
            if coord in seen_coords:
                anomalies.append(f"duplicate_coord:p{p.pid}:{coord}")
            seen_coords.add(coord)
            anomalies.extend(_validate_card_state(card))

        for card in p.hand:
            anomalies.extend(_validate_card_state(card))

        for k, v in p.stats.items():
            if isinstance(v, (int, float)) and v < 0:
                anomalies.append(f"player_stat_negative:p{p.pid}:{k}:{v}")

    return anomalies


def _run_single_game(game_id: int, n_players: int, verbose: bool) -> Tuple[Dict, Dict]:
    players = _build_players(n_players)
    game = Game(players, verbose=verbose)
    winner = game.run()

    total_damage = sum(p.stats.get("damage_dealt", 0) for p in players)
    total_kills = sum(p.stats.get("kills", 0) for p in players)
    total_combos = 0
    for line in game.log:
        if "combo=" in line:
            parts = line.split("combo=")
            for part in parts[1:]:
                num = ""
                for ch in part:
                    if ch.isdigit():
                        num += ch
                    else:
                        break
                if num:
                    total_combos += int(num)

    state_anomalies = _validate_game_state(game)

    game_log = {
        "game_id": game_id,
        "turns": game.turn,
        "winner": {
            "pid": winner.pid,
            "strategy": winner.strategy,
            "hp": winner.hp,
        },
        "total_damage": total_damage,
        "total_combos": total_combos,
        "total_kills": total_kills,
        "player_win_flags": {str(p.pid): int(p.pid == winner.pid) for p in players},
        "player_strategies": {str(p.pid): p.strategy for p in players},
        "anomalies": state_anomalies,
    }

    metrics = {
        "turns": game.turn,
        "total_damage": total_damage,
        "total_combos": total_combos,
        "total_kills": total_kills,
        "winner_pid": winner.pid,
        "winner_strategy": winner.strategy,
        "anomaly_count": len(state_anomalies),
    }
    return game_log, metrics


def run_crash_and_validation_batch(cfg: QAConfig, batch_seed: int, start_game_id: int = 0) -> Dict:
    random.seed(batch_seed)
    game_logs: List[Dict] = []
    crashes: List[Dict] = []
    metrics_list: List[Dict] = []
    all_anomalies: List[Dict] = []

    for i in range(cfg.games):
        game_id = start_game_id + i
        try:
            log, metrics = _run_single_game(game_id=game_id, n_players=cfg.players, verbose=cfg.verbose)
            game_logs.append(log)
            metrics_list.append(metrics)
            if log["anomalies"]:
                all_anomalies.append({"game_id": game_id, "anomalies": log["anomalies"]})
        except Exception as exc:
            crash_ctx = {
                "game_id": game_id,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
            crashes.append(crash_ctx)
            # best-effort context if game object existed in local scope
            if "game" in locals():
                try:
                    crash_ctx["context"] = _snapshot_game_state(locals()["game"])
                except Exception:
                    pass

    with open(cfg.log_path, "a", encoding="utf-8") as f:
        for row in game_logs:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    return {
        "seed": batch_seed,
        "games_attempted": cfg.games,
        "games_completed": len(game_logs),
        "crashes": crashes,
        "metrics": metrics_list,
        "anomalies": all_anomalies,
    }


def _metrics_signature(metrics_list: List[Dict]) -> List[Tuple]:
    return [
        (
            m["turns"],
            m["total_damage"],
            m["total_combos"],
            m["total_kills"],
            m["winner_pid"],
            m["winner_strategy"],
            m["anomaly_count"],
        )
        for m in metrics_list
    ]


def run_determinism_check(cfg: QAConfig) -> Dict:
    runs = []
    for r in range(cfg.determinism_repeats):
        seed = cfg.seed
        random.seed(seed)
        metrics_list: List[Dict] = []
        crashes: List[Dict] = []
        for i in range(min(50, cfg.games)):
            try:
                _, metrics = _run_single_game(game_id=i, n_players=cfg.players, verbose=False)
                metrics_list.append(metrics)
            except Exception as exc:
                crashes.append(
                    {
                        "run": r,
                        "game_id": i,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                        "traceback": traceback.format_exc(),
                    }
                )
                break
        runs.append({"run": r, "metrics": metrics_list, "crashes": crashes})

    baseline = _metrics_signature(runs[0]["metrics"]) if runs else []
    deterministic = True
    drift = []
    for run in runs[1:]:
        sig = _metrics_signature(run["metrics"])
        if sig != baseline:
            deterministic = False
            drift.append(
                {
                    "run": run["run"],
                    "baseline_len": len(baseline),
                    "run_len": len(sig),
                    "first_diff_index": next((i for i, (a, b) in enumerate(zip(baseline, sig)) if a != b), None),
                }
            )
        if run["crashes"]:
            deterministic = False

    return {"deterministic": deterministic, "drift": drift, "runs": runs}


def _safe_avg(vals: List[float]) -> float:
    return float(sum(vals) / len(vals)) if vals else 0.0


def aggregate_batch(batch: Dict) -> Dict:
    metrics = batch["metrics"]
    turns = [m["turns"] for m in metrics]
    damage = [m["total_damage"] for m in metrics]
    combos = [m["total_combos"] for m in metrics]
    kills = [m["total_kills"] for m in metrics]
    winners = [m["winner_pid"] for m in metrics]

    win_dist = Counter(winners)
    return {
        "games_completed": len(metrics),
        "average_damage_per_game": _safe_avg(damage),
        "average_game_length": _safe_avg(turns),
        "average_combo_count": _safe_avg(combos),
        "average_kill_count": _safe_avg(kills),
        "win_distribution_per_player": dict(win_dist),
        "turns_min_max": [min(turns) if turns else 0, max(turns) if turns else 0],
        "damage_min_max": [min(damage) if damage else 0, max(damage) if damage else 0],
        "combos_min_max": [min(combos) if combos else 0, max(combos) if combos else 0],
        "kills_min_max": [min(kills) if kills else 0, max(kills) if kills else 0],
        "anomaly_count": len(batch["anomalies"]),
        "crash_count": len(batch["crashes"]),
    }


def compare_batches(batch_a_summary: Dict, batch_b_summary: Dict) -> Dict:
    rel = {}
    keys = [
        "average_damage_per_game",
        "average_game_length",
        "average_combo_count",
        "average_kill_count",
    ]
    anomalies = []
    for k in keys:
        a = batch_a_summary[k]
        b = batch_b_summary[k]
        if a == 0:
            rel[k] = 0.0
            continue
        delta = (b - a) / a
        rel[k] = delta
        if abs(delta) > 0.10:
            anomalies.append({"metric": k, "relative_deviation": delta})
    return {"relative_deviation": rel, "anomalies": anomalies}


def main():
    parser = argparse.ArgumentParser(description="Autochess QA validation runner")
    parser.add_argument("--games", type=int, default=300, help="Crash/stat batch game count (200-500 önerilir)")
    parser.add_argument("--players", type=int, default=4, help="Player count")
    parser.add_argument("--seed", type=int, default=1337, help="Base seed")
    parser.add_argument("--determinism-repeats", type=int, default=3, help="Determinism rerun count")
    parser.add_argument("--log-path", type=str, default="qa_game_logs.jsonl", help="JSONL game log output")
    parser.add_argument("--verbose", action="store_true", help="Verbose game logging")
    args = parser.parse_args()

    cfg = QAConfig(
        games=args.games,
        players=args.players,
        seed=args.seed,
        determinism_repeats=args.determinism_repeats,
        log_path=args.log_path,
        verbose=args.verbose,
    )

    # deterministic clean log start
    with open(cfg.log_path, "w", encoding="utf-8"):
        pass

    crash_batch = run_crash_and_validation_batch(cfg, batch_seed=cfg.seed, start_game_id=0)
    crash_summary = aggregate_batch(crash_batch)

    # second independent batch for deviation detection
    compare_batch = run_crash_and_validation_batch(cfg, batch_seed=cfg.seed + 99991, start_game_id=cfg.games)
    compare_summary = aggregate_batch(compare_batch)
    deviation = compare_batches(crash_summary, compare_summary)

    determinism = run_determinism_check(cfg)

    report = {
        "config": {
            "games": cfg.games,
            "players": cfg.players,
            "seed": cfg.seed,
            "determinism_repeats": cfg.determinism_repeats,
            "log_path": cfg.log_path,
        },
        "crash_testing": {
            "batch_a": crash_summary,
            "batch_b": compare_summary,
            "batch_a_crashes": crash_batch["crashes"],
            "batch_b_crashes": compare_batch["crashes"],
            "batch_a_anomalies": crash_batch["anomalies"],
            "batch_b_anomalies": compare_batch["anomalies"],
        },
        "consistency_check": {
            "deterministic": determinism["deterministic"],
            "drift": determinism["drift"],
            "run_crashes": [r["crashes"] for r in determinism["runs"]],
        },
        "statistical_deviation": deviation,
        "totals": {
            "games_attempted": crash_batch["games_attempted"] + compare_batch["games_attempted"],
            "games_completed": crash_batch["games_completed"] + compare_batch["games_completed"],
            "total_crashes": len(crash_batch["crashes"]) + len(compare_batch["crashes"]),
            "total_anomalies": len(crash_batch["anomalies"]) + len(compare_batch["anomalies"]),
        },
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

