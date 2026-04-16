"""
test_shop_scene_phase_machine.py
═══════════════════════════════════════════════════════════════════════════════
ShopScene Phase State Machine — AAA TDD Contract Testleri

Bu dosya, ShopScene'in Phase State Machine'ini (PREPARATION → VERSUS → COMBAT
→ PREPARATION/ENDGAME) yönetmesi gereken davranışları kontrol eder.

Mimari Kuralı:
- ShopScene oyunun ÖLÜMSüz ana tahtasıdır.
- VersusOverlay, CombatOverlay, EndgameOverlay birer Popup'tır;
  onları açıp kapatan ShopScene'in set_phase() metodudur.
- Bu testler KASITLI OLARAK kırmızı (RED) fazda başlar.
  ShopScene.set_phase(), STATE_PREPARATION, STATE_VERSUS, STATE_COMBAT,
  STATE_ENDGAME henüz implement edilmemiştir.

TDD Akışı:
  RED  → Bu testler çalışır, hepsi FAIL eder   (şu an)
  GREEN → Task A'da ShopScene'e state machine eklenir
  REFACTOR → Overlay'ler bağlanır
"""

import os
import pygame
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from v2.core.game_state import GameState
from v2.core.scene_manager import SceneManager
from v2.mock.engine_mock import MockGame
from v2.scenes.shop import ShopScene
from v2.ui.background_manager import BackgroundManager
from v2.assets.loader import AssetLoader
from v2.core.card_database import CardDatabase
from v2.constants import GridMath, Screen

CARDS_JSON = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                          "assets", "data", "cards.json")


# ─── Fixtures ────────────────────────────────────────────────────────────────

def _reset_singletons():
    GameState._instance = None
    SceneManager._instance = None
    BackgroundManager._instance = None
    AssetLoader._instance = None
    CardDatabase.reset()
    GridMath.camera.offset_x = 0.0
    GridMath.camera.offset_y = 0.0
    GridMath.camera.zoom = 1.0


@pytest.fixture(autouse=True)
def clean_state():
    _reset_singletons()
    pygame.init()
    try:
        from v2.ui import font_cache
        font_cache.clear_cache()
    except Exception:
        pass
    pygame.display.set_mode((Screen.W, Screen.H), pygame.NOFRAME)
    yield
    _reset_singletons()
    pygame.quit()


def _build_scene():
    """GameState + MockGame ile donanmış ShopScene oluşturur."""
    gs = GameState.get()
    game = MockGame()
    game.initialize_deterministic_fixture()
    gs.hook_engine(game)
    scene = ShopScene()
    return gs, game, scene


# ─── 1. Başlangıç Durumu ────────────────────────────────────────────────────

def test_shopscene_starts_in_preparation_state():
    """
    Arrange: ShopScene oluşturuldu.
    Act:     phase alanı okundu.
    Assert:  Başlangıç fazı STATE_PREPARATION olmalı.
    """
    _, _, scene = _build_scene()

    assert scene.phase == "STATE_PREPARATION"


# ─── 2. Faz Geçişleri ────────────────────────────────────────────────────────

def test_shopscene_set_phase_changes_state_to_versus():
    """
    Arrange: ShopScene PREPARATION'da.
    Act:     set_phase("STATE_VERSUS") çağrıldı.
    Assert:  scene.phase == "STATE_VERSUS"
    """
    _, _, scene = _build_scene()

    scene.set_phase("STATE_VERSUS")

    assert scene.phase == "STATE_VERSUS"


def test_shopscene_set_phase_changes_state_to_combat():
    """
    Arrange: ShopScene herhangi bir fazda.
    Act:     set_phase("STATE_COMBAT") çağrıldı.
    Assert:  scene.phase == "STATE_COMBAT"
    """
    _, _, scene = _build_scene()

    scene.set_phase("STATE_COMBAT")

    assert scene.phase == "STATE_COMBAT"


def test_shopscene_set_phase_changes_state_to_endgame():
    """
    Arrange: ShopScene herhangi bir fazda.
    Act:     set_phase("STATE_ENDGAME") çağrıldı.
    Assert:  scene.phase == "STATE_ENDGAME"
    """
    _, _, scene = _build_scene()

    scene.set_phase("STATE_ENDGAME")

    assert scene.phase == "STATE_ENDGAME"


# ─── 3. Input Bloklama ───────────────────────────────────────────────────────

def test_shopscene_blocks_reroll_click_during_versus_state():
    """
    Arrange: ShopScene STATE_VERSUS'a geçti.
    Act:     Reroll butonunun üstüne MOUSEBUTTONDOWN event'i gönderildi.
    Assert:  GameState.reroll() ASLA çağrılmadı (input bloklandı).

    Bu, sahne geçişi olmadan ShopScene'in inputu susturduğunu kanıtlar.
    """
    from v2.constants import Layout
    gs, game, scene = _build_scene()
    scene.set_phase("STATE_VERSUS")

    click_pos = (Layout.REROLL_BTN_X + 10, Layout.REROLL_BTN_Y + 10)
    event = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, button=1, pos=click_pos
    )

    with patch.object(gs, "reroll_market") as mock_reroll:
        scene.handle_event(event)
        mock_reroll.assert_not_called()


def test_shopscene_blocks_buy_click_during_combat_state():
    """
    Arrange: ShopScene STATE_COMBAT'a geçti.
    Act:     Shop slot'larından birine MOUSEBUTTONDOWN gönderildi.
    Assert:  GameState.buy_card() ASLA çağrılmadı.
    """
    from v2.constants import Layout
    gs, game, scene = _build_scene()
    scene.set_phase("STATE_COMBAT")

    # Simulasyon: Dükkanın içine bir tıklama atalım
    click_pos = (Layout.CENTER_ORIGIN_X + 100, Layout.SHOP_PANEL_Y + 100)
    event = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, button=1, pos=click_pos
    )

    with patch.object(gs, "buy_card") as mock_buy:
        scene.handle_event(event)
        mock_buy.assert_not_called()


# ─── 4. Overlay Aktivasyonu ──────────────────────────────────────────────────

def test_shopscene_activates_versus_overlay_when_state_is_versus(monkeypatch):
    """
    Arrange: ShopScene STATE_VERSUS'a geçirildi.
    Act:     render() / draw() çağrıldı.
    Assert:  VersusOverlay.render() en az bir kez çağrıldı.

    Mock Render: font_cache.render_text yerine VersusOverlay.render'ı izleriz.
    """
    _, _, scene = _build_scene()
    scene.set_phase("STATE_VERSUS")

    surface = pygame.Surface((Screen.W, Screen.H))

    # VersusOverlay henüz var (stub) — render'ının çağrıldığını izle
    if not hasattr(scene, "versus_overlay") or scene.versus_overlay is None:
        pytest.skip("versus_overlay henüz ShopScene'e bağlanmadı — Task A")

    with patch.object(scene.versus_overlay, "render") as mock_render:
        scene.render(surface)
        mock_render.assert_called_once_with(surface)


def test_shopscene_activates_combat_overlay_when_state_is_combat(monkeypatch):
    """
    Arrange: ShopScene STATE_COMBAT'a geçirildi.
    Act:     draw() çağrıldı.
    Assert:  CombatOverlay.render() en az bir kez çağrıldı.
    """
    _, _, scene = _build_scene()
    scene.set_phase("STATE_COMBAT")

    surface = pygame.Surface((Screen.W, Screen.H))

    if not hasattr(scene, "combat_overlay") or scene.combat_overlay is None:
        pytest.skip("combat_overlay henüz ShopScene'e bağlanmadı — Task A")

    with patch.object(scene.combat_overlay, "render") as mock_render:
        scene.render(surface)
        mock_render.assert_called_once_with(surface)


# ─── 5. Otomatik Faz İlerlemesi ──────────────────────────────────────────────

def test_shopscene_transitions_to_combat_when_versus_overlay_finishes():
    """
    Arrange: ShopScene STATE_VERSUS, VersusOverlay.is_finished = True.
    Act:     update(dt) çağrıldı.
    Assert:  scene.phase == "STATE_COMBAT"

    Kritik: Overlay'in bitiş sinyali ShopScene tarafından dinlenmeli.
    """
    _, _, scene = _build_scene()
    scene.set_phase("STATE_VERSUS")

    if not hasattr(scene, "versus_overlay") or scene.versus_overlay is None:
        pytest.skip("versus_overlay henüz ShopScene'e bağlanmadı — Task A")

    scene.versus_overlay.is_finished = True
    scene.update(16)

    assert scene.phase == "STATE_COMBAT"


def test_shopscene_returns_to_preparation_after_combat_if_game_continues():
    """
    Arrange: ShopScene STATE_COMBAT, CombatOverlay bitti, oyun devam ediyor.
    Act:     update(dt) çağrıldı.
    Assert:  scene.phase == "STATE_PREPARATION"

    GameState.get_alive_pids() >= 2 olduğundan oyun devam eder.
    """
    gs, game, scene = _build_scene()
    scene.set_phase("STATE_COMBAT")

    if not hasattr(scene, "combat_overlay") or scene.combat_overlay is None:
        pytest.skip("combat_overlay henüz ShopScene'e bağlanmadı — Task A")

    scene.combat_overlay.is_finished = True

    # 8 oyuncu hayatta → endgame koşulu yok
    with patch.object(gs, "get_alive_pids", return_value=[0, 1, 2, 3, 4, 5, 6, 7]):
        scene.update(16)

    assert scene.phase == "STATE_PREPARATION"


def test_shopscene_transitions_to_endgame_when_only_one_player_remains():
    """
    Arrange: ShopScene STATE_COMBAT, CombatOverlay bitti, 1 oyuncu kaldı.
    Act:     update(dt) çağrıldı.
    Assert:  scene.phase == "STATE_ENDGAME"
    """
    gs, game, scene = _build_scene()
    scene.set_phase("STATE_COMBAT")

    if not hasattr(scene, "combat_overlay") or scene.combat_overlay is None:
        pytest.skip("combat_overlay henüz ShopScene'e bağlanmadı — Task A")

    scene.combat_overlay.is_finished = True

    # Sadece 1 oyuncu hayatta → endgame!
    with patch.object(gs, "get_alive_pids", return_value=[0]):
        scene.update(16)

    assert scene.phase == "STATE_ENDGAME"


# ─── 6. Single-Fire Kuralı ───────────────────────────────────────────────────

def test_shopscene_combat_phase_fires_exactly_once_on_state_combat_entry():
    """
    Arrange: ShopScene STATE_COMBAT'a girdi.
    Act:     update() ÜÇ KEZ çağrıldı.
    Assert:  engine.combat_phase() tam 1 kez çağrıldı, 3 kez DEĞİL.

    Bu test "double-combat" sessiz hatasını önler. combat_phase() idempotent
    değildir; iki kez çağrılırsa HP iki kez düşer. Guard zorunludur.
    """
    gs, game, scene = _build_scene()

    with patch.object(game, "combat_phase") as mock_combat:
        scene.set_phase("STATE_COMBAT")
        scene.update(16)
        scene.update(16)
        scene.update(16)

        assert mock_combat.call_count == 1, (
            f"combat_phase() {mock_combat.call_count} kez çağrıldı, "
            "tam 1 kez çağrılmalıydı!"
        )
