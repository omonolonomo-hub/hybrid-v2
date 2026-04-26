#!/usr/bin/env python3
"""
================================================================
  AUTOCHESS HYBRID — Strategy Analytics Viewer
  Kullanım:
      python analyze_strategies.py
      python analyze_strategies.py --plot      ← grafik de göster (matplotlib gerekli)
  
  Önce simülasyonu analytics modunda çalıştır:
      python sim1000.py --analytics
================================================================
"""

import sys, os, json
from collections import defaultdict
from pathlib import Path

ROOT     = os.path.dirname(os.path.abspath(__file__))
LOG_DIR  = Path(ROOT) / "output" / "strategy_logs"
SHOW_PLOT = "--plot" in sys.argv

# ── Renk sabitleri (terminal) ─────────────────────────────────
RED    = "\033[91m"
YLW    = "\033[93m"
GRN    = "\033[92m"
CYN    = "\033[96m"
BLD    = "\033[1m"
RST    = "\033[0m"

def _color(val, lo, hi):
    """val yüksekse kırmızı (dominant), düşükse yeşil (zayıf)."""
    if val >= hi: return RED + BLD
    if val <= lo: return GRN
    return ""


def load_jsonl(path: Path):
    if not path.exists():
        return []
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def load_json(path: Path):
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ════════════════════════════════════════════════════════════════
#  1. Strategy Summary (JSON özet)
# ════════════════════════════════════════════════════════════════

def print_strategy_summary():
    data = load_json(LOG_DIR / "strategy_summary.json")
    if not data:
        print(f"{YLW}  strategy_summary.json bulunamadı.{RST}")
        print(f"  Önce:  python sim1000.py --analytics")
        return

    print(f"\n{BLD}{'═'*76}{RST}")
    print(f"{BLD}  STRATEGY ANALYTICS — Snowball & Placement Dominance{RST}")
    print(f"{BLD}{'═'*76}{RST}")

    # ── Win Rate tablosu ──────────────────────────────────────────────────────
    print(f"\n{BLD}  WİN RATE & SNOWBALL HIZI{RST}")
    print(f"  {'Strateji':<14} {'WinRate':>8} {'Kazanılan tur ort':>18} {'AvgTur':>8}   Bar")
    print(f"  {'-'*72}")

    sorted_data = sorted(data, key=lambda x: x["win_rate"], reverse=True)
    max_wr = max(x["win_rate"] for x in data) if data else 1

    for row in sorted_data:
        s  = row["strategy"]
        wr = row["win_rate"]
        at = row["avg_turns"]
        sb = row.get("snowball_avg_turn")
        sb_str = f"{sb:>5.1f}" if sb else "  N/A"
        bar_len = int(wr / max(max_wr, 0.01) * 24)
        bar = "█" * bar_len
        clr = _color(wr, 0.08, 0.20)
        print(f"  {clr}{s:<14}{RST} {wr:>7.1%} {sb_str:>18} {at:>8.1f}   {clr}{bar}{RST}")

    # ── Placement Dominance tablosu ───────────────────────────────────────────
    print(f"\n{BLD}  PLACEMENT DOMINANCE (center vs rim){RST}")
    print(f"  {'Strateji':<14} {'CenterOrt':>10} {'RimOrt':>8} {'CtrRatio':>10} {'AvgPow':>8} {'AvgCombo':>10}")
    print(f"  {'-'*72}")

    max_cr = max(x.get("center_ratio", 0) for x in data) if data else 1
    for row in sorted(data, key=lambda x: x.get("center_ratio", 0), reverse=True):
        s  = row["strategy"]
        cc = row.get("avg_center_per_game", 0)
        rc = row.get("avg_rim_per_game", 0)
        cr = row.get("center_ratio", 0)
        ap = row.get("avg_power_per_card", 0)
        ac = row.get("avg_combo_per_placement", 0)
        clr = _color(cr, 0.25, 0.55)
        print(f"  {s:<14} {cc:>10.1f} {rc:>8.1f} {clr}{cr:>9.1%}{RST} {ap:>8.1f} {ac:>10.3f}")

    # ── Dead Board & Rarity ───────────────────────────────────────────────────
    print(f"\n{BLD}  DEAD BOARD & RARITY ADVANTAGE{RST}")
    print(f"  {'Strateji':<14} {'DeadBrd':>8}   Rarity dağılımı (görülen)")
    print(f"  {'-'*72}")

    for row in sorted(data, key=lambda x: x.get("avg_dead_board", 0), reverse=True):
        s  = row["strategy"]
        db = row.get("avg_dead_board", 0)
        rc = row.get("rarity_seen", {})
        rstr = "  ".join(f"r{k}={v}" for k, v in sorted(rc.items()))
        clr_db = _color(db, 0, 2)
        print(f"  {s:<14} {clr_db}{db:>8.2f}{RST}   {rstr}")

    print()


# ════════════════════════════════════════════════════════════════
#  2. Game Endings — turn & board state analizi
# ════════════════════════════════════════════════════════════════

def analyze_game_endings():
    records = load_jsonl(LOG_DIR / "game_endings.jsonl")
    if not records:
        print(f"{YLW}  game_endings.jsonl bulunamadı veya boş.{RST}\n")
        return

    n = len(records)
    wins_by = defaultdict(int)
    turn_sum = defaultdict(float)
    center_sum = defaultdict(float)
    combo_sum = defaultdict(float)
    dead_sum = defaultdict(float)
    games_count = defaultdict(int)  # her stratejinin oynadığı oyun sayısı

    for rec in records:
        winner = rec.get("winner", "?")
        turns  = rec.get("turns", 0)
        wins_by[winner] += 1
        turn_sum[winner] += turns

        board = rec.get("board", {})
        for strat, bdata in board.items():
            center_sum[strat] += bdata.get("center", 0)
            games_count[strat] += 1

        combo = rec.get("combo_score", {})
        for strat, cs in combo.items():
            combo_sum[strat] += cs

        dead = rec.get("dead_board_warnings", {})
        for strat, dc in dead.items():
            dead_sum[strat] += dc

    print(f"{BLD}  GAME ENDINGS ÖZETİ  ({n} oyun){RST}")
    print(f"  {'Strateji':<14} {'Kazandı':>8} {'%Win':>7} {'AvgWinTur':>11} {'AvgCenter':>11} {'AvgCombo':>10}")
    print(f"  {'-'*68}")

    for strat in sorted(wins_by, key=lambda s: wins_by[s], reverse=True):
        w   = wins_by[strat]
        wr  = w / n
        awt = turn_sum[strat] / max(1, w)
        gc  = max(1, games_count[strat])
        ac  = center_sum[strat] / gc
        cs  = combo_sum[strat] / gc
        clr = _color(wr, 0.08, 0.20)
        print(f"  {clr}{strat:<14}{RST} {w:>8} {clr}{wr:>6.1%}{RST} {awt:>11.1f} {ac:>11.2f} {cs:>10.2f}")
    print()


# ════════════════════════════════════════════════════════════════
#  3. Placement Events — per-strateji derinlik analizi
# ════════════════════════════════════════════════════════════════

def analyze_placements():
    records = load_jsonl(LOG_DIR / "placement_events.jsonl")
    if not records:
        print(f"{YLW}  placement_events.jsonl bulunamadı veya boş.{RST}\n")
        return

    strat_data = defaultdict(lambda: {
        "center": 0, "rim": 0,
        "combo_sum": 0.0, "power_sum": 0.0,
        "count": 0,
        "rarity_dist": defaultdict(int),
    })

    for ev in records:
        s   = ev.get("player", "?")
        d   = strat_data[s]
        d["count"] += 1
        d["power_sum"]  += ev.get("power", 0)
        d["combo_sum"]  += ev.get("combo_score", 0)
        d["rarity_dist"][ev.get("rarity", "?")] += 1
        if ev.get("center"):
            d["center"] += 1
        else:
            d["rim"] += 1

    print(f"{BLD}  PLACEMENT EVENT ANALİZİ  ({len(records)} event){RST}")
    print(f"  {'Strateji':<14} {'Count':>7} {'Center%':>8} {'AvgPow':>8} {'AvgCombo':>10}  Rarity dağılımı")
    print(f"  {'-'*78}")

    for strat, d in sorted(strat_data.items(),
                            key=lambda x: x[1]["center"] / max(1, x[1]["count"]),
                            reverse=True):
        cnt = d["count"]
        cr  = d["center"] / max(1, cnt)
        ap  = d["power_sum"] / max(1, cnt)
        ac  = d["combo_sum"] / max(1, cnt)
        rd  = "  ".join(f"r{k}={v}" for k, v in sorted(d["rarity_dist"].items()))
        clr = _color(cr, 0.25, 0.55)
        print(f"  {strat:<14} {cnt:>7} {clr}{cr:>7.1%}{RST} {ap:>8.1f} {ac:>10.3f}  {rd}")
    print()


# ════════════════════════════════════════════════════════════════
#  4. Market Events — early access analizi
# ════════════════════════════════════════════════════════════════

def analyze_market():
    records = load_jsonl(LOG_DIR / "market_events.jsonl")
    if not records:
        print(f"{YLW}  market_events.jsonl bulunamadı veya boş.{RST}\n")
        return

    # Turn aralıklarına göre rarity görüntüleme
    BUCKETS = [(1, 5, "early"), (6, 15, "mid"), (16, 99, "late")]
    strat_bucket = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    # strat_bucket[strat][bucket_name][rarity] = count

    for ev in records:
        s    = ev.get("player", "?")
        turn = ev.get("turn", 0)
        rc   = ev.get("rarity_counts", {})
        for lo, hi, label in BUCKETS:
            if lo <= turn <= hi:
                for rar, cnt in rc.items():
                    strat_bucket[s][label][rar] += cnt
                break

    print(f"{BLD}  MARKET WINDOW ANALİZİ — Rarity Görme Oranı / Dönem{RST}")
    for lo, hi, label in BUCKETS:
        print(f"\n  ── {label.upper()} (turn {lo}-{hi}) ──")
        print(f"  {'Strateji':<14}  r1     r2     r3     r4     r5")
        print(f"  {'-'*55}")
        for strat in sorted(strat_bucket.keys()):
            bkt = strat_bucket[strat][label]
            total = max(1, sum(bkt.values()))
            cells = " ".join(f"{bkt.get(str(r), 0)/total:>5.1%}" for r in range(1, 6))
            print(f"  {strat:<14}  {cells}")
    print()


# ════════════════════════════════════════════════════════════════
#  5. Opsiyonel: matplotlib görselleştirme
# ════════════════════════════════════════════════════════════════

def plot_if_available():
    if not SHOW_PLOT:
        return
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        print(f"{YLW}  matplotlib bulunamadı. Grafik atlanıyor.{RST}")
        print(f"  Kurmak için:  pip install matplotlib")
        return

    data = load_json(LOG_DIR / "strategy_summary.json")
    if not data:
        return

    strategies = [r["strategy"] for r in data]
    win_rates  = [r["win_rate"] for r in data]
    center_r   = [r.get("center_ratio", 0) for r in data]
    avg_combo  = [r.get("avg_combo_per_placement", 0) for r in data]
    dead_board = [r.get("avg_dead_board", 0) for r in data]

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle("Autochess Hybrid — Strategy Analytics", fontsize=14, fontweight="bold")

    colors = plt.cm.tab10.colors

    # ── Win Rate ──────────────────────────────────────────────
    ax = axes[0, 0]
    bars = ax.bar(strategies, win_rates, color=colors[:len(strategies)])
    ax.axhline(1 / len(strategies), color="red", linestyle="--", alpha=0.7, label="Beklenen")
    ax.set_title("Win Rate")
    ax.set_ylabel("Oran")
    ax.set_ylim(0, max(win_rates) * 1.3)
    ax.legend()
    for bar, v in zip(bars, win_rates):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.003,
                f"{v:.1%}", ha="center", va="bottom", fontsize=8)
    ax.tick_params(axis="x", rotation=30)

    # ── Center Ratio ─────────────────────────────────────────
    ax = axes[0, 1]
    ax.bar(strategies, center_r, color=colors[:len(strategies)])
    ax.set_title("Center Placement Ratio")
    ax.set_ylabel("Center / Toplam placement")
    ax.set_ylim(0, 1)
    ax.tick_params(axis="x", rotation=30)

    # ── Avg Combo per Placement ──────────────────────────────
    ax = axes[1, 0]
    ax.bar(strategies, avg_combo, color=colors[:len(strategies)])
    ax.set_title("Avg Combo Score per Placement")
    ax.set_ylabel("Combo Score")
    ax.tick_params(axis="x", rotation=30)

    # ── Dead Board Ort. ──────────────────────────────────────
    ax = axes[1, 1]
    ax.bar(strategies, dead_board, color=colors[:len(strategies)])
    ax.set_title("Avg Dead Board Warnings / Game")
    ax.set_ylabel("Overflow (kart düşürme) sayısı")
    ax.tick_params(axis="x", rotation=30)

    plt.tight_layout()
    out = Path(ROOT) / "output" / "strategy_logs" / "strategy_analytics.png"
    plt.savefig(out, dpi=150)
    print(f"\n  Grafik kaydedildi: {out}")
    plt.show()


# ════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if not LOG_DIR.exists():
        print(f"\n{YLW}  Log dizini bulunamadı: {LOG_DIR}{RST}")
        print(f"  Önce simülasyonu analytics modunda çalıştır:")
        print(f"      python sim1000.py --analytics\n")
        sys.exit(1)

    print_strategy_summary()
    analyze_game_endings()
    analyze_placements()
    analyze_market()
    plot_if_available()

    print(f"  Log dosyaları: {LOG_DIR}\n")
