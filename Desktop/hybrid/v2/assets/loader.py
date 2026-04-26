import os

import pygame

from v2.constants import AudioConfig
from v2.core.exceptions import AssetLoadError

# Kart adı -> dosya adı özel eşlemeler
_CARD_NAME_OVERRIDES: dict[str, str] = {
    "π (Pi)": "pi_(Pi)",
}


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
            raise AssetLoadError("AssetLoader henüz başlatılmadı! initialize() çağrısı yapılmamış.")
        return cls._instance

    @classmethod
    def initialize(cls, base_dir: str) -> None:
        if cls._instance is None:
            inst = AssetLoader()
            inst.base_dir = base_dir
            cls._instance = inst

    def get_sprite(self, name: str) -> pygame.Surface:
        if name in self._sprites:
            return self._sprites[name]

        full_path = os.path.join(self.base_dir, "sprites", name)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"[AssetLoader] Eksik sprite: {full_path}")

        try:
            surface = pygame.image.load(full_path).convert_alpha()
        except pygame.error:
            surface = pygame.image.load(full_path)
        self._sprites[name] = surface
        return surface

    def get_card_front(self, card_name: str) -> pygame.Surface:
        file_name = _CARD_NAME_OVERRIDES.get(card_name, card_name)
        return self.get_sprite(f"cards/{file_name}_front.png")

    def get_card_back(self, card_name: str) -> pygame.Surface:
        file_name = _CARD_NAME_OVERRIDES.get(card_name, card_name)
        return self.get_sprite(f"cards/{file_name}_back.png")

    def get_font(self, name: str, size: int) -> pygame.font.Font:
        key = (name, size)
        if key in self._fonts:
            return self._fonts[key]

        ttf_path = os.path.join(self.base_dir, "fonts", name)
        if os.path.exists(ttf_path):
            font = pygame.font.Font(ttf_path, size)
        else:
            font_base = os.path.splitext(name)[0].lower()
            font = pygame.font.SysFont(font_base, size)

        self._fonts[key] = font
        return font

    def get_default_font(self, size: int) -> pygame.font.Font:
        return self.get_font("monospace", size)

    def get_sfx(self, name: str) -> pygame.mixer.Sound:
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
        for asset_name in asset_names:
            try:
                if asset_name.lower().endswith((".wav", ".mp3", ".flac")):
                    self.get_sfx(asset_name)
                elif asset_name.lower().endswith((".ogg", ".wav", ".mp3", ".flac")):
                    self.get_music(asset_name)
            except (AssetLoadError, FileNotFoundError, pygame.error):
                pass

    def clear_cache(self) -> None:
        self._sprites.clear()
        self._fonts.clear()

    @property
    def cached_sprite_count(self) -> int:
        return len(self._sprites)
