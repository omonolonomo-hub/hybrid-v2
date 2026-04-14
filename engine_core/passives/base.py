"""
Passive Handler Base Module

Provides decorator-based auto-registration for passive handlers.
"""

from typing import Dict, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ..card import Card
    from ..player import Player

# Central registry — populated at import time via @passive decorator
PASSIVE_HANDLERS: Dict[str, Callable] = {}


def passive(*card_names: str):
    """Decorator that registers a handler function for one or more card names.
    
    Usage:
        @passive("Ragnarök")
        def handle(card, trigger, owner, opponent, ctx):
            ...
        
        @passive("Midas", "Midas Dokunuşu")  # multiple names → same handler
        def handle(card, trigger, owner, opponent, ctx):
            ...
    
    Rules:
        - Function name does not matter (use descriptive names)
        - Decorator registers at import time, no manual dict entry needed
        - Duplicate registration raises ValueError immediately (fail-fast)
    """
    def decorator(fn: Callable) -> Callable:
        for name in card_names:
            if name in PASSIVE_HANDLERS:
                raise ValueError(
                    f"Duplicate passive registration for '{name}': "
                    f"{PASSIVE_HANDLERS[name].__name__} vs {fn.__name__}"
                )
            PASSIVE_HANDLERS[name] = fn
        return fn
    return decorator
