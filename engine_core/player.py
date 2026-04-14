"""
Player Module

Contains the Player class which manages player state, resources, and actions
in the autochess simulation.
"""

import random
from typing import Dict, List, Optional

# Import dependencies
try:
    # Try relative import first (when used as a module)
    from .constants import (
        STARTING_HP, BASE_INCOME, MAX_INTEREST, INTEREST_STEP,
        CARD_COSTS, HAND_LIMIT, PLACE_PER_TURN, COPY_THRESH,
        COPY_THRESH_C, EVOLVE_COPIES_REQUIRED
    )
    from .card import Card, evolve_card
    from .board import Board
except ImportError:
    # Fall back to absolute import (when run as a script)
    from constants import (
        STARTING_HP, BASE_INCOME, MAX_INTEREST, INTEREST_STEP,
        CARD_COSTS, HAND_LIMIT, PLACE_PER_TURN, COPY_THRESH,
        COPY_THRESH_C, EVOLVE_COPIES_REQUIRED
    )
    from card import Card, evolve_card
    from board import Board


class Player:
    def __init__(self, pid: int, strategy: str = "random"):
        self.pid       = pid
        self.strategy  = strategy
        self.hp        = STARTING_HP
        self.gold      = 0
        self.board     = Board()
        self.hand: List[Card] = []          # copies not on board
        self.copies: Dict[str, int] = {}    # card_name -> copy count
        self.copy_turns: Dict[str, int] = {}# card_name -> turns waited
        self.turn_pts  = 0                  # this turn's total points
        self.total_pts = 0                  # cumulative points
        self.alive     = True
        self.win_streak = 0                 # consecutive wins
        self.turns_played = 0               # turns played
        self.cards_bought_this_turn = 0     # buys this turn (mirrors stats)
        self.interest_multiplier = 1.5 if strategy == "economist" else 1.0
        self.interest_cap = MAX_INTEREST + 3 if strategy == "economist" else MAX_INTEREST
        self.copy_applied: Dict[str, Dict[str, bool]] = {}
        self._window_bought: List[str] = []  # names bought from current market window (for return_unsold)
        self.evolved_card_names: List[str] = []  # Track evolved card names
        self.card_turns_alive: Dict[str, int] = {}  # card_name -> total turns on board
        self.evolution_turns: List[int] = []  # game turn when each evolution fired
        self.passive_buff_log: List[dict] = []  # [{turn, card, passive, trigger, delta}]
        # Builder synergy matrix — session-level adjacency memory
        # Sadece builder strategy için oluşturulur; diğer stratejiler None alır.
        if strategy == "builder":
            try:
                from .ai import BuilderSynergyMatrix
            except ImportError:
                from ai import BuilderSynergyMatrix
            self.synergy_matrix = BuilderSynergyMatrix()
        else:
            self.synergy_matrix = None
        self.stats = {
            "wins": 0, "losses": 0, "draws": 0,
            "kills": 0, "damage_dealt": 0, "damage_taken": 0,
            "synergy_sum": 0, "synergy_turns": 0,  # synergy tracking
            "gold_spent": 0, "gold_earned": 0,    # economy tracking
            "cards_bought_this_turn": 0,           # buys this turn
            "opponent_board_checks": 0,            # opponent board checks
            # --- instrumentation metrics ---
            "board_power": 0,           # cumulative sum of board total_power each turn
            "unit_count": 0,            # cumulative sum of board card count each turn
            "combo_triggers": 0,        # total combo points earned across all turns
            "synergy_trigger_count": 0, # number of turns synergy bonus > 0
            "gold_per_turn": 0,         # cumulative gold earned (for avg: / turns_played)
            "win_streak_max": 0,        # peak win streak reached
            "market_rolls": 0,          # number of market windows opened
            "copies_created": 0,        # number of copy-strengthen thresholds fired
        }

    def income(self):
        """Turn-start income: base + HP bailout + win-streak bonus.
        NOTE: Interest is applied separately in apply_interest()."""
        base_income = BASE_INCOME

        # Win streak: +1 gold per 3 consecutive wins
        streak_bonus = self.win_streak // 3

        # Low-HP bailout gold
        hp_bonus = 0
        if self.hp < 45:
            hp_bonus = 3
        elif self.hp < 75:
            hp_bonus = 1

        self.gold += base_income + streak_bonus + hp_bonus
        self.stats["gold_earned"] += base_income + streak_bonus + hp_bonus

        # GOLD_CAP removed (unlimited gold economy)
        # Advance turn and reset per-turn buy counter
        self.turns_played += 1
        self.cards_bought_this_turn = 0
        self.stats["cards_bought_this_turn"] = 0

    def apply_interest(self):
        """Interest: +1 per 10 gold banked (max 5). Call AFTER card purchases."""
        interest = min(MAX_INTEREST, self.gold // INTEREST_STEP)

        # Economist (multiplier > 1) gets boosted interest
        if self.interest_multiplier > 1.0:
            interest = min(self.interest_cap, int(interest * self.interest_multiplier) + 1)

        self.gold += interest
        self.stats["gold_earned"] += interest

        # GOLD_CAP removed (unlimited gold economy)

    def buy_card(self, card: Card, market=None, trigger_passive_fn=None):
        """Buy a card from the market (copy tracking included).
        v0.6: hand cap HAND_LIMIT (6). On 7th buy, oldest card (hand[0]) is removed
        and returned to the pool when market is passed.
        
        Args:
            card: Card to buy
            market: Market instance for hand-overflow pool returns (optional)
            trigger_passive_fn: Function to trigger passive effects (optional)
        """
        cost = CARD_COSTS[card.rarity]
        if self.gold >= cost:
            self.gold -= cost
            self.stats["gold_spent"] += cost
            cloned = card.clone()
            self.hand.append(cloned)
            self.copies[card.name] = self.copies.get(card.name, 0) + 1
            self.cards_bought_this_turn += 1
            self.stats["cards_bought_this_turn"] += 1
            self._window_bought.append(card.name)

            # Trigger card_buy passive if function provided
            if trigger_passive_fn is not None:
                turn = self.turns_played if self.turns_played > 0 else 1
                for board_card in self.board.alive_cards():
                    trigger_passive_fn(board_card, "card_buy", self, None, {
                        "turn": turn,
                        "bought_card": cloned
                    }, verbose=False)

            # v0.6 - hand overflow: drop oldest card
            if len(self.hand) > HAND_LIMIT:
                dropped = self.hand.pop(0)          # FIFO: oldest card
                # update copy count (we lost a held copy)
                if self.copies.get(dropped.name, 0) > 0:
                    self.copies[dropped.name] -= 1
                # return to pool if market reference available
                if market is not None and hasattr(market, "pool_copies"):
                    market.pool_copies[dropped.name] = (
                        market.pool_copies.get(dropped.name, 0) + 1
                    )
                self.stats["cards_dropped"] = self.stats.get("cards_dropped", 0) + 1

    def place_cards(self, rng=None):
        """Place up to PLACE_PER_TURN cards from hand onto random empty hexes.
        v0.6: default 1 card per turn to board; rest stay in hand.
        Selection walks hand in list order (FIFO queue).
        """
        hand = self.hand
        if not hand:
            return
        free = self.board.free_coords()
        if not free:
            return
        _choice = rng.choice if rng is not None else random.choice
        placed = 0
        i = 0
        while i < len(hand) and placed < PLACE_PER_TURN:
            card = hand[i]
            coord = _choice(free)
            self.board.place(coord, card)
            free.remove(coord)
            hand.pop(i)
            placed += 1

    def check_copy_strengthening(self, turn: int, trigger_passive_fn=None):
        """Strengthen cards when copy thresholds are reached.
        
        Args:
            turn: Current game turn
            trigger_passive_fn: Function to trigger passive effects (optional)
        """
        board = self.board
        thresholds = COPY_THRESH_C if board.has_catalyst else COPY_THRESH
        thresh_2 = thresholds[0]
        thresh_3 = thresholds[1]
        grid = board.grid
        grid_vals = list(grid.values())
        copy_turns = self.copy_turns
        copy_applied = self.copy_applied
        _ctx = {"turn": turn}

        for name, count in self.copies.items():
            on_board = any(c.name == name for c in grid_vals)
            if not on_board:
                continue
            t = copy_turns.get(name, 0) + 1
            copy_turns[name] = t

            if name not in copy_applied:
                copy_applied[name] = {"2": False, "3": False}
            applied = copy_applied[name]

            if count >= 2 and t >= thresh_2 and not applied["2"]:
                for card in grid_vals:
                    if card.name == name:
                        card.strengthen(2)
                        self.passive_buff_log.append({
                            "turn":    turn,
                            "card":    name,
                            "passive": "copy_strengthen",
                            "trigger": "copy_2",
                            "delta":   2,
                        })
                        if trigger_passive_fn is not None:
                            trigger_passive_fn(card, "copy_2", self, None, _ctx, verbose=False)
                applied["2"] = True
                self.stats["copies_created"] += 1

            if count >= 3 and t >= thresh_3 and not applied["3"]:
                for card in grid_vals:
                    if card.name == name:
                        card.strengthen(3)
                        self.passive_buff_log.append({
                            "turn":    turn,
                            "card":    name,
                            "passive": "copy_strengthen",
                            "trigger": "copy_3",
                            "delta":   3,
                        })
                        if trigger_passive_fn is not None:
                            trigger_passive_fn(card, "copy_3", self, None, _ctx, verbose=False)
                applied["3"] = True
                self.stats["copies_created"] += 1

    def check_evolution(self, market=None, card_by_name=None):
        """v0.7 Evolution System: if a player has EVOLVE_COPIES_REQUIRED (3) copies
        of any base card, immediately evolve:
        - Remove 2 copies from hand/board (the 3rd becomes the evolved card)
        - Replace the board copy (or hand copy) with the Evolved card
        - Return the 2 consumed copies to the market pool
        - Only evolver strategy triggers this; others keep the old copy system
        
        Args:
            market: Market instance for returning consumed copies (optional)
            card_by_name: Dictionary mapping card names to Card templates (optional)
        
        Returns:
            List of card names that were evolved this call
        """
        if self.strategy != "evolver":
            return []

        evolved_names = []
        for base_name, count in list(self.copies.items()):
            if count < EVOLVE_COPIES_REQUIRED:
                continue
            evolved_key = f"Evolved {base_name}"
            if self.copies.get(evolved_key, 0) > 0:
                continue
            
            # Get base card template
            if card_by_name is None:
                continue
            base_template = card_by_name.get(base_name)
            if base_template is None:
                continue

            # Remove 2 copies, keep 1 slot for the evolved card
            removed = 0
            for card in list(self.hand):
                if removed >= 2:
                    break
                if card.name == base_name:
                    self.hand.remove(card)
                    removed += 1
                    if market is not None and hasattr(market, "pool_copies"):
                        market.pool_copies[base_name] = market.pool_copies.get(base_name, 0) + 1

            if removed < 2:
                for coord, card in list(self.board.grid.items()):
                    if removed >= 2:
                        break
                    if card.name == base_name:
                        self.board.remove(coord)
                        removed += 1
                        if market is not None and hasattr(market, "pool_copies"):
                            market.pool_copies[base_name] = market.pool_copies.get(base_name, 0) + 1

            self.copies[base_name] = max(0, self.copies.get(base_name, 0) - 2)

            evolved = evolve_card(base_template)

            # ── FAZ 3: Rarity-bazlı güç ölçekleme (Evolver high-risk/high-reward) ─
            # R3 → +12%  |  R4 → +16%  |  R5 → +20%
            # HP aynı factor ile ama daha muhafazakâr (%04 per rarity yerine %02).
            # Not: strengthen() toplam power'a mutlak puan ekler, oran değil;
            #      bu yüzden önce base power'dan delta hesaplanır.
            try:
                rarity_int = int(base_template.rarity)
            except (ValueError, TypeError):
                rarity_int = 0
            if 3 <= rarity_int <= 5:
                bonus_pct    = 0.04 * rarity_int          # 0.12 / 0.16 / 0.20
                base_power   = evolved.total_power()
                bonus_points = int(round(base_power * bonus_pct))
                if bonus_points > 0:
                    evolved.strengthen(bonus_points)
            replaced_on_board = False
            for coord, card in list(self.board.grid.items()):
                if card.name == base_name:
                    self.board.place(coord, evolved)
                    replaced_on_board = True
                    break

            if not replaced_on_board:
                for i, card in enumerate(self.hand):
                    if card.name == base_name:
                        self.hand[i] = evolved
                        break
                else:
                    self.hand.append(evolved)

            self.copies[evolved_key] = self.copies.get(evolved_key, 0) + 1
            self.stats["evolutions"] = self.stats.get("evolutions", 0) + 1
            evolved_names.append(base_name)
            self.evolved_card_names.append(base_name)
            # Track evolution turn
            current_turn = self.turns_played if self.turns_played > 0 else 1
            self.evolution_turns.append(current_turn)

        return evolved_names

    def take_damage(self, amount: int):
        self.hp = max(0, self.hp - amount)
        self.stats["damage_taken"] += amount
        if self.hp <= 0:
            self.alive = False

    def __repr__(self):
        return f"P{self.pid}[{self.strategy}] HP={self.hp} pts={self.total_pts}"
