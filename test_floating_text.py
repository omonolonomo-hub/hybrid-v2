import os
import random
import pygame
from v2.ui.widgets import FloatingTextManager
from v2.constants import Colors

BUTTON_RECT = pygame.Rect(40, 40, 180, 50)
FPS_OPTIONS = [30, 144]

COLOR_MAP = [
    ("MIND", Colors.MIND),
    ("CONNECTION", Colors.CONNECTION),
    ("EXISTENCE", Colors.EXISTENCE),
]


def main():
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    pygame.display.set_caption("FloatingText QA Sandbox")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 18)

    manager = FloatingTextManager()
    fps_limit = 30
    fps_index = 0

    running = True
    while running:
        dt_ms = clock.tick(fps_limit)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if BUTTON_RECT.collidepoint(event.pos):
                    spawn_random_text(manager)
                else:
                    pass
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    fps_index = (fps_index + 1) % len(FPS_OPTIONS)
                    fps_limit = FPS_OPTIONS[fps_index]

        manager.update(dt_ms)

        screen.fill((16, 20, 30))
        pygame.draw.rect(screen, (40, 60, 90), BUTTON_RECT, border_radius=8)
        pygame.draw.rect(screen, (160, 200, 255), BUTTON_RECT, width=2, border_radius=8)
        draw_text(screen, font, "Spawn FloatingText", BUTTON_RECT, center=True)

        info_lines = [
            f"Click button to spawn queued floating text.",
            f"Current FPS limit: {fps_limit}",
            "Press SPACE to toggle 30/144 FPS.",
            "Rapid clicks should queue without overlap.",
            f"Active texts: {manager.active_count}",
        ]
        for idx, line in enumerate(info_lines):
            draw_text(screen, font, line, pygame.Rect(40, 110 + idx * 24, 560, 24))

        manager.render(screen)
        pygame.display.flip()

    pygame.quit()


def spawn_random_text(manager: FloatingTextManager) -> None:
    label, color = random.choice(COLOR_MAP)
    x = random.randint(200, 580)
    y = random.randint(200, 420)
    manager.spawn(
        f"+{label}", x, y,
        color,
        font_size=18,
        coord_key=("floating_text",),
    )


def draw_text(surface, font, text, rect, center=False):
    text_surf = font.render(text, True, (230, 230, 240))
    if center:
        target = text_surf.get_rect(center=rect.center)
    else:
        target = text_surf.get_rect(topleft=(rect.x + 8, rect.y + 8))
    surface.blit(text_surf, target)


if __name__ == "__main__":
    main()
