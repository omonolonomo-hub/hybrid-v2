import os
import re

def update_ai_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 1. Update method signatures
    content = re.sub(
        r"def buy_cards\(player: Player, market: List\[Card\], max_cards: int = 1,\s+market_obj=None, rng=None, trigger_passive_fn=None,\s+ai_instance=None\):",
        "def buy_cards(player: Player, market: List[Card], max_cards: int = 1,\n                  market_obj=None, rng=None, trigger_passive_fn=None,\n                  ai_instance=None, next_uid_fn=None):",
        content
    )

    content = re.sub(
        r"def _buy_([a-z_]+)\(player: Player, market: List\[Card\], max_cards: int,\s+market_obj=None, rng=None, trigger_passive_fn=None,\s+ai_instance=None\):",
        r"def _buy_\1(player: Player, market: List[Card], max_cards: int,\n                    market_obj=None, rng=None, trigger_passive_fn=None,\n                    ai_instance=None, next_uid_fn=None):",
        content
    )

    # 2. Update calls to _buy_... within buy_cards
    content = re.sub(
        r"AI\._buy_([a-z_]+)\(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance\)",
        r"AI._buy_\1(player, market, max_cards, market_obj, rng, trigger_passive_fn, ai_instance, next_uid_fn)",
        content
    )

    # 3. Update player.buy_card calls to pass uid
    content = re.sub(
        r"player\.buy_card\((.*?), market=market_obj, trigger_passive_fn=trigger_passive_fn\)",
        r"player.buy_card(\1, market=market_obj, trigger_passive_fn=trigger_passive_fn, uid=next_uid_fn() if next_uid_fn else 0)",
        content
    )

    # 4. Update ParameterizedAI.buy_cards
    content = re.sub(
        r"def buy_cards\(self, player: Player, market: List\[Card\], max_cards: int = 1,\s+market_obj=None, rng=None, trigger_passive_fn=None\):",
        "def buy_cards(self, player: Player, market: List[Card], max_cards: int = 1,\n                  market_obj=None, rng=None, trigger_passive_fn=None, next_uid_fn=None):",
        content
    )
    content = re.sub(
        r"AI\.buy_cards\(player, market, max_cards, market_obj, rng,\s+trigger_passive_fn, ai_instance=self\)",
        "AI.buy_cards(player, market, max_cards, market_obj, rng,\n                     trigger_passive_fn, ai_instance=self, next_uid_fn=next_uid_fn)",
        content
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

update_ai_file("engine_core/ai.py")
