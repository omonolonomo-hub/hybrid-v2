# Requirements Document

## Introduction

This feature implements a minimal safe refactor of economist strategy parameter loading. The current system has hardcoded TRAINED_PARAMS at the top of ai.py. This Phase 0 refactor will enable crash-proof JSON-based parameter loading with hot-reload at initialization, using pathlib, and maintaining a simple priority system. This is economist-only with no new infrastructure, logging, or validation layers.

## Glossary

- **Parameter_Loader**: The helper function that loads economist strategy parameters from JSON file
- **Economist_Strategy**: The economist AI strategy in ParameterizedAI class
- **Parameter_File**: The JSON file containing economist parameters (trained_params.json in project root)
- **Hardcoded_Defaults**: The fallback parameter values embedded in code (current TRAINED_PARAMS)
- **Hot_Reload**: Loading parameters from disk once at game initialization (not per-turn)
- **Manual_Override**: Constructor-level parameter injection that bypasses file loading

## Requirements

### Requirement 1: Crash-Proof Parameter Loading

**User Story:** As a developer, I want the parameter loading system to never crash the simulation, so that missing or corrupted configuration files don't break gameplay.

#### Acceptance Criteria

1. WHEN the Parameter_File is missing, THE Parameter_Loader SHALL return Hardcoded_Defaults
2. WHEN the Parameter_File contains invalid JSON, THE Parameter_Loader SHALL return Hardcoded_Defaults
3. IF an exception occurs during file reading, THEN THE Parameter_Loader SHALL catch the exception and return Hardcoded_Defaults
4. THE Parameter_Loader SHALL NOT raise any exceptions to calling code

### Requirement 2: Pathlib-Based File Access

**User Story:** As a developer, I want to use modern pathlib instead of os.path, so that the codebase follows current Python best practices.

#### Acceptance Criteria

1. THE Parameter_Loader SHALL use pathlib.Path for all file path operations
2. THE Parameter_Loader SHALL resolve the Parameter_File path as "trained_params.json" in project root
3. THE Parameter_Loader SHALL use Path.exists() for file existence checks
4. THE Parameter_Loader SHALL use Path.read_text() for file reading operations

### Requirement 3: Hot Reload at Initialization

**User Story:** As a researcher, I want parameters to reload from disk at game start, so that I can tune economist parameters between simulation runs without code changes.

#### Acceptance Criteria

1. WHEN the Economist_Strategy is initialized, THE Parameter_Loader SHALL read the Parameter_File from disk
2. THE Parameter_Loader SHALL execute ONLY during Economist_Strategy initialization
3. THE Parameter_Loader SHALL NOT execute during per-turn game logic
4. THE Economist_Strategy SHALL cache loaded parameters for the duration of a single game

### Requirement 4: Parameter Priority System

**User Story:** As a developer, I want a clear parameter priority hierarchy, so that I can override parameters at different levels for testing and production.

#### Acceptance Criteria

1. WHEN Manual_Override parameters are provided to constructor, THE Economist_Strategy SHALL use Manual_Override parameters
2. WHEN Manual_Override is None AND Parameter_File exists, THE Economist_Strategy SHALL use Parameter_File parameters
3. WHEN Manual_Override is None AND Parameter_File does not exist, THE Economist_Strategy SHALL use Hardcoded_Defaults
4. THE Parameter_Loader SHALL use simple dict.get() for merging partial parameters with defaults
