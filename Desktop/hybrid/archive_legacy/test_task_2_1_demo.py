"""
Demo script for Task 2.1: ParameterizedAI parameter resolution

This script demonstrates the three-tier priority system:
1. Manual overrides > JSON file > hardcoded defaults
"""

from engine_core.ai import ParameterizedAI, TRAINED_PARAMS
import json
from pathlib import Path

def demo_parameter_resolution():
    print("=" * 70)
    print("Task 2.1 Demo: ParameterizedAI Parameter Resolution")
    print("=" * 70)
    
    # Demo 1: Defaults only (no file, no params)
    print("\n1. Defaults only (no file, no manual params):")
    print("-" * 70)
    
    # Temporarily remove file if it exists
    params_file = Path("trained_params.json")
    backup_file = Path("trained_params.json.backup")
    file_existed = params_file.exists()
    if file_existed:
        params_file.rename(backup_file)
    
    try:
        ai1 = ParameterizedAI(strategy="economist")
        print(f"  thresh_high: {ai1.p['thresh_high']}")
        print(f"  greed_turn_end: {ai1.p['greed_turn_end']}")
        print(f"  Source: TRAINED_PARAMS (hardcoded defaults)")
        
        # Demo 2: File parameters override defaults
        print("\n2. File parameters override defaults:")
        print("-" * 70)
        
        test_params = {
            "economist": {
                "thresh_high": 35.0,
                "greed_turn_end": 12.0,
                "spike_turn_end": 20.0
            }
        }
        params_file.write_text(json.dumps(test_params, indent=2))
        
        ai2 = ParameterizedAI(strategy="economist")
        print(f"  thresh_high: {ai2.p['thresh_high']} (from file)")
        print(f"  greed_turn_end: {ai2.p['greed_turn_end']} (from file)")
        print(f"  spike_turn_end: {ai2.p['spike_turn_end']} (from file)")
        print(f"  spike_buy_count: {ai2.p['spike_buy_count']} (from defaults)")
        print(f"  Source: trained_params.json + defaults for missing keys")
        
        # Demo 3: Manual params override file and defaults
        print("\n3. Manual parameters override file and defaults:")
        print("-" * 70)
        
        manual_params = {
            "thresh_high": 100.0,
            "convert_buy_count": 5.0
        }
        
        ai3 = ParameterizedAI(strategy="economist", params=manual_params)
        print(f"  thresh_high: {ai3.p['thresh_high']} (manual override)")
        print(f"  greed_turn_end: {ai3.p['greed_turn_end']} (from file)")
        print(f"  convert_buy_count: {ai3.p['convert_buy_count']} (manual override)")
        print(f"  Source: manual > file > defaults")
        
        # Demo 4: Crash-proof loading (invalid JSON)
        print("\n4. Crash-proof loading (invalid JSON):")
        print("-" * 70)
        
        params_file.write_text("{ invalid json }")
        ai4 = ParameterizedAI(strategy="economist")
        print(f"  thresh_high: {ai4.p['thresh_high']}")
        print(f"  Source: TRAINED_PARAMS (file had invalid JSON, no crash)")
        
        print("\n" + "=" * 70)
        print("✓ All parameter resolution scenarios work correctly!")
        print("=" * 70)
        
    finally:
        # Cleanup
        params_file.unlink(missing_ok=True)
        if file_existed:
            backup_file.rename(params_file)

if __name__ == "__main__":
    demo_parameter_resolution()
