## card_pool.gd  –  Autochess Hybrid Godot 4 Port
## Autoload olarak kayıtlı — class_name KULLANILMAZ (autoload ile çakışır)
extends Node

const LEGACY_RARITY := {
	"◆":"1","◆◆":"2","◆◆◆":"3","◆◆◆◆":"4","◆◆◆◆◆":"5"
}

static var _cache: Array = []

static func get_pool() -> Array:
	if _cache.is_empty():
		_cache = _build_pool()
		_apply_micro_buff(_cache)
	return _cache

static func _build_pool() -> Array:
	var path := "res://assets/data/cards.json"
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("cards.json bulunamadı: " + path)
		return []
	var json := JSON.new()
	var err  := json.parse(file.get_as_text())
	file.close()
	if err != OK:
		push_error("JSON parse hatası: " + json.get_error_message())
		return []
	var data: Array = json.get_data()
	var cards := []
	for entry in data:
		var rarity: String = LEGACY_RARITY.get(entry.get("rarity","1"), entry.get("rarity","1"))
		var stats: Dictionary = entry.get("stats", {})
		# int'e çevir
		for k in stats:
			stats[k] = int(stats[k])
		var c := Card.new(
			entry.get("name","?"),
			entry.get("category",""),
			rarity,
			stats,
			entry.get("passive_type","none")
		)
		c.image_front = entry.get("image_front", "")
		c.image_back  = entry.get("image_back",  "")
		cards.append(c)
	return cards

## Zayıf kartlara +1 micro-buff (v0.7)
static func _apply_micro_buff(cards: Array) -> int:
	var total_stats := 0
	var total_count := 0
	for card in cards:
		for k in card.stats:
			if not k.begins_with("_"):
				total_stats += card.stats[k]
				total_count += 1
	if total_count == 0: return 0
	var global_avg := float(total_stats) / float(total_count)
	var threshold  := global_avg - 1.0
	var buffed := 0
	for card in cards:
		var card_vals := []
		for k in card.stats:
			if not k.begins_with("_"):
				card_vals.append({"name":k,"value":card.stats[k]})
		if card_vals.is_empty(): continue
		var s := 0
		for e in card_vals: s += e["value"]
		var card_avg := float(s) / float(card_vals.size())
		if card_avg < threshold:
			card_vals.sort_custom(func(a,b): return a["value"] < b["value"])
			var lowest_name: String = card_vals[0]["name"]
			card.stats[lowest_name] += 1
			# edges güncelle
			for e in card.edges:
				if e["name"] == lowest_name:
					e["value"] = card.stats[lowest_name]; break
			buffed += 1
	return buffed
