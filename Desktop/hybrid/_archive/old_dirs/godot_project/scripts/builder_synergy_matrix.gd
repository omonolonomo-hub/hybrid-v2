# ================================================================
# AUTOCHESS HYBRID - BuilderSynergyMatrix (GDScript 4)
# Builder AI için oturum bazlı adjacency bellek sistemi.
# ai.py::BuilderSynergyMatrix'in karşılığı.
# ================================================================
class_name BuilderSynergyMatrix
extends RefCounted

const HEX_DIRS: Array = [Vector2i(1,0), Vector2i(-1,0), Vector2i(0,1), Vector2i(0,-1), Vector2i(1,-1), Vector2i(-1,1)]

var _weights: Dictionary = {}  # card_a_name -> { card_b_name -> float }
var _decay_rate: float    = 0.97
var _reward: float        = 1.0
var _penalty: float       = 0.3


func record_combo(a: String, b: String) -> void:
	if not _weights.has(a): _weights[a] = {}
	if not _weights.has(b): _weights[b] = {}
	_weights[a][b] = _weights[a].get(b, 0.0) + _reward
	_weights[b][a] = _weights[b].get(a, 0.0) + _reward


func record_miss(a: String, b: String) -> void:
	if not _weights.has(a): _weights[a] = {}
	if not _weights.has(b): _weights[b] = {}
	_weights[a][b] = maxf(0.0, _weights[a].get(b, 0.0) - _penalty)
	_weights[b][a] = maxf(0.0, _weights[b].get(a, 0.0) - _penalty)


func decay() -> void:
	for a in _weights:
		for b in _weights[a]:
			_weights[a][b] *= _decay_rate


func synergy_score(card_name: String, board_card_names: Array) -> float:
	var row: Dictionary = _weights.get(card_name, {})
	var total: float = 0.0
	for bn in board_card_names:
		total += row.get(bn, 0.0)
	return total


func update_from_board(board) -> void:
	var grid: Dictionary = board.grid
	var counted: Dictionary = {}
	for coord in grid.keys():
		var card = grid[coord]
		var cg: String = card.dominant_group()
		for d in HEX_DIRS:
			var nc: Vector2i = coord + d
			if not grid.has(nc):
				continue
			var pair_key: String = "%s|%s" % [
				str(mini(coord.x, nc.x)) + "," + str(mini(coord.y, nc.y)),
				str(maxi(coord.x, nc.x)) + "," + str(maxi(coord.y, nc.y))]
			if counted.has(pair_key):
				continue
			counted[pair_key] = true
			var neighbor = grid[nc]
			if cg == neighbor.dominant_group():
				record_combo(card.name, neighbor.name)
			else:
				record_miss(card.name, neighbor.name)
