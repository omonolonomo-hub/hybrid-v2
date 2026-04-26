## board.gd  –  Autochess Hybrid Godot 4 Port
## engine_core/board.py karşılığı
## Axial koordinatlı hex board
class_name HexBoard

var grid: Dictionary = {}   # Vector2i(q,r) -> Card
var has_catalyst: bool = false

# ── Board koordinatları (radius = 3 → 37 hex) ─────────────────────
static func board_coords(radius: int = 3) -> Array:
	var coords := []
	for q in range(-radius, radius+1):
		for r in range(-radius, radius+1):
			if abs(q + r) <= radius:
				coords.append(Vector2i(q, r))
	return coords

# ── Yerleştirme ────────────────────────────────────────────────────
func place(coord: Vector2i, card: Card) -> void:
	grid[coord] = card

func remove(coord: Vector2i) -> void:
	grid.erase(coord)

func free_coords(radius: int = 3) -> Array:
	var all := board_coords(radius)
	var free := []
	for c in all:
		if not grid.has(c):
			free.append(c)
	return free

# ── Sorgu ─────────────────────────────────────────────────────────
func alive_count() -> int:
	var cnt := 0
	for c in grid.values():
		if not c.is_eliminated():
			cnt += 1
	return cnt

func alive_cards() -> Array:
	var result := []
	for c in grid.values():
		if not c.is_eliminated():
			result.append(c)
	return result

# ── Hex → Piksel dönüşümü (flat-top) ──────────────────────────────
static func hex_to_pixel(q: int, r: int, origin_x: float, origin_y: float,
						  size: float = 68.0) -> Vector2:
	var x := origin_x + size * (3.0/2.0 * q)
	var y := origin_y + size * (sqrt(3.0)/2.0 * q + sqrt(3.0) * r)
	return Vector2(x, y)

static func pixel_to_hex(px: float, py: float,
						  origin_x: float, origin_y: float,
						  size: float = 68.0) -> Vector2i:
	var rel_x := px - origin_x
	var rel_y := py - origin_y
	var fq := (2.0/3.0 * rel_x) / size
	var fr := (-1.0/3.0 * rel_x + sqrt(3.0)/3.0 * rel_y) / size
	return _hex_round(fq, fr)

static func _hex_round(fq: float, fr: float) -> Vector2i:
	var fs := -fq - fr
	var q := roundi(fq)
	var r := roundi(fr)
	var s := roundi(fs)
	var dq: float = absf(q - fq)
	var dr: float = absf(r - fr)
	var ds: float = absf(s - fs)
	if dq > dr and dq > ds:
		q = -r - s
	elif dr > ds:
		r = -q - s
	return Vector2i(q, r)

# ── Kombo Tespiti ─────────────────────────────────────────────────
## İki bitişik kartın ortak yöndeki stat değerleri = eşleşme
## Python'daki find_combos() karşılığı
func find_combos() -> Array:
	## Döndürür: [combo_pts: int, bonus_dict: Dictionary]
	var combo_pts := 0
	var bonus: Dictionary = {}

	for coord in grid:
		var card: Card = grid[coord]
		var re_a := card.rotated_edges()
		for d in range(6):
			var n_coord: Vector2i = coord + (Constants.HEX_DIRS[d] as Vector2i)
			if not grid.has(n_coord): continue
			var neighbor: Card = grid[n_coord]
			var re_b: Array = neighbor.rotated_edges()
			var opp: int = Constants.OPP_DIR[d] as int
			var val_a: int = re_a[d]["value"] if d < re_a.size() else 0
			var val_b: int = re_b[opp]["value"] if opp < re_b.size() else 0
			if val_a > 0 and val_b > 0:
				var g_a: String = Constants.STAT_TO_GROUP.get(re_a[d]["name"],"")
				var g_b: String = Constants.STAT_TO_GROUP.get(re_b[opp]["name"],"")
				if g_a == g_b and g_a != "":
					combo_pts += min(val_a, val_b)
	return [combo_pts, bonus]

# ── Grup Sinerji Bonusu (v0.7 – Python board.py karşılığı) ──────────
## game.gd tarafından calculate_group_synergy_bonus() olarak çağrılır.
func calculate_group_synergy_bonus() -> int:
	# Her kartı ait olduğu gruplara göre say (kart başına 1 kez).
	var group_count: Dictionary = {}
	for card in grid.values():
		var card_groups: Dictionary = {}
		for stat in card.stats:
			if card.stats[stat] > 0 and not stat.begins_with("_"):
				var g: String = Constants.STAT_TO_GROUP.get(stat, "")
				if g != "":
					card_groups[g] = true
		for g in card_groups:
			group_count[g] = group_count.get(g, 0) + 1

	# Grup bonusu: 3 * (n-1)^1.25, max 18 per group
	var group_bonus: int = 0
	for count in group_count.values():
		if count >= 2:
			var raw: float = 3.0 * pow(float(count - 1), 1.25)
			group_bonus += mini(18, int(raw))

	# Çeşitlilik bonusu: her benzersiz grup +1, max +5
	var diversity_bonus: int = mini(5, group_count.keys().size())
	return group_bonus + diversity_bonus

## Eski isim – geriye uyumluluk için tutuldu.
func group_synergy_bonus() -> int:
	return calculate_group_synergy_bonus()

# ── Hasar Hesabı (Python board.py → calculate_damage karşılığı) ───
## Kazananın tahtasında çağrılır.
## game.gd: board_a.calculate_damage(pts_a, pts_b, turn)
func calculate_damage(winner_pts: int, loser_pts: int, turn: int) -> int:
	var base: int  = abs(winner_pts - loser_pts)
	var alive: int = int(alive_count() / 2.0)          # dampened
	# RARITY_DMG_BONUS v0.4'te temizlendi → rarity terimi 0
	var raw: int = maxi(1, base + alive)

	# BAL 5: Erken tur çarpanı
	var turn_mult: float
	if turn <= 5:
		turn_mult = 0.5
	elif turn <= 15:
		turn_mult = 0.5 + (turn - 5) * 0.05
	else:
		turn_mult = 1.0

	var final_dmg: int = maxi(1, int(float(raw) * turn_mult))
	if turn <= 10:
		final_dmg = mini(final_dmg, 15)  # Erken oyun üst sınırı
	return final_dmg
