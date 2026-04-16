import os
import pygame
from v2.constants import AudioConfig

class AssetLoader:
    _instance = None

    def __init__(self):
        self.base_dir = ""
        self._sprites: dict[str, pygame.Surface] = {}
        self._fonts: dict[tuple, pygame.font.Font] = {}
        self._sfx: dict[str, pygame.mixer.Sound] = {}
        self._music: dict[str, str] = {}

    @classmethod
    def get(cls) -> "AssetLoader":
        if cls._instance is None:
            raise RuntimeError("AssetLoader henüz başlatılmadı! initialize() çağrısı yapılmamış.")
        return cls._instance

    @classmethod
    def initialize(cls, base_dir: str) -> None:
        """Singleton başlatıcı. main.py içinden bir kez çağrılır."""
        if cls._instance is None:
            inst = AssetLoader()
            inst.base_dir = base_dir
            cls._instance = inst

    # ------------------------------------------------------------------ #
    # Sprite (PNG)                                                         #
    # ------------------------------------------------------------------ #
    def get_sprite(self, name: str) -> pygame.Surface:
        """
        name: sprites/ altındaki göreli yol. Örn: 'cards/Fibonacci Sequence_front.png'
        İlk yüklemede cache'e alır, sonrakinde cache'den döner.
        Dosya yoksa FileNotFoundError fırlatır — sessiz fallback YOKTUR.
        """
        if name in self._sprites:
            return self._sprites[name]

        full_path = os.path.join(self.base_dir, "sprites", name)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"[AssetLoader] Eksik sprite: {full_path}")

        # convert_alpha() display context gerektirir; test ortamlarında fallback uygula
        try:
            surface = pygame.image.load(full_path).convert_alpha()
        except pygame.error:
            surface = pygame.image.load(full_path)
        self._sprites[name] = surface
        return surface

    def get_card_front(self, card_name: str) -> pygame.Surface:
        """Kolaylık yardımcısı: Kart ön yüzü. Örn: card_name='Fibonacci Sequence'"""
        return self.get_sprite(f"cards/{card_name}_front.png")

    def get_card_back(self, card_name: str) -> pygame.Surface:
        """Kolaylık yardımcısı: Kart arka yüzü."""
        return self.get_sprite(f"cards/{card_name}_back.png")

    # ------------------------------------------------------------------ #
    # Font                                                                 #
    # ------------------------------------------------------------------ #
    def get_font(self, name: str, size: int) -> pygame.font.Font:
        """
        name: v2/assets/fonts/ altındaki TTF dosya adı.
        Dosya bulunamazsa pygame SysFont ("monospace" veya name) ile geri düşer.
        Çift yüklemeyi önlemek için (name, size) tuple ile cache'lenir.
        """
        key = (name, size)
        if key in self._fonts:
            return self._fonts[key]

        ttf_path = os.path.join(self.base_dir, "fonts", name)
        if os.path.exists(ttf_path):
            font = pygame.font.Font(ttf_path, size)
        else:
            # SysFont fallback — sessizce devam eder ama WARNING basar
            font_base = os.path.splitext(name)[0].lower()
            font = pygame.font.SysFont(font_base, size)

        self._fonts[key] = font
        return font

    def get_default_font(self, size: int) -> pygame.font.Font:
        """Fallback font: sistem monospace."""
        return self.get_font("monospace", size)

    def get_sfx(self, name: str) -> pygame.mixer.Sound:
        """Returns a cached pygame Sound for the given SFX filename."""
        if name in self._sfx:
            return self._sfx[name]

        full_path = os.path.join(self.base_dir, "sfx", name)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"[AssetLoader] Eksik SFX: {full_path}")

        sound = pygame.mixer.Sound(full_path)
        sound.set_volume(AudioConfig.MASTER * AudioConfig.SFX)
        self._sfx[name] = sound
        return sound

    def get_music(self, name: str) -> str:
        """Returns the filesystem path for a music track and applies music volume."""
        if name in self._music:
            return self._music[name]

        full_path = os.path.join(self.base_dir, "music", name)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"[AssetLoader] Eksik music track: {full_path}")

        if pygame.mixer.get_init() is not None:
            pygame.mixer.music.set_volume(AudioConfig.MASTER * AudioConfig.MUSIC)

        self._music[name] = full_path
        return full_path

    def preload_scene(self, *asset_names: str) -> None:
        """Preloads the specified audio files for a scene.

        Supports both SFX and music assets by file extension.
        """
        for asset_name in asset_names:
            if asset_name.lower().endswith((".wav", ".mp3", ".flac")):
                try:
                    self.get_sfx(asset_name)
                except Exception:
                    pass
            elif asset_name.lower().endswith((".ogg", ".wav", ".mp3", ".flac")):
                try:
                    self.get_music(asset_name)
                except Exception:
                    pass

    # ------------------------------------------------------------------ #
    # Cache kontrolü                                                        #
    # ------------------------------------------------------------------ #
    def clear_cache(self) -> None:
        """Test veya sahne geçişlerinde RAM'i temizlemek için kullanılabilir."""
        self._sprites.clear()
        self._fonts.clear()

    @property
    def cached_sprite_count(self) -> int:
        return len(self._sprites)
