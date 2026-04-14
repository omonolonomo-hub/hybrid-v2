# ================================================================
# AUTOCHESS HYBRID - Board Renderer (GDScript 4)
# Hex tahtasini Node2D uzerinde _draw() ile cizer.
# Main.gd: board_renderer.draw_board(human_player.board)
# ================================================================
extends Node2D

# Sabitler
var HEX_SIZE:         float = 52.0  # Dinamik (viewport'a göre ayarlanır)
var ORIGIN:           Vector2 = Vector2(640.0, 270.0)  # Dinamik (viewport'a göre ayarlanır)
const FONT_SIZE_NAME: int = 11
const FONT_SIZE_STAT: int = 10
const BOARD_RADIUS:   int  = 3

# Durum
var _board = null
var _selected: Vector2i = Vector2i(-99, -99)
var highlight_coords: Array = []   # yerlestirme modu vurgu hexleri

# Texture cache: res:// yolu -> ImageTexture
var _tex_cache: Dictionary = {}

func _load_texture(path: String) -> ImageTexture:
	if path == "": return null
	if _tex_cache.has(path): return _tex_cache[path]
	if not ResourceLoader.exists(path): return null
	var tex = load(path)
	_tex_cache[path] = tex
	return tex

# Sinyal: hex tiklaninca emit edilir (Main.gd dinler)
signal hex_selected(coord: Vector2i)


func _ready() -> void:
	_fit_to_screen()


func _fit_to_screen() -> void:
	"""Viewport boyutuna göre board'u responsive yap."""
	var viewport: Vector2 = get_viewport_rect().size
	
	# HEX_SIZE dinamik ayarla (viewport'a göre)
	HEX_SIZE = minf(viewport.x, viewport.y) / 22.0  # 22.0 = daha küçük hex (37 hex için)
	
	# ORIGIN'i viewport merkezine ayarla
	ORIGIN = viewport / 2.0
	
	# Position sıfırla (parent container'ın merkezinde olacak)
	position = Vector2.ZERO


# Public API

func draw_board(board) -> void:
	_board = board
	queue_redraw()

func select_hex(coord: Vector2i) -> void:
	_selected = coord
	queue_redraw()

func pixel_to_hex_coord(px: Vector2) -> Vector2i:
	return HexBoard.pixel_to_hex(px.x, px.y, ORIGIN.x, ORIGIN.y, HEX_SIZE)

## Yerlestirme modunda bos hexleri yesil vurgula.
func set_highlight(coords: Array) -> void:
	highlight_coords = coords
	queue_redraw()

# Giris

func _input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var local_pos: Vector2 = get_local_mouse_position()
		var coord: Vector2i = pixel_to_hex_coord(local_pos)
		select_hex(coord)
		hex_selected.emit(coord)

# Cizim ana fonksiyonu

func _draw() -> void:
	var all_coords: Array = HexBoard.board_coords(BOARD_RADIUS)
	for coord in all_coords:
		var center: Vector2 = HexBoard.hex_to_pixel(
			coord.x, coord.y, ORIGIN.x, ORIGIN.y, HEX_SIZE)
		var is_sel: bool = (coord == _selected)
		var is_hi: bool  = coord in highlight_coords

		if _board != null and _board.grid.has(coord):
			_draw_card_hex(center, _board.grid[coord], is_sel)
		else:
			_draw_empty_hex(center, is_sel, is_hi)


# Bos hex

func _draw_empty_hex(center: Vector2, selected: bool, highlighted: bool = false) -> void:
	var fill_col: Color
	if highlighted:
		fill_col = Color(0.0, 0.6, 0.2, 0.55)
	else:
		fill_col = Color(0.063, 0.078, 0.133, 0.75)
	_fill_hex(center, fill_col)
	var border_col: Color
	if selected:
		border_col = Constants.C_SELECT
	elif highlighted:
		border_col = Color(0.0, 1.0, 0.3, 0.8)
	else:
		border_col = Constants.C_LINE
	_stroke_hex(center, border_col, 2.5 if (selected or highlighted) else 1.0)


# Kart iceren hex

func _draw_card_hex(center: Vector2, card, selected: bool) -> void:
	var group: String = card.dominant_group()
	var group_col: Color = Constants.GROUP_COLORS.get(group, Color.GRAY)
	_fill_hex(center, group_col.darkened(0.55))

	var rarity_col: Color = Constants.RARITY_COLORS.get(card.rarity, Color.WHITE)
	_stroke_hex(center,
		Constants.C_SELECT if selected else rarity_col,
		2.5 if selected else 1.8)

	# ── Ön görsel varsa çiz ──────────────────────────────────────────
	if card.get("image_front") != null and card.image_front != "":
		var tex = _load_texture(card.image_front)
		if tex != null:
			var img_size: float = HEX_SIZE * 1.2
			var img_rect := Rect2(
				center + Vector2(-img_size * 0.5, -img_size * 0.5),
				Vector2(img_size, img_size))
			draw_texture_rect(tex, img_rect, false)

	var badge_pos: Vector2 = center + Vector2(HEX_SIZE * 0.35, -HEX_SIZE * 0.55)
	draw_circle(badge_pos, 6.0, rarity_col)
	draw_string(ThemeDB.fallback_font,
		badge_pos + Vector2(-5, 4), card.rarity,
		HORIZONTAL_ALIGNMENT_LEFT, -1, 8, Color.BLACK)

	var dname: String = card.name
	if dname.length() > 9:
		dname = dname.substr(0, 9) + "."
	draw_string(ThemeDB.fallback_font,
		center + Vector2(-HEX_SIZE * 0.58, -6),
		dname, HORIZONTAL_ALIGNMENT_LEFT, -1,
		FONT_SIZE_NAME, Constants.C_WHITE)

	draw_string(ThemeDB.fallback_font,
		center + Vector2(-HEX_SIZE * 0.58, 10),
		"P:%d" % card.total_power(),
		HORIZONTAL_ALIGNMENT_LEFT, -1,
		FONT_SIZE_STAT, Constants.C_GOLD)

	if card.rarity == "E":
		var br := Rect2(center + Vector2(-24, -HEX_SIZE * 0.78), Vector2(48, 14))
		draw_rect(br, Color(0.9, 0.7, 0.0, 0.9), true)
		draw_string(ThemeDB.fallback_font,
			br.position + Vector2(4, 11),
			"EVOLVED", HORIZONTAL_ALIGNMENT_LEFT, -1, 9, Color.BLACK)

	var re: Array = card.rotated_edges()
	var dirs_deg: Array = [270.0, 330.0, 30.0, 90.0, 150.0, 210.0]
	for d in mini(6, re.size()):
		var val: int = re[d]["value"]
		if val <= 0:
			continue
		var ang_rad: float = deg_to_rad(dirs_deg[d])
		var tip: Vector2 = center + Vector2(cos(ang_rad), sin(ang_rad)) * (HEX_SIZE - 10.0)
		var sname: String = Constants.STAT_SHORT.get(re[d]["name"], re[d]["name"].substr(0, 2))
		draw_string(ThemeDB.fallback_font,
			tip + Vector2(-8, 5),
			"%s%d" % [sname, val],
			HORIZONTAL_ALIGNMENT_LEFT, -1, 8,
			group_col.lightened(0.4))


# Hex cizim yardimcilari (flat-top)

func _hex_corners(center: Vector2, size: float) -> PackedVector2Array:
	var pts: PackedVector2Array
	pts.resize(6)
	for i in 6:
		var a: float = deg_to_rad(60.0 * i)
		pts[i] = center + Vector2(cos(a), sin(a)) * (size - 2.0)
	return pts

func _fill_hex(center: Vector2, color: Color) -> void:
	var pts := _hex_corners(center, HEX_SIZE)
	draw_colored_polygon(pts, color)

func _stroke_hex(center: Vector2, color: Color, width: float) -> void:
	var pts := _hex_corners(center, HEX_SIZE)
	for i in 6:
		draw_line(pts[i], pts[(i + 1) % 6], color, width, true)
