import os

import pygame
import pytest

from v2.assets.loader import AssetLoader
from v2.constants import GridMath, Layout, Screen
from v2.core.card_database import CardDatabase
from v2.core.game_state import GameState
from v2.core.scene_manager import SceneManager
from v2.main import _bootstrap
from v2.mock.engine_mock import MockGame
from v2.scenes.shop import ShopScene
from v2.ui.background_manager import BackgroundManager
from v2.ui.hex_grid import VALID_HEX_COORDS
from v2.ui.income_preview import IncomePreview
from v2.ui import font_cache

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
V2_ASSETS_DIR = os.path.join(REPO_ROOT, "v2", "assets")
CARDS_JSON = os.path.join(REPO_ROOT, "assets", "data", "cards.json")


def _reset_singletons() -> None:
    GameState._instance = None
    SceneManager._instance = None
    BackgroundManager._instance = None
    AssetLoader._instance = None
    CardDatabase.reset()
    font_cache.clear_cache()
    GridMath.camera.offset_x = 0.0
    GridMath.camera.offset_y = 0.0
    GridMath.camera.zoom = 1.0


@pytest.fixture(autouse=True)
def reset_shop_scene_state():
    pygame.init()
    pygame.font.init()
    _reset_singletons()
    yield
    _reset_singletons()
    pygame.quit()


def _build_scene():
    gs = GameState.get()
    game = MockGame()
    game.initialize_deterministic_fixture()
    gs.hook_engine(game)
    scene = ShopScene()
    return gs, game, scene


def _init_card_db() -> None:
    CardDatabase.initialize(CARDS_JSON)


def _first_filled_hand_slot(scene: ShopScene) -> int:
    for idx, card_name in enumerate(scene.hand_panel._card_names):
        if card_name:
            return idx
    raise AssertionError("fixture should start with at least one card in hand")


def test_main_bootstrap_and_first_frame_smoke():
    _bootstrap()

    loader = AssetLoader.get()
    db = CardDatabase.get()
    manager = SceneManager.get()
    surface = pygame.Surface((Screen.W, Screen.H))

    manager.set_scene(ShopScene())
    manager.update(16)
    manager.draw(surface)

    assert os.path.basename(loader.base_dir) == "assets"
    assert os.path.basename(os.path.dirname(loader.base_dir)) == "v2"
    assert db.card_count > 0
    assert manager.current_scene_name == "ShopScene"


def test_valid_hand_drop_places_card_and_syncs_panels(monkeypatch):
    gs, game, scene = _build_scene()
    slot_idx = _first_filled_hand_slot(scene)
    card_name = scene.hand_panel._card_names[slot_idx]
    target_coord = (0, 0)
    target_pos = (Layout.CENTER_ORIGIN_X + 220, Layout.SHOP_PANEL_Y + 260)
    initial_float_count = scene.ft_manager.active_count

    assert target_coord in VALID_HEX_COORDS

    from v2.ui import hex_grid

    monkeypatch.setattr(hex_grid, "pixel_to_axial", lambda _x, _y: target_coord)

    scene.handle_event(
        pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=1,
            pos=scene.hand_panel.card_rects[slot_idx].center,
        )
    )
    scene.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=target_pos))
    scene.handle_event(
        pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=target_pos)
    )

    assert gs.get_board_cards()[target_coord] == card_name
    assert gs.get_board_rotations()[target_coord] == 0
    assert game.players[0].hand[slot_idx] is None
    assert scene.hand_panel._card_names[slot_idx] is None
    assert scene.player_hub._board_used == 1
    assert target_coord in scene._board_flips
    assert scene.ft_manager.active_count == initial_float_count + 1
    assert scene.drag_state["is_dragging"] is False
    assert scene.drag_state["source_panel"] is None
    assert scene.drag_state["source_index"] == -1
    assert scene.world_drag["is_dragging"] is False


def test_shop_scene_update_keeps_core_hud_in_sync_same_frame():
    _init_card_db()
    gs = GameState.get()
    game = MockGame()
    game.initialize_deterministic_fixture()
    gs.hook_engine(game)

    player = game.players[0]
    player.gold = 27
    player.hp = 61
    player.win_streak = 4
    player.total_pts = 19
    player.interest_multiplier = 1.4
    game.turn = 4

    assert gs.place_card(0, (0, 0), rotation=2).name == "OK"
    assert gs.place_card(1, (1, 0), rotation=4).name == "OK"

    scene = ShopScene()
    scene.update(16)

    expected_income = IncomePreview._compute(
        player.gold,
        player.hp,
        player.win_streak,
        gs.get_interest_multiplier(0),
    )["total"]
    synergy_state = scene.synergy_hud._compute_state()

    assert scene.shop_panel._card_names == gs.get_shop(0)
    assert scene.hand_panel._card_names == gs.get_hand(0)
    assert scene.player_hub._gold == player.gold
    assert scene.player_hub._hp == player.hp
    assert scene.player_hub._streak == player.win_streak
    assert scene.player_hub._total_pts == player.total_pts
    assert scene.player_hub._turn == game.turn
    assert scene.player_hub._board_used == len(gs.get_board_cards()) == 2
    assert scene.player_hub._next_gold == expected_income
    assert set(synergy_state["group_counts"]) == {"MIND", "CONNECTION", "EXISTENCE"}
    assert sum(synergy_state["group_counts"].values()) > 0


def test_empty_world_drag_moves_camera_and_releases_on_mouse_up():
    _, _, scene = _build_scene()
    start_pos = (
        Layout.CENTER_ORIGIN_X + Layout.CENTER_W // 2,
        (Layout.SHOP_PANEL_Y + Layout.SHOP_PANEL_H + Layout.HAND_PANEL_Y) // 2,
    )
    moved_pos = (start_pos[0] + 35, start_pos[1] + 24)

    scene.handle_event(
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=start_pos)
    )
    scene.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=moved_pos))
    scene.handle_event(
        pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=moved_pos)
    )

    assert GridMath.camera.offset_x == 35
    assert GridMath.camera.offset_y == 24
    assert scene.world_drag["is_dragging"] is False
    assert scene.drag_state["is_dragging"] is False


def test_hand_slot_click_starts_card_drag_instead_of_world_drag():
    _, _, scene = _build_scene()
    slot_idx = _first_filled_hand_slot(scene)
    click_pos = scene.hand_panel.card_rects[slot_idx].center

    scene.handle_event(
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=click_pos)
    )

    assert scene.drag_state["is_dragging"] is True
    assert scene.drag_state["source_panel"] == "hand"
    assert scene.drag_state["source_index"] == slot_idx
    assert scene.world_drag["is_dragging"] is False


def test_lobby_panel_click_does_not_start_world_drag():
    _, _, scene = _build_scene()
    click_pos = scene.lobby_panel.player_rects[0].center

    scene.handle_event(
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=click_pos)
    )

    assert scene.world_drag["is_dragging"] is False
    assert scene.drag_state["is_dragging"] is False


def test_render_passes_live_lobby_payload_from_game_state(monkeypatch):
    _, game, scene = _build_scene()
    # game.players[i].name assignment removed: real engine has no player.name
    # Identity bridge uses P{pid} format
    game.players[0].hp = 111
    game.players[1].hp = 77

    captured = {}

    def capture_lobby_players(_surface, players):
        captured["players"] = players

    monkeypatch.setattr(scene.lobby_panel, "render", capture_lobby_players)

    scene.render(pygame.Surface((Screen.W, Screen.H)))

    # game.players[0].pid is 0, getting display name "P0"
    hero_data = next((p for p in captured["players"] if p["name"] == "P0"), None)
    # game.players[1].pid is 1, getting display name "P1"
    rival_data = next((p for p in captured["players"] if p["name"] == "P1"), None)

    assert hero_data is not None
    assert hero_data["hp"] == 111
    assert rival_data is not None
    assert rival_data["hp"] == 77
