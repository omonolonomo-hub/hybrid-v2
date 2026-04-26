# Implementation Plan: AssetLoader Integration

## Overview

This plan integrates AssetLoader as the single unified asset management system, replacing duplicate loading logic in ShopScene and CombatScene. The integration follows these critical design decisions:

1. **Persistent Cache**: Asset cache persists across scene transitions (NO clear() on exit)
2. **Required Parameter**: asset_loader is REQUIRED (not Optional) in scene constructors
3. **Deduplication**: Always deduplicate card names before preload: `preload(list(set(card_names)))`
4. **No Double Scaling**: Scenes use AssetLoader surfaces directly without additional scaling

## Tasks

- [x] 1. Update main.py to create AssetLoader and pass to factories
  - [x] 1.1 Import AssetLoader from scenes.asset_loader
    - Add import statement at top of main.py
    - _Requirements: 2.1, 8.1_
  
  - [x] 1.2 Create single AssetLoader instance in main()
    - Create AssetLoader with cards_dir="assets/cards" and target_size=(100, 116)
    - Place creation after pygame.init() and before scene creation
    - _Requirements: 2.1, 2.2, 18.4_
  
  - [x] 1.3 Update resolution to 1920x1080
    - Change SCREEN_WIDTH from 1600 to 1920
    - Change SCREEN_HEIGHT from 960 to 1080
    - _Requirements: 18.1, 18.2, 18.3_
  
  - [x] 1.4 Modify create_shop factory to pass asset_loader
    - Add asset_loader parameter to ShopScene constructor call
    - Use closure to capture asset_loader from main() scope
    - _Requirements: 8.3, 8.5_
  
  - [x] 1.5 Modify create_combat factory to pass asset_loader
    - Add asset_loader parameter to CombatScene constructor call
    - Use closure to capture asset_loader from main() scope
    - _Requirements: 8.4, 8.5_

- [x] 2. Checkpoint - Verify main.py changes
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Update ShopScene to use AssetLoader
  - [x] 3.1 Add required asset_loader parameter to ShopScene.__init__
    - Change asset_loader parameter from Optional to required (remove Optional type hint)
    - Add validation: `if asset_loader is None: raise ValueError("asset_loader is required for ShopScene")`
    - Store asset_loader as instance variable: `self.asset_loader = asset_loader`
    - _Requirements: 2.3, 2.5, 14.1, 19.2_
  
  - [x] 3.2 Remove inline asset loading code from ShopScene
    - Delete _load_card_assets() method entirely (lines ~355-385)
    - Delete _create_hex_placeholder() method entirely (lines ~387-467)
    - Remove self.card_front_img attribute
    - Remove self.card_back_img attribute
    - _Requirements: 1.2, 1.4_
  
  - [x] 3.3 Implement preload in ShopScene.on_enter()
    - Collect visible card names from market window
    - Collect visible card names from player board
    - Deduplicate using list(set(visible_cards))
    - Call self.asset_loader.preload(deduplicated_names)
    - _Requirements: 3.2, 4.2, 4.4, 9.2, 14.2, 14.3, 14.4_
  
  - [x] 3.4 Update ShopScene card drawing to use AssetLoader
    - In _draw_market_grid(), call self.asset_loader.get(card.name) for each card
    - Pass CardFaces to ShopCard.draw() instead of card_front_img/card_back_img
    - Update ShopCard.draw() signature to accept faces parameter
    - Use faces.front and faces.back directly (no additional scaling)
    - _Requirements: 1.2, 5.4, 7.3, 9.3, 14.5_
  
  - [x] 3.5 Remove cache clear from ShopScene.on_exit()
    - Ensure on_exit() does NOT call asset_loader.clear()
    - Cache must persist across scene transitions
    - _Requirements: 3.1, 3.2, 9.4_

- [x] 4. Checkpoint - Verify ShopScene integration
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Update CombatScene to use AssetLoader
  - [x] 5.1 Add required asset_loader parameter to CombatScene.__init__
    - Change asset_loader parameter from Optional to required (remove Optional type hint)
    - Add validation: `if asset_loader is None: raise ValueError("asset_loader is required for CombatScene")`
    - Store asset_loader as instance variable: `self.asset_loader = asset_loader`
    - _Requirements: 2.4, 2.5, 15.1, 19.2_
  
  - [x] 5.2 Remove AssetManager class from CombatScene
    - Delete entire AssetManager class definition (lines ~205-450+)
    - Remove self.asset_manager = AssetManager() from __init__
    - Remove AssetManager import if it exists
    - _Requirements: 1.3, 1.5_
  
  - [x] 5.3 Remove AssetManager dependency from HexCardRenderer
    - Update HexCardRenderer.__init__ to remove asset_manager parameter
    - Remove any asset_manager usage from HexCardRenderer methods
    - HexCardRenderer should only work with pre-loaded HexCard images
    - _Requirements: 1.3_
  
  - [x] 5.4 Implement preload in CombatScene.on_enter()
    - Collect visible card names from all player boards
    - Deduplicate using list(set(visible_cards))
    - Call self.asset_loader.preload(deduplicated_names)
    - _Requirements: 3.3, 4.3, 4.4, 9.2, 15.2, 15.3, 15.4_
  
  - [x] 5.5 Update _create_hex_card() to use AssetLoader
    - Call self.asset_loader.get(card.name) to get CardFaces
    - Use faces.front for front_image parameter
    - Use faces.back for back_image parameter
    - Do NOT apply additional scaling (surfaces already at target_size)
    - _Requirements: 1.3, 5.4, 7.4, 9.3, 15.5_
  
  - [x] 5.6 Update _preload_all_card_assets() to use AssetLoader
    - Replace asset_manager.load_card_image() calls with asset_loader.preload()
    - Collect all card names first, then call preload once with deduplicated list
    - _Requirements: 4.3, 4.4_
  
  - [x] 5.7 Remove cache clear from CombatScene.on_exit()
    - Ensure on_exit() does NOT call asset_loader.clear()
    - Cache must persist across scene transitions
    - _Requirements: 3.3, 3.4, 9.4_

- [x] 6. Checkpoint - Verify CombatScene integration
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Update PlaceCardAction to use AssetLoader
  - [x] 7.1 Add asset_loader parameter to PlaceCardAction.__init__
    - Update PlaceCardAction constructor to accept asset_loader
    - Store as instance variable
    - _Requirements: 1.3_
  
  - [x] 7.2 Replace asset_manager calls in PlaceCardAction
    - Replace asset_manager.load_card_image() with asset_loader.get()
    - Use CardFaces.front and CardFaces.back from result
    - _Requirements: 1.3_
  
  - [x] 7.3 Update ActionSystem to pass asset_loader to actions
    - Ensure ActionSystem has reference to asset_loader
    - Pass asset_loader when creating PlaceCardAction instances
    - _Requirements: 1.3_

- [x] 8. Project-wide scan for hidden dependencies
  - [x] 8.1 Search for remaining asset_manager references
    - Use grep/search to find any remaining asset_manager usage
    - Update or remove all found references
    - _Requirements: 1.1_
  
  - [x] 8.2 Search for remaining pygame.image.load() calls
    - Find any direct pygame.image.load() calls for card assets
    - Verify only AssetLoader uses pygame.image.load() for cards
    - _Requirements: 1.1_
  
  - [x] 8.3 Search for remaining _load_card_assets() references
    - Ensure no calls to removed _load_card_assets() method
    - _Requirements: 1.4_
  
  - [x] 8.4 Verify no double scaling in rendering pipeline
    - Check that scenes don't scale AssetLoader surfaces
    - Verify FlipAnimator only scales horizontally
    - _Requirements: 7.1, 7.2, 7.5, 16.2, 16.3_

- [x] 9. Final validation and testing
  - [x] 9.1 Run application and test shop scene
    - Launch application and navigate to shop
    - Verify cards render correctly
    - Verify no errors in console
    - Check loading statistics output
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  
  - [x] 9.2 Test scene transitions
    - Transition from shop to combat
    - Verify cache persists (no reload messages)
    - Transition back to shop
    - Verify cards still cached
    - _Requirements: 3.2, 3.3, 3.4, 3.5_
  
  - [x] 9.3 Test with missing card assets
    - Temporarily rename a card asset file
    - Verify placeholder generation works
    - Verify no crashes
    - Restore asset file
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 11.1, 11.2, 11.3, 11.4, 11.5_
  
  - [x] 9.4 Verify flip animations work correctly
    - Test card flip animations in shop
    - Test card flip animations in combat
    - Verify no visual artifacts or scaling issues
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5_
  
  - [x] 9.5 Check memory usage and performance
    - Monitor memory usage during scene transitions
    - Verify cache persistence reduces load times
    - Check for memory leaks
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 10. Final checkpoint - Complete integration
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- All tasks reference specific requirements for traceability
- Checkpoints ensure incremental validation
- Cache persistence is critical - never call clear() on scene exit
- asset_loader parameter is REQUIRED, not Optional
- Always deduplicate card names before preload
- No additional scaling of AssetLoader surfaces
