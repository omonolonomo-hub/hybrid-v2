# ================================================================
# AUTOCHESS HYBRID - Main Scene Controller (GDScript 4)
# ================================================================
extends Node

# Sahne icindeki referanslar
@onready var hp_label:      Label          = $UI/GameView/BottomPanel/HBoxLayout/PlayerInfo/HPLabel
@onready var gold_label:    Label          = $UI/GameView/BottomPanel/HBoxLayout/PlayerInfo/GoldLabel
@onready var turn_label:    Label          = $UI/GameView/BottomPanel/HBoxLayout/PlayerInfo/TurnLabel
@onready var buy_button:    Button         = $UI/GameView/BottomPanel/HBoxLayout/PlayerInfo/BuyButton
@onready var shop_cards:    HBoxContainer  = $UI/GameView/BottomPanel/HBoxLayout/ShopArea/ShopCards
@onready var hand_cards:    HBoxContainer  = $UI/GameView/BottomPanel/HBoxLayout/HandArea/HandCards
@onready var hand_label:    Label          = $UI/GameView/BottomPanel/HBoxLayout/HandArea/HandLabel
@onready var result_panel:  PanelContainer = $UI/GameView/CombatResultPanel
@onready var result_label:  Label          = $UI/GameView/CombatResultPanel/ResultLabel
@onready var board_renderer: Node2D        = $UI/GameView/BoardContainer/BoardViewport/BoardRenderer

# Oyun nesneleri
var game: Game
var human_player
var current_market: Array = []
var _combat_resolver: CombatResolver  # savaş çözücü instance

# El -> Board yerlestirme modu
var _pending_card = null   # Card veya null


func _ready() -> void:
	buy_button.pressed.connect(_on_next_turn)
	board_renderer.hex_selected.connect(_on_hex_selected)
	_start_new_game()


func _start_new_game() -> void:
	# CardPool autoload - static method uyarısı normal (suppress edilebilir)
	@warning_ignore("static_called_on_instance")
	var pool: Array = CardPool.get_pool()
	var strategies: Array = ["warrior", "builder", "economist", "evolver"]
	var players: Array = []
	for i in range(4):
		var p = Player.new(i, strategies[i])
		p.synergy_matrix = BuilderSynergyMatrix.new() if strategies[i] == "builder" else null
		players.append(p)
	human_player = players[0]

	var ai_instance: AI = AI.new()
	_combat_resolver = CombatResolver.new()

	# PassiveTrigger autoload'undan callable al
	var passive_fn: Callable = Callable(PassiveTrigger, "trigger_passive")
	var combat_fn:  Callable = Callable(_combat_resolver, "resolve")

	game = Game.new(
		players,
		false,
		null,
		passive_fn,
		combat_fn,
		pool,
		ai_instance
	)

	_update_ui()
	_open_market_window()
	_refresh_hand_ui()
	_redraw_board()


# Tur dongusu

func _on_next_turn() -> void:
	_cancel_placement()
	game.preparation_phase()
	game.combat_phase()
	_show_combat_results()
	_update_ui()
	_open_market_window()
	_refresh_hand_ui()
	_redraw_board()

	if game.alive_players().size() <= 1:
		buy_button.disabled = true
		result_label.text = "OYUN BITTI!\n" + result_label.text
		result_panel.visible = true


func _open_market_window() -> void:
	current_market = game.market.deal_market_window(human_player, 5)
	_refresh_shop_ui()


# UI guncellemeleri

func _update_ui() -> void:
	hp_label.text   = "HP: %d" % human_player.hp
	gold_label.text = "Gold: %d" % human_player.gold
	turn_label.text = "Tur: %d" % game.turn


func _refresh_shop_ui() -> void:
	for child in shop_cards.get_children():
		child.queue_free()

	for card in current_market:
		var btn: Button = Button.new()
		var cost: int = Constants.CARD_COSTS.get(card.rarity, 0)
		btn.text = "%s\n[R%s | %dg | P:%d]" % [card.name, card.rarity, cost, card.total_power()]
		btn.custom_minimum_size = Vector2(140, 70)
		btn.disabled = human_player.gold < cost
		
		# FIX 4: Market gri kart sorunu - modulate beyaz yap
		btn.modulate = Color(1.0, 1.0, 1.0, 1.0)
		
		# Rarity rengi border (theme override)
		var rarity_color: Color = Constants.RARITY_COLORS.get(card.rarity, Color.WHITE)
		var style_normal := StyleBoxFlat.new()
		style_normal.bg_color = Constants.C_PANEL
		style_normal.border_color = rarity_color
		style_normal.border_width_left = 2
		style_normal.border_width_right = 2
		style_normal.border_width_top = 2
		style_normal.border_width_bottom = 2
		style_normal.corner_radius_top_left = 4
		style_normal.corner_radius_top_right = 4
		style_normal.corner_radius_bottom_left = 4
		style_normal.corner_radius_bottom_right = 4
		btn.add_theme_stylebox_override("normal", style_normal)
		
		var style_hover := style_normal.duplicate()
		style_hover.bg_color = Constants.C_PANEL.lightened(0.2)
		btn.add_theme_stylebox_override("hover", style_hover)
		
		btn.pressed.connect(_on_buy_card.bind(card, btn))
		shop_cards.add_child(btn)


func _refresh_hand_ui() -> void:
	for child in hand_cards.get_children():
		child.queue_free()

	if human_player.hand.is_empty():
		var lbl := Label.new()
		lbl.text = "(el bos)"
		hand_cards.add_child(lbl)
		return

	for card in human_player.hand:
		var btn: Button = Button.new()
		btn.text = "%s\nR%s | P:%d" % [card.name, card.rarity, card.total_power()]
		btn.custom_minimum_size = Vector2(120, 65)
		
		# Seçili kart vurgusu
		if card == _pending_card:
			btn.modulate = Color(0.3, 1.0, 0.4)
		else:
			btn.modulate = Color(1.0, 1.0, 1.0, 1.0)  # FIX 4: Beyaz modulate
		
		# Rarity rengi border
		var rarity_color: Color = Constants.RARITY_COLORS.get(card.rarity, Color.WHITE)
		var style_normal := StyleBoxFlat.new()
		style_normal.bg_color = Constants.C_PANEL
		style_normal.border_color = rarity_color
		style_normal.border_width_left = 2
		style_normal.border_width_right = 2
		style_normal.border_width_top = 2
		style_normal.border_width_bottom = 2
		style_normal.corner_radius_top_left = 4
		style_normal.corner_radius_top_right = 4
		style_normal.corner_radius_bottom_left = 4
		style_normal.corner_radius_bottom_right = 4
		btn.add_theme_stylebox_override("normal", style_normal)
		
		var style_hover := style_normal.duplicate()
		style_hover.bg_color = Constants.C_PANEL.lightened(0.2)
		btn.add_theme_stylebox_override("hover", style_hover)
		
		btn.pressed.connect(_on_hand_card_clicked.bind(card))
		hand_cards.add_child(btn)

	# El etiketi: bos yer var mi goster
	var free_n: int = human_player.board.free_coords().size()
	hand_label.text = "EL (%d kart)   Board: %d bos hex" % [
		human_player.hand.size(), free_n]


func _on_buy_card(card, btn: Button) -> void:
	human_player.buy_card(card, game.market)
	btn.disabled = true
	_update_ui()
	_refresh_hand_ui()
	# Altin yetersizse diger butonlari da devre disi birak
	for child in shop_cards.get_children():
		if child is Button and not child.disabled:
			child.disabled = (human_player.gold <= 0)


# El karti tiklama -> yerlestirme modu

func _on_hand_card_clicked(card) -> void:
	if _pending_card == card:
		# Ayni karta tekrar tiklandiysa iptali
		_cancel_placement()
		return

	var free: Array = human_player.board.free_coords()
	if free.is_empty():
		# Board dolu — otomatik koyacak yer yok, uyari
		hand_label.text = "Board dolu! Once bir karti kaldirman gerekiyor."
		return

	_pending_card = card
	board_renderer.set_highlight(free)
	hand_label.text = "Hex sec (ESC = iptal)..."
	_refresh_hand_ui()


# Hex secilince yerlestir

func _on_hex_selected(coord: Vector2i) -> void:
	if _pending_card == null:
		return

	var ok: bool = human_player.place_card_on_board(_pending_card, coord)
	if ok:
		_cancel_placement()
		_refresh_hand_ui()
		_redraw_board()
	else:
		# Dolu hex secildi — vurguyu koru, kullaniciya bildir
		hand_label.text = "O hex dolu, baska bir hex sec."


func _cancel_placement() -> void:
	_pending_card = null
	board_renderer.set_highlight([])
	board_renderer.select_hex(Vector2i(-99, -99))


func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
		if _pending_card != null:
			_cancel_placement()
			_refresh_hand_ui()


# Combat sonuclari

func _show_combat_results() -> void:
	if game.last_combat_results.is_empty():
		return
	var lines: Array = []
	for res in game.last_combat_results:
		var winner_txt: String
		if res["winner_pid"] == -1:
			winner_txt = "Berabere"
		else:
			winner_txt = "P%d kazandi (-%d HP)" % [res["winner_pid"], res["dmg"]]
		lines.append("P%d vs P%d -> %s" % [res["pid_a"], res["pid_b"], winner_txt])
	result_label.text = "\n".join(lines)
	result_panel.visible = true
	await get_tree().create_timer(2.0).timeout
	result_panel.visible = false


func _redraw_board() -> void:
	if board_renderer and board_renderer.has_method("draw_board"):
		board_renderer.draw_board(human_player.board)
