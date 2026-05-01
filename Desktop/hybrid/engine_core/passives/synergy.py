"""
Synergy Field Passive Handlers

These handlers trigger on pre_combat. Permanent growth uses base stats plus meta,
while short-lived combat debuffs use the effect layer.
"""

from typing import TYPE_CHECKING

from engine_core.board import _find_coord, _neighbor_cards
from engine_core.effects import Effect, EffectPriority
from engine_core.passives.base import passive

if TYPE_CHECKING:
    from engine_core.card import Card
from engine_core.player import Player


def _mark_pre_combat(card: "Card") -> None:
    card.inc_meta("_sf_pc")


def _current_stacks(card: "Card") -> int:
    return card.get_meta("_sf_stacks", 0)


def _add_temp_effect(card: "Card", stat_name: str, delta: int, turn: int) -> None:
    if card.has_stat(stat_name):
        card.add_effect(
            Effect(
                source="synergy_field",
                stat_name=stat_name,
                delta=delta,
                duration=1,
                applied_turn=turn,
                priority=int(EffectPriority.COMBAT_DEBUFF),
            )
        )


@passive("Odin")
def _passive_odin(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Odin: Buff neighboring Mythology & Gods cards' Meaning by +1 (capped at 6 stacks)."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        stacks = _current_stacks(card)
        if stacks >= 6:
            return 1

        coord = _find_coord(owner.board, card)
        if coord:
            buffed = False
            for neighbor_card in _neighbor_cards(owner.board, coord):
                if neighbor_card.category == "Mythology & Gods" and neighbor_card.has_stat("Meaning"):
                    neighbor_card.add_base_stat("Meaning", 1)
                    buffed = True
            if buffed:
                card.set_meta("_sf_stacks", stacks + 1)
        return 1
    return 0


@passive("Olympus")
def _passive_olympus(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Olympus: If 2+ neighboring Mythology & Gods cards, buff all their Prestige by +1."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        coord = _find_coord(owner.board, card)
        mito_neighbors = []
        if coord:
            mito_neighbors = [
                neighbor_card
                for neighbor_card in _neighbor_cards(owner.board, coord)
                if neighbor_card.category == "Mythology & Gods"
            ]
        if len(mito_neighbors) >= 2:
            for neighbor_card in mito_neighbors:
                if neighbor_card.has_stat("Prestige"):
                    neighbor_card.add_base_stat("Prestige", 1)
        return 1
    return 0


@passive("Medusa")
def _passive_medusa(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Medusa: Reduce all enemy cards' Speed by -1 for this combat."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        if opponent:
            turn = ctx.get("turn", 1)
            for other_card in opponent.board.alive_cards():
                _add_temp_effect(other_card, "Speed", -1, turn)
        return 1
    return 0


@passive("Black Hole")
def _passive_black_hole(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Black Hole: Reduce enemy center card's Gravity by -1 for this combat."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        if opponent:
            center = opponent.board.grid.get((0, 0))
            if center:
                _add_temp_effect(center, "Gravity", -1, ctx.get("turn", 1))
        return 1
    return 0


@passive("Entropy")
def _passive_entropy(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Entropy: Every 3rd turn, all neighbors lose their highest edge."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        turn = ctx.get("turn", 1)
        if turn % 3 == 0:
            coord = _find_coord(owner.board, card)
            if coord:
                for neighbor_card in _neighbor_cards(owner.board, coord):
                    neighbor_card.lose_highest_edge()
        return 1
    return 0


@passive("Gravity")
def _passive_gravity(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Gravity: Reduce all neighbors' Speed by -1 for this combat."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        coord = _find_coord(owner.board, card)
        if coord:
            turn = ctx.get("turn", 1)
            for neighbor_card in _neighbor_cards(owner.board, coord):
                _add_temp_effect(neighbor_card, "Speed", -1, turn)
        return 1
    return 0


@passive("Isaac Newton")
def _passive_isaac_newton(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Isaac Newton: If 3+ Science cards on board, buff all their Intelligence by +1 (capped at 6 stacks)."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        stacks = _current_stacks(card)
        if stacks >= 6:
            return 1

        science_cards = [board_card for board_card in owner.board.alive_cards() if board_card.category == "Science"]
        if len(science_cards) >= 3:
            for science_card in science_cards:
                if science_card.has_stat("Intelligence"):
                    science_card.add_base_stat("Intelligence", 1)
            card.set_meta("_sf_stacks", stacks + 1)
        return 1
    return 0


@passive("Nikola Tesla")
def _passive_nikola_tesla(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Nikola Tesla: Buff neighboring Science cards' Intelligence by +1 (capped at 6 stacks)."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        stacks = _current_stacks(card)
        if stacks >= 6:
            return 1

        coord = _find_coord(owner.board, card)
        if coord:
            buffed = False
            for neighbor_card in _neighbor_cards(owner.board, coord):
                if neighbor_card.category == "Science" and neighbor_card.has_stat("Intelligence"):
                    neighbor_card.add_base_stat("Intelligence", 1)
                    buffed = True
            if buffed:
                card.set_meta("_sf_stacks", stacks + 1)
        return 1
    return 0


@passive("Black Death")
def _passive_black_death(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Black Death: Reduce all enemy cards' Spread by -1 for this combat."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        if opponent:
            turn = ctx.get("turn", 1)
            for other_card in opponent.board.alive_cards():
                _add_temp_effect(other_card, "Spread", -1, turn)
        return 1
    return 0


@passive("French Revolution")
def _passive_french_revolution(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """French Revolution: If 3+ History & Civilizations cards, reduce enemy's highest stat by -1 for this combat."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        hist_count = sum(
            1
            for board_card in owner.board.alive_cards()
            if board_card.category == "History & Civilizations"
        )
        if hist_count >= 3 and opponent:
            best_opponent = None
            best_stat = None
            best_value = -1
            for opponent_card in opponent.board.alive_cards():
                for stat_name, value in opponent_card.stats.items():
                    if value > best_value:
                        best_value = value
                        best_opponent = opponent_card
                        best_stat = stat_name
            if best_opponent is not None and best_stat is not None:
                _add_temp_effect(best_opponent, best_stat, -1, ctx.get("turn", 1))
        return 1
    return 0


@passive("Opera")
def _passive_opera(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Opera: When 2+ Art cards on board, +1 Prestige to all Art cards."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        stacks = _current_stacks(card)
        if stacks >= 6:
            return 1
        
        art_cards = [c for c in owner.board.alive_cards() if "Art" in c.category]
        if len(art_cards) >= 2:
            for art_card in art_cards:
                if art_card.has_stat("Prestige"):
                    art_card.add_base_stat("Prestige", 1)
            card.set_meta("_sf_stacks", stacks + 1)
        return 1
    return 0


@passive("Baroque")
def _passive_baroque(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Baroque: When 2+ Art cards on board, +1 to Prestige edges."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        stacks = _current_stacks(card)
        if stacks >= 6:
            return 1
        
        art_cards = [c for c in owner.board.alive_cards() if "Art" in c.category]
        if len(art_cards) >= 2:
            for art_card in art_cards:
                if art_card.has_stat("Prestige"):
                    art_card.add_base_stat("Prestige", 1)
            card.set_meta("_sf_stacks", stacks + 1)
        return 1
    return 0


@passive("Blue Whale")
def _passive_blue_whale(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Blue Whale: When 3+ Nature cards on board, +1 Harmony to all ally cards."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        nature_cards = [c for c in owner.board.alive_cards() if "Nature" in c.category]
        if len(nature_cards) >= 3:
            for ally_card in owner.board.alive_cards():
                if ally_card.has_stat("Harmony"):
                    ally_card.add_base_stat("Harmony", 1)
        return 1
    return 0


@passive("Coral Reef")
def _passive_coral_reef(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Coral Reef: Spreads +1 Harmony to neighboring ally Nature cards per turn."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        stacks = _current_stacks(card)
        if stacks >= 6:
            return 1
        
        coord = _find_coord(owner.board, card)
        if coord:
            buffed = False
            for neighbor_card in _neighbor_cards(owner.board, coord):
                if "Nature" in neighbor_card.category and neighbor_card.has_stat("Harmony"):
                    neighbor_card.add_base_stat("Harmony", 1)
                    buffed = True
            if buffed:
                card.set_meta("_sf_stacks", stacks + 1)
        return 1
    return 0


@passive("Rainforest")
def _passive_rainforest(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Rainforest: When 4+ Nature cards on board, +1 Spread to all Nature cards."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        stacks = _current_stacks(card)
        if stacks >= 6:
            return 1
        
        nature_cards = [c for c in owner.board.alive_cards() if "Nature" in c.category]
        if len(nature_cards) >= 4:
            for nature_card in nature_cards:
                if nature_card.has_stat("Spread"):
                    nature_card.add_base_stat("Spread", 1)
            card.set_meta("_sf_stacks", stacks + 1)
        return 1
    return 0


@passive("Cordyceps")
def _passive_cordyceps(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Cordyceps: While on board, opponent's neighboring cards take -1 Trace per turn."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        coord = _find_coord(owner.board, card)
        if coord and opponent:
            turn = ctx.get("turn", 1)
            for neighbor_card in _neighbor_cards(owner.board, coord):
                _add_temp_effect(neighbor_card, "Trace", -1, turn)
        return 1
    return 0


@passive("Milky Way")
def _passive_milky_way(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Milky Way: When 3+ Cosmos cards on board, +1 Gravity to all Cosmos cards."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        stacks = _current_stacks(card)
        if stacks >= 6:
            return 1
        
        cosmos_cards = [c for c in owner.board.alive_cards() if "Cosmos" in c.category]
        if len(cosmos_cards) >= 3:
            for cosmos_card in cosmos_cards:
                if cosmos_card.has_stat("Gravity"):
                    cosmos_card.add_base_stat("Gravity", 1)
            card.set_meta("_sf_stacks", stacks + 1)
        return 1
    return 0


@passive("Andromeda Galaxy")
def _passive_andromeda_galaxy(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Andromeda Galaxy: When 4+ Cosmos cards on board, Gravity edges +2."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        stacks = _current_stacks(card)
        if stacks >= 6:
            return 1
        
        cosmos_cards = [c for c in owner.board.alive_cards() if "Cosmos" in c.category]
        if len(cosmos_cards) >= 4:
            for cosmos_card in cosmos_cards:
                if cosmos_card.has_stat("Gravity"):
                    cosmos_card.add_base_stat("Gravity", 2)
            card.set_meta("_sf_stacks", stacks + 1)
        return 1
    return 0


@passive("Europa")
def _passive_europa(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Europa: Spreads +1 Harmony to neighboring ally Cosmos cards."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        stacks = _current_stacks(card)
        if stacks >= 6:
            return 1
        
        coord = _find_coord(owner.board, card)
        if coord:
            buffed = False
            for neighbor_card in _neighbor_cards(owner.board, coord):
                if "Cosmos" in neighbor_card.category and neighbor_card.has_stat("Harmony"):
                    neighbor_card.add_base_stat("Harmony", 1)
                    buffed = True
            if buffed:
                card.set_meta("_sf_stacks", stacks + 1)
        return 1
    return 0


@passive("Quasar")
def _passive_quasar(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Quasar: When 3+ Cosmos cards on board, +1 Spread to all cards."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        cosmos_cards = [c for c in owner.board.alive_cards() if "Cosmos" in c.category]
        if len(cosmos_cards) >= 3:
            for ally_card in owner.board.alive_cards():
                if ally_card.has_stat("Spread"):
                    ally_card.add_base_stat("Spread", 1)
        return 1
    return 0


@passive("Periodic Table")
def _passive_periodic_table(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Periodic Table: When 4+ Science cards on board, +1 Intelligence +1 Meaning to all Science cards."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        stacks = _current_stacks(card)
        if stacks >= 6:
            return 1
        
        science_cards = [c for c in owner.board.alive_cards() if "Science" in c.category]
        if len(science_cards) >= 4:
            for science_card in science_cards:
                if science_card.has_stat("Intelligence"):
                    science_card.add_base_stat("Intelligence", 1)
                if science_card.has_stat("Meaning"):
                    science_card.add_base_stat("Meaning", 1)
            card.set_meta("_sf_stacks", stacks + 1)
        return 1
    return 0


@passive("Higgs Boson")
def _passive_higgs_boson(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Higgs Boson: While on board, all cards' Gravity edges +1."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        # Buff all cards on both boards
        for ally_card in owner.board.alive_cards():
            if ally_card.has_stat("Gravity"):
                ally_card.add_base_stat("Gravity", 1)
        if opponent:
            for enemy_card in opponent.board.alive_cards():
                if enemy_card.has_stat("Gravity"):
                    enemy_card.add_base_stat("Gravity", 1)
        return 1
    return 0


@passive("Renaissance")
def _passive_renaissance(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Renaissance: When 3+ cards from different categories on board, +1 Meaning to all cards."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        categories = set(c.category for c in owner.board.alive_cards())
        if len(categories) >= 3:
            for ally_card in owner.board.alive_cards():
                if ally_card.has_stat("Meaning"):
                    ally_card.add_base_stat("Meaning", 1)
        return 1
    return 0


@passive("Roman Empire")
def _passive_roman_empire(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Roman Empire: When 4+ History cards on board, +1 Durability to all ally cards."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        history_cards = [c for c in owner.board.alive_cards() if "History" in c.category]
        if len(history_cards) >= 4:
            for ally_card in owner.board.alive_cards():
                if ally_card.has_stat("Durability"):
                    ally_card.add_base_stat("Durability", 1)
        return 1
    return 0


@passive("Kraken")
def _passive_kraken(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Kraken: While on board, neighboring enemy cards' Connection edges take -1 field effect."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        coord = _find_coord(owner.board, card)
        if coord and opponent:
            turn = ctx.get("turn", 1)
            # Apply debuff to all enemy cards (simplified - affects all enemies)
            for enemy_card in opponent.board.alive_cards():
                _add_temp_effect(enemy_card, "Connection", -1, turn)
        return 1
    return 0


@passive("Kabuki")
def _passive_kabuki(card: "Card", trigger: str, owner: "Player", opponent: "Player", ctx: dict) -> int:
    """Kabuki: When Eclipse active, spreads +1 Secret to neighboring ally cards."""
    if trigger == "pre_combat" and owner is not None:
        _mark_pre_combat(card)
        # Check if Eclipse is active (simplified - always apply for now)
        coord = _find_coord(owner.board, card)
        if coord:
            for neighbor_card in _neighbor_cards(owner.board, coord):
                if neighbor_card.has_stat("Secret"):
                    neighbor_card.add_base_stat("Secret", 1)
        return 1
    return 0
