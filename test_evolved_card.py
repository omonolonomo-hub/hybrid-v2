import os
import pygame
from v2.ui.card_flip import CardFlip
from v2.constants import Colors

BUTTON_EVO = pygame.Rect(40, 40, 180, 45)
BUTTON_FLIP = pygame.Rect(240, 40, 180, 45)


def make_card_surfaces(size):
    w, h = size
    back = pygame.Surface((w, h), pygame.SRCALPHA)
    front = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(back, (32, 44, 72), back.get_rect(), border_radius=16)
    pygame.draw.rect(back, (60, 90, 140), back.get_rect(), width=3, border_radius=16)
    pygame.draw.rect(front, (72, 120, 180), front.get_rect(), border_radius=16)
    pygame.draw.rect(front, (220, 250, 255), front.get_rect(), width=3, border_radius=16)
    font = pygame.font.SysFont("Arial", 26, bold=True)
    text_surf = font.render("Card", True, (240, 240, 255))
    front.blit(text_surf, text_surf.get_rect(center=front.get_rect().center))
    return back, front


def main():
    pygame.init()
    screen = pygame.display.set_mode((640, 520))
    pygame.display.set_caption("Evolved Card QA Sandbox")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 18)

    card_rect = pygame.Rect(220, 140, 200, 260)
    back, front = make_card_surfaces(card_rect.size)
    flip = CardFlip(back, front, card_rect)
    evolved = False
    flip_state = False

    running = True
    while running:
        dt_ms = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if BUTTON_EVO.collidepoint(event.pos):
                    evolved = True
                    flip = CardFlip(back, front, card_rect, evolved=True, evolved_color=Colors.PLATINUM)
                    flip_state = True
                    flip.hover_start()
                elif BUTTON_FLIP.collidepoint(event.pos):
                    if flip_state:
                        flip.hover_end()
                    else:
                        flip.hover_start()
                    flip_state = not flip_state

        flip.update(dt_ms)

        screen.fill((16, 18, 28))
        pygame.draw.rect(screen, (48, 68, 96), BUTTON_EVO, border_radius=8)
        pygame.draw.rect(screen, (180, 220, 255), BUTTON_EVO, width=2, border_radius=8)
        pygame.draw.rect(screen, (48, 68, 96), BUTTON_FLIP, border_radius=8)
        pygame.draw.rect(screen, (180, 220, 255), BUTTON_FLIP, width=2, border_radius=8)
        draw_text(screen, font, "Evrimleştir", BUTTON_EVO)
        draw_text(screen, font, "Kartı Çevir", BUTTON_FLIP)

        info = [
            "Evrimleştir butonuna basarak platin glow'u test edin.",
            "Kartı Çevir butonuyla CardFlip animasyonunu çalıştırın.",
            "Glow efektinin ve platin çerçevenin sabit kaldığını doğrulayın.",
        ]
        for idx, line in enumerate(info):
            draw_text(screen, font, line, pygame.Rect(40, 420 + idx * 20, 560, 20))

        flip.render(screen)
        pygame.display.flip()

    pygame.quit()


def draw_text(surface, font, text, rect):
    text_surf = font.render(text, True, (224, 228, 240))
    surface.blit(text_surf, (rect.x + 10, rect.y + 10))


if __name__ == "__main__":
    main()
