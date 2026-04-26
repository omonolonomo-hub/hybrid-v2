import os
import pygame
from v2.assets.loader import AssetLoader
from v2.constants import Paths

BUTTONS = [
    ("Buy", Paths.SFX_BUY),
    ("Reroll", Paths.SFX_REROLL),
    ("Place", Paths.SFX_PLACE),
]

TRACKS = [
    ("Lobby", Paths.MUSIC_LOBBY),
    ("Shop", Paths.MUSIC_SHOP),
    ("Combat", Paths.MUSIC_COMBAT),
]


def main():
    pygame.init()
    if not pygame.mixer.get_init():
        pygame.mixer.init()

    screen = pygame.display.set_mode((760, 520))
    pygame.display.set_caption("Audio System QA Sandbox")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 18)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "v2", "assets"))
    AssetLoader.initialize(base_dir)
    loader = AssetLoader.get()

    button_rects = [pygame.Rect(40 + i * 240, 40, 220, 60) for i in range(len(BUTTONS))]
    music_rects = [pygame.Rect(40 + i * 240, 140, 220, 60) for i in range(len(TRACKS))]
    master_slider = Slider(pygame.Rect(40, 260, 420, 30), 0.8)
    sfx_slider = Slider(pygame.Rect(40, 320, 420, 30), 0.5)

    current_track = 0
    load_music(loader, TRACKS[current_track][1], master_slider.value)

    running = True
    while running:
        dt_ms = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for idx, rect in enumerate(button_rects):
                    if rect.collidepoint(event.pos):
                        play_sfx(loader, BUTTONS[idx][1], master_slider.value, sfx_slider.value)
                for idx, rect in enumerate(music_rects):
                    if rect.collidepoint(event.pos):
                        current_track = idx
                        load_music(loader, TRACKS[idx][1], master_slider.value)
                master_slider.handle_event(event)
                sfx_slider.handle_event(event)
            elif event.type == pygame.MOUSEMOTION:
                master_slider.handle_event(event)
                sfx_slider.handle_event(event)
            elif event.type == pygame.MOUSEBUTTONUP:
                master_slider.handle_event(event)
                sfx_slider.handle_event(event)

        master_slider.update(dt_ms)
        sfx_slider.update(dt_ms)

        screen.fill((18, 22, 32))
        draw_section(screen, font, "Action Sounds", button_rects, BUTTONS)
        draw_section(screen, font, "Music Tracks", music_rects, TRACKS)
        draw_text(screen, font, f"Master Volume: {master_slider.value:.2f}", pygame.Rect(40, 240, 420, 20))
        draw_text(screen, font, f"SFX Volume: {sfx_slider.value:.2f}", pygame.Rect(40, 300, 420, 20))
        draw_text(screen, font, "Click track buttons to switch music.", pygame.Rect(40, 380, 680, 24))
        draw_text(screen, font, "Rapidly click Reroll to test channel saturation.", pygame.Rect(40, 410, 680, 24))

        master_slider.render(screen)
        sfx_slider.render(screen)

        pygame.display.flip()

    pygame.quit()


def play_sfx(loader, sfx_name, master, sfx_vol):
    try:
        sound = loader.get_sfx(sfx_name)
        sound.set_volume(master * sfx_vol)
        sound.play()
    except Exception:
        pass


def load_music(loader, music_name, master):
    try:
        path = loader.get_music(music_name)
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(master * 0.6)
        pygame.mixer.music.play(-1)
    except Exception:
        pass


def draw_section(screen, font, title, rects, items):
    draw_text(screen, font, title, pygame.Rect(rects[0].x, rects[0].y - 28, 680, 20))
    for rect, item in zip(rects, items):
        pygame.draw.rect(screen, (45, 65, 90), rect, border_radius=10)
        pygame.draw.rect(screen, (170, 210, 255), rect, width=2, border_radius=10)
        draw_text(screen, font, item[0], rect)


def draw_text(surface, font, text, rect):
    surf = font.render(text, True, (230, 230, 230))
    surface.blit(surf, (rect.x + 12, rect.y + 8))


class Slider:
    def __init__(self, rect, value=0.5):
        self.rect = pygame.Rect(rect)
        self.value = max(0.0, min(1.0, value))
        self._dragging = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self._dragging = True
            self._update_value(event.pos)
        elif event.type == pygame.MOUSEMOTION and self._dragging:
            self._update_value(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP:
            self._dragging = False

    def _update_value(self, pos):
        rel_x = pos[0] - self.rect.x
        self.value = max(0.0, min(1.0, rel_x / self.rect.w))

    def update(self, dt_ms):
        pass

    def render(self, surface):
        pygame.draw.rect(surface, (80, 100, 130), self.rect, border_radius=8)
        fill_rect = self.rect.copy()
        fill_rect.width = int(self.rect.w * self.value)
        pygame.draw.rect(surface, (120, 180, 255), fill_rect, border_radius=8)
        handle_x = self.rect.x + int(self.rect.w * self.value)
        pygame.draw.circle(surface, (220, 240, 255), (handle_x, self.rect.centery), 10)


if __name__ == "__main__":
    main()
