"""
Stat İkonları Görsel Test
==========================
Tüm 12 stat ikonunu ekranda gösterir.
"""

import pygame
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from v2.ui import icon_loader

# Stat isimleri ve ikon anahtarları
STATS = [
    ("Power", "FIST", (255, 80, 80)),
    ("Durability", "SHIELD", (255, 80, 80)),
    ("Size", "EXPAND", (255, 80, 80)),
    ("Speed", "BOLT", (255, 80, 80)),
    ("Meaning", "BOOK", (120, 200, 255)),
    ("Secret", "LOCK", (120, 200, 255)),
    ("Intelligence", "GEAR", (120, 200, 255)),
    ("Trace", "FOOTPRINT", (120, 200, 255)),
    ("Gravity", "MAGNET", (60, 200, 100)),
    ("Harmony", "MUSIC", (60, 200, 100)),
    ("Spread", "BROADCAST", (60, 200, 100)),
    ("Prestige", "GEM", (60, 200, 100)),
]

def main():
    pygame.init()
    screen = pygame.display.set_mode((1000, 700))
    pygame.display.set_caption("Stat İkonları Test")
    clock = pygame.time.Clock()
    
    font_title = pygame.font.SysFont("Arial", 28, bold=True)
    font_label = pygame.font.SysFont("Arial", 16)
    font_small = pygame.font.SysFont("Arial", 12)
    
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
        title = font_title.render("12 Stat İkonu Test", True, (255, 255, 255))
        screen.blit(title, (350, 20))
        
        subtitle = font_small.render("ESC tuşuna basarak çıkabilirsiniz", True, (150, 150, 150))
        screen.blit(subtitle, (380, 55))
        
        # Grup başlıkları
        y_offset = 100
        
        # EXISTENCE Grubu
        group_title = font_label.render("EXISTENCE (Kırmızı)", True, (255, 80, 80))
        screen.blit(group_title, (50, y_offset))
        
        for i in range(4):
            stat_name, icon_key, color = STATS[i]
            x = 50 + (i * 220)
            y = y_offset + 40
            
            # İkon
            icon_surf = icon_loader.get_icon(icon_key, 64, is_category=False)
            if icon_surf:
                screen.blit(icon_surf, (x, y))
                status = "✓"
                status_color = (0, 255, 0)
            else:
                # Fallback göster
                fallback = font_title.render("?", True, (150, 150, 150))
                screen.blit(fallback, (x + 20, y + 10))
                status = "✗"
                status_color = (255, 0, 0)
            
            # Stat adı
            label = font_label.render(stat_name, True, color)
            screen.blit(label, (x, y + 70))
            
            # İkon anahtarı
            key_label = font_small.render(f"({icon_key})", True, (150, 150, 150))
            screen.blit(key_label, (x, y + 92))
            
            # Durum
            status_label = font_small.render(status, True, status_color)
            screen.blit(status_label, (x + 70, y))
        
        # MIND Grubu
        y_offset = 280
        group_title = font_label.render("MIND (Mavi)", True, (120, 200, 255))
        screen.blit(group_title, (50, y_offset))
        
        for i in range(4):
            stat_name, icon_key, color = STATS[4 + i]
            x = 50 + (i * 220)
            y = y_offset + 40
            
            # İkon
            icon_surf = icon_loader.get_icon(icon_key, 64, is_category=False)
            if icon_surf:
                screen.blit(icon_surf, (x, y))
                status = "✓"
                status_color = (0, 255, 0)
            else:
                fallback = font_title.render("?", True, (150, 150, 150))
                screen.blit(fallback, (x + 20, y + 10))
                status = "✗"
                status_color = (255, 0, 0)
            
            # Stat adı
            label = font_label.render(stat_name, True, color)
            screen.blit(label, (x, y + 70))
            
            # İkon anahtarı
            key_label = font_small.render(f"({icon_key})", True, (150, 150, 150))
            screen.blit(key_label, (x, y + 92))
            
            # Durum
            status_label = font_small.render(status, True, status_color)
            screen.blit(status_label, (x + 70, y))
        
        # CONNECTION Grubu
        y_offset = 460
        group_title = font_label.render("CONNECTION (Yeşil)", True, (60, 200, 100))
        screen.blit(group_title, (50, y_offset))
        
        for i in range(4):
            stat_name, icon_key, color = STATS[8 + i]
            x = 50 + (i * 220)
            y = y_offset + 40
            
            # İkon
            icon_surf = icon_loader.get_icon(icon_key, 64, is_category=False)
            if icon_surf:
                screen.blit(icon_surf, (x, y))
                status = "✓"
                status_color = (0, 255, 0)
            else:
                fallback = font_title.render("?", True, (150, 150, 150))
                screen.blit(fallback, (x + 20, y + 10))
                status = "✗"
                status_color = (255, 0, 0)
            
            # Stat adı
            label = font_label.render(stat_name, True, color)
            screen.blit(label, (x, y + 70))
            
            # İkon anahtarı
            key_label = font_small.render(f"({icon_key})", True, (150, 150, 150))
            screen.blit(key_label, (x, y + 92))
            
            # Durum
            status_label = font_small.render(status, True, status_color)
            screen.blit(status_label, (x + 70, y))
        
        # Alt bilgi
        info = font_small.render("✓ = İkon yüklendi | ✗ = İkon bulunamadı", True, (180, 180, 180))
        screen.blit(info, (350, 650))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()
