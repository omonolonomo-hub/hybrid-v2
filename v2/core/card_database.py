"""
CardDatabase — Kart Veri Tabanı
=================================
cards.json'ı bellekte tutar. Kart adına göre O(1) lookup.
Singleton pattern — AssetLoader ile aynı tasarım.

Kullanım:
    CardDatabase.initialize("assets/data/cards.json")
    data = CardDatabase.get().lookup("Fibonacci Sequence")
    # → {"category": "Science", "passive_effect": "...", "stats": {...}, "rarity": "◆◆◆"}
"""

import json
import os
from dataclasses import dataclass, field


# Kategori → Sinerji grubu eşlemesi (cards.json'daki category değerleri)
CATEGORY_TO_SYNERGY: dict[str, str] = {
    "Mythology & Gods":        "EXISTENCE",
    "Science":                 "MIND",
    "Art & Culture":           "CONNECTION",
    "History":                 "CONNECTION",
    "Nature & Biology":        "EXISTENCE",
    "Cosmos & Space":          "MIND",
    "Science & Technology":    "MIND",
}

# Passive type → English labels for UI
PASSIVE_TYPE_LABEL: dict[str, str] = {
    "synergy_field": "SYNERGY FIELD",
    "combat":        "COMBAT",
    "combo":         "COMBO",
    "copy":          "COPY",
    "survival":      "SURVIVAL",
    "economy":       "ECONOMY",
    "ekonomi":       "ECONOMY",
    "kopya":         "COPY",
    "hayatta_kalma": "SURVIVAL",
}


@dataclass
class CardData:
    name:           str
    category:       str
    rarity:         str                          # "◆◆◆" vb.
    stats:          dict[str, int]               # {"Power": 7, "Durability": 6, ...}
    passive_type:   str
    passive_effect: str
    synergy_group:  str = field(default="")      # CATEGORY_TO_SYNERGY'den türetilir

    @property
    def rarity_level(self) -> int:
        """Handles both '◆◆◆' (cards.json) and '3' (engine_core runtime)."""
        if self.rarity.isdigit():
            return int(self.rarity)
        return self.rarity.count("◆")

    @property
    def passive_label(self) -> str:
        return PASSIVE_TYPE_LABEL.get(self.passive_type.lower(), self.passive_type.upper())

    @property
    def rarity_color(self) -> tuple[int, int, int]:
        """Nadir seviyesine göre renk döndür."""
        colors = {
            1: (150, 150, 150),   # Gri
            2: (80, 200, 120),    # Yeşil
            3: (80, 140, 255),    # Mavi
            4: (180, 80, 255),    # Mor
            5: (255, 200, 50),    # Altın
        }
        return colors.get(self.rarity_level, (200, 200, 200))


class CardDatabase:
    _instance: "CardDatabase | None" = None

    def __init__(self) -> None:
        self._cards: dict[str, CardData] = {}

    @classmethod
    def get(cls) -> "CardDatabase":
        if cls._instance is None:
            raise RuntimeError(
                "CardDatabase henüz başlatılmadı! "
                "initialize(path) çağrısı yapılmamış."
            )
        return cls._instance

    @classmethod
    def initialize(cls, json_path: str) -> None:
        """Singleton başlatıcı. main.py içinden bir kez çağrılır."""
        if cls._instance is not None:
            return   # Zaten başlatılmış

        inst = CardDatabase()
        if not os.path.exists(json_path):
            raise FileNotFoundError(
                f"[CardDatabase] cards.json bulunamadı: {json_path}"
            )

        with open(json_path, "r", encoding="utf-8") as f:
            raw: list[dict] = json.load(f)

        for entry in raw:
            name     = entry.get("name", "")
            category = entry.get("category", "")
            synergy  = CATEGORY_TO_SYNERGY.get(category, "")
            card = CardData(
                name           = name,
                category       = category,
                rarity         = entry.get("rarity", "◆"),
                stats          = entry.get("stats", {}),
                passive_type   = entry.get("passive_type", ""),
                passive_effect  = entry.get("passive_effect", ""),
                synergy_group  = synergy,
            )
            inst._cards[name] = card

        cls._instance = inst

    # ------------------------------------------------------------------ #
    # Sorgular                                                              #
    # ------------------------------------------------------------------ #
    def lookup(self, card_name: str) -> CardData | None:
        """Kart adına göre veri döndür. Bulunamazsa None."""
        return self._cards.get(card_name)

    def all_names(self) -> list[str]:
        return list(self._cards.keys())

    @property
    def card_count(self) -> int:
        return len(self._cards)

    @classmethod
    def reset(cls) -> None:
        """Test teardown için singleton sıfırla."""
        cls._instance = None
