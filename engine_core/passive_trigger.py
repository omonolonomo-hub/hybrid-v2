"""
================================================================
|         AUTOCHESS HYBRID - Passive Trigger Module            |
|  Passive ability trigger system and logging                  |
================================================================

This module contains the passive trigger system that handles card
passive abilities and tracks their usage for statistics.
"""

from collections import defaultdict
from typing import Callable, Dict

# Import dependencies
try:
    from .passives.registry import PASSIVE_HANDLERS
    from .strategy_logger import get_strategy_logger
except ImportError:
    from passives.registry import PASSIVE_HANDLERS
    try:
        from strategy_logger import get_strategy_logger
    except ImportError:
        def get_strategy_logger(): return None


# ===================================================================
# PASSIVE TRIGGER LOG
# ===================================================================

def _create_passive_log():
    """Create a new passive trigger log instance for a game."""
    return defaultdict(lambda: defaultdict(int))


# Initialize passive trigger log
_passive_trigger_log = _create_passive_log()


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
    # Log passive trigger if it had a visual/gameplay effect
    # (Power change, points result, or it's a specific system trigger like income)
    # [FIX] Only log if a handler exists OR it's a system 'combo' trigger.
    # This prevents "ghost logs" for cards that have a passive name but no code implementation.
    has_handler = (PASSIVE_HANDLERS.get(card.name) is not None or 
                   PASSIVE_HANDLERS.get(card.name.lower().replace(" ", "_")) is not None)
    
    is_impactful = (delta != 0) or (res != 0)
    is_system_event = (trigger in ("income", "market_refresh", "combo"))
    
    should_log = (is_impactful or is_system_event) and (has_handler or trigger == "combo")
    
    if should_log and owner is not None and hasattr(owner, 'passive_buff_log'):
        entry = {
            "turn":    ctx.get("turn", 0),
            "card":    card.name,
            "passive": pt,
            "trigger": trigger,
            "delta":   delta,
            "res":     res
        }
        owner.passive_buff_log.append(entry)
        
        # Terminal debugging for Human (pid=0)
        if getattr(owner, "pid", -1) == 0:
            msg = f"[PASSIVE] {safe_name} | {trigger} -> "
            if delta > 0: msg += f"Power +{delta} "
            if res > 0:   msg += f"Result +{res} "
            if delta == 0 and res == 0: msg += "Activated"
            print(msg)

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

    turn = ctx.get("turn", 1)

    # Check if card has a specific handler
    handler = PASSIVE_HANDLERS.get(card.name)
    if handler:
        return handler(card, trigger, owner, opponent, ctx)

    # Default behaviors for passive types without specific handlers
    if pt == "copy" and trigger in ("copy_2", "copy_3"):
        # Default: +1 to highest edge
        if card.edges:
            idx = max(range(len(card.edges)), key=lambda i: card.edges[i][1])
            s, v = card.edges[idx]
            card.edges[idx] = (s, v + 1)
            card.stats[s] = v + 1
        return 0

    return 0


# ===================================================================
# HELPER FUNCTIONS
# ===================================================================

def get_passive_trigger_log():
    """Return current passive trigger log (snapshot reference)."""
    return _passive_trigger_log


def clear_passive_trigger_log():
    """Replace passive trigger log with a fresh instance.

    Re-assignment (not .clear()) ensures callers that captured a reference
    via get_passive_trigger_log() before this call still see the old data,
    eliminating the race window where .clear() could wipe data mid-read.
    """
    global _passive_trigger_log
    _passive_trigger_log = _create_passive_log()
