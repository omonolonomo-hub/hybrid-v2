# Design Document: Strategy Parameters Hot Reload

## Overview

This design implements a minimal, crash-proof parameter loading system for the economist AI strategy. The current implementation has hardcoded TRAINED_PARAMS at the top of ai.py. This Phase 0 refactor enables JSON-based parameter loading with hot-reload at initialization while maintaining backward compatibility and zero-crash guarantees.

The design follows a simple three-tier priority system: manual overrides > JSON file > hardcoded defaults. All file operations use pathlib for modern Python practices, and the system never raises exceptions regardless of file system state.

Key design principles:
- Crash-proof: Never raise exceptions, always return valid parameters
- Minimal scope: Economist strategy only, no multi-strategy support
- Hot-reload: Load once at initialization, cache for game duration
- Backward compatible: Existing code continues to work unchanged
- No new infrastructure: No logging, validation layers, or dependencies

## Architecture

### Component Structure

```
ai.py
├── load_strategy_params()          # Helper function (new)
│   ├── Uses pathlib.Path
│   ├── Reads trained_params.json
│   └── Returns dict (never raises)
│
├── ParameterizedAI                 # New class (wraps AI)
│   ├── __init__(strategy, params)  # Constructor with params
│   ├── self.p                      # Cached parameters
│   └── buy_cards()                 # Delegates to AI
│
└── AI._buy_economist()             # Modified method
    └── Uses self.p.get() for params
```

### Data Flow

```
Initialization:
  ParameterizedAI.__init__()
    → load_strategy_params()
      → Path("trained_params.json").exists()?
        → Yes: json.loads(Path.read_text())
        → No: return {}
    → Merge: params arg > JSON > TRAINED_PARAMS
    → Store in self.p

Per-Turn Execution:
  ParameterizedAI.buy_cards()
    → AI._buy_economist(player, ...)
      → Uses self.p.get("thresh_high", default)
      → No file I/O
```

### Priority System

```
Parameter Resolution Order:
1. Manual Override (constructor params argument)
   ↓ (if None or partial)
2. JSON File (trained_params.json)
   ↓ (if missing or invalid)
3. Hardcoded Defaults (TRAINED_PARAMS["economist"])
```

## Components and Interfaces

### 1. load_strategy_params() Helper Function

**Purpose:** Load economist parameters from JSON file with crash-proof guarantees.

**Signature:**
```python
def load_strategy_params() -> Dict[str, Any]:
    """Load strategy parameters from trained_params.json.
    
    Returns:
        Dict containing economist parameters, or empty dict on any error.
        Never raises exceptions.
    """
```

**Behavior:**
- Uses `pathlib.Path` for all file operations
- Looks for `trained_params.json` in project root (same directory as ai.py parent)
- Returns empty dict `{}` on any error (missing file, invalid JSON, I/O error, etc.)
- Never raises exceptions to calling code

**Error Handling:**
- Wraps all operations in try-except with broad `Exception` catch
- Returns `{}` for: FileNotFoundError, JSONDecodeError, PermissionError, IOError, etc.
- No logging or error messages (silent failure with safe defaults)

**Pseudocode:**
```python
def load_strategy_params():
    try:
        # Resolve path to trained_params.json in project root
        params_file = Path(__file__).parent.parent / "trained_params.json"
        
        # Check if file exists
        if not params_file.exists():
            return {}
        
        # Read and parse JSON
        content = params_file.read_text(encoding="utf-8")
        data = json.loads(content)
        
        # Return economist params if present
        return data.get("economist", {})
    
    except Exception:
        # Catch ALL exceptions (JSON errors, I/O errors, etc.)
        return {}
```

### 2. ParameterizedAI Class

**Purpose:** Wrapper class that adds parameter injection to AI strategies.

**Signature:**
```python
class ParameterizedAI:
    def __init__(self, strategy: str = "economist", params: Optional[Dict[str, Any]] = None):
        """Initialize parameterized AI with strategy and optional parameter overrides.
        
        Args:
            strategy: AI strategy name (only "economist" supported in Phase 0)
            params: Optional parameter overrides (bypasses file loading if provided)
        """
```

**Attributes:**
- `self.strategy`: Strategy name (string)
- `self.p`: Resolved parameters (dict) - cached for game duration

**Parameter Resolution Logic:**
```python
def __init__(self, strategy="economist", params=None):
    self.strategy = strategy
    
    # Load defaults from hardcoded TRAINED_PARAMS
    defaults = TRAINED_PARAMS.get("economist", {})
    
    # Load from JSON file (returns {} on error)
    file_params = load_strategy_params()
    
    # Merge: defaults < file_params < manual params
    self.p = {**defaults, **file_params}
    if params is not None:
        self.p.update(params)
```

**Methods:**
- `buy_cards(player, market, ...)`: Delegates to `AI.buy_cards()`, passing self for parameter access
- `place_cards(player, ...)`: Delegates to `AI.place_cards()`

### 3. Modified AI._buy_economist()

**Changes:**
- Accept `ai_instance` parameter (ParameterizedAI instance)
- Replace hardcoded values with `ai_instance.p.get(key, default)`
- No changes to decision logic or method signature (except ai_instance param)

**Parameter Mapping:**
```python
# Current hardcoded values → New parameterized values
turn <= 8                    → turn <= ai_instance.p.get("greed_turn_end", 8)
gold >= 12                   → gold >= ai_instance.p.get("greed_gold_thresh", 12)
9 <= turn <= 18              → greed_end < turn <= ai_instance.p.get("spike_turn_end", 18)
gold >= 40                   → gold >= ai_instance.p.get("spike_r4_thresh", 40)
gold >= 25                   → gold >= ai_instance.p.get("thresh_high", 25)
gold >= 15                   → gold >= ai_instance.p.get("buy_2_thresh", 15)
gold >= 60                   → gold >= ai_instance.p.get("convert_r5_thresh", 60)
cnt = min(max_cards, 3)      → cnt = min(max_cards, int(ai_instance.p.get("spike_buy_count", 3)))
cnt = min(max_cards, 4)      → cnt = min(max_cards, int(ai_instance.p.get("convert_buy_count", 4)))
```

**Modified Signature:**
```python
@staticmethod
def _buy_economist(player: Player, market: List[Card], max_cards: int,
                   market_obj=None, rng=None, trigger_passive_fn=None,
                   ai_instance=None):  # NEW PARAMETER
    """Phase-aware economist strategy with parameterized thresholds."""
```

## Data Models

### Parameter Dictionary Structure

```python
{
    "economist": {
        # Threshold parameters (gold amounts)
        "thresh_high": float,        # High gold threshold (default: 27.0)
        "thresh_mid": float,         # Mid gold threshold (default: 5.9)
        "thresh_low": float,         # Low gold threshold (default: 11.6)
        "buy_2_thresh": float,       # Threshold for buying 2 cards (default: 15.0)
        
        # Phase timing parameters (turn numbers)
        "greed_turn_end": float,     # End of greed phase (default: 6.6)
        "spike_turn_end": float,     # End of spike phase (default: 14.8)
        
        # Phase-specific thresholds
        "greed_gold_thresh": float,  # Gold threshold in greed phase (default: 15.0)
        "spike_r4_thresh": float,    # R4 threshold in spike phase (default: 42.1)
        "convert_r5_thresh": float,  # R5 threshold in convert phase (default: 80.0)
        
        # Buy count parameters
        "spike_buy_count": float,    # Cards to buy in spike (default: 3.2)
        "convert_buy_count": float   # Cards to buy in convert (default: 3.6)
    }
}
```

### JSON File Format (trained_params.json)

```json
{
    "economist": {
        "thresh_high": 27.012525825899594,
        "thresh_mid": 5.887870123764179,
        "thresh_low": 11.572130722067811,
        "buy_2_thresh": 15.0,
        "greed_turn_end": 6.556475060280888,
        "spike_turn_end": 14.773731014667712,
        "greed_gold_thresh": 15.0,
        "spike_r4_thresh": 42.07452062733782,
        "convert_r5_thresh": 80.0,
        "spike_buy_count": 3.1891953600814538,
        "convert_buy_count": 3.6086842743641023
    }
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Exception Safety

*For any* file system state (missing file, invalid JSON, I/O errors, permission errors), the `load_strategy_params()` function SHALL return a valid dictionary without raising any exceptions.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

### Property 2: Parameter Override Priority

*For any* set of manual override parameters provided to `ParameterizedAI.__init__()`, those parameters SHALL take precedence over both JSON file parameters and hardcoded defaults in the resolved parameter dictionary.

**Validates: Requirements 4.1**

### Property 3: Partial Parameter Merging

*For any* partial parameter dictionary (containing a subset of economist parameters), the `ParameterizedAI` SHALL merge it with defaults such that provided parameters override defaults and missing parameters use default values.

**Validates: Requirements 4.4**

## Error Handling

### File System Errors

**Strategy:** Silent failure with safe defaults

**Scenarios:**
1. **Missing file:** `load_strategy_params()` returns `{}`
2. **Invalid JSON:** `json.loads()` raises JSONDecodeError → caught → return `{}`
3. **Permission denied:** `Path.read_text()` raises PermissionError → caught → return `{}`
4. **I/O errors:** Any IOError → caught → return `{}`

**Implementation:**
```python
try:
    # All file operations
    ...
except Exception:  # Broad catch - never crash
    return {}
```

### Invalid Parameter Values

**Strategy:** Use defaults via `dict.get()`

**Scenarios:**
1. **Missing parameter key:** `self.p.get("key", default)` returns default
2. **Wrong type:** Caller handles type conversion (e.g., `int(self.p.get(...))`)
3. **Out of range:** No validation - trust parameter source

**No validation layer:** Parameters are used as-is. If values are nonsensical, gameplay behavior may be suboptimal but won't crash.

### Backward Compatibility

**Strategy:** Existing code continues to work

**Scenarios:**
1. **No JSON file:** Falls back to `TRAINED_PARAMS` (current behavior)
2. **No ParameterizedAI:** Direct `AI._buy_economist()` calls still work (ai_instance=None)
3. **Legacy callers:** `ai_instance=None` → use hardcoded values in method

## Testing Strategy

### Unit Tests

**Focus:** Specific examples, edge cases, integration points

**Test Cases:**

1. **File Loading:**
   - Test with valid JSON file → parameters loaded correctly
   - Test with missing file → returns empty dict
   - Test with invalid JSON → returns empty dict
   - Test with empty file → returns empty dict

2. **Parameter Priority:**
   - Test manual override → overrides file and defaults
   - Test file parameters → overrides defaults
   - Test no file, no override → uses defaults

3. **Initialization:**
   - Test ParameterizedAI with params → uses provided params
   - Test ParameterizedAI without params → loads from file
   - Test parameter caching → file changes don't affect running game

4. **Integration:**
   - Test _buy_economist with ai_instance → uses parameterized values
   - Test _buy_economist without ai_instance → uses hardcoded values (backward compat)

### Property-Based Tests

**Focus:** Universal properties across all inputs

**Configuration:**
- Library: `hypothesis` (Python property-based testing)
- Iterations: 100 minimum per property
- Tag format: `# Feature: strategy-params-hot-reload, Property N: <text>`

**Property Tests:**

1. **Property 1: Exception Safety**
   ```python
   @given(file_state=st.one_of(
       st.just("missing"),
       st.just("invalid_json"),
       st.text(),  # Random content
       st.binary()  # Binary garbage
   ))
   def test_load_never_crashes(file_state):
       # Feature: strategy-params-hot-reload, Property 1: Exception Safety
       result = load_strategy_params()
       assert isinstance(result, dict)  # Always returns dict
   ```

2. **Property 2: Parameter Override Priority**
   ```python
   @given(overrides=st.dictionaries(
       keys=st.sampled_from(["thresh_high", "greed_turn_end", "spike_buy_count"]),
       values=st.floats(min_value=0, max_value=100)
   ))
   def test_override_priority(overrides):
       # Feature: strategy-params-hot-reload, Property 2: Parameter Override Priority
       ai = ParameterizedAI(params=overrides)
       for key, value in overrides.items():
           assert ai.p[key] == value
   ```

3. **Property 3: Partial Parameter Merging**
   ```python
   @given(partial_params=st.dictionaries(
       keys=st.sampled_from(["thresh_high", "greed_turn_end"]),
       values=st.floats(min_value=0, max_value=100),
       min_size=1, max_size=5
   ))
   def test_partial_merge(partial_params):
       # Feature: strategy-params-hot-reload, Property 3: Partial Parameter Merging
       ai = ParameterizedAI(params=partial_params)
       
       # Provided params should be present
       for key in partial_params:
           assert key in ai.p
           assert ai.p[key] == partial_params[key]
       
       # Missing params should have defaults
       all_keys = set(TRAINED_PARAMS["economist"].keys())
       for key in all_keys - set(partial_params.keys()):
           assert key in ai.p  # Default should be present
   ```

### Integration Tests

**Focus:** End-to-end behavior with real file system

**Test Cases:**

1. **Full Simulation Run:**
   - Create trained_params.json with custom values
   - Run simulation with ParameterizedAI
   - Verify economist behavior reflects custom parameters

2. **Hot Reload Between Games:**
   - Run game 1 with params A
   - Modify trained_params.json to params B
   - Run game 2 → should use params B

3. **Backward Compatibility:**
   - Run simulation with legacy AI class
   - Verify no crashes, uses hardcoded defaults

## Low-Level Design

### Function: load_strategy_params()

**Location:** `engine_core/ai.py` (top-level function, after TRAINED_PARAMS)

**Implementation:**
```python
def load_strategy_params() -> Dict[str, Any]:
    """Load strategy parameters from trained_params.json.
    
    Crash-proof parameter loading with pathlib. Returns empty dict
    on any error (missing file, invalid JSON, I/O errors).
    
    Returns:
        Dict containing economist parameters, or {} on error.
        Never raises exceptions.
    
    File location: trained_params.json in project root
    Expected structure: {"economist": {...}}
    """
    try:
        # Resolve path: project_root/trained_params.json
        # ai.py is in engine_core/, so parent.parent gets project root
        params_file = Path(__file__).parent.parent / "trained_params.json"
        
        # Check existence before reading
        if not params_file.exists():
            return {}
        
        # Read file content
        content = params_file.read_text(encoding="utf-8")
        
        # Parse JSON
        data = json.loads(content)
        
        # Extract economist params (return {} if key missing)
        return data.get("economist", {})
    
    except Exception:
        # Catch ALL exceptions:
        # - JSONDecodeError (invalid JSON)
        # - PermissionError (file permissions)
        # - IOError (disk errors)
        # - UnicodeDecodeError (encoding issues)
        # - Any other unexpected errors
        return {}
```

**Dependencies:**
```python
from pathlib import Path
import json
from typing import Dict, Any
```

### Class: ParameterizedAI

**Location:** `engine_core/ai.py` (after AI class definition)

**Implementation:**
```python
class ParameterizedAI:
    """AI wrapper with parameter injection for economist strategy.
    
    Supports three-tier parameter priority:
    1. Manual overrides (constructor params argument)
    2. JSON file (trained_params.json)
    3. Hardcoded defaults (TRAINED_PARAMS)
    
    Parameters are loaded once at initialization and cached for
    the game duration (hot-reload at game start, not per-turn).
    
    Phase 0: Economist strategy only.
    """
    
    def __init__(self, strategy: str = "economist", params: Optional[Dict[str, Any]] = None):
        """Initialize parameterized AI.
        
        Args:
            strategy: AI strategy name (only "economist" supported)
            params: Optional parameter overrides (bypasses file if provided)
        
        Parameter resolution order:
            params argument > JSON file > TRAINED_PARAMS defaults
        """
        self.strategy = strategy
        
        # Start with hardcoded defaults
        defaults = TRAINED_PARAMS.get(strategy, {})
        
        # Load from JSON file (returns {} on any error)
        file_params = load_strategy_params()
        
        # Merge: defaults < file_params < manual params
        # Using dict unpacking for simple merge
        self.p = {**defaults, **file_params}
        
        # Apply manual overrides if provided
        if params is not None:
            self.p.update(params)
    
    def buy_cards(self, player: Player, market: List[Card], max_cards: int = 1,
                  market_obj=None, rng=None, trigger_passive_fn=None):
        """Delegate to AI.buy_cards with parameter injection."""
        # Pass self to AI methods for parameter access
        AI.buy_cards(player, market, max_cards, market_obj, rng, 
                     trigger_passive_fn, ai_instance=self)
    
    def place_cards(self, player: Player, rng=None, 
                    placement_strategy: str = "smart_default"):
        """Delegate to AI.place_cards."""
        AI.place_cards(player, rng, placement_strategy)
```

### Modified Method: AI._buy_economist()

**Changes:**
1. Add `ai_instance` parameter (default None for backward compatibility)
2. Replace hardcoded values with `ai_instance.p.get(key, default)`
3. Keep all decision logic unchanged

**Parameter Access Pattern:**
```python
# Helper function for safe parameter access
def get_param(key, default):
    if ai_instance is not None:
        return ai_instance.p.get(key, default)
    return default

# Usage in method
greed_turn_end = get_param("greed_turn_end", 8)
if turn <= greed_turn_end:
    # GREED phase logic
    ...
```

**Modified Signature:**
```python
@staticmethod
def _buy_economist(player: Player, market: List[Card], max_cards: int,
                   market_obj=None, rng=None, trigger_passive_fn=None,
                   ai_instance=None):  # NEW: Parameter injection
    """Phase-aware economist strategy with parameterized thresholds.
    
    Args:
        ai_instance: ParameterizedAI instance for parameter access (optional)
                     If None, uses hardcoded defaults (backward compatibility)
    """
```

**Key Modifications:**
```python
# Phase 1: GREED
greed_turn_end = get_param("greed_turn_end", 8)
greed_gold_thresh = get_param("greed_gold_thresh", 12)

if turn <= greed_turn_end:
    if gold >= greed_gold_thresh:
        # Buy logic
        ...

# Phase 2: SPIKE
spike_turn_end = get_param("spike_turn_end", 18)
spike_r4_thresh = get_param("spike_r4_thresh", 40)
thresh_high = get_param("thresh_high", 25)
buy_2_thresh = get_param("buy_2_thresh", 15)
spike_buy_count = int(get_param("spike_buy_count", 3))

elif turn <= spike_turn_end:
    if gold >= spike_r4_thresh:
        max_cost = CARD_COSTS["4"]
    elif gold >= thresh_high:
        max_cost = CARD_COSTS["3"]
    # ... rest of logic
    
    if gold >= thresh_high:
        cnt = min(max_cards, spike_buy_count)
    elif gold >= buy_2_thresh:
        cnt = min(max_cards, 2)
    # ... rest of logic

# Phase 3: CONVERT
convert_r5_thresh = get_param("convert_r5_thresh", 60)
convert_buy_count = int(get_param("convert_buy_count", 4))

else:
    if gold >= convert_r5_thresh:
        max_cost = CARD_COSTS["5"]
    # ... rest of logic
    
    cnt = min(max_cards, convert_buy_count)
    # ... rest of logic
```

### Modified Method: AI.buy_cards()

**Changes:**
1. Add `ai_instance` parameter
2. Pass to strategy methods that need it

**Implementation:**
```python
@staticmethod
def buy_cards(player: Player, market: List[Card], max_cards: int = 1,
              market_obj=None, rng=None, trigger_passive_fn=None,
              ai_instance=None):  # NEW: Parameter injection
    """Buy from market according to player.strategy."""
    if rng is None:
        rng = random.Random()
    
    if player.strategy == "economist":
        AI._buy_economist(player, market, max_cards, market_obj, rng, 
                         trigger_passive_fn, ai_instance)
    # ... other strategies unchanged
```

## Implementation Notes

### Phase 0 Constraints

**What's included:**
- load_strategy_params() helper function
- ParameterizedAI class with params parameter
- Modified _buy_economist() to use self.p
- Backward compatibility for legacy callers

**What's NOT included:**
- No logging (no print statements, no log files)
- No validation layer (trust parameter values)
- No multi-strategy support (economist only)
- No new dependencies (uses stdlib only: pathlib, json)
- No configuration system (single hardcoded file path)
- No parameter schema or type checking

### Backward Compatibility

**Existing code continues to work:**
```python
# Legacy usage (still works)
ai = AI()
ai.buy_cards(player, market)  # Uses hardcoded TRAINED_PARAMS

# New usage (parameterized)
ai = ParameterizedAI(params={"thresh_high": 30.0})
ai.buy_cards(player, market)  # Uses custom params
```

### Migration Path

**For existing simulations:**
1. No changes required - code continues to work
2. Optional: Create trained_params.json for hot-reload
3. Optional: Switch to ParameterizedAI for parameter injection

**For parameter tuning:**
1. Create trained_params.json in project root
2. Modify parameters between simulation runs
3. No code changes needed - parameters reload at game start

### File Location

**Why project root?**
- Simple path resolution: `Path(__file__).parent.parent`
- Accessible to all simulation scripts
- Easy to find and edit manually
- Matches current TRAINED_PARAMS location (top of ai.py)

**Alternative considered:** `.kiro/config/` directory
- Rejected: Adds complexity, requires directory creation
- Phase 0 goal: Minimal changes

### Performance Considerations

**File I/O cost:**
- Load once per game initialization (not per-turn)
- Typical file size: <1KB (11 float parameters)
- Read time: <1ms on modern systems
- Negligible impact on simulation performance

**Memory cost:**
- One dict per ParameterizedAI instance
- ~11 float values = ~88 bytes
- Negligible memory overhead

### Future Extensions (Out of Scope)

**Not implemented in Phase 0:**
- Multi-strategy support (builder, evolver, etc.)
- Parameter validation and schema
- Logging and diagnostics
- Configuration file discovery (multiple locations)
- Hot-reload during gameplay (per-turn reload)
- Parameter versioning and migration
- Web UI for parameter editing

These may be added in future phases if needed.
