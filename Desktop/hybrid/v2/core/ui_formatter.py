from typing import List, Dict, Any, Tuple, Optional
from v2.core.card_database import CardDatabase, CardData
from v2.core.exceptions import DatabaseError

class UIFormatter:
    """
    Handles UI-specific data transformations and formatting.
    Converts raw domain data to presentation-friendly formats.
    """
    
    @staticmethod
    def format_combat_logs(results: List[Dict], pid: int, turn: int, passive_logs: List[Dict]) -> List[str]:
        lines = []
        # Passive Buff Logs
        for log in passive_logs:
            if log.get("delta", 0) > 0:
                lines.append(f"-> {log.get('trigger', 'Combat').upper()} tetiği ateşledi: +{log['delta']} Puan")

        if not results: return lines

        match = next((r for r in results if r.get("pid_a") == pid or r.get("pid_b") == pid), None)
        if match:
            is_a = match["pid_a"] == pid
            opp_pid = match["pid_b"] if is_a else match["pid_a"]
            my_pts  = match["pts_a"] if is_a else match["pts_b"]
            opp_pts = match["pts_b"] if is_a else match["pts_a"]

            lines.append(f"SEN: Toplam Savaş Puanı = {my_pts}")
            lines.append(f"P{opp_pid}: Toplam Savaş Puanı = {opp_pts}")

            winner_pid = match.get("winner_pid")
            dmg = match.get("dmg", 0)

            if winner_pid not in (-1, pid):
                if turn <= 10: lines.append(f"  (Erken Oyun Sınırı — Tur {turn}: max 15 hasar)")
                if turn <= 5: lines.append(f"  (Tur Penaltısı — Tur {turn}: hasar x0.5 uygulandı)")
                elif turn <= 15:
                    mult = round(0.5 + (turn - 5) * 0.05, 2)
                    lines.append(f"  (Tur Çarpanı — Tur {turn}: hasar x{mult} uygulandı)")

            if match.get("draws", 0) > 0 or my_pts == opp_pts:
                lines.append("SONUÇ: Berabere kalındı!")
            elif winner_pid == pid:
                lines.append(f"SONUÇ: VICTORY! {dmg} Hasar vurdun!")
            else:
                lines.append(f"SONUÇ: DEFEAT! -{dmg} HP Hasar aldın.")
        return lines

    @staticmethod
    def format_rarity_probs(weights_fn, turn: int) -> Dict[str, float]:
        weights = {}
        total_w = 0.0
        for r in ["1", "2", "3", "4", "5"]:
            w = weights_fn(r, turn)
            if not isinstance(w, (int, float)):
                w = 0.0
            weights[r] = w
            total_w += w
        if total_w <= 0: return {"1": 100.0}
        return {r: (w / total_w) * 100.0 for r, w in weights.items()}

    @staticmethod
    def get_card_data_snapshot(card_obj) -> Optional[CardData]:
        if not card_obj:
            return None
        raw_name = getattr(card_obj, "name", card_obj if isinstance(card_obj, str) else None)
        if not raw_name:
            return None
        lookup_name = raw_name.replace("Evolved ", "", 1) if raw_name.startswith("Evolved ") else raw_name
        try:
            base_data = CardDatabase.get().lookup(lookup_name)
        except DatabaseError:
            return None
        if not base_data:
            return None

        return CardData(
            name=raw_name,
            category=base_data.category,
            rarity=str(getattr(card_obj, "rarity", base_data.rarity)),
            stats=dict(getattr(card_obj, "stats", base_data.stats)),
            passive_type=base_data.passive_type,
            passive_effect=base_data.passive_effect,
            synergy_group=base_data.synergy_group
        )
