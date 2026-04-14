# ================================================================
# AUTOCHESS HYBRID - Game (GDScript 4)
# Maç akışı: hazırlık fazı, savaş fazı, oyun döngüsü.
# game.py'nin birebir karşılığı.
# ================================================================
class_name Game
extends RefCounted

# ── Bağımlılıklar (autoload ya da dışarıdan inject edilir) ────────
# trigger_passive_fn : Callable  (card, event, player, opp, ctx, verbose)
# combat_phase_fn    : Callable  (board_a, board_b, bonus_a, bonus_b, pa, pb, ctx)
# ai_override        : Object    — buy_cards() + place_cards() olan herhangi nesne
#                                  null ise varsayılan AI sınıfı kullanılır

const KILL_PTS: int    = 1     # constants.gd'den; burada sabit olarak tutuyoruz
const STARTING_HP: int = 100

var players: Array           # Array[Player]
var card_pool: Array         # Array[Card]
var card_by_name: Dictionary # card.name -> Card

var market: Market
var turn: int = 0
var verbose: bool = false
var log_lines: Array = []    # Array[String]

var _rng: RandomNumberGenerator
var trigger_passive_fn                   # Callable veya null
var combat_phase_fn                      # Callable veya null
var _ai                                  # AI sınıfı / instance

# UI için: son turun tüm maç sonuçları
var last_combat_results: Array = []      # Array[Dictionary]


func _init(
	p_players: Array,
	p_verbose: bool = false,
	p_rng: RandomNumberGenerator = null,
	p_trigger_passive = null,
	p_combat_phase = null,
	p_card_pool: Array = [],
	p_ai_override = null
) -> void:
	players = p_players
	card_pool = p_card_pool
	card_by_name = {}
	for c in card_pool:
		card_by_name[c.name] = c

	_rng = p_rng if p_rng != null else RandomNumberGenerator.new()
	if p_rng == null:
		_rng.randomize()

	market = Market.new(card_pool, _rng)
	verbose = p_verbose
	trigger_passive_fn = p_trigger_passive
	combat_phase_fn    = p_combat_phase

	# AI: override yoksa varsayılan AI sınıfı kullanılır
	# (Godot'ta sınıfa referans: load("res://scripts/ai.gd") ile ayarlanır)
	_ai = p_ai_override

	_deal_starting_hands()


# ================================================================
# Kart havuzu yönetimi
# ================================================================

func _return_cards_to_pool(player) -> void:
	"""Elenen oyuncunun kart ve elini havuza geri yükle."""
	var _pool_copies: Dictionary = market.pool_copies

	var _return_one = func(card) -> void:
		var base: String = card.name.substr(8) if card.name.begins_with("Evolved ") else card.name
		if _pool_copies.has(base):
			_pool_copies[base] = mini(_pool_copies[base] + 1, 3)

	for card in player.board.grid.values():
		_return_one.call(card)
	player.board.grid.clear()
	if "has_catalyst" in player.board:
		player.board.has_catalyst = false

	for card in player.hand:
		_return_one.call(card)
	player.hand.clear()

	player.copies.clear()
	player.copy_turns.clear()


func _deal_starting_hands() -> void:
	"""Her oyuncuya başlangıçta 3 rarity-1 kart dağıt."""
	var common_cards: Array = card_pool.filter(func(c): return c.rarity == "1")
	for player in players:
		var chosen: Array = _sample(common_cards, mini(3, common_cards.size()))
		for card in chosen:
			var cloned = card.clone()
			player.hand.append(cloned)
			player.copies[card.name] = player.copies.get(card.name, 0) + 1
		_log("  P%d starting cards: %s" % [player.pid,
			", ".join(chosen.map(func(c): return c.name))])


# Basit shuffle-sample (RandomNumberGenerator tabanlı)
func _sample(arr: Array, k: int) -> Array:
	var copy: Array = arr.duplicate()
	for i in range(copy.size() - 1, 0, -1):
		var j: int = _rng.randi_range(0, i)
		var tmp = copy[i]; copy[i] = copy[j]; copy[j] = tmp
	return copy.slice(0, k)


func _log(msg: String) -> void:
	if verbose:
		print(msg)
	log_lines.append(msg)


func alive_players() -> Array:
	return players.filter(func(p): return p.alive)


# ================================================================
# Swiss pairing
# ================================================================

func swiss_pairs() -> Array:
	"""HP'ye göre sırala, aynı HP bandında jitter ekle, en yakın eşleştir."""
	var alive: Array = alive_players()
	# Sort comparison must be consistent - calculate jitter once per player
	var jitter_map: Dictionary = {}
	for p in alive:
		jitter_map[p.pid] = p.hp + _rng.randf() * 0.5
	alive.sort_custom(func(a, b):
		return jitter_map[a.pid] > jitter_map[b.pid])

	var pairs: Array = []
	var used: Dictionary = {}

	for i in range(alive.size()):
		var p1 = alive[i]
		if used.has(p1.pid):
			continue
		for j in range(i + 1, alive.size()):
			var p2 = alive[j]
			if not used.has(p2.pid):
				pairs.append([p1, p2])
				used[p1.pid] = true
				used[p2.pid] = true
				break
	return pairs


# ================================================================
# Hazırlık fazı
# ================================================================

func preparation_phase() -> void:
	turn += 1
	_log("\n%s\n  TUR %d\n%s" % ["-".repeat(50), turn, "-".repeat(50)])

	var alive: Array = alive_players()

	# Önce tüm pencereleri aç (ilk oyuncu avantajını kaldır)
	var player_markets: Dictionary = {}
	for player in alive:
		player_markets[player.pid] = market.deal_market_window(player, 5)

	for player in alive:
		player.income()

		if trigger_passive_fn != null:
			for card in player.board.grid.values():
				trigger_passive_fn.call(card, "income", player, null, {"turn": turn}, verbose)

		var player_market: Array = player_markets[player.pid]

		if trigger_passive_fn != null:
			for card in player.board.grid.values():
				trigger_passive_fn.call(card, "market_refresh", player, null, {"turn": turn}, verbose)

		var hand_before: int = player.hand.size()

		if _ai != null:
			_ai.buy_cards(player, player_market, market, _rng, trigger_passive_fn)

		var newly_bought: Array = player.hand.slice(hand_before)
		market.return_unsold(player, newly_bought)

		player.apply_interest()

		var evos: Array = player.check_evolution(market, card_by_name)
		if evos.size() > 0 and verbose:
			for base_name in evos:
				_log("  *** EVRIM: P%d -> Evolved %s! ***" % [player.pid, base_name])

		if _ai != null:
			_ai.place_cards(player, _rng)

		if trigger_passive_fn != null:
			player.check_copy_strengthening(turn, trigger_passive_fn)

		# Board istatistikleri
		var bp: int = 0
		var uc: int = 0
		for card in player.board.grid.values():
			bp += card.total_power()
			uc += 1
			player.card_turns_alive[card.name] = player.card_turns_alive.get(card.name, 0) + 1
		player.stats["board_power"] = player.stats.get("board_power", 0) + bp
		player.stats["unit_count"]  = player.stats.get("unit_count",  0) + uc
		player.stats["gold_per_turn"] = player.stats.get("gold_per_turn", 0) + player.gold


# ================================================================
# Savaş fazı
# ================================================================

func combat_phase() -> void:
	var pairs: Array = swiss_pairs()
	if pairs.is_empty():
		return

	last_combat_results = []

	for pair in pairs:
		var p_a = pair[0]
		var p_b = pair[1]

		_log("\n  P%d(%s, %dHP) vs P%d(%s, %dHP)" % [
			p_a.pid, p_a.strategy, p_a.hp,
			p_b.pid, p_b.strategy, p_b.hp])

		var ctx: Dictionary = {"turn": turn}
		var board_a = p_a.board
		var board_b = p_b.board

		if trigger_passive_fn != null:
			for card in board_a.grid.values():
				trigger_passive_fn.call(card, "pre_combat", p_a, p_b, ctx, verbose)
			for card in board_b.grid.values():
				trigger_passive_fn.call(card, "pre_combat", p_b, p_a, ctx, verbose)

		# Kombo ve sinerji puanları
		var combo_result_a: Array = board_a.find_combos()  # [pts, bonus]
		var combo_result_b: Array = board_b.find_combos()
		var combo_pts_a: int = combo_result_a[0]
		var bonus_a     = combo_result_a[1]
		var combo_pts_b: int = combo_result_b[0]
		var bonus_b     = combo_result_b[1]

		if board_a.has_catalyst:
			combo_pts_a *= 2
		if board_b.has_catalyst:
			combo_pts_b *= 2

		var synergy_pts_a: int = board_a.calculate_group_synergy_bonus()
		var synergy_pts_b: int = board_b.calculate_group_synergy_bonus()

		# Savaş çözümü
		var kill_a: int = 0
		var kill_b: int = 0
		var draws: int  = 0
		if combat_phase_fn != null:
			var res: Array = combat_phase_fn.call(board_a, board_b, bonus_a, bonus_b, p_a, p_b, ctx)
			kill_a = res[0]; kill_b = res[1]; draws = res[2]

		var pts_a: int = kill_a + combo_pts_a + synergy_pts_a
		var pts_b: int = kill_b + combo_pts_b + synergy_pts_b

		p_a.turn_pts  = pts_a;  p_b.turn_pts  = pts_b
		p_a.total_pts += pts_a; p_b.total_pts += pts_b

		p_a.stats["kills"] = p_a.stats.get("kills", 0) + int(kill_a / float(KILL_PTS))
		p_b.stats["kills"] = p_b.stats.get("kills", 0) + int(kill_b / float(KILL_PTS))
		p_a.stats["combo_triggers"] = p_a.stats.get("combo_triggers", 0) + combo_pts_a
		p_b.stats["combo_triggers"] = p_b.stats.get("combo_triggers", 0) + combo_pts_b
		if synergy_pts_a > 0:
			p_a.stats["synergy_trigger_count"] = p_a.stats.get("synergy_trigger_count", 0) + 1
		if synergy_pts_b > 0:
			p_b.stats["synergy_trigger_count"] = p_b.stats.get("synergy_trigger_count", 0) + 1

		_log("    Skor: P%d=%d (kill=%d combo=%d synergy=%d)  |  P%d=%d (kill=%d combo=%d synergy=%d)" % [
			p_a.pid, pts_a, kill_a, combo_pts_a, synergy_pts_a,
			p_b.pid, pts_b, kill_b, combo_pts_b, synergy_pts_b])

		p_a.stats["synergy_sum"] = p_a.stats.get("synergy_sum", 0) + synergy_pts_a
		p_b.stats["synergy_sum"] = p_b.stats.get("synergy_sum", 0) + synergy_pts_b
		p_a.stats["synergy_turns"] = p_a.stats.get("synergy_turns", 0) + 1
		p_b.stats["synergy_turns"] = p_b.stats.get("synergy_turns", 0) + 1

		var hp_before_a: int = p_a.hp
		var hp_before_b: int = p_b.hp

		var result_dmg: int    = 0
		var result_winner: int = -1  # -1 = berabere

		if pts_a > pts_b:
			var dmg: int = board_a.calculate_damage(pts_a, pts_b, turn)
			p_b.take_damage(dmg)
			p_a.stats["wins"] = p_a.stats.get("wins", 0) + 1
			p_b.stats["losses"] = p_b.stats.get("losses", 0) + 1
			p_a.stats["damage_dealt"] = p_a.stats.get("damage_dealt", 0) + dmg
			p_a.win_streak += 1
			if p_a.win_streak > p_a.stats.get("win_streak_max", 0):
				p_a.stats["win_streak_max"] = p_a.win_streak
			p_b.win_streak = 0
			result_winner = p_a.pid
			result_dmg    = dmg
			_log("    -> P%d kazandı! P%d -%d HP  [HP: %d]" % [p_a.pid, p_b.pid, dmg, p_b.hp])

		elif pts_b > pts_a:
			var dmg: int = board_b.calculate_damage(pts_b, pts_a, turn)
			p_a.take_damage(dmg)
			p_b.stats["wins"] = p_b.stats.get("wins", 0) + 1
			p_a.stats["losses"] = p_a.stats.get("losses", 0) + 1
			p_b.stats["damage_dealt"] = p_b.stats.get("damage_dealt", 0) + dmg
			p_b.win_streak += 1
			if p_b.win_streak > p_b.stats.get("win_streak_max", 0):
				p_b.stats["win_streak_max"] = p_b.win_streak
			p_a.win_streak = 0
			result_winner = p_b.pid
			result_dmg    = dmg
			_log("    -> P%d kazandı! P%d -%d HP  [HP: %d]" % [p_b.pid, p_a.pid, dmg, p_a.hp])

		else:
			p_a.gold += 1
			p_b.gold += 1
			p_a.stats["gold_earned"] = p_a.stats.get("gold_earned", 0) + 1
			p_b.stats["gold_earned"] = p_b.stats.get("gold_earned", 0) + 1
			p_a.stats["draws"] = p_a.stats.get("draws", 0) + 1
			p_b.stats["draws"] = p_b.stats.get("draws", 0) + 1
			p_a.win_streak = 0
			p_b.win_streak = 0
			_log("    -> Berabere! Her iki oyuncu +1 altın.")

		# UI sonuç kaydı
		last_combat_results.append({
			"pid_a":       p_a.pid,
			"pid_b":       p_b.pid,
			"pts_a":       pts_a,
			"pts_b":       pts_b,
			"kill_a":      kill_a,
			"kill_b":      kill_b,
			"combo_a":     combo_pts_a,
			"combo_b":     combo_pts_b,
			"synergy_a":   synergy_pts_a,
			"synergy_b":   synergy_pts_b,
			"draws":       draws,
			"winner_pid":  result_winner,
			"dmg":         result_dmg,
			"hp_before_a": hp_before_a,
			"hp_before_b": hp_before_b,
			"hp_after_a":  p_a.hp,
			"hp_after_b":  p_b.hp,
		})

		# Eleme kontrolü
		if not p_a.alive:
			_return_cards_to_pool(p_a)
			_log("    ELENDİ: P%d (HP=0) — kartlar havuza döndü" % p_a.pid)
		if not p_b.alive:
			_return_cards_to_pool(p_b)
			_log("    ELENDİ: P%d (HP=0) — kartlar havuza döndü" % p_b.pid)


# ================================================================
# Ana oyun döngüsü
# ================================================================

func run():
	"""Tüm turları oynar, kazananı döndürür."""
	while players.filter(func(p): return p.alive).size() > 1:
		preparation_phase()
		combat_phase()

		# Builder sinerji matrisi: her tur sonunda hafifçe unut
		for p in players:
			if p.alive and p.synergy_matrix != null:
				p.synergy_matrix.decay()

		if turn >= 50:  # sonsuz döngü güvencesi
			break

	var winners: Array = players.filter(func(p): return p.alive)
	var winner
	if winners.size() > 0:
		winner = winners.reduce(func(a, b): return a if a.hp >= b.hp else b)
	else:
		winner = players.reduce(func(a, b): return a if a.hp >= b.hp else b)

	_log("\n  KAZANAN: P%d (%s)  HP=%d  Skor=%d" % [
		winner.pid, winner.strategy, winner.hp, winner.total_pts])
	return winner
