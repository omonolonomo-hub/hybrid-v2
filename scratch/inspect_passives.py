import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine_core.passives.registry import PASSIVE_HANDLERS

print(f"Total Handlers: {len(PASSIVE_HANDLERS)}")
print("Registered Passives:")
for name in sorted(PASSIVE_HANDLERS.keys()):
    handler = PASSIVE_HANDLERS[name]
    print(f"  - {name} ({handler.__name__ if hasattr(handler, '__name__') else str(handler)})")
