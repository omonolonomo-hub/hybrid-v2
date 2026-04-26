# ================================================================
# AUTOCHESS HYBRID - Market (GDScript 4)
# Shared card pool yönetimi, market window açma/kapama,
# rarity ağırlıklandırma. market.py'nin birebir karşılığı.
# ================================================================
class_name Market
extends RefCounted

# Rarity ağırlık eğrileri: { rarity -> [[min_turn, weight], ...] }
const RARITY_WEIGHT: Dictionary = {
	"1": [[1, 1.0]],
	"2": [[1, 1.0]],
	"3": [[1, 0.3], [5, 0.7], [9, 1.0]],
	"4": [[1, 0.0], [5, 0.2], [10, 0.6], [14, 1.0]],
	"5": [[1, 0.0], [8, 0.1], [13, 0.5], [18, 1.0]],
	"E": [[1, 1.0]],
}

var pool: Array            # List[Card]
var pool_copies: Dictionary  # card_name -> int  (kaç kopya havuzda kaldı)
var _player_windows: Dictionary  # pid -> Array[Card]
var _rng: RandomNumberGenerator
var _current_turn: int = 1


func _init(p_pool: Array, p_rng: RandomNumberGenerator = null) -> void:
	pool = p_pool
	pool_copies = {}
	for card in pool:
		pool_copies[card.name] = 3  # Başlangıçta her kartan 3 kopya
	_player_windows = {}
	_rng = p_rng if p_rng != null else RandomNumberGenerator.new()
	if p_rng == null:
		_rng.randomize()


# ── Rarity ağırlığı ─────────────────────────────────────────────
func _rarity_weight(rarity: String, turn: int) -> float:
	var steps: Array = RARITY_WEIGHT.get(rarity, [[1, 1.0]])
	var w: float = steps[0][1]
	for step in steps:
		if turn >= step[0]:
			w = step[1]
	return w


# ── Ağırlıklı örneklem havuzu ────────────────────────────────────
func _available_weighted(turn: int) -> Array:
	# Döner: [cards_array, weights_array]
	var cards: Array = []
	var weights: Array = []
	for card in pool:
		if pool_copies.get(card.name, 0) <= 0:
			continue
		var w: float = _rarity_weight(card.rarity, turn)
		if w > 0.0:
			cards.append(card)
			weights.append(w)
	return [cards, weights]


func _weighted_sample(cards: Array, weights: Array, k: int) -> Array:
	"""Ağırlıklı rastgele k benzersiz kart seç (yerine koymadan)."""
	if cards.is_empty():
		return []
	k = mini(k, cards.size())
	var result: Array = []
	var rem_cards: Array = cards.duplicate()
	var rem_weights: Array = weights.duplicate()
	for _i in range(k):
		var total: float = 0.0
		for w in rem_weights:
			total += w
		if total <= 0.0:
			break
		var r: float = _rng.randf() * total
		var cumulative: float = 0.0
		var chosen_idx: int = rem_cards.size() - 1
		for i in range(rem_weights.size()):
			cumulative += rem_weights[i]
			if r <= cumulative:
				chosen_idx = i
				break
		result.append(rem_cards[chosen_idx])
		rem_cards.remove_at(chosen_idx)
		rem_weights.remove_at(chosen_idx)
	return result


# ── Oyuncu market penceresi ──────────────────────────────────────
func deal_market_window(player, n: int = 5) -> Array:
	"""Oyuncuya ağırlıklı rarity örneklemesiyle market penceresi aç."""
	var pid: int = player.pid
	_return_window(pid)

	var turn: int = player.turns_played if "turns_played" in player else _current_turn

	var aw: Array = _available_weighted(turn)
	var cards: Array = aw[0]
	var weights: Array = aw[1]

	if cards.is_empty():
		# Fallback: tüm mevcut kartlar
		cards = pool.filter(func(c): return pool_copies.get(c.name, 0) > 0)
		if cards.is_empty():
			cards = pool.duplicate()
		weights = []
		for _c in cards:
			weights.append(1.0)

	var window: Array = _weighted_sample(cards, weights, n)
	for card in window:
		pool_copies[card.name] = max(0, pool_copies.get(card.name, 0) - 1)

	_player_windows[pid] = window
	if "stats" in player:
		player.stats["market_rolls"] = player.stats.get("market_rolls", 0) + 1

	return window


func _return_window(pid: int) -> void:
	"""Oyuncunun açık penceresindeki kartları havuza geri yükle."""
	if not _player_windows.has(pid):
		return
	for card in _player_windows[pid]:
		pool_copies[card.name] = pool_copies.get(card.name, 0) + 1
	_player_windows.erase(pid)


func return_unsold(player, bought: Array = []) -> void:
	"""Satılmamış pencere kartlarını havuza iade et."""
	var pid: int = player.pid
	var bought_counts: Dictionary = {}
	for card in bought:
		bought_counts[card.name] = bought_counts.get(card.name, 0) + 1

	var window: Array = _player_windows.get(pid, [])
	_player_windows.erase(pid)

	for card in window:
		if bought_counts.get(card.name, 0) > 0:
			bought_counts[card.name] -= 1
			continue
		pool_copies[card.name] = pool_copies.get(card.name, 0) + 1


func return_one(card_name: String) -> void:
	"""Tek bir kartı havuza geri yükle (el taşması için)."""
	pool_copies[card_name] = mini(pool_copies.get(card_name, 0) + 1, 3)


func get_cards_for_player(n: int = 5, turn: int = 1) -> Array:
	"""Legacy API — pencere takibi olmadan örnekle."""
	var aw: Array = _available_weighted(turn)
	var cards: Array = aw[0]
	var weights: Array = aw[1]
	if cards.is_empty():
		cards = pool.filter(func(c): return pool_copies.get(c.name, 0) > 0)
		if cards.is_empty():
			cards = pool.duplicate()
		weights = []
		for _c in cards:
			weights.append(1.0)
	var window: Array = _weighted_sample(cards, weights, n)
	for card in window:
		pool_copies[card.name] = max(0, pool_copies.get(card.name, 0) - 1)
	return window


func refresh_cost() -> int:
	return 2  # MARKET_REFRESH_COST
