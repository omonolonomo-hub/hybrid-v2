# Requirements Document: AssetLoader Integration

## Introduction

This document specifies the requirements for integrating AssetLoader as the single unified asset management system across the game project. The integration replaces duplicate asset loading implementations in ShopScene and CombatScene with a centralized, cached asset loader that provides consistent card rendering, efficient memory usage, and proper lifecycle management. The system maintains the existing SceneManager factory pattern architecture while eliminating redundant I/O operations and ensuring asset consistency across scene transitions.

## Glossary

- **AssetLoader**: Centralized asset management system that loads, caches, and provides card images with fuzzy matching and placeholder generation
- **CardFaces**: Data structure containing front and back pygame.Surface objects for a single card
- **Scene**: A game state (Lobby, Shop, Combat) managed by SceneManager with lifecycle methods (on_enter, update, draw, on_exit)
- **SceneManager**: Orchestrates scene transitions and lifecycle using factory pattern
- **Factory_Function**: Function that creates scene instances with required dependencies
- **Cache**: In-memory dictionary storing loaded CardFaces objects keyed by normalized card names
- **Preload**: Loading card assets into cache before they are needed for rendering
- **Placeholder**: Procedurally generated neon hex image used when card asset file is missing
- **Fuzzy_Matching**: Algorithm that matches card names to asset files despite spelling variations or Turkish character differences
- **Target_Size**: Standard card dimensions (100x116 pixels) used for all card rendering
- **Normalized_Name**: Card name converted to lowercase with Turkish characters transliterated and whitespace standardized
- **Lifecycle_Method**: Scene methods called by SceneManager (on_enter, update, draw, on_exit)
- **Persistent_Cache**: Cache that remains populated across scene transitions to avoid redundant loading

## Requirements

### Requirement 1: Unified Asset Management

**User Story:** As a developer, I want a single asset loading system, so that card images are loaded consistently across all scenes without duplicate code.

#### Acceptance Criteria

1. THE AssetLoader SHALL be the only system that calls pygame.image.load() for card assets
2. WHEN ShopScene needs card images THEN THE ShopScene SHALL use AssetLoader.get() instead of inline loading
3. WHEN CombatScene needs card images THEN THE CombatScene SHALL use AssetLoader.get() instead of AssetManager
4. THE ShopScene SHALL NOT contain _load_card_assets() method after integration
5. THE CombatScene SHALL NOT contain AssetManager class after integration

### Requirement 2: Single Instance Pattern

**User Story:** As a system architect, I want exactly one AssetLoader instance, so that memory usage is controlled and cache is shared across scenes.

#### Acceptance Criteria

1. THE main.py SHALL create exactly one AssetLoader instance during initialization
2. WHEN a scene factory creates a scene THEN THE Factory_Function SHALL pass the same AssetLoader instance
3. THE ShopScene constructor SHALL require asset_loader parameter (not Optional)
4. THE CombatScene constructor SHALL require asset_loader parameter (not Optional)
5. WHEN asset_loader parameter is None THEN THE Scene constructor SHALL raise ValueError

### Requirement 3: Persistent Cache Management

**User Story:** As a performance engineer, I want asset cache to persist across scene transitions, so that cards are not reloaded when switching between shop and combat.

#### Acceptance Criteria

1. WHEN a scene exits THEN THE Scene SHALL NOT call asset_loader.clear()
2. WHEN transitioning from ShopScene to CombatScene THEN THE Cache SHALL retain all previously loaded cards
3. WHEN transitioning from CombatScene to ShopScene THEN THE Cache SHALL retain all previously loaded cards
4. THE AssetLoader.clear() method SHALL only be called when the application terminates
5. FOR ALL scene transitions, THE Cache size SHALL be monotonically non-decreasing

### Requirement 4: Targeted Preloading

**User Story:** As a performance engineer, I want only visible cards preloaded, so that memory usage is minimized and loading time is reduced.

#### Acceptance Criteria

1. WHEN a scene enters THEN THE Scene SHALL call asset_loader.preload() with only visible card names
2. THE ShopScene.on_enter() SHALL preload market window cards and player board cards
3. THE CombatScene.on_enter() SHALL preload all cards on all player boards
4. WHEN preloading cards THEN THE Scene SHALL deduplicate card names before calling preload()
5. THE AssetLoader.preload() SHALL skip cards that are already in cache

### Requirement 5: Guaranteed Asset Availability

**User Story:** As a game developer, I want asset loading to never fail, so that the game continues running even with missing asset files.

#### Acceptance Criteria

1. THE AssetLoader.get() SHALL never return None
2. WHEN a card asset file is missing THEN THE AssetLoader SHALL generate a neon hex placeholder
3. WHEN pygame.image.load() raises an exception THEN THE AssetLoader SHALL catch it and generate a placeholder
4. THE CardFaces object SHALL always contain valid pygame.Surface objects for front and back
5. THE CardFaces.is_placeholder flag SHALL indicate whether placeholder was generated

### Requirement 6: Fuzzy Name Matching

**User Story:** As a content creator, I want card names to match asset files despite spelling variations, so that minor naming inconsistencies don't break rendering.

#### Acceptance Criteria

1. WHEN matching card names to files THEN THE AssetLoader SHALL normalize Turkish characters (ş→s, ğ→g, ü→u, ö→o, ç→c, ı→i)
2. WHEN matching card names to files THEN THE AssetLoader SHALL normalize whitespace and underscores
3. WHEN exact match fails THEN THE AssetLoader SHALL attempt partial token matching
4. WHEN partial matching finds multiple candidates THEN THE AssetLoader SHALL select the best match by token overlap score
5. WHEN no match is found with ≥60% token overlap THEN THE AssetLoader SHALL generate a placeholder

### Requirement 7: Consistent Card Dimensions

**User Story:** As a UI designer, I want all cards rendered at the same size, so that the visual presentation is consistent across scenes.

#### Acceptance Criteria

1. THE AssetLoader SHALL scale all loaded card images to target_size=(100, 116)
2. WHEN AssetLoader loads a card image THEN THE AssetLoader SHALL use pygame.transform.smoothscale()
3. THE ShopScene SHALL use card surfaces from AssetLoader without additional scaling
4. THE CombatScene SHALL use card surfaces from AssetLoader without additional scaling
5. THE FlipAnimator SHALL only scale horizontally (width) and SHALL NOT scale vertically (height)

### Requirement 8: Factory Pattern Preservation

**User Story:** As a system architect, I want scene creation to follow factory pattern, so that dependency injection is centralized and testable.

#### Acceptance Criteria

1. THE main.py SHALL register scene factories with SceneManager
2. WHEN SceneManager transitions to a scene THEN THE SceneManager SHALL call the registered Factory_Function
3. THE create_shop factory SHALL pass asset_loader parameter to ShopScene constructor
4. THE create_combat factory SHALL pass asset_loader parameter to CombatScene constructor
5. THE Factory_Function SHALL use closure to capture asset_loader reference from main.py scope

### Requirement 9: Asset Loading Lifecycle

**User Story:** As a game developer, I want clear asset loading lifecycle, so that I know when assets are loaded and when memory is freed.

#### Acceptance Criteria

1. WHEN a scene is created THEN THE Scene constructor SHALL NOT load any assets
2. WHEN a scene enters THEN THE Scene.on_enter() SHALL call asset_loader.preload()
3. WHEN a scene draws THEN THE Scene.draw() SHALL call asset_loader.get() for each visible card
4. WHEN a scene exits THEN THE Scene.on_exit() SHALL NOT call asset_loader.clear()
5. THE AssetLoader SHALL print loading statistics after preload() completes

### Requirement 10: Error Reporting and Diagnostics

**User Story:** As a developer, I want detailed asset loading reports, so that I can identify missing or incomplete card assets.

#### Acceptance Criteria

1. WHEN AssetLoader.preload() completes THEN THE AssetLoader SHALL print a loading report
2. THE loading report SHALL include count of fully loaded cards (front + back)
3. THE loading report SHALL include count of partially loaded cards (one face missing)
4. THE loading report SHALL include count of completely missing cards (both faces missing)
5. THE loading report SHALL list names of all partially loaded and missing cards

### Requirement 11: Placeholder Visual Design

**User Story:** As a UI designer, I want missing card placeholders to be visually distinct, so that players and developers can identify missing assets.

#### Acceptance Criteria

1. WHEN generating a placeholder THEN THE AssetLoader SHALL create a neon hex shape
2. THE placeholder front face SHALL display card initials in bright neon color
3. THE placeholder back face SHALL display "?" in muted neon color
4. THE placeholder color hue SHALL be derived from card name hash for consistency
5. THE placeholder SHALL include hex outline and inner glow effect

### Requirement 12: Memory Efficiency

**User Story:** As a performance engineer, I want efficient memory usage, so that the game runs smoothly on target hardware.

#### Acceptance Criteria

1. THE AssetLoader SHALL cache each card exactly once regardless of how many times get() is called
2. WHEN a card is already in cache THEN THE AssetLoader.get() SHALL return cached instance without I/O
3. WHEN a card is already in cache THEN THE AssetLoader.preload() SHALL skip that card
4. THE AssetLoader SHALL use pygame.Surface.convert_alpha() for optimal blitting performance
5. THE Cache SHALL use normalized names as keys to prevent duplicate entries for same card

### Requirement 13: Directory Scanning

**User Story:** As a developer, I want automatic asset discovery, so that I don't need to manually register each card asset.

#### Acceptance Criteria

1. WHEN AssetLoader first needs assets THEN THE AssetLoader SHALL scan the cards directory
2. THE AssetLoader SHALL only scan the directory once per application lifetime
3. WHEN scanning THEN THE AssetLoader SHALL process only files with .png extension
4. WHEN scanning THEN THE AssetLoader SHALL identify front faces by "_front.png" suffix
5. WHEN scanning THEN THE AssetLoader SHALL identify back faces by "_back.png" suffix

### Requirement 14: Scene Integration - ShopScene

**User Story:** As a shop scene developer, I want AssetLoader integrated into ShopScene, so that market cards are loaded efficiently.

#### Acceptance Criteria

1. THE ShopScene constructor SHALL accept asset_loader parameter as required argument
2. WHEN ShopScene.on_enter() is called THEN THE ShopScene SHALL collect visible card names from market and board
3. WHEN ShopScene.on_enter() is called THEN THE ShopScene SHALL deduplicate card names using set()
4. WHEN ShopScene.on_enter() is called THEN THE ShopScene SHALL call asset_loader.preload() with deduplicated names
5. WHEN ShopScene draws a card THEN THE ShopScene SHALL call asset_loader.get() to retrieve CardFaces

### Requirement 15: Scene Integration - CombatScene

**User Story:** As a combat scene developer, I want AssetLoader integrated into CombatScene, so that board cards are loaded efficiently.

#### Acceptance Criteria

1. THE CombatScene constructor SHALL accept asset_loader parameter as required argument
2. WHEN CombatScene.on_enter() is called THEN THE CombatScene SHALL collect visible card names from all player boards
3. WHEN CombatScene.on_enter() is called THEN THE CombatScene SHALL deduplicate card names using set()
4. WHEN CombatScene.on_enter() is called THEN THE CombatScene SHALL call asset_loader.preload() with deduplicated names
5. WHEN CombatScene creates a HexCard THEN THE CombatScene SHALL call asset_loader.get() to retrieve CardFaces

### Requirement 16: Flip Animation Compatibility

**User Story:** As an animation developer, I want AssetLoader to work with flip animations, so that card reveal effects continue functioning.

#### Acceptance Criteria

1. THE FlipAnimator SHALL accept CardFaces objects from AssetLoader
2. WHEN FlipAnimator animates THEN THE FlipAnimator SHALL scale only the width dimension
3. WHEN FlipAnimator animates THEN THE FlipAnimator SHALL preserve the height dimension
4. THE FlipAnimator SHALL create a new surface for each frame without modifying the cached surface
5. THE FlipAnimator SHALL center the scaled surface within the original card dimensions

### Requirement 17: Backward Compatibility During Migration

**User Story:** As a developer, I want phased migration, so that I can integrate AssetLoader incrementally without breaking the build.

#### Acceptance Criteria

1. WHEN Phase 1 completes THEN THE main.py SHALL create AssetLoader but scenes may still use old loading
2. WHEN Phase 2 completes THEN THE ShopScene SHALL use AssetLoader and old loading code SHALL be removed
3. WHEN Phase 3 completes THEN THE CombatScene SHALL use AssetLoader and AssetManager SHALL be removed
4. WHEN Phase 4 completes THEN THE ActionSystem SHALL use AssetLoader for dynamic card placement
5. WHEN Phase 5 completes THEN THE codebase SHALL contain no references to AssetManager or inline asset loading

### Requirement 18: Resolution Configuration

**User Story:** As a system administrator, I want correct screen resolution, so that card dimensions are calculated correctly.

#### Acceptance Criteria

1. THE main.py SHALL set SCREEN_WIDTH to 1920
2. THE main.py SHALL set SCREEN_HEIGHT to 1080
3. THE AssetLoader CARD_SIZE calculation SHALL assume 1920x1080 resolution
4. THE target_size parameter SHALL be (100, 116) matching CARD_SIZE constant
5. WHEN resolution changes THEN THE AssetLoader SHALL be recreated with new target_size

### Requirement 19: Type Safety

**User Story:** As a developer, I want type-safe interfaces, so that integration errors are caught at development time.

#### Acceptance Criteria

1. THE AssetLoader.get() return type SHALL be CardFaces (not Optional[CardFaces])
2. THE Scene constructor asset_loader parameter type SHALL be AssetLoader (not Optional[AssetLoader])
3. THE CardFaces dataclass SHALL use type hints for all fields
4. THE AssetLoader._cache type SHALL be dict[str, CardFaces]
5. THE AssetLoader.preload() parameter type SHALL be list[str]

### Requirement 20: Testing Support

**User Story:** As a QA engineer, I want testable asset loading, so that I can verify correct behavior in automated tests.

#### Acceptance Criteria

1. THE AssetLoader SHALL support initialization with non-existent directory for testing
2. WHEN directory does not exist THEN THE AssetLoader SHALL print warning and continue with empty file_map
3. THE AssetLoader.get_missing() method SHALL return list of cards with missing or partial assets
4. THE AssetLoader.is_fully_loaded() method SHALL return True only when all cards have both faces
5. THE AssetLoader SHALL be mockable for unit testing scene integration
