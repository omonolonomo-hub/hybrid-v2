#!/usr/bin/env python
"""Verify passive handler registration"""

from engine_core.passives.registry import PASSIVE_HANDLERS

print(f"Registered handlers: {len(PASSIVE_HANDLERS)}")
print("\nAll registered handlers:")
for name in sorted(PASSIVE_HANDLERS.keys()):
    print(f"  {name}: {PASSIVE_HANDLERS[name].__name__}")
