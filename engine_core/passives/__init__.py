"""Passive handlers package"""

try:
    from .registry import PASSIVE_HANDLERS
except ImportError:
    from passives.registry import PASSIVE_HANDLERS

__all__ = ["PASSIVE_HANDLERS"]
