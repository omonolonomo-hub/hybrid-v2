# Requirements Document: Passive Handlers Extraction

## Introduction

This document specifies the requirements for extracting the PASSIVE_HANDLERS dictionary and related passive handler functions from `autochess_sim_v06.py` into a dedicated module `passive_registry.py`. The goal is to improve code organization and maintainability while preserving all existing functionality and maintaining backward compatibility.

## Glossary

- **PASSIVE_HANDLERS**: A dictionary mapping card names (strings) to handler functions that implement passive abilities
- **Passive_Handler**: A callable function with signature `(Card, str, Player, Player, dict) -> int` that implements a card's passive ability
- **trigger_passive**: The main dispatch function that invokes passive handlers based on card name and trigger type
- **Passive_Registry_Module**: The new module `engine_core/passive_registry.py` that will contain extracted passive handlers
- **Main_Simulation_Module**: The existing `engine_core/autochess_sim_v06.py` file
- **Trigger_Type**: A string identifier for when a passive ability fires (e.g., "combat_win", "income", "pre_combat")

## Requirements

### Requirement 1: Extract Passive Handler Functions

**User Story:** As a developer, I want all passive handler functions moved to a dedicated module, so that the codebase is better organized and easier to maintain.

#### Acceptance Criteria

1. THE Passive_Registry_Module SHALL contain all 40+ passive handler functions currently defined in Main_Simulation_Module
2. WHEN a passive handler function is extracted, THE Passive_Registry_Module SHALL preserve the exact function signature and implementation
3. THE Passive_Registry_Module SHALL include all handler functions matching the pattern `_passive_*`
4. THE Passive_Registry_Module SHALL maintain the original function names without modification

### Requirement 2: Extract PASSIVE_HANDLERS Dictionary

**User Story:** As a developer, I want the PASSIVE_HANDLERS dictionary moved to the passive registry module, so that handler registration is colocated with handler definitions.

#### Acceptance Criteria

1. THE Passive_Registry_Module SHALL contain the PASSIVE_HANDLERS dictionary definition
2. THE PASSIVE_HANDLERS dictionary SHALL be initialized as an empty dictionary at module level
3. WHEN the module is imported, THE PASSIVE_HANDLERS dictionary SHALL be populated with all handler registrations
4. THE PASSIVE_HANDLERS dictionary SHALL maintain all 40+ card name to handler function mappings
5. THE PASSIVE_HANDLERS dictionary SHALL include both original card names and ASCII-safe fallback names (e.g., "Ragnarök" and "Ragnark")

### Requirement 3: Preserve Helper Function Dependencies

**User Story:** As a developer, I want helper functions used by passive handlers to remain accessible, so that passive handlers continue to work correctly.

#### Acceptance Criteria

1. THE Main_Simulation_Module SHALL retain the `_find_coord` function (used by 15+ passive handlers)
2. THE Main_Simulation_Module SHALL retain the `_neighbor_cards` function (used by 10+ passive handlers)
3. WHEN passive handlers need helper functions, THE Passive_Registry_Module SHALL import them from board module or Main_Simulation_Module
4. THE Passive_Registry_Module SHALL NOT duplicate helper function implementations

### Requirement 4: Maintain Import Structure

**User Story:** As a developer, I want the import structure to avoid circular dependencies, so that the modules can be imported without errors.

#### Acceptance Criteria

1. THE Passive_Registry_Module SHALL import Card class from card module
2. THE Passive_Registry_Module SHALL import Board helper functions from board module
3. THE Passive_Registry_Module SHALL use TYPE_CHECKING for Player type hints to avoid circular imports
4. WHEN Main_Simulation_Module imports from Passive_Registry_Module, THE import SHALL NOT create circular dependency
5. THE Passive_Registry_Module SHALL support both relative and absolute imports (try/except pattern)

### Requirement 5: Preserve Backward Compatibility

**User Story:** As a developer, I want existing code to continue working without modification, so that the refactoring is safe and non-breaking.

#### Acceptance Criteria

1. THE Main_Simulation_Module SHALL re-export PASSIVE_HANDLERS from Passive_Registry_Module
2. WHEN code imports PASSIVE_HANDLERS from Main_Simulation_Module, THE import SHALL succeed without modification
3. THE trigger_passive function SHALL remain in Main_Simulation_Module
4. THE trigger_passive function SHALL use PASSIVE_HANDLERS from Passive_Registry_Module
5. WHEN trigger_passive is called, THE function SHALL behave identically to the original implementation

### Requirement 6: Maintain Type Safety

**User Story:** As a developer, I want type hints preserved during extraction, so that type checking continues to work correctly.

#### Acceptance Criteria

1. THE Passive_Registry_Module SHALL define the PassiveHandler type alias
2. THE PassiveHandler type alias SHALL specify the signature `Callable[[Card, str, Player, Player, dict], int]`
3. THE PASSIVE_HANDLERS dictionary SHALL be typed as `Dict[str, PassiveHandler]`
4. WHEN using TYPE_CHECKING, THE Passive_Registry_Module SHALL import Player type for type hints only

### Requirement 7: Preserve All Handler Logic

**User Story:** As a developer, I want all passive handler logic preserved exactly, so that game behavior remains unchanged.

#### Acceptance Criteria

1. THE Passive_Registry_Module SHALL preserve all combat handlers (Ragnarök, World War II, Loki, Cubism, etc.)
2. THE Passive_Registry_Module SHALL preserve all economy handlers (Industrial Revolution, Midas, Silk Road, etc.)
3. THE Passive_Registry_Module SHALL preserve all copy handlers (Coelacanth, Marie Curie, Space-Time, Fungus)
4. THE Passive_Registry_Module SHALL preserve all survival handlers (Valhalla, Phoenix, Axolotl, etc.)
5. THE Passive_Registry_Module SHALL preserve all synergy field handlers (Odin, Olympus, Medusa, etc.)
6. THE Passive_Registry_Module SHALL preserve all combo handlers (Athena, Ballet, Impressionism, etc.)
7. WHEN a passive handler modifies card stats, THE modification SHALL produce identical results to the original implementation

### Requirement 8: Maintain Test Compatibility

**User Story:** As a developer, I want existing tests to continue passing, so that I can verify the refactoring is correct.

#### Acceptance Criteria

1. WHEN tests import trigger_passive from Main_Simulation_Module, THE import SHALL succeed
2. WHEN tests call trigger_passive, THE function SHALL produce identical results to the original implementation
3. THE test file `tests/unit/test_trigger_passive.py` SHALL pass without modification
4. WHEN tests verify passive handler behavior, THE behavior SHALL match the original implementation

### Requirement 9: Document Module Structure

**User Story:** As a developer, I want clear documentation of the module structure, so that I understand the organization and dependencies.

#### Acceptance Criteria

1. THE Passive_Registry_Module SHALL include a module docstring explaining its purpose
2. THE module docstring SHALL document the handler function signature
3. THE module docstring SHALL list the main exports (PASSIVE_HANDLERS, PassiveHandler type)
4. THE module docstring SHALL note dependencies on Card, Board, and Player types

### Requirement 10: Minimize Code Duplication

**User Story:** As a developer, I want to avoid code duplication, so that maintenance is simplified.

#### Acceptance Criteria

1. THE Passive_Registry_Module SHALL NOT duplicate helper functions from board module
2. THE Passive_Registry_Module SHALL NOT duplicate type definitions from other modules
3. WHEN multiple handlers share logic, THE shared logic SHALL remain in a single location
4. THE Main_Simulation_Module SHALL NOT retain copies of extracted handler functions
