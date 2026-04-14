# ================================================================
# AUTOCHESS HYBRID - Passive Trigger (GDScript 4)
# engine_core/passive_trigger.py karşılığı
# Autoload adı: PassiveTrigger
# Kullanım: Callable(PassiveTrigger, "trigger_passive")
# ================================================================
extends Node

# ── Ana tetikleyici (Game.new()'e Callable olarak geçirilir) ──────
## trigger_passive(card, event, card_owner, opp, ctx, verbose)
## Dönüş: int (ek combat puanı — çoğu pasif için 0)
func trigger_passive(card: Card, trigger: String, card_owner,
		opponent, ctx: Dictionary, verbose: bool = false) -> int:
	if card.passive_type == "none":
		return 0

	var power_before: int = card.total_power()
	var result: int       = _dispatch(card, trigger, card_owner, opponent, ctx)
	var delta: int        = card.total_power() - power_before

	if verbose:
		print("[PASSIVE] %s | %s → delta=%d res=%d" % [card.name, trigger, delta, result])

	# Güçlenme varsa card_owner log'una yaz
	if delta > 0 and card_owner != null and "passive_buff_log" in card_owner:
		card_owner.passive_buff_log.append({
			"turn":    ctx.get("turn", 0),
			"card":    card.name,
			"passive": card.passive_type,
			"trigger": trigger,
			"delta":   delta,
		})

	return result


# ── Dispatch: passive_type → handler ─────────────────────────────
func _dispatch(card: Card, trigger: String, card_owner,
		opponent, ctx: Dictionary) -> int:
	match card.passive_type:
		"copy":     return _passive_copy(card, trigger, card_owner, opponent, ctx)
		"combat":   return _passive_combat(card, trigger, card_owner, opponent, ctx)
		"economy":  return _passive_economy(card, trigger, card_owner, opponent, ctx)
		"survival": return _passive_survival(card, trigger, card_owner, opponent, ctx)
		"synergy":  return _passive_synergy(card, trigger, card_owner, opponent, ctx)
		"combo":    return _passive_combo(card, trigger, card_owner, opponent, ctx)
	return 0


# ── copy ─────────────────────────────────────────────────────────
## copy_2 / copy_3 tetiklenince en yüksek kenara +1 ekle.
func _passive_copy(card: Card, trigger: String, _card_owner,
		_opp, _ctx: Dictionary) -> int:
	if trigger not in ["copy_2", "copy_3"]:
		return 0
	if card.edges.is_empty():
		return 0
	var idx: int = 0
	var max_val: int = -1
	for i in card.edges.size():
		if card.edges[i]["value"] > max_val:
			max_val = card.edges[i]["value"]
			idx = i
	var sname: String = card.edges[idx]["name"]
	card.edges[idx]["value"] += 1
	card.stats[sname] = card.edges[idx]["value"]
	return 0


# ── combat ───────────────────────────────────────────────────────
## pre_combat tetiklenince toplam güce göre ek puan üret.
func _passive_combat(card: Card, trigger: String, _card_owner,
		_opp, _ctx: Dictionary) -> int:
	if trigger != "pre_combat":
		return 0
	# Temel: kartın total_power'ının %10'u kadar bonus (tavan 5)
	return mini(5, int(card.total_power() / 10.0))


# ── economy ──────────────────────────────────────────────────────
## income tetiklenince card_owner'a +1 altın.
func _passive_economy(_card: Card, trigger: String, card_owner,
		_opp, _ctx: Dictionary) -> int:
	if trigger != "income" or card_owner == null:
		return 0
	if "gold" in card_owner:
		card_owner.gold += 1
		if "stats" in card_owner:
			card_owner.stats["gold_earned"] = card_owner.stats.get("gold_earned", 0) + 1
	return 0


# ── survival ─────────────────────────────────────────────────────
## Kart elenmek üzereyken (is_eliminated true olmadan önce) bir
## stat'ı 1'e yükselt.
func _passive_survival(card: Card, trigger: String, _card_owner,
		_opp, _ctx: Dictionary) -> int:
	if trigger != "near_elimination":
		return 0
	# En düşük sıfır-olmayan stat'ı bul ve 1'e çek
	var lowest_idx: int = -1
	var lowest_val: int = 999
	for i in card.edges.size():
		var v: int = card.edges[i]["value"]
		if v > 0 and v < lowest_val:
			lowest_val = v
			lowest_idx = i
	if lowest_idx >= 0:
		card.edges[lowest_idx]["value"] = maxi(1, card.edges[lowest_idx]["value"])
		card.stats[card.edges[lowest_idx]["name"]] = card.edges[lowest_idx]["value"]
	return 0


# ── synergy ──────────────────────────────────────────────────────
## Grup sinerji bonusu olan turlarda kartın kendi grubuna göre +1.
func _passive_synergy(_card: Card, trigger: String, card_owner,
		_opp, _ctx: Dictionary) -> int:
	if trigger != "pre_combat" or card_owner == null:
		return 0
	if not ("board" in card_owner):
		return 0
	var syn: int = card_owner.board.calculate_group_synergy_bonus()
	return 1 if syn >= 3 else 0


# ── combo ────────────────────────────────────────────────────────
## Kombo puanı kazanıldığında ek puan üret.
func _passive_combo(_card: Card, trigger: String, _card_owner,
		_opp, ctx: Dictionary) -> int:
	if trigger != "combo":
		return 0
	return mini(3, ctx.get("combo_pts", 0) / 5)
