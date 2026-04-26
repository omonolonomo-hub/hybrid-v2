# Bugfix Requirements Document

## Introduction

The `build_card_pool()` function in `engine_core/card.py` uses an incorrect file path to locate `cards.json`. The current implementation assumes the file is at `../assets/data/cards.json` relative to the `engine_core/` directory, but this path may not work in all environments. The fix adds a fallback mechanism that checks for the file in the same directory as `card.py` first, then falls back to the original path.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN `build_card_pool()` is called THEN the system constructs the path as `os.path.join(base_dir, "..", "assets", "data", "cards.json")` without checking if the file exists

1.2 WHEN the cards.json file is not at the expected relative path THEN the system may fail to load the card pool with a FileNotFoundError

### Expected Behavior (Correct)

2.1 WHEN `build_card_pool()` is called THEN the system SHALL first check for cards.json in the same directory as card.py using `os.path.join(base_dir, "cards.json")`

2.2 WHEN cards.json is not found in the same directory as card.py THEN the system SHALL fall back to the original path `os.path.join(base_dir, "..", "assets", "data", "cards.json")`

### Unchanged Behavior (Regression Prevention)

3.1 WHEN cards.json exists at the original path `../assets/data/cards.json` relative to engine_core/ THEN the system SHALL CONTINUE TO load the card pool successfully

3.2 WHEN the loaded JSON data contains valid card entries THEN the system SHALL CONTINUE TO parse and create Card objects with the same structure (name, category, rarity, stats, passive_type)

3.3 WHEN `build_card_pool()` returns the card list THEN the system SHALL CONTINUE TO return a List[Card] with all cards from the JSON file
