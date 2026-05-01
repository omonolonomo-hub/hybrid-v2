"""
Hızlı İkon Testi
================
Sadece science ikonunun yüklenip yüklenmediğini kontrol eder.
"""

import os
import sys

# Proje kök dizinini path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_icon_files():
    """İkon dosyalarının varlığını kontrol et."""
    icon_dir = "v2/assets/icons"
    
    print("\n" + "="*60)
    print("PNG İKON KONTROL")
    print("="*60)
    
    # Kontrol edilecek dosyalar
    icons = {
        # Kategori İkonları
        "science.png": "Science kategorisi",
        "mythology.png": "Mythology & Gods kategorisi",
        "art.png": "Art & Culture kategorisi",
        "nature.png": "Nature & Creatures kategorisi",
        "cosmos.png": "Cosmos kategorisi",
        "history.png": "History & Civilizations kategorisi",
        # Stat İkonları
        "stat_power.png": "Power stat",
        "stat_durability.png": "Durability stat",
        "stat_size.png": "Size stat",
        "stat_speed.png": "Speed stat",
        "stat_meaning.png": "Meaning stat",
        "stat_secret.png": "Secret stat",
        "stat_intelligence.png": "Intelligence stat",
        "stat_trace.png": "Trace stat",
        "stat_gravity.png": "Gravity stat",
        "stat_harmony.png": "Harmony stat",
        "stat_spread.png": "Spread stat",
        "stat_prestige.png": "Prestige stat",
    }
    
    found = []
    missing = []
    
    for filename, description in icons.items():
        filepath = os.path.join(icon_dir, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            found.append((filename, description, size))
            status = "✓"
            color = "\033[92m"  # Yeşil
        else:
            missing.append((filename, description))
            status = "✗"
            color = "\033[91m"  # Kırmızı
        
        reset = "\033[0m"
        print(f"{color}{status}{reset} {filename:20} - {description}")
    
    print("="*60)
    print(f"\nBulunan: {len(found)}/{len(icons)}")
    
    if found:
        print("\n✅ MEVCUT İKONLAR:")
        for filename, desc, size in found:
            print(f"   • {filename} ({size:,} bytes)")
    
    if missing:
        print("\n❌ EKSİK İKONLAR:")
        for filename, desc in missing:
            print(f"   • {filename} - {desc}")
        print("\n💡 Bu ikonları eklemek için:")
        print(f"   1. PNG dosyalarını hazırlayın (science.png gibi)")
        print(f"   2. {icon_dir}/ klasörüne kopyalayın")
        print(f"   3. Bu scripti tekrar çalıştırın")
    
    print("\n" + "="*60)
    
    # Pygame ile yükleme testi
    if found:
        print("\n🔍 PYGAME YÜKLEME TESTİ...")
        try:
            import pygame
            pygame.init()
            
            for filename, desc, size in found:
                filepath = os.path.join(icon_dir, filename)
                try:
                    img = pygame.image.load(filepath)
                    w, h = img.get_size()
                    print(f"   ✓ {filename}: {w}x{h} piksel")
                except Exception as e:
                    print(f"   ✗ {filename}: HATA - {e}")
            
            pygame.quit()
        except ImportError:
            print("   ⚠ Pygame yüklü değil, yükleme testi atlandı")
    
    print("="*60 + "\n")
    
    return len(found), len(missing)

if __name__ == "__main__":
    found_count, missing_count = check_icon_files()
    
    if missing_count == 0:
        print("🎉 Tüm ikonlar hazır! Oyunu başlatabilirsiniz.")
        sys.exit(0)
    else:
        print(f"⚠ {missing_count} ikon eksik. Oyun çalışır ama eski ikonları gösterir.")
        sys.exit(1)
