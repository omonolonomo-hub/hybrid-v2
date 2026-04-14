# Bugfix Requirements Document

## Introduction

This document addresses four critical runtime errors in the pygame-based autochess game that prevent normal gameplay. These errors occur in the combat scene's card rendering system, the shop scene's market refresh functionality, and asset loading. The bugs cause AttributeErrors that crash the game during normal user interactions (hovering over cards, refreshing the market).

The fixes are straightforward attribute name corrections and API call updates to match the actual implementations in the codebase.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the user hovers over a placed card in combat_scene.py line 2010 THEN the system crashes with `AttributeError: 'HexCard' object has no attribute 'card'`

1.2 WHEN the user hovers over a placed card in combat_scene_alternative.py line 1904 THEN the system crashes with `AttributeError: 'HexCard' object has no attribute 'card'`

1.3 WHEN the user clicks the refresh button in shop_scene.py line 546 THEN the system crashes with `AttributeError: 'Market' object has no attribute 'refresh_window'`

1.4 WHEN main.py imports SHOP_CARD_SIZE and CARD_SIZE from scenes/asset_loader.py THEN the system successfully imports these constants (this is already working correctly)

### Expected Behavior (Correct)

2.1 WHEN the user hovers over a placed card in combat_scene.py line 2010 THEN the system SHALL access `hex_card.card_data` instead of `hex_card.card` to retrieve the card object

2.2 WHEN the user hovers over a placed card in combat_scene_alternative.py line 1904 THEN the system SHALL access `hex_card.card_data` instead of `hex_card.card` to retrieve the card object

2.3 WHEN the user clicks the refresh button in shop_scene.py line 546 THEN the system SHALL call the correct Market API methods: `market._return_window(player.pid)` followed by `market.deal_market_window(player, n=5)` instead of the non-existent `refresh_window()` method

2.4 WHEN main.py imports SHOP_CARD_SIZE and CARD_SIZE from scenes/asset_loader.py THEN the system SHALL continue to successfully import these constants (no change needed)

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the HexCard dataclass is used elsewhere in the codebase THEN the system SHALL CONTINUE TO use the `card_data` attribute name consistently

3.2 WHEN the Market class methods are called elsewhere in the codebase THEN the system SHALL CONTINUE TO use the correct API: `deal_market_window(player, n=5)` and `_return_window(pid)`

3.3 WHEN AssetLoader constants are imported in main.py THEN the system SHALL CONTINUE TO successfully import SHOP_CARD_SIZE and CARD_SIZE

3.4 WHEN cards are rendered in combat_scene.py THEN the system SHALL CONTINUE TO access card properties through `hex_card.card_data.rotated_edges()` and other card_data methods

3.5 WHEN HandPanel accesses card attributes THEN the system SHALL CONTINUE TO use the corrected methods: `card.dominant_group()`, `card.passive_type`, and `card.total_power()`
