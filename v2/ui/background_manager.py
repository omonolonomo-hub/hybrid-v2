import pygame
import math
from v2.constants import Screen

class BackgroundManager:
    _instance = None

    @classmethod
    def get(cls) -> "BackgroundManager":
        if cls._instance is None:
            cls._instance = BackgroundManager()
        return cls._instance

    def __init__(self):
        self._cache: dict[str, pygame.Surface] = {}
        # Eagerly generate defaults (Vignette)
        self._cache["vignette"] = self._create_vignette(Screen.W, Screen.H)

    def render(self, surface: pygame.Surface, zoom: float = 1.0, offset: tuple[float, float] = (0, 0)):
        """
        Siberpunk Void Arkaplanını (Hex-Grid + Vignette) kamera state'ine göre çizer.
        """
        w, h = Screen.W, Screen.H

        # 1. Taban Katmanı
        surface.fill((12, 16, 26))

        # 2. Dinamik Petek Dokusu (Kamera odaklı)
        self._render_hex_pattern(surface, zoom, offset)

        # 3. Vignette
        if "vignette" not in self._cache:
            self._cache["vignette"] = self._create_vignette(w, h)
        surface.blit(self._cache["vignette"], (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    def _render_hex_pattern(self, surface: pygame.Surface, zoom: float, offset: tuple[float, float]):
        """Kamera odaklı, sonsuz petek illüzyonu çizen dinamik render."""
        from v2.ui.hex_grid import axial_to_pixel
        from v2.constants import GridMath

        color = (120, 180, 255, 15) # Daha az göz yorucu arka plan dokusu
        radius = GridMath.HEX_SIZE * zoom

        # Ekranı kaplayacak q, r aralığını hesapla (Kaba taslak)
        # 1920x1080 için yaklaşık -15 ile +15 arası yeterli olur (zoom 1.0'da)
        limit = int(20 / zoom) + 2

        for q in range(-limit, limit):
            for r in range(-limit, limit):
                cx, cy = axial_to_pixel(q, r)

                # Sadece ekranda görünenleri çiz (Performance guard)
                if -radius < cx < Screen.W + radius and -radius < cy < Screen.H + radius:
                    points = []
                    for i in range(6):
                        angle = math.radians(60 * i - 30)
                        px = cx + radius * math.cos(angle)
                        py = cy + radius * math.sin(angle)
                        points.append((int(px), int(py)))

                    pygame.draw.polygon(surface, color, points, 1)

    def _create_vignette(self, width: int, height: int) -> pygame.Surface:
        v_size = 256
        v_surf = pygame.Surface((v_size, v_size))
        center = v_size // 2

        # Dış çeperin alacağı minimum renk (Kenarlar çok koyu)
        v_surf.fill((30, 20, 30))

        # Merkeze doğru giderek aydınlanan iç içe halkalar (Banding SDL Smoothscale ile eriyecek)
        for r in range(v_size, 0, -2):
            ratio = 1.0 - (r / v_size)
            # Smoothstep interpolasyon eğrisi (Işığın merkezi daha uzun parlak, kenarlara aniden kırılması için)
            ratio = ratio * ratio * (3 - 2 * ratio)

            # Merkezdeki ışık %100 geçirgen (255)
            c_val = int(30 + (225 * ratio))
            pygame.draw.circle(v_surf, (c_val, c_val, c_val), (center, center), r)

        # 256x256 çözünürlükteki gradiyenti, oyun çözünürlüğüne donanımsal gerdirmek
        # banding (çizgilenme) izlerini yok edip harika bir smooth shadow yaratır.
        return pygame.transform.smoothscale(v_surf, (width, height))
