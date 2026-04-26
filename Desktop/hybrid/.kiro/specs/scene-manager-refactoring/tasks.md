# Implementation Plan: Scene Manager Refactoring

## Overview

This plan refactors the Pygame-based game engine from "Multiple Game Loop" architecture to "Single Loop + Scene Manager" architecture. The implementation follows a 6-phase incremental approach, building core systems first, then implementing scenes, and finally integrating everything into the main game loop.

## Tasks

- [x] 1. Implement core infrastructure and base classes
  - [x] 1.1 Implement Scene base class with lifecycle methods
    - Create `core/scene.py` with abstract Scene class
    - Define `handle_input`, `update`, `draw` abstract methods
    - Implement `on_enter` and `on_exit` lifecycle hooks
    - Add `scene_manager` reference for transition requests
    - _Requirements: 2.1, 2.2, 2.3, 2.7_

  - [ ]* 1.2 Write property test for Scene lifecycle
    - **Property 5: UIState Lifecycle**
    - **Validates: Requirements 2.4, 2.5**

  - [x] 1.3 Implement CoreGameState for saveable state
    - Create `core/core_game_state.py` with CoreGameState class
    - Add `game`, `view_player_index`, `fast_mode` fields
    - Implement `to_dict` and `from_dict` for serialization
    - Add `current_player` property
    - _Requirements: 3.1, 3.2, 3.3_

  - [ ]* 1.4 Write property test for CoreGameState serialization
    - **Property 8: CoreGameState Serialization Round-Trip**
    - **Validates: Requirements 3.3**

  - [x] 1.5 Implement UIState for throwaway state
    - Create `core/ui_state.py` with UIState class
    - Add fields for selections, hovers, camera, temporary state
    - Initialize all fields in `__init__`
    - _Requirements: 3.4, 3.5_

- [x] 2. Implement input and hex systems
  - [x] 2.1 Implement InputState for intent-based input
    - Create `core/input_state.py` with InputState class
    - Translate pygame events to intent flags
    - Add mouse state tracking (position, clicked, released)
    - Add keyboard state tracking (pressed, held)
    - Implement intent flags (confirm, cancel, rotate_cw, rotate_ccw)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 2.2 Write property test for InputState determinism
    - **Property 9: Intent Translation Determinism**
    - **Validates: Requirements 4.1, 13.5, 13.6**

  - [ ]* 2.3 Write property test for InputState immutability
    - **Property 10: InputState Immutability**
    - **Validates: Requirements 13.4**

  - [x] 2.4 Implement HexSystem for coordinate math
    - Create `core/hex_system.py` with HexSystem class
    - Implement `pixel_to_hex` with cube rounding
    - Implement `hex_to_pixel` for rendering
    - Implement `cube_round` algorithm
    - Add `neighbors` and `distance` methods
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

  - [ ]* 2.5 Write property test for cube coordinate constraint
    - **Property 17: Cube Coordinate Constraint**
    - **Validates: Requirements 7.3**

  - [ ]* 2.6 Write property test for hex conversion round-trip
    - **Property 18: Hex Conversion Round-Trip**
    - **Validates: Requirements 7.4**

- [ ] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement animation and action systems
  - [x] 4.1 Implement Animation base class and AnimationSystem
    - Create `core/animation_system.py` with Animation base class
    - Implement `update`, `is_finished`, `draw` methods
    - Create AnimationSystem to manage animation lifecycle
    - Implement `add`, `update`, `draw`, `is_animating`, `clear` methods
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.6, 6.7_

  - [ ]* 4.2 Write property test for animation lifecycle
    - **Property 16: Animation Lifecycle**
    - **Validates: Requirements 6.2, 6.3**

  - [x] 4.3 Implement CardMoveAnimation concrete animation
    - Create CardMoveAnimation class extending Animation
    - Implement position interpolation with delta time
    - Add `get_current_pos` method for smooth movement
    - _Requirements: 6.1, 8.3_

  - [ ]* 4.4 Write property test for frame independence
    - **Property 20: Frame Independence**
    - **Validates: Requirements 8.6**

  - [x] 4.5 Implement Action base class and ActionSystem
    - Create `core/action_system.py` with Action base class
    - Define `execute` and `undo` abstract methods
    - Create ActionSystem with history and redo stacks
    - Implement `execute`, `undo`, `redo` methods
    - _Requirements: 5.1, 5.5, 12.1, 12.2, 12.4_

  - [ ]* 4.6 Write property test for action success behavior
    - **Property 11: Action Success Behavior**
    - **Validates: Requirements 5.2, 5.4, 6.5**

  - [ ]* 4.7 Write property test for action failure behavior
    - **Property 12: Action Failure Behavior**
    - **Validates: Requirements 5.3, 15.5**

  - [ ]* 4.8 Write property test for action undo correctness
    - **Property 13: Action Undo Correctness**
    - **Validates: Requirements 5.6, 12.3**

  - [x] 4.9 Implement PlaceCardAction concrete action
    - Create PlaceCardAction class extending Action
    - Implement validation, execution, and undo logic
    - Spawn CardMoveAnimation on successful execution
    - Save previous state for undo support
    - _Requirements: 5.2, 5.3, 5.4, 5.6, 5.7_

  - [x] 4.10 Implement BuyCardAction concrete action
    - Create BuyCardAction class extending Action
    - Implement gold validation and card purchase logic
    - Spawn CardMoveAnimation on successful purchase
    - Save previous state for undo support
    - _Requirements: 5.2, 5.3, 5.4, 5.6, 5.7_

- [x] 5. Implement SceneManager with transition logic
  - [x] 5.1 Implement SceneManager core functionality
    - Create `core/scene_manager.py` with SceneManager class
    - Implement `__init__` to initialize with initial scene
    - Add `active_scene` and `_transition_requested` fields
    - Call `on_enter` on initial scene
    - _Requirements: 1.1, 1.2_

  - [ ]* 5.2 Write property test for single active scene
    - **Property 1: Single Active Scene**
    - **Validates: Requirements 1.1**

  - [x] 5.3 Implement SceneManager update with transition check
    - Implement `update` method with delta time and input state
    - Call `active_scene.handle_input(input_state)`
    - **CRITICAL**: Check `_transition_requested` BEFORE calling `active_scene.update(dt)`
    - If transition requested, call `_execute_transition()` and return early
    - Otherwise, call `active_scene.update(dt)`
    - _Requirements: 1.3, 1.6, 1.7, 10.2, 10.3, 10.4_

  - [ ]* 5.4 Write property test for transition before update
    - **Property 2: Transition Before Update**
    - **Validates: Requirements 1.3, 1.7, 10.2, 10.3**

  - [x] 5.5 Implement SceneManager draw delegation
    - Implement `draw` method to delegate to active scene
    - _Requirements: 1.6_

  - [ ]* 5.6 Write property test for method delegation
    - **Property 4: Method Delegation**
    - **Validates: Requirements 1.6**

  - [x] 5.7 Implement request_transition method
    - Add `request_transition` method to set transition flag
    - Store scene name and kwargs for later execution
    - _Requirements: 1.3_

  - [x] 5.8 Implement _execute_transition method
    - Call `active_scene.on_exit()` to discard UIState
    - Create new scene with preserved CoreGameState
    - Set new scene's `scene_manager` reference
    - Call new scene's `on_enter()` to create fresh UIState
    - Update `active_scene` reference
    - Clear `_transition_requested` flag
    - _Requirements: 1.4, 1.5, 3.6, 3.7, 10.5, 10.6, 10.7_

  - [ ]* 5.9 Write property test for scene lifecycle ordering
    - **Property 3: Scene Lifecycle Ordering**
    - **Validates: Requirements 1.4, 1.5, 2.2, 2.3**

  - [ ]* 5.10 Write property test for CoreGameState preservation
    - **Property 6: CoreGameState Preservation**
    - **Validates: Requirements 3.6, 10.5**

  - [ ]* 5.11 Write property test for UIState reset
    - **Property 7: UIState Reset**
    - **Validates: Requirements 3.7, 10.6**

  - [ ]* 5.12 Write property test for scene manager reference
    - **Property 21: Scene Manager Reference**
    - **Validates: Requirements 2.7, 10.7**

- [ ] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement concrete scene: LobbyScene
  - [x] 7.1 Create LobbyScene class structure
    - Create `scenes/lobby_scene.py` with LobbyScene class
    - Extend Scene base class
    - Implement `__init__` to accept CoreGameState
    - _Requirements: 11.1_

  - [x] 7.2 Implement LobbyScene.on_enter
    - Create fresh UIState instance
    - Initialize lobby-specific UI state (strategy selection)
    - _Requirements: 2.4, 11.5_

  - [x] 7.3 Implement LobbyScene.handle_input
    - Use InputState intents (not raw events)
    - Handle strategy selection with intent_confirm
    - Request transition to shop when ready
    - _Requirements: 4.6, 11.1, 11.6_

  - [x] 7.4 Implement LobbyScene.update
    - Update UI animations with delta time
    - No direct CoreGameState modification
    - _Requirements: 11.5_

  - [x] 7.5 Implement LobbyScene.draw
    - Render strategy selection UI
    - Highlight selected strategy
    - _Requirements: 11.1_

  - [x] 7.6 Implement LobbyScene.on_exit
    - Discard UIState
    - Cleanup scene-specific resources
    - _Requirements: 2.5, 14.1, 14.2, 14.3, 14.4_

  - [ ]* 7.7 Write integration test for LobbyScene
    - Test strategy selection flow
    - Test transition to shop scene
    - _Requirements: 11.1_

- [x] 8. Implement concrete scene: ShopScene
  - [x] 8.1 Create ShopScene class structure
    - Create `scenes/shop_scene.py` with ShopScene class
    - Extend Scene base class
    - Implement `__init__` to accept CoreGameState
    - _Requirements: 11.2_

  - [x] 8.2 Implement ShopScene.on_enter
    - Create fresh UIState instance
    - Initialize shop-specific UI state (card selection, hover)
    - _Requirements: 2.4, 11.5_

  - [x] 8.3 Implement ShopScene.handle_input for card purchasing
    - Use InputState intents for card selection
    - Create BuyCardAction when purchasing cards
    - Execute action through ActionSystem
    - Use HexSystem for coordinate conversions
    - _Requirements: 4.6, 5.7, 11.2, 11.4, 11.6, 11.7_

  - [x] 8.4 Implement ShopScene.handle_input for card placement
    - Handle card selection from hand
    - Handle rotation with intent_rotate_cw and intent_rotate_ccw
    - Create PlaceCardAction when placing cards
    - Execute action through ActionSystem
    - _Requirements: 4.6, 5.7, 11.4, 11.6, 11.7_

  - [x] 8.5 Implement ShopScene.update
    - Update camera smoothing with delta time
    - Update hover state
    - No direct CoreGameState modification
    - _Requirements: 8.4, 11.5_

  - [x] 8.6 Implement ShopScene.draw
    - Render market cards
    - Render player hand
    - Render board with hex grid using HexSystem
    - Highlight selected and hovered cards
    - _Requirements: 11.2, 11.7_

  - [x] 8.7 Implement ShopScene transition to combat
    - Request transition to combat when ready
    - _Requirements: 11.2_

  - [x] 8.8 Implement ShopScene.on_exit
    - Discard UIState
    - Cleanup scene-specific resources
    - _Requirements: 2.5, 14.1, 14.2, 14.3, 14.4_

  - [ ]* 8.9 Write integration test for ShopScene
    - Test card purchasing flow
    - Test card placement flow
    - Test transition to combat scene
    - _Requirements: 11.2_

- [x] 9. Implement concrete scene: CombatScene
  - [x] 9.1 Create CombatScene class structure
    - Create `scenes/combat_scene.py` with CombatScene class
    - Extend Scene base class
    - Implement `__init__` to accept CoreGameState
    - _Requirements: 11.3_

  - [x] 9.2 Implement CombatScene.on_enter
    - Create fresh UIState instance
    - Initialize combat-specific UI state (locked coords)
    - _Requirements: 2.4, 11.5_

  - [x] 9.3 Implement CombatScene.handle_input
    - Use InputState intents for combat controls
    - Handle cancel intent to return to shop
    - _Requirements: 4.6, 11.3, 11.6_

  - [x] 9.4 Implement CombatScene.update
    - Update combat animations with delta time
    - Update camera tracking
    - No direct CoreGameState modification
    - _Requirements: 8.4, 11.5_

  - [x] 9.5 Implement CombatScene.draw
    - Render battle visualization
    - Render hex grid with HexSystem
    - Render combat animations
    - _Requirements: 11.3, 11.7_

  - [x] 9.6 Implement CombatScene transition to shop
    - Request transition to shop when combat ends
    - _Requirements: 11.3_

  - [x] 9.7 Implement CombatScene.on_exit
    - Discard UIState
    - Cleanup scene-specific resources
    - _Requirements: 2.5, 14.1, 14.2, 14.3, 14.4_

  - [ ]* 9.8 Write integration test for CombatScene
    - Test combat visualization
    - Test transition back to shop
    - _Requirements: 11.3_

- [ ] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Integrate into main game loop
  - [x] 11.1 Refactor main.py to use single game loop
    - Remove nested while loops from old screen classes
    - Create single centralized game loop in main.py
    - Initialize pygame and create display
    - _Requirements: 9.1, 9.2_

  - [x] 11.2 Initialize core systems in main.py
    - Create AnimationSystem instance
    - Create ActionSystem instance
    - Create HexSystem instance with hex_size and origin
    - _Requirements: 6.1, 5.5, 7.7_

  - [x] 11.3 Initialize game state and SceneManager
    - Build game with strategies
    - Create CoreGameState instance
    - Create initial LobbyScene
    - Create SceneManager with initial scene
    - _Requirements: 1.2, 3.1_

  - [x] 11.4 Implement main game loop structure
    - Capture delta time with clock.tick(FPS)
    - Capture pygame events once per frame
    - Create InputState from events
    - Check for QUIT event
    - _Requirements: 9.2, 9.3, 9.7_

  - [ ]* 11.5 Write property test for delta time positivity
    - **Property 19: Delta Time Positivity**
    - **Validates: Requirements 8.5**

  - [x] 11.6 Implement game loop update phase
    - Update AnimationSystem with delta time
    - Update SceneManager with delta time and InputState
    - _Requirements: 9.4, 9.5_

  - [x] 11.7 Implement game loop render phase
    - Clear screen with background color
    - Call SceneManager.draw(screen)
    - Call AnimationSystem.draw(screen)
    - Call pygame.display.flip()
    - _Requirements: 9.6_

  - [ ]* 11.8 Write property test for no nested loops
    - **Property 22: No Nested Loops**
    - **Validates: Requirements 9.1**

- [ ] 12. Add error handling and validation
  - [ ] 12.1 Add error handling to SceneManager
    - Handle invalid scene names in request_transition
    - Log errors and remain in current scene
    - _Requirements: 15.1_

  - [ ] 12.2 Add validation to Scene constructors
    - Raise ValueError if CoreGameState is None
    - _Requirements: 15.2_

  - [ ] 12.3 Add delta time clamping in main loop
    - Clamp negative or zero delta time to minimum positive value
    - Log warning when clamping occurs
    - _Requirements: 15.3_

  - [ ] 12.4 Add coordinate validation to HexSystem
    - Return None for invalid pixel-to-hex conversions
    - _Requirements: 15.4_

  - [ ] 12.5 Add animation error handling
    - Catch and log animation errors
    - Remove problematic animations and continue
    - _Requirements: 15.6_

  - [ ]* 12.6 Write unit tests for error handling
    - Test invalid scene transition
    - Test missing CoreGameState
    - Test negative delta time
    - Test invalid coordinates
    - _Requirements: 15.1, 15.2, 15.3, 15.4_

- [ ] 13. Final integration and cleanup
  - [ ] 13.1 Remove old screen classes
    - Delete or deprecate LobbyScreen class
    - Delete or deprecate ShopScreen class
    - Update imports throughout codebase
    - _Requirements: 11.1, 11.2_

  - [ ] 13.2 Update all coordinate conversions to use HexSystem
    - Replace inline hex math with HexSystem calls
    - Ensure consistency across all scenes
    - _Requirements: 7.1, 7.2, 11.7_

  - [ ] 13.3 Verify state separation throughout codebase
    - Ensure no UI state in CoreGameState
    - Ensure no domain state in UIState
    - _Requirements: 3.1, 3.4_

  - [ ] 13.4 Add resource cleanup to all scenes
    - Verify on_exit properly releases resources
    - Check for memory leaks
    - _Requirements: 14.3, 14.5, 14.6, 14.7_

  - [ ]* 13.5 Write end-to-end integration tests
    - Test full game loop for 100 frames
    - Test all scene transitions
    - Test action execution and undo/redo
    - Verify consistent FPS
    - _Requirements: 9.1, 9.7, 12.1, 12.2, 12.3_

- [ ] 14. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The implementation follows a 6-phase approach: (1) Core infrastructure, (2) Input/Hex systems, (3) Animation/Action systems, (4) SceneManager, (5) Concrete scenes, (6) Main loop integration
- **CRITICAL**: SceneManager must check for transitions BEFORE calling scene.update() to prevent double-update bug
- All game state modifications must go through Actions (no direct modification)
- All coordinate conversions must use HexSystem (no inline hex math)
- CoreGameState is SAVEABLE (preserved across scenes), UIState is THROWAWAY (reset on scene change)
