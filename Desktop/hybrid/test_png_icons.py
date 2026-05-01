"""
PNG İkon Test Scripti
======================
Science ikonunun ve diğer PNG ikonlarının doğru yüklenip yüklenmediğini test eder.
"""

import pygame
import sys
import os

# Proje kök dizinini path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from v2.ui import icon_loader

def test_icons():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("PNG İkon Testi")
    clock = pygame.time.Clock()
    
    # Test edilecek ikonlar
    test_data = [
        # (isim, x, y, is_category, renk)
        ("Science", 100, 100, True, None),
        ("Mythology & Gods", 250, 100, True, None),
        ("Art & Culture", 400, 100, True, None),
        ("Nature & Creatures", 100, 250, True, None),
        ("Cosmos", 250, 250, True, None),
        ("History & Civilizations", 400, 250, True, None),
        ("HEART", 100, 400, False, (255, 0, 0)),
        ("GOLD", 200, 400, False, (255, 215, 0)),
        ("SWORD", 300, 400, False, (200, 200, 200)),
        ("FIRE", 400, 400, False, (255, 100, 0)),
    ]
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Arka plan
        screen.fill((20, 25, 35))
        
        # Başlık
        font = pygame.font.SysFont("Arial", 24, bold=True)
        title = font.render("PNG İkon Testi", True, (255, 255, 255))
        screen.blit(title, (300, 20))
        
        # Alt başlık
        font_small = pygame.font.SysFont("Arial", 14)
        subtitle = font_small.render("ESC tuşuna basarak çıkabilirsiniz", True, (150, 150, 150))
        screen.blit(subtitle, (280, 50))
        
        # İkonları çiz
        for icon_name, x, y, is_cat, color in test_data:
            # İkon
            icon_loader.render_icon(
                surface=screen,
                icon_name=icon_name,
                size=48,
                pos=(x, y),
                is_category=is_cat,
                color_tint=color,
                shadow=True
            )
            
            # İkon adı
            label = font_small.render(icon_name[:20], True, (200, 200, 200))
            screen.blit(label, (x, y + 55))
            
            # Durum kontrolü
            icon_surf = icon_loader.get_icon(icon_name, 48, is_cat)
            if icon_surf:
                status = font_small.render("✓ OK", True, (0, 255, 0))
            else:
                status = font_small.render("✗ Eksik", True, (255, 0, 0))
            screen.blit(status, (x, y + 75))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    print("\n" + "="*50)
    print("İKON DURUM RAPORU")
    print("="*50)
    
    # Detaylı rapor
    for icon_name, _, _, is_cat, _ in test_data:
        icon_surf = icon_loader.get_icon(icon_name, 48, is_cat)
        status = "✓ Yüklendi" if icon_surf else "✗ Bulunamadı"
        icon_type = "Kategori" if is_cat else "Genel"
        print(f"{icon_type:10} | {icon_name:25} | {status}")
    
    print("="*50)
    print("\nEksik ikonlar için:")
    print("1. PNG dosyalarını v2/assets/icons/ klasörüne ekleyin")
    print("2. Dosya adlarının icon_loader.py'deki eşlemelerle uyumlu olduğundan emin olun")
    print("\nÖrnek:")
    print("  Science kategorisi için: v2/assets/icons/science.png")
    print("  HEART ikonu için: v2/assets/icons/heart.png")

if __name__ == "__main__":
    test_icons()
