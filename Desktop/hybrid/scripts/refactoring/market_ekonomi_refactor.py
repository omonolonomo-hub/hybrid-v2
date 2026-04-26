# Market & economy refactor notes
# For autochess_sim_v06.py — apply in Cursor in order

"""
==========================================================
MARKET SYSTEM — 4 issues
==========================================================

ISSUE 1: refresh() vs get_cards_for_player() conflict
---------------------------------------------------------
Previously:
  - refresh()              → filled global slots, decremented pool_copies
  - get_cards_for_player() → bypassed slots, pulled independently from pool
  Result: refresh() had no durable effect; slots unused.

Target architecture:
  Per-turn per-player market window from the shared pool.
  Each draw lowers pool_copies; unpurchased cards return at end of turn.

Tasks:
  - Remove refresh() or reduce to “turn start reset” only
  - deal_market_window(player, n=5) per player
  - Track each window; return unsold copies to pool_copies

---

ISSUE 2: Same card visible in multiple markets
---------------------------------------------------------
Previously:
  get_cards_for_player() sampled independently per player.
  No pool_copies enforcement.

Intended:
  Three physical copies per card; showing a copy “locks” it until return.

Tasks:
  - Atomic decrement in deal_market_window()
  - End-of-turn return path

---

ISSUE 3: Duplicate cards in market slots (~10%)
---------------------------------------------------------
Previously:
  refresh() used random.choices — selection with replacement.

Tasks:
  - random.choices → random.sample (no replacement)

---

ISSUE 4: Reroll missing
---------------------------------------------------------
Previously:
  MARKET_REFRESH_COST = 2 existed but players could not reroll.

Tasks:
  - Player.reroll_market(market):
      if self.gold >= MARKET_REFRESH_COST:
          self.gold -= MARKET_REFRESH_COST
          return market.deal_market_window(self)
  - AI: economist rerolls if gold is high and window is weak; evolver if no copies to build


==========================================================
ECONOMY SYSTEM — 5 issues
==========================================================

ISSUE 5: Interest applied before spending
---------------------------------------------------------
Previously:
  income() bundled income + interest, then purchases — double-dipping.

Target flow:
  1. income()  → base + streak + HP bonus only
  2. buy_card()
  3. apply_interest() on remaining gold

Sketch:
  def income(self):
      base = BASE_INCOME + (self.win_streak // 3) + hp_bonus
      self.gold += base
      ...

  def apply_interest(self):
      interest = min(MAX_INTEREST, self.gold // INTEREST_STEP)
      if self.strategy == "economist":
          interest = min(MAX_INTEREST + 3, int(interest * 1.5) + 1)
      self.gold += interest

  In Game.preparation_phase():
      player.income()
      AI.buy_cards(...)
      player.apply_interest()

---

ISSUE 6: Draw resets win_streak — GDD unclear
---------------------------------------------------------
Document both options; add DRAW_BREAKS_STREAK.

---

ISSUE 7: Economist bonus tied to strategy string
---------------------------------------------------------
Move to Player fields:
  interest_multiplier, interest_cap

---

ISSUE 8: No gold cap
---------------------------------------------------------
Add GOLD_CAP (e.g. 50); clamp after income and interest.

---

ISSUE 9: buy_card does not decrement pool (historical)
---------------------------------------------------------
Pass Market into buy_card and decrement pool_copies when appropriate.

==========================================================
SUGGESTED ORDER
==========================================================

1. ISSUE 3 — sample without replacement
2. ISSUE 5 — split income / interest
3. ISSUE 8 — GOLD_CAP
4. ISSUE 9 — market-aware buy (if required by design)
5. ISSUES 1+2 — deal_market_window architecture
6. ISSUE 7 — interest_multiplier on Player
7. ISSUE 4 — reroll
8. ISSUE 6 — DRAW_BREAKS_STREAK decision

After each step:
  python autochess_sim_v06.py --games 100 --players 8

==========================================================
"""
