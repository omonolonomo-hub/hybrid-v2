# Design Document: Passive Efficiency KPI Logging

## Overview

This feature optimizes the passive event logging system by eliminating real-time file I/O operations and replacing them with in-memory accumulation followed by a single end-of-simulation write. The current system writes to `passive_events.jsonl` on every passive trigger, creating significant performance overhead during simulations. The new design aggregates passive efficiency data in memory and generates a single `passive_efficiency_kpi.jsonl` file at simulation end.

### Goals

- Eliminate per-trigger file writes to improve simulation performance
- Provide aggregated passive efficiency metrics for learning system consumption
- Maintain backward compatibility with existing passive trigger detection
- Enable normalized value comparison across different passive types
- Support win rate correlation analysis for passive effectiveness

### Non-Goals

- Modifying passive trigger detection logic
- Changing the passive ability system architecture
- Altering existing summary file formats (strategy_summary.json, passive_summary.json)
- Real-time passive monitoring during gameplay

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Game Execution                          │
│  ┌──────────────┐    ┌──────────────┐   ┌──────────────┐  │
│  │   Game.run() │───▶│ trigger_     │──▶│   Player     │  │
│  │              │    │ passive()    │   │ .passive_    │  │
│  │              │    │              │   │ buff_log[]   │  │
│  └──────────────┘    └──────────────┘   └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              KPI_Aggregator (Computation)                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  _passive_game_data: Dict[                           │  │
│  │    (game_id, strategy, card_name, passive_type):     │  │
│  │      {total_triggers, raw_value, normalized_value,   │  │
│  │       game_won}                                       │  │
│  │  ]                                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  aggregate_passive_buff_log() ──▶ Process Player data      │
│  normalize_passive_value()    ──▶ Value conversion         │
│  get_kpi_records()            ──▶ Return formatted data    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              StrategyLogger (I/O Only)                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  _kpi_aggregator: KPI_Aggregator                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  end_game()  ──▶ Call _kpi_aggregator.aggregate()          │
│  flush()     ──▶ Get data and write to file                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│         Output: passive_efficiency_kpi.jsonl                │
│  {game_id, strategy, card_name, passive_type,               │
│   total_triggers, raw_value, normalized_value,              │
│   efficiency_score, game_won}                               │
└─────────────────────────────────────────────────────────────┘
```

### Separation of Concerns

**KPI_Aggregator (Computation Layer)**
- Owns all data aggregation logic
- Manages `_passive_game_data` dictionary
- Performs value normalization
- Calculates efficiency metrics
- No file I/O operations
- Easily testable without mocking file system

**StrategyLogger (I/O Layer)**
- Owns file writing operations
- Delegates computation to KPI_Aggregator
- Handles file path management
- Manages error handling for I/O failures
- No business logic or calculations

### Data Flow

1. **Trigger Phase**: `trigger_passive()` appends to `Player.passive_buff_log` (existing behavior)
2. **Game End Phase**: `StrategyLogger.end_game()` → `KPI_Aggregator.aggregate_passive_buff_log(player, game_id, game_won)`
3. **Simulation End Phase**: `StrategyLogger.flush()` → `KPI_Aggregator.get_kpi_records()` → Write to file

### Integration Points

**KPI_Aggregator:**
- `__init__()`: Initialize `_passive_game_data` dictionary
- `aggregate_passive_buff_log(player, game_id, game_won)`: Process player's passive_buff_log
- `normalize_passive_value(passive_type, raw_value)`: Convert raw values to normalized values
- `get_kpi_records()`: Return list of KPI records ready for serialization

**StrategyLogger:**
- `__init__()`: Create KPI_Aggregator instance
- `end_game()`: Call aggregator for each player
- `flush()`: Get records from aggregator and write to file
- `_write_passive_efficiency_kpi()`: Pure I/O operation (no computation)

## Components and Interfaces

### KPI_Aggregator (New Class)

**Responsibility**: Data aggregation and computation logic

#### Data Structures

```python
class KPI_Aggregator:
    """
    Aggregates passive efficiency data from Player.passive_buff_log.
    Handles all computation logic without file I/O.
    """
    
    _passive_game_data: Dict[Tuple[int, str, str, str], Dict[str, Any]]
    # Key: (game_id, strategy, card_name, passive_type)
    # Value: {
    #   "total_triggers": int,
    #   "raw_value": float,
    #   "normalized_value": float,
    #   "game_won": bool
    # }
```

#### Public Methods

```python
def __init__(self):
    """Initialize empty aggregation dictionary."""
    self._passive_game_data = {}

def aggregate_passive_buff_log(self, player: "Player", 
                               game_id: int, 
                               game_won: bool) -> None:
    """
    Process a player's passive_buff_log and aggregate into _passive_game_data.
    
    Args:
        player: Player instance with passive_buff_log attribute
        game_id: Unique game identifier
        game_won: Whether this player won the game
    
    Side Effects:
        Updates _passive_game_data dictionary with aggregated values
    """
    if not hasattr(player, 'passive_buff_log'):
        return
    
    for entry in player.passive_buff_log:
        key = (
            game_id,
            player.strategy,
            entry.get("card", "unknown"),
            entry.get("passive", "none")
        )
        
        if key not in self._passive_game_data:
            self._passive_game_data[key] = {
                "total_triggers": 0,
                "raw_value": 0.0,
                "normalized_value": 0.0,
                "game_won": game_won
            }
        
        data = self._passive_game_data[key]
        data["total_triggers"] += 1
        delta = entry.get("delta", 0)
        data["raw_value"] += delta
        
        # Normalize value
        passive_type = entry.get("passive", "none")
        normalized = self.normalize_passive_value(passive_type, delta)
        data["normalized_value"] += normalized

def normalize_passive_value(self, passive_type: str, 
                           raw_value: float) -> float:
    """
    Convert raw passive effect value to normalized value.
    
    Based on empirical game economy analysis from 5000-game simulations:
    - 1 gold ≈ 10 stat points (average card cost/power ratio)
    - 1 combat point = 1 damage potential
    - 1 stat increase = 1 combat power contribution
    
    Args:
        passive_type: Type of passive effect
        raw_value: Raw numeric benefit (gold, stats, points, etc.)
    
    Returns:
        Normalized value for cross-passive comparison
    
    References:
        - docs/kpi/KPI_SIMULATION_SUMMARY.md
        - Simulation data: 5000 games, 8 strategies
    """
    VALUE_CONVERSION = {
        "economy": 10.0,     # 1 gold ≈ 10 stat value
        "combat": 1.0,       # 1 combat point = 1 value
        "combo": 1.0,        # 1 combo point = 1 combat point
        "copy": 1.0,         # 1 stat increase = 1 value
        "synergy_field": 1.0,# 1 stat increase = 1 value
        "survival": 15.0,    # Resurrection ≈ avg card cost × 10
        "none": 0.0
    }
    multiplier = VALUE_CONVERSION.get(passive_type, 0.0)
    return raw_value * multiplier

def get_kpi_records(self) -> List[Dict[str, Any]]:
    """
    Return formatted KPI records ready for serialization.
    
    Returns:
        List of dictionaries with fields:
        - game_id, strategy, card_name, passive_type
        - total_triggers, raw_value, normalized_value
        - efficiency_score, game_won
    """
    records = []
    for key, data in sorted(self._passive_game_data.items()):
        game_id, strategy, card_name, passive_type = key
        total_triggers = data["total_triggers"]
        efficiency_score = (
            data["normalized_value"] / total_triggers 
            if total_triggers > 0 else 0.0
        )
        
        records.append({
            "game_id": game_id,
            "strategy": strategy,
            "card_name": card_name,
            "passive_type": passive_type,
            "total_triggers": total_triggers,
            "raw_value": data["raw_value"],
            "normalized_value": data["normalized_value"],
            "efficiency_score": round(efficiency_score, 4),
            "game_won": data["game_won"]
        })
    
    return records
```

### StrategyLogger Modifications

**Responsibility**: File I/O operations only

#### New Data Structures

```python
class StrategyLogger:
    """
    Handles file writing for strategy and passive KPI data.
    Delegates computation to KPI_Aggregator.
    """
    
    _kpi_aggregator: KPI_Aggregator  # Injected or created in __init__
```

#### Modified Methods

```python
def __init__(self, enabled: bool = True, 
             output_dir: str = "output/strategy_logs",
             kpi_aggregator: Optional[KPI_Aggregator] = None):
    """
    Initialize StrategyLogger with optional KPI_Aggregator injection.
    
    Args:
        enabled: Whether logging is enabled
        output_dir: Directory for output files
        kpi_aggregator: Optional KPI_Aggregator instance (creates new if None)
    """
    self.enabled = enabled
    self.output_dir = Path(output_dir)
    self._kpi_aggregator = kpi_aggregator or KPI_Aggregator()
    
    # ... existing initialization ...

def log_passive(self, card_name: str, passive_type: str,
                trigger: str, owner_strategy: str,
                delta: int, ctx_turn: int):
    """
    Update in-memory statistics only.
    No file write operations.
    """
    # Update _strat summary (existing)
    # Update _passive_card summary (existing)
    # NO _passive_buf.append() or file write

def end_game(self, game: "Game", winner: "Player"):
    """
    Delegate passive_buff_log aggregation to KPI_Aggregator.
    """
    if not self.enabled:
        return
    
    # Existing game_endings.jsonl logic
    # ...
    
    # NEW: Delegate aggregation to KPI_Aggregator
    for player in game.players:
        try:
            game_won = (player.pid == winner.pid)
            self._kpi_aggregator.aggregate_passive_buff_log(
                player, self._game_id, game_won
            )
        except Exception as e:
            print(f"Warning: Error aggregating passive data for player {player.pid}: {e}")
            continue

def flush(self):
    """
    Write all accumulated data to files.
    Delegates data retrieval to KPI_Aggregator.
    """
    if not self.enabled:
        return
    
    # Existing flush logic for other files
    # ...
    
    # NEW: Write passive efficiency KPI
    self._write_passive_efficiency_kpi()

def _write_passive_efficiency_kpi(self):
    """
    Pure I/O operation: Get data from aggregator and write to file.
    No computation logic.
    """
    if not self.enabled:
        return
    
    try:
        path = self.output_dir / "passive_efficiency_kpi.jsonl"
        records = self._kpi_aggregator.get_kpi_records()
        
        with open(path, "w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except IOError as e:
        print(f"Warning: Failed to write passive_efficiency_kpi.jsonl: {e}")
    except Exception as e:
        print(f"Warning: Unexpected error in passive KPI generation: {e}")
```

### Value Normalization System

#### Empirical Game Economy Data

Based on 5000-game simulation analysis:

**Card Economy:**
- Average card cost: 3-4 gold (rarity-2 cards)
- Average card power: ~40 stat points
- **Power-to-cost ratio: 10-13 stat points per gold**

**Combat System:**
- 1 kill = 10 combat points (KILL_PTS constant)
- Average damage per game: 140-180
- Average kills per game: 140-160
- **1 combat point ≈ 1 damage potential**

**Passive Delta Impact:**
- High-performing strategies: 7-8 delta/game → 18-20% win rate
- Low-performing strategies: 2-4 delta/game → 1-5% win rate
- **Strong correlation between passive effectiveness and win rate**

#### Conversion Table

```python
# Located in KPI_Aggregator.normalize_passive_value()
VALUE_CONVERSION = {
    "economy": 10.0,     # 1 gold ≈ 10 stat value (avg card cost/power ratio)
    "combat": 1.0,       # 1 combat point = 1 value (direct damage mapping)
    "combo": 1.0,        # 1 combo point = 1 combat point
    "copy": 1.0,         # 1 stat increase = 1 value (direct power contribution)
    "synergy_field": 1.0,# 1 stat increase = 1 value (field effects same as direct)
    "survival": 15.0,    # Resurrection ≈ avg card cost (3-5 gold) × 10
    "none": 0.0
}
```

**Rationale:**
- **Economy (10.0)**: Buying a card with 1 gold gives ~10 stat points of value
- **Combat/Combo (1.0)**: Direct combat point mapping, 1:1 damage potential
- **Copy/Synergy (1.0)**: Stat increases directly contribute to combat power
- **Survival (15.0)**: Preventing card loss ≈ cost of replacement card (3-5 gold × 10 = 30-50, conservative estimate)

#### Normalization Logic

Implemented in `KPI_Aggregator.normalize_passive_value()` method (see Components and Interfaces section above).

## Data Models

### Passive Efficiency KPI Record

```python
{
    "game_id": int,              # Unique game identifier
    "strategy": str,             # Player strategy name
    "card_name": str,            # Card that triggered passive
    "passive_type": str,         # Type of passive effect
    "total_triggers": int,       # Number of times passive triggered
    "raw_value": float,          # Sum of raw delta values
    "normalized_value": float,   # Sum of normalized values
    "efficiency_score": float,   # normalized_value / total_triggers
    "game_won": bool             # Whether this game was won
}
```

### Player.passive_buff_log Entry (Existing)

```python
{
    "turn": int,           # Game turn when triggered
    "card": str,           # Card name
    "passive": str,        # Passive type
    "trigger": str,        # Trigger event
    "delta": int           # Stat increase amount
}
```

### StrategyLogger._passive_game_data Structure

```python
# REMOVED: This data structure now lives in KPI_Aggregator
# See KPI_Aggregator._passive_game_data in Components and Interfaces section
```


## Error Handling

### Separation of Error Handling Responsibilities

**KPI_Aggregator Error Handling:**
- Handles data validation errors (missing attributes, malformed entries)
- Gracefully skips invalid passive_buff_log entries
- No file I/O error handling (not its responsibility)

**StrategyLogger Error Handling:**
- Handles file I/O errors (write failures, permission issues)
- Handles directory creation errors
- Delegates data validation to KPI_Aggregator

### KPI_Aggregator Error Handling

```python
def aggregate_passive_buff_log(self, player: "Player", 
                               game_id: int, 
                               game_won: bool) -> None:
    """Process passive_buff_log with data validation."""
    if not hasattr(player, 'passive_buff_log'):
        return  # Silently skip players without passive_buff_log
    
    for entry in player.passive_buff_log:
        try:
            # Validate entry structure
            card_name = entry.get("card", "unknown")
            passive_type = entry.get("passive", "none")
            delta = entry.get("delta", 0)
            
            # Aggregate data
            key = (game_id, player.strategy, card_name, passive_type)
            
            if key not in self._passive_game_data:
                self._passive_game_data[key] = {
                    "total_triggers": 0,
                    "raw_value": 0.0,
                    "normalized_value": 0.0,
                    "game_won": game_won
                }
            
            data = self._passive_game_data[key]
            data["total_triggers"] += 1
            data["raw_value"] += delta
            data["normalized_value"] += self.normalize_passive_value(passive_type, delta)
            
        except (KeyError, TypeError, ValueError) as e:
            # Skip malformed entries without crashing
            print(f"Warning: Skipping malformed passive_buff_log entry: {e}")
            continue
```

### StrategyLogger Error Handling

#### File I/O Error Handling

```python
def _write_passive_efficiency_kpi(self):
    """Generate passive_efficiency_kpi.jsonl with robust error handling."""
    if not self.enabled:
        return
    
    try:
        path = self.output_dir / "passive_efficiency_kpi.jsonl"
        records = self._kpi_aggregator.get_kpi_records()
        
        with open(path, "w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except IOError as e:
        print(f"Warning: Failed to write passive_efficiency_kpi.jsonl: {e}")
    except Exception as e:
        print(f"Warning: Unexpected error in passive KPI generation: {e}")
```

#### Directory Creation Error Handling

```python
def __init__(self, enabled: bool = True, 
             output_dir: str = "output/strategy_logs",
             kpi_aggregator: Optional[KPI_Aggregator] = None):
    self.enabled = enabled
    self.output_dir = Path(output_dir)
    self._kpi_aggregator = kpi_aggregator or KPI_Aggregator()
    
    # ... existing initialization ...
    
    if self.enabled:
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"Warning: Failed to create output directory {output_dir}: {e}")
            self.enabled = False  # Disable logging if directory creation fails
```

#### Data Aggregation Error Handling

```python
def end_game(self, game: "Game", winner: "Player"):
    if not self.enabled:
        return
    
    # ... existing game_endings.jsonl logic ...
    
    # Process passive_buff_log with error handling
    for player in game.players:
        try:
            game_won = (player.pid == winner.pid)
            self._kpi_aggregator.aggregate_passive_buff_log(
                player, self._game_id, game_won
            )
        except Exception as e:
            print(f"Warning: Error aggregating passive data for player {player.pid}: {e}")
            continue
```

### Graceful Degradation

- If logging is disabled (`enabled=False`), all methods return immediately without error
- If directory creation fails, logging is automatically disabled
- If file write fails, a warning is printed but simulation continues
- If data aggregation fails for one player, other players are still processed
- Missing or malformed `passive_buff_log` entries are skipped with warnings

## Testing Strategy

### Unit Tests

This feature is primarily focused on data aggregation, file I/O, and configuration management. Property-based testing is not appropriate because:

- The system performs data transformation and aggregation, not algorithmic computation
- File I/O operations are deterministic and best tested with specific examples
- Value normalization uses a fixed conversion table with no complex input space
- Integration with existing systems requires concrete test scenarios

#### Test Categories

**1. KPI_Aggregator Tests (Pure Logic, No I/O)**

**Value Normalization Tests**
- Test economy conversion: 5 gold → 50.0 value (5 × 10.0)
- Test combat conversion: 10 points → 10.0 value (10 × 1.0)
- Test copy conversion: 3 stats → 3.0 value (3 × 1.0)
- Test survival conversion: 1 trigger → 15.0 value (1 × 15.0)
- Test synergy_field conversion: 2 stats → 2.0 value (2 × 1.0)
- Verify zero handling for unknown passive types
- Test edge cases (negative values, zero triggers)

**Data Aggregation Tests**
- Test single game with single passive trigger
- Test multiple games with same card/passive combination
- Test multiple players with different strategies
- Test win/loss tracking accuracy
- Test efficiency_score calculation (division by zero handling)
- Test missing passive_buff_log attribute handling
- Test malformed passive_buff_log entries

**get_kpi_records() Tests**
- Test empty aggregation returns empty list
- Test single record formatting
- Test multiple records sorting
- Test efficiency_score rounding (4 decimal places)

**2. StrategyLogger Tests (I/O Layer)**

**File I/O Tests**
- Test file creation in non-existent directory
- Test JSONL format correctness
- Test UTF-8 encoding with special characters
- Test file write failure handling
- Test relative path resolution

**Integration Tests**
- Test end_game() calls KPI_Aggregator correctly
- Test flush() retrieves data from KPI_Aggregator
- Test _write_passive_efficiency_kpi() writes correct format
- Test disabled logger (enabled=False) has zero overhead

**Error Handling Tests**
- Test directory creation failure
- Test file write permission errors
- Test graceful degradation scenarios

**3. End-to-End Integration Tests**

- Test full simulation flow: trigger → aggregate → write
- Test backward compatibility with existing log_passive() calls
- Test flush() generates all expected files
- Test multiple games with multiple players

#### Example Test Cases

**KPI_Aggregator Tests:**

```python
def test_normalize_economy():
    """Economy passive: 1 gold = 10.0 value"""
    aggregator = KPI_Aggregator()
    result = aggregator.normalize_passive_value("economy", 5.0)
    assert result == 50.0

def test_normalize_combat():
    """Combat passive: 1 point = 1.0 value"""
    aggregator = KPI_Aggregator()
    result = aggregator.normalize_passive_value("combat", 10.0)
    assert result == 10.0

def test_aggregate_single_player():
    """Test aggregating single player's passive_buff_log"""
    aggregator = KPI_Aggregator()
    player = MockPlayer(
        strategy="economist",
        passive_buff_log=[
            {"card": "Merchant", "passive": "economy", "delta": 5}
        ]
    )
    aggregator.aggregate_passive_buff_log(player, game_id=1, game_won=True)
    
    records = aggregator.get_kpi_records()
    assert len(records) == 1
    assert records[0]["total_triggers"] == 1
    assert records[0]["raw_value"] == 5.0
    assert records[0]["normalized_value"] == 50.0
    assert records[0]["efficiency_score"] == 50.0

def test_aggregate_multiple_triggers():
    """Test aggregating multiple triggers for same card/passive"""
    aggregator = KPI_Aggregator()
    player = MockPlayer(
        strategy="warrior",
        passive_buff_log=[
            {"card": "Berserker", "passive": "combat", "delta": 10},
            {"card": "Berserker", "passive": "combat", "delta": 15}
        ]
    )
    aggregator.aggregate_passive_buff_log(player, game_id=1, game_won=False)
    
    records = aggregator.get_kpi_records()
    assert len(records) == 1
    assert records[0]["total_triggers"] == 2
    assert records[0]["raw_value"] == 25.0
    assert records[0]["normalized_value"] == 25.0
    assert records[0]["efficiency_score"] == 12.5

def test_missing_passive_buff_log():
    """Test handling player without passive_buff_log"""
    aggregator = KPI_Aggregator()
    player = MockPlayer(strategy="random")  # No passive_buff_log
    aggregator.aggregate_passive_buff_log(player, game_id=1, game_won=True)
    
    records = aggregator.get_kpi_records()
    assert len(records) == 0

def test_malformed_entry():
    """Test handling malformed passive_buff_log entry"""
    aggregator = KPI_Aggregator()
    player = MockPlayer(
        strategy="economist",
        passive_buff_log=[
            {"card": "Merchant"},  # Missing passive and delta
            {"card": "Trader", "passive": "economy", "delta": 3}
        ]
    )
    aggregator.aggregate_passive_buff_log(player, game_id=1, game_won=True)
    
    records = aggregator.get_kpi_records()
    assert len(records) == 2  # Both entries processed with defaults
```

**StrategyLogger Tests:**

```python
def test_logger_uses_aggregator():
    """Test StrategyLogger delegates to KPI_Aggregator"""
    aggregator = KPI_Aggregator()
    logger = StrategyLogger(enabled=True, kpi_aggregator=aggregator)
    
    game = MockGame(players=[
        MockPlayer(strategy="economist", passive_buff_log=[
            {"card": "Merchant", "passive": "economy", "delta": 5}
        ])
    ])
    winner = game.players[0]
    
    logger.end_game(game, winner)
    
    records = aggregator.get_kpi_records()
    assert len(records) == 1

def test_write_kpi_file():
    """Test _write_passive_efficiency_kpi() creates correct file"""
    aggregator = KPI_Aggregator()
    aggregator._passive_game_data[(1, "economist", "Merchant", "economy")] = {
        "total_triggers": 2,
        "raw_value": 10.0,
        "normalized_value": 100.0,
        "game_won": True
    }
    
    logger = StrategyLogger(enabled=True, kpi_aggregator=aggregator)
    logger._write_passive_efficiency_kpi()
    
    # Verify file exists and contains correct data
    path = Path("output/strategy_logs/passive_efficiency_kpi.jsonl")
    assert path.exists()
    
    with open(path) as f:
        record = json.loads(f.readline())
        assert record["game_id"] == 1
        assert record["strategy"] == "economist"
        assert record["efficiency_score"] == 50.0

def test_disabled_logger_no_overhead():
    """Test disabled logger performs no operations"""
    logger = StrategyLogger(enabled=False)
    logger.log_passive("card", "economy", "income", "economist", 5, 1)
    logger.end_game(mock_game, mock_winner)
    logger.flush()
    # Verify: No files created, no data structures populated
    pass
```

### Integration Testing

- Run full simulation with logging enabled
- Verify `passive_efficiency_kpi.jsonl` contains expected records
- Verify existing summary files still generate correctly
- Verify simulation performance improvement (measure execution time)
- Verify learning system can consume generated KPI file

### Performance Testing

- Measure simulation time with old system (passive_events.jsonl writes)
- Measure simulation time with new system (in-memory aggregation)
- Verify memory usage remains acceptable with large simulations
- Target: 20-30% performance improvement for 1000+ game simulations

### Backward Compatibility Testing

- Verify existing `log_passive()` calls still work
- Verify `strategy_summary.json` and `passive_summary.json` still generate
- Verify `print_summary()` displays correct statistics
- Verify disabled logger (`enabled=False`) maintains zero overhead
