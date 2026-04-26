# Requirements Document: Scene Manager Refactoring

## Introduction

This document specifies the functional requirements for refactoring a Pygame-based game engine from a "Multiple Game Loop" architecture to a "Single Loop + Scene Manager" architecture. The refactoring addresses critical issues including animation desync, input lag, state management bugs, and lack of visual feedback systems. The new architecture introduces centralized scene management, intent-based input handling, action-based state modification, and a complete animation system.

## Glossary

- **Scene**: A distinct game state (lobby, shop, combat) that implements the Scene interface with lifecycle methods
- **SceneManager**: The system that manages scene lifecycle, transitions, and delegates game loop calls to the active scene
- **CoreGameState**: SAVEABLE state that persists across scenes and can be saved/loaded (contains game domain state only)
- **UIState**: THROWAWAY state that is reset when scenes change (contains UI selections, hovers, camera position)
- **InputState**: Intent-based input abstraction that translates raw pygame events into game intents
- **Action**: Command pattern implementation for all game state modifications (enables undo/redo/replay)
- **AnimationSystem**: System that manages all animations and provides visual feedback for game state changes
- **HexSystem**: Centralized hex coordinate math utilities for all hex-to-pixel and pixel-to-hex conversions
- **Intent**: High-level input action (confirm, cancel, rotate) derived from raw events (mouse clicks, key presses)
- **Delta Time (dt)**: Time elapsed since last frame in milliseconds, used for frame-independent movement
- **Cube Coordinates**: Hex coordinate system using (q, r, s) where q + r + s = 0

## Requirements

### Requirement 1: Scene Management

**User Story:** As a game developer, I want a centralized scene manager that controls scene lifecycle, so that I can eliminate nested game loops and ensure consistent frame timing.

#### Acceptance Criteria

1. THE SceneManager SHALL maintain exactly one active scene at any point in time
2. WHEN the game starts, THE SceneManager SHALL initialize with a specified initial scene
3. WHEN a scene requests a transition, THE SceneManager SHALL execute the transition before updating the old scene
4. WHEN executing a scene transition, THE SceneManager SHALL call the old scene's on_exit method before creating the new scene
5. WHEN executing a scene transition, THE SceneManager SHALL call the new scene's on_enter method after creating the new scene
6. THE SceneManager SHALL delegate handle_input, update, and draw calls to the active scene
7. WHEN a transition is requested during a frame, THE SceneManager SHALL prevent the old scene from updating in that frame

### Requirement 2: Scene Lifecycle

**User Story:** As a game developer, I want scenes to have well-defined lifecycle methods, so that I can properly initialize and cleanup scene-specific resources.

#### Acceptance Criteria

1. THE Scene base class SHALL define abstract methods for handle_input, update, and draw
2. WHEN a scene becomes active, THE Scene SHALL execute its on_enter method
3. WHEN a scene is deactivated, THE Scene SHALL execute its on_exit method
4. WHEN on_enter is called, THE Scene SHALL create a fresh UIState instance
5. WHEN on_exit is called, THE Scene SHALL discard its UIState instance
6. THE Scene SHALL maintain a reference to CoreGameState throughout its lifecycle
7. THE Scene SHALL maintain a reference to its SceneManager for requesting transitions

### Requirement 3: State Separation

**User Story:** As a game developer, I want clear separation between saveable and throwaway state, so that I can implement save/load functionality without bugs.

#### Acceptance Criteria

1. THE CoreGameState SHALL contain only domain state that can be saved and loaded
2. THE CoreGameState SHALL contain the Game instance, view_player_index, and fast_mode settings
3. THE CoreGameState SHALL provide to_dict and from_dict methods for serialization
4. THE UIState SHALL contain only UI-specific state that does not need to persist
5. THE UIState SHALL contain selections, hovers, camera position, and temporary state
6. WHEN a scene transition occurs, THE CoreGameState SHALL be preserved and passed to the new scene
7. WHEN a scene transition occurs, THE UIState SHALL be discarded and a fresh instance created

### Requirement 4: Intent-Based Input

**User Story:** As a game developer, I want input translated into intents rather than raw events, so that I can support AI, replay, and network functionality.

#### Acceptance Criteria

1. THE InputState SHALL translate raw pygame events into game intents
2. THE InputState SHALL provide intent flags for confirm, cancel, rotate_cw, and rotate_ccw actions
3. THE InputState SHALL capture mouse position, mouse button states, and keyboard states
4. THE InputState SHALL distinguish between keys held down and keys pressed this frame
5. WHEN multiple input sources trigger the same intent, THE InputState SHALL set the intent flag once
6. THE InputState SHALL be created once per frame from pygame events
7. THE InputState SHALL be passed to the active scene's handle_input method

### Requirement 5: Action-Based State Modification

**User Story:** As a game developer, I want all game state modifications to go through actions, so that I can implement undo/redo, replay, and network synchronization.

#### Acceptance Criteria

1. THE Action base class SHALL define execute and undo methods
2. WHEN an action executes successfully, THE Action SHALL modify CoreGameState and return True
3. WHEN an action fails, THE Action SHALL leave CoreGameState unchanged and return False
4. WHEN an action executes successfully, THE Action SHALL spawn appropriate animations
5. THE ActionSystem SHALL maintain a history of executed actions for undo support
6. WHEN an action is undone, THE ActionSystem SHALL restore the previous CoreGameState
7. THE Action SHALL be the only mechanism for modifying CoreGameState

### Requirement 6: Animation System

**User Story:** As a game developer, I want a complete animation system for visual feedback, so that players can see game state changes clearly.

#### Acceptance Criteria

1. THE AnimationSystem SHALL manage all active animations
2. WHEN an animation is added, THE AnimationSystem SHALL update it with delta time each frame
3. WHEN an animation completes, THE AnimationSystem SHALL remove it from the active list
4. THE Animation base class SHALL track elapsed time and finished status
5. WHEN an action executes successfully, THE Action SHALL spawn at least one animation
6. THE AnimationSystem SHALL provide an is_animating query method
7. THE AnimationSystem SHALL render all active animations to the screen

### Requirement 7: Hex Coordinate System

**User Story:** As a game developer, I want centralized hex coordinate math, so that I can eliminate coordinate conversion bugs.

#### Acceptance Criteria

1. THE HexSystem SHALL provide pixel_to_hex conversion using cube rounding
2. THE HexSystem SHALL provide hex_to_pixel conversion for rendering
3. WHEN converting coordinates, THE HexSystem SHALL ensure cube constraint q + r + s = 0 is satisfied
4. THE HexSystem SHALL implement the cube rounding algorithm for accurate pixel-to-hex conversion
5. THE HexSystem SHALL provide neighbor calculation for hex coordinates
6. THE HexSystem SHALL provide distance calculation between hex coordinates
7. THE HexSystem SHALL be initialized with hex_size and origin parameters

### Requirement 8: Frame-Independent Movement

**User Story:** As a game developer, I want animations and movement to be frame-independent, so that the game runs consistently at variable frame rates.

#### Acceptance Criteria

1. THE game loop SHALL capture delta time in milliseconds each frame
2. THE game loop SHALL pass delta time to scene update methods
3. WHEN updating animations, THE AnimationSystem SHALL advance animations by delta time
4. WHEN updating movement, THE Scene SHALL scale movement by delta time
5. THE delta time SHALL always be positive and non-zero
6. WHEN the same total time elapses, animations SHALL reach the same position regardless of frame rate
7. THE game loop SHALL target 60 FPS but support variable frame rates

### Requirement 9: Single Game Loop

**User Story:** As a game developer, I want a single centralized game loop, so that I can eliminate animation desync and input lag.

#### Acceptance Criteria

1. THE main game loop SHALL be located in main.py only
2. THE game loop SHALL capture input events once per frame
3. THE game loop SHALL create InputState from captured events
4. THE game loop SHALL update AnimationSystem before SceneManager
5. THE game loop SHALL update SceneManager with delta time and InputState
6. THE game loop SHALL render scene and animations to screen
7. THE game loop SHALL use clock.tick to maintain target frame rate

### Requirement 10: Scene Transition Correctness

**User Story:** As a game developer, I want scene transitions to be correct and bug-free, so that players don't experience double-updates or state corruption.

#### Acceptance Criteria

1. WHEN a scene requests a transition, THE SceneManager SHALL set a transition flag
2. WHEN checking for transitions, THE SceneManager SHALL check before calling scene.update
3. WHEN a transition is pending, THE SceneManager SHALL execute the transition and skip scene.update
4. WHEN no transition is pending, THE SceneManager SHALL call scene.update normally
5. WHEN transitioning, THE SceneManager SHALL preserve CoreGameState across the transition
6. WHEN transitioning, THE SceneManager SHALL reset UIState to a fresh instance
7. WHEN transitioning, THE SceneManager SHALL set the new scene's scene_manager reference

### Requirement 11: Concrete Scene Implementations

**User Story:** As a game developer, I want concrete scene implementations for lobby, shop, and combat, so that I can replace the old screen classes.

#### Acceptance Criteria

1. THE LobbyScene SHALL allow strategy selection and transition to shop
2. THE ShopScene SHALL allow card purchasing and transition to combat
3. THE CombatScene SHALL visualize battles and transition back to shop
4. WHEN implementing scenes, THE Scene SHALL use Actions for all CoreGameState modifications
5. WHEN implementing scenes, THE Scene SHALL store UI-specific state in UIState only
6. WHEN implementing scenes, THE Scene SHALL use InputState intents rather than raw events
7. WHEN implementing scenes, THE Scene SHALL use HexSystem for all coordinate conversions

### Requirement 12: Undo/Redo Support

**User Story:** As a game developer, I want undo/redo functionality, so that players can experiment with card placements.

#### Acceptance Criteria

1. THE ActionSystem SHALL maintain a history stack of executed actions
2. WHEN an action executes successfully, THE ActionSystem SHALL add it to the history stack
3. WHEN undo is requested, THE ActionSystem SHALL pop the last action and call its undo method
4. WHEN undo is called, THE ActionSystem SHALL move the action to a redo stack
5. WHEN redo is requested, THE ActionSystem SHALL pop from redo stack and re-execute the action
6. WHEN a new action executes, THE ActionSystem SHALL clear the redo stack
7. THE Action SHALL save sufficient state in execute to support undo

### Requirement 13: Input Testability

**User Story:** As a game developer, I want input to be testable and replayable, so that I can write automated tests and support AI players.

#### Acceptance Criteria

1. THE InputState SHALL be constructible from a list of pygame events
2. THE InputState SHALL provide a query API for input state without side effects
3. WHEN testing, THE Scene SHALL accept InputState instances created from synthetic events
4. THE InputState SHALL be immutable after construction
5. THE InputState SHALL translate events to intents deterministically
6. WHEN the same events are provided, THE InputState SHALL produce the same intents
7. THE InputState SHALL support serialization for replay functionality

### Requirement 14: Resource Management

**User Story:** As a game developer, I want proper resource management in scenes, so that I can prevent memory leaks.

#### Acceptance Criteria

1. WHEN on_enter is called, THE Scene SHALL load scene-specific resources
2. WHEN on_exit is called, THE Scene SHALL release scene-specific resources
3. THE Scene SHALL not maintain references to resources after on_exit
4. THE UIState SHALL be explicitly set to None in on_exit
5. WHEN a scene is deactivated, THE SceneManager SHALL ensure on_exit is called
6. THE Scene SHALL not create resource leaks through circular references
7. THE Scene SHALL properly cleanup pygame surfaces and fonts

### Requirement 15: Error Handling

**User Story:** As a game developer, I want robust error handling, so that invalid operations don't crash the game.

#### Acceptance Criteria

1. WHEN an invalid scene name is requested, THE SceneManager SHALL log an error and remain in current scene
2. WHEN a scene is created without CoreGameState, THE Scene SHALL raise ValueError
3. WHEN delta time is negative or zero, THE game loop SHALL clamp it to a minimum positive value
4. WHEN pixel-to-hex conversion produces invalid coordinates, THE HexSystem SHALL return None
5. WHEN an action fails validation, THE Action SHALL return False without modifying state
6. WHEN an animation encounters an error, THE AnimationSystem SHALL remove it and continue
7. THE game loop SHALL catch and log exceptions without crashing

