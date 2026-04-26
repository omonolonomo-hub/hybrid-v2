# AUTOCHESS HYBRID — FINAL GAME DESIGN DOCUMENT
**Version:** Engine-Verified Final  
**Source:** engine_core/ (game.py, board.py, card.py, player.py, market.py, constants.py, passive_trigger.py, passives/*)  
**Format:** AI-agent-readable reference document  
**Date:** 2026-04-08

---

## TABLE OF CONTENTS
1. [Game Overview](#1-game-overview)
2. [Core Data Structures](#2-core-data-structures)
3. [Turn Structure — Full Decision Tree](#3-turn-structure--full-decision-tree)
4. [Board Mechanics](#4-board-mechanics)
5. [Hand, Board, Shop System](#5-hand-board-shop-system)
6. [Card Rotation Mechanic](#6-card-rotation-mechanic)
7. [Combo System](#7-combo-system)
8. [Synergy System (Group Synergy Bonus)](#8-synergy-system-group-synergy-bonus)
9. [Combat Resolution — Full Pipeline](#9-combat-resolution--full-pipeline)
10. [Damage Formula](#10-damage-formula)
11. [Passive System — Complete Taxonomy](#11-passive-system--complete-taxonomy)
12. [MIND, CONNECTION, EXISTENCE Groups](#12-mind-connection-existence-groups)
13. [Economy System](#13-economy-system)
14. [Evolution System](#14-evolution-system)
15. [Market System (Shop)](#15-market-system-shop)
16. [Player Lifecycle & Elimination](#16-player-lifecycle--elimination)
17. [Win Condition](#17-win-condition)
18. [AI Strategies (Reference)](#18-ai-strategies-reference)
19. [Constants Quick Reference](#19-constants-quick-reference)

---

## 1. GAME OVERVIEW

**Genre:** Auto-chess hex-grid card battler  
**Players:** N players (simulated via Swiss pairing)  
**Match Structure:** Rounds of alternating Preparation Phase → Combat Phase until one player remains  
**Starting HP:** 150  
**Game Loop Guard:** Max 50 turns  

Each player maintains:
- A hand (max 6 cards)
- A hex board (37 hexes, radius 3)
- Gold pool (no cap; unlimited economy)
- Copy/evolution tracker
- Passive buff log

---

## 2. CORE DATA STRUCTURES

### 2.1 Card

```
Card:
  name:         str               # unique card identifier
  category:     str               # e.g. "Science", "Mythology & Gods", "Cosmos", "History & Civilizations"
  rarity:       str               # "1" (common) .. "5" (legendary) | "E" (evolved)
  stats:        Dict[str, int]    # 6 named stats, one per hex edge
  passive_type: str               # "none" | "copy" | "combat_win" | ... (tag, not logic)
  edges:        List[(str, int)]  # ordered list of (stat_name, value) — SAME data as stats, edge-indexed
  rotation:     int               # 0-5 (steps of 60° clockwise)
  uid:          int               # globally unique runtime ID (for coord_index O(1) lookup)
```

**Critical invariant:** `card.edges[i]` = the stat facing hex direction `i` AFTER rotation is applied.  
Raw `card.edges` are base slots. To get the value facing physical direction `d`, call `card.rotated_edges()[d]`.

### 2.2 Board

```
Board:
  grid:         Dict[(q,r), Card]   # axial coord → Card
  coord_index:  Dict[card.uid, (q,r)]  # O(1) reverse lookup
  has_catalyst: bool
  has_eclipse:  bool
  square_card:  Optional[Card]      # Catalyst or Eclipse card slot
```

### 2.3 Player

```
Player:
  pid:           int
  strategy:      str
  hp:            int (starts 150)
  gold:          int (no cap)
  board:         Board
  hand:          List[Card]     # max 6, FIFO overflow
  copies:        Dict[str, int] # card_name → total owned copies (hand + board)
  copy_turns:    Dict[str, int] # card_name → turns waited since first copy
  win_streak:    int
  total_pts:     int
  alive:         bool
  stats:         Dict[str, int] # instrumentation counters
```

---

## 3. TURN STRUCTURE — FULL DECISION TREE

Every turn executes in strict order:

```
TURN N
│
├── PREPARATION PHASE (game.preparation_phase)
│   │
│   ├── [Step 1] Market Pre-Deal (all alive players simultaneously)
│   │     └─ For EVERY alive player: deal_market_window(player, 5)
│   │        → removes 5 cards from pool into player-specific window
│   │        → all windows dealt BEFORE any player acts (no first-player advantage)
│   │
│   ├── [Step 2] Per-Player Loop (sequential, order = alive list)
│   │   │
│   │   ├── [2a] Income
│   │   │     ├─ +BASE_INCOME (3 gold)
│   │   │     ├─ +1 per 3 consecutive wins (win_streak // 3)
│   │   │     ├─ +3 if HP < 45 (bailout)
│   │   │     ├─ +1 if HP < 75 (bailout)
│   │   │     └─ Trigger "income" passives on all board cards
│   │   │
│   │   ├── [2b] Market Refresh Trigger
│   │   │     └─ Trigger "market_refresh" passives on all board cards
│   │   │
│   │   ├── [2c] AI Buy Phase
│   │   │     ├─ AI.buy_cards(player, market_window)
│   │   │     ├─ Each purchased card: clone → append to hand → copy count +1
│   │   │     ├─ Trigger "card_buy" passives on all board cards for each purchase
│   │   │     ├─ Hand overflow (>6): FIFO drop oldest card → return to pool
│   │   │     └─ Unsold window cards returned to pool
│   │   │
│   │   ├── [2d] Interest Calculation
│   │   │     ├─ interest = min(5, gold // 10)
│   │   │     └─ Economist: interest = min(8, floor(interest * 1.5) + 1)
│   │   │
│   │   ├── [2e] Evolution Check (evolver strategy only)
│   │   │     └─ If copies[card_name] >= 3: trigger evolution (see Section 14)
│   │   │
│   │   ├── [2f] AI Place Cards
│   │   │     └─ Place up to PLACE_PER_TURN (1) cards from hand to board
│   │   │
│   │   └── [2g] Copy Strengthening Check
│   │         ├─ For each card with 2+ copies on board (with thresholds met):
│   │         │   ├─ 2nd copy milestone (turn 4, or turn 3 w/Catalyst): +2 to highest edge
│   │         │   └─ 3rd copy milestone (turn 7, or turn 6 w/Catalyst): +3 to highest edge
│   │         ├─ Trigger "copy_2" or "copy_3" passives
│   │         └─ Board snapshot: record board_power, unit_count, gold_per_turn stats
│
└── COMBAT PHASE (game.combat_phase)
    │
    ├── [Step 1] Swiss Pairing
    │     └─ Sort alive players by HP (with ±0.5 RNG jitter), pair nearest-HP opponents
    │
    └── [Step 2] Per-Pair Combat Loop
        │
        ├── [2a] Pre-Combat Passives
        │     └─ Trigger "pre_combat" on all board cards of BOTH players
        │        (synergy fields, debuffs, combo bonuses applied here)
        │
        ├── [2b] Combo Detection
        │     ├─ find_combos(board_a) → (combo_pts_a, combat_bonus_a)
        │     ├─ find_combos(board_b) → (combo_pts_b, combat_bonus_b)
        │     └─ If board.has_catalyst: combo_pts *= 2
        │
        ├── [2c] Group Synergy Bonus
        │     ├─ synergy_pts_a = calculate_group_synergy_bonus(board_a)
        │     └─ synergy_pts_b = calculate_group_synergy_bonus(board_b)
        │
        ├── [2d] Board Combat Resolution
        │     └─ combat_phase(board_a, board_b, bonus_a, bonus_b)
        │        → returns (kill_pts_a, kill_pts_b, draw_count)
        │        (see Section 9 for full pipeline)
        │
        ├── [2e] Score Aggregation
        │     ├─ pts_a = kill_pts_a + combo_pts_a + synergy_pts_a
        │     └─ pts_b = kill_pts_b + combo_pts_b + synergy_pts_b
        │
        ├── [2f] Damage & HP Update
        │     ├─ pts_a > pts_b → calculate_damage(pts_a, pts_b, board_a, turn) → p_b.take_damage()
        │     ├─ pts_b > pts_a → calculate_damage(pts_b, pts_a, board_b, turn) → p_a.take_damage()
        │     └─ Draw → both +1 gold, win_streak = 0 for both
        │
        ├── [2g] Win Streak Update
        │     ├─ Winner: win_streak += 1; record win_streak_max
        │     └─ Loser: win_streak = 0
        │
        └── [2h] Elimination Check
              └─ If player.hp <= 0: alive = False → return all cards to pool
```

---

## 4. BOARD MECHANICS

### 4.1 Hex Grid

- **Coordinate system:** Axial (q, r) with center (0, 0)
- **Radius:** 3 → **37 hexes** total
- **Valid hex formula:** `abs(q) + abs(r) + abs(q+r) <= 2 * radius` (equivalently `abs(q+r) <= radius` for range)
- **Directions (6):** N=(0,-1), NE=(1,-1), SE=(1,0), S=(0,1), SW=(-1,1), NW=(-1,0)
- **Opposite direction lookup:** `OPP_DIR = {0:3, 1:4, 2:5, 3:0, 4:1, 5:2}`

### 4.2 Positioning Notes

- Radius-3 board: 19 of 37 hexes have 6 neighbors (51.4%), so center is not uniquely dominant
- Cards placed via FIFO hand order (1 per turn default)
- Free hex selected by AI strategy (random/scored); board is open placement (no ownership zones)

### 4.3 Board State Flags

| Flag | Source | Effect |
|------|--------|--------|
| `has_catalyst` | Square card slot | Copy thresholds: turn 3/6 instead of 4/7; combo_pts doubled |
| `has_eclipse` | Square card slot | Currently tracked but mechanics TBD |

---

## 5. HAND, BOARD, SHOP SYSTEM

### 5.1 Hand

- **Max size:** 6 cards (`HAND_LIMIT`)
- **Overflow rule:** When 7th card is bought, `hand[0]` (oldest, FIFO) is dropped and returned to pool
- **Cards in hand:** Contribute to copy count tracking but do NOT participate in combat or trigger passives
- **Movement to board:** 1 card per turn (`PLACE_PER_TURN`) via AI placement decision

### 5.2 Board

- **Max occupancy:** 37 hexes (one card per hex)
- **Cards on board:** Actively combat, trigger passives, count toward synergy/combo
- **No explicit "bench" separate from hand** — hand IS the waiting area

### 5.3 Shop (Market Window)

- Each player gets a **5-card window** per turn
- Window is dealt **before** any player's income/buy phase (simultaneous dealing)
- Cards in a window are **removed from the pool** during the window's lifetime
- Unsold cards are **returned to pool** after buy phase
- Window composition is **rarity-weighted by turn** (see Section 15)
- **Refresh cost:** 2 gold (via `MARKET_REFRESH_COST`); triggers "market_refresh" passives

---

## 6. CARD ROTATION MECHANIC

### 6.1 Mechanics

Each card has **6 edges** (one per hex direction). Each edge = one named stat.  
**Rotation** (0–5, integer steps of 60°) determines which stat faces which physical direction.

```
rotation = 0:  edge[0]→dir0(N), edge[1]→dir1(NE), edge[2]→dir2(SE), ...
rotation = 1:  edge[0]→dir1(NE), edge[1]→dir2(SE), edge[2]→dir3(S), ...
rotation = r:  rotated_edges()[d] = edges[(d - r) % 6]
```

### 6.2 Impact on Combat

- `resolve_single_combat` reads `card.rotated_edges()` for each direction d (0–5)
- Two opposing cards compare: `va = rotated_edges_a[d]` vs `vb = rotated_edges_b[d]`
- If card A has a EXISTENCE stat facing direction 2 (SE) after rotation, and card B has a CONNECTION stat facing direction 2 → EXISTENCE beats CONNECTION → va += 1

### 6.3 Damage / Edge Loss

- `card.lose_highest_edge()`: finds the highest-value slot in `card.edges` (base list, not rotated), sets it to 0
- `card.apply_edge_debuff(d, amount)`: maps physical direction d back to base edge index via `(d - rotation) % 6`, reduces value
- `card.strengthen(copy_num)`: +2 or +3 to highest base edge (not direction-aware)

### 6.4 Elimination Condition

A card is eliminated when **at least one group has 2+ stats all reduced to 0**:
- Groups = EXISTENCE, MIND, CONNECTION (each has 4 stat names)
- Cards with only 1 stat per group are NOT eliminated by that group alone (prevents single-stat cards from insta-dying on first loss)

---

## 7. COMBO SYSTEM

### 7.1 Detection Algorithm (`find_combos`)

```
For each (coord, card) in board.grid:
  card_group = card.dominant_group()       # group with most active stats
  For each (neighbor_coord, direction) in board.neighbors(coord):
    pair = (min(coord, neighbor_coord), max(coord, neighbor_coord))
    if pair already counted: skip
    neighbor_group = neighbor_card.dominant_group()
    if card_group == neighbor_group:
      combo_points += 1
      combat_bonus[coord][direction] += 1
      combat_bonus[neighbor_coord][opposite_direction] += 1
    mark pair as counted
```

### 7.2 Output

- `combo_points`: Integer, +1 per matching neighbor pair
- `combat_bonus`: Dict of `{coord: {direction: +1}}` — applied as per-edge bonus during `resolve_single_combat`

### 7.3 Catalyst Modifier

If `board.has_catalyst == True`: `combo_pts *= 2` (after detection, before adding to score)

### 7.4 Dominant Group Calculation

```
card.dominant_group():
  Count stat names per group where stat value > 0
  Return group with highest count (tie-break: arbitrary; default "EXISTENCE" if empty)
```

### 7.5 Combo Effect on Score

Combo points are added to `pts_a` or `pts_b` AFTER card combat kill points and alongside synergy points:
```
pts = kill_pts + combo_pts + synergy_pts
```

---

## 8. SYNERGY SYSTEM (GROUP SYNERGY BONUS)

### 8.1 Calculation (`calculate_group_synergy_bonus`)

```
Step 1: Count cards per group
  group_count[group] = number of board cards where card.get_group_composition() includes that group

Step 2: Group bonus per group
  For each group with count n >= 2:
    bonus = min(18, floor(3 * (n-1)^1.25))

Step 3: Diversity bonus
  unique_groups = count of groups with at least 1 card
  diversity_bonus = min(5, unique_groups)

Total = sum(group_bonuses) + diversity_bonus
```

### 8.2 Scaling Table

| Cards in group | Group bonus |
|---------------|------------|
| 1             | 0 (no synergy) |
| 2             | 3 |
| 3             | 7 |
| 4             | 11 |
| 5             | 16 |
| 7             | 18 (capped) |
| 10+           | 18 (capped) |

**Diversity bonus:** +1 per unique group present, max +5

**Mono-group strategy:** 18 (group) + 1 (diversity) = 19 max  
**3-group diverse strategy:** ~13-16 (groups) + 3 (diversity) = 16-19 total

### 8.3 Impact on Match Score

`synergy_pts` adds directly to `pts_a`/`pts_b`. Note: a 30% power cap was designed (mentioned in code comments) but not enforced at runtime in the current engine.

---

## 9. COMBAT RESOLUTION — FULL PIPELINE

### 9.1 Phase: Pre-Combat Passives (before card duels)

All "pre_combat" passive handlers fire. These can:
- Buff friendly card stats (Odin, Isaac Newton, Nikola Tesla, Yggdrasil...)
- Debuff enemy card stats (Medusa, Black Hole, Black Death, French Revolution...)
- Award extra combat points (Athena, Ballet, Albert Einstein, Golden Ratio, Nebula...)
- Apply entropy effects (Entropy card)

### 9.2 Phase: Shared Coordinate Combat

```
shared_coords = set(board_a.grid.keys()) & set(board_b.grid.keys())
For each coord in shared_coords:
  card_a = board_a.grid[coord]
  card_b = board_b.grid[coord]
  ba = combo_bonus_a.get(coord, {})   # per-direction bonus from combos
  bb = combo_bonus_b.get(coord, {})

  (a_wins, b_wins) = resolve_single_combat(card_a, card_b, ba, bb)
```

### 9.3 `resolve_single_combat(card_a, card_b, bonus_a, bonus_b)`

```
For direction d in 0..5:
  va = rotated_edges_a[d].value  + bonus_a.get(d, 0) + (sum of _prefix stats // 6)
  vb = rotated_edges_b[d].value  + bonus_b.get(d, 0) + (sum of _prefix stats // 6)

  // Group advantage check (if both edges are active > 0):
  ga = group of stat at rotated_edges_a[d]
  gb = group of stat at rotated_edges_b[d]
  if GROUP_BEATS[ga] == gb: va += 1
  if GROUP_BEATS[gb] == ga: vb += 1

  if va > vb: a_wins += 1
  elif vb > va: b_wins += 1
  // else: edge draw, no points

return (a_wins, b_wins)
```

**Group Advantage Matrix:**
```
EXISTENCE beats CONNECTION (+1)
MIND      beats EXISTENCE (+1)
CONNECTION beats MIND     (+1)
```

### 9.4 Combat Outcome Processing

**Case: a_wins > b_wins**
1. Trigger "combat_win" passive on card_a → may return bonus kill_pts_a
2. Trigger "combat_lose" passive on card_b → may return bonus kill_pts_b (e.g., Guernica)
3. `card_b.lose_highest_edge()` (zeroes the highest edge)
4. If `card_b.is_eliminated()`:
   - Trigger "card_killed" passive on card_b
   - `board_b.remove(coord)`
   - `kill_pts_a += KILL_PTS` (= 8)

**Case: b_wins > a_wins** (symmetric, kill_pts_b += 8)

**Case: a_wins == b_wins** (draw at this coordinate): `draws += 1`, no HP change, no passive trigger

### 9.5 Passive Bonus Points

`trigger_passive()` returns an int. Combat win/lose/kill passives that return > 0 are added directly to that player's kill point pool for this combat round.

---

## 10. DAMAGE FORMULA

```
base   = abs(winner_pts - loser_pts)
alive  = winner_board.alive_count() // 2      # dampened board size contribution
rarity = winner_board.rarity_bonus() // 2     # (currently 0; RARITY_DMG_BONUS is empty dict)
raw    = max(1, base + alive + rarity)

// Turn-based multiplier (early game protection):
turn <= 5:         multiplier = 0.5
turn 6-15:         multiplier = 0.5 + (turn - 5) * 0.05    # linear 0.5 → 1.0
turn >= 16:        multiplier = 1.0

final = max(1, floor(raw * multiplier))

// Hard cap for turns 1-10:
if turn <= 10: final = min(final, 15)
```

**Draw result:** No damage; both players +1 gold, win_streak reset to 0.

---

## 11. PASSIVE SYSTEM — COMPLETE TAXONOMY

### 11.1 Architecture

```
PASSIVE_HANDLERS: Dict[card_name → handler_fn]
  Populated at import time via @passive("Card Name") decorator
  Registered per-card-name (not per passive_type)

trigger_passive(card, trigger, owner, opponent, ctx):
  1. Look up PASSIVE_HANDLERS[card.name]
  2. If found: call handler(card, trigger, owner, opponent, ctx) → int
  3. Else: default behavior for card.passive_type (copy type: +1 to highest edge)
  4. Log delta to owner.passive_buff_log if card power changed
  5. Return int (bonus combat points, or 0 for side-effect-only)
```

### 11.2 Trigger Events

| Trigger | When | Called On |
|---------|------|-----------|
| `income` | Start of turn, after income gold added | All board cards of that player |
| `market_refresh` | After market window is dealt | All board cards |
| `card_buy` | After each card purchase | All board cards (ctx contains bought_card) |
| `pre_combat` | Before card duels in combat phase | All board cards of BOTH players |
| `combat_win` | Card wins its hex duel (a_wins > b_wins) | The winning card |
| `combat_lose` | Card loses its hex duel | The losing card |
| `card_killed` | Card's is_eliminated() returns True | The killed card (before removal) |
| `copy_2` | 2nd copy threshold met | The card that was strengthened |
| `copy_3` | 3rd copy threshold met | The card that was strengthened |

### 11.3 Passive Handler Categories

#### COMBAT WIN Passives
| Card | Effect |
|------|--------|
| Ragnarök | Enemy's strongest card loses its highest edge |
| World War II | ALL enemy cards lose their highest edge |
| Loki | Strongest enemy loses 1 Meaning |
| Cubism | Strongest enemy loses 1 Size |
| Komodo Dragon | Strongest enemy loses 2 from its LOWEST edge |
| Venus Flytrap | Strongest enemy loses 1 Gravity (max 2× per game) |
| Narwhal | Self gains +1 Power (max 3 stacks) |
| Sirius | Self gains +1 Speed (max 2 stacks) |
| Pulsar | Award +2 combat points (once per turn) |
| Cerberus | Every 3rd win → +3 combat points |
| Fibonacci Sequence | +min(3, streak+1) combat points per win |

#### COMBAT LOSE Passives
| Card | Effect |
|------|--------|
| Guernica | +1 combat point when losing (max 3× per turn) |
| Minotaur | Self gains +1 Power on loss (max 2× per turn, max +4 total) |
| Code of Hammurabi | First non-zero edge +2 (max +4 total) |
| Frida Kahlo | Set first zero edge to 1 |

#### CARD KILLED Passives
| Card | Effect |
|------|--------|
| Anubis | +1 Secret on self (max 2 stacks) |
| Valhalla | Owner +3 gold (once per game) |
| Phoenix | Revive with all stats = 1 (once per combat) |
| Axolotl | Revive with all stats = 2 (once per combat) |
| Gothic Architecture | All neighbors +1 Durability |
| Baobab | All neighbors +2 Durability |

#### ECONOMY Passives (trigger: income / market_refresh / card_buy)
| Card | Trigger | Effect |
|------|---------|--------|
| Industrial Revolution | income | +1 gold |
| Ottoman Empire | income | +1 gold |
| Babylon | income | +1 gold |
| Printing Press | income | +1 gold |
| Midas | income | +1 gold if win_streak >= 2 |
| Silk Road | income | +1 gold if bought 2+ cards last turn |
| Exoplanet | income | +1 gold if market had rarity 4 or 5 card |
| Moon Landing | income | +1 gold on even turns |
| Algorithm | market_refresh | +1 gold |
| Age of Discovery | card_buy | +2 gold when buying first card of a new category |

#### SYNERGY FIELD Passives (trigger: pre_combat → return 1 pt + effect)
| Card | Effect |
|------|--------|
| Odin | Neighboring "Mythology & Gods" cards +1 Meaning (≤6 stacks) |
| Olympus | If 2+ neighboring Mythology & Gods → all their Prestige +1 |
| Isaac Newton | If 3+ Science cards on board → all their Intelligence +1 (≤6 stacks) |
| Nikola Tesla | Neighboring Science cards +1 Intelligence (≤6 stacks) |
| Medusa | ALL enemy cards -1 Speed |
| Black Hole | Enemy center card (0,0) -1 Gravity |
| Entropy | Every 3rd turn → all neighbors lose highest edge |
| Gravity | All neighbors -1 Speed |
| Black Death | ALL enemy cards -1 Spread |
| French Revolution | If 3+ History & Civilizations cards → enemy highest stat -1 |

#### COMBO Passives (trigger: pre_combat, use ctx combo data)
| Card | Effect |
|------|--------|
| Athena | 1 + combo_count if combo_group == MIND |
| Ballet | 1 + combo_count if combo_group == CONNECTION |
| Albert Einstein | 1 + 2 if combo_group == MIND |
| Impressionism | 1 + 1 if combo_count >= 2 |
| Nebula | 1 + 2 if combo_target_category == "Cosmos" |
| Golden Ratio | 1 + 3 if surrounded by 6+ neighbors |

#### COPY / EVOLUTION Passives (trigger: copy_2 / copy_3)
| Card | Effect |
|------|--------|
| Coelacanth | +2 to highest edge |
| Marie Curie | +2 gold to owner |
| Space-Time | All friendly board cards +1 to ALL edges (max 5 applications/game) |
| Fungus | First neighbor's highest edge +1 |
| Yggdrasil | (pre_combat) All neighbors gain stacking _yggdrasil_bonus counter |

---

## 12. MIND, CONNECTION, EXISTENCE GROUPS

### 12.1 Group Definitions

```python
STAT_GROUPS = {
    "EXISTENCE":  ["Power", "Durability", "Size", "Speed"],
    "MIND":       ["Meaning", "Secret", "Intelligence", "Trace"],
    "CONNECTION": ["Gravity", "Harmony", "Spread", "Prestige"],
}
```

Each card has exactly 6 stats drawn from these 12 possible stat names.  
(Not all 12 are necessarily present on a card; each card has exactly 6 named slots.)

### 12.2 Group Advantage (Rock-Paper-Scissors)

```
MIND beats EXISTENCE      (adds +1 to MIND edge value in head-to-head)
EXISTENCE beats CONNECTION (adds +1 to EXISTENCE edge value)
CONNECTION beats MIND      (adds +1 to CONNECTION edge value)
```

Applied per-edge during `resolve_single_combat`: if both edges are active (value > 0), the winning group's edge gets +1.

### 12.3 Mechanical Roles of Groups

**EXISTENCE stats (Power, Durability, Size, Speed):**
- Physical combat anchors — high raw values
- Speed also targeted by debuff passives (Medusa, Gravity)
- Size targeted by Cubism

**MIND stats (Meaning, Secret, Intelligence, Trace):**
- Synergy-heavy group — many passive buffs target Intelligence and Meaning
- Beats EXISTENCE, loses to CONNECTION
- Secret targeted by Anubis (grows on kill)

**CONNECTION stats (Gravity, Harmony, Spread, Prestige):**
- Economy/synergy integration group
- Gravity: targeted by Black Hole (center debuff), Venus Flytrap
- Spread: targeted by Black Death
- Prestige: buffed by Olympus

### 12.4 Dominant Group and Combo Matching

`card.dominant_group()` = group with the most active (value > 0) stats.  
Used for combo detection: two neighboring cards with the same dominant group trigger a combo.

### 12.5 Synergy Bonus Counting

`card.get_group_composition()` returns `{group: count_of_active_stats}`.  
Synergy calculation counts how many cards contribute to each group (any card contributing at least 1 active stat of that group counts as +1 for that group).

---

## 13. ECONOMY SYSTEM

### 13.1 Gold Sources Per Turn

| Source | Amount | Condition |
|--------|--------|-----------|
| Base income | +3 | Always |
| Win streak bonus | +floor(streak/3) | Per 3 consecutive wins |
| HP bailout tier 1 | +1 | HP < 75 |
| HP bailout tier 2 | +3 | HP < 45 |
| Interest | +1 per 10 gold banked, max +5 | Applied AFTER purchases |
| Economist interest | +floor(base_interest * 1.5) + 1, max +8 | Only economist strategy |
| Draw bonus | +1 | Combat draw result |
| Passive income | varies | Economy passives (see 11.3) |

### 13.2 Gold Costs

| Item | Cost |
|------|------|
| Rarity 1 card | 1 gold |
| Rarity 2 card | 2 gold |
| Rarity 3 card | 3 gold |
| Rarity 4 card | 5 gold |
| Rarity 5 card | 7 gold |
| Evolved card | 0 gold (earned via evolution) |
| Market refresh | 2 gold |

### 13.3 Interest Calculation Timing

Interest is calculated and applied **AFTER** card purchases in the preparation phase.  
This incentivizes saving gold (don't spend everything — keep 10, 20, 30, 40, 50+ for max interest tiers).

### 13.4 Economy Efficiency by Rarity

| Rarity | Cost | Avg Power | Power/Gold |
|--------|------|-----------|-----------|
| 1 | 1 | 29 | 29.0× |
| 2 | 2 | 32.7 | 16.4× |
| 3 | 3 | 38 | 12.7× |
| 4 | 5 | 44.3 | 8.9× |
| 5 | 7 | 49.3 | 7.1× |

---

## 14. EVOLUTION SYSTEM

### 14.1 Trigger Condition

- **Only evolver strategy** triggers evolution
- Requires `copies[card_name] >= EVOLVE_COPIES_REQUIRED` (= 3)
- Cannot evolve a card that already has an evolved version (`Evolved {name}` count > 0)
- Requires card template in `card_by_name` dict

### 14.2 Evolution Process

```
1. Remove 2 base copies (from hand first, then board if needed)
   → Return each consumed copy to market pool
2. copies[base_name] -= 2
3. Create evolved card:
   new_stats = scale all base stats proportionally to rarity-based target
   Rarity 1 → target 40 pts
   Rarity 2 → target 48 pts
   Rarity 3 → target 56 pts
   Rarity 4 → target 64 pts
   Rarity 5 → target 72 pts
4. Rarity-bonus scale (R3/R4/R5 only):
   R3: +12% power  |  R4: +16%  |  R5: +20%
5. Replace board copy (or hand copy) with evolved card
6. copies["Evolved {name}"] = 1
7. stats["evolutions"] += 1
8. Log evolution_turns
```

### 14.3 Copy Strengthening (all strategies)

Separate from evolution. When **any player** accumulates copies and leaves them on board:
- After `copy_turns >= COPY_THRESH[0]` (turn 4, or turn 3 with Catalyst): `strengthen(2)` → +2 to highest edge
- After `copy_turns >= COPY_THRESH[1]` (turn 7, or turn 6 with Catalyst): `strengthen(3)` → +3 to highest edge
- Copy thresholds fire only once each (tracked via `copy_applied` dict)
- Triggers copy_2 / copy_3 passive handlers

---

## 15. MARKET SYSTEM (SHOP)

### 15.1 Pool Structure

- Each card in the pool starts with **3 copies** (`pool_copies[card_name] = 3`)
- Pool is **shared** across all players
- Cards are removed from pool when dealt to a window, returned when unsold or player eliminated

### 15.2 Rarity Availability by Turn (Weighted Sampling)

| Rarity | Turn 1 | Turn 5 | Turn 8 | Turn 9 | Turn 10 | Turn 13 | Turn 14 | Turn 18 |
|--------|--------|--------|--------|--------|---------|---------|---------|---------|
| 1 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| 2 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| 3 | 0.3 | 0.7 | 0.7 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| 4 | 0.0 | 0.2 | 0.2 | 0.2 | 0.6 | 0.6 | 1.0 | 1.0 |
| 5 | 0.0 | 0.0 | 0.1 | 0.1 | 0.1 | 0.5 | 0.5 | 1.0 |
| E | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |

Weight = 0.0 means card of that rarity will never appear in market that turn.

### 15.3 Window Dealing

```
deal_market_window(player, n=5):
  1. Return any previous open window to pool
  2. Get (cards, weights) for current turn
  3. Weighted sample without replacement → n cards
  4. Remove sampled cards from pool_copies
  5. Store window in _player_windows[pid]
  6. Log to strategy_logger
  7. Return window list
```

### 15.4 Starting Hand

At game start, each player receives **3 random rarity-1 cards** from the pool (cloned, copy tracked).

---

## 16. PLAYER LIFECYCLE & ELIMINATION

### 16.1 HP Thresholds

- **Start:** 150 HP
- **Damage floor:** take_damage ensures HP >= 0
- **Elimination:** HP == 0 → `alive = False`
- **Bailout income:** Auto-activates at HP < 75 (+1 gold) and HP < 45 (+3 gold)

### 16.2 Elimination Consequences

When a player is eliminated (`_return_cards_to_pool`):
1. All board cards returned to pool (pool_copies += 1 per card, max 3)
2. All hand cards returned to pool
3. Evolved cards return 1 copy of their base name (conservative)
4. `board.grid.clear()`, `hand.clear()`, `copies.clear()`, `copy_turns.clear()`
5. `board.has_catalyst = False`

**Effect on pool economics:** Dead player's cards re-enter pool, making quality cards available again to survivors.

---

## 17. WIN CONDITION

```
game.run():
  While len(alive_players) > 1 AND turn < 50:
    preparation_phase()
    combat_phase()
    // Builder synergy_matrix.decay() for all alive players

Winner = alive player with highest HP
  (if 0 alive players: max HP across all players including eliminated)
```

---

## 18. AI STRATEGIES (REFERENCE)

| Strategy | Core Behavior | Key Parameters |
|----------|--------------|----------------|
| random | Random buys, random placement | — |
| warrior | Maximizes raw card power | power_weight, rarity_weight |
| builder | Maximizes combo/synergy score on board; uses BuilderSynergyMatrix (session adjacency memory) | combo_weight=0.5, power_weight=0.4 |
| evolver | Aggressively collects 3 copies for evolution; prioritizes base cards | evo_near_bonus=1000, evo_one_bonus=500 |
| economist | Greed phase (save gold) → spike phase (buy r4/r5) → convert phase (hold power) | greed_turn_end, spike_turn_end, thresholds |
| balancer | Maintains balance across MIND/CONNECTION/EXISTENCE groups | group_bonus=5, group_thresh=3 |
| rare_hunter | Seeks rarity 4+ cards; fallback to rarity 3 | fallback_rarity=3 |
| tempo | Places highest-power card at center hex (0,0) first | power_center_thresh=45, combo_center_weight=1.5 |

---

## 19. CONSTANTS QUICK REFERENCE

```python
# Board
BOARD_RADIUS     = 3          # 37 hexes
STARTING_HP      = 150
KILL_PTS         = 8          # pts per card eliminated

# Economy
BASE_INCOME      = 3
MAX_INTEREST     = 5          # max interest gold (standard)
INTEREST_STEP    = 10         # +1 per 10 gold banked
MARKET_REFRESH_COST = 2
HAND_LIMIT       = 6          # 7th card triggers FIFO drop
PLACE_PER_TURN   = 1          # cards moved to board per turn

# Copy/Evolution
COPY_THRESH      = [4, 7]     # standard copy milestone turns
COPY_THRESH_C    = [3, 6]     # with Catalyst active
EVOLVE_COPIES_REQUIRED = 3

# Card Costs
CARD_COSTS = {"1":1, "2":2, "3":3, "4":5, "5":7, "E":0}

# Power Targets
RARITY_TAVAN   = {"1":30, "2":36, "3":42, "4":48, "5":54, "E":72}
EVOLVED_TAVAN  = {"1":40, "2":48, "3":56, "4":64, "5":72, "E":72}

# Groups
STAT_GROUPS = {
    "EXISTENCE":  ["Power", "Durability", "Size", "Speed"],
    "MIND":       ["Meaning", "Secret", "Intelligence", "Trace"],
    "CONNECTION": ["Gravity", "Harmony", "Spread", "Prestige"],
}
GROUP_BEATS = {
    "EXISTENCE": "CONNECTION",
    "MIND":      "EXISTENCE",
    "CONNECTION": "MIND",
}

# Hex Directions (axial)
HEX_DIRS = [(0,-1), (1,-1), (1,0), (0,1), (-1,1), (-1,0)]
# N=0, NE=1, SE=2, S=3, SW=4, NW=5
OPP_DIR  = {0:3, 1:4, 2:5, 3:0, 4:1, 5:2}
```

---

## APPENDIX A: SCORE COMPOSITION SUMMARY

Every combat match between two players produces scores via:

```
pts_player = kill_pts + combo_pts + synergy_pts

Where:
  kill_pts   = sum of KILL_PTS (8) per enemy card eliminated
             + bonus pts from "combat_win" passive returns
             + bonus pts from "combat_lose" passive returns (e.g. Guernica)
             + bonus pts from "pre_combat" combo/synergy passives

  combo_pts  = find_combos(board).combo_points
             * 2 if has_catalyst

  synergy_pts = calculate_group_synergy_bonus(board)
              = group_bonus + diversity_bonus
```

Higher `pts` → wins the round → opponent takes damage.

---

## APPENDIX B: PASSIVE TRIGGER ORDER IN A SINGLE TURN

```
income passives            [preparation, per board card]
market_refresh passives    [preparation, per board card]
card_buy passives          [preparation, per board card, per purchase]
  → copy_2 / copy_3        [preparation, after all buys]
pre_combat passives        [combat, BEFORE any card duels — both players]
combat_win passives        [combat, per winning card in each hex duel]
combat_lose passives       [combat, per losing card in each hex duel]
card_killed passives       [combat, per eliminated card]
```

---

*This document was generated directly from engine_core/ source code.*  
*All mechanics described are implementation-verified, not design-intent speculation.*
