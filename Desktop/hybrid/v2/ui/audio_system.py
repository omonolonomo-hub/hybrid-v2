"""
AudioSystem - Merkezi ses efekti yönetimi.

Pure I/O component, hiçbir scene state'ine bağımlı değil.
"""
from typing import Dict, Optional

import pygame

from v2.assets.loader import AssetLoader
from v2.core.exceptions import AutochessException


class AudioSystem:
    """Ses efektlerini merkezi yönetir ve cache'ler."""

    def __init__(self):
        self._cache: Dict[str, pygame.mixer.Sound] = {}
        self._loader: Optional[AssetLoader] = None

    def _ensure_loader(self) -> AssetLoader:
        """Lazy-load AssetLoader instance."""
        if self._loader is None:
            self._loader = AssetLoader.get()
        return self._loader

    def preload(self, name: str) -> None:
        """
        Ses efektini önceden yükle ve cache'le.
        
        Args:
            name: SFX dosya adı (örn: "buy.wav")
        """
        if name not in self._cache:
            try:
                loader = self._ensure_loader()
                sound = loader.get_sfx(name)
                self._cache[name] = sound
            except (AutochessException, FileNotFoundError):
                pass  # Sessizce başarısız ol

    def play(self, name: str, volume: float = 1.0) -> None:
        """
        Ses efektini çal.
        
        Args:
            name: SFX dosya adı
            volume: Ses seviyesi (0.0-1.0)
        """
        try:
            # Cache'de yoksa yükle
            if name not in self._cache:
                self.preload(name)
            
            sound = self._cache.get(name)
            if sound:
                sound.set_volume(volume)
                sound.play()
        except (AutochessException, pygame.error):
            pass  # Sessizce başarısız ol

    def stop(self, name: str) -> None:
        """
        Belirli bir ses efektini durdur.
        
        Args:
            name: SFX dosya adı
        """
        sound = self._cache.get(name)
        if sound:
            sound.stop()

    def stop_all(self) -> None:
        """Tüm ses efektlerini durdur."""
        for sound in self._cache.values():
            sound.stop()

    def clear_cache(self) -> None:
        """Cache'i temizle."""
        self.stop_all()
        self._cache.clear()

    @property
    def cached_count(self) -> int:
        """Cache'lenmiş ses sayısı."""
        return len(self._cache)
