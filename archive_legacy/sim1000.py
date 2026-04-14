#!/usr/bin/env python3
"""
================================================================
  AUTOCHESS HYBRID — 1000 Oyun Simülasyonu + Tam KPI Logu
  Çalıştır: python sim1000.py
================================================================
  Detaylı loglar her zaman aktif — output/strategy_logs/
    placement_events.jsonl   kart yerleşimleri
    combat_events.jsonl      tur bazlı combat sonuçları
    buy_events.jsonl         kart alım kararları
    game_endings.jsonl       oyun sonu özet
    strategy_summary.json    strateji KPI özeti
    passive_summary.json     passive etkinlik tablosu
    passive_efficiency_kpi.jsonl  passive etkinlik KPI verileri
    kpi_training.json        AI eğitimi için normalize KPI vektörleri
================================================================
"""

import sys, os, json, time, traceback, random, math, argparse
from collections import defaultdict
from statistics import mean, median

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from engine_core.card import get_card_pool
from engine_core.constants import STRATEGIES, STARTING_HP, CARD_COSTS, HAND_LIMIT, PLACE_PER_TURN
from engine_core.player import Player
from engine_core.game import Game
from engine_core.board import combat_phase
from engine_core.passive_trigger import trigger_passive, clear_passive_trigger_log
from engine_core.strategy_logger import init_strategy_logger
from engine_core.ai import ParameterizedAI

# ── CLI args ──────────────────────────────────────────────────────────────────
_parser = argparse.ArgumentParser(add_help=False)
_parser.add_argument("--games", type=int, default=None)
_parser.add_argument("--seed",  type=int, default=None)
_cli, _ = _parser.parse_known_args()

# ── Config ────────────────────────────────────────────────────
N_GAMES   = _cli.games if _cli.games is not None else 1000
N_PLAYERS = 8
SEED      = _cli.seed  if _cli.seed  is not None else 2024
OUT_DIR   = os.path.join(ROOT, "output", "results")
LOG_DIR   = os.path.join(ROOT, "output", "strategy_logs")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# ── Bug Kayıt ────────────────────────────────────────────────
bugs = []

def bug(game_num, turn, sev, code, msg):
    bugs.append({"game": game_num, "turn": turn,
                 "sev": sev, "code": code, "msg": msg})

# ── İstatistik ───────────────────────────────────────────────
wins           = defaultdict(int)
games_played   = defaultdict(int)
dmg_by_strat   = defaultdict(list)
kills_by_strat = defaultdict(list)
hp_by_strat    = defaultdict(list)
synergy_by_strat = defaultdict(list)
eco_by_strat   = defaultdict(list)
all_turns      = []
turn_50_count  = 0
crash_count    = 0
per_game_rows  = []

# ── Validatör ───────────────────────────────────────────────
def validate_game_snapshot(game_num, turn, players):
    alive = [p for p in players if p.alive]
    dead  = [p for p in players if not p.alive]

    for p in dead:
        if p.board.alive_count() > 0:
            bug(game_num, turn, "WARNING", "B1_DEAD_BOARD",
                f"P{p.pid}({p.strategy}) ölü ama board'unda {p.board.alive_count()} kart var")
    for p in players:
        if p.hp < 0:
            bug(game_num, turn, "CRITICAL", "B2_NEGATIVE_HP",
                f"P{p.pid}({p.strategy}) HP={p.hp}")
        if p.hp > STARTING_HP:
            bug(game_num, turn, "WARNING", "B3_HP_OVER_MAX",
                f"P{p.pid}({p.strategy}) HP={p.hp}")
        if len(p.hand) > HAND_LIMIT + 1:
            bug(game_num, turn, "WARNING", "B4_HAND_OVERFLOW",
                f"P{p.pid}({p.strategy}) hand={len(p.hand)}")
    for p in alive:
        if p.gold < 0:
            bug(game_num, turn, "CRITICAL", "B6_NEGATIVE_GOLD",
                f"P{p.pid}({p.strategy}) gold={p.gold}")
        for coord, card in p.board.grid.items():
            for ei, (stat, val) in enumerate(card.edges):
                if val > 200:
                    bug(game_num, turn, "WARNING", "B7_EDGE_OVERFLOW",
                        f"P{p.pid} {card.name}[{ei}]={val}")
                if val < 0:
                    bug(game_num, turn, "CRITICAL", "B7_EDGE_NEGATIVE",
                        f"P{p.pid} {card.name}[{ei}]={val}")
        for coord, card in p.board.grid.items():
            if p.board.coord_index.get(card.uid) != coord:
                bug(game_num, turn, "CRITICAL", "B9_COORD_INDEX_CORRUPT",
                    f"P{p.pid} {card.name} grid={coord} idx={p.board.coord_index.get(card.uid)}")
    if len(alive) == 0 and turn < 50:
        bug(game_num, turn, "CRITICAL", "B8_ALL_DEAD",
            f"Tüm oyuncular {turn}. turda öldü")


def validate_final_state(game_num, game, winner):
    global turn_50_count
    if game.turn >= 50:
        turn_50_count += 1
        bug(game_num, game.turn, "WARNING", "F1_TURN_LIMIT", "50 tur limitine çarptı")
    if winner.hp <= 0:
        bug(game_num, game.turn, "CRITICAL", "F2_WINNER_DEAD",
            f"Kazanan HP={winner.hp}")
    if game.turn == 0:
        bug(game_num, 0, "CRITICAL", "F4_ZERO_TURNS", "Oyun 0 turda bitti")


# ── buy_card hook ────────────────────────────────────────────
# Player.buy_card'ı slogger ile beslemek için monkey-patch
_orig_buy_card = Player.buy_card

def _patched_buy_card(self, card, market=None, trigger_passive_fn=None):
    gold_before = self.gold
    _orig_buy_card(self, card, market=market,
                   trigger_passive_fn=trigger_passive_fn)
    # Satın alma gerçekleştiyse logla (gold azaldıysa)
    if self.gold < gold_before:
        _slogger = _get_slogger()
        if _slogger is not None:
            _slogger.log_buy(self, card, gold_before)

Player.buy_card = _patched_buy_card


def _get_slogger():
    from engine_core.strategy_logger import get_strategy_logger
    return get_strategy_logger()


# ── game.py combat_phase'den sonra log için Game sınıfını monkey-patch ───
_orig_game_combat_phase = Game.combat_phase

def _patched_game_combat_phase(self):
    _orig_game_combat_phase(self)
    # last_combat_results'dan logları üret
    _slogger = _get_slogger()
    if _slogger is None:
        return
    pid_to_player = {p.pid: p for p in self.players}
    for res in self.last_combat_results:
        pa = pid_to_player.get(res["pid_a"])
        pb = pid_to_player.get(res["pid_b"])
        if pa is None or pb is None:
            continue
        _slogger.log_combat(
            player_a=pa, player_b=pb,
            pts_a=res["pts_a"], pts_b=res["pts_b"],
            kill_a=res["kill_a"], kill_b=res["kill_b"],
            combo_a=res["combo_a"], combo_b=res["combo_b"],
            synergy_a=res["synergy_a"], synergy_b=res["synergy_b"],
            winner_pid=res["winner_pid"],
            dmg=res["dmg"],
            draws=res["draws"],
        )
        _slogger.set_turn(self.turn)

Game.combat_phase = _patched_game_combat_phase


# ── Ana Simülasyon ───────────────────────────────────────────
def main():
    global crash_count

    print("=" * 65)
    print("  AUTOCHESS HYBRID — 1000 Oyun Simülasyonu + Tam KPI Log")
    print("=" * 65)
    print(f"  {N_GAMES} oyun | {N_PLAYERS} oyuncu/oyun | seed={SEED}")
    print(f"  Loglar: {LOG_DIR}/")
    print()

    slogger = init_strategy_logger(enabled=True, output_dir=LOG_DIR)

    card_pool = get_card_pool()
    rng = random.Random(SEED)
    t0  = time.time()

    # ParameterizedAI: JSON'u bir kez oku, tüm oyunlarda paylaş.
    # Tuner her run başında JSON'u güncelledikten sonra sim1000.py'yi başlatır,
    # dolayısıyla oyun döngüsü boyunca parametre değerleri sabit kalır.
    ai_instance = ParameterizedAI(strategy="tempo")

    for game_num in range(1, N_GAMES + 1):
        try:
            clear_passive_trigger_log()

            shuffled = STRATEGIES[:]
            rng.shuffle(shuffled)
            players = [
                Player(pid=i, strategy=shuffled[i % len(shuffled)])
                for i in range(N_PLAYERS)
            ]

            game = Game(
                players,
                verbose=False,
                rng=rng,
                trigger_passive_fn=trigger_passive,
                combat_phase_fn=combat_phase,
                card_pool=card_pool,
                ai_override=ai_instance,
            )

            slogger.begin_game(game_id=game_num)

            while len([p for p in game.players if p.alive]) > 1:
                if game.turn >= 50:
                    break
                game.preparation_phase()
                slogger.set_turn(game.turn)
                game.combat_phase()
                # Builder synergy matrix: her tur sonunda decay
                for _p in game.players:
                    if _p.alive and getattr(_p, 'synergy_matrix', None) is not None:
                        _p.synergy_matrix.decay()
                if game.turn % 5 == 0:
                    validate_game_snapshot(game_num, game.turn, players)

            alive_players = [p for p in game.players if p.alive]
            winner = max(
                alive_players if alive_players else game.players,
                key=lambda p: p.hp
            )

            validate_final_state(game_num, game, winner)
            slogger.end_game(game, winner)

            wins[winner.strategy] += 1
            all_turns.append(game.turn)

            for p in players:
                games_played[p.strategy] += 1
                dmg_by_strat[p.strategy].append(p.stats.get("damage_dealt", 0))
                kills_by_strat[p.strategy].append(p.stats.get("kills", 0))
                hp_by_strat[p.strategy].append(p.hp)
                syn_t = max(1, p.stats.get("synergy_turns", 1))
                synergy_by_strat[p.strategy].append(
                    p.stats.get("synergy_sum", 0) / syn_t)
                spent = max(1, p.stats.get("gold_spent", 1))
                eco_by_strat[p.strategy].append(
                    p.stats.get("gold_earned", 0) / spent)

            per_game_rows.append({
                "game": game_num, "turns": game.turn,
                "winner": winner.strategy, "winner_hp": winner.hp,
            })

        except Exception as exc:
            crash_count += 1
            bug(game_num, -1, "CRITICAL", "CRASH",
                f"{exc}\n{traceback.format_exc()}")
            continue

        if game_num % 100 == 0:
            elapsed = time.time() - t0
            rate    = game_num / elapsed
            eta     = (N_GAMES - game_num) / max(rate, 0.001)
            print(f"  [{game_num:>4}/{N_GAMES}] {elapsed:>5.1f}s | "
                  f"{rate:>5.1f} oyun/s | ETA {eta:>4.0f}s | Bug: {len(bugs)}")

    elapsed = time.time() - t0
    print(f"\n  Tamamlandı: {elapsed:.1f}s | {N_GAMES/elapsed:.1f} oyun/s")

    slogger.flush()
    slogger.print_summary(n_games=N_GAMES)

    _write_reports(elapsed)
    _print_report()


def _avgs(lst):
    if not lst: return 0, 0, 0, 0
    return mean(lst), median(lst), min(lst), max(lst)


def _write_reports(elapsed):
    summary = {
        "config": {"games": N_GAMES, "players": N_PLAYERS, "seed": SEED},
        "runtime": {"seconds": round(elapsed, 2),
                    "games_per_sec": round(N_GAMES / elapsed, 2)},
        "game_length": {
            "avg":          round(mean(all_turns), 2) if all_turns else 0,
            "median":       median(all_turns) if all_turns else 0,
            "min":          min(all_turns) if all_turns else 0,
            "max":          max(all_turns) if all_turns else 0,
            "turn_50_hits": turn_50_count,
        },
        "crashes": crash_count,
        "total_bugs": len(bugs),
        "bugs_by_severity": {
            sev: sum(1 for b in bugs if b["sev"] == sev)
            for sev in ("CRITICAL", "WARNING", "INFO")
        },
        "strategies": {},
    }

    for s in STRATEGIES:
        gp = games_played[s]
        if not gp:
            continue
        w = wins[s]
        summary["strategies"][s] = {
            "games_played": gp,
            "wins": w,
            "win_rate_pct": round(w / gp * 100, 2),
            "avg_damage":  round(mean(dmg_by_strat[s]),   2) if dmg_by_strat[s]   else 0,
            "avg_kills":   round(mean(kills_by_strat[s]), 2) if kills_by_strat[s] else 0,
            "avg_final_hp":round(mean(hp_by_strat[s]),    2) if hp_by_strat[s]    else 0,
            "avg_synergy": round(mean(synergy_by_strat[s]),2) if synergy_by_strat[s] else 0,
            "avg_eco_eff": round(mean(eco_by_strat[s]),   2) if eco_by_strat[s]   else 0,
        }

    rates = [v["win_rate_pct"] for v in summary["strategies"].values()]
    if rates:
        expected = 100 / N_PLAYERS
        summary["balance"] = {
            "expected_win_rate_pct": round(expected, 2),
            "max_deviation_pct":     round(max(abs(r - expected) for r in rates), 2),
            "dominant_strategy":     max(summary["strategies"],
                key=lambda s: summary["strategies"][s]["win_rate_pct"]),
            "weakest_strategy":      min(summary["strategies"],
                key=lambda s: summary["strategies"][s]["win_rate_pct"]),
        }

    out_json = os.path.join(OUT_DIR, "sim1000_summary.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    out_bugs = os.path.join(OUT_DIR, "sim1000_bugs.json")
    from collections import defaultdict as dd
    by_code = dd(list)
    for b in bugs:
        by_code[b["code"]].append(b)
    with open(out_bugs, "w", encoding="utf-8") as f:
        json.dump({
            "total": len(bugs),
            "by_code": {
                code: {"count": len(lst), "examples": lst[:3]}
                for code, lst in sorted(by_code.items())
            },
        }, f, indent=2, ensure_ascii=False)

    out_csv = os.path.join(OUT_DIR, "sim1000_games.csv")
    with open(out_csv, "w", encoding="utf-8") as f:
        f.write("game,turns,winner,winner_hp\n")
        for row in per_game_rows:
            f.write(f"{row['game']},{row['turns']},{row['winner']},{row['winner_hp']}\n")

    print(f"\n  Raporlar:")
    print(f"    {out_json}")
    print(f"    {out_bugs}")
    print(f"    {out_csv}")
    print(f"    {LOG_DIR}/strategy_summary.json")
    print(f"    {LOG_DIR}/passive_summary.json")
    print(f"    {LOG_DIR}/passive_efficiency_kpi.jsonl")
    print(f"    {LOG_DIR}/kpi_training.json")
    print(f"    {LOG_DIR}/placement_events.jsonl")
    print(f"    {LOG_DIR}/combat_events.jsonl")
    print(f"    {LOG_DIR}/buy_events.jsonl")
    print(f"    {LOG_DIR}/game_endings.jsonl")


def _print_report():
    print()
    print("=" * 65)
    print("  SONUÇLAR")
    print("=" * 65)

    if all_turns:
        print(f"\n  ▸ Oyun Süresi")
        print(f"    Ort. tur     : {mean(all_turns):.1f}")
        print(f"    Medyan tur   : {median(all_turns):.1f}")
        print(f"    En kısa      : {min(all_turns)}")
        print(f"    En uzun      : {max(all_turns)}")
        print(f"    50-tur limiti: {turn_50_count} oyun ({turn_50_count/N_GAMES*100:.1f}%)")

    expected = 100 / N_PLAYERS
    print(f"\n  ▸ Strateji İstatistikleri  (beklenen: %{expected:.1f})")
    print(f"  {'Strateji':<14} {'Kazan':>6} {'%Win':>6} {'Sapma':>7} "
          f"{'AvgDmg':>8} {'AvgKill':>8} {'AvgHP':>7}")
    print(f"  {'-'*65}")
    for s in sorted(STRATEGIES, key=lambda x: wins[x], reverse=True):
        gp = games_played[s]
        if not gp: continue
        w    = wins[s]
        rate = w / gp * 100
        dev  = rate - expected
        adm  = mean(dmg_by_strat[s])   if dmg_by_strat[s]   else 0
        akl  = mean(kills_by_strat[s]) if kills_by_strat[s] else 0
        ahp  = mean(hp_by_strat[s])    if hp_by_strat[s]    else 0
        flag = (" ◄ DOM"   if rate > expected * 1.7 else
                " ◄ ZAYIF" if rate < expected * 0.5 else "")
        print(f"  {s:<14} {w:>6} {rate:>5.1f}% {dev:>+6.1f}% "
              f"{adm:>8.1f} {akl:>8.1f} {ahp:>7.1f}{flag}")

    print(f"\n  ▸ Bug Özeti")
    print(f"    Toplam crash  : {crash_count}")
    print(f"    Toplam bug    : {len(bugs)}")
    if bugs:
        from collections import Counter
        by_code = Counter(b["code"] for b in bugs)
        by_sev  = Counter(b["sev"] for b in bugs)
        print(f"\n    Önem derecesi:")
        for sev in ("CRITICAL", "WARNING", "INFO"):
            if by_sev[sev]:
                print(f"      {sev:<10}: {by_sev[sev]}")
        print(f"\n    Bug türleri (en sık 10):")
        for code, cnt in by_code.most_common(10):
            print(f"      {code:<30}: {cnt} kez")
    else:
        print(f"    Hiç bug tespit edilmedi!")

    print()
    print("=" * 65)


if __name__ == "__main__":
    main()
