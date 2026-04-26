"""
Player Module

Contains the Player class which manages player state, resources, and actions
in the autochess simulation.
"""

import random
from typing import Dict, List, Optional

from engine_core.constants import (
    STARTING_HP, CARD_COSTS, HAND_LIMIT, PLACE_PER_TURN, COPY_THRESH,
    COPY_THRESH_C, EVOLVE_COPIES_REQUIRED
)
from engine_core.card import Card, evolve_card
from engine_core.board import Board
from engine_core.economy import Economy
from engine_core.inventory import Inventory
from engine_core.progression import Progression
from engine_core.progression_system import ProgressionSystem
import warnings


class Player:
    def __init__(self, pid: int, strategy: str = "random"):
        self.pid       = pid
        self.strategy  = strategy
        self.hp        = STARTING_HP
        self.alive     = True
        self.win_streak = 0
        self.turns_played = 0
        
        # Composed components
        self.economy = Economy(strategy)
        self.inventory = Inventory()
        self.progression = Progression()
        self.board = Board()
        
        self.turn_pts  = 0
        self.total_pts = 0
        self._cards_bought_this_turn = 0
        self.passive_buff_log: List[dict] = []
        self.game = None # Assigned by Game instance
        
        # Legacy compatibility (for attributes directly accessed)
        self._window_bought: List[str] = []
        
        if strategy == "builder":
            from engine_core.ai import BuilderSynergyMatrix
            self.synergy_matrix = BuilderSynergyMatrix()
        else:
            self.synergy_matrix = None
            
        self.stats = {
            "wins": 0, "losses": 0, "draws": 0,
            "kills": 0, "damage_dealt": 0, "damage_taken": 0,
            "synergy_sum": 0, "synergy_turns": 0,
            "gold_spent": 0, "gold_earned": 0,
            "cards_bought_this_turn": 0,
            "opponent_board_checks": 0,
            "board_power": 0,
            "unit_count": 0,
            "combo_triggers": 0,
            "synergy_trigger_count": 0,
            "gold_per_turn": 0,
            "win_streak_max": 0,
            "market_rolls": 0,
            "copies_created": 0,
        }

    # -- Properties for backward compatibility --
    @property
    def gold(self) -> int: return self.economy.gold
    @gold.setter
    def gold(self, value: int): self.economy.gold = value

    @property
    def hand(self) -> List[Card]: return self.inventory.hand
    @hand.setter
    def hand(self, value: List[Card]): self.inventory.hand = value

    @property
    def copies(self) -> Dict[str, int]: return self.inventory.copies
    @property
    def copy_turns(self) -> Dict[str, int]: return self.inventory.copy_turns
    @property
    def copy_applied(self) -> Dict[str, Dict[str, bool]]: return self.inventory.copy_applied
    
    @property
    def evolved_card_names(self) -> List[str]: return self.progression.evolved_card_names
    @property
    def evolution_turns(self) -> List[int]: return self.progression.evolution_turns
    @property
    def card_turns_alive(self) -> Dict[str, int]: return self.progression.card_turns_alive

    @property
    def interest_multiplier(self) -> float: return self.economy.interest_multiplier
    @property
    def interest_cap(self) -> int: return self.economy.interest_cap

    @property
    def cards_bought_this_turn(self) -> int:
        return self._cards_bought_this_turn

    @cards_bought_this_turn.setter
    def cards_bought_this_turn(self, value: int):
        normalized = max(0, int(value))
        self._cards_bought_this_turn = normalized
        self.stats["cards_bought_this_turn"] = normalized

    def reset_turn_state(self):
        self.cards_bought_this_turn = 0

    def income(self):
        amount = self.economy.calculate_income(self.win_streak, self.hp)
        self.economy.add_gold(amount)
        self.stats["gold_earned"] += amount
        self.turns_played += 1
        self.reset_turn_state()

    def apply_interest(self):
        interest = self.economy.calculate_interest()
        self.economy.add_gold(interest)
        self.stats["gold_earned"] += interest

    def buy_card(self, card: Card, market=None, trigger_passive_fn=None, uid=0):
        cost = CARD_COSTS[card.rarity]
        if self.economy.spend_gold(cost):
            self.stats["gold_spent"] += cost
            cloned = card.clone(); cloned.uid = uid if uid > 0 else card.uid
            
            dropped = self.inventory.add_to_hand(cloned)
            if dropped:
                if market is not None:
                    market.pool_copies[dropped.name] = market.pool_copies.get(dropped.name, 0) + 1
                self.stats["cards_dropped"] = self.stats.get("cards_dropped", 0) + 1

            self.cards_bought_this_turn += 1
            self._window_bought.append(card.name)

            if trigger_passive_fn is not None:
                turn = self.turns_played if self.turns_played > 0 else 1
                for board_card in self.board.alive_cards():
                    trigger_passive_fn(board_card, "card_buy", self, None, {
                        "turn": turn, 
                        "bought_card": cloned, 
                        "game": self.game,
                        "market_window": getattr(self, "market", []) # Compatibility
                    }, verbose=False)

    def place_cards(self, rng=None):
        free = self.board.free_coords()
        if not free: return
        _choice = rng.choice if rng is not None else random.choice
        placed = 0
        cleared_indices = []  # Track which slots to clear
        
        for i in range(len(self.inventory.hand)):
            if placed >= PLACE_PER_TURN or not free:
                break
            card = self.inventory.hand[i]
            if card is None:
                continue
            
            coord = _choice(free)
            self.board.place(coord, card)
            cleared_indices.append(i)  # Mark for clearing
            free.remove(coord)
            placed += 1
        
        # Batch clear: N cards → 1 signal instead of N signals
        if cleared_indices:
            self.inventory.clear_slots_batch(cleared_indices)

    def check_copy_strengthening(self, turn: int, trigger_passive_fn=None):
        warnings.warn(
            "Player.check_copy_strengthening is deprecated; use ProgressionSystem.check_copy_strengthening(player, ...) instead.",
            DeprecationWarning, stacklevel=2
        )
        ProgressionSystem.check_copy_strengthening(self, turn, trigger_passive_fn)

    def check_evolution(self, market=None, card_by_name=None):
        warnings.warn(
            "Player.check_evolution is deprecated; use ProgressionSystem.check_evolution(player, ...) instead.",
            DeprecationWarning, stacklevel=2
        )
        return ProgressionSystem.check_evolution(self, market, card_by_name)

    def take_damage(self, amount: int):
        self.hp = max(0, self.hp - amount)
        self.stats["damage_taken"] += amount
        if self.hp <= 0: self.alive = False

    def __repr__(self):
        return f"P{self.pid}[{self.strategy}] HP={self.hp} pts={self.total_pts}"
