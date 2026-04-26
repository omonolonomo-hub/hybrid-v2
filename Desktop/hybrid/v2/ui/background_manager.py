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
        from v2.constants import GridMath
        
        # Sadece zoom değiştiğinde oluşturulacak büyük bir önbellek yüzeyi kullanıyoruz
        if "hex_grid" not in self._cache or getattr(self, '_last_zoom', None) != zoom:
            self._cache["hex_grid"] = self._create_hex_grid_surface(zoom)
            self._last_zoom = zoom

        grid_surf = self._cache["hex_grid"]
        
        radius = GridMath.HEX_SIZE * zoom
        tw = math.sqrt(3) * radius
        th = 3.0 * radius
        
        # Sonsuz kaydırma için offset'i periyotlara modüllüyoruz
        # Board ile tam hizalanması için ORIGIN_X/Y'yi de hesaba katıyoruz
        draw_x = (GridMath.ORIGIN_X + offset[0]) % tw
        draw_y = (GridMath.ORIGIN_Y + offset[1]) % th
        
        # Üstte ve solda boşluk kalmaması için -tw ve -th konumundan başlatarak çiziyoruz
        surface.blit(grid_surf, (draw_x - tw, draw_y - th))

    def _create_hex_grid_surface(self, zoom: float) -> pygame.Surface:
        """Sonsuz kaydırma için ekranı ve payları kapsayacak kadar büyük statik petek yüzeyi."""
        from v2.constants import Screen, GridMath
        
        radius = GridMath.HEX_SIZE * zoom
        tw = math.sqrt(3) * radius
        th_step = 1.5 * radius
        th_full = 3.0 * radius
        
        # Yüzey boyutu: Ekran boyutu + kaydırma payları (2xTW, 2xTH_FULL)
        surf_w = int(Screen.W + tw * 2)
        surf_h = int(Screen.H + th_full * 2)
        
        surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
        color = (15, 20, 32)
        
        cos_a = [math.cos(math.radians(60 * i - 30)) for i in range(6)]
        sin_a = [math.sin(math.radians(60 * i - 30)) for i in range(6)]
        
        limit_r = int(surf_h / th_step) + 2
        
        # surface içi (0,0) aslında oyun board'unda cx=0, cy=0 noktasıyla tam hizalıdır
        for r in range(-2, limit_r):
            q_start = int(-r / 2.0) - 2
            q_end = int(surf_w / tw - r / 2.0) + 3
            for q in range(q_start, q_end):
                cx = tw * q + (tw / 2.0) * r
                cy = th_step * r
                
                if -radius <= cx <= surf_w + radius and -radius <= cy <= surf_h + radius:
                    points = [(cx + radius * cos_a[i], cy + radius * sin_a[i]) for i in range(6)]
                    pygame.draw.polygon(surf, color, points, 1)
                    
        return surf

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
