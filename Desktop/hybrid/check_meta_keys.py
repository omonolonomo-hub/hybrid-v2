"""Check registered meta keys"""
from engine_core.meta_keys import META_SPECS

print("Registered meta keys:")
for k in sorted(META_SPECS.keys()):
    spec = META_SPECS[k]
    print(f"  {k:30} -> {spec.value_type.__name__:5} ({spec.scope})")

print(f"\nTotal: {len(META_SPECS)} keys")
