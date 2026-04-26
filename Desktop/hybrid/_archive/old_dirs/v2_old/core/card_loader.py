"""
card_loader.py
--------------
Kart verilerini cards.json'dan yükler.
Herhangi bir oyun motoruna bağımlılığı yoktur.
Her kart sözlük olarak döner — sade, düz, bağımlılıksız.
"""

import json
import os
import random
from typing import List, Dict, Any

# assets/data/cards.json yolu (v2/ klasöründen üst dizine çıkıyoruz)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CARDS_JSON = os.path.join(_BASE_DIR, "..", "assets", "data", "cards.json")

# Rarity dönüşüm tablosu (◆◆◆ → "3")
_RARITY_MAP = {
    "◆": "1",
    "◆◆": "2",
    "◆◆◆": "3",
    "◆◆◆◆": "4",
    "◆◆◆◆◆": "5",
}

# Stat → Grup eşlemesi
STAT_TO_GROUP: Dict[str, str] = {
    "Power": "EXISTENCE", "Durability": "EXISTENCE",
    "Size": "EXISTENCE",  "Speed": "EXISTENCE",
    "Meaning": "MIND",    "Secret": "MIND",
    "Intelligence": "MIND", "Trace": "MIND",
    "Gravity": "CONNECTION", "Harmony": "CONNECTION",
    "Spread": "CONNECTION",  "Prestige": "CONNECTION",
}

GROUP_COLORS: Dict[str, tuple] = {
    "EXISTENCE": (255, 110, 80),
    "MIND":      (70, 150, 255),
    "CONNECTION": (60, 235, 150),
}

RARITY_COST: Dict[str, int] = {
    "1": 1, "2": 2, "3": 3, "4": 5, "5": 7, "E": 0
}

RARITY_COLORS: Dict[str, tuple] = {
    "1": (160, 160, 160),  # gri
    "2": (80, 200, 100),   # yeşil
    "3": (60, 140, 255),   # mavi
    "4": (180, 80, 255),   # mor
    "5": (255, 180, 40),   # altın
    "E": (0, 242, 255),    # cyan (evolved)
}


def load_all_cards() -> List[Dict[str, Any]]:
    """
    Tüm kartları cards.json'dan yükler.
    Her kart şu alanlara sahip sözlüktür:
      name, category, rarity ("1"–"5"), stats {str:int},
      passive_type, passive_effect, cost, dominant_group,
      card_img_path, back_img_path
    """
    with open(_CARDS_JSON, "r", encoding="utf-8") as f:
        raw: List[dict] = json.load(f)

    cards_dir = os.path.join(_BASE_DIR, "..", "assets", "cards")
    cards: List[Dict[str, Any]] = []

    for entry in raw:
        rarity_raw = entry.get("rarity", "◆")
        rarity = _RARITY_MAP.get(rarity_raw, "1")
        stats: Dict[str, int] = entry.get("stats", {})

        # Dominant grup: en çok stat hangi grupta
        group_count: Dict[str, int] = {}
        for stat_name in stats:
            g = STAT_TO_GROUP.get(stat_name)
            if g:
                group_count[g] = group_count.get(g, 0) + 1
        dominant = max(group_count, key=group_count.get) if group_count else "EXISTENCE"

        name = entry.get("name", "Unknown")
        front_path = os.path.join(cards_dir, f"{name}_front.png")
        back_path  = os.path.join(cards_dir, f"{name}_back.png")

        cards.append({
            "name": name,
            "category": entry.get("category", ""),
            "rarity": rarity,
            "stats": stats,
            "passive_type": entry.get("passive_type", "none"),
            "passive_effect": entry.get("passive_effect", ""),
            "cost": RARITY_COST[rarity],
            "dominant_group": dominant,
            "card_img_path": front_path if os.path.exists(front_path) else None,
            "back_img_path":  back_path  if os.path.exists(back_path)  else None,
        })

    return cards


def build_shop_pool(all_cards: List[Dict], rarity_weights: Dict[str, float] = None) -> List[Dict]:
    """
    Market havuzu: ağırlıklı rastgele 5 kart seçer.
    rarity_weights örn: {"1": 0.35, "2": 0.30, "3": 0.20, "4": 0.10, "5": 0.05}
    """
    if rarity_weights is None:
        rarity_weights = {"1": 0.35, "2": 0.30, "3": 0.20, "4": 0.10, "5": 0.05}

    pool: List[Dict] = []
    for card in all_cards:
        w = rarity_weights.get(card["rarity"], 0.1)
        pool.extend([card] * max(1, int(w * 100)))

    return random.sample(pool, min(5, len(pool)))
