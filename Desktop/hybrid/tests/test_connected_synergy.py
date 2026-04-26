import unittest
from engine_core.board import Board, calculate_group_synergy_bonus
from engine_core.card import Card

class TestConnectedSynergy(unittest.TestCase):
    def setUp(self):
        self.board = Board()
        # Mock cards with specific stats to ensure MIND matches
        # Direction 0 is N, 1 is NE, 2 is SE, 3 is S, 4 is SW, 5 is NW
        # For axial (0,0): 
        # (0, -1) is N [dir 0]
        # (1, -1) is NE [dir 1]
        # (1, 0) is SE [dir 2]
        # (0, 1) is S [dir 3]
        # (-1, 1) is SW [dir 4]
        # (-1, 0) is NW [dir 5]
        
    def create_mind_card(self, name="MindCard"):
        # Create a card where all edges are MIND group
        # Using "Meaning" which is in "MIND" group according to constants.py
        stats = {
            "Meaning": 10,
            "Secret": 10,
            "Intelligence": 10,
            "Trace": 10,
            "Meaning2": 10, # Card class expects unique names for edges, but actually uses values
            "Secret2": 10
        }
        # Actually Card.stats is a dict, so keys must be unique.
        # Let's use the actual stat names from constants.py
        # MIND: Meaning, Secret, Intelligence, Trace
        stats = {
            "Meaning": 10,
            "Secret": 10,
            "Intelligence": 10,
            "Trace": 10,
            "Meaning_alt": 10, # I hope STAT_TO_GROUP handles these or I should use exact names
            "Secret_alt": 10
        }
        # Checking constants.py STAT_GROUPS:
        # MIND: ["Meaning", "Secret", "Intelligence", "Trace"]
        # I'll just use these 4 and repeat.
        stats = {
            "Meaning": 10,
            "Secret": 10,
            "Intelligence": 10,
            "Trace": 10,
            "Power": 10,   # EXISTENCE group
            "Gravity": 10  # CONNECTION group
        }
        return Card(name=name, category="MIND", rarity="1", stats=stats)

    def test_scattered_units(self):
        # Place two MIND cards far apart
        c1 = self.create_mind_card("C1")
        c2 = self.create_mind_card("C2")
        self.board.place((0, 0), c1)
        self.board.place((2, 0), c2)
        
        score = calculate_group_synergy_bonus(self.board)
        self.assertEqual(score, 0, "Scattered units should produce 0 synergy points")

    def test_pair_connected(self):
        # Place two MIND cards adjacent
        c1 = self.create_mind_card("C1")
        c2 = self.create_mind_card("C2")
        self.board.place((0, 0), c1)
        self.board.place((0, 1), c2) # S neighbor
        
        # C1 dir 3 (S) is 'Trace' [MIND]
        # C2 dir 0 (N) is 'Meaning' [MIND]
        # They should match!
        score = calculate_group_synergy_bonus(self.board)
        self.assertEqual(score, 5, "Connected pair should produce 5 pts (3 tier + 2 line)")

    def test_triangle_connected(self):
        c1 = self.create_mind_card("C1")
        c2 = self.create_mind_card("C2")
        c3 = self.create_mind_card("C3")
        
        # To form a MIND triangle with only 4 MIND edges:
        # (0,0) faces (1,0) at dir 2 and (0,1) at dir 3. (MIND: 0,1,2,3) -> OK.
        # (1,0) faces (0,0) at dir 5 and (0,1) at dir 4. (MIND: 0,1,2,3) -> Needs rotate!
        # (0,1) faces (0,0) at dir 0 and (1,0) at dir 1. (MIND: 0,1,2,3) -> OK.
        
        c2.rotate(2) # Shift stats by 2. Dir 5 was 3 (MIND), Dir 4 was 2 (MIND).
        
        self.board.place((0, 0), c1)
        self.board.place((1, 0), c2)
        self.board.place((0, 1), c3)
        
        score = calculate_group_synergy_bonus(self.board)
        self.assertEqual(score, 15, "Triangle cluster should produce 15 pts (9 tier + 6 lines)")

if __name__ == "__main__":
    unittest.main()
