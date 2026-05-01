"""
menu_v3.py - Pywebview tabanli HTML menu entegrasyonu.

Mevcut MenuScene'in (v2/scenes/menu.py) gorsel katmanini degistirir.
Oyun mantigi (SceneManager, LobbyScene gecisi) Python tarafinda kalir.
"""

from __future__ import annotations

import argparse
import atexit
import ctypes
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import webview

from v2.constants import Screen
from v2.core.scene_manager import SceneManager  # Imported for integration context.


StartCallback = Callable[[], None]
MatchCallback = Callable[[list[str]], None]
OverlayBounds = tuple[int, int, int, int]
VALID_STRATEGIES = [
    "random",
    "warrior",
    "builder",
    "evolver",
    "economist",
    "balancer",
    "rare_hunter",
]
STRATEGY_META = {
    "random": {
        "label": "Random",
        "color": "#8C8C8C",
        "description": "Unpredictable card purchases",
    },
    "warrior": {
        "label": "Warrior",
        "color": "#DC3C3C",
        "description": "Aggressive combat focus",
    },
    "builder": {
        "label": "Builder",
        "color": "#50B464",
        "description": "Synergy building strategy",
    },
    "evolver": {
        "label": "Evolver",
        "color": "#A05ADC",
        "description": "Evolution-focused gameplay",
    },
    "economist": {
        "label": "Economist",
        "color": "#FFC832",
        "description": "Gold optimization",
    },
    "balancer": {
        "label": "Balancer",
        "color": "#6496FF",
        "description": "Balanced approach",
    },
    "rare_hunter": {
        "label": "Rare Hunter",
        "color": "#C8A0FF",
        "description": "Targets rare cards",
    },
}


def set_dpi_awareness() -> None:
    """Keep Pygame and pywebview sizes in real pixels on scaled Windows desktops."""
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


class WebMenuAPI:
    """JavaScript tarafindan window.pywebview.api uzerinden cagrilan API."""

    def __init__(
        self,
        on_start_game_callback: StartCallback,
        on_ready_callback: StartCallback | None = None,
        on_quit_callback: StartCallback | None = None,
        on_lobby_callback: StartCallback | None = None,
        on_match_callback: MatchCallback | None = None,
        close_on_start: bool = True,
        close_on_match: bool = True,
        lobby_url: str | None = None,
        menu_url: str | None = None,
    ):
        self._callback = on_start_game_callback
        self._ready_callback = on_ready_callback
        self._quit_callback = on_quit_callback
        self._lobby_callback = on_lobby_callback
        self._match_callback = on_match_callback
        self._close_on_start = close_on_start
        self._close_on_match = close_on_match
        self._lobby_url = lobby_url
        self._menu_url = menu_url
        self._window: webview.Window | None = None
        self._start_lock = threading.Lock()
        self._match_lock = threading.Lock()
        self._started = False
        self._match_started = False
        self._selected_strategies = list(VALID_STRATEGIES)

    def bind_window(self, window: webview.Window) -> None:
        self._window = window

    def start_game(self) -> dict[str, bool]:
        """JS tarafindaki YENI OYUN butonu bu metodu tetikler."""
        with self._start_lock:
            if self._started:
                return {"ok": True}
            self._started = True

        if self._lobby_callback is not None:
            threading.Thread(
                target=self._lobby_callback,
                daemon=True,
                name="WebMenuOpenLobbyCallback",
            ).start()
        else:
            # webview callback'leri ayri thread'den gelir; Pygame'e event iletilir.
            threading.Thread(
                target=self._callback,
                daemon=True,
                name="WebMenuStartGameCallback",
            ).start()

        if self._lobby_url:
            self._load_url(self._lobby_url)

        if self._close_on_start:
            self._close_overlay()
        return {"ok": True}

    def get_version(self) -> str:
        """JS tarafina versiyon bilgisi dondurur (debug amacli)."""
        return "AUTOCHESS HYBRID v2"

    def quit_app(self) -> dict[str, bool]:
        """ESC veya pencere kapatma akisinda web menuyu kapatir."""
        if self._quit_callback is not None:
            threading.Thread(
                target=self._quit_callback,
                daemon=True,
                name="WebMenuQuitCallback",
            ).start()
        self._close_overlay()
        return {"ok": True}

    def menu_ready(self) -> dict[str, bool]:
        """JS ilk gorunur frame hazir oldugunda gizli pencereyi gosterir."""
        if self._ready_callback is not None:
            threading.Thread(
                target=self._ready_callback,
                daemon=True,
                name="WebMenuReadyCallback",
            ).start()
        self._show_overlay()
        return {"ok": True}

    def lobby_ready(self) -> dict[str, bool]:
        """Lobby sayfasi ilk frame'e hazir oldugunda parent'a bildirir."""
        if self._lobby_callback is not None:
            threading.Thread(
                target=self._lobby_callback,
                daemon=True,
                name="WebLobbyReadyCallback",
            ).start()
        return {"ok": True}

    def get_lobby_state(self) -> dict[str, Any]:
        """Lobby HTML'inin strateji secim verisini alir."""
        return {
            "players": [
                {
                    "kind": "ai",
                    "name": f"AI {index + 1:02d}",
                    "strategy": strategy,
                }
                for index, strategy in enumerate(self._selected_strategies)
            ]
            + [{"kind": "human", "name": "HUMAN", "strategy": "human"}],
            "strategies": [
                {"id": strategy, **STRATEGY_META[strategy]}
                for strategy in VALID_STRATEGIES
            ],
        }

    def set_strategy(self, index: int, strategy: str) -> dict[str, bool]:
        """Tek bir AI stratejisini gunceller."""
        if not isinstance(index, int) or index < 0 or index >= len(self._selected_strategies):
            return {"ok": False}
        if strategy not in VALID_STRATEGIES:
            return {"ok": False}
        self._selected_strategies[index] = strategy
        return {"ok": True}

    def start_match(self, strategies: list[str] | None = None) -> dict[str, bool]:
        """Lobby'deki START MATCH butonu motor baslatma istegini Python'a iletir."""
        with self._match_lock:
            if self._match_started:
                return {"ok": True}
            self._match_started = True

        selected = self._sanitize_strategies(strategies)
        self._selected_strategies = selected

        if self._match_callback is not None:
            threading.Thread(
                target=self._match_callback,
                args=(selected,),
                daemon=True,
                name="WebLobbyStartMatchCallback",
            ).start()

        if self._close_on_match:
            self._close_overlay()
        return {"ok": True}

    def back_to_menu(self) -> dict[str, bool]:
        """Lobby'den menüye geri dönmek icin kullanilir."""
        self._started = False
        self._match_started = False
        if self._menu_url:
            self._load_url(self._menu_url)
        return {"ok": True}

    def _sanitize_strategies(self, strategies: list[str] | None) -> list[str]:
        if not isinstance(strategies, list):
            return list(self._selected_strategies)

        sanitized: list[str] = []
        for strategy in strategies[: len(VALID_STRATEGIES)]:
            sanitized.append(strategy if strategy in VALID_STRATEGIES else "random")

        while len(sanitized) < len(VALID_STRATEGIES):
            sanitized.append(VALID_STRATEGIES[len(sanitized)])
        return sanitized

    def _load_url(self, url: str) -> None:
        if self._window is None:
            return
        try:
            self._window.load_url(url)
        except Exception:
            try:
                self._window.evaluate_js(f"window.location.href = {json.dumps(url)}")
            except Exception:
                pass

    def _show_overlay(self) -> None:
        if self._window is None:
            return
        try:
            self._window.show()
            _activate_native_window(self._window)
        except Exception:
            pass

    def _close_overlay(self) -> None:
        if self._window is None:
            return
        try:
            self._window.destroy()
        except Exception:
            # Overlay kapanamasa bile Pygame tarafindaki gecisi engellemeyelim.
            pass


@dataclass
class WebMenuOverlayProcess:
    process: subprocess.Popen
    signal_path: Path

    def close(self) -> None:
        if self.process.poll() is None:
            try:
                self.process.terminate()
            except Exception:
                pass
        try:
            self.signal_path.unlink(missing_ok=True)
        except Exception:
            pass


def create_web_menu_window(
    on_start_callback: StartCallback,
    bounds: OverlayBounds | None = None,
    fullscreen: bool = False,
    hidden: bool = False,
    on_ready_callback: StartCallback | None = None,
    on_quit_callback: StartCallback | None = None,
    on_lobby_callback: StartCallback | None = None,
    on_match_callback: MatchCallback | None = None,
    close_on_start: bool = True,
    close_on_match: bool = True,
) -> webview.Window:
    ui_dir = Path(__file__).parent
    html_path = ui_dir / "index.html"
    lobby_path = ui_dir / "lobby.html"
    api = WebMenuAPI(
        on_start_callback,
        on_ready_callback=on_ready_callback,
        on_quit_callback=on_quit_callback,
        on_lobby_callback=on_lobby_callback,
        on_match_callback=on_match_callback,
        close_on_start=close_on_start,
        close_on_match=close_on_match,
        lobby_url=lobby_path.as_uri(),
        menu_url=html_path.as_uri(),
    )
    left, top, width, height = bounds or (0, 0, Screen.W, Screen.H)

    window = webview.create_window(
        title="AUTOCHESS HYBRID",
        url=html_path.as_uri(),
        js_api=api,
        width=width,
        height=height,
        x=left,
        y=top,
        frameless=True,
        easy_drag=False,
        shadow=False,
        transparent=False,
        draggable=False,
        on_top=True,
        resizable=False,
        fullscreen=fullscreen,
        hidden=hidden,
        background_color="#141928",
    )
    api.bind_window(window)
    return window


def _get_primary_screen_bounds() -> OverlayBounds:
    if sys.platform != "win32":
        return (0, 0, Screen.W, Screen.H)
    try:
        user32 = ctypes.windll.user32
        return (0, 0, int(user32.GetSystemMetrics(0)), int(user32.GetSystemMetrics(1)))
    except Exception:
        return (0, 0, Screen.W, Screen.H)


def show_web_menu_blocking() -> bool:
    """
    Pywebview menusunu ana thread'de tam ekran acar.

    Returns:
        True: YENI OYUN secildi.
        False: Menu kapatildi veya ESC ile cikildi.
    """
    set_dpi_awareness()
    start_requested = threading.Event()

    def _on_start() -> None:
        start_requested.set()

    create_web_menu_window(
        _on_start,
        bounds=_get_primary_screen_bounds(),
        fullscreen=True,
        hidden=False,
    )
    webview.start(debug=False)
    return start_requested.is_set()


def _get_client_bounds(hwnd: int | None) -> OverlayBounds:
    if sys.platform != "win32" or not hwnd:
        return (0, 0, Screen.W, Screen.H)

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        ]

    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    rect = RECT()
    origin = POINT(0, 0)
    user32 = ctypes.windll.user32

    if not user32.GetClientRect(int(hwnd), ctypes.byref(rect)):
        return (0, 0, Screen.W, Screen.H)
    if not user32.ClientToScreen(int(hwnd), ctypes.byref(origin)):
        return (0, 0, Screen.W, Screen.H)

    width = max(int(rect.right - rect.left), 1)
    height = max(int(rect.bottom - rect.top), 1)
    return (int(origin.x), int(origin.y), width, height)


def _position_window(
    window: webview.Window,
    pygame_hwnd: int | None,
    show: bool = True,
) -> None:
    left, top, width, height = _get_client_bounds(pygame_hwnd)
    edge_pad = 12
    left -= edge_pad
    top -= edge_pad
    width += edge_pad * 2
    height += edge_pad * 2

    try:
        import win32con
        import win32gui

        webview_hwnd = _get_native_hwnd(window)
        if not webview_hwnd:
            return

        flags = win32con.SWP_SHOWWINDOW if show else win32con.SWP_NOACTIVATE
        win32gui.SetWindowPos(
            webview_hwnd,
            win32con.HWND_TOPMOST,
            left,
            top,
            width,
            height,
            flags,
        )
    except ImportError:
        _position_window_with_ctypes(window, left, top, width, height, show)
    except Exception:
        _position_window_with_ctypes(window, left, top, width, height, show)


def _position_window_with_ctypes(
    window: webview.Window,
    left: int,
    top: int,
    width: int,
    height: int,
    show: bool = True,
) -> None:
    if sys.platform != "win32":
        return

    webview_hwnd = _get_native_hwnd(window)
    if not webview_hwnd:
        return

    hwnd_topmost = -1
    swp_showwindow = 0x0040
    swp_noactivate = 0x0010
    flags = swp_showwindow if show else swp_noactivate
    try:
        ctypes.windll.user32.SetWindowPos(
            int(webview_hwnd),
            hwnd_topmost,
            int(left),
            int(top),
            int(width),
            int(height),
            flags,
        )
    except Exception:
        pass


def _activate_native_window(window: webview.Window) -> None:
    if sys.platform != "win32":
        return

    hwnd = _get_native_hwnd(window)
    if not hwnd:
        return

    try:
        user32 = ctypes.windll.user32
        sw_restore = 9
        swp_nomove = 0x0002
        swp_nosize = 0x0001
        swp_showwindow = 0x0040
        hwnd_topmost = -1
        user32.ShowWindow(int(hwnd), sw_restore)
        user32.SetWindowPos(
            int(hwnd),
            hwnd_topmost,
            0,
            0,
            0,
            0,
            swp_nomove | swp_nosize | swp_showwindow,
        )
        user32.SetForegroundWindow(int(hwnd))
    except Exception:
        pass


def _get_native_hwnd(window: webview.Window) -> int | None:
    """Best-effort native handle lookup for pywebview's Windows backend."""
    for owner in (getattr(window, "native", None), window):
        if owner is None:
            continue
        for attr_name in ("Handle", "handle", "hwnd"):
            handle = getattr(owner, attr_name, None)
            if handle:
                try:
                    return int(handle)
                except (TypeError, ValueError):
                    continue

    try:
        import win32gui

        handle = win32gui.FindWindow(None, "AUTOCHESS HYBRID")
        return int(handle) if handle else None
    except Exception:
        if sys.platform != "win32":
            return None
        try:
            handle = ctypes.windll.user32.FindWindowW(None, "AUTOCHESS HYBRID")
            return int(handle) if handle else None
        except Exception:
            return None


def launch_menu_overlay(
    pygame_hwnd: int | None,
    on_start_callback: StartCallback,
    on_ready_callback: StartCallback | None = None,
    on_quit_callback: StartCallback | None = None,
    on_lobby_callback: StartCallback | None = None,
    on_match_callback: MatchCallback | None = None,
) -> WebMenuOverlayProcess:
    """
    Pywebview penceresini Pygame penceresinin uzerine konumlandirir.

    Args:
        pygame_hwnd: Windows'ta pygame.display.get_wm_info()["window"] ile alinir.
        on_start_callback: start_game tetiklendiginde cagrilacak fonksiyon.
    """
    signal_path = Path(tempfile.gettempdir()) / f"autochess_hybrid_menu_{os.getpid()}.signal"
    signal_path.unlink(missing_ok=True)

    project_root = Path(__file__).resolve().parents[3]
    command = [
        sys.executable,
        "-m",
        "v2.ui.web_menu.menu_v3",
        "--overlay-child",
        "--signal-file",
        str(signal_path),
    ]
    if pygame_hwnd:
        command.extend(["--pygame-hwnd", str(int(pygame_hwnd))])

    process = subprocess.Popen(command, cwd=str(project_root))
    overlay = WebMenuOverlayProcess(process=process, signal_path=signal_path)
    atexit.register(overlay.close)

    def _dispatch_signal(payload: dict[str, Any]) -> bool:
        action = str(payload.get("action", "start")).lower()
        if action in {"ready", "menu_ready"}:
            if on_ready_callback is not None:
                on_ready_callback()
            return False
        if action in {"open_lobby", "lobby_ready"}:
            if on_lobby_callback is not None:
                on_lobby_callback()
            return False
        if action == "start_match":
            if on_match_callback is not None:
                strategies = payload.get("strategies")
                on_match_callback(strategies if isinstance(strategies, list) else [])
            return True
        if action == "quit":
            if on_quit_callback is not None:
                on_quit_callback()
            return True

        on_start_callback()
        return True

    def _watch_signal() -> None:
        while process.poll() is None:
            if signal_path.exists():
                payload = _read_signal_payload(signal_path)
                signal_path.unlink(missing_ok=True)
                if _dispatch_signal(payload):
                    return
            time.sleep(0.05)

        if signal_path.exists():
            payload = _read_signal_payload(signal_path)
            signal_path.unlink(missing_ok=True)
            _dispatch_signal(payload)
        elif on_quit_callback is not None:
            on_quit_callback()

    threading.Thread(
        target=_watch_signal,
        daemon=True,
        name="WebMenuSignalWatcher",
    ).start()
    return overlay


def _read_signal_payload(signal_path: Path) -> dict[str, Any]:
    try:
        raw = signal_path.read_text(encoding="utf-8").strip()
    except Exception:
        return {"action": "start"}

    if not raw:
        return {"action": "start"}

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {"action": raw.lower()}

    if isinstance(payload, dict):
        return payload
    return {"action": "start"}


def _write_signal(signal_file: Path, action: str, **payload: Any) -> None:
    data = {"action": action, **payload}
    signal_file.write_text(json.dumps(data), encoding="utf-8")


def _run_overlay_child(signal_file: Path, pygame_hwnd: int | None) -> None:
    set_dpi_awareness()
    bounds = _get_primary_screen_bounds()

    def _on_start() -> None:
        _write_signal(signal_file, "start")

    def _on_ready() -> None:
        _write_signal(signal_file, "menu_ready")

    def _on_quit() -> None:
        _write_signal(signal_file, "quit")

    def _on_lobby() -> None:
        _write_signal(signal_file, "open_lobby")

    def _on_match(strategies: list[str]) -> None:
        _write_signal(signal_file, "start_match", strategies=strategies)

    def _on_loaded(*_args: object) -> None:
        _position_window(window, pygame_hwnd, show=False)

    window = create_web_menu_window(
        _on_start,
        bounds,
        fullscreen=False,
        hidden=True,
        on_ready_callback=_on_ready,
        on_quit_callback=_on_quit,
        on_lobby_callback=_on_lobby,
        on_match_callback=_on_match,
        close_on_start=False,
        close_on_match=False,
    )
    window.events.loaded += _on_loaded
    webview.start(debug=False)


def _run_legacy_threaded_overlay(
    pygame_hwnd: int | None,
    on_start_callback: StartCallback,
) -> None:
    """Kept for manual experiments on backends that allow threaded startup."""

    def _on_loaded(*_args: object) -> None:
        _position_window(window, pygame_hwnd)

    window = create_web_menu_window(on_start_callback)
    window.events.loaded += _on_loaded

    def _start_webview() -> None:
        try:
            webview.start(debug=False)
        except Exception as exc:
            print(f"[UYARI] pywebview overlay baslatilamadi: {exc}")

    webview_thread = threading.Thread(
        target=_start_webview,
        daemon=True,
        name="WebMenuOverlay",
    )
    webview_thread.start()


def _handle_start_game() -> None:
    """JS'den gelen start_game() cagrisini Pygame event queue'ya iletir."""
    import pygame

    _ = SceneManager.get()
    pygame.event.post(
        pygame.event.Event(
            pygame.USEREVENT,
            {"action": "transition_to_lobby"},
        )
    )


def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overlay-child", action="store_true")
    parser.add_argument("--signal-file")
    parser.add_argument("--pygame-hwnd", type=int)
    args = parser.parse_args()

    if args.overlay_child:
        if not args.signal_file:
            raise SystemExit("--signal-file is required for overlay child mode")
        _run_overlay_child(Path(args.signal_file), args.pygame_hwnd)


if __name__ == "__main__":
    _main()
