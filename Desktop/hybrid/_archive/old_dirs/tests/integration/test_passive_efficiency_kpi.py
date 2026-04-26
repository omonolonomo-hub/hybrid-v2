"""
Integration test for passive efficiency KPI logging.
Tests Task 7.1: _write_passive_efficiency_kpi() method.
"""

import json
import tempfile
from pathlib import Path

from engine_core.strategy_logger import StrategyLogger
from engine_core.kpi_aggregator import KPI_Aggregator


class MockPlayer:
    """Mock player for testing."""
    def __init__(self, strategy, pid=1, passive_buff_log=None):
        self.strategy = strategy
        self.pid = pid
        self.passive_buff_log = passive_buff_log or []


def test_write_passive_efficiency_kpi_basic():
    """Test that _write_passive_efficiency_kpi creates the file correctly."""
    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create KPI_Aggregator with test data
        aggregator = KPI_Aggregator()
        
        # Add test data directly to the aggregator
        aggregator._passive_game_data[(1, "economist", "Merchant", "economy")] = {
            "total_triggers": 2,
            "raw_value": 10.0,
            "normalized_value": 100.0,
            "game_won": True
        }
        
        # Create StrategyLogger with the test aggregator
        logger = StrategyLogger(enabled=True, output_dir=tmpdir)
        logger._kpi_aggregator = aggregator
        
        # Call the method
        logger._write_passive_efficiency_kpi()
        
        # Verify file was created
        output_file = Path(tmpdir) / "passive_efficiency_kpi.jsonl"
        assert output_file.exists(), "passive_efficiency_kpi.jsonl should be created"
        
        # Verify file content
        with open(output_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 1, "Should have exactly one record"
            
            record = json.loads(lines[0])
            assert record["game_id"] == 1
            assert record["strategy"] == "economist"
            assert record["card_name"] == "Merchant"
            assert record["passive_type"] == "economy"
            assert record["total_triggers"] == 2
            assert record["raw_value"] == 10.0
            assert record["normalized_value"] == 100.0
            assert record["efficiency_score"] == 50.0
            assert record["game_won"] is True
        
        print("✓ Test passed: _write_passive_efficiency_kpi creates file correctly")


def test_write_passive_efficiency_kpi_disabled():
    """Test that disabled logger doesn't write files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create disabled logger
        logger = StrategyLogger(enabled=False, output_dir=tmpdir)
        
        # Call the method
        logger._write_passive_efficiency_kpi()
        
        # Verify file was NOT created
        output_file = Path(tmpdir) / "passive_efficiency_kpi.jsonl"
        assert not output_file.exists(), "Disabled logger should not create files"
        
        print("✓ Test passed: Disabled logger doesn't write files")


def test_write_passive_efficiency_kpi_empty():
    """Test that empty aggregator creates empty file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create logger with empty aggregator
        logger = StrategyLogger(enabled=True, output_dir=tmpdir)
        
        # Call the method
        logger._write_passive_efficiency_kpi()
        
        # Verify file was created but is empty
        output_file = Path(tmpdir) / "passive_efficiency_kpi.jsonl"
        assert output_file.exists(), "File should be created even if empty"
        
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert content == "", "File should be empty"
        
        print("✓ Test passed: Empty aggregator creates empty file")


def test_write_passive_efficiency_kpi_multiple_records():
    """Test writing multiple KPI records."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create KPI_Aggregator with multiple records
        aggregator = KPI_Aggregator()
        
        aggregator._passive_game_data[(1, "economist", "Merchant", "economy")] = {
            "total_triggers": 2,
            "raw_value": 10.0,
            "normalized_value": 100.0,
            "game_won": True
        }
        
        aggregator._passive_game_data[(1, "warrior", "Berserker", "combat")] = {
            "total_triggers": 5,
            "raw_value": 25.0,
            "normalized_value": 25.0,
            "game_won": False
        }
        
        # Create StrategyLogger with the test aggregator
        logger = StrategyLogger(enabled=True, output_dir=tmpdir)
        logger._kpi_aggregator = aggregator
        
        # Call the method
        logger._write_passive_efficiency_kpi()
        
        # Verify file content
        output_file = Path(tmpdir) / "passive_efficiency_kpi.jsonl"
        with open(output_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 2, "Should have exactly two records"
            
            # Parse both records
            record1 = json.loads(lines[0])
            record2 = json.loads(lines[1])
            
            # Verify records are sorted (by key tuple)
            assert record1["strategy"] == "economist"
            assert record2["strategy"] == "warrior"
        
        print("✓ Test passed: Multiple records written correctly")


if __name__ == "__main__":
    test_write_passive_efficiency_kpi_basic()
    test_write_passive_efficiency_kpi_disabled()
    test_write_passive_efficiency_kpi_empty()
    test_write_passive_efficiency_kpi_multiple_records()
    print("\n✅ All tests passed!")
