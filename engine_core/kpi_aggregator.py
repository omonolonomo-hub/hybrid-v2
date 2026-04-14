"""
KPI Aggregator Module

Handles passive efficiency data aggregation and computation logic.
Separated from StrategyLogger to maintain single responsibility principle.
"""

from typing import Dict, List, Tuple, Any


class KPI_Aggregator:
    """
    Aggregates passive efficiency data from Player.passive_buff_log.
    Handles all computation logic without file I/O.
    
    This class maintains separation of concerns by handling only data
    aggregation and normalization, while StrategyLogger handles file I/O.
    """
    
    def __init__(self):
        """Initialize empty aggregation dictionary."""
        # Key: (game_id, strategy, card_name, passive_type)
        # Value: {
        #   "total_triggers": int,
        #   "raw_value": float,
        #   "normalized_value": float,
        #   "game_won": bool
        # }
        self._passive_game_data: Dict[Tuple[int, str, str, str], Dict[str, Any]] = {}

    def normalize_passive_value(self, passive_type: str, raw_value: float) -> float:
        """
        Convert raw passive effect value to normalized value.
        
        Based on empirical game economy analysis from 5000-game simulations:
        - 1 gold ≈ 10 stat points (average card cost/power ratio)
        - 1 combat point = 1 damage potential
        - 1 stat increase = 1 combat power contribution
        
        Value Conversion Rationale:
        - Economy (10.0): Buying a card with 1 gold gives ~10 stat points
        - Combat/Combo (1.0): Direct combat point mapping, 1:1 damage potential
        - Copy/Synergy (1.0): Stat increases directly contribute to combat power
        - Survival (15.0): Preventing card loss ≈ avg card cost (3-5 gold) × 10
        
        Args:
            passive_type: Type of passive effect (economy, combat, combo, copy, 
                         synergy_field, survival, none)
            raw_value: Raw numeric benefit (gold, stats, points, etc.)
        
        Returns:
            Normalized value for cross-passive comparison
        
        References:
            - docs/kpi/KPI_SIMULATION_SUMMARY.md
            - Simulation data: 5000 games, 8 strategies
            - output/strategy_logs/strategy_summary.json
        """
        VALUE_CONVERSION = {
            "economy": 10.0,      # 1 gold ≈ 10 stat value
            "combat": 1.0,        # 1 combat point = 1 value
            "combo": 1.0,         # 1 combo point = 1 combat point
            "copy": 1.0,          # 1 stat increase = 1 value
            "synergy_field": 1.0, # 1 stat increase = 1 value
            "survival": 15.0,     # Resurrection ≈ avg card cost × 10
            "none": 0.0
        }
        
        multiplier = VALUE_CONVERSION.get(passive_type, 0.0)
        return raw_value * multiplier

    def aggregate_passive_buff_log(self, player, game_id: int, game_won: bool) -> None:
        """
        Process a player's passive_buff_log and aggregate into _passive_game_data.
        
        Args:
            player: Player instance with passive_buff_log attribute
            game_id: Unique game identifier
            game_won: Whether this player won the game
        
        Side Effects:
            Updates _passive_game_data dictionary with aggregated values
        """
        # Check if player has passive_buff_log attribute
        if not hasattr(player, 'passive_buff_log'):
            return
        
        # Iterate through player's passive_buff_log entries
        for entry in player.passive_buff_log:
            try:
                # Extract card, passive, delta from each entry
                card_name = entry.get("card", "unknown")
                passive_type = entry.get("passive", "none")
                delta = entry.get("delta", 0)
                
                # Create dictionary key
                key = (game_id, player.strategy, card_name, passive_type)
                
                # Create or update dictionary entry
                if key not in self._passive_game_data:
                    self._passive_game_data[key] = {
                        "total_triggers": 0,
                        "raw_value": 0.0,
                        "normalized_value": 0.0,
                        "game_won": game_won
                    }
                
                data = self._passive_game_data[key]
                
                # Increment total_triggers counter
                data["total_triggers"] += 1
                
                # Accumulate raw_value from delta
                data["raw_value"] += delta
                
                # Calculate and accumulate normalized_value
                normalized = self.normalize_passive_value(passive_type, delta)
                data["normalized_value"] += normalized
                
            except (KeyError, TypeError, ValueError) as e:
                # Skip malformed entries without crashing
                print(f"Warning: Skipping malformed passive_buff_log entry: {e}")
                continue

    def get_kpi_records(self) -> List[Dict[str, Any]]:
        """
        Return formatted KPI records ready for serialization.
        
        Returns:
            List of dictionaries with fields:
            - game_id, strategy, card_name, passive_type
            - total_triggers, raw_value, normalized_value
            - efficiency_score, game_won
        """
        records = []
        
        # Iterate through _passive_game_data dictionary (sorted for consistency)
        for key, data in sorted(self._passive_game_data.items()):
            game_id, strategy, card_name, passive_type = key
            total_triggers = data["total_triggers"]
            
            # Calculate efficiency_score (handle division by zero)
            efficiency_score = (
                data["normalized_value"] / total_triggers 
                if total_triggers > 0 else 0.0
            )
            
            # Format record with all required fields
            records.append({
                "game_id": game_id,
                "strategy": strategy,
                "card_name": card_name,
                "passive_type": passive_type,
                "total_triggers": total_triggers,
                "raw_value": data["raw_value"],
                "normalized_value": data["normalized_value"],
                "efficiency_score": round(efficiency_score, 4),  # Round to 4 decimal places
                "game_won": data["game_won"]
            })
        
        return records
