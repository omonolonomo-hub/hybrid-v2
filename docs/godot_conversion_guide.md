# Godot Conversion Guide - Python to GDScript

This guide helps you convert the Python game systems to Godot Engine (GDScript).

## Already Completed ✓
- `market.gd` - Market system (from `engine_core/market.py`)
- `game.gd` - Game loop and flow (from `engine_core/game.py`)

## Missing Systems (Connection Points)

Your Godot code needs these three systems to complete the game:

### 1. Combat System (`combat_phase_fn`)
**Python Source**: `engine_core/board.py`
**Godot Target**: `combat_resolver.gd`

### 2. Passive System (`trigger_passive_fn`)
**Python Source**: `engine_core/passive_trigger.py`
**Godot Target**: `passive_system.gd`

### 3. AI System (`_ai`)
**Python Source**: `engine_core/ai.py`
**Godot Target**: `ai.gd`

---

## 1. Combat System Conversion

### Python Functions to Convert

#### Core Combat Functions (from `engine_core/board.py`)

```python
# 1. resolve_single_combat(card_a, card_b, bonus_a, bonus_b) -> (a_wins, b_wins)
#    Compares two cards at one coordinate, returns edge win counts
#    Includes _ prefix bonuses distributed across edges

# 2. combat_phase(board_a, board_b, combo_bonus_a, combo_bonus_b, 
#                 player_a, player_b, ctx) -> (kill_pts_a, kill_pts_b, draws)
#    Resolves combat at every overlapping coordinate
#    Triggers passive abilities, removes eliminated cards

# 3. find_combos(board) -> (combo_points, combat_bonus)
#    Finds combo matches between neighboring cards
#    Returns combo points and edge bonuses for combat

# 4. calculate_group_synergy_bonus(board) -> int
#    Calculates synergy bonus based on group composition
#    Moderated scaling with diversity bonus

# 5. calculate_damage(winner_pts, loser_pts, winner_board, turn) -> int
#    Calculates damage with turn-based multiplier
#    Early game protection (turns 1-10 capped at 15 damage)
```

### GDScript Structure (`combat_resolver.gd`)

```gdscript
extends Node
class_name CombatResolver

# Constants (import from your constants.gd)
const HEX_DIRS = [...]  # 6 hex directions
const OPP_DIR = {...}   # Opposite direction map
const STAT_TO_GROUP = {...}  # Stat to group mapping
const GROUP_BEATS = {...}  # Rock-paper-scissors
const RARITY_DMG_BONUS = {...}  # Rarity damage bonuses
const KILL_PTS = 10  # Points for killing a card

# Core combat resolution
func resolve_single_combat(card_a: Card, card_b: Card, 
                          bonus_a: Dictionary = {}, 
                          bonus_b: Dictionary = {}) -> Array:
	# Returns [a_wins, b_wins]
	var a_wins = 0
	var b_wins = 0
	
	# Calculate _ prefix bonuses (e.g., _yggdrasil_bonus, _pulsar_buff)
	var bonus_total_a = 0
	var bonus_total_b = 0
	for stat_key in card_a.stats:
		if str(stat_key).begins_with("_") and typeof(card_a.stats[stat_key]) == TYPE_INT:
			bonus_total_a += card_a.stats[stat_key]
	for stat_key in card_b.stats:
		if str(stat_key).begins_with("_") and typeof(card_b.stats[stat_key]) == TYPE_INT:
			bonus_total_b += card_b.stats[stat_key]
	
	# Distribute bonuses evenly across edges
	var bonus_per_edge_a = int(bonus_total_a / 6) if bonus_total_a > 0 else 0
	var bonus_per_edge_b = int(bonus_total_b / 6) if bonus_total_b > 0 else 0
	
	var edges_a = card_a.rotated_edges()
	var edges_b = card_b.rotated_edges()
	
	for d in range(6):
		var va = edges_a[d][1] if d < edges_a.size() else 0
		var vb = edges_b[d][1] if d < edges_b.size() else 0
		va += bonus_a.get(d, 0) + bonus_per_edge_a
		vb += bonus_b.get(d, 0) + bonus_per_edge_b
		
		# Group advantage (rock-paper-scissors)
		if va > 0 and vb > 0:
			var ga = STAT_TO_GROUP.get(edges_a[d][0]) if d < edges_a.size() else null
			var gb = STAT_TO_GROUP.get(edges_b[d][0]) if d < edges_b.size() else null
			if ga and gb:
				if GROUP_BEATS.get(ga) == gb:
					va += 1
				elif GROUP_BEATS.get(gb) == ga:
					vb += 1
		
		if va > vb:
			a_wins += 1
		elif vb > va:
			b_wins += 1
	
	return [a_wins, b_wins]

func find_combos(board: Board) -> Array:
	# Returns [combo_points, combat_bonus]
	var combo_points = 0
	var combat_bonus = {}  # {coord: {direction: +1}}
	var counted = {}  # Track counted pairs
	
	var grid = board.grid
	for coord in grid:
		var card = grid[coord]
		var card_group = card.dominant_group()
		
		for neighbor_data in board.neighbors(coord):
			var neighbor_coord = neighbor_data[0]
			var direction = neighbor_data[1]
			
			# Create pair key (sorted to avoid duplicates)
			var pair_key = str(min(coord, neighbor_coord)) + "_" + str(max(coord, neighbor_coord))
			if counted.has(pair_key):
				continue
			
			var neighbor_card = grid[neighbor_coord]
			var neighbor_group = neighbor_card.dominant_group()
			
			if card_group == neighbor_group:
				combo_points += 1
				var opp = OPP_DIR[direction]
				
				if not combat_bonus.has(coord):
					combat_bonus[coord] = {}
				if not combat_bonus.has(neighbor_coord):
					combat_bonus[neighbor_coord] = {}
				
				combat_bonus[coord][direction] = combat_bonus[coord].get(direction, 0) + 1
				combat_bonus[neighbor_coord][opp] = combat_bonus[neighbor_coord].get(opp, 0) + 1
			
			counted[pair_key] = true
	
	return [combo_points, combat_bonus]

func calculate_group_synergy_bonus(board: Board) -> int:
	# Count cards per group
	var group_count = {}
	for card in board.grid.values():
		var comp = card.get_group_composition()
		for group_name in comp:
			group_count[group_name] = group_count.get(group_name, 0) + 1
	
	# Group bonus: 3 * (n-1)^1.25, capped at 18 per group
	var group_bonus = 0
	for count in group_count.values():
		if count >= 2:
			var bonus = 3 * pow(count - 1, 1.25)
			group_bonus += min(18, int(bonus))
	
	# Diversity bonus: +1 per unique group (max +5)
	var unique_groups = 0
	for count in group_count.values():
		if count > 0:
			unique_groups += 1
	var diversity_bonus = min(5, unique_groups)
	
	return group_bonus + diversity_bonus

func calculate_damage(winner_pts: int, loser_pts: int, 
                     winner_board: Board, turn: int = 99) -> int:
	var base = abs(winner_pts - loser_pts)
	var alive = int(winner_board.alive_count() / 2)
	var rarity = int(winner_board.rarity_bonus() / 2)
	var raw_damage = max(1, base + alive + rarity)
	
	# Turn-based damage multiplier (early game protection)
	var turn_multiplier = 1.0
	if turn <= 5:
		turn_multiplier = 0.5
	elif turn <= 15:
		turn_multiplier = 0.5 + ((turn - 5) * 0.05)
	else:
		turn_multiplier = 1.0
	
	var scaled_damage = int(raw_damage * turn_multiplier)
	var final_damage = max(1, scaled_damage)
	
	# Hard cap for early game (turns 1-10)
	if turn <= 10:
		final_damage = min(final_damage, 15)
	
	return final_damage

func combat_phase(board_a: Board, board_b: Board,
                 combo_bonus_a: Dictionary, combo_bonus_b: Dictionary,
                 player_a, player_b, ctx: Dictionary,
                 trigger_passive_fn: FuncRef) -> Array:
	# Returns [kill_pts_a, kill_pts_b, draws]
	var kill_a = 0
	var kill_b = 0
	var draws = 0
	
	var grid_a = board_a.grid
	var grid_b = board_b.grid
	
	# Find overlapping coordinates
	var shared_coords = []
	for coord in grid_a:
		if grid_b.has(coord):
			shared_coords.append(coord)
	
	for coord in shared_coords:
		if not grid_a.has(coord) or not grid_b.has(coord):
			continue
		
		var card_a = grid_a[coord]
		var card_b = grid_b[coord]
		
		var ba = combo_bonus_a.get(coord, {})
		var bb = combo_bonus_b.get(coord, {})
		
		var result = resolve_single_combat(card_a, card_b, ba, bb)
		var a_wins = result[0]
		var b_wins = result[1]
		
		if a_wins > b_wins:
			# A wins
			kill_a += trigger_passive_fn.call_func(card_a, "combat_win", player_a, player_b, ctx, false)
			kill_b += trigger_passive_fn.call_func(card_b, "combat_lose", player_b, player_a, ctx, false)
			
			card_b.lose_highest_edge()
			if card_b.is_eliminated():
				trigger_passive_fn.call_func(card_b, "card_killed", player_b, player_a, ctx, false)
				board_b.remove(coord)
				kill_a += KILL_PTS
		
		elif b_wins > a_wins:
			# B wins
			kill_b += trigger_passive_fn.call_func(card_b, "combat_win", player_b, player_a, ctx, false)
			kill_a += trigger_passive_fn.call_func(card_a, "combat_lose", player_a, player_b, ctx, false)
			
			card_a.lose_highest_edge()
			if card_a.is_eliminated():
				trigger_passive_fn.call_func(card_a, "card_killed", player_a, player_b, ctx, false)
				board_a.remove(coord)
				kill_b += KILL_PTS
		
		else:
			# Draw
			draws += 1
	
	return [kill_a, kill_b, draws]
```

---

## 2. Passive System Conversion

### Python Functions to Convert (from `engine_core/passive_trigger.py`)

```python
# 1. trigger_passive(card, trigger, owner, opponent, ctx, verbose) -> int
#    Main entry point - triggers a card's passive ability
#    Returns bonus combat points or 0 for side-effect-only passives
#    Logs passive triggers and updates strategy logger

# 2. _trigger_passive_impl(card, trigger, owner, opponent, ctx) -> int
#    Internal implementation - checks PASSIVE_HANDLERS registry
#    Falls back to default behaviors for passive types
```

### GDScript Structure (`passive_system.gd`)

```gdscript
extends Node
class_name PassiveSystem

# Passive trigger log (for statistics)
var _passive_trigger_log = {}

# Passive handlers registry (populated by passive implementations)
var PASSIVE_HANDLERS = {}

func _init():
	_passive_trigger_log = {}
	# Register passive handlers here or load from separate files
	# PASSIVE_HANDLERS["Card Name"] = funcref(self, "_handler_card_name")

func trigger_passive(card: Card, trigger: String, 
                    owner, opponent, ctx: Dictionary, 
                    verbose: bool = false) -> int:
	"""Main entry point for triggering passive abilities"""
	var safe_name = card.name  # GDScript handles Unicode better
	if verbose:
		print("[PASSIVE] %s | %s" % [safe_name, trigger])
	
	var power_before = card.total_power()
	var res = _trigger_passive_impl(card, trigger, owner, opponent, ctx)
	var delta = card.total_power() - power_before
	
	if verbose:
		print("[EFFECT] %s -> %d" % [safe_name, res])
	
	# Log passive trigger
	if not _passive_trigger_log.has(safe_name):
		_passive_trigger_log[safe_name] = {}
	_passive_trigger_log[safe_name][trigger] = _passive_trigger_log[safe_name].get(trigger, 0) + 1
	
	# Log buff to owner if strengthening occurred
	if delta > 0 and owner != null and owner.has("passive_buff_log"):
		owner.passive_buff_log.append({
			"turn": ctx.get("turn", 0),
			"card": card.name,
			"passive": card.passive_type,
			"trigger": trigger,
			"delta": delta
		})
	
	# Strategy logger hook (if you have one)
	# _log_to_strategy_logger(card, trigger, owner, delta, ctx)
	
	return res

func _trigger_passive_impl(card: Card, trigger: String,
                          owner, opponent, ctx: Dictionary) -> int:
	"""Internal implementation - checks handlers and defaults"""
	var pt = card.passive_type
	if pt == "none":
		return 0
	
	var turn = ctx.get("turn", 1)
	
	# Check if card has a specific handler
	if PASSIVE_HANDLERS.has(card.name):
		var handler = PASSIVE_HANDLERS[card.name]
		return handler.call_func(card, trigger, owner, opponent, ctx)
	
	# Default behaviors for passive types without specific handlers
	if pt == "copy" and (trigger == "copy_2" or trigger == "copy_3"):
		# Default: +1 to highest edge
		if card.edges.size() > 0:
			var max_idx = 0
			var max_val = card.edges[0][1]
			for i in range(card.edges.size()):
				if card.edges[i][1] > max_val:
					max_val = card.edges[i][1]
					max_idx = i
			var s = card.edges[max_idx][0]
			var v = card.edges[max_idx][1]
			card.edges[max_idx] = [s, v + 1]
			card.stats[s] = v + 1
		return 0
	
	return 0

func get_passive_trigger_log() -> Dictionary:
	"""Return current passive trigger log"""
	return _passive_trigger_log

func clear_passive_trigger_log():
	"""Clear passive trigger log"""
	_passive_trigger_log = {}
```

---

## 3. AI System Conversion

### Python Functions to Convert (from `engine_core/ai.py`)

The AI system is the most complex. It has:
- **8 buying strategies**: random, warrior, builder, evolver, economist, balancer, rare_hunter, tempo
- **3 placement strategies**: smart_default, fast_synergy, aggressive

### GDScript Structure (`ai.gd`)

```gdscript
extends Node
class_name AI

# Constants
const MAX_LOOKAHEAD_CARDS = 4
const MAX_COORD_CHECK = 8
const PLACEMENT_TIME_BUDGET_S = 0.05

# Main entry points
static func buy_cards(player: Player, market: Array, max_cards: int = 1,
                     market_obj = null, rng = null, 
                     trigger_passive_fn: FuncRef = null,
                     ai_instance = null):
	"""Buy from market according to player.strategy"""
	if rng == null:
		rng = RandomNumberGenerator.new()
		rng.randomize()
	
	match player.strategy:
		"random":
			_buy_random(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance)
		"warrior":
			_buy_warrior(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance)
		"builder":
			_buy_builder(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance)
		"evolver":
			_buy_evolver(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance)
		"economist":
			_buy_economist(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance)
		"balancer":
			_buy_balancer(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance)
		"rare_hunter":
			_buy_rare_hunter(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance)
		"tempo":
			_buy_warrior(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance)
		_:
			_buy_random(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance)

static func place_cards(player: Player, rng = null,
                       power_center_thresh: float = 45.0,
                       combo_center_weight: float = 1.5):
	"""Place hand cards onto the board per strategy"""
	match player.strategy:
		"builder":
			_place_fast_synergy(player)
		"tempo":
			_place_aggressive(player, power_center_thresh, combo_center_weight)
		_:
			_place_smart_default(player, rng)

# Buying strategies (simplified examples - see Python for full logic)
static func _buy_random(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance):
	var budget = player.gold
	var affordable = []
	for card in market:
		if CARD_COSTS[card.rarity] <= budget:
			affordable.append(card)
	affordable.shuffle()
	for i in range(min(max_cards, affordable.size())):
		player.buy_card(affordable[i], market_obj, trigger_passive_fn)

static func _buy_warrior(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance):
	# Sort by total_power, buy highest
	var affordable = []
	for card in market:
		if CARD_COSTS[card.rarity] <= player.gold:
			affordable.append(card)
	affordable.sort_custom(self, "_sort_by_power")
	for i in range(min(max_cards, affordable.size())):
		player.buy_card(affordable[i], market_obj, trigger_passive_fn)

static func _sort_by_power(a: Card, b: Card) -> bool:
	return a.total_power() > b.total_power()

# ... (implement other buying strategies following Python logic)

# Placement strategies
static func _place_smart_default(player, rng):
	"""Smart placement for most strategies"""
	if rng == null:
		rng = RandomNumberGenerator.new()
		rng.randomize()
	
	var free = player.board.free_coords()
	if free.empty():
		return
	
	var grid = player.board.grid
	var strategy = player.strategy
	
	# Sort hand by power (or strategy-specific logic)
	var sorted_cards = player.hand.duplicate()
	sorted_cards.sort_custom(self, "_sort_by_power")
	
	var placed = 0
	for card in sorted_cards:
		if placed >= PLACE_PER_TURN or free.empty():
			break
		
		# Find best coordinate based on combo score
		var best_coord = null
		var best_score = -1
		
		for coord in free:
			var score = _combo_score_at(coord, card, grid)
			if score > best_score:
				best_score = score
				best_coord = coord
		
		var target = best_coord if best_coord != null else free[free.size() - 1]
		player.board.place(target, card)
		free.erase(target)
		player.hand.erase(card)
		placed += 1

static func _combo_score_at(coord: Vector2, card: Card, grid: Dictionary) -> int:
	"""Count neighbors with matching dominant group"""
	var card_group = card.dominant_group()
	var q = coord.x
	var r = coord.y
	var score = 0
	
	for dir in HEX_DIRS:
		var nbr_coord = Vector2(q + dir[0], r + dir[1])
		if grid.has(nbr_coord):
			var nbr = grid[nbr_coord]
			if nbr.dominant_group() == card_group:
				score += 1
	
	return score

# ... (implement other placement strategies)
```

---

## Key Differences: Python vs GDScript

### 1. Data Structures
- **Python**: `dict`, `list`, `tuple`, `set`
- **GDScript**: `Dictionary`, `Array`, `Array` (no tuple), `Dictionary` (no set)

### 2. Type Hints
- **Python**: `def func(x: int) -> str:`
- **GDScript**: `func func(x: int) -> String:`

### 3. None vs null
- **Python**: `None`
- **GDScript**: `null`

### 4. String Formatting
- **Python**: `f"Player {pid}"`
- **GDScript**: `"Player %d" % pid` or `"Player {0}".format([pid])`

### 5. Lambda Functions
- **Python**: `lambda x: x.power`
- **GDScript**: Use `FuncRef` or custom sorter methods

### 6. Dictionary Methods
- **Python**: `dict.get(key, default)`
- **GDScript**: `dict.get(key, default)` (same!)

### 7. List Comprehensions
- **Python**: `[x for x in list if x > 0]`
- **GDScript**: Use loops or `filter()` method

---

## Integration Steps

### Step 1: Create the Three GDScript Files
1. `combat_resolver.gd` - Combat system
2. `passive_system.gd` - Passive abilities
3. `ai.gd` - AI strategies

### Step 2: Update Your `game.gd`
Replace the placeholder function references:

```gdscript
# In game.gd __init__:
var combat_resolver = CombatResolver.new()
var passive_system = PassiveSystem.new()
var ai_system = AI.new()

# Create FuncRefs
combat_phase_fn = funcref(combat_resolver, "combat_phase")
trigger_passive_fn = funcref(passive_system, "trigger_passive")
_ai = ai_system  # Use AI class directly
```

### Step 3: Test Each System Independently
1. Test combat resolution with simple boards
2. Test passive triggers with test cards
3. Test AI buying/placement with mock data

### Step 4: Integration Testing
Run full games and compare results with Python version

---

## Next Steps

Which system would you like me to help convert first?

1. **Combat System** - Core battle resolution
2. **Passive System** - Card abilities
3. **AI System** - Strategy behaviors
4. **All Systems** - Complete documentation for all three

Let me know and I'll provide detailed conversion code!
