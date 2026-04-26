from typing import List, Dict

class Progression:
    def __init__(self):
        self.evolved_card_names: List[str] = []
        self.evolution_turns: List[int] = []
        self.card_turns_alive: Dict[str, int] = {}

    def record_evolution(self, base_name: str, turn: int):
        self.evolved_card_names.append(base_name)
        self.evolution_turns.append(turn)

    def record_card_presence(self, card_name: str):
        self.card_turns_alive[card_name] = self.card_turns_alive.get(card_name, 0) + 1
