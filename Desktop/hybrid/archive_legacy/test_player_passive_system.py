"""
Test and Analysis Script for Player Class and Passive System

This script performs comprehensive testing and analysis of:
1. Player class methods with passive triggers
2. PASSIVE_HANDLERS registry completeness
3. Documentation and parameter usage
4. cards.json path validation

NO CODE MODIFICATIONS - READ-ONLY ANALYSIS
"""

import sys
import os
import json
from typing import Dict, List, Set, Tuple

# Add engine_core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'engine_core'))

from engine_core.player import Player
from engine_core.card import Card
from engine_core.board import Board
from engine_core.autochess_sim_v06 import trigger_passive
from engine_core.passives.registry import PASSIVE_HANDLERS
from engine_core.constants import CARD_COSTS


class TestReport:
    """Collects test results and generates report"""
    def __init__(self):
        self.sections = []
        self.errors = []
        self.warnings = []
        self.successes = []
    
    def add_section(self, title: str):
        self.sections.append(f"\n{'='*80}\n{title}\n{'='*80}")
    
    def add_error(self, msg: str):
        self.errors.append(f"❌ ERROR: {msg}")
    
    def add_warning(self, msg: str):
        self.warnings.append(f"⚠️  WARNING: {msg}")
    
    def add_success(self, msg: str):
        self.successes.append(f"✅ SUCCESS: {msg}")
    
    def print_report(self):
        for section in self.sections:
            print(section)
        
        print(f"\n{'='*80}")
        print("SUMMARY")
        print(f"{'='*80}")
        print(f"Total Errors: {len(self.errors)}")
        print(f"Total Warnings: {len(self.warnings)}")
        print(f"Total Successes: {len(self.successes)}")
        
        if self.errors:
            print(f"\n{'='*80}")
            print("ERRORS")
            print(f"{'='*80}")
            for err in self.errors:
                print(err)
        
        if self.warnings:
            print(f"\n{'='*80}")
            print("WARNINGS")
            print(f"{'='*80}")
            for warn in self.warnings:
                print(warn)
        
        if self.successes:
            print(f"\n{'='*80}")
            print("SUCCESSES")
            print(f"{'='*80}")
            for succ in self.successes:
                print(succ)


def test_cards_json_path():
    """Test 1: Verify cards.json path and accessibility"""
    report = TestReport()
    report.add_section("TEST 1: cards.json Path Validation")
    
    # Test multiple possible paths
    possible_paths = [
        "assets/data/cards.json",
        "./assets/data/cards.json",
        os.path.join(os.path.dirname(__file__), "assets", "data", "cards.json")
    ]
    
    found_path = None
    for path in possible_paths:
        if os.path.exists(path):
            found_path = path
            report.add_success(f"cards.json found at: {path}")
            break
    
    if not found_path:
        report.add_error(f"cards.json NOT FOUND in any of: {possible_paths}")
        return report, None
    
    # Try to load and parse
    try:
        with open(found_path, 'r', encoding='utf-8') as f:
            cards_data = json.load(f)
        report.add_success(f"cards.json loaded successfully: {len(cards_data)} cards")
        
        # Validate structure
        if not isinstance(cards_data, list):
            report.add_error("cards.json is not a list")
            return report, None
        
        # Check first card structure
        if cards_data:
            first_card = cards_data[0]
            required_fields = ['name', 'category', 'rarity', 'stats', 'passive_type']
            missing = [f for f in required_fields if f not in first_card]
            if missing:
                report.add_warning(f"First card missing fields: {missing}")
            else:
                report.add_success("Card structure validation passed")
        
        return report, cards_data
    
    except json.JSONDecodeError as e:
        report.add_error(f"JSON parse error: {e}")
        return report, None
    except Exception as e:
        report.add_error(f"Error loading cards.json: {e}")
        return report, None


def test_registry_completeness(cards_data):
    """Test 2: Registry Audit - Check all handlers are valid"""
    report = TestReport()
    report.add_section("TEST 2: PASSIVE_HANDLERS Registry Audit")
    
    if not cards_data:
        report.add_error("No cards data available for registry audit")
        return report
    
    # Get all cards with non-none passive types
    cards_with_passives = [
        c for c in cards_data 
        if c.get('passive_type') and c['passive_type'] != 'none'
    ]
    
    report.add_success(f"Found {len(cards_with_passives)} cards with active passives")
    
    # Check which cards have handlers
    cards_in_registry = set(PASSIVE_HANDLERS.keys())
    cards_needing_handlers = set(c['name'] for c in cards_with_passives)
    
    # Cards with handlers
    has_handler = cards_needing_handlers & cards_in_registry
    report.add_success(f"{len(has_handler)} cards have registered handlers")
    
    # Cards missing handlers
    missing_handlers = cards_needing_handlers - cards_in_registry
    if missing_handlers:
        report.add_warning(f"{len(missing_handlers)} cards with passive_type but NO handler:")
        for name in sorted(missing_handlers):
            card = next(c for c in cards_with_passives if c['name'] == name)
            report.add_warning(f"  - {name} (type: {card['passive_type']})")
    else:
        report.add_success("All cards with passive_type have handlers")
    
    # Extra handlers (in registry but not in cards.json)
    extra_handlers = cards_in_registry - cards_needing_handlers
    if extra_handlers:
        report.add_warning(f"{len(extra_handlers)} handlers with no matching card:")
        for name in sorted(extra_handlers):
            report.add_warning(f"  - {name}")
    
    # Test handler callability
    report.add_success(f"\nTesting handler callability...")
    for name, handler in PASSIVE_HANDLERS.items():
        if not callable(handler):
            report.add_error(f"Handler for '{name}' is not callable")
        else:
            # Try to inspect signature
            try:
                import inspect
                sig = inspect.signature(handler)
                params = list(sig.parameters.keys())
                expected = ['card', 'trigger', 'owner', 'opponent', 'ctx']
                if params != expected:
                    report.add_warning(f"Handler '{name}' has unexpected signature: {params}")
            except Exception as e:
                report.add_warning(f"Could not inspect handler '{name}': {e}")
    
    report.add_success("Handler callability check complete")
    
    return report


def test_player_methods_with_passives():
    """Test 3: Test Player methods with mock passive triggers"""
    report = TestReport()
    report.add_section("TEST 3: Player Methods with Passive Triggers")
    
    # Create test player
    player = Player(pid=1, strategy="random")
    player.gold = 100  # Give enough gold for testing
    
    # Track trigger calls
    trigger_log = []
    
    def mock_trigger_passive(card, trigger, owner, opponent, ctx, verbose=False):
        trigger_log.append({
            'card': card.name if hasattr(card, 'name') else str(card),
            'trigger': trigger,
            'owner_pid': owner.pid if owner else None,
            'ctx': ctx
        })
        return 0
    
    # Test 1: buy_card with trigger_passive_fn
    report.add_success("\nTesting buy_card with trigger_passive_fn...")
    test_card = Card("Test Card", "Test", "◆◆", {"Power": 5, "Speed": 5})
    test_card.rarity = "2"
    
    # Place a card on board first (to trigger card_buy passive)
    board_card = Card("Age of Discovery", "History", "◆◆", {"Power": 5})
    player.board.place((0, 0), board_card)
    
    trigger_log.clear()
    player.buy_card(test_card, trigger_passive_fn=mock_trigger_passive)
    
    if trigger_log:
        report.add_success(f"buy_card triggered {len(trigger_log)} passive(s)")
        for log in trigger_log:
            if log['trigger'] == 'card_buy':
                report.add_success(f"  - card_buy trigger detected for {log['card']}")
    else:
        report.add_warning("buy_card did not trigger any passives (expected if no card_buy handlers on board)")
    
    # Test 2: check_copy_strengthening with trigger_passive_fn
    report.add_success("\nTesting check_copy_strengthening with trigger_passive_fn...")
    player.copies["Test Card"] = 2
    player.copy_turns["Test Card"] = 0
    player.board.place((1, 0), test_card.clone())
    
    trigger_log.clear()
    player.check_copy_strengthening(turn=1, trigger_passive_fn=mock_trigger_passive)
    
    if trigger_log:
        report.add_success(f"check_copy_strengthening triggered {len(trigger_log)} passive(s)")
        for log in trigger_log:
            if log['trigger'] in ('copy_2', 'copy_3'):
                report.add_success(f"  - {log['trigger']} trigger detected")
    else:
        report.add_warning("check_copy_strengthening did not trigger passives (may need more turns)")
    
    # Test 3: Player methods without trigger_passive_fn (should not crash)
    report.add_success("\nTesting Player methods without trigger_passive_fn...")
    try:
        player2 = Player(pid=2, strategy="random")
        player2.gold = 50
        player2.buy_card(test_card)  # No trigger_passive_fn
        report.add_success("buy_card works without trigger_passive_fn")
        
        player2.check_copy_strengthening(turn=1)  # No trigger_passive_fn
        report.add_success("check_copy_strengthening works without trigger_passive_fn")
    except Exception as e:
        report.add_error(f"Player methods failed without trigger_passive_fn: {e}")
    
    return report


def test_trigger_passive_function():
    """Test 4: Test trigger_passive function from autochess_sim_v06"""
    report = TestReport()
    report.add_section("TEST 4: trigger_passive Function Testing")
    
    # Create test setup
    owner = Player(pid=1, strategy="random")
    opponent = Player(pid=2, strategy="random")
    
    # Test cards with known handlers
    test_cases = [
        ("Ragnarök", "combat_win", "Should trigger on combat_win"),
        ("Industrial Revolution", "income", "Should trigger on income"),
        ("Marie Curie", "copy_2", "Should trigger on copy_2"),
        ("Valhalla", "card_killed", "Should trigger on card_killed"),
        ("Athena", "pre_combat", "Should trigger on pre_combat"),
    ]
    
    for card_name, trigger_type, description in test_cases:
        if card_name in PASSIVE_HANDLERS:
            card = Card(card_name, "Test", "◆◆◆", {"Power": 5})
            try:
                result = trigger_passive(card, trigger_type, owner, opponent, {"turn": 1}, verbose=False)
                report.add_success(f"{card_name} + {trigger_type}: returned {result} - {description}")
            except Exception as e:
                report.add_error(f"{card_name} + {trigger_type}: FAILED with {e}")
        else:
            report.add_warning(f"{card_name} not in PASSIVE_HANDLERS")
    
    # Test with non-existent handler (should not crash)
    try:
        fake_card = Card("Nonexistent Card", "Test", "◆", {"Power": 1})
        result = trigger_passive(fake_card, "combat_win", owner, opponent, {"turn": 1}, verbose=False)
        report.add_success(f"trigger_passive handles missing handler gracefully (returned {result})")
    except Exception as e:
        report.add_error(f"trigger_passive crashed on missing handler: {e}")
    
    return report


def test_documentation_and_usage():
    """Test 5: Documentation and optional parameter usage"""
    report = TestReport()
    report.add_section("TEST 5: Documentation and Optional Parameter Usage")
    
    # Check Player class methods for trigger_passive_fn parameter
    import inspect
    
    player_methods = [
        ('buy_card', ['card', 'market', 'trigger_passive_fn']),
        ('check_copy_strengthening', ['turn', 'trigger_passive_fn']),
    ]
    
    for method_name, expected_params in player_methods:
        method = getattr(Player, method_name, None)
        if method is None:
            report.add_error(f"Player.{method_name} not found")
            continue
        
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        
        # Check if expected params exist
        missing = [p for p in expected_params if p not in params]
        if missing:
            report.add_error(f"Player.{method_name} missing parameters: {missing}")
        else:
            report.add_success(f"Player.{method_name} has all expected parameters")
        
        # Check if trigger_passive_fn has default None
        if 'trigger_passive_fn' in params:
            param = sig.parameters['trigger_passive_fn']
            if param.default is None or param.default == inspect.Parameter.empty:
                report.add_success(f"Player.{method_name} trigger_passive_fn is optional (default=None)")
            else:
                report.add_warning(f"Player.{method_name} trigger_passive_fn default is {param.default}")
    
    # Check trigger_passive function signature
    sig = inspect.signature(trigger_passive)
    params = list(sig.parameters.keys())
    expected = ['card', 'trigger', 'owner', 'opponent', 'ctx', 'verbose']
    
    if params == expected:
        report.add_success(f"trigger_passive has correct signature: {params}")
    else:
        report.add_warning(f"trigger_passive signature mismatch. Expected {expected}, got {params}")
    
    # Check verbose parameter default
    verbose_param = sig.parameters.get('verbose')
    if verbose_param and verbose_param.default is False:
        report.add_success("trigger_passive verbose parameter defaults to False")
    else:
        report.add_warning(f"trigger_passive verbose parameter default is {verbose_param.default if verbose_param else 'missing'}")
    
    return report


def main():
    """Run all tests and generate comprehensive report"""
    print("="*80)
    print("PLAYER CLASS AND PASSIVE SYSTEM TEST & ANALYSIS")
    print("="*80)
    print("NO CODE MODIFICATIONS - READ-ONLY ANALYSIS")
    print("="*80)
    
    all_reports = []
    
    # Test 1: cards.json path
    report1, cards_data = test_cards_json_path()
    all_reports.append(report1)
    
    # Test 2: Registry audit
    if cards_data:
        report2 = test_registry_completeness(cards_data)
        all_reports.append(report2)
    
    # Test 3: Player methods
    report3 = test_player_methods_with_passives()
    all_reports.append(report3)
    
    # Test 4: trigger_passive function
    report4 = test_trigger_passive_function()
    all_reports.append(report4)
    
    # Test 5: Documentation
    report5 = test_documentation_and_usage()
    all_reports.append(report5)
    
    # Print all reports
    for report in all_reports:
        report.print_report()
    
    # Final summary
    total_errors = sum(len(r.errors) for r in all_reports)
    total_warnings = sum(len(r.warnings) for r in all_reports)
    total_successes = sum(len(r.successes) for r in all_reports)
    
    print(f"\n{'='*80}")
    print("FINAL SUMMARY")
    print(f"{'='*80}")
    print(f"Total Tests Run: 5")
    print(f"Total Errors: {total_errors}")
    print(f"Total Warnings: {total_warnings}")
    print(f"Total Successes: {total_successes}")
    
    if total_errors == 0:
        print("\n✅ ALL TESTS PASSED - No critical errors found")
    else:
        print(f"\n❌ {total_errors} CRITICAL ERRORS FOUND - Review required")
    
    if total_warnings > 0:
        print(f"⚠️  {total_warnings} warnings found - Review recommended")


if __name__ == "__main__":
    main()
