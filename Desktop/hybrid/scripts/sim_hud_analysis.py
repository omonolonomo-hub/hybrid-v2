"""
sim_hud_analysis.py
====================
HUD tasarım analizi için tek maç, tam verbose simülasyon.

Çalıştır:
    python scripts/sim_hud_analysis.py

Çıktı:
    - Konsola renkli özet
    - output/logs/hud_analysis.txt  (tam log)
"""

import sys
import os
import math
from collections import defaultdict

# ── Proje kökünü sys.path'e ekle ──────────────────────────────────────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from engine_core.card       import get_card_pool
from engine_core.player     import Player
from engine_core.game       import Game
from engine_core.board      import (calculate_group_synergy_bonus,
                                     find_combos, calculate_damage)
from engine_core.constants  import (STRATEGIES, KILL_PTS, STAT_TO_GROUP,
                                     COPY_THRESH, BASE_INCOME,
                                     MAX_INTEREST, INTEREST_STEP)
from engine_core.passive_trigger import (trigger_passive,
                                          get_passive_trigger_log,
                                          clear_passive_trigger_log)

# ── Çıktı klasörü ─────────────────────────────────────────────────────────
OUT_DIR  = os.path.join(ROOT, "output", "logs")
OUT_FILE = os.path.join(OUT_DIR, "hud_analysis.txt")
os.makedirs(OUT_DIR, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════
#  YARDIMCI: group dağılımı özeti
# ══════════════════════════════════════════════════════════════════════════

def board_group_counts(board) -> dict:
    counts = {}
    for card in board.grid.values():
        for grp, n in card.get_group_composition().items():
            counts[grp] = counts.get(grp, 0) + 1
    return counts


def group_bonus_detail(board) -> tuple:
    """(group_bonus, diversity_bonus, total, per_group_dict)"""
    gc = board_group_counts(board)
    per = {}
    group_bonus = 0
    for grp, n in gc.items():
        if n >= 2:
            b = min(18, int(3 * math.pow(n - 1, 1.25)))
            per[grp] = b
            group_bonus += b
        else:
            per[grp] = 0
    unique = len([v for v in gc.values() if v > 0])
    div_bonus = min(5, unique)
    return group_bonus, div_bonus, group_bonus + div_bonus, per


# ══════════════════════════════════════════════════════════════════════════
#  YARDIMCI: gelir hesabı
# ══════════════════════════════════════════════════════════════════════════

def compute_income(player) -> dict:
    base   = BASE_INCOME
    streak = player.win_streak // 3
    hp_bail = (3 if player.hp < 45 else 1 if player.hp < 75 else 0)
    raw_int = min(MAX_INTEREST, player.gold // INTEREST_STEP)
    if player.interest_multiplier > 1.0:
        interest = min(player.interest_cap,
                       int(raw_int * player.interest_multiplier) + 1)
    else:
        interest = raw_int
    return {
        "base": base, "streak": streak,
        "bailout": hp_bail, "interest": interest,
        "total": base + streak + hp_bail + interest,
    }


# ══════════════════════════════════════════════════════════════════════════
#  PER-TURN PROBE — Game.preparation_phase + combat_phase'i wrap'le
# ══════════════════════════════════════════════════════════════════════════

class ProbedGame(Game):
    """Game alt sınıfı: her fazı gözlemler ve per-turn veriyi toplar."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.turn_logs: list[dict] = []   # ana veri yapısı

    # ── Hazırlık fazı ─────────────────────────────────────────────────

    def preparation_phase(self):
        # Board + gelir snapshot'ı HAZIRLIK BAŞLAMADAN önce al
        pre_snap = {}
        for p in self.alive_players():
            gb, db, total, per = group_bonus_detail(p.board)
            combo_pts, _ = find_combos(p.board)
            income_proj  = compute_income(p)
            pre_snap[p.pid] = {
                "gold_before": p.gold,
                "hp":          p.hp,
                "win_streak":  p.win_streak,
                "board_cards": list(p.board.grid.values()),
                "board_count": p.board.alive_count(),
                "group_counts": board_group_counts(p.board),
                "group_bonus":  gb,
                "div_bonus":    db,
                "synergy_total": total,
                "per_group":    per,
                "combo_pts":    combo_pts,
                "income_proj":  income_proj,
            }
        self._pre_snap = pre_snap
        super().preparation_phase()

    # ── Savaş fazı ────────────────────────────────────────────────────

    def combat_phase(self):
        # Savaş öncesi HP
        hp_before = {p.pid: p.hp for p in self.players}

        super().combat_phase()

        # Savaş sonrası veriyi topla
        turn_data = {
            "turn":    self.turn,
            "results": [],
        }

        for res in self.last_combat_results:
            pid_a, pid_b = res["pid_a"], res["pid_b"]
            pa = next((p for p in self.players if p.pid == pid_a), None)
            pb = next((p for p in self.players if p.pid == pid_b), None)

            snap_a = self._pre_snap.get(pid_a, {})
            snap_b = self._pre_snap.get(pid_b, {})

            entry = {
                # Kim oynadı
                "pid_a": pid_a, "strategy_a": pa.strategy if pa else "?",
                "pid_b": pid_b, "strategy_b": pb.strategy if pb else "?",

                # Puan kırılımı
                "kill_a":    res["kill_a"],    "kill_b":    res["kill_b"],
                "combo_a":   res["combo_a"],   "combo_b":   res["combo_b"],
                "synergy_a": res["synergy_a"], "synergy_b": res["synergy_b"],
                "pts_a":     res["pts_a"],     "pts_b":     res["pts_b"],
                "draws":     res["draws"],
                "winner":    res["winner_pid"],
                "dmg":       res["dmg"],

                # HP değişimi
                "hp_before_a": hp_before.get(pid_a, "?"),
                "hp_before_b": hp_before.get(pid_b, "?"),
                "hp_after_a":  res["hp_after_a"],
                "hp_after_b":  res["hp_after_b"],

                # Synergy detayı (hazırlık sonrası board durumu)
                "group_counts_a": snap_a.get("group_counts", {}),
                "per_group_a":    snap_a.get("per_group", {}),
                "div_bonus_a":    snap_a.get("div_bonus", 0),
                "group_counts_b": snap_b.get("group_counts", {}),
                "per_group_b":    snap_b.get("per_group", {}),
                "div_bonus_b":    snap_b.get("div_bonus", 0),

                # Gelir tahmini
                "income_a": snap_a.get("income_proj", {}),
                "income_b": snap_b.get("income_proj", {}),

                # Board güç
                "board_count_a": snap_a.get("board_count", 0),
                "board_count_b": snap_b.get("board_count", 0),
                "board_cards_a": [c.name for c in snap_a.get("board_cards", [])],
                "board_cards_b": [c.name for c in snap_b.get("board_cards", [])],
            }

            # Pasif log — bu tur ateşlenen pasifler
            plog_a = [e for e in (pa.passive_buff_log if pa else [])
                      if e.get("turn") == self.turn]
            plog_b = [e for e in (pb.passive_buff_log if pb else [])
                      if e.get("turn") == self.turn]
            entry["passives_a"] = plog_a
            entry["passives_b"] = plog_b

            turn_data["results"].append(entry)

        self.turn_logs.append(turn_data)


# ══════════════════════════════════════════════════════════════════════════
#  FORMATLI ÇIKTI
# ══════════════════════════════════════════════════════════════════════════

SEP  = "═" * 70
SEP2 = "─" * 70
SEP3 = "┄" * 70

def fmt_group_bar(counts: dict, per: dict) -> str:
    parts = []
    for g in ("MIND", "CONNECTION", "EXISTENCE"):
        n  = counts.get(g, 0)
        bp = per.get(g, 0)
        pip = "●" * n + "○" * max(0, 6 - n)
        parts.append(f"{g[:4]}[{pip}] +{bp}pts")
    return "  ".join(parts)


def fmt_income(inc: dict) -> str:
    return (f"Base:{inc.get('base',3)} "
            f"+Streak:{inc.get('streak',0)} "
            f"+Bail:{inc.get('bailout',0)} "
            f"+Int:{inc.get('interest',0)} "
            f"= +{inc.get('total',3)}G")


def build_report(game: ProbedGame) -> list[str]:
    lines = []
    lines.append(SEP)
    lines.append("  AUTOCHESS HYBRID — HUD TASARIM ANALİZİ  (tek maç, tam verbose)")
    lines.append(f"  {game.turn} tur  |  {len(game.players)} oyuncu")
    lines.append(SEP)

    # ── Tur bazlı detay ───────────────────────────────────────────────
    for td in game.turn_logs:
        tur = td["turn"]
        lines.append(f"\n{SEP2}")
        lines.append(f"  TUR {tur}")
        lines.append(SEP2)

        for e in td["results"]:
            sa = e["strategy_a"]
            sb = e["strategy_b"]
            lines.append(f"\n  [{sa.upper()} P{e['pid_a']}] vs [{sb.upper()} P{e['pid_b']}]")
            lines.append(SEP3)

            # Board durumu
            lines.append(f"  Board A ({e['board_count_a']} kart): "
                         + ", ".join(e["board_cards_a"]) or "boş")
            lines.append(f"  Board B ({e['board_count_b']} kart): "
                         + ", ".join(e["board_cards_b"]) or "boş")

            # Synergy kırılımı
            lines.append(f"\n  ── SYNERGY ──")
            lines.append(f"  A: {fmt_group_bar(e['group_counts_a'], e['per_group_a'])}"
                         f"  Div:+{e['div_bonus_a']}  → TOPLAM +{e['synergy_a']}pts")
            lines.append(f"  B: {fmt_group_bar(e['group_counts_b'], e['per_group_b'])}"
                         f"  Div:+{e['div_bonus_b']}  → TOPLAM +{e['synergy_b']}pts")

            # Puan kırılımı
            lines.append(f"\n  ── PUAN KIRILIMLARI ──")
            lines.append(f"  A: Kill={e['kill_a']:>3}  Combo={e['combo_a']:>3}"
                         f"  Synergy={e['synergy_a']:>3}  TOPLAM={e['pts_a']:>4}")
            lines.append(f"  B: Kill={e['kill_b']:>3}  Combo={e['combo_b']:>3}"
                         f"  Synergy={e['synergy_b']:>3}  TOPLAM={e['pts_b']:>4}")

            # Savaş sonucu
            if e["winner"] == e["pid_a"]:
                w_str = f"P{e['pid_a']} ({sa}) kazandı → P{e['pid_b']} -{e['dmg']} HP"
            elif e["winner"] == e["pid_b"]:
                w_str = f"P{e['pid_b']} ({sb}) kazandı → P{e['pid_a']} -{e['dmg']} HP"
            else:
                w_str = "BERABERE (+1G her ikisine)"
            lines.append(f"\n  ── SONUÇ: {w_str} ──")
            lines.append(f"  HP: A  {e['hp_before_a']} → {e['hp_after_a']}"
                         f"      B  {e['hp_before_b']} → {e['hp_after_b']}")

            # Draws
            if e["draws"] > 0:
                lines.append(f"  Berabere hex sayısı: {e['draws']}")

            # Pasif tetiklemeleri
            all_passives = e["passives_a"] + e["passives_b"]
            if all_passives:
                lines.append(f"\n  ── PASİF TETİKLEMELERİ ({len(all_passives)}) ──")
                for p in all_passives:
                    who = f"P{e['pid_a']}" if p in e["passives_a"] else f"P{e['pid_b']}"
                    delta_str = f"  Δ+{p['delta']}" if p.get("delta", 0) > 0 else ""
                    lines.append(f"  {who} · {p['card']:<32} [{p['passive']}]"
                                 f"  trigger={p['trigger']}{delta_str}")

            # Gelir tahmini
            lines.append(f"\n  ── GELİR TAHMİNİ (savaş sonrası) ──")
            lines.append(f"  A: {fmt_income(e['income_a'])}")
            lines.append(f"  B: {fmt_income(e['income_b'])}")

    # ── Oyun sonu özet tablosu ────────────────────────────────────────
    lines.append(f"\n{SEP}")
    lines.append("  OYUN SONU — OYUNCU ÖZETİ")
    lines.append(SEP)
    lines.append(f"  {'P':>2}  {'Strateji':<14} {'HP':>5} {'TotalPts':>9} "
                 f"{'Kills':>6} {'SynAvg':>8} {'ComboTot':>9} "
                 f"{'Evos':>5} {'Rolls':>6} {'WinStr':>7}")
    lines.append(SEP2)
    for p in sorted(game.players, key=lambda x: x.hp, reverse=True):
        syn_avg = (p.stats["synergy_sum"] / max(1, p.stats["synergy_turns"]))
        lines.append(
            f"  P{p.pid}  {p.strategy:<14} {p.hp:>5} {p.total_pts:>9} "
            f"{p.stats['kills']:>6} {syn_avg:>8.2f} {p.stats['combo_triggers']:>9} "
            f"{p.stats.get('evolutions', 0):>5} "
            f"{p.stats.get('market_rolls', 0):>6} "
            f"{p.stats.get('win_streak_max', 0):>7}"
        )

    # ── Pasif trigger özeti (tüm oyun) ───────────────────────────────
    lines.append(f"\n{SEP}")
    lines.append("  TÜM OYUN PASİF TETİKLEME ÖZETİ")
    lines.append(SEP)
    ptl = get_passive_trigger_log()
    if ptl:
        for card_name in sorted(ptl.keys()):
            triggers = ptl[card_name]
            t_str = "  ".join(f"{t}={n}" for t, n in sorted(triggers.items()))
            lines.append(f"  {card_name:<38} {t_str}")
    else:
        lines.append("  (pasif tetikleme kaydı bulunamadı)")

    # ── HUD tasarım önerileri (değer aralıkları) ─────────────────────
    lines.append(f"\n{SEP}")
    lines.append("  HUD TASARIM VERİSİ — DEĞER ARALIKLARI")
    lines.append(SEP)

    all_syn     = [r["synergy_a"] for td in game.turn_logs for r in td["results"]] + \
                  [r["synergy_b"] for td in game.turn_logs for r in td["results"]]
    all_combo   = [r["combo_a"]   for td in game.turn_logs for r in td["results"]] + \
                  [r["combo_b"]   for td in game.turn_logs for r in td["results"]]
    all_kill    = [r["kill_a"]    for td in game.turn_logs for r in td["results"]] + \
                  [r["kill_b"]    for td in game.turn_logs for r in td["results"]]
    all_pts     = [r["pts_a"]     for td in game.turn_logs for r in td["results"]] + \
                  [r["pts_b"]     for td in game.turn_logs for r in td["results"]]
    all_dmg     = [r["dmg"]       for td in game.turn_logs for r in td["results"]
                   if r["dmg"] > 0]

    def stat(lst, name):
        if not lst:
            return f"  {name}: (veri yok)"
        return (f"  {name:<20} min={min(lst):>4}  max={max(lst):>4}"
                f"  avg={sum(lst)/len(lst):>6.1f}"
                f"  p50={sorted(lst)[len(lst)//2]:>4}")

    lines.append(stat(all_syn,   "Synergy pts/maç"))
    lines.append(stat(all_combo, "Combo pts/maç"))
    lines.append(stat(all_kill,  "Kill pts/maç"))
    lines.append(stat(all_pts,   "Toplam pts/maç"))
    lines.append(stat(all_dmg,   "Hasar/maç"))

    # Group bazlı synergy dağılımı
    group_syn = defaultdict(list)
    for td in game.turn_logs:
        for r in td["results"]:
            for grp, val in r["per_group_a"].items():
                group_syn[grp].append(val)
            for grp, val in r["per_group_b"].items():
                group_syn[grp].append(val)

    lines.append(f"\n  Grup bazlı synergy bonus dağılımı:")
    for grp in ("MIND", "CONNECTION", "EXISTENCE"):
        vals = group_syn.get(grp, [0])
        nonzero = [v for v in vals if v > 0]
        lines.append(f"    {grp:<14} aktif={len(nonzero)}/{len(vals)} maç"
                     f"  max={max(vals)}  avg_aktif="
                     f"{sum(nonzero)/max(1,len(nonzero)):.1f}")

    lines.append(f"\n{SEP}\n")
    return lines


# ══════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════

def main():
    from engine_core.board import combat_phase as cp_fn
    clear_passive_trigger_log()

    pool     = get_card_pool()
    strats   = ["warrior", "builder", "economist", "evolver",
                "balancer", "rare_hunter", "tempo", "random"]
    players  = [Player(pid=i, strategy=s) for i, s in enumerate(strats)]
    game     = ProbedGame(
        players,
        verbose=False,       # ham engine logu istemiyoruz, kendi logumuz var
        rng=__import__("random").Random(42),
        trigger_passive_fn=trigger_passive,
        combat_phase_fn=cp_fn,
        card_pool=pool,
    )

    print("Simülasyon başlatılıyor (seed=42, 8 oyuncu)...")
    winner = game.run()
    print(f"Tamamlandı: {game.turn} tur  |  Kazanan: P{winner.pid} ({winner.strategy})"
          f"  HP={winner.hp}")

    report = build_report(game)

    # Konsol özeti (son 80 satır)
    print("\n" + "\n".join(report[-80:]))

    # Tam log dosyasına yaz
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    print(f"\n>>> Tam log: {OUT_FILE}")


if __name__ == "__main__":
    main()
