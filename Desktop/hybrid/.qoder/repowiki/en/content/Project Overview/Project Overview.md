# Project Overview

<cite>
**Referenced Files in This Document**
- [README.md](file://README.md)
- [AUTOCHESS_HYBRID_FINAL_GDD.md](file://AUTOCHESS_HYBRID_FINAL_GDD.md)
- [engine_core/autochess_sim_v06.py](file://engine_core/autochess_sim_v06.py)
- [engine_core/game.py](file://engine_core/game.py)
- [engine_core/game_factory.py](file://engine_core/game_factory.py)
- [v2/main.py](file://v2/main.py)
- [v2/core/scene_manager.py](file://v2/core/scene_manager.py)
- [v2/core/game_state.py](file://v2/core/game_state.py)
- [archive_legacy/MIGRATION.md](file://archive_legacy/MIGRATION.md)
- [_archive/old_dirs/scenes/lobby_scene.py](file://_archive/old_dirs/scenes/lobby_scene.py)
- [_archive/old_dirs/scenes/shop_scene.py](file://_archive/old_dirs/scenes/shop_scene.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Dependency Analysis](#dependency-analysis)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Conclusion](#conclusion)

## Introduction
Autochess Hybrid is a hex-grid based autochess simulation engine designed to run 8-player strategic combat simulations. It models a competitive autochess environment where each of eight players selects from a 101-card pool, places units on a 37-hex board using a hex-grid, and engages in turn-based combat governed by group synergies, combos, and a rich passive ability system. The project’s mission is to provide a robust, AI-driven framework for strategy game simulation, enabling reproducible matches, KPI tracking, and extensive experimentation with AI strategies.

The project occupies a significant role in the gaming AI research ecosystem by offering:
- A deterministic, rule-specified autochess engine suitable for AI training and evaluation
- A modular, scene-based architecture that cleanly separates UI, game orchestration, and simulation logic
- A comprehensive GDD defining turn structure, board mechanics, economy, combat resolution, and passive taxonomy
- Extensive documentation, testing, and simulation tooling for reproducibility and performance analysis

## Project Structure
The repository organizes functionality into distinct layers:
- Engine core: simulation logic, game orchestration, board mechanics, combat engine, AI strategies, and economy
- Scene-based UI: modular scenes for lobby, shop, combat, and game over, orchestrated by a scene manager
- Assets and data: card definitions, passive descriptions, and UI resources
- Scripts and tools: simulation runners, batch analyzers, and QA/validation utilities
- Documentation: GDD, migration reports, and design specs

```mermaid
graph TB
subgraph "Engine Core"
EC_Game["engine_core/game.py"]
EC_Factory["engine_core/game_factory.py"]
EC_Sim["engine_core/autochess_sim_v06.py"]
end
subgraph "Scene-Based UI"
V2_Main["v2/main.py"]
V2_SM["v2/core/scene_manager.py"]
V2_GS["v2/core/game_state.py"]
Old_Lobby["_archive/old_dirs/scenes/lobby_scene.py"]
Old_Shop["_archive/old_dirs/scenes/shop_scene.py"]
end
subgraph "Assets & Docs"
Docs["AUTOCHESS_HYBRID_FINAL_GDD.md"]
Readme["README.md"]
Migration["archive_legacy/MIGRATION.md"]
end
V2_Main --> V2_SM
V2_Main --> V2_GS
V2_Main --> EC_Factory
EC_Factory --> EC_Game
EC_Sim --> EC_Game
V2_SM --> Old_Lobby
V2_SM --> Old_Shop
Readme --> Migration
Readme --> Docs
```

**Diagram sources**
- [v2/main.py:37-74](file://v2/main.py#L37-L74)
- [v2/core/scene_manager.py:28-156](file://v2/core/scene_manager.py#L28-L156)
- [v2/core/game_state.py:14-173](file://v2/core/game_state.py#L14-L173)
- [_archive/old_dirs/scenes/lobby_scene.py:66-462](file://_archive/old_dirs/scenes/lobby_scene.py#L66-L462)
- [_archive/old_dirs/scenes/shop_scene.py:287-1054](file://_archive/old_dirs/scenes/shop_scene.py#L287-L1054)
- [engine_core/game_factory.py:30-70](file://engine_core/game_factory.py#L30-L70)
- [engine_core/game.py:35-224](file://engine_core/game.py#L35-L224)
- [engine_core/autochess_sim_v06.py:78-107](file://engine_core/autochess_sim_v06.py#L78-L107)
- [README.md:143-189](file://README.md#L143-L189)
- [AUTOCHESS_HYBRID_FINAL_GDD.md:1-50](file://AUTOCHESS_HYBRID_FINAL_GDD.md#L1-L50)
- [archive_legacy/MIGRATION.md:18-96](file://archive_legacy/MIGRATION.md#L18-L96)

**Section sources**
- [README.md:7-58](file://README.md#L7-L58)
- [README.md:143-189](file://README.md#L143-L189)
- [AUTOCHESS_HYBRID_FINAL_GDD.md:1-50](file://AUTOCHESS_HYBRID_FINAL_GDD.md#L1-L50)
- [archive_legacy/MIGRATION.md:18-96](file://archive_legacy/MIGRATION.md#L18-L96)

## Core Components
- Simulation engine: orchestrates 8-player matches, turn phases, market windows, preparation and combat phases, and win condition checks
- Scene manager: manages modular scenes (lobby, shop, combat, game over) with smooth transitions and input routing
- Game factory: constructs Game instances with configured strategies and dependencies
- UI bridge: GameState exposes mutation APIs for UI interactions and caches public state for rendering

Key capabilities:
- Hex-grid board with axial coordinates and 37-hex capacity
- Turn structure with preparation and combat phases
- Market system with rarity-weighted windows and refresh mechanics
- Synergy and combo scoring, passive triggers, and combat resolution pipeline
- AI strategies and KPI aggregation for simulation runs

**Section sources**
- [engine_core/game.py:35-224](file://engine_core/game.py#L35-L224)
- [engine_core/game_factory.py:30-70](file://engine_core/game_factory.py#L30-L70)
- [v2/core/scene_manager.py:28-156](file://v2/core/scene_manager.py#L28-L156)
- [v2/core/game_state.py:14-173](file://v2/core/game_state.py#L14-L173)
- [engine_core/autochess_sim_v06.py:78-107](file://engine_core/autochess_sim_v06.py#L78-L107)

## Architecture Overview
Autochess Hybrid evolved from a monolithic legacy system to a modern scene-based architecture. The legacy run_game.py (over 730 lines) is being decomposed into specialized scenes while preserving all game logic. The new architecture centers around:
- SceneManager coordinating scene lifecycles and transitions
- CoreGameState holding persistent state across scenes
- UI adapters bridging GameState to rendering and user input
- EngineAdapter exposing mutation methods to the UI layer

```mermaid
sequenceDiagram
participant User as "User"
participant SM as "SceneManager"
participant GS as "GameState"
participant GA as "EngineAdapter"
participant Game as "Game"
User->>SM : "Start match"
SM->>GS : "Initialize CoreGameState"
SM->>GA : "Hook engine"
SM->>Game : "build_game(strategies)"
SM->>SM : "Transition to LobbyScene"
User->>SM : "Confirm strategies"
SM->>SM : "Transition to GameLoopScene"
SM->>SM : "Transition to ShopScene"
User->>GS : "Mutations (buy/place/commit)"
GS->>GA : "perform_buy_card/place_card/commit_turn"
GA->>Game : "Apply state changes"
SM->>SM : "Transition to CombatScene"
SM->>SM : "Transition to GameLoopScene"
SM->>SM : "Transition to GameOverScene"
```

**Diagram sources**
- [v2/main.py:37-74](file://v2/main.py#L37-L74)
- [v2/core/scene_manager.py:28-156](file://v2/core/scene_manager.py#L28-L156)
- [v2/core/game_state.py:37-173](file://v2/core/game_state.py#L37-L173)
- [engine_core/game_factory.py:30-70](file://engine_core/game_factory.py#L30-L70)
- [engine_core/game.py:35-224](file://engine_core/game.py#L35-L224)
- [archive_legacy/MIGRATION.md:22-37](file://archive_legacy/MIGRATION.md#L22-L37)

**Section sources**
- [archive_legacy/MIGRATION.md:18-96](file://archive_legacy/MIGRATION.md#L18-L96)
- [v2/main.py:14-74](file://v2/main.py#L14-L74)
- [v2/core/scene_manager.py:28-156](file://v2/core/scene_manager.py#L28-L156)
- [v2/core/game_state.py:14-173](file://v2/core/game_state.py#L14-L173)

## Detailed Component Analysis

### Simulation Workflow: From Lobby Selection to Combat Resolution
This workflow demonstrates the end-to-end flow from strategy selection through combat resolution, highlighting the scene-based architecture and engine orchestration.

```mermaid
flowchart TD
Start(["Start"]) --> Lobby["LobbyScene<br/>Select strategies for 8 players"]
Lobby --> GameLoop["GameLoopScene<br/>Turn orchestration, fast mode, player switching"]
GameLoop --> Shop["ShopScene<br/>Purchase cards, refresh market, hand management"]
Shop --> Combat["CombatScene<br/>Hex board placement, rotation, locked coordinates"]
Combat --> GameLoop2["GameLoopScene<br/>Combat results, pairings, next turn"]
GameLoop2 --> GameOver["GameOverScene<br/>Announce winner, restart option"]
GameOver --> Lobby
```

Practical example steps:
- Strategy selection: Players choose AI strategies in the lobby; transitions pass strategies to the game loop
- Turn orchestration: GameLoopScene advances turns, handles fast mode, and displays combat results
- Shop phase: Players buy cards from weighted windows; hand overflow is managed; market refresh costs gold
- Combat placement: Players select cards from hand, rotate hexes, and place on the 37-hex board with placement limits and locked coordinates
- Combat resolution: Pairwise combat resolves per-edge strengths, applying group advantages, combos, synergy bonuses, and passive triggers; damage computed and HP updated
- Game over: Winner determined by HP; restart returns to lobby

**Diagram sources**
- [archive_legacy/MIGRATION.md:31-89](file://archive_legacy/MIGRATION.md#L31-L89)
- [AUTOCHESS_HYBRID_FINAL_GDD.md:104-190](file://AUTOCHESS_HYBRID_FINAL_GDD.md#L104-L190)
- [v2/core/scene_manager.py:28-156](file://v2/core/scene_manager.py#L28-L156)

**Section sources**
- [archive_legacy/MIGRATION.md:31-89](file://archive_legacy/MIGRATION.md#L31-L89)
- [AUTOCHESS_HYBRID_FINAL_GDD.md:104-190](file://AUTOCHESS_HYBRID_FINAL_GDD.md#L104-L190)
- [_archive/old_dirs/scenes/lobby_scene.py:140-156](file://_archive/old_dirs/scenes/lobby_scene.py#L140-L156)
- [_archive/old_dirs/scenes/shop_scene.py:444-532](file://_archive/old_dirs/scenes/shop_scene.py#L444-L532)

### Engine Orchestration and Turn Management
The Game class centralizes turn orchestration, delegating preparation and combat phases to TurnManager and CombatEngine respectively. It coordinates Swiss pairing, passive triggers, and post-combat cleanup.

```mermaid
classDiagram
class Game {
+players : List[Player]
+turn : int
+log : List[str]
+alive_players() List[Player]
+start_turn() void
+finish_turn() void
+preparation_phase() void
+combat_phase(pairs) void
+run() Player
}
class TurnManager {
+turn : int
+start_turn() void
+finish_turn() void
+preparation_phase() void
+swiss_pairs() List[Tuple[Player, Player]]
}
class CombatEngine {
+turn : int
+run_combat(pairs) List[dict]
}
Game --> TurnManager : "delegates"
Game --> CombatEngine : "delegates"
```

**Diagram sources**
- [engine_core/game.py:35-224](file://engine_core/game.py#L35-L224)

**Section sources**
- [engine_core/game.py:35-224](file://engine_core/game.py#L35-L224)

### Scene-Based Architecture and State Management
The scene-based architecture cleanly separates persistent state (CoreGameState) from transient UI state (UIState). Scenes communicate via SceneManager and receive data through transition kwargs.

```mermaid
classDiagram
class Scene {
+on_enter() void
+on_exit() void
+handle_event(event) void
+update(dt_ms) void
+draw(surface) void
}
class SceneManager {
+set_scene(scene) void
+transition_to(scene, fade_ms) void
+handle_event(event) void
+update(dt_ms) void
+draw(surface) void
+is_transitioning bool
+current_scene_name str
}
class GameState {
+hook_engine(engine) void
+get_public_state() PublicState
+buy_card(player_index, slot_index) ActionResult
+place_card(hand_index, coord, rotation, player_index) ActionResult
+commit_human_turn() void
+start_turn() void
+run_combat_phase() void
}
SceneManager --> Scene : "controls lifecycle"
GameState --> Game : "bridges UI to engine"
```

**Diagram sources**
- [v2/core/scene_manager.py:4-156](file://v2/core/scene_manager.py#L4-L156)
- [v2/core/game_state.py:14-173](file://v2/core/game_state.py#L14-L173)

**Section sources**
- [v2/core/scene_manager.py:28-156](file://v2/core/scene_manager.py#L28-L156)
- [v2/core/game_state.py:14-173](file://v2/core/game_state.py#L14-L173)
- [archive_legacy/MIGRATION.md:96-156](file://archive_legacy/MIGRATION.md#L96-L156)

### Hex-Grid and Board Mechanics
The hex-grid system uses axial coordinates with a radius of three, yielding a 37-hex board. Cards are placed with rotation affecting which stat faces which direction, and edge loss occurs when stats reach zero.

```mermaid
flowchart TD
A["Place card on hex"] --> B["Rotate card (0-5 steps)"]
B --> C["Compare opposing edges<br/>apply group advantage"]
C --> D{"Edge values equal?"}
D --> |Yes| E["No combat points"]
D --> |No| F["Award combat points to higher edge"]
F --> G["Apply passive triggers"]
G --> H["Edge loss or elimination"]
```

**Diagram sources**
- [AUTOCHESS_HYBRID_FINAL_GDD.md:195-275](file://AUTOCHESS_HYBRID_FINAL_GDD.md#L195-L275)

**Section sources**
- [AUTOCHESS_HYBRID_FINAL_GDD.md:195-275](file://AUTOCHESS_HYBRID_FINAL_GDD.md#L195-L275)

### AI Strategy Integration and Simulation
The engine supports multiple AI strategies and can run large-scale simulations with configurable parameters. The simulation runner validates card pools, initializes strategies, and aggregates results.

```mermaid
sequenceDiagram
participant CLI as "CLI"
participant Sim as "autochess_sim_v06.py"
participant Factory as "game_factory.build_game"
participant Game as "Game"
participant Results as "Results"
CLI->>Sim : "Run simulation (games, players, strategies)"
Sim->>Factory : "build_game(strategies)"
Factory-->>Sim : "Game instance"
Sim->>Game : "run_simulation(n_games, n_players)"
Game-->>Sim : "results"
Sim-->>CLI : "print_results(results)"
```

**Diagram sources**
- [engine_core/autochess_sim_v06.py:78-107](file://engine_core/autochess_sim_v06.py#L78-L107)
- [engine_core/game_factory.py:30-70](file://engine_core/game_factory.py#L30-L70)
- [engine_core/game.py:203-224](file://engine_core/game.py#L203-L224)

**Section sources**
- [engine_core/autochess_sim_v06.py:78-107](file://engine_core/autochess_sim_v06.py#L78-L107)
- [engine_core/game_factory.py:30-70](file://engine_core/game_factory.py#L30-L70)
- [engine_core/game.py:203-224](file://engine_core/game.py#L203-L224)

## Dependency Analysis
The project exhibits clean separation of concerns:
- v2/main.py depends on engine_core/game_factory to construct Game instances and on v2/core/scene_manager to orchestrate scenes
- v2/core/game_state.py bridges UI mutations to engine operations via EngineAdapter
- engine_core/game.py delegates turn and combat logic to TurnManager and CombatEngine
- Legacy scenes (lobby_scene.py, shop_scene.py) demonstrate the prior monolithic approach and inform the migration

```mermaid
graph LR
V2Main["v2/main.py"] --> V2SM["v2/core/scene_manager.py"]
V2Main --> V2GS["v2/core/game_state.py"]
V2Main --> ECFactory["engine_core/game_factory.py"]
ECFactory --> ECGame["engine_core/game.py"]
LegacyLobby["_archive/old_dirs/scenes/lobby_scene.py"] -. migration reference .-> V2SM
LegacyShop["_archive/old_dirs/scenes/shop_scene.py"] -. migration reference .-> V2SM
```

**Diagram sources**
- [v2/main.py:14-74](file://v2/main.py#L14-L74)
- [v2/core/scene_manager.py:28-156](file://v2/core/scene_manager.py#L28-L156)
- [v2/core/game_state.py:14-173](file://v2/core/game_state.py#L14-L173)
- [engine_core/game_factory.py:30-70](file://engine_core/game_factory.py#L30-L70)
- [engine_core/game.py:35-224](file://engine_core/game.py#L35-L224)
- [_archive/old_dirs/scenes/lobby_scene.py:66-462](file://_archive/old_dirs/scenes/lobby_scene.py#L66-L462)
- [_archive/old_dirs/scenes/shop_scene.py:287-1054](file://_archive/old_dirs/scenes/shop_scene.py#L287-L1054)

**Section sources**
- [v2/main.py:14-74](file://v2/main.py#L14-L74)
- [engine_core/game_factory.py:30-70](file://engine_core/game_factory.py#L30-L70)
- [engine_core/game.py:35-224](file://engine_core/game.py#L35-L224)
- [archive_legacy/MIGRATION.md:18-96](file://archive_legacy/MIGRATION.md#L18-L96)

## Performance Considerations
- Scene-based architecture improves maintainability and testability, enabling incremental development and UI responsiveness
- GameState caching avoids expensive recomputation of public state; cache invalidation occurs on mutations
- Simulation runner supports batch processing and verbosity controls for performance profiling
- Hex-grid operations and passive triggers are optimized through efficient data structures and minimal allocations

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common issues and remedies:
- Scene transitions: Ensure transitions occur at safe points; avoid input during fade transitions
- State duplication: Persist only saveable state in CoreGameState; throwaway state belongs in UIState
- Legacy compatibility: Use the feature flag to switch between legacy and scene-based architectures during migration
- Card pool validation: Run card pool verification before simulations to catch stat/cost violations
- UI responsiveness: Use GameState mutation APIs to trigger cache invalidation and redraw updates

**Section sources**
- [archive_legacy/MIGRATION.md:116-156](file://archive_legacy/MIGRATION.md#L116-L156)
- [engine_core/autochess_sim_v06.py:53-71](file://engine_core/autochess_sim_v06.py#L53-L71)
- [v2/core/game_state.py:55-65](file://v2/core/game_state.py#L55-L65)

## Conclusion
Autochess Hybrid delivers a mature, scene-based autochess simulation engine capable of 8-player strategic combat with rich mechanics spanning hex-grid placement, synergy and combo scoring, passive abilities, and turn-based economy. Its evolution from a monolithic legacy system to a modular architecture positions it as a strong foundation for AI strategy research, enabling reproducible simulations, detailed KPI tracking, and extensible experimentation. The combination of a comprehensive GDD, robust engine orchestration, and clean UI bridges makes it a valuable resource for both researchers and developers working on strategy game simulation frameworks.