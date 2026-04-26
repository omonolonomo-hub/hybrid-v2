import pygame


class Scene:
    """Tüm sahnelerin türetildiği base class. (Spec Section 3.1)"""

    def on_enter(self) -> None:
        """Sahne aktif hale geldiğinde bir kez çağrılır."""
        pass

    def on_exit(self) -> None:
        """Sahne değişmeden önce bir kez çağrılır; kaynakları serbest bırak."""
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        """Pygame event'lerini işle. Geçiş sırasında çağrılmaz."""
        pass

    def update(self, dt_ms: float) -> None:
        """dt_ms: milisaniye cinsinden delta time."""
        pass

    def draw(self, surface: pygame.Surface) -> None:
        """Sahneyi yüzeye çiz."""
        pass


class SceneManager:
    """
    Tek aktif sahneyi yönetir. Sahneler arası alpha-fade geçişi sağlar.
    Geçiş sırasında input iletilmez (spec gereği).

    Kullanım:
        sm = SceneManager.get()
        sm.set_scene(ShopScene())          # İlk sahne — fade yok
        sm.transition_to(CombatScene())    # Fade geçişi

    Ana döngüde:
        sm.handle_event(event)
        sm.update(dt_ms)
        sm.draw(screen)
    """

    _instance: 'SceneManager | None' = None

    def __init__(self):
        self._current: Scene | None = None
        self._pending: Scene | None = None
        self._fade_surface: pygame.Surface | None = None
        self._fade_duration_ms: float = 200.0
        self._fade_elapsed_ms: float = 0.0
        self._alpha: int = 0                     # 0 = şeffaf, 255 = siyah
        # "idle" | "fade_out" | "fade_in"
        self._state: str = "idle"

    @classmethod
    def get(cls) -> 'SceneManager':
        if cls._instance is None:
            cls._instance = SceneManager()
        return cls._instance

    # ── Public API ────────────────────────────────────────────────────────────

    def set_scene(self, scene: Scene) -> None:
        """İlk sahneyi fade olmadan yükler. Yalnızca başlangıçta çağır."""
        if self._current is not None:
            if hasattr(self._current, 'on_exit'):
                self._current.on_exit()
        self._current = scene
        if hasattr(self._current, 'on_enter'):
            self._current.on_enter()
        self._state = "idle"
        self._alpha = 0

    def transition_to(self, scene: Scene, fade_ms: int = 200) -> None:
        """
        Fade-out → sahne değiş → fade-in geçişini başlatır.
        Geçiş devam ediyorsa yeni geçiş yoksayılır.
        """
        if self._state != "idle":
            return
        self._pending = scene
        self._fade_duration_ms = max(float(fade_ms), 1.0)
        self._fade_elapsed_ms = 0.0
        self._alpha = 0
        self._state = "fade_out"

    def handle_event(self, event: pygame.event.Event) -> None:
        """Geçiş sırasında input iletilmez."""
        if self._state == "idle" and self._current is not None:
            # ShopScene gibi eski sahneler handle_event kullanıyor
            if hasattr(self._current, 'handle_event'):
                self._current.handle_event(event)

    def update(self, dt_ms: float) -> None:
        if self._state == "idle":
            if self._current is not None:
                self._current.update(dt_ms)
            return

        self._fade_elapsed_ms += dt_ms
        progress = min(self._fade_elapsed_ms / self._fade_duration_ms, 1.0)

        if self._state == "fade_out":
            self._alpha = int(255 * progress)
            if progress >= 1.0:
                # Sahneyi değiştir
                if self._current is not None:
                    if hasattr(self._current, 'on_exit'):
                        self._current.on_exit()
                self._current = self._pending
                self._pending = None
                if self._current is not None:
                    if hasattr(self._current, 'on_enter'):
                        self._current.on_enter()
                self._fade_elapsed_ms = 0.0
                self._state = "fade_in"

        elif self._state == "fade_in":
            self._alpha = int(255 * (1.0 - progress))
            if self._current is not None:
                self._current.update(dt_ms)
            if progress >= 1.0:
                self._alpha = 0
                self._state = "idle"

    def draw(self, surface: pygame.Surface) -> None:
        """Aktif sahneyi çizer; geçiş sırasında siyah overlay ekler."""
        if self._current is not None:
            # Geriye dönük uyumluluk: eski sahneler render() kullanıyor
            if hasattr(self._current, 'draw'):
                self._current.draw(surface)
            elif hasattr(self._current, 'render'):
                self._current.render(surface)

        # Fade overlay
        if self._alpha > 0:
            if (self._fade_surface is None
                    or self._fade_surface.get_size() != surface.get_size()):
                self._fade_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            self._fade_surface.fill((0, 0, 0, self._alpha))
            surface.blit(self._fade_surface, (0, 0))

    # ── Read-only props ───────────────────────────────────────────────────────

    @property
    def is_transitioning(self) -> bool:
        return self._state != "idle"

    @property
    def current_scene_name(self) -> str:
        if self._current is None:
            return "None"
        return type(self._current).__name__

