# Cards JSON Path Fix Bugfix Design

## Overview

The `build_card_pool()` function in `engine_core/card.py` currently uses a hardcoded relative path to locate `cards.json`, which fails when the file structure differs from expectations. This fix implements a fallback mechanism that first checks for `cards.json` in the same directory as `card.py`, then falls back to the original path `../assets/data/cards.json` for compatibility with existing environments. This approach ensures the card pool loads successfully across different deployment scenarios while preserving all existing functionality.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - when `cards.json` is not located at the hardcoded relative path `../assets/data/cards.json`
- **Property (P)**: The desired behavior when the bug condition occurs - the system should successfully locate and load `cards.json` using a fallback mechanism
- **Preservation**: Existing card loading behavior for environments where `cards.json` is at the original path must remain unchanged
- **build_card_pool()**: The function in `engine_core/card.py` that loads card data from `cards.json` and returns a list of Card objects
- **base_dir**: The directory containing `card.py`, calculated as `os.path.dirname(os.path.abspath(__file__))`

## Bug Details

### Bug Condition

The bug manifests when `build_card_pool()` is called in an environment where `cards.json` is not located at the expected relative path `../assets/data/cards.json` from the `engine_core/` directory. The function attempts to open a file at a hardcoded path without verifying its existence, leading to a FileNotFoundError.

**Formal Specification:**
```
FUNCTION isBugCondition(environment)
  INPUT: environment representing the file system state
  OUTPUT: boolean
  
  base_dir := directory containing card.py
  original_path := base_dir + "/../assets/data/cards.json"
  
  RETURN NOT file_exists(original_path)
         AND cards.json exists somewhere accessible
         AND build_card_pool() is called
END FUNCTION
```

### Examples

- **Example 1**: When `cards.json` is placed in `engine_core/cards.json` (same directory as `card.py`) but not at `../assets/data/cards.json`, the function raises FileNotFoundError instead of loading the file from the local directory
- **Example 2**: When the project is deployed with a different directory structure where `assets/` is not a sibling of `engine_core/`, the function fails instead of checking alternative locations
- **Example 3**: When running tests or scripts from different working directories, the relative path may not resolve correctly, causing the function to fail
- **Edge Case**: When `cards.json` exists at both locations (same directory and original path), the function should prioritize the local copy for flexibility

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- When `cards.json` exists at the original path `../assets/data/cards.json`, the system must continue to load it successfully
- The structure and content of Card objects created from the JSON data must remain identical (name, category, rarity, stats, passive_type)
- The return type of `build_card_pool()` must remain `List[Card]` with all cards from the JSON file
- JSON parsing logic and card creation logic must remain unchanged
- Error handling for malformed JSON or invalid card data must remain unchanged

**Scope:**
All inputs and environments where `cards.json` is located at the original path `../assets/data/cards.json` should be completely unaffected by this fix. This includes:
- Existing production environments with the standard directory structure
- Existing test suites that rely on the original path
- Any scripts or tools that place `cards.json` at the original location

## Hypothesized Root Cause

Based on the bug description, the root cause is:

1. **Hardcoded Path Assumption**: The function assumes a specific directory structure where `assets/` is always a sibling of `engine_core/`, which may not hold in all deployment scenarios
   - The path is constructed as `os.path.join(base_dir, "..", "assets", "data", "cards.json")`
   - No existence check is performed before attempting to open the file

2. **Lack of Fallback Mechanism**: The function does not attempt alternative locations when the primary path fails
   - No `os.path.exists()` check before opening
   - No try-except logic to attempt alternative paths

3. **Environment Sensitivity**: Different execution contexts (tests, scripts, deployments) may have different working directories or file structures
   - The relative path resolution depends on where `card.py` is located
   - No accommodation for flexible deployment scenarios

## Correctness Properties

Property 1: Bug Condition - Fallback Path Resolution

_For any_ environment where `cards.json` is not located at the original path `../assets/data/cards.json` but exists in the same directory as `card.py`, the fixed `build_card_pool()` function SHALL successfully locate and load the file from the local directory, returning a valid `List[Card]` without raising FileNotFoundError.

**Validates: Requirements 2.1, 2.2**

Property 2: Preservation - Original Path Compatibility

_For any_ environment where `cards.json` is located at the original path `../assets/data/cards.json`, the fixed `build_card_pool()` function SHALL produce exactly the same result as the original function, loading the file from the original path and returning an identical `List[Card]` with the same card objects.

**Validates: Requirements 3.1, 3.2, 3.3**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `engine_core/card.py`

**Function**: `build_card_pool()`

**Specific Changes**:
1. **Add Local Path Check**: Before constructing the original path, check if `cards.json` exists in the same directory as `card.py`
   - Construct local path: `os.path.join(base_dir, "cards.json")`
   - Use `os.path.exists()` to verify file presence

2. **Implement Fallback Logic**: Use the local path if it exists, otherwise fall back to the original path
   - If local path exists: `json_path = os.path.join(base_dir, "cards.json")`
   - Otherwise: `json_path = os.path.join(base_dir, "..", "assets", "data", "cards.json")`

3. **Preserve Existing Logic**: Keep all JSON loading and card creation logic unchanged
   - The `with open(json_path, "r", encoding="utf-8")` block remains the same
   - Card object creation loop remains unchanged

4. **No Error Handling Changes**: Let FileNotFoundError propagate naturally if neither path exists
   - This preserves the original error behavior when the file is genuinely missing

**Implementation Pseudocode**:
```python
def build_card_pool() -> List[Card]:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check local directory first
    local_path = os.path.join(base_dir, "cards.json")
    if os.path.exists(local_path):
        json_path = local_path
    else:
        # Fall back to original path
        json_path = os.path.join(base_dir, "..", "assets", "data", "cards.json")
    
    # Rest of the function remains unchanged
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # ... card creation logic ...
```

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code by simulating environments where the file is not at the expected path, then verify the fix works correctly and preserves existing behavior for the original path.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Create test scenarios where `cards.json` is placed only in the local directory (same as `card.py`) and not at the original path. Run these tests on the UNFIXED code to observe FileNotFoundError and confirm the hardcoded path assumption.

**Test Cases**:
1. **Local File Only Test**: Place `cards.json` in `engine_core/` directory only, remove from `assets/data/` (will fail on unfixed code with FileNotFoundError)
2. **Missing Original Path Test**: Simulate environment where `../assets/data/` directory doesn't exist (will fail on unfixed code)
3. **Different Working Directory Test**: Run `build_card_pool()` from a different working directory where relative paths resolve differently (may fail on unfixed code)
4. **Both Paths Exist Test**: Place `cards.json` at both locations with different content to observe which is loaded (will load from original path on unfixed code)

**Expected Counterexamples**:
- FileNotFoundError when `cards.json` is only in the local directory
- Possible causes: hardcoded path assumption, no existence check, no fallback mechanism

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL environment WHERE isBugCondition(environment) DO
  result := build_card_pool_fixed()
  ASSERT result is List[Card]
  ASSERT len(result) > 0
  ASSERT no FileNotFoundError raised
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL environment WHERE NOT isBugCondition(environment) DO
  ASSERT build_card_pool_original() = build_card_pool_fixed()
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across different file system states
- It catches edge cases that manual unit tests might miss (e.g., different file permissions, symlinks)
- It provides strong guarantees that behavior is unchanged for all environments with the original path

**Test Plan**: Observe behavior on UNFIXED code first with `cards.json` at the original path, then write property-based tests capturing that the same cards are loaded with identical attributes.

**Test Cases**:
1. **Original Path Loading Preservation**: Observe that cards load correctly from `../assets/data/cards.json` on unfixed code, then verify this continues after fix
2. **Card Object Structure Preservation**: Observe that Card objects have correct attributes (name, category, rarity, stats, passive_type) on unfixed code, then verify these remain identical after fix
3. **Card Count Preservation**: Observe the number of cards loaded on unfixed code, then verify the same count after fix
4. **JSON Parsing Preservation**: Verify that malformed JSON produces the same errors before and after fix

### Unit Tests

- Test that `build_card_pool()` successfully loads from local directory when file exists there
- Test that `build_card_pool()` falls back to original path when local file doesn't exist
- Test that FileNotFoundError is raised when file exists at neither location
- Test that local path takes precedence when file exists at both locations
- Test that Card objects are created with correct attributes from JSON data

### Property-Based Tests

- Generate random file system states (file at local path, original path, both, or neither) and verify correct loading behavior
- Generate random valid JSON card data and verify Card objects are created identically regardless of which path is used
- Generate random directory structures and verify the function handles different base_dir values correctly

### Integration Tests

- Test full game initialization with `cards.json` at local path only
- Test full game initialization with `cards.json` at original path only
- Test that switching between deployment scenarios (moving the file) works correctly
- Test that card pool is used correctly by other game systems after loading from either path
