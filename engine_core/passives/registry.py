"""
Passive Handler Registry

Imports all handler modules so their @passive decorators fire,
then re-exports the populated PASSIVE_HANDLERS dict.

To add a new handler:
1. Write a function in the appropriate module (combat.py, economy.py, etc.)
2. Decorate it with @passive("Card Name")
3. Done. No changes needed here.
"""

try:
    from .base import PASSIVE_HANDLERS
    # Import handler modules to trigger decorator registration
    from . import combat, economy, copy_handlers, survival, synergy, combo
except ImportError:
    from passives.base import PASSIVE_HANDLERS
    from passives import combat, economy, copy_handlers, survival, synergy, combo

__all__ = ["PASSIVE_HANDLERS"]
