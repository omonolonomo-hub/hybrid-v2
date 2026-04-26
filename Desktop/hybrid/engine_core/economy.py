from engine_core.constants import BASE_INCOME, MAX_INTEREST, INTEREST_STEP

class Economy:
    def __init__(self, strategy: str):
        self.gold = 0
        self.interest_multiplier = 1.5 if strategy == "economist" else 1.0
        self.interest_cap = MAX_INTEREST + 3 if strategy == "economist" else MAX_INTEREST
        self._on_change = None

    def _emit_change(self):
        if self._on_change:
            self._on_change()
        
    def calculate_income(self, win_streak: int, hp: int) -> int:
        streak_bonus = win_streak // 3
        hp_bonus = 0
        if hp < 45: hp_bonus = 3
        elif hp < 75: hp_bonus = 1
        return BASE_INCOME + streak_bonus + hp_bonus

    def calculate_interest(self) -> int:
        interest = min(MAX_INTEREST, self.gold // INTEREST_STEP)
        if self.interest_multiplier > 1.0:
            interest = min(self.interest_cap, int(interest * self.interest_multiplier) + 1)
        return interest

    def calculate_total_next_income(self, win_streak: int, hp: int) -> int:
        """Predict total gold for the next turn."""
        return self.calculate_income(win_streak, hp) + self.calculate_interest()

    def add_gold(self, amount: int):
        self.gold += amount
        self._emit_change()

    def spend_gold(self, amount: int) -> bool:
        if self.gold >= amount:
            self.gold -= amount
            self._emit_change()
            return True
        return False
