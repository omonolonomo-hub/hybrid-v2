# ================================================================
# AUTOCHESS HYBRID - AI (GDScript 4)
# Kart satın alma ve yerleştirme stratejileri.
# ai.py'nin birebir karşılığı.
# ================================================================
class_name AI
extends RefCounted

# ── Eğitilmiş varsayılan parametreler ───────────────────────────
const TRAINED_PARAMS: Dictionary = {
	"economist": {
		"thresh_high":       27.012525825899594,
		"thresh_mid":         5.887870123764179,
		"thresh_low":        11.572130722067811,
		"buy_2_thresh":      15.0,
		"greed_turn_end":     6.556475060280888,
		"spike_turn_end":    14.773731014667712,
		"greed_gold_thresh": 15.0,
		"spike_r4_thresh":   42.07452062733782,
		"convert_r5_thresh": 80.0,
		"spike_buy_count":    3.1891953600814538,
		"convert_buy_count":  3.6086842743641023,
	},
	"warrior": {
		"power_weight":  1.0,
		"rarity_weight": 0.0,
	},
	"builder": {
		"combo_weight":       0.5,
		"power_weight":       0.4,
		"greed_turn_end":     5.0,
		"spike_turn_end":    14.773731014667712,
		"greed_gold_thresh":  8.0,
		"spike_r4_thresh":   42.07452062733782,
		"convert_r5_thresh": 80.0,
		"spike_buy_count":    2.0,
		"convert_buy_count":  3.0,
	},
	"evolver": {
		"evo_near_bonus":    1000.0,
		"evo_one_bonus":      500.0,
		"rarity_weight_mult":  10.0,
		"power_weight":         1.0,
	},
	"balancer": {
		"group_bonus":  5.0,
		"group_thresh": 3.0,
		"power_weight": 1.0,
	},
	"rare_hunter": {
		"fallback_rarity": 3.0,
	},
	"tempo": {
		"power_center_thresh": 45.0,
		"combo_center_weight":  1.5,
	},
	"random": {},
}

# constants.gd'den
const CARD_COSTS: Dictionary = {"1": 1, "2": 2, "3": 3, "4": 5, "5": 8, "E": 0}
const HEX_DIRS: Array = [Vector2i(1,0), Vector2i(-1,0), Vector2i(0,1), Vector2i(0,-1), Vector2i(1,-1), Vector2i(-1,1)]
const PLACE_PER_TURN: int = 1
const MAX_LOOKAHEAD_CARDS: int = 4
const MAX_COORD_CHECK: int = 8

# STAT_TO_GROUP: stat adından grup adına eşleme
# (constants.py'den — gerekirse genişlet)
const STAT_TO_GROUP: Dictionary = {
	"attack":     "COMBAT",
	"defense":    "COMBAT",
	"speed":      "MOTION",
	"range":      "MOTION",
	"magic":      "ARCANE",
	"spirit":     "ARCANE",
	"connection": "BOND",
	"loyalty":    "BOND",
}

# ── Parametre sözlüğü (ParameterizedAI için) ─────────────────────
var p: Dictionary = {}   # strateji -> { key -> value }


func _init(params_override: Dictionary = {}) -> void:
	# Varsayılanları kopyala
	for strat in TRAINED_PARAMS:
		p[strat] = TRAINED_PARAMS[strat].duplicate()
	# Manuel override uygula
	for strat in params_override:
		if p.has(strat):
			for k in params_override[strat]:
				p[strat][k] = params_override[strat][k]
		else:
			p[strat] = params_override[strat].duplicate()


func get_param(strategy: String, key: String, default: Variant) -> Variant:
	return p.get(strategy, {}).get(key, default)


# ================================================================
# Ana dispatcher: buy_cards
# ================================================================

func buy_cards(player, market: Array, market_obj = null,
			   rng: RandomNumberGenerator = null,
			   trigger_passive_fn: Callable = Callable()) -> void:
	if rng == null:
		rng = RandomNumberGenerator.new()
		rng.randomize()

	match player.strategy:
		"random":      _buy_random(player, market, market_obj, rng, trigger_passive_fn)
		"warrior":     _buy_warrior(player, market, market_obj, rng, trigger_passive_fn)
		"builder":     _buy_builder(player, market, market_obj, rng, trigger_passive_fn)
		"evolver":     _buy_evolver(player, market, market_obj, rng, trigger_passive_fn)
		"economist":   _buy_economist(player, market, market_obj, rng, trigger_passive_fn)
		"balancer":    _buy_balancer(player, market, market_obj, rng, trigger_passive_fn)
		"rare_hunter": _buy_rare_hunter(player, market, market_obj, rng, trigger_passive_fn)
		"tempo":       _buy_warrior(player, market, market_obj, rng, trigger_passive_fn)
		_:             _buy_random(player, market, market_obj, rng, trigger_passive_fn)


# ================================================================
# Ana dispatcher: place_cards
# ================================================================

func place_cards(player, rng: RandomNumberGenerator = null) -> void:
	if rng == null:
		rng = RandomNumberGenerator.new()
		rng.randomize()

	match player.strategy:
		"builder": _place_fast_synergy(player)
		"tempo":
			var pct: float = get_param("tempo", "power_center_thresh", 45.0)
			var ccw: float = get_param("tempo", "combo_center_weight",  1.5)
			_place_aggressive(player, pct, ccw)
		_: _place_smart_default(player, rng)


# ================================================================
# Paylaşılan faz ekonomi motoru
# ================================================================

func _economy_phase_controls(player, market: Array, max_cards: int,
							  strategy: String) -> Dictionary:
	var gold: int  = player.gold
	var hp: int    = player.hp
	var turn: int  = player.turns_played

	# Acil durum
	if hp < 35:
		var affordable: Array = market.filter(
			func(c): return CARD_COSTS.get(c.rarity, 99) <= gold)
		return {
			"phase": "emergency", "candidates": affordable,
			"buy_count": mini(max_cards, 3),
			"cheap_only": false, "ratio_floor": null
		}

	var fallback: String = "economist" if strategy != "economist" else ""
	var _gp: Callable = func(key: String, default: Variant) -> Variant:
		return get_param(strategy, key,
			get_param(fallback, key, default) if fallback != "" else default)

	var greed_turn_end:   float = _gp.call("greed_turn_end",   8.0)
	var greed_gold_thresh:float = _gp.call("greed_gold_thresh",12.0)
	var spike_turn_end:   float = _gp.call("spike_turn_end",   18.0)
	var spike_r4_thresh:  float = _gp.call("spike_r4_thresh",  40.0)
	var thresh_high:      float = _gp.call("thresh_high",      25.0)
	var buy_2_thresh:     float = _gp.call("buy_2_thresh",     15.0)
	var spike_buy_count:  int   = maxi(1, int(_gp.call("spike_buy_count", 3.0)))
	var convert_r5_thresh:float = _gp.call("convert_r5_thresh",60.0)
	var convert_buy_count:int   = maxi(1, int(_gp.call("convert_buy_count",4.0)))

	# GREED fazı
	if turn <= greed_turn_end:
		if gold < 8:
			return {"phase":"greed_hold","candidates":[],"buy_count":0,
				"cheap_only":true,"ratio_floor":3.0}
		if gold >= greed_gold_thresh:
			var cheap: Array = market.filter(func(c):
				return CARD_COSTS.get(c.rarity,99) <= CARD_COSTS.get("2",2))
			return {"phase":"greed_buy","candidates":cheap,
				"buy_count":mini(max_cards,1),"cheap_only":true,"ratio_floor":3.0}
		return {"phase":"greed_hold","candidates":[],"buy_count":0,
			"cheap_only":true,"ratio_floor":3.0}

	# SPIKE fazı
	if turn <= spike_turn_end:
		var max_cost: int
		if   gold >= spike_r4_thresh: max_cost = CARD_COSTS.get("4",5)
		elif gold >= thresh_high:     max_cost = CARD_COSTS.get("3",3)
		elif gold >= 12:              max_cost = CARD_COSTS.get("2",2)
		else:                         max_cost = CARD_COSTS.get("1",1)

		var candidates: Array = market.filter(
			func(c): return CARD_COSTS.get(c.rarity,99) <= max_cost)
		var cnt: int
		if   gold >= thresh_high: cnt = mini(max_cards, spike_buy_count)
		elif gold >= buy_2_thresh: cnt = mini(max_cards, 2)
		else:                      cnt = mini(max_cards, 1)
		return {"phase":"spike","candidates":candidates,"buy_count":cnt,
			"cheap_only":false,"ratio_floor":null}

	# CONVERT fazı
	var max_cost_c: int
	if   gold >= convert_r5_thresh: max_cost_c = CARD_COSTS.get("5",8)
	elif gold >= 40:                 max_cost_c = CARD_COSTS.get("4",5)
	elif gold >= 20:                 max_cost_c = CARD_COSTS.get("3",3)
	else:                            max_cost_c = CARD_COSTS.get("2",2)

	var cands: Array = market.filter(
		func(c): return CARD_COSTS.get(c.rarity,99) <= max_cost_c)
	var cnt_c: int
	if   gold >= 50: cnt_c = mini(max_cards, convert_buy_count)
	elif gold >= 30: cnt_c = mini(max_cards, 3)
	else:            cnt_c = mini(max_cards, 2)
	return {"phase":"convert","candidates":cands,"buy_count":cnt_c,
		"cheap_only":false,"ratio_floor":null}


# ================================================================
# Satın alma stratejileri
# ================================================================

func _buy_random(player, market: Array, market_obj, rng: RandomNumberGenerator,
				 trigger_passive_fn: Callable) -> void:
	var gold: int = player.gold
	var affordable: Array = market.filter(
		func(c): return CARD_COSTS.get(c.rarity,99) <= gold)
	# Fisher-Yates shuffle
	for i in range(affordable.size() - 1, 0, -1):
		var j: int = rng.randi_range(0, i)
		var tmp = affordable[i]; affordable[i] = affordable[j]; affordable[j] = tmp
	for card in affordable.slice(0, 1):
		player.buy_card(card, market_obj, trigger_passive_fn)


func _buy_warrior(player, market: Array, market_obj, _rng: RandomNumberGenerator,
				  trigger_passive_fn: Callable) -> void:
	var strat: String = player.strategy
	var pw: float = get_param(strat, "power_weight", 1.0)
	var rw: float = get_param(strat, "rarity_weight", 0.0)
	var rmap: Dictionary = {"1":1,"2":2,"3":3,"4":4,"5":5,"E":6}
	var affordable: Array = market.filter(
		func(c): return CARD_COSTS.get(c.rarity,99) <= player.gold)
	affordable.sort_custom(func(a,b):
		var sa: float = a.total_power()*pw + rmap.get(a.rarity,0)*rw
		var sb: float = b.total_power()*pw + rmap.get(b.rarity,0)*rw
		return sa > sb)
	for card in affordable.slice(0, 1):
		player.buy_card(card, market_obj, trigger_passive_fn)


func _buy_builder(player, market: Array, market_obj, _rng: RandomNumberGenerator,
				  trigger_passive_fn: Callable) -> void:
	var cw: float = get_param("builder","combo_weight",0.5)
	var pw: float = get_param("builder","power_weight",0.4)
	var econ: Dictionary = _economy_phase_controls(player, market, 3, "builder")
	if econ["candidates"].is_empty() or econ["buy_count"] <= 0:
		return

	# Tahta durumu
	var dom_count: Dictionary = {}
	var board_cards: Array = player.board.alive_cards()
	var board_card_names: Array = board_cards.map(func(c): return c.name)
	var board_categories: Array = board_cards.map(func(c): return c.category)

	for card in board_cards:
		var grp: String = card.dominant_group()
		dom_count[grp] = dom_count.get(grp, 0) + 1

	var target_group: String
	if dom_count.is_empty():
		# Erken oyun: marketteki en yaygın grubu hedef al
		var market_groups: Dictionary = {}
		for mc in econ["candidates"]:
			for s in mc.stats.keys():
				var g: String = STAT_TO_GROUP.get(s, "")
				if g != "":
					market_groups[g] = market_groups.get(g, 0) + 1
		if market_groups.is_empty():
			target_group = "CONNECTION"
		else:
			target_group = market_groups.keys().reduce(
				func(a,b): return a if market_groups[a] >= market_groups[b] else b)
	else:
		target_group = dom_count.keys().reduce(
			func(a,b): return a if dom_count[a] >= dom_count[b] else b)

	var sm = player.synergy_matrix if "synergy_matrix" in player else null

	var affordable: Array = econ["candidates"].filter(
		func(c): return CARD_COSTS.get(c.rarity,99) <= player.gold)

	var _score: Callable = func(c) -> float:
		var group_match: float = 0.0
		for s in c.stats.keys():
			if STAT_TO_GROUP.get(s,"") == target_group:
				group_match += 4.0
		var passive_compat: float = 2.0 if c.category in board_categories else 0.0
		var matrix_sc: float = 0.0
		if sm != null:
			matrix_sc = minf(3.0, sm.synergy_score(c.name, board_card_names) * 0.5)
		var tavan: float = 36.0  # ortalama tavan
		var power_norm: float = (c.total_power() / tavan) * maxf(0.0, pw)
		return (group_match + passive_compat + matrix_sc) * cw + power_norm
	affordable.sort_custom(func(a, b):
		return _score.call(a) > _score.call(b))

	if econ["ratio_floor"] != null:
		var ratio_floor: float = econ["ratio_floor"]
		affordable = affordable.filter(func(c):
			var cost: int = CARD_COSTS.get(c.rarity,1)
			return cost > 0 and (float(c.total_power()) / cost) >= ratio_floor)

	for card in affordable.slice(0, econ["buy_count"]):
		player.buy_card(card, market_obj, trigger_passive_fn)


func _buy_evolver(player, market: Array, market_obj, _rng: RandomNumberGenerator,
				  trigger_passive_fn: Callable) -> void:
	var owned: Dictionary = player.copies
	var gold: int = player.gold
	var evo_near: float = get_param("evolver","evo_near_bonus", 1000.0)
	var evo_one:  float = get_param("evolver","evo_one_bonus",   500.0)
	var rw_mult:  float = get_param("evolver","rarity_weight_mult", 10.0)
	var pw:       float = get_param("evolver","power_weight", 1.0)
	var rmap: Dictionary = {"1":1,"2":2,"3":3,"4":4,"5":5}

	var market_base: Array = market.filter(
		func(c): return CARD_COSTS.get(c.rarity,99) <= gold and c.rarity != "E")
	if market_base.is_empty():
		return

	var focus_score: Callable = func(c) -> float:
		var count: int = owned.get(c.name, 0)
		if owned.get("Evolved " + c.name, 0) > 0:
			return -1.0
		var rv: float = rmap.get(c.rarity, 0)
		if count == 2:
			return evo_near + rv * rw_mult + c.total_power() * pw
		elif count == 1:
			return evo_one  + rv * rw_mult + c.total_power() * pw
		else:
			return rv * rw_mult + c.total_power() * pw

	var best = market_base.reduce(
		func(a,b): return a if focus_score.call(a) >= focus_score.call(b) else b)
	if focus_score.call(best) < 0.0:
		best = market_base.reduce(
			func(a,b): return a if a.total_power() >= b.total_power() else b)
	player.buy_card(best, market_obj, trigger_passive_fn)

	if player.gold >= 4:
		var remaining: Array = market_base.filter(func(c): return c.name != best.name)
		var second_cands: Array = remaining.filter(func(c):
			return owned.get(c.name, 0) >= 1 and owned.get("Evolved "+c.name, 0) == 0)
		if not second_cands.is_empty():
			var second = second_cands.reduce(
				func(a,b): return a if focus_score.call(a) >= focus_score.call(b) else b)
			player.buy_card(second, market_obj, trigger_passive_fn)


func _buy_economist(player, market: Array, market_obj, _rng: RandomNumberGenerator,
					trigger_passive_fn: Callable) -> void:
	var econ: Dictionary = _economy_phase_controls(player, market, 1, "economist")
	if econ["candidates"].is_empty() or econ["buy_count"] <= 0:
		return
	var affordable: Array = econ["candidates"].filter(
		func(c): return CARD_COSTS.get(c.rarity,99) <= player.gold)
	affordable.sort_custom(func(a,b): return a.total_power() > b.total_power())
	if econ["ratio_floor"] != null:
		var ratio_floor: float = econ["ratio_floor"]
		affordable = affordable.filter(func(c):
			var cost: int = CARD_COSTS.get(c.rarity,1)
			return cost > 0 and (float(c.total_power()) / cost) >= ratio_floor)
	for card in affordable.slice(0, econ["buy_count"]):
		player.buy_card(card, market_obj, trigger_passive_fn)


func _buy_balancer(player, market: Array, market_obj, _rng: RandomNumberGenerator,
				   trigger_passive_fn: Callable) -> void:
	var group_bonus:  float = get_param("balancer","group_bonus",  5.0)
	var group_thresh: int   = int(get_param("balancer","group_thresh",3.0))
	var pw:           float = get_param("balancer","power_weight", 1.0)

	var board_groups: Dictionary = {}
	for card in player.board.alive_cards():
		var g: String = card.dominant_group()
		board_groups[g] = board_groups.get(g, 0) + 1

	var affordable: Array = market.filter(
		func(c): return CARD_COSTS.get(c.rarity,99) <= player.gold)
	var _s: Callable = func(c) -> float:
		var bonus: float = group_bonus if board_groups.get(c.dominant_group(),0) < group_thresh else 0.0
		return c.total_power() * pw + bonus
	affordable.sort_custom(func(a, b):
		return _s.call(a) > _s.call(b))
	for card in affordable.slice(0, 1):
		player.buy_card(card, market_obj, trigger_passive_fn)


func _buy_rare_hunter(player, market: Array, market_obj, _rng: RandomNumberGenerator,
					  trigger_passive_fn: Callable) -> void:
	var gold: int = player.gold
	var fb_rarity: String = str(int(clamp(
		round(get_param("rare_hunter","fallback_rarity",3.0)), 1, 4)))

	if gold >= CARD_COSTS.get("5",8):
		var r5: Array = market.filter(func(c): return c.rarity == "5")
		if not r5.is_empty():
			var best = r5.reduce(func(a,b): return a if a.total_power()>=b.total_power() else b)
			player.buy_card(best, market_obj, trigger_passive_fn)
			return

	if gold >= CARD_COSTS.get("4",5):
		var r4: Array = market.filter(func(c): return c.rarity == "4")
		r4.sort_custom(func(a,b): return a.total_power() > b.total_power())
		for card in r4.slice(0,1):
			player.buy_card(card, market_obj, trigger_passive_fn)
		if not r4.is_empty():
			return

	var rfb: Array = market.filter(func(c):
		return c.rarity == fb_rarity and CARD_COSTS.get(c.rarity,99) <= gold)
	rfb.sort_custom(func(a,b): return a.total_power() > b.total_power())
	for card in rfb.slice(0,1):
		player.buy_card(card, market_obj, trigger_passive_fn)


# ================================================================
# Yerleştirme stratejileri
# ================================================================

func _combo_score_at(coord: Vector2i, card, grid: Dictionary) -> int:
	var cg: String = card.dominant_group()
	var score: int = 0
	for d in HEX_DIRS:
		var nb = grid.get(coord + d)
		if nb != null and nb.dominant_group() == cg:
			score += 1
	return score


func _place_smart_default(player, rng: RandomNumberGenerator) -> void:
	var free: Array = player.board.free_coords()
	if free.is_empty():
		return
	var grid: Dictionary = player.board.grid
	var strategy: String = player.strategy

	var sorted_cards: Array = player.hand.duplicate()
	if strategy in ["warrior","rare_hunter"]:
		sorted_cards.sort_custom(func(a,b): return a.total_power() > b.total_power())
	elif strategy == "evolver":
		sorted_cards.sort_custom(func(a,b):
			var sa: int = 1 if a.rarity=="E" else 0
			var sb: int = 1 if b.rarity=="E" else 0
			if sa != sb: return sa > sb
			return a.total_power() > b.total_power())
	else:
		sorted_cards.sort_custom(func(a,b): return a.total_power() > b.total_power())

	var center_coords: Array = [Vector2i(0,0)]
	for d in HEX_DIRS:
		center_coords.append(d)

	var placed: int = 0
	for card in sorted_cards:
		if placed >= PLACE_PER_TURN or free.is_empty():
			break

		var target: Vector2i
		if strategy == "random" and rng.randf() < 0.5:
			target = free[rng.randi_range(0, free.size()-1)]
		else:
			var best_coord: Vector2i = free[0]
			var best_score: float = -1.0
			for coord in free:
				var cs: float = _combo_score_at(coord, card, grid)
				if strategy in ["warrior","rare_hunter"]:
					if card.total_power() >= 42 and coord in center_coords:
						cs += 0.5
				if cs > best_score:
					best_score = cs
					best_coord = coord
			target = best_coord

		player.board.place(target, card)
		free.erase(target)
		player.hand.erase(card)
		placed += 1


func _place_fast_synergy(player) -> void:
	"""Builder için hızlı sinerji yerleşimi (lookahead olmadan)."""
	var free: Array = player.board.free_coords()
	if free.is_empty():
		return
	var grid: Dictionary = player.board.grid
	var sm = player.synergy_matrix if "synergy_matrix" in player else null

	var center_ring: Array = [Vector2i(0,0)]
	for d in HEX_DIRS:
		center_ring.append(d)

	var _passive_score: Callable = func(coord: Vector2i, card) -> int:
		var s: int = 0
		for d in HEX_DIRS:
			var nb = grid.get(coord + d)
			if nb != null and nb.category == card.category:
				s += 1
		return s

	var _matrix_score: Callable = func(coord: Vector2i, card) -> float:
		if sm == null: return 0.0
		var neighbor_names: Array = []
		for d in HEX_DIRS:
			var nb = grid.get(coord + d)
			if nb != null: neighbor_names.append(nb.name)
		return sm.synergy_score(card.name, neighbor_names) * 0.5

	var placed: int = 0
	for card in player.hand.duplicate():
		if placed >= PLACE_PER_TURN or free.is_empty():
			break
		var best_coord: Vector2i = free[0]
		var best_sc: float = -1.0
		for coord in free.slice(0, MAX_COORD_CHECK):
			var sc: float = (_combo_score_at(coord, card, grid) * 5.0
				+ _passive_score.call(coord, card) * 4.0
				+ (2.0 if coord in center_ring else 0.0)
				+ _matrix_score.call(coord, card))
			if sc > best_sc:
				best_sc = sc
				best_coord = coord
		player.board.place(best_coord, card)
		free.erase(best_coord)
		player.hand.erase(card)
		placed += 1
		if sm != null:
			sm.update_from_board(player.board)


func _place_aggressive(player, power_center_thresh: float, combo_center_weight: float) -> void:
	"""Tempo stratejisi: güçlü kartı merkeze koy, yüksek combo varsa kenara."""
	var free: Array = player.board.free_coords()
	if free.is_empty():
		return
	var grid: Dictionary = player.board.grid

	var center_coords: Array = [Vector2i(0,0)]
	for d in HEX_DIRS:
		center_coords.append(d)

	var sorted_cards: Array = player.hand.duplicate()
	sorted_cards.sort_custom(func(a,b): return a.total_power() > b.total_power())

	var placed: int = 0
	for card in sorted_cards:
		if placed >= PLACE_PER_TURN or free.is_empty():
			break
		var power: float = card.total_power()
		var target: Vector2i

		if power >= power_center_thresh:
			var center_free: Array = free.filter(func(c): return c in center_coords)
			var rim_free: Array    = free.filter(func(c): return not (c in center_coords))

			var best_center: Vector2i = center_free[0] if not center_free.is_empty() else Vector2i(-99,-99)
			var center_combo: int  = _combo_score_at(best_center, card, grid) if not center_free.is_empty() else -1

			var best_rim: Vector2i = Vector2i(-99,-99)
			var has_best_rim: bool = false
			var best_rim_combo: int = -1
			for rc in rim_free:
				var cs: int = _combo_score_at(rc, card, grid)
				if cs > best_rim_combo:
					best_rim_combo = cs
					best_rim = rc
					has_best_rim = true

			if has_best_rim and best_rim_combo > center_combo * combo_center_weight:
				target = best_rim
			elif not center_free.is_empty():
				target = best_center
			else:
				target = free[free.size()-1]
		else:
			var best_coord: Vector2i = free[0]
			var best_cs: int = -1
			for rc in free:
				var cs: int = _combo_score_at(rc, card, grid)
				if cs > best_cs: best_cs = cs; best_coord = rc
			target = best_coord

		player.board.place(target, card)
		free.erase(target)
		player.hand.erase(card)
		placed += 1
