"""
================================================================
|         AUTOCHESS HYBRID - Passive Trigger Module            |
|  Passive ability trigger system and logging                  |
================================================================

This module contains the passive trigger system that handles card
passive abilities and tracks their usage for statistics.
"""

import logging
from collections import defaultdict
from typing import Callable, Dict

from engine_core.passives.registry import PASSIVE_HANDLERS
from engine_core.strategy_logger import get_strategy_logger

logger = logging.getLogger(__name__)

# ===================================================================
# PASSIVE TRIGGER FUNCTIONS
# ===================================================================

def trigger_passive(card: "Card", trigger: str, owner, opponent, ctx: dict, verbose: bool = False) -> int:
    """Trigger a card's passive ability.
    
    Args:
        card: The card whose passive is being triggered
        trigger: The trigger type (e.g., "combat_win", "income", etc.)
        owner: The player who owns the card
        opponent: The opponent player
        ctx: Context dictionary with game state
        verbose: Whether to print debug output
        
    Returns:
        Bonus combat points or 0 for side-effect-only passives
    """
    pt = getattr(card, "passive_type", "none")
    safe_name = card.name.encode('ascii', 'ignore').decode('ascii')
    if verbose:
        print(f"[PASSIVE] {safe_name} | {trigger}")
    power_before = card.total_power()
    res = _trigger_passive_impl(card, trigger, owner, opponent, ctx)
    delta = card.total_power() - power_before
    if verbose:
        print(f"[EFFECT] {safe_name} -> {res}")
    
    # [REENTRANCY FIX] Log to the specific game instance if available in ctx
    game_instance = ctx.get("game")
    
    # Log passive trigger if it had a visual/gameplay effect
    has_handler = (PASSIVE_HANDLERS.get(card.name) is not None or 
                   PASSIVE_HANDLERS.get(card.name.lower().replace(" ", "_")) is not None)
    
    is_impactful = (delta != 0) or (res != 0)
    is_system_event = (trigger in ("income", "market_refresh", "combo"))
    
    should_log = (is_impactful or is_system_event) and (has_handler or trigger == "combo")
    
    if should_log:
        entry = {
            "turn":    ctx.get("turn", 0),
            "card":    card.name,
            "passive": pt,
            "trigger": trigger,
            "delta":   delta,
            "res":     res
        }
        
        # 1. Player-level log (UI and internal tracking)
        if owner is not None and hasattr(owner, 'passive_buff_log'):
            owner.passive_buff_log.append(entry)
        
        # 2. Game-level global log (Sim summary tracking)
        if game_instance is not None:
            game_instance._passive_trigger_log[card.name][trigger] += 1
        
        # Terminal debugging for Human (pid=0)
        if owner is not None and getattr(owner, "pid", -1) == 0:
            msg = f"[PASSIVE] {safe_name} | {trigger} -> "
            if delta > 0: msg += f"Power +{delta} "
            if res > 0:   msg += f"Result +{res} "
            if delta == 0 and res == 0: msg += "Activated"
            logger.debug(msg)

    # -- Strategy Logger hook --
    _slogger = get_strategy_logger()
    if _slogger is not None:
        owner_strat = getattr(owner, "strategy", "unknown") if owner else "unknown"
        _slogger.log_passive(
            card_name=card.name,
            passive_type=getattr(card, "passive_type", "none"),
            trigger=trigger,
            owner_strategy=owner_strat,
            delta=delta,
            ctx_turn=ctx.get("turn", 0),
        )
    return res


def _trigger_passive_impl(card: "Card", trigger: str, owner, opponent, ctx: dict) -> int:
    """
    Fire this card's passive for the given trigger.
    Return value: bonus combat points, or 0 for side-effect-only passives.
    """
    pt = card.passive_type
    if pt == "none":
        return 0

    # Check if card has a specific handler
    handler = PASSIVE_HANDLERS.get(card.name)
    if handler:
        return handler(card, trigger, owner, opponent, ctx)

    # Default behaviors for passive types without specific handlers
    if pt == "copy" and trigger in ("copy_2", "copy_3"):
        # Default: +1 to highest edge
        if card.edges:
            idx = max(range(len(card.edges)), key=lambda i: card.edges[i][1])
            stat_name, _ = card.edges[idx]
            card.add_base_stat(stat_name, 1)
        return 0

    return 0


# ===================================================================
# DEPRECATED GLOBALS (For backward compatibility with simulations)
# ===================================================================

_legacy_passive_log = defaultdict(lambda: defaultdict(int))

def get_passive_trigger_log():
    """DEPRECATED: Returns the legacy global log. Use game._passive_trigger_log instead."""
    return _legacy_passive_log

def clear_passive_trigger_log():
    """DEPRECATED: Clears the legacy global log."""
    global _legacy_passive_log
    _legacy_passive_log = defaultdict(lambda: defaultdict(int))
