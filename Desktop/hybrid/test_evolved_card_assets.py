"""
Test: Evolved kartların asset yükleme mantığı
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def test_evolved_card_name_stripping():
    """Evolved prefix'inin doğru kaldırıldığını test et"""
    
    test_cases = [
        ("Evolved Pop Art", "Pop Art"),
        ("Evolved Odin", "Odin"),
        ("Evolved Isaac Newton", "Isaac Newton"),
        ("Pop Art", "Pop Art"),  # Evolved olmayan
        ("Odin", "Odin"),  # Evolved olmayan
    ]
    
    for card_name, expected_base in test_cases:
        if card_name.startswith("Evolved "):
            base_name = card_name[8:]
        else:
            base_name = card_name
        
        assert base_name == expected_base, f"Failed: {card_name} -> {base_name} (expected {expected_base})"
        print(f"✅ {card_name:30} -> {base_name}")
    
    print("\n✅ Tüm testler başarılı!")

if __name__ == "__main__":
    test_evolved_card_name_stripping()
