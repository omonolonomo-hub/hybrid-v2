"""Pygame + engine temel test — hata mesajını görmek için."""
import traceback

print("1) pygame import...")
try:
    import pygame
    print(f"   OK — pygame {pygame.version.ver}")
except Exception as e:
    print(f"   HATA: {e}")
    raise

print("2) pygame.init()...")
try:
    pygame.init()
    print("   OK")
except Exception as e:
    print(f"   HATA: {e}")
    raise

print("3) pencere aç (800x600)...")
try:
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("TEST")
    print("   OK — pencere açıldı")
except Exception as e:
    print(f"   HATA: {e}")
    raise

print("4) engine import...")
try:
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from engine_core.card import get_card_pool
    from engine_core.player import Player
    from engine_core.game import Game
    from engine_core.board import combat_phase, BOARD_COORDS
    from engine_core.passive_trigger import trigger_passive
    print(f"   OK — {len(get_card_pool())} kart yüklendi")
    print(f"   OK — BOARD_COORDS: {len(BOARD_COORDS)} hex")
except Exception as e:
    print(f"   HATA: {e}")
    traceback.print_exc()
    raise

print("5) ui.renderer import...")
try:
    from ui.renderer import BoardRenderer, hex_to_pixel, BOARD_COORDS as BC2
    print("   OK")
except Exception as e:
    print(f"   HATA: {e}")
    traceback.print_exc()
    raise

print("6) Game oluştur + 1 tur çalıştır...")
try:
    import random
    from engine_core.constants import STRATEGIES
    rng = random.Random(42)
    pool = get_card_pool()
    strats = STRATEGIES[:]
    rng.shuffle(strats)
    players = [Player(pid=i, strategy=strats[i % len(strats)]) for i in range(8)]
    game = Game(players, verbose=False, rng=rng,
                trigger_passive_fn=trigger_passive,
                combat_phase_fn=combat_phase,
                card_pool=pool)
    game.preparation_phase()
    game.combat_phase()
    print(f"   OK — tur {game.turn} tamamlandı")
except Exception as e:
    print(f"   HATA: {e}")
    traceback.print_exc()
    raise

print("\n✅ Tüm testler geçti — pencere 3 saniye açık kalacak")
import time
start = time.time()
running = True
while running and time.time() - start < 3:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False
    screen.fill((15, 16, 24))
    font = pygame.font.SysFont("segoeui", 24)
    surf = font.render("Autochess Hybrid — Test OK!", True, (80, 200, 120))
    screen.blit(surf, (800//2 - surf.get_width()//2, 280))
    pygame.display.flip()

pygame.quit()
print("Bitti.")
