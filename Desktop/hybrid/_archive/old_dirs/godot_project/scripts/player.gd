## player.gd  –  Autochess Hybrid Godot 4 Port
## engine_core/player.py karşılığı
class_name Player

var pid:          int
var strategy:     String
var hp:           int
var gold:         int = 0
var board:        HexBoard
var hand:         Array = []      # Card[]
var copies:       Dictionary = {} # card_name -> count
var copy_turns:   Dictionary = {}
var copy_applied: Dictionary = {}
var turn_pts:     int = 0
var total_pts:    int = 0
var alive:        bool = true
var win_streak:   int = 0
var turns_played: int = 0
var evolved_card_names: Array = []
var passive_buff_log:   Array = []  # [{turn,card,passive,trigger,delta}]
var synergy_matrix = null            # BuilderSynergyMatrix veya null
var card_turns_alive:   Dictionary = {}   # card_name -> board'da geçirilen tur sayısı
var evolution_turns:    Array = []         # evrim ateşlendiğindeki tur numaraları
var _window_bought:     Array = []

var stats: Dictionary = {
	"wins":0,"losses":0,"draws":0,
	"kills":0,"damage_dealt":0,"damage_taken":0,
	"synergy_sum":0,"synergy_turns":0,
	"gold_spent":0,"gold_earned":0,
	"combo_triggers":0,"synergy_trigger_count":0,
	"gold_per_turn":0,"win_streak_max":0,
	"market_rolls":0,"copies_created":0,
	"board_power":0,"unit_count":0,
}

func _init(p_pid: int, p_strategy: String = "random") -> void:
	pid      = p_pid
	strategy = p_strategy
	hp       = Constants.STARTING_HP
	board    = HexBoard.new()

# ── Gelir ──────────────────────────────────────────────────────────
func income() -> void:
	var streak_bonus := int(win_streak / 3.0)
	var hp_bonus := 0
	if hp < 45:  hp_bonus = 3
	elif hp < 75: hp_bonus = 1
	var earned := Constants.BASE_INCOME + streak_bonus + hp_bonus
	gold  += earned
	stats["gold_earned"] += earned
	turns_played += 1

func apply_interest() -> void:
	var cap := Constants.MAX_INTEREST
	var mult := 1.5 if strategy == "economist" else 1.0
	var interest: int = mini(cap, int(float(gold) / float(Constants.INTEREST_STEP)))
	if mult > 1.0:
		interest = mini(cap + 3, int(float(interest) * mult) + 1)
	gold += interest
	stats["gold_earned"] += interest

# ── Kart Satın Alma ────────────────────────────────────────────────
func buy_card(card: Card, market = null, _trigger_passive_fn: Callable = Callable()) -> bool:
	var cost: int = Constants.CARD_COSTS.get(card.rarity, 99)
	if gold < cost:
		return false
	gold -= cost
	stats["gold_spent"] += cost
	var cloned := card.clone()
	hand.append(cloned)
	copies[card.name] = copies.get(card.name, 0) + 1
	_window_bought.append(card.name)
	# El taşması
	if hand.size() > Constants.HAND_LIMIT:
		var dropped: Card = hand.pop_front()
		if copies.get(dropped.name, 0) > 0:
			copies[dropped.name] -= 1
		if market != null:
			market.return_one(dropped.name)
	return true

# ── Hasar / Ölüm ────────────────────────────────────────────────────
func take_damage(amount: int) -> void:
	hp = max(0, hp - amount)
	stats["damage_taken"] += amount
	if hp <= 0:
		alive = false

# ── Copy Güçlendirme ────────────────────────────────────────────────
func check_copy_strengthening(turn: int, trigger_passive_fn = null) -> void:
	var thresholds := Constants.COPY_THRESH_C if board.has_catalyst else Constants.COPY_THRESH
	var thresh_2: int = thresholds[0]
	var thresh_3: int = thresholds[1]

	for card_name in copies:
		var count: int = copies[card_name]
		var on_board := false
		for c in board.grid.values():
			if c.name == card_name:
				on_board = true; break
		if not on_board: continue

		var t: int = copy_turns.get(card_name, 0) + 1
		copy_turns[card_name] = t

		if not copy_applied.has(card_name):
			copy_applied[card_name] = {"2": false, "3": false}

		if count >= 2 and t >= thresh_2 and not copy_applied[card_name]["2"]:
			for c in board.grid.values():
				if c.name == card_name:
					c.strengthen(2)
					passive_buff_log.append({"turn":turn,"card":card_name,
						"passive":"copy_strengthen","trigger":"copy_2","delta":2})
					if trigger_passive_fn != null:
						trigger_passive_fn.call(c, "copy_2", self, null, {"turn": turn}, false)
			copy_applied[card_name]["2"] = true
			stats["copies_created"] += 1

		if count >= 3 and t >= thresh_3 and not copy_applied[card_name]["3"]:
			for c in board.grid.values():
				if c.name == card_name:
					c.strengthen(3)
					passive_buff_log.append({"turn":turn,"card":card_name,
						"passive":"copy_strengthen","trigger":"copy_3","delta":3})
					if trigger_passive_fn != null:
						trigger_passive_fn.call(c, "copy_3", self, null, {"turn": turn}, false)
			copy_applied[card_name]["3"] = true
			stats["copies_created"] += 1

func _to_string() -> String:
	return "P%d[%s] HP=%d pts=%d" % [pid, strategy, hp, total_pts]

# ── Kartı elle board'a yerleştir (UI için) ────────────────────────────
func place_card_on_board(card: Card, coord: Vector2i) -> bool:
	if board.grid.has(coord):
		return false  # dolu hex
	var idx: int = hand.find(card)
	if idx == -1:
		return false  # elde yok
	hand.remove_at(idx)
	board.place(coord, card)
	return true

# ── Evrim Kontrolü (evolver stratejisi için) ─────────────────────────
func check_evolution(market = null, card_by_name: Dictionary = {}) -> Array:
	if strategy != "evolver":
		return []

	var evolved_names: Array = []
	for base_name in copies.keys().duplicate():
		var count: int = copies.get(base_name, 0)
		if count < Constants.EVOLVE_COPIES_REQUIRED:
			continue
		var evolved_key: String = "Evolved " + base_name
		if copies.get(evolved_key, 0) > 0:
			continue
		if not card_by_name.has(base_name):
			continue
		var base_template: Card = card_by_name[base_name]

		# El'den 2 kopya çıkar
		var removed: int = 0
		var i: int = 0
		while i < hand.size() and removed < 2:
			if hand[i].name == base_name:
				hand.remove_at(i)
				removed += 1
				if market != null:
					market.pool_copies[base_name] = market.pool_copies.get(base_name, 0) + 1
			else:
				i += 1

		# Hala yetmiyorsa board'dan al
		if removed < 2:
			for coord in board.grid.keys().duplicate():
				if removed >= 2: break
				var c: Card = board.grid[coord]
				if c.name == base_name:
					board.remove(coord)
					removed += 1
					if market != null:
						market.pool_copies[base_name] = market.pool_copies.get(base_name, 0) + 1

		copies[base_name] = maxi(0, copies.get(base_name, 0) - 2)
		var evolved: Card = Card.evolve_card(base_template)

		# Rarity bazlı güç oranı (R3 +12% / R4 +16% / R5 +20%)
		if base_template.rarity.is_valid_int():
			var rarity_int: int = int(base_template.rarity)
			if rarity_int >= 3 and rarity_int <= 5:
				var bonus_pct: float = 0.04 * float(rarity_int)
				var bonus_pts: int = int(round(float(evolved.total_power()) * bonus_pct))
				if bonus_pts > 0:
					evolved.strengthen(bonus_pts)

		# Board'daki kopyasının yerine koy
		var replaced: bool = false
		for coord in board.grid.keys().duplicate():
			var c: Card = board.grid[coord]
			if c.name == base_name:
				board.place(coord, evolved)
				replaced = true; break

		if not replaced:
			var found: bool = false
			for j in range(hand.size()):
				if hand[j].name == base_name:
					hand[j] = evolved; found = true; break
			if not found:
				hand.append(evolved)

		copies[evolved_key] = copies.get(evolved_key, 0) + 1
		stats["evolutions"] = stats.get("evolutions", 0) + 1
		evolved_names.append(base_name)
		evolved_card_names.append(base_name)
		evolution_turns.append(turns_played if turns_played > 0 else 1)

	return evolved_names
