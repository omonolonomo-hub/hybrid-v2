"""
================================================================
|   AUTOCHESS HYBRID - Strategy Analytics Logger  v2.0        |
|   Passive, combat, economy ve placement tam KPI kaydı        |
================================================================

Üretilen dosyalar (output/strategy_logs/):
  placement_events.jsonl   — her kart yerleşimi
  combat_events.jsonl      — her tur çift bazlı combat sonucu
  buy_events.jsonl         — her kart alımı
  game_endings.jsonl       — oyun sonu özet
  strategy_summary.json    — tüm simülasyon özeti (AI eğitimi için)
  passive_summary.json     — passive etkinlik tablosu
  passive_efficiency_kpi.jsonl — passive etkinlik KPI verileri
  kpi_training.json        — AI eğitimine doğrudan girdi formatı
"""

from __future__ import annotations

import json
import math
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from .game import Game
    from .player import Player
    from .card import Card

# Import KPI_Aggregator for passive efficiency tracking
try:
    from .kpi_aggregator import KPI_Aggregator
except ImportError:
    from kpi_aggregator import KPI_Aggregator

_HEX_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]
CENTER_COORDS: frozenset = frozenset(
    [(0, 0)] + [(dq, dr) for dq, dr in _HEX_DIRS]
)


def is_center(coord: Tuple[int, int]) -> bool:
    return coord in CENTER_COORDS


# ═══════════════════════════════════════════════════════════════════════════════
#  StrategyLogger  v2.0
# ═══════════════════════════════════════════════════════════════════════════════

class StrategyLogger:
    """
    Kapsamlı loglama sistemi.  enabled=True ile tüm KPI grupları aktif.
    enabled=False → tüm metodlar hiçbir şey yapmaz (sıfır overhead).
    """

    _FLUSH = 1000   # buffer büyüklüğü — 1000-oyun simde 500 çok erken flush yapar

    # Ghost-load eşiği: abs(delta) < bu değerin altındaki passive çağrıları
    # hem delta == 0 hemde floating-point artıklarını (1e-15 gibi) filtreler.
    _DELTA_THRESH = 0.01

    def __init__(self, enabled: bool = True,
                 output_dir: str = "output/strategy_logs",
                 verbose_passive: bool = False):
        self.enabled = enabled
        self.verbose_passive = verbose_passive   # JSONL passive event yazımı (yavaş)
        self.output_dir = Path(output_dir)

        # Canlı state
        self._game_id: Optional[int] = None
        self._turn: int = 0

        # Per-game tamponlar
        self._placement_buf: List[dict] = []
        self._combat_buf: List[dict] = []
        self._buy_buf: List[dict] = []
        self._game_buf: List[dict] = []

        # KPI Aggregator for passive efficiency tracking
        self._kpi_aggregator = KPI_Aggregator()

        # ── Özet istatistikler ──────────────────────────────────────────────
        # Strateji bazlı
        def _new_strat():
            return {
                "wins": 0, "total_games": 0, "turn_sum": 0,
                "center_sum": 0, "rim_sum": 0,
                "power_sum": 0.0, "combo_sum": 0.0, "placement_count": 0,
                "rarity_seen": Counter(),
                # combat
                "kill_sum": 0, "combat_wins": 0, "combat_losses": 0,
                "combat_draws": 0, "combat_total": 0,
                "damage_dealt_sum": 0,
                # economy
                "gold_earned_sum": 0, "gold_spent_sum": 0,
                "cards_bought_sum": 0,
                # passive
                "passive_triggers": Counter(),   # trigger_type → count
                "passive_delta_sum": 0,          # toplam güçlenme
                # son pozisyon HP
                "hp_sum": 0,
                # snowball
                "snowball_turns": [],
            }
        self._strat: Dict[str, dict] = defaultdict(_new_strat)

        # Passive bazlı (card_name → trigger → count / delta)
        self._passive_card: Dict[str, dict] = defaultdict(lambda: {
            "triggers": Counter(),
            "delta_sum": 0,
            "strategies_using": Counter(),
        })

        if self.enabled:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            for fname in ("placement_events.jsonl", "combat_events.jsonl",
                          "buy_events.jsonl",
                          "game_endings.jsonl"):
                p = self.output_dir / fname
                if p.exists():
                    p.unlink()

    # ── Oyun yaşam döngüsü ───────────────────────────────────────────────────

    def begin_game(self, game_id: int):
        if not self.enabled:
            return
        self._game_id = game_id
        self._turn = 0

    def set_turn(self, turn: int):
        if not self.enabled:
            return
        self._turn = turn

    # ── Placement ────────────────────────────────────────────────────────────

    def log_placement(self, player: "Player", card: "Card",
                      hex_coord: Tuple[int, int], combo_score: int):
        if not self.enabled:
            return
        center = is_center(hex_coord)
        ev = {
            "game_id": self._game_id, "turn": self._turn,
            "player": player.strategy,
            "card": card.name, "rarity": card.rarity,
            "power": card.total_power(),
            "hex": list(hex_coord), "center": center,
            "combo_score": combo_score,
        }
        self._placement_buf.append(ev)
        s = self._strat[player.strategy]
        s["center_sum"] += int(center)
        s["rim_sum"] += int(not center)
        s["power_sum"] += card.total_power()
        s["combo_sum"] += combo_score
        s["placement_count"] += 1
        s["rarity_seen"][card.rarity] += 1
        if len(self._placement_buf) >= self._FLUSH:
            self._write("placement_events.jsonl", self._placement_buf)

    # ── Satın alma ───────────────────────────────────────────────────────────

    def log_buy(self, player: "Player", card: "Card", gold_before: int):
        if not self.enabled:
            return
        ev = {
            "game_id": self._game_id, "turn": self._turn,
            "player": player.strategy,
            "card": card.name, "rarity": card.rarity,
            "power": card.total_power(),
            "cost": gold_before - player.gold,
            "gold_after": player.gold,
        }
        self._buy_buf.append(ev)
        s = self._strat[player.strategy]
        s["cards_bought_sum"] += 1
        s["gold_spent_sum"] += ev["cost"]
        if len(self._buy_buf) >= self._FLUSH:
            self._write("buy_events.jsonl", self._buy_buf)

    # ── Combat ───────────────────────────────────────────────────────────────

    def log_combat(self, player_a: "Player", player_b: "Player",
                   pts_a: int, pts_b: int,
                   kill_a: int, kill_b: int,
                   combo_a: int, combo_b: int,
                   synergy_a: int, synergy_b: int,
                   winner_pid: int, dmg: int, draws: int):
        """game.py combat_phase içinde her çift için çağır."""
        if not self.enabled:
            return
        ev = {
            "game_id": self._game_id, "turn": self._turn,
            "strat_a": player_a.strategy, "strat_b": player_b.strategy,
            "pts_a": pts_a, "pts_b": pts_b,
            "kill_a": kill_a, "kill_b": kill_b,
            "combo_a": combo_a, "combo_b": combo_b,
            "synergy_a": synergy_a, "synergy_b": synergy_b,
            "winner": "a" if winner_pid == player_a.pid
                      else ("b" if winner_pid == player_b.pid else "draw"),
            "dmg": dmg, "draws": draws,
        }
        self._combat_buf.append(ev)

        # Özet güncelle
        for p, kill, pts_self, pts_opp in [
            (player_a, kill_a, pts_a, pts_b),
            (player_b, kill_b, pts_b, pts_a),
        ]:
            s = self._strat[p.strategy]
            s["kill_sum"] += kill
            s["damage_dealt_sum"] += dmg if (
                (p is player_a and winner_pid == player_a.pid) or
                (p is player_b and winner_pid == player_b.pid)
            ) else 0
            s["combat_total"] += 1
            if winner_pid == p.pid:
                s["combat_wins"] += 1
            elif winner_pid == -1:
                s["combat_draws"] += 1
            else:
                s["combat_losses"] += 1

        if len(self._combat_buf) >= self._FLUSH:
            self._write("combat_events.jsonl", self._combat_buf)

    # ── Passive ──────────────────────────────────────────────────────────────

    def log_passive(self, card_name: str, passive_type: str,
                    trigger: str, owner_strategy: str,
                    delta: int, ctx_turn: int):
        """passive_trigger.py içinde her tetiklenme sonrası çağır.

        Performans optimizasyonları (235k+ tetiklenme senaryosu için):
          1. abs(delta) < _DELTA_THRESH: hem delta==0 hem float artıklarını (1e-15)
             tek seferde keser — dict update milyonlarca gereksiz döngüden kurtulur.
          2. Yerel değişken cache: tekrarlı nested dict erişimi (~4x) önlenir.
          3. verbose_passive=False (default): JSONL buffer hiç doldurulmaz;
             sadece sayaç ve delta_sum güncellenir ("summary-only" mod).
        """
        if not self.enabled:
            return

        # ── 1. Ghost-load filtresi ──────────────────────────────────
        if abs(delta) < self._DELTA_THRESH:
            return

        # ── 2. Yerel cache — nested dict erişimini minimuma indir ───
        s  = self._strat[owner_strategy]
        pc = self._passive_card[card_name]

        # Strateji özeti
        s_triggers = s["passive_triggers"]
        s_triggers[trigger] += 1
        s["passive_delta_sum"] += delta

        # Kart özeti
        pc_triggers = pc["triggers"]
        pc_triggers[trigger] += 1
        pc["delta_sum"] += delta
        pc["strategies_using"][owner_strategy] += 1

    # ── Market logging ───────────────────────────────────────────────────────

    def log_market_window(self, player: "Player", turn: int,
                          available_cards: List["Card"]):
        if not self.enabled:
            return
        rc = Counter(c.rarity for c in available_cards)
        self._strat[player.strategy]["rarity_seen"].update(rc)

    # ── Oyun sonu ────────────────────────────────────────────────────────────

    def end_game(self, game: "Game", winner: "Player"):
        if not self.enabled:
            return

        # Oyuncu bazlı son durum snapshotı
        player_snapshot = {}
        for p in game.players:
            alive_cards = list(p.board.grid.values())
            player_snapshot[p.strategy] = {
                "hp": p.hp,
                "gold": p.gold,
                "board_cards": len(alive_cards),
                "board_power": sum(c.total_power() for c in alive_cards),
                "kills": p.stats.get("kills", 0),
                "damage_dealt": p.stats.get("damage_dealt", 0),
                "wins": p.stats.get("wins", 0),
                "losses": p.stats.get("losses", 0),
                "draws": p.stats.get("draws", 0),
                "gold_earned": p.stats.get("gold_earned", 0),
                "gold_spent": p.stats.get("gold_spent", 0),
                "combo_triggers": p.stats.get("combo_triggers", 0),
                "synergy_sum": p.stats.get("synergy_sum", 0),
                "win_streak_max": p.stats.get("win_streak_max", 0),
                "evolutions": p.stats.get("evolutions", 0),
                "copies_created": p.stats.get("copies_created", 0),
                "passive_buff_count": len(p.passive_buff_log),
            }
            # Özet güncelle
            s = self._strat[p.strategy]
            s["total_games"] += 1
            s["turn_sum"] += game.turn
            s["hp_sum"] += p.hp
            s["gold_earned_sum"] += p.stats.get("gold_earned", 0)

        self._strat[winner.strategy]["wins"] += 1
        self._strat[winner.strategy]["snowball_turns"].append(game.turn)

        rec = {
            "game_id": self._game_id,
            "turns": game.turn,
            "winner": winner.strategy,
            "winner_hp": winner.hp,
            "players": player_snapshot,
        }
        self._game_buf.append(rec)
        if len(self._game_buf) >= self._FLUSH:
            self._write("game_endings.jsonl", self._game_buf)

        # Aggregate passive efficiency data for each player
        for player in game.players:
            try:
                game_won = (player.pid == winner.pid)
                self._kpi_aggregator.aggregate_passive_buff_log(
                    player, self._game_id, game_won
                )
            except Exception as e:
                print(f"Warning: Error aggregating passive data for player {player.pid}: {e}")
                continue

    # ── Flush & özet ────────────────────────────────────────────────────────

    def flush(self):
        if not self.enabled:
            return
        self._write("placement_events.jsonl", self._placement_buf)
        self._write("combat_events.jsonl", self._combat_buf)
        self._write("buy_events.jsonl", self._buy_buf)
        self._write("game_endings.jsonl", self._game_buf)
        self._write_strategy_summary()
        self._write_passive_summary()
        self._write_kpi_training()
        self._write_passive_efficiency_kpi()

    def _write(self, fname: str, buf: List[dict]):
        if not buf:
            return
        path = self.output_dir / fname
        with open(path, "a", encoding="utf-8") as f:
            for rec in buf:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        buf.clear()

    # ── strategy_summary.json ────────────────────────────────────────────────

    def _write_strategy_summary(self):
        rows = []
        for strat, s in sorted(self._strat.items()):
            n  = max(1, s["total_games"])
            pc = max(1, s["placement_count"])
            ct = max(1, s["combat_total"])
            rows.append({
                "strategy": strat,
                "total_games": n,
                "win_rate": round(s["wins"] / n, 4),
                # placement
                "avg_turns": round(s["turn_sum"] / n, 2),
                "avg_center_per_game": round(s["center_sum"] / n, 2),
                "avg_rim_per_game":    round(s["rim_sum"] / n, 2),
                "center_ratio":        round(s["center_sum"] / max(1, s["center_sum"] + s["rim_sum"]), 3),
                "avg_power_per_card":  round(s["power_sum"] / pc, 2),
                "avg_combo_per_placement": round(s["combo_sum"] / pc, 3),
                # combat
                "avg_kills_per_game":   round(s["kill_sum"] / n, 2),
                "combat_win_rate":      round(s["combat_wins"] / ct, 3),
                "combat_draw_rate":     round(s["combat_draws"] / ct, 3),
                "avg_damage_per_game":  round(s["damage_dealt_sum"] / n, 2),
                # economy
                "avg_gold_earned": round(s["gold_earned_sum"] / n, 2),
                "avg_gold_spent":  round(s["gold_spent_sum"] / n, 2),
                "avg_cards_bought": round(s["cards_bought_sum"] / n, 2),
                # passive
                "passive_triggers_per_game": {
                    t: round(c / n, 3)
                    for t, c in s["passive_triggers"].most_common(10)
                },
                "avg_passive_delta_per_game": round(s["passive_delta_sum"] / n, 2),
                # HP
                "avg_final_hp": round(s["hp_sum"] / n, 2),
                # rarity
                "rarity_seen": dict(s["rarity_seen"]),
                # snowball
                "snowball_avg_turn": (
                    round(sum(s["snowball_turns"]) / len(s["snowball_turns"]), 1)
                    if s["snowball_turns"] else None
                ),
            })
        path = self.output_dir / "strategy_summary.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)

    # ── passive_summary.json ─────────────────────────────────────────────────

    def _write_passive_summary(self):
        """Hangi passive ne kadar tetikleniyor, ne kadar güç kazandırıyor."""
        rows = []
        for card_name, d in sorted(
            self._passive_card.items(),
            key=lambda x: -sum(x[1]["triggers"].values())
        ):
            total_triggers = sum(d["triggers"].values())
            rows.append({
                "card": card_name,
                "total_triggers": total_triggers,
                "triggers_by_type": dict(d["triggers"].most_common()),
                "total_delta": d["delta_sum"],
                "avg_delta_per_trigger": round(
                    d["delta_sum"] / max(1, total_triggers), 3),
                "strategies_using": dict(d["strategies_using"].most_common()),
            })
        
        # Add metadata referencing detailed KPI file
        summary_data = {
            "_metadata": {
                "description": "Aggregated passive trigger statistics across all games",
                "detailed_kpi_file": "passive_efficiency_kpi.jsonl",
                "note": "For per-game passive efficiency metrics including normalized values and win rate correlation, see passive_efficiency_kpi.jsonl"
            },
            "passive_cards": rows
        }
        
        path = self.output_dir / "passive_summary.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)

    # ── kpi_training.json — AI eğitim formatı ────────────────────────────────

    def _write_kpi_training(self):
        """
        Her strateji için normalized KPI vektörü.
        Format: {strategy: {feature_name: float, ...}}
        Doğrudan train_strategies.py veya bir ML pipeline'ına beslenebilir.

        KPI grupları:
          G1 — Placement verimliliği
          G2 — Combat etkinliği
          G3 — Economy yönetimi
          G4 — Passive sinerji
          G5 — Snowball / tempo
          G6 — Kart kalitesi
        """
        result = {}
        for strat, s in self._strat.items():
            n  = max(1, s["total_games"])
            pc = max(1, s["placement_count"])
            ct = max(1, s["combat_total"])
            result[strat] = {
                # G1 — Placement
                "g1_center_ratio":          round(s["center_sum"] / max(1, s["center_sum"] + s["rim_sum"]), 4),
                "g1_avg_combo_per_place":   round(s["combo_sum"] / pc, 4),
                "g1_placements_per_game":   round(s["placement_count"] / n, 2),
                # G2 — Combat
                "g2_combat_win_rate":       round(s["combat_wins"] / ct, 4),
                "g2_avg_kills_per_game":    round(s["kill_sum"] / n, 4),
                "g2_avg_damage_per_game":   round(s["damage_dealt_sum"] / n, 4),
                "g2_draw_rate":             round(s["combat_draws"] / ct, 4),
                # G3 — Economy
                "g3_avg_gold_earned":       round(s["gold_earned_sum"] / n, 4),
                "g3_avg_gold_spent":        round(s["gold_spent_sum"] / n, 4),
                "g3_gold_efficiency":       round(
                    s["gold_spent_sum"] / max(1, s["gold_earned_sum"]), 4),
                "g3_avg_cards_per_game":    round(s["cards_bought_sum"] / n, 4),
                # G4 — Passive
                "g4_passive_triggers_per_game": round(
                    sum(s["passive_triggers"].values()) / n, 4),
                "g4_passive_delta_per_game": round(s["passive_delta_sum"] / n, 4),
                # G5 — Snowball / tempo
                "g5_win_rate":              round(s["wins"] / n, 4),
                "g5_avg_win_turn":          round(
                    sum(s["snowball_turns"]) / max(1, len(s["snowball_turns"])), 4),
                "g5_avg_final_hp":          round(s["hp_sum"] / n, 4),
                # G6 — Kart kalitesi
                "g6_avg_power_per_card":    round(s["power_sum"] / pc, 4),
                "g6_r4r5_ratio":            round(
                    (s["rarity_seen"].get("4", 0) + s["rarity_seen"].get("5", 0)) /
                    max(1, sum(s["rarity_seen"].values())), 4),
            }
        path = self.output_dir / "kpi_training.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    # ── passive_efficiency_kpi.jsonl ─────────────────────────────────────────

    def _write_passive_efficiency_kpi(self):
        """
        Generate passive_efficiency_kpi.jsonl with aggregated passive efficiency data.
        Pure I/O operation: Get data from KPI_Aggregator and write to file.
        """
        if not self.enabled:
            return
        
        try:
            path = self.output_dir / "passive_efficiency_kpi.jsonl"
            records = self._kpi_aggregator.get_kpi_records()
            
            with open(path, "w", encoding="utf-8") as f:
                for record in records:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except IOError as e:
            print(f"Warning: Failed to write passive_efficiency_kpi.jsonl: {e}")
        except Exception as e:
            print(f"Warning: Unexpected error in passive KPI generation: {e}")

    # ── Konsol özet ─────────────────────────────────────────────────────────

    def print_summary(self, n_games: int = None):
        if not self.enabled:
            return

        print(f"\n{'═'*78}")
        print("  STRATEGY ANALYTICS v2.0 — Tam KPI Raporu")
        print(f"{'═'*78}")

        header = (f"  {'Strategy':<14} {'WinRate':>7} {'CmboPl':>7} "
                  f"{'CombatWR':>9} {'AvgKill':>8} {'GoldEff':>8} "
                  f"{'PsvDelta':>9} {'AvgHP':>7}")
        print(header)
        print(f"  {'-'*72}")

        for strat, s in sorted(
            self._strat.items(),
            key=lambda x: x[1]["wins"] / max(1, x[1]["total_games"]),
            reverse=True
        ):
            n  = max(1, s["total_games"])
            pc = max(1, s["placement_count"])
            ct = max(1, s["combat_total"])
            wr  = s["wins"] / n
            cpl = s["combo_sum"] / pc
            cwr = s["combat_wins"] / ct
            akl = s["kill_sum"] / n
            ge  = s["gold_spent_sum"] / max(1, s["gold_earned_sum"])
            pd  = s["passive_delta_sum"] / n
            hp  = s["hp_sum"] / n
            print(f"  {strat:<14} {wr:>6.1%} {cpl:>7.3f} "
                  f"{cwr:>9.1%} {akl:>8.1f} {ge:>8.2f} "
                  f"{pd:>9.2f} {hp:>7.1f}")

        print(f"\n  En çok tetiklenen 10 passive:")
        top10 = sorted(
            self._passive_card.items(),
            key=lambda x: -sum(x[1]["triggers"].values())
        )[:10]
        for card_name, d in top10:
            total = sum(d["triggers"].values())
            top_trig = d["triggers"].most_common(3)
            tstr = ", ".join(f"{t}:{c}" for t, c in top_trig)
            print(f"    {card_name:<28} total={total:>6}  [{tstr}]  delta={d['delta_sum']:+}")

        print(f"\n  Dosyalar: {self.output_dir}/")
        print(f"{'═'*78}\n")


# ═══════════════════════════════════════════════════════════════════════════════
#  Global singleton
# ═══════════════════════════════════════════════════════════════════════════════

_global_strategy_logger: Optional[StrategyLogger] = None


def init_strategy_logger(enabled: bool = True,
                         output_dir: str = "output/strategy_logs") -> StrategyLogger:
    global _global_strategy_logger
    _global_strategy_logger = StrategyLogger(enabled=enabled,
                                              output_dir=output_dir)
    return _global_strategy_logger


def get_strategy_logger() -> Optional[StrategyLogger]:
    return _global_strategy_logger
