"""
CardDatabase — kart veri tabanı.
"""

import json
import os
from dataclasses import dataclass, field

from v2.core.exceptions import DatabaseError


CATEGORY_TO_SYNERGY: dict[str, str] = {
    "Mythology & Gods": "EXISTENCE",
    "Science": "MIND",
    "Art & Culture": "CONNECTION",
    "History": "CONNECTION",
    "Nature & Biology": "EXISTENCE",
    "Cosmos & Space": "MIND",
    "Science & Technology": "MIND",
}

PASSIVE_TYPE_LABEL: dict[str, str] = {
    "synergy_field": "SYNERGY FIELD",
    "combat": "COMBAT",
    "combo": "COMBO",
    "copy": "COPY",
    "survival": "SURVIVAL",
    "economy": "ECONOMY",
    "ekonomi": "ECONOMY",
    "kopya": "COPY",
    "hayatta_kalma": "SURVIVAL",
}


@dataclass
class CardData:
    name: str
    category: str
    rarity: str
    stats: dict[str, int]
    passive_type: str
    passive_effect: str
    synergy_group: str = field(default="")

    @property
    def rarity_level(self) -> int | str:
        if self.rarity.upper() == "E":
            return "E"
        if self.rarity.isdigit():
            return int(self.rarity)
        return self.rarity.count("◆")

    @property
    def passive_label(self) -> str:
        return PASSIVE_TYPE_LABEL.get(self.passive_type.lower(), self.passive_type.upper())

    @property
    def rarity_color(self) -> tuple[int, int, int]:
        colors = {
            1: (150, 150, 150),
            2: (80, 200, 120),
            3: (80, 140, 255),
            4: (180, 80, 255),
            5: (255, 200, 50),
        }
        return colors.get(self.rarity_level, (200, 200, 200))


class CardDatabase:
    _instance: "CardDatabase | None" = None

    def __init__(self) -> None:
        self._cards: dict[str, CardData] = {}

    @classmethod
    def get(cls) -> "CardDatabase":
        if cls._instance is None:
            raise DatabaseError(
                "CardDatabase henüz başlatılmadı! initialize(path) çağrısı yapılmamış."
            )
        return cls._instance

    @classmethod
    def initialize(cls, json_path: str) -> None:
        if cls._instance is not None:
            return

        inst = CardDatabase()
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"[CardDatabase] cards.json bulunamadı: {json_path}")

        with open(json_path, "r", encoding="utf-8") as handle:
            raw: list[dict] = json.load(handle)

        for entry in raw:
            name = entry.get("name", "")
            category = entry.get("category", "")
            inst._cards[name] = CardData(
                name=name,
                category=category,
                rarity=entry.get("rarity", "◆"),
                stats=entry.get("stats", {}),
                passive_type=entry.get("passive_type", ""),
                passive_effect=entry.get("passive_effect", ""),
                synergy_group=CATEGORY_TO_SYNERGY.get(category, ""),
            )

        cls._instance = inst

    def lookup(self, card_name: str) -> "CardData | None":
        result = self._cards.get(card_name)
        if result is not None:
            return result

        if card_name.startswith("Evolved "):
            base_name = card_name[8:]
            base = self._cards.get(base_name)
            if base is not None:
                evolved_stats = {
                    stat_key: min(72, int(value * 1.4))
                    for stat_key, value in base.stats.items()
                }
                return CardData(
                    name=card_name,
                    category=base.category,
                    rarity="E",
                    stats=evolved_stats,
                    passive_type=base.passive_type,
                    passive_effect=base.passive_effect,
                    synergy_group=base.synergy_group,
                )

        return None

    def all_names(self) -> list[str]:
        return list(self._cards.keys())

    @property
    def card_count(self) -> int:
        return len(self._cards)

    @classmethod
    def reset(cls) -> None:
        cls._instance = None
