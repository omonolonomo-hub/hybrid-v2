import json
import os
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "assets", "data")

with open(os.path.join(DATA_DIR, "cards.json"), encoding="utf-8") as f:
    data = json.load(f)

passives = defaultdict(list)
for c in data:
    ptype = c.get("passive_type")
    if ptype and ptype not in ["none", "combat"]:
        passives[ptype].append((c['name'], c.get('passive_effect')))

with open(os.path.join(DATA_DIR, "passives.txt"), "w", encoding="utf-8") as out:
    for ptype, items in passives.items():
        out.write(f"\n--- {ptype.upper()} ---\n")
        for name, effect in items:
            out.write(f"- {name}: {effect}\n")
