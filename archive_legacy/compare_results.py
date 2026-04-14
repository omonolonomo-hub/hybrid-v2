#!/usr/bin/env python3
"""
compare_results.py  —  Builder v2 Before/After karşılaştırması

Kullanım:
  python compare_results.py <before_json> <after_json>

Örnek:
  python compare_results.py output/results/sim1000_summary_BEFORE.json output/results/sim1000_summary.json
"""

import sys, json

BOLD  = "\033[1m"
GRN   = "\033[92m"
RED   = "\033[91m"
YLW   = "\033[93m"
CYN   = "\033[96m"
RST   = "\033[0m"
BAR_W = 28

def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def bar(rate, max_rate=25.0):
    filled = int(rate / max_rate * BAR_W)
    return "█" * filled + "░" * (BAR_W - filled)

def delta_color(d, positive_good=True):
    if abs(d) < 0.1:
        return ""
    if (d > 0) == positive_good:
        return GRN
    return RED

def arrow(d):
    if d > 0.1:  return "▲"
    if d < -0.1: return "▼"
    return "─"

def main():
    if len(sys.argv) < 3:
        print("Kullanım: python compare_results.py <before.json> <after.json>")
        sys.exit(1)

    before = load(sys.argv[1])
    after  = load(sys.argv[2])

    bs  = before["strategies"]
    as_ = after["strategies"]

    expected = 100 / before["config"]["players"]

    print()
    print(f"{BOLD}{'═'*72}{RST}")
    print(f"{BOLD}  BUILDER v2  —  BEFORE vs AFTER  (expected: %{expected:.1f}){RST}")
    print(f"{BOLD}{'═'*72}{RST}")

    # ── Win Rate tablosu ──────────────────────────────────────────
    print(f"\n{BOLD}  WIN RATE KARŞILAŞTIRMASI{RST}")
    print(f"  {'Strateji':<14} {'Before':>7}  {'After':>7}  {'Δ':>7}  Bar (after)")
    print(f"  {'-'*68}")

    strategies = sorted(bs.keys(),
                        key=lambda s: as_.get(s, {}).get("win_rate_pct", 0),
                        reverse=True)

    for s in strategies:
        if s not in as_:
            continue
        b_wr = bs[s]["win_rate_pct"]
        a_wr = as_[s]["win_rate_pct"]
        d_wr = a_wr - b_wr
        clr  = delta_color(d_wr)
        marker = " ◄ HEDEF" if s == "builder" else ""
        print(f"  {s:<14} {b_wr:>6.1f}%  {clr}{a_wr:>6.1f}%{RST}  "
              f"{clr}{arrow(d_wr)}{d_wr:>+5.1f}%{RST}  "
              f"{bar(a_wr)}{marker}")

    # ── Builder odak metrikleri ───────────────────────────────────
    print(f"\n{BOLD}  BUILDER ODAK METRİKLERİ{RST}")
    print(f"  {'Metrik':<22} {'Before':>10}  {'After':>10}  {'Δ':>10}")
    print(f"  {'-'*58}")

    builder_metrics = [
        ("win_rate_pct",   "Win Rate %",        True),
        ("avg_damage",     "Avg Damage",         True),
        ("avg_kills",      "Avg Kills",          True),
        ("avg_final_hp",   "Avg Final HP",       True),
        ("avg_synergy",    "Avg Synergy",        True),
        ("avg_eco_eff",    "Eco Efficiency",     True),
    ]

    bb = bs.get("builder", {})
    ab = as_.get("builder", {})
    for key, label, pos_good in builder_metrics:
        bv = bb.get(key, 0)
        av = ab.get(key, 0)
        dv = av - bv
        clr = delta_color(dv, pos_good)
        unit = "%" if "rate" in key else ""
        print(f"  {label:<22} {bv:>9.2f}{unit}  {clr}{av:>9.2f}{unit}{RST}  "
              f"{clr}{arrow(dv)}{dv:>+8.2f}{RST}")

    # ── Tüm stratejiler detay ─────────────────────────────────────
    print(f"\n{BOLD}  TÜM STRATEJİLER — AVG DAMAGE & KILLS{RST}")
    print(f"  {'Strateji':<14} {'BDmg':>7}  {'ADmg':>7}  {'ΔDmg':>7}  "
          f"{'BKill':>7}  {'AKill':>7}  {'ΔKill':>7}")
    print(f"  {'-'*66}")
    for s in strategies:
        if s not in as_:
            continue
        bd = bs[s]["avg_damage"]
        ad = as_[s]["avg_damage"]
        bk = bs[s]["avg_kills"]
        ak = as_[s]["avg_kills"]
        dd = ad - bd
        dk = ak - bk
        clr_d = delta_color(dd)
        clr_k = delta_color(dk)
        print(f"  {s:<14} {bd:>7.1f}  {ad:>7.1f}  {clr_d}{arrow(dd)}{dd:>+5.1f}{RST}  "
              f"{bk:>7.1f}  {ak:>7.1f}  {clr_k}{arrow(dk)}{dk:>+5.1f}{RST}")

    # ── Meta denge özeti ──────────────────────────────────────────
    print(f"\n{BOLD}  META DENGE{RST}")
    bb_bal = before.get("balance", {})
    ab_bal = after.get("balance", {})

    b_dev = bb_bal.get("max_deviation_pct", 0)
    a_dev = ab_bal.get("max_deviation_pct", 0)
    dev_d = a_dev - b_dev
    clr = delta_color(dev_d, positive_good=False)

    print(f"  {'Max Sapma':<22} {b_dev:>9.2f}%  {clr}{a_dev:>9.2f}%{RST}  "
          f"{clr}{arrow(dev_d)}{dev_d:>+8.2f}%{RST}")
    print(f"  {'Dominant (before)':<22} {bb_bal.get('dominant_strategy','?'):>10}")
    print(f"  {'Dominant (after)':<22} {ab_bal.get('dominant_strategy','?'):>10}")
    print(f"  {'Weakest (before)':<22} {bb_bal.get('weakest_strategy','?'):>10}")
    print(f"  {'Weakest (after)':<22} {ab_bal.get('weakest_strategy','?'):>10}")

    # ── Runtime ───────────────────────────────────────────────────
    print(f"\n{BOLD}  RUNTIME{RST}")
    b_rt = before.get("runtime", {})
    a_rt = after.get("runtime", {})
    print(f"  Before : {b_rt.get('seconds',0):.1f}s  ({b_rt.get('games_per_sec',0):.2f} oyun/s)")
    print(f"  After  : {a_rt.get('seconds',0):.1f}s  ({a_rt.get('games_per_sec',0):.2f} oyun/s)")
    rt_delta = a_rt.get('seconds', 0) - b_rt.get('seconds', 0)
    pct = rt_delta / max(b_rt.get('seconds', 1), 0.001) * 100
    clr = RED if pct > 20 else GRN if pct < -5 else ""
    print(f"  Δ      : {clr}{rt_delta:+.1f}s  ({pct:+.1f}%){RST}")
    if pct > 20:
        print(f"  {YLW}⚠ Lookahead ek maliyet getirdi — optimize edilebilir{RST}")
    elif pct <= 15:
        print(f"  {GRN}✓ Kabul edilebilir overhead{RST}")

    # ── Değerlendirme ─────────────────────────────────────────────
    b_builder_wr = bs.get("builder", {}).get("win_rate_pct", 0)
    a_builder_wr = as_.get("builder", {}).get("win_rate_pct", 0)
    print(f"\n{BOLD}  DEĞERLENDİRME{RST}")
    if a_builder_wr >= 10.0:
        print(f"  {GRN}✓ Hedef aşıldı: Builder %{a_builder_wr:.1f} (hedef ≥10%){RST}")
    elif a_builder_wr >= 6.0:
        print(f"  {YLW}~ Kısmi iyileşme: Builder %{a_builder_wr:.1f} — "
              f"GA tuning ile hedefe ulaşılabilir{RST}")
    elif a_builder_wr > b_builder_wr:
        print(f"  {YLW}~ İyileşme var (%{b_builder_wr:.1f}→%{a_builder_wr:.1f}) "
              f"ama yetersiz — ek tuning gerekli{RST}")
    else:
        print(f"  {RED}✗ Regresyon: %{b_builder_wr:.1f}→%{a_builder_wr:.1f} "
              f"— kodu gözden geçir{RST}")

    print(f"\n{BOLD}{'═'*72}{RST}\n")


if __name__ == "__main__":
    main()
