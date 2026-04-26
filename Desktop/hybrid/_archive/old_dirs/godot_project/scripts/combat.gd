# ================================================================
# AUTOCHESS HYBRID - CombatResolver (GDScript 4)
# Kart başına kart savaş çözümü.
# game.gd → combat_phase_fn.call(board_a, board_b, bonus_a, bonus_b, p_a, p_b, ctx)
# Döndürür: [kill_pts_a: int, kill_pts_b: int, draw_count: int]
# ================================================================
class_name CombatResolver
extends RefCounted

var _rng: RandomNumberGenerator


func _init() -> void:
	_rng = RandomNumberGenerator.new()
	_rng.randomize()


func resolve(board_a: HexBoard, board_b: HexBoard,
             _bonus_a, _bonus_b, _p_a, _p_b,
             _ctx: Dictionary) -> Array:

	var cards_a: Array = board_a.alive_cards().duplicate()
	var cards_b: Array = board_b.alive_cards().duplicate()

	if cards_a.is_empty() or cards_b.is_empty():
		return [0, 0, 0]

	# Fisher-Yates karıştırma
	_shuffle(cards_a)
	_shuffle(cards_b)

	var kill_a := 0
	var kill_b := 0
	var draws  := 0
	var count  := mini(cards_a.size(), cards_b.size())

	for i in range(count):
		var ca: Card = cards_a[i]
		var cb: Card = cards_b[i]
		var pw_a: int = ca.total_power()
		var pw_b: int = cb.total_power()

		if pw_a > pw_b:
			kill_a += Constants.KILL_PTS
			cb.lose_highest_edge()
		elif pw_b > pw_a:
			kill_b += Constants.KILL_PTS
			ca.lose_highest_edge()
		else:
			draws += 1
			# Beraberede her iki kartta hafif hasar
			ca.apply_edge_debuff(_rng.randi_range(0, 5), 1)
			cb.apply_edge_debuff(_rng.randi_range(0, 5), 1)

	# Elenen kartları board'dan kaldır
	for coord in board_a.grid.keys().duplicate():
		if board_a.grid[coord].is_eliminated():
			board_a.remove(coord)
	for coord in board_b.grid.keys().duplicate():
		if board_b.grid[coord].is_eliminated():
			board_b.remove(coord)

	return [kill_a, kill_b, draws]


func _shuffle(arr: Array) -> void:
	for i in range(arr.size() - 1, 0, -1):
		var j: int = _rng.randi_range(0, i)
		var tmp = arr[i]; arr[i] = arr[j]; arr[j] = tmp
