# Requirements Document

## Introduction

Bu özellik, mevcut passive event loglama sistemini optimize ederek simülasyon performansını artırmayı ve learning system için daha kullanışlı KPI verileri üretmeyi amaçlamaktadır. Şu anki sistem her passive tetiklendiğinde `passive_events.jsonl` dosyasına yazma yapmakta ve bu durum simülasyonu yavaşlatmaktadır. Yeni sistem, passive etkilerini oyun boyunca bellekte biriktirip simülasyon sonunda tek bir özet dosya (`passive_efficiency_kpi.jsonl`) oluşturacaktır.

## Glossary

- **Passive_System**: Kartların pasif yeteneklerini yöneten sistem (passive_trigger.py, passives/ modülleri)
- **Strategy_Logger**: Strateji bazlı istatistikleri toplayan ve dosyaya yazan sınıf (strategy_logger.py)
- **Player**: Oyuncu durumunu yöneten sınıf (player.py)
- **Game**: Oyun akışını yöneten sınıf (game.py)
- **KPI_Aggregator**: Passive etkinlik verilerini oyun boyunca biriktiren yeni bileşen
- **Passive_Efficiency_KPI**: Her kart/pasif kombinasyonu için özet metrikler içeren veri yapısı
- **Learning_System**: G1-G6 stat gruplarını kullanarak strateji optimizasyonu yapan sistem
- **Normalized_Value**: Farklı passive türlerinin etkilerini karşılaştırılabilir hale getiren standardize edilmiş değer metriği
- **Value_Conversion_Table**: Her passive_type için raw değerleri normalized değerlere dönüştüren katsayı tablosu

## Requirements

### Requirement 1: Remove Real-Time Passive Event Logging

**User Story:** As a simulation developer, I want to eliminate per-trigger passive event logging, so that simulation performance improves significantly.

#### Acceptance Criteria

1. THE Strategy_Logger SHALL NOT write to passive_events.jsonl during game execution
2. THE Passive_System SHALL NOT call file write operations when a passive triggers
3. WHEN a passive triggers, THE System SHALL accumulate data in memory instead of writing to disk
4. THE System SHALL maintain backward compatibility with existing passive trigger detection logic

### Requirement 2: Implement In-Memory KPI Accumulation

**User Story:** As a simulation developer, I want to accumulate passive efficiency data in memory during gameplay, so that I can minimize disk I/O operations.

#### Acceptance Criteria

1. THE KPI_Aggregator SHALL maintain a dictionary structure for each card/passive combination
2. WHEN a passive triggers, THE KPI_Aggregator SHALL increment the trigger counter for that card
3. WHEN a passive produces numeric benefit, THE KPI_Aggregator SHALL accumulate the total value
4. THE KPI_Aggregator SHALL track game_id, strategy, card_name, and passive_type for each entry
5. THE System SHALL use relative paths for all file operations
6. THE System SHALL handle errors gracefully with try-except blocks

### Requirement 3: Generate Passive Efficiency KPI File

**User Story:** As a learning system developer, I want a single passive efficiency KPI file after simulation, so that I can analyze passive effectiveness without processing thousands of individual events.

#### Acceptance Criteria

1. WHEN simulation completes, THE Strategy_Logger SHALL generate passive_efficiency_kpi.jsonl
2. THE passive_efficiency_kpi.jsonl file SHALL contain one JSON object per line
3. THE System SHALL write the file to output/strategy_logs/ directory
4. THE System SHALL use UTF-8 encoding with ensure_ascii=False
5. THE System SHALL NOT create passive_events.jsonl file

### Requirement 4: Calculate Passive Efficiency Metrics

**User Story:** As a data analyst, I want comprehensive efficiency metrics for each passive, so that I can identify which passives contribute most to winning strategies.

#### Acceptance Criteria

1. FOR EACH card/passive combination, THE System SHALL calculate total_triggers (total number of activations)
2. FOR EACH card/passive combination, THE System SHALL calculate total_value (cumulative numeric benefit)
3. FOR EACH card/passive combination, THE System SHALL calculate efficiency_score (total_value / total_triggers)
4. WHEN total_triggers is zero, THE System SHALL set efficiency_score to zero
5. THE System SHALL include game_id, strategy, card_name, and passive_type in each KPI record

### Requirement 5: Track Win Rate Contribution

**User Story:** As a strategy analyst, I want to know win rate correlation for each passive, so that I can identify passives that contribute to victories.

#### Acceptance Criteria

1. WHEN a game ends, THE System SHALL record whether the game was won or lost
2. FOR EACH passive used in a game, THE System SHALL associate the game outcome with that passive
3. THE System SHALL calculate win_rate_contribution as (wins / total_games) for each passive
4. THE passive_efficiency_kpi.jsonl SHALL include win_rate_contribution field
5. WHEN a passive has zero games, THE System SHALL set win_rate_contribution to zero

### Requirement 6: Integrate with Existing Player Passive Buff Log

**User Story:** As a system integrator, I want to leverage existing Player.passive_buff_log data, so that I don't duplicate tracking logic.

#### Acceptance Criteria

1. THE System SHALL read passive trigger data from Player.passive_buff_log
2. WHEN check_copy_strengthening executes, THE System SHALL use existing passive_buff_log entries
3. WHEN trigger_passive executes, THE System SHALL use existing passive_buff_log entries
4. THE System SHALL NOT create duplicate tracking structures in Player class
5. THE System SHALL aggregate passive_buff_log data at game end

### Requirement 7: Optimize File I/O Operations

**User Story:** As a performance engineer, I want minimal file operations during simulation, so that simulation speed is maximized.

#### Acceptance Criteria

1. THE System SHALL open passive_efficiency_kpi.jsonl file only once per simulation
2. THE System SHALL write all KPI records in a single batch operation
3. THE System SHALL close the file immediately after writing
4. THE System SHALL NOT use buffered writes with periodic flushes during gameplay
5. WHEN file operations fail, THE System SHALL log the error and continue execution

### Requirement 8: Maintain Strategy Logger Integration

**User Story:** As a system architect, I want seamless integration with Strategy_Logger, so that all logging systems work cohesively.

#### Acceptance Criteria

1. THE Strategy_Logger.flush() method SHALL trigger passive KPI file generation
2. THE Strategy_Logger SHALL maintain existing summary file generation (strategy_summary.json, passive_summary.json)
3. THE Strategy_Logger SHALL update passive_summary.json to reference passive_efficiency_kpi.jsonl
4. THE System SHALL preserve existing log_passive() method signature for backward compatibility
5. THE Strategy_Logger.print_summary() SHALL display passive efficiency statistics

### Requirement 9: Support Learning System Integration

**User Story:** As a machine learning engineer, I want KPI data formatted for direct consumption by the learning system, so that I can train strategy models efficiently.

#### Acceptance Criteria

1. THE passive_efficiency_kpi.jsonl format SHALL be compatible with G1-G6 stat group processing
2. THE System SHALL include all fields required for KPI improvement analysis
3. THE System SHALL provide aggregated metrics per strategy per passive
4. THE System SHALL enable correlation analysis between passive usage and win rates
5. THE System SHALL support filtering by strategy, card_name, or passive_type

### Requirement 10: Ensure Path Safety and Error Handling

**User Story:** As a system administrator, I want robust path handling and error management, so that the system works reliably across different environments.

#### Acceptance Criteria

1. THE System SHALL use relative paths for all file operations
2. THE System SHALL NOT use Turkish characters in file paths
3. WHEN output directory does not exist, THE System SHALL create it with parents=True
4. WHEN file write fails, THE System SHALL catch the exception and log a warning
5. THE System SHALL continue simulation execution even if logging fails

### Requirement 11: Standardize Value Calculation Across Passive Types

**User Story:** As a data scientist, I want normalized value metrics across different passive types, so that I can compare passive effectiveness regardless of their effect type.

#### Game Economy Analysis (From 5000-Game Simulation Data)

**Observed Metrics:**
- Average card cost: 3-4 gold (rarity-2 cards)
- Average card power: ~40 stat points
- **1 gold ≈ 10-13 stat points** (power/cost ratio)
- 1 kill = 10 combat points (KILL_PTS constant)
- Average damage per game: 140-180
- Average kills per game: 140-160
- **1 combat point ≈ 1 damage potential**

**Strategy Performance Correlation:**
- High delta strategies (7-8 delta/game): 18-20% win rate (tempo, warrior, balancer)
- Low delta strategies (2-4 delta/game): 1-5% win rate (random, builder, economist)
- **Strong correlation between passive delta and win rate**

**Value Conversion Rationale:**
- **Economy (1 gold = 10.0 value)**: Based on average card cost/power ratio (3-4 gold buys ~40 stats = 10 stat/gold)
- **Combat/Combo (1 point = 1.0 value)**: Direct combat point mapping, 1:1 damage potential
- **Copy/Synergy (1 stat = 1.0 value)**: Stat increases directly contribute to combat power
- **Survival (1 trigger = 15.0 value)**: Card resurrection ≈ average card cost (3-5 gold) × 10 = 30-50, using conservative 15.0

#### Acceptance Criteria

1. THE System SHALL define a value conversion table based on empirical game economy data
2. THE System SHALL convert gold gains to normalized value (1 gold = 10.0 value)
3. THE System SHALL convert combat points to normalized value (1 point = 1.0 value)
4. THE System SHALL convert combo points to normalized value (1 point = 1.0 value)
5. THE System SHALL convert stat increases (copy) to normalized value (1 stat = 1.0 value)
6. THE System SHALL convert field effects (synergy_field) to normalized value (1 stat = 1.0 value)
7. THE System SHALL convert survival effects to normalized value (per trigger = 15.0 value)
8. THE passive_efficiency_kpi.jsonl SHALL include both raw_value and normalized_value fields
9. THE efficiency_score SHALL be calculated using normalized_value
10. THE System SHALL document the conversion rationale with references to simulation data
