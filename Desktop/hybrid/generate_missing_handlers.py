"""
Eksik Pasif Handler'ları Otomatik Oluşturma
===========================================
Bu script eksik handler'lar için kod şablonları üretir.
"""

import json

# Eksik kartları ve şablonlarını tanımla
MISSING_HANDLERS = {
    "synergy_field": [
        {
            "name": "Kraken",
            "effect": "While on board, neighboring enemy cards' Connection edges take -1 field effect.",
            "template": "neighbor_enemy_debuff",
            "params": {"stat": "Connection", "amount": -1}
        },
        {
            "name": "Opera",
            "effect": "When 2+ Art cards on board, +1 Prestige to all Art cards.",
            "template": "category_count_buff",
            "params": {"category": "Art & Culture", "threshold": 2, "stat": "Prestige", "amount": 1}
        },
        {
            "name": "Baroque",
            "effect": "When 2+ Art cards on board, +1 to Prestige edges.",
            "template": "category_count_buff",
            "params": {"category": "Art & Culture", "threshold": 2, "stat": "Prestige", "amount": 1}
        },
        {
            "name": "Blue Whale",
            "effect": "When 3+ Nature cards on board, +1 Harmony to all ally cards.",
            "template": "category_count_all_buff",
            "params": {"category": "Nature", "threshold": 3, "stat": "Harmony", "amount": 1}
        },
        {
            "name": "Coral Reef",
            "effect": "Spreads +1 Harmony to neighboring ally Nature cards per turn.",
            "template": "neighbor_category_buff",
            "params": {"category": "Nature", "stat": "Harmony", "amount": 1}
        },
        {
            "name": "Rainforest",
            "effect": "When 4+ Nature cards on board, +1 Spread to all Nature cards.",
            "template": "category_count_buff",
            "params": {"category": "Nature", "threshold": 4, "stat": "Spread", "amount": 1}
        },
        {
            "name": "Cordyceps",
            "effect": "While on board, opponent's neighboring cards take -1 Trace per turn.",
            "template": "neighbor_enemy_debuff",
            "params": {"stat": "Trace", "amount": -1}
        },
        {
            "name": "Milky Way",
            "effect": "When 3+ Cosmos cards on board, +1 Gravity to all Cosmos cards.",
            "template": "category_count_buff",
            "params": {"category": "Cosmos", "threshold": 3, "stat": "Gravity", "amount": 1}
        },
        {
            "name": "Andromeda Galaxy",
            "effect": "When 4+ Cosmos cards on board, Gravity edges +2.",
            "template": "category_count_buff",
            "params": {"category": "Cosmos", "threshold": 4, "stat": "Gravity", "amount": 2}
        },
        {
            "name": "Europa",
            "effect": "Spreads +1 Harmony to neighboring ally Cosmos cards.",
            "template": "neighbor_category_buff",
            "params": {"category": "Cosmos", "stat": "Harmony", "amount": 1}
        },
        {
            "name": "Quasar",
            "effect": "When 3+ Cosmos cards on board, +1 Spread to all cards.",
            "template": "category_count_all_buff",
            "params": {"category": "Cosmos", "threshold": 3, "stat": "Spread", "amount": 1}
        },
        {
            "name": "Periodic Table",
            "effect": "When 4+ Science cards on board, +1 Intelligence +1 Meaning to all Science cards.",
            "template": "category_count_multi_buff",
            "params": {"category": "Science", "threshold": 4, "stats": ["Intelligence", "Meaning"], "amount": 1}
        },
        {
            "name": "Higgs Boson",
            "effect": "While on board, all cards' Gravity edges +1.",
            "template": "global_buff",
            "params": {"stat": "Gravity", "amount": 1}
        },
        {
            "name": "Renaissance",
            "effect": "When 3+ cards from different categories on board, +1 Meaning to all cards.",
            "template": "diversity_buff",
            "params": {"threshold": 3, "stat": "Meaning", "amount": 1}
        },
        {
            "name": "Roman Empire",
            "effect": "When 4+ History cards on board, +1 Durability to all ally cards.",
            "template": "category_count_all_buff",
            "params": {"category": "History", "threshold": 4, "stat": "Durability", "amount": 1}
        },
    ],
    "combat": [
        {
            "name": "Quetzalcoatl",
            "effect": "If combat is won, grants +1 Speed to 1 neighboring ally card for that turn.",
            "template": "combat_win_neighbor_temp_buff",
            "params": {"stat": "Speed", "amount": 1, "count": 1}
        },
        {
            "name": "Flamenco",
            "effect": "If combat is won, +1 Speed to all ally cards that turn.",
            "template": "combat_win_all_temp_buff",
            "params": {"stat": "Speed", "amount": 1}
        },
        {
            "name": "Asteroid Belt",
            "effect": "If combat is won, spreads -1 Size field effect to opponent's board (to neighbors).",
            "template": "combat_win_enemy_debuff",
            "params": {"stat": "Size", "amount": -1}
        },
        {
            "name": "Quantum Mechanics",
            "effect": "When combat won, opponent's random 2 edges swap.",
            "template": "combat_win_swap_edges",
            "params": {"count": 2}
        },
        {
            "name": "Mongol Empire",
            "effect": "If combat is won, -1 Speed to 2 neighboring cards on opponent's board.",
            "template": "combat_win_enemy_neighbor_debuff",
            "params": {"stat": "Speed", "amount": -1, "count": 2}
        },
        {
            "name": "Sparta",
            "effect": "If combat is won, accumulates +2 Power permanently (max +4 throughout game).",
            "template": "combat_win_accumulate",
            "params": {"stat": "Power", "amount": 2, "max": 4}
        },
    ],
    "survival": [
        {
            "name": "Tardigrade",
            "effect": "When about to be destroyed, reset Durability group edges to 3, stay on board (twice).",
            "template": "revive_with_stat",
            "params": {"stat_group": "Durability", "value": 3, "max_uses": 2}
        },
        {
            "name": "Betelgeuse",
            "effect": "When about to be destroyed, explosion: -1 to highest edge of all neighboring cards (ally/enemy).",
            "template": "death_explosion_neighbors",
            "params": {"amount": -1, "target": "all"}
        },
        {
            "name": "Supernova",
            "effect": "When destroyed, deals -2 to highest edge of 3 neighboring enemy cards.",
            "template": "death_explosion_neighbors",
            "params": {"amount": -2, "target": "enemy", "count": 3}
        },
    ],
    "copy": [
        {
            "name": "Event Horizon",
            "effect": "Copy counter advances +1 extra per turn (copies Catalyst effect).",
            "template": "copy_counter_boost",
            "params": {"amount": 1}
        },
        {
            "name": "Charles Darwin",
            "effect": "In each copy strengthening, next threshold comes 1 turn early.",
            "template": "copy_threshold_reduce",
            "params": {"amount": 1}
        },
        {
            "name": "DNA",
            "effect": "At copy strengthening, +1 Durability permanently to all copies.",
            "template": "copy_all_buff",
            "params": {"stat": "Durability", "amount": 1}
        },
    ],
    "combo": [
        {
            "name": "Jazz",
            "effect": "When combo match occurs, gain +1 gold (max 2/turn).",
            "template": "combo_gold",
            "params": {"amount": 1, "max_per_turn": 2}
        },
        {
            "name": "Bioluminescence",
            "effect": "When combo match occurs, +1 Harmony to neighboring ally cards that turn.",
            "template": "combo_neighbor_temp_buff",
            "params": {"stat": "Harmony", "amount": 1}
        },
    ],
}

# Kod şablonları
TEMPLATES = {
    "category_count_buff": '''@passive("{name}")
def _passive_{snake_name}(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """{name}: {effect}"""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        stacks = _current_stacks(card)
        if stacks >= 6:
            return 1
        
        category_cards = [c for c in owner.board.alive_cards() if "{category}" in c.category]
        if len(category_cards) >= {threshold}:
            for target_card in category_cards:
                if target_card.has_stat("{stat}"):
                    target_card.add_base_stat("{stat}", {amount})
            card.set_meta("_sf_stacks", stacks + 1)
        return 1
    return 0
''',

    "category_count_all_buff": '''@passive("{name}")
def _passive_{snake_name}(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """{name}: {effect}"""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        category_cards = [c for c in owner.board.alive_cards() if "{category}" in c.category]
        if len(category_cards) >= {threshold}:
            for target_card in owner.board.alive_cards():
                if target_card.has_stat("{stat}"):
                    target_card.add_base_stat("{stat}", {amount})
        return 1
    return 0
''',

    "neighbor_category_buff": '''@passive("{name}")
def _passive_{snake_name}(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """{name}: {effect}"""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        stacks = _current_stacks(card)
        if stacks >= 6:
            return 1
        
        coord = _find_coord(owner.board, card)
        if coord:
            buffed = False
            for neighbor_card in _neighbor_cards(owner.board, coord):
                if "{category}" in neighbor_card.category and neighbor_card.has_stat("{stat}"):
                    neighbor_card.add_base_stat("{stat}", {amount})
                    buffed = True
            if buffed:
                card.set_meta("_sf_stacks", stacks + 1)
        return 1
    return 0
''',

    "neighbor_enemy_debuff": '''@passive("{name}")
def _passive_{snake_name}(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """{name}: {effect}"""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        coord = _find_coord(owner.board, card)
        if coord and opponent:
            turn = ctx.get("turn", 1)
            # Find enemy cards adjacent to this position
            for neighbor_card in opponent.board.alive_cards():
                enemy_coord = _find_coord(opponent.board, neighbor_card)
                if enemy_coord and _is_adjacent(coord, enemy_coord):
                    _add_temp_effect(neighbor_card, "{stat}", {amount}, turn)
        return 1
    return 0

def _is_adjacent(coord1, coord2):
    """Check if two hex coordinates are adjacent"""
    dx = abs(coord1[0] - coord2[0])
    dy = abs(coord1[1] - coord2[1])
    return (dx <= 1 and dy <= 1 and dx + dy <= 2)
''',

    "combat_win_neighbor_temp_buff": '''@passive("{name}")
def _passive_{snake_name}(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """{name}: {effect}"""
    if trigger == "combat_win" and owner is not None:
        coord = _find_coord(owner.board, card)
        if coord:
            neighbors = _neighbor_cards(owner.board, coord)
            if neighbors:
                turn = ctx.get("turn", 1)
                target = neighbors[0]  # First neighbor
                _add_temp_effect(target, "{stat}", {amount}, turn)
    return 0
''',

    "combat_win_all_temp_buff": '''@passive("{name}")
def _passive_{snake_name}(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """{name}: {effect}"""
    if trigger == "combat_win" and owner is not None:
        turn = ctx.get("turn", 1)
        for ally_card in owner.board.alive_cards():
            _add_temp_effect(ally_card, "{stat}", {amount}, turn)
    return 0
''',

    "combat_win_accumulate": '''@passive("{name}")
def _passive_{snake_name}(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """{name}: {effect}"""
    if trigger == "combat_win":
        total_buff = card.get_meta("_{snake_name}_total", 0)
        if total_buff >= {max}:
            return 0
        
        if card.has_stat("{stat}"):
            card.add_base_stat("{stat}", {amount})
            card.set_meta("_{snake_name}_total", total_buff + {amount})
    return 0
''',

    "combo_gold": '''@passive("{name}")
def _passive_{snake_name}(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """{name}: {effect}"""
    if trigger == "pre_combat" and owner is not None:
        combo_count = ctx.get("combo_count", 0)
        if combo_count > 0:
            turn = ctx.get("turn", 1)
            last_turn = card.get_meta("_{snake_name}_turn", -1)
            if last_turn != turn:
                card.set_meta("_{snake_name}_turn", turn)
                card.set_meta("_{snake_name}_count", 0)
            
            count = card.get_meta("_{snake_name}_count", 0)
            if count < {max_per_turn}:
                owner.gold += {amount}
                owner.stats["gold_earned"] = owner.stats.get("gold_earned", 0) + {amount}
                card.set_meta("_{snake_name}_count", count + 1)
        return 1
    return 0
''',
}

def to_snake_case(name):
    """Convert card name to snake_case for function names"""
    return name.lower().replace(" ", "_").replace("-", "_")

def generate_handler_code(card_info):
    """Generate handler code for a card"""
    template_name = card_info["template"]
    if template_name not in TEMPLATES:
        return f"# TODO: Template '{template_name}' not implemented for {card_info['name']}\n"
    
    template = TEMPLATES[template_name]
    params = card_info["params"].copy()
    params["name"] = card_info["name"]
    params["snake_name"] = to_snake_case(card_info["name"])
    params["effect"] = card_info["effect"]
    
    try:
        return template.format(**params)
    except KeyError as e:
        return f"# ERROR: Missing parameter {e} for {card_info['name']}\n"

def generate_all_handlers():
    """Generate all missing handlers organized by type"""
    output = {}
    
    for passive_type, cards in MISSING_HANDLERS.items():
        code_parts = []
        code_parts.append(f"# {passive_type.upper()} HANDLERS - Missing implementations\n")
        code_parts.append("# " + "=" * 70 + "\n\n")
        
        for card_info in cards:
            code = generate_handler_code(card_info)
            code_parts.append(code)
            code_parts.append("\n")
        
        output[passive_type] = "".join(code_parts)
    
    return output

def save_generated_handlers():
    """Save generated handlers to separate files"""
    handlers = generate_all_handlers()
    
    for passive_type, code in handlers.items():
        filename = f"generated_handlers_{passive_type}.py"
        with open(filename, "w", encoding="utf-8") as f:
            f.write('"""\n')
            f.write(f"Generated {passive_type.upper()} Passive Handlers\n")
            f.write("=" * 70 + "\n")
            f.write("Auto-generated handler implementations for missing passives.\n")
            f.write('"""\n\n')
            f.write("from typing import TYPE_CHECKING\n")
            f.write("from engine_core.passives.base import passive\n")
            f.write("from engine_core.board import _find_coord, _neighbor_cards\n")
            f.write("from engine_core.effects import Effect, EffectPriority\n\n")
            f.write('if TYPE_CHECKING:\n')
            f.write('    from engine_core.card import Card\n')
            f.write('from engine_core.player import Player\n\n')
            
            # Helper functions for synergy
            if passive_type == "synergy_field":
                f.write("def _mark_pre_combat(card: 'Card') -> None:\n")
                f.write('    card.inc_meta("_sf_pc")\n\n')
                f.write("def _current_stacks(card: 'Card') -> int:\n")
                f.write('    return card.get_meta("_sf_stacks", 0)\n\n')
                f.write("def _add_temp_effect(card: 'Card', stat_name: str, delta: int, turn: int) -> None:\n")
                f.write("    if card.has_stat(stat_name):\n")
                f.write("        card.add_effect(\n")
                f.write("            Effect(\n")
                f.write('                source="synergy_field",\n')
                f.write("                stat_name=stat_name,\n")
                f.write("                delta=delta,\n")
                f.write("                duration=1,\n")
                f.write("                applied_turn=turn,\n")
                f.write("                priority=int(EffectPriority.COMBAT_DEBUFF),\n")
                f.write("            )\n")
                f.write("        )\n\n")
            
            # Helper functions for combat
            if passive_type == "combat":
                f.write("def _add_temp_effect(card: 'Card', stat_name: str, delta: int, turn: int) -> None:\n")
                f.write("    if card.has_stat(stat_name):\n")
                f.write("        card.add_effect(\n")
                f.write("            Effect(\n")
                f.write('                source="combat",\n')
                f.write("                stat_name=stat_name,\n")
                f.write("                delta=delta,\n")
                f.write("                duration=1,\n")
                f.write("                applied_turn=turn,\n")
                f.write("                priority=int(EffectPriority.COMBAT_BUFF),\n")
                f.write("            )\n")
                f.write("        )\n\n")
            
            f.write(code)
        
        print(f"✅ Generated: {filename}")

if __name__ == "__main__":
    print("🔧 Eksik handler'lar için kod üretiliyor...\n")
    save_generated_handlers()
    print("\n✨ Tamamlandı! Oluşturulan dosyalar:")
    for passive_type in MISSING_HANDLERS.keys():
        print(f"   - generated_handlers_{passive_type}.py")
    print("\n📝 Bu dosyaları ilgili modüllere kopyalayıp düzenleyebilirsiniz.")
