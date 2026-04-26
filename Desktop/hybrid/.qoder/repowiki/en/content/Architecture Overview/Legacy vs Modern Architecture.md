# Legacy vs Modern Architecture

<cite>
**Referenced Files in This Document**
- [engine_core/__init__.py](file://engine_core/__init__.py)
- [engine_core/game_factory.py](file://engine_core/game_factory.py)
- [engine_core/game.py](file://engine_core/game.py)
- [engine_core/board.py](file://engine_core/board.py)
- [engine_core/player.py](file://engine_core/player.py)
- [engine_core/ai.py](file://engine_core/ai.py)
- [v2/mock/engine_mock.py](file://v2/mock/engine_mock.py)
- [v2/core/engine_adapter.py](file://v2/core/engine_adapter.py)
- [v2/core/game_state.py](file://v2/core/game_state.py)
- [v2/core/public_state.py](file://v2/core/public_state.py)
- [v2/core/state_store.py](file://v2/core/state_store.py)
- [v2/core/ui_adapter.py](file://v2/core/ui_adapter.py)
- [v2/main.py](file://v2/main.py)
- [v2/HYBRID_ENGINE_CORE_VS_MOCK_REPORT.md](file://v2/HYBRID_ENGINE_CORE_VS_MOCK_REPORT.md)
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
This document presents a comprehensive architectural comparison between the legacy engine_core/ and the modern v2/ architecture of AutoChess Hybrid. The legacy engine_core/ provides a complete, production-grade game engine with full combat resolution, passive effects, 8 AI strategies, economy and evolution systems, and Swiss pairing. The modern v2/ architecture introduces a bridge layer (GameState) that enables parallel UI development against a lightweight mock engine, while preserving the ability to swap to the production engine with minimal friction. The document explains the factory pattern for game creation, the strategy pattern for AI implementations, and the architectural decisions that maintain backward compatibility while enabling rapid UI iteration.

## Project Structure
The repository separates concerns into three layers:
- engine_core/: Production game engine with complete simulation and AI
- v2/: UI framework and bridge layer for parallel development
- Shared assets and tests supporting both layers

```mermaid
graph TB
subgraph "UI Layer (v2)"
UI_Main["v2/main.py"]
UI_GameState["v2/core/game_state.py"]
UI_Adapter["v2/core/ui_adapter.py"]
UI_Store["v2/core/state_store.py"]
UI_Public["v2/core/public_state.py"]
UI_Mock["v2/mock/engine_mock.py"]
end
subgraph "Bridge Layer"
Bridge_Adapter["v2/core/engine_adapter.py"]
end
subgraph "Production Engine (engine_core)"
Core_Game["engine_core/game.py"]
Core_Factory["engine_core/game_factory.py"]
Core_AI["engine_core/ai.py"]
Core_Board["engine_core/board.py"]
Core_Player["engine_core/player.py"]
end
UI_Main --> UI_GameState
UI_GameState --> UI_Adapter
UI_GameState --> UI_Store
UI_GameState --> UI_Public
UI_GameState --> Bridge_Adapter
Bridge_Adapter --> Core_Game
UI_GameState --> UI_Mock
Core_Factory --> Core_Game
Core_Game --> Core_AI
Core_Game --> Core_Board
Core_Game --> Core_Player
```

**Diagram sources**
- [v2/main.py:14-35](file://v2/main.py#L14-L35)
- [v2/core/game_state.py:37-40](file://v2/core/game_state.py#L37-L40)
- [v2/core/engine_adapter.py:38-46](file://v2/core/engine_adapter.py#L38-L46)
- [engine_core/game_factory.py:30-70](file://engine_core/game_factory.py#L30-L70)
- [engine_core/game.py:35-96](file://engine_core/game.py#L35-L96)

**Section sources**
- [v2/HYBRID_ENGINE_CORE_VS_MOCK_REPORT.md:172-211](file://v2/HYBRID_ENGINE_CORE_VS_MOCK_REPORT.md#L172-L211)
- [v2/main.py:14-35](file://v2/main.py#L14-L35)

## Core Components
- Legacy engine_core/ provides:
  - Game orchestration, turn management, and Swiss pairing
  - Full combat resolution with edge-to-edge combat, group advantage, synergy bonuses, and damage scaling
  - Passive effect system with registry-based dispatch and lifecycle triggers
  - Economy system (income, interest, card costs, rarity-weighted markets)
  - Evolution mechanics and copy strengthening
  - AI strategies with parameterized training and synergy matrices
  - Factory pattern for game creation with configurable strategies

- v2/ bridge layer provides:
  - GameState singleton acting as the UI engine abstraction
  - UIAdapter that constructs immutable PublicState snapshots
  - StateStore caching and reactive updates
  - EngineAdapter wrapping engine_core.Game for UI integration
  - Mock engine for parallel UI development

**Section sources**
- [engine_core/__init__.py:17-46](file://engine_core/__init__.py#L17-L46)
- [engine_core/game_factory.py:30-70](file://engine_core/game_factory.py#L30-L70)
- [engine_core/game.py:35-96](file://engine_core/game.py#L35-L96)
- [v2/core/game_state.py:14-40](file://v2/core/game_state.py#L14-L40)
- [v2/core/engine_adapter.py:38-46](file://v2/core/engine_adapter.py#L38-L46)
- [v2/mock/engine_mock.py:61-84](file://v2/mock/engine_mock.py#L61-L84)

## Architecture Overview
The modern architecture uses a layered approach:
- UI components interact exclusively with GameState
- GameState delegates to either MockGame (for parallel development) or EngineAdapter (for production)
- EngineAdapter wraps engine_core.Game and translates between string-based UI interfaces and engine objects
- UIAdapter builds immutable PublicState snapshots for rendering

```mermaid
sequenceDiagram
participant UI as "UI Components"
participant GS as "GameState"
participant EA as "EngineAdapter"
participant EC as "engine_core.Game"
participant UIA as "UIAdapter"
UI->>GS : buy_card_from_slot(player, slot)
GS->>EA : perform_buy_card(player, slot)
EA->>EC : player.buy_card(card, market, uid, trigger_passive_fn)
EC-->>EA : ActionResult.OK
EA-->>GS : ActionResult.OK
GS-->>UI : ActionResult.OK
UI->>GS : get_public_state()
GS->>UIA : build_public_state(adapter, store, formatter)
UIA->>EA : get_shop_window(player), get_hand(player), get_player(player)
EA-->>UIA : data snapshots
UIA-->>GS : PublicState
GS-->>UI : PublicState
```

**Diagram sources**
- [v2/core/game_state.py:92-102](file://v2/core/game_state.py#L92-L102)
- [v2/core/engine_adapter.py:81-114](file://v2/core/engine_adapter.py#L81-L114)
- [v2/core/ui_adapter.py:97-120](file://v2/core/ui_adapter.py#L97-L120)

**Section sources**
- [v2/HYBRID_ENGINE_CORE_VS_MOCK_REPORT.md:519-602](file://v2/HYBRID_ENGINE_CORE_VS_MOCK_REPORT.md#L519-L602)
- [v2/core/game_state.py:59-65](file://v2/core/game_state.py#L59-L65)

## Detailed Component Analysis

### Legacy Engine Core (engine_core/)
The engine_core/ implements a complete AutoChess simulation:
- Game orchestrates preparation and combat phases, Swiss pairing, and turn lifecycle
- Board manages hex grid, combat resolution, combo detection, and synergy calculations
- Player encapsulates economy, inventory, progression, and board state
- AI module implements 8 strategies with parameterized training and synergy matrices

```mermaid
classDiagram
class Game {
+players : List[Player]
+market : Market
+turn : int
+combat_phase(pairs)
+start_turn()
+finish_turn()
}
class Board {
+grid : Dict
+free_coords()
+place(coord, card)
+remove(coord)
}
class Player {
+pid : int
+strategy : str
+board : Board
+inventory
+economy
+progression
+buy_card(card, market, trigger_passive_fn, uid)
+check_copy_strengthening(turn, trigger_passive_fn)
+check_evolution(market, card_by_name)
}
class AI {
+buy_cards(player, market, max_cards, ...)
+place_cards(player, rng, ...)
}
Game --> Player : "manages"
Player --> Board : "owns"
Game --> AI : "uses"
```

**Diagram sources**
- [engine_core/game.py:35-96](file://engine_core/game.py#L35-L96)
- [engine_core/board.py:54-106](file://engine_core/board.py#L54-L106)
- [engine_core/player.py:22-51](file://engine_core/player.py#L22-L51)
- [engine_core/ai.py:214-380](file://engine_core/ai.py#L214-L380)

**Section sources**
- [engine_core/game.py:35-96](file://engine_core/game.py#L35-L96)
- [engine_core/board.py:54-106](file://engine_core/board.py#L54-L106)
- [engine_core/player.py:22-51](file://engine_core/player.py#L22-L51)
- [engine_core/ai.py:214-380](file://engine_core/ai.py#L214-L380)

### Mock Engine (v2/mock/engine_mock.py)
The mock engine enables parallel UI development:
- Uses string-based card names instead of Card objects
- Provides deterministic shop windows and simplified player state
- Exposes stub implementations for shop operations and turn flow
- Intentionally omits combat, board, and advanced systems

```mermaid
flowchart TD
Start(["MockGame Initialization"]) --> Fixtures["initialize_deterministic_fixture()"]
Fixtures --> Players["Create 8 MockPlayer instances"]
Players --> Shop["Fill shop window with 5 random cards"]
Shop --> UI["UI Components read state via GameState"]
UI --> Actions{"User Action?"}
Actions --> |Buy Card| Buy["buy_card_from_slot()"]
Actions --> |Reroll| Reroll["reroll_market()"]
Actions --> |Place Card| Place["place_card()"]
Buy --> UI
Reroll --> UI
Place --> UI
```

**Diagram sources**
- [v2/mock/engine_mock.py:71-84](file://v2/mock/engine_mock.py#L71-L84)
- [v2/mock/engine_mock.py:105-118](file://v2/mock/engine_mock.py#L105-L118)
- [v2/mock/engine_mock.py:119-122](file://v2/mock/engine_mock.py#L119-L122)

**Section sources**
- [v2/mock/engine_mock.py:61-84](file://v2/mock/engine_mock.py#L61-L84)
- [v2/mock/engine_mock.py:105-122](file://v2/mock/engine_mock.py#L105-L122)

### Bridge Layer (v2/core/)
The bridge layer abstracts engine differences:
- GameState is a singleton that holds an EngineAdapter and caches PublicState
- EngineAdapter translates between GameState expectations and engine_core.Game
- UIAdapter builds immutable snapshots for rendering
- StateStore caches board and pairing data to minimize engine polling

```mermaid
classDiagram
class GameState {
-_adapter : EngineAdapter
-_store : StateStore
-_cached_public_state : PublicState
+hook_engine(engine)
+get_public_state() PublicState
+buy_card_from_slot(...)
+place_card(...)
+commit_human_turn()
}
class EngineAdapter {
-_engine : Game
+perform_buy_card(...)
+perform_placement(...)
+get_shop_window(...)
+get_hand(...)
+run_combat_phase()
}
class UIAdapter {
+build_public_state(adapter, store, formatter) PublicState
}
class StateStore {
-_board_names : Dict
-_board_rotations : Dict
+update_board(player_index, board_dict)
+get_board_names() Dict
}
GameState --> EngineAdapter : "delegates"
GameState --> UIAdapter : "builds snapshots"
GameState --> StateStore : "caches"
```

**Diagram sources**
- [v2/core/game_state.py:14-40](file://v2/core/game_state.py#L14-L40)
- [v2/core/engine_adapter.py:38-46](file://v2/core/engine_adapter.py#L38-L46)
- [v2/core/ui_adapter.py:24-27](file://v2/core/ui_adapter.py#L24-L27)
- [v2/core/state_store.py:3-18](file://v2/core/state_store.py#L3-L18)

**Section sources**
- [v2/core/game_state.py:14-40](file://v2/core/game_state.py#L14-L40)
- [v2/core/engine_adapter.py:38-46](file://v2/core/engine_adapter.py#L38-L46)
- [v2/core/ui_adapter.py:24-27](file://v2/core/ui_adapter.py#L24-L27)
- [v2/core/state_store.py:3-18](file://v2/core/state_store.py#L3-L18)

### Factory Pattern for Game Creation
The legacy engine uses a factory to construct games with configurable strategies:
- build_game() creates players with specified strategies
- Injects trigger_passive_fn, combat_phase_fn, and card_pool
- Enables deterministic simulations and training pipelines

```mermaid
sequenceDiagram
participant Client as "Client Code"
participant Factory as "build_game()"
participant Game as "Game"
participant Players as "Players"
Client->>Factory : build_game(["random","warrior",...])
Factory->>Players : create Player(pid=i, strategy=strategies[i])
Factory->>Game : Game(players, trigger_passive_fn, combat_phase_fn, card_pool)
Game-->>Factory : Game instance
Factory-->>Client : Game
```

**Diagram sources**
- [engine_core/game_factory.py:30-70](file://engine_core/game_factory.py#L30-L70)

**Section sources**
- [engine_core/game_factory.py:30-70](file://engine_core/game_factory.py#L30-L70)

### Strategy Pattern for AI Implementations
The AI module implements a strategy pattern:
- AI.buy_cards() selects strategy-specific logic based on player.strategy
- Each strategy (random, warrior, builder, evolver, economist, balancer, rare_hunter, tempo) defines its own scoring and selection
- ParameterizedAI supports trained parameters loaded from JSON

```mermaid
flowchart TD
Start(["AI.buy_cards(player, market, ...)"]) --> CheckStrategy{"player.strategy"}
CheckStrategy --> |random| Random["_buy_random()"]
CheckStrategy --> |warrior| Warrior["_buy_warrior()"]
CheckStrategy --> |builder| Builder["_buy_builder()"]
CheckStrategy --> |evolver| Evolver["_buy_evolver()"]
CheckStrategy --> |economist| Economist["_buy_economist()"]
CheckStrategy --> |balancer| Balancer["_buy_balancer()"]
CheckStrategy --> |rare_hunter| RareHunter["_buy_rare_hunter()"]
CheckStrategy --> |tempo| Tempo["_buy_warrior()"]
Random --> End(["Place cards"])
Warrior --> End
Builder --> End
Evolver --> End
Economist --> End
Balancer --> End
RareHunter --> End
Tempo --> End
```

**Diagram sources**
- [engine_core/ai.py:351-380](file://engine_core/ai.py#L351-L380)
- [engine_core/ai.py:382-574](file://engine_core/ai.py#L382-L574)

**Section sources**
- [engine_core/ai.py:351-380](file://engine_core/ai.py#L351-L380)
- [engine_core/ai.py:382-574](file://engine_core/ai.py#L382-L574)

### UI Integration Through GameState
UI components interact with the engine through GameState:
- Bootstrap initializes assets, builds a game via build_game(), and hooks it to GameState
- UI components call GameState methods (buy_card_from_slot, place_card, reroll_market)
- GameState delegates to EngineAdapter, which translates to engine_core.Game calls
- UIAdapter constructs PublicState snapshots for rendering

```mermaid
sequenceDiagram
participant Bootstrap as "main.py bootstrap"
participant GS as "GameState"
participant EA as "EngineAdapter"
participant EC as "engine_core.Game"
participant UI as "UI Panels"
Bootstrap->>GS : GameState.get().hook_engine(build_game(...))
UI->>GS : buy_card_from_slot(0, slot)
GS->>EA : perform_buy_card(0, slot)
EA->>EC : player.buy_card(...)
EC-->>EA : success
EA-->>GS : ActionResult.OK
GS-->>UI : ActionResult.OK
UI->>GS : get_public_state()
GS->>EA : get_shop_window(0), get_hand(0), get_player(0)
EA-->>GS : data
GS->>UI : PublicState snapshot
```

**Diagram sources**
- [v2/main.py:28-34](file://v2/main.py#L28-L34)
- [v2/core/game_state.py:92-102](file://v2/core/game_state.py#L92-L102)
- [v2/core/engine_adapter.py:81-114](file://v2/core/engine_adapter.py#L81-L114)
- [v2/core/ui_adapter.py:97-120](file://v2/core/ui_adapter.py#L97-L120)

**Section sources**
- [v2/main.py:28-34](file://v2/main.py#L28-L34)
- [v2/core/game_state.py:92-102](file://v2/core/game_state.py#L92-L102)
- [v2/core/engine_adapter.py:81-114](file://v2/core/engine_adapter.py#L81-L114)
- [v2/core/ui_adapter.py:97-120](file://v2/core/ui_adapter.py#L97-L120)

## Dependency Analysis
The modern architecture minimizes coupling through abstraction:
- UI depends only on GameState interface
- GameState depends on EngineAdapter abstraction
- EngineAdapter depends on engine_core.Game
- MockGame provides a compatible interface for parallel development

```mermaid
graph LR
UI["UI Components"] --> GS["GameState"]
GS --> EA["EngineAdapter"]
EA --> EC["engine_core.Game"]
GS --> MOCK["MockGame"]
MOCK -.-> UI
EC -.-> UI
```

**Diagram sources**
- [v2/core/game_state.py:37-40](file://v2/core/game_state.py#L37-L40)
- [v2/core/engine_adapter.py:38-46](file://v2/core/engine_adapter.py#L38-L46)
- [v2/mock/engine_mock.py:61-84](file://v2/mock/engine_mock.py#L61-L84)

**Section sources**
- [v2/core/game_state.py:37-40](file://v2/core/game_state.py#L37-L40)
- [v2/core/engine_adapter.py:38-46](file://v2/core/engine_adapter.py#L38-L46)
- [v2/mock/engine_mock.py:61-84](file://v2/mock/engine_mock.py#L61-L84)

## Performance Considerations
- GameState caches PublicState to avoid repeated expensive computations
- EngineAdapter performs safe type coercion and graceful fallbacks
- UIAdapter computes synergy and passive feeds from cached data
- Mock engine uses seeded RNG for deterministic testing

## Troubleshooting Guide
Common issues and resolutions:
- EngineAdapter errors: Check engine attribute access and type coercion
- GameState cache misses: Call _invalidate_cache() after mutations
- UI sync problems: Use GameState.get_public_state() instead of direct engine access
- Mock limitations: Intentional simplifications; swap to EngineAdapter for full features

**Section sources**
- [v2/core/engine_adapter.py:48-53](file://v2/core/engine_adapter.py#L48-L53)
- [v2/core/game_state.py:55-57](file://v2/core/game_state.py#L55-L57)
- [v2/HYBRID_ENGINE_CORE_VS_MOCK_REPORT.md:744-758](file://v2/HYBRID_ENGINE_CORE_VS_MOCK_REPORT.md#L744-L758)

## Conclusion
The transition from engine_core/ to v2/ demonstrates a successful architectural evolution:
- Legacy engine_core/ provides a complete, battle-tested simulation
- v2/ introduces a robust bridge layer enabling parallel UI and engine development
- Factory and strategy patterns ensure clean separation of concerns
- Backward compatibility is maintained through GameState abstraction
- The remaining work focuses on integrating the production engine via EngineAdapter rather than implementing missing features