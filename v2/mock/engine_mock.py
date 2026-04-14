"""
MockGame — UI Geliştirme & Test Ortamı
=======================================
Gerçek engine_core ihtiyacı olmadan UI bileşenlerini beslemek için tasarlandı.
Kartların isimleri, doğrudan sprites/cards/ klasöründeki dosya adlarından alınır.
"""

import random

# Gerçek asset klasöründeki kart isimleri (sadece isim, _front/_back._png eksiz)
CARD_POOL = [
    "Age of Discovery", "Albert Einstein", "Algorithm", "Andromeda Galaxy",
    "Anubis", "Asteroid Belt", "Athena", "Axolotl", "Babylon", "Ballet",
    "Baobab", "Baroque", "Betelgeuse", "Bioluminescence", "Black Death",
    "Black Hole", "Blue Whale", "Camouflage", "Cerberus", "Charles Darwin",
    "Code of Hammurabi", "Coelacanth", "Cold War", "Coral Reef", "Cordyceps",
    "Cosmic Microwave Background", "Cubism", "DNA", "Dark Matter",
    "E = mc²", "Entropy", "Europa", "Event Horizon", "Exoplanet",
    "Fibonacci Sequence", "Flamenco", "French Revolution", "Frida Kahlo",
    "Fungus", "Golden Ratio", "Gothic Architecture", "Graffiti", "Gravity",
    "Guernica", "Higgs Boson", "Impressionism", "Industrial Revolution",
    "Isaac Newton", "Jazz", "Kabuki", "Komodo Dragon", "Kraken",
    "Loki", "Mantis Karidesi", "Marie Curie", "Medusa", "Midas Dokunuşu",
    "Migration", "Milky Way", "Minimalism", "Minotaur", "Mongol Empire",
    "Moon Landing", "Narwhal", "Nebula", "Nikola Tesla", "Odin",
    "Olympus", "Opera", "Ottoman Empire", "Pandora'nın Kutusu",
    "Periodic Table", "Phoenix", "Platypus", "Pop Art", "Printing Press",
    "Pulsar", "Quantum Mechanics", "Quasar", "Quetzalcoatl", "Ragnarök",
    "Rainforest", "Renaissance", "Roman Empire", "Schrödinger's Cat",
    "Shadow Puppetry", "Silk Road", "Sirius", "Space-Time", "Sparta",
    "Supernova", "Surrealism", "Tardigrade", "The Persistence of Memory",
    "Truva Atı", "Turing Machine", "Valhalla", "Venus Flytrap",
    "World War II", "Yggdrasil", "π (Pi)",
]

SHOP_SIZE = 5
HAND_SIZE = 6


class MockPlayer:
    def __init__(self, name="Player", hp=150, gold=10):
        self.name  = name
        self.hp    = hp
        self.gold  = gold
        # El: None = boş slot
        self.hand: list[str | None] = [None] * HAND_SIZE
        self.win_streak: int = 0
        self.alive: bool = True
        self.copies: dict = {}
        self.total_pts: int = 0
        self.turn_pts: int = 0
        self.passive_buff_log: list = []
        self.evolved_card_names: list = []
        self.stats: dict = {
            "wins": 0, "losses": 0, "draws": 0,
            "market_rolls": 0, "evolutions": 0, "win_streak_max": 0,
        }


class MockGame:
    def __init__(self):
        self.turn    = 1
        self.state   = "SHOP"
        self.players: list[MockPlayer] = []
        # Dükkan: human oyuncu için 5 kart
        self._shop_window: list[str | None] = [None] * SHOP_SIZE
        self._rng = random.Random(42)   # Deterministik üretim
        self.last_combat_results: list = []

    def initialize_deterministic_fixture(self) -> None:
        """Tekrarlanabilir seed ile 8 oyuncu ve dolu bir dükkan + el oluştur."""
        self.players = [
            MockPlayer(name=f"Player {i}", hp=max(150 - i * 15, 30), gold=10)
            for i in range(8)
        ]
        # Human (index 0) eline ilk 2 kartı ver
        sample = self._rng.sample(CARD_POOL, HAND_SIZE)
        for idx, name in enumerate(sample[:2]):
            self.players[0].hand[idx] = name

        # Dükkanı doldur
        self._reroll_shop()

    # ------------------------------------------------------------------ #
    # Dükkan Operasyonları                                                  #
    # ------------------------------------------------------------------ #
    def _reroll_shop(self) -> None:
        available = [c for c in CARD_POOL if c not in self.players[0].hand]
        self._shop_window = self._rng.sample(available, SHOP_SIZE)

    def get_shop_window(self, player_index: int = 0) -> list[str | None]:
        return list(self._shop_window)

    def reroll_market(self, player_index: int = 0) -> bool:
        """2 Gold karşılığı dükkânı yenile."""
        player = self.players[player_index]
        if player.gold >= 2:
            player.gold -= 2
            self._reroll_shop()
            player.stats["market_rolls"] = player.stats.get("market_rolls", 0) + 1
            return True
        return False

    def buy_card_from_slot(self, player_index: int, slot_index: int) -> bool:
        """Belirtilen slottaki kartı satın al, ele ekle, slotu boşalt."""
        player   = self.players[player_index]
        card     = self._shop_window[slot_index]
        if card is None:
            return False
        # İlk boş slota ekle
        for i, slot in enumerate(player.hand):
            if slot is None:
                player.hand[i]            = card
                player.copies[card] = player.copies.get(card, 0) + 1
                self._shop_window[slot_index] = None
                return True
        return False   # El dolu

    def toggle_lock_shop(self, player_index: int = 0) -> None:
        """Şimdilik stub — Lock mekaniği ileride eklenecek."""
        pass

    # ------------------------------------------------------------------ #
    # Okuma Erişimcileri                                                    #
    # ------------------------------------------------------------------ #
    def get_hand(self, player_index: int = 0) -> list[str | None]:
        return list(self.players[player_index].hand)

    def get_hp(self, player_index: int) -> int:
        return self.players[player_index].hp

    def get_gold(self, player_index: int) -> int:
        return self.players[player_index].gold
