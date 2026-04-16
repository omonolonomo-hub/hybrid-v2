from v2.assets.loader import AssetLoader
from v2.constants import Paths

class LobbyScene:
    def __init__(self):
        self._audio_loader = None
        try:
            self._audio_loader = AssetLoader.get()
            self._audio_loader.preload_scene(
                Paths.MUSIC_LOBBY,
                Paths.SFX_BUY,
                Paths.SFX_REROLL,
            )
        except Exception:
            self._audio_loader = None
