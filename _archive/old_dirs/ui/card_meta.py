"""
ui/card_meta.py
================
Kategori simgeleri ve pasif kart açıklamaları.
Her UI dosyasından import edilebilir merkezi kaynak.
"""
from typing import Dict, Tuple

# ── Kategori simgesi + renk (unicode karakter, RGB tuple) ───────────────────
# Not: Segoe UI Symbol fontunda mevcut karakterler kullanıldı
CATEGORY_META: Dict[str, Tuple[str, Tuple[int, int, int]]] = {
    "Mythology & Gods":        ("\u26a1", (248, 222,  34)),   # ⚡ sarı  – ilahi güç
    "Art & Culture":           ("\u266a", (209,  32,  82)),   # ♪ kırmızı – sanat/müzik
    "Nature & Creatures":      ("\u2663", ( 35, 114,  39)),   # ♣ yeşil  – doğa
    "Cosmos":                  ("\u2605", ( 80,  50, 180)),   # ★ mor    – uzay/yıldız
    "Science":                 ("\u2295", (  3, 174, 210)),   # ⊕ cyan   – atom/bilim
    "History & Civilizations": ("\u269c", (244,  91,  38)),   # ⚜ turuncu – tarih
}

# Geriye dönük uyumluluk: sadece renk sözlüğü
CATEGORY_COLORS: Dict[str, Tuple[int, int, int]] = {
    k: v[1] for k, v in CATEGORY_META.items()
}


def get_category_icon(category: str) -> str:
    """Kategori için unicode simge döndür."""
    return CATEGORY_META.get(category, ("\u25c6", (150, 150, 170)))[0]


def get_category_color(category: str) -> Tuple[int, int, int]:
    """Kategori için RGB renk döndür."""
    return CATEGORY_META.get(category, ("\u25c6", (150, 150, 170)))[1]


# ── Pasif açıklamaları: kart adı → oyuncu dostu kısa İngilizce açıklama ────
PASSIVE_DESCRIPTIONS: Dict[str, str] = {
    # ── COMBAT WIN ────────────────────────────────────────────────────────────
    "Ragnar\u00f6k":           "Win: strongest enemy loses highest edge.",
    "Ragnark":            "Win: strongest enemy loses highest edge.",
    "World War II":       "Win: ALL enemy cards lose highest edge.",
    "Loki":               "Win: reduce strongest enemy Meaning by -1.",
    "Cubism":             "Win: reduce strongest enemy Size by -1.",
    "Komodo Dragon":      "Win: reduce strongest enemy lowest edge by -2.",
    "Venus Flytrap":      "Win: reduce strongest enemy Gravity -1 (max 2x).",
    "Narwhal":            "Win: gain +1 Power (max 3x total).",
    "Sirius":             "Win: gain +1 Speed (max 2x total).",
    "Pulsar":             "Win: +2 combat pts (once per turn).",
    "Cerberus":           "Every 3 wins: award +3 combat pts.",
    "Fibonacci Sequence": "Win: bonus pts scale with win streak (1-3 pts).",
    # ── COMBAT LOSE ───────────────────────────────────────────────────────────
    "Guernica":           "Loss: +1 combat pt (max 3 per turn).",
    "Minotaur":           "Loss: +1 Power (max 2x/turn, +4 total).",
    "Code of Hammurabi":  "Loss: first active edge +2 (max +4 total).",
    "Frida Kahlo":        "Loss: first zero edge is restored to 1.",
    # ── CARD KILLED ───────────────────────────────────────────────────────────
    "Anubis":             "Kill: gain +1 Secret (max 2x).",
    # ── ECONOMY: INCOME ───────────────────────────────────────────────────────
    "Industrial Revolution": "Income: +1 gold each turn.",
    "Ottoman Empire":     "Income: +1 gold each turn.",
    "Babylon":            "Income: +1 gold each turn.",
    "Printing Press":     "Income: +1 gold each turn.",
    "Midas":              "Income: +1 gold if win streak >= 2.",
    "Silk Road":          "Income: +1 gold if bought 2+ cards this turn.",
    "Exoplanet":          "Income: +1 gold if market has a rarity 4-5 card.",
    "Moon Landing":       "Income: +1 gold on even-numbered turns.",
    # ── ECONOMY: MARKET & BUY ─────────────────────────────────────────────────
    "Algorithm":          "Market refresh: gain +1 gold.",
    "Age of Discovery":   "Buy a new-category card: gain +2 gold.",
    # ── SYNERGY: MYTHOLOGY ────────────────────────────────────────────────────
    "Odin":               "Pre-combat: adjacent Mythology & Gods cards +1 Meaning.",
    "Olympus":            "Pre-combat: 2+ Myth & Gods neighbors -> their Prestige +1.",
    # ── SYNERGY: COSMOS ───────────────────────────────────────────────────────
    "Medusa":             "Pre-combat: all enemy cards lose -1 Speed.",
    "Black Hole":         "Pre-combat: enemy center card loses -1 Gravity.",
    "Entropy":            "Pre-combat: every 3rd turn all neighbors lose highest edge.",
    "Gravity":            "Pre-combat: all board neighbors lose -1 Speed.",
    # ── SYNERGY: SCIENCE ──────────────────────────────────────────────────────
    "Isaac Newton":       "Pre-combat: 3+ Science cards on board -> all +1 Intelligence.",
    "Nikola Tesla":       "Pre-combat: adjacent Science cards gain +1 Intelligence.",
    # ── SYNERGY: HISTORY ──────────────────────────────────────────────────────
    "Black Death":        "Pre-combat: all enemy cards lose -1 Spread.",
    "French Revolution":  "Pre-combat: 3+ History cards -> reduce enemy best stat -1.",
    # ── COMBO ─────────────────────────────────────────────────────────────────
    "Athena":             "Pre-combat: base 1 pt + 1 pt per MIND combo.",
    "Ballet":             "Pre-combat: base 1 pt + 1 pt per CONNECTION combo.",
    "Albert Einstein":    "Pre-combat: base 1 pt + 2 bonus pts if MIND combo.",
    "Impressionism":      "Pre-combat: base 1 pt + 1 bonus if combo count >= 2.",
    "Nebula":             "Pre-combat: base 1 pt + 2 bonus if combo targets Cosmos.",
    "Golden Ratio":       "Pre-combat: base 1 pt + 3 bonus if surrounded by 6 cards.",
    # ── SURVIVAL ──────────────────────────────────────────────────────────────
    "Valhalla":           "Killed: owner gains +3 gold (once per game).",
    "Phoenix":            "Killed: revive with all stats set to 1 (once/combat).",
    "Axolotl":            "Killed: revive with all stats set to 2 (once/combat).",
    "Gothic Architecture": "Killed: all adjacent cards gain +1 Durability.",
    "Baobab":             "Killed: all adjacent cards gain +2 Durability.",
    # ── COPY / EVOLUTION ──────────────────────────────────────────────────────
    "Coelacanth":         "On copy milestone: highest edge +2.",
    "Marie Curie":        "On copy milestone: owner gains +2 gold.",
    "Space-Time":         "On copy milestone: all friendly cards +1 to all edges.",
    "Fungus":             "On copy milestone: first neighbor's highest edge +1.",
    "Yggdrasil":          "Pre-combat: grants all adjacent cards a stacking bonus.",
    # ── MISC / EXTRA ──────────────────────────────────────────────────────────
    "Eclipse":            "Pre-combat: zero out one enemy card's highest edge.",
    "Catalyst":           "Income: all board cards gain +1 power each turn.",
    "Rainforest":         "4+ Nature cards on board: all Nature cards +1 Spread.",
    "Schr\u00f6dinger's Cat":   "Pre-combat: randomly buff or debuff a neighbor edge.",
    "Platypus":           "Dual: triggers both a combat and an income bonus.",
}


def get_passive_desc(card_name: str, passive_type: str = "") -> str:
    """Pasif açıklamasını kart adıyla bul; bulunamazsa passive_type'ı döndür."""
    return PASSIVE_DESCRIPTIONS.get(
        card_name,
        PASSIVE_DESCRIPTIONS.get(passive_type, passive_type or "—")
    )
