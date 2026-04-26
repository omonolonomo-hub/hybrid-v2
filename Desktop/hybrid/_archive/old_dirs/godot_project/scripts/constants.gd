## constants.gd  –  Autochess Hybrid Godot 4 Port
## Autoload olarak kayıtlı — class_name KULLANILMAZ (autoload ile çakışır)
extends Node

# ── Stat Grupları ──────────────────────────────────────────────────
const STAT_GROUPS := {
	"EXISTENCE":  ["Power","Durability","Size","Speed"],
	"MIND":       ["Meaning","Secret","Intelligence","Trace"],
	"CONNECTION": ["Gravity","Harmony","Spread","Prestige"],
}

# Stat adından grup adına doğrudan const eşleme
const STAT_TO_GROUP := {
	"Power":        "EXISTENCE",
	"Durability":   "EXISTENCE",
	"Size":         "EXISTENCE",
	"Speed":        "EXISTENCE",
	"Meaning":      "MIND",
	"Secret":       "MIND",
	"Intelligence": "MIND",
	"Trace":        "MIND",
	"Gravity":      "CONNECTION",
	"Harmony":      "CONNECTION",
	"Spread":       "CONNECTION",
	"Prestige":     "CONNECTION",
}

# ── Grup Avantaj ────────────────────────────────────────────────────
const GROUP_BEATS := {
	"EXISTENCE":"CONNECTION","MIND":"EXISTENCE","CONNECTION":"MIND"
}

# ── Rarity ────────────────────────────────────────────────────────
const RARITY_TAVAN   := {"1":30,"2":36,"3":42,"4":48,"5":54,"E":72}
const EVOLVED_TAVAN  := {"1":40,"2":48,"3":56,"4":64,"5":72,"E":72}
const CARD_COSTS     := {"1":1, "2":2, "3":3, "4":5, "5":7, "E":0}

# ── Hex Grid Yönleri (axial)  ─────────────────────────────────────
# Sıra: N(0) NE(1) SE(2) S(3) SW(4) NW(5)
const HEX_DIRS := [
	Vector2i( 0,-1), Vector2i( 1,-1), Vector2i(1, 0),
	Vector2i( 0, 1), Vector2i(-1, 1), Vector2i(-1,0),
]
const DIR_NAME  := ["N","NE","SE","S","SW","NW"]
const OPP_DIR   := {0:3,1:4,2:5,3:0,4:1,5:2}

# ── Board & Oyun Kuralları ─────────────────────────────────────────
const BOARD_RADIUS          := 3
const STARTING_HP           := 150
const KILL_PTS              := 8
const COPY_THRESH           := [4, 7]
const COPY_THRESH_C         := [3, 6]
const BASE_INCOME           := 3
const MARKET_REFRESH_COST   := 2
const MAX_INTEREST          := 5
const INTEREST_STEP         := 10
const HAND_LIMIT            := 6
const PLACE_PER_TURN        := 1
const EVOLVE_COPIES_REQUIRED := 3

# ── AI Stratejileri ────────────────────────────────────────────────
const STRATEGIES := [
	"random","warrior","builder","evolver",
	"economist","balancer","rare_hunter","tempo"
]

# ── Renkler (Color) ────────────────────────────────────────────────
const C_BG      := Color(0.047,0.059,0.110)
const C_PANEL   := Color(0.063,0.078,0.133)
const C_ACCENT  := Color(0.000,0.950,1.000)
const C_GOLD    := Color(1.000,0.800,0.000)
const C_WHITE   := Color(0.961,0.961,1.000)
const C_DIM     := Color(0.510,0.549,0.667)
const C_SELECT  := Color(1.000,0.000,1.000)
const C_HP_OK   := Color(0.275,0.882,0.549)
const C_HP_LOW  := Color(1.000,0.373,0.431)
const C_BRONZE  := Color(0.588,0.314,0.157)
const C_MAGENTA := Color(1.000,0.000,0.588)
const C_LINE    := Color(0.165,0.227,0.361)

const GROUP_COLORS := {
	"EXISTENCE":  Color(1.000,0.235,0.196),
	"MIND":       Color(0.196,0.510,1.000),
	"CONNECTION": Color(0.157,0.902,0.510),
}
const RARITY_COLORS := {
	"1":Color(0.627,0.627,0.627),"2":Color(0.196,1.000,0.471),
	"3":Color(0.000,0.706,1.000),"4":Color(1.000,0.000,1.000),
	"5":Color(1.000,0.843,0.000),"E":Color(1.000,1.000,1.000),
}
const STRATEGY_COLORS := {
	"random":Color(0.6,0.6,0.6),      "warrior":Color(1.0,0.3,0.2),
	"builder":Color(0.3,0.8,1.0),     "evolver":Color(0.8,0.3,1.0),
	"economist":Color(1.0,0.8,0.0),   "balancer":Color(0.4,1.0,0.6),
	"rare_hunter":Color(1.0,0.5,0.0), "tempo":Color(0.0,1.0,0.8),
}
# ── Hasar Bonusu (v0.4'te boşaltıldı – çıkış geçmiş ile uyumluluk) ────────
const RARITY_DMG_BONUS: Dictionary = {}

const STAT_SHORT := {
	"Power":"PW","Durability":"DU","Size":"SZ","Speed":"SP",
	"Meaning":"MN","Secret":"SC","Intelligence":"IN","Trace":"TR",
	"Gravity":"GR","Harmony":"HR","Spread":"SR","Prestige":"PR",
}
