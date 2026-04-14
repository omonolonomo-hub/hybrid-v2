## card.gd  –  Autochess Hybrid Godot 4 Port
## engine_core/card.py karşılığı
class_name Card

static var _uid_counter: int = 0

var name:         String
var category:     String
var rarity:       String   # "1".."5" veya "E"
var stats:        Dictionary   # stat_name -> int
var passive_type: String = "none"
var image_front:  String = ""   # res://assets/cards/xxx_front.png
var image_back:   String = ""   # res://assets/cards/xxx_back.png
var edges:        Array         # [{name, value}, ...]  len=6
var rotation:     int   = 0    # 0-5  (60° adımlar)
var uid:          int   = 0

# ── Oluşturucu ─────────────────────────────────────────────────────
func _init(p_name:String, p_cat:String, p_rarity:String,
           p_stats:Dictionary, p_passive:String="none") -> void:
	name         = p_name
	category     = p_cat
	rarity       = p_rarity
	stats        = p_stats.duplicate()
	passive_type = p_passive
	_uid_counter += 1
	uid = _uid_counter
	# stats sırasına göre 6 kenar oluştur
	edges = []
	for k in stats:
		edges.append({"name": k, "value": stats[k]})

# ── Döndürme ────────────────────────────────────────────────────────
func rotate(steps: int = 1) -> void:
	rotation = (rotation + steps) % 6

## Rotasyonlu kenar listesi döndürür.
## rotated_edges()[d] → yön d'deki stat
func rotated_edges() -> Array:
	var n := edges.size()
	if n == 0:
		return []
	var r := rotation % n
	if r == 0:
		return edges.duplicate()
	var result := []
	result.resize(n)
	for i in n:
		result[i] = edges[(i - r + n) % n]
	return result

# ── Kenar Sorguları ─────────────────────────────────────────────────
func edge_val(d: int) -> int:
	var re := rotated_edges()
	return re[d]["value"] if d < re.size() else 0

func edge_group(d: int) -> String:
	var re := rotated_edges()
	if d < re.size() and re[d]["value"] > 0:
		return Constants.STAT_TO_GROUP.get(re[d]["name"], "")
	return ""

func dominant_group() -> String:
	var cnt := {}
	for s in stats:
		if stats[s] <= 0 or s.begins_with("_"):
			continue
		var g: String = Constants.STAT_TO_GROUP.get(s, "")
		if g != "":
			cnt[g] = cnt.get(g, 0) + 1
	if cnt.is_empty():
		return "EXISTENCE"
	var best := ""
	var best_n := -1
	for g in cnt:
		if cnt[g] > best_n:
			best_n = cnt[g]; best = g
	return best

func total_power() -> int:
	var total := 0
	for k in stats:
		if not k.begins_with("_"):
			total += stats[k]
	return total

# ── Eleme Kontrolü ─────────────────────────────────────────────────
func is_eliminated() -> bool:
	var group_vals: Dictionary = {}
	for s in stats:
		var g: String = Constants.STAT_TO_GROUP.get(s, "")
		if g != "":
			if not group_vals.has(g):
				group_vals[g] = []
			group_vals[g].append(stats[s])
	for g in group_vals:
		if group_vals[g].size() >= 2:
			var all_zero := true
			for v in group_vals[g]:
				if v != 0:
					all_zero = false; break
			if all_zero:
				return true
	return false

# ── Hasar ──────────────────────────────────────────────────────────
func lose_highest_edge() -> void:
	if edges.is_empty(): return
	var idx := 0
	var max_val := -1
	for i in edges.size():
		if edges[i]["value"] > max_val:
			max_val = edges[i]["value"]; idx = i
	var sname: String = edges[idx]["name"]
	edges[idx]["value"] = 0
	stats[sname] = 0

func apply_edge_debuff(d: int, amount: int = 1) -> void:
	var n := edges.size()
	if n == 0: return
	var base_idx := (d - rotation + n) % n
	var sname: String = edges[base_idx]["name"]
	var new_val: int = maxi(0, (edges[base_idx]["value"] as int) - amount)
	edges[base_idx]["value"] = new_val
	stats[sname] = new_val

# ── Güçlendirme ─────────────────────────────────────────────────────
func strengthen(copy_num_or_amount: int) -> void:
	## copy_num = 2 → +2,  copy_num = 3 → +3
	## Direkt puan olarak da kullanılabilir (evolver için)
	var bonus := copy_num_or_amount if copy_num_or_amount > 3 else (2 if copy_num_or_amount == 2 else 3)
	if edges.is_empty(): return
	var idx := 0; var mx := -1
	for i in edges.size():
		if edges[i]["value"] > mx:
			mx = edges[i]["value"]; idx = i
	var sname: String = edges[idx]["name"]
	edges[idx]["value"] += bonus
	stats[sname] = edges[idx]["value"]

# ── Clone ───────────────────────────────────────────────────────────
func clone() -> Card:
	var c := Card.new(name, category, rarity, stats.duplicate(), passive_type)
	c.image_front = image_front
	c.image_back  = image_back
	c.edges    = []
	for e in edges:
		c.edges.append(e.duplicate())
	c.rotation = rotation
	_uid_counter += 1
	c.uid = _uid_counter
	return c

func _to_string() -> String:
	return "Card(%s r=%s pwr=%d rot=%d)" % [name, rarity, total_power(), rotation]

# ── Evrim (3 kopya → Evolved) ──────────────────────────────────────
static func evolve_card(base_card: Card) -> Card:
	var base_total: int = base_card.total_power()
	var target_total: int = Constants.EVOLVED_TAVAN.get(base_card.rarity,
			Constants.RARITY_TAVAN["E"])
	var scale: float = 1.0 if base_total == 0 else float(target_total) / float(base_total)

	var new_stats: Dictionary = {}
	for stat_name in base_card.stats:
		if not str(stat_name).begins_with("_"):
			new_stats[stat_name] = maxi(1, int(round(float(base_card.stats[stat_name]) * scale)))

	# Yuvarlama sapmasını düzelt
	var actual_total: int = 0
	for v in new_stats.values():
		actual_total += v
	var diff: int = target_total - actual_total
	if diff != 0 and not new_stats.is_empty():
		var top_stat: String = ""
		var top_val: int = -1
		for k in new_stats:
			if new_stats[k] > top_val:
				top_val = new_stats[k]; top_stat = k
		if top_stat != "":
			new_stats[top_stat] = maxi(1, new_stats[top_stat] + diff)

	return Card.new(
		"Evolved " + base_card.name,
		base_card.category,
		"E",
		new_stats,
		base_card.passive_type
	)
