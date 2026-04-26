import pygame
from collections import defaultdict
from typing import Optional, Any

from v2.constants import Colors, Layout, Paths, Screen, GridMath, STAT_TO_GROUP, CameraState
from v2.core.action_result import ActionResult
from v2.core.exceptions import AutochessException
from v2.core.game_state import GameState
from v2.core.phase_machine import PhaseMachine
from v2.core.scene_manager import Scene
from v2.core.shop_controller import ShopController
from v2.ui.hand_panel import HandPanel
from v2.ui.info_box import InfoBox
from v2.ui.lobby_panel import LobbyPanel
from v2.ui.minimap_hud import MinimapHUD
from v2.ui.player_hub import PlayerHub, PlayerHubData
from v2.ui.shop_panel import ShopPanel
from v2.ui.synergy_hud import SynergyHud
from v2.ui.timer_bar import TimerBar
from v2.ui.widgets import FloatingTextManager
from v2.assets.loader import AssetLoader
from v2.ui.background_manager import BackgroundManager
from v2.ui.hex_grid import (
    axial_to_pixel,
    pixel_to_axial,
    render_ghost_preview,
    render_hex_grid,
    render_synergy_lines,
    render_synergy_preview
)
from v2.ui.hex_grid_config import HexGridConfig
from v2.ui.card_flip import CardFlip


class ShopScene(Scene):
    _HOVER_DELAY_MS = 150
    _TIER_SET = frozenset({2, 3, 4, 5, 6})
    _TIER_COLORS = {"MIND": Colors.MIND, "CONNECTION": Colors.CONNECTION, "EXISTENCE": Colors.EXISTENCE}
    _TIER_SHORT = {"MIND": "MIND", "CONNECTION": "CONN", "EXISTENCE": "EXST"}

    def __init__(self, game_state: Optional[GameState] = None):
        super().__init__()
        self._game_state = game_state
        self._hex_config = HexGridConfig.from_engine()
        self.shop_panel = ShopPanel()
        self.hand_panel = HandPanel()
        self.player_hub = PlayerHub()
        self.synergy_hud = SynergyHud()
        self.lobby_panel = LobbyPanel(player_count=8)
        self.timer_bar = TimerBar()
        self.minimap = MinimapHUD(Screen.W, Screen.H)
        self.ft_manager = FloatingTextManager()

        self.phase_machine = PhaseMachine()
        self.phase_machine.set_callback(self._on_phase_change)
        self.controller = ShopController(self._game_state)

        self._audio_loader = None
        self._public_state = None
        self.camera = CameraState()
        self._lobby_players = []
        self._last_lobby_players = []
        self._income_data = (10, 150, 0, 1.0)
        self._prev_synergy_total = 0
        self._prev_group_counts = {"MIND": 0, "CONNECTION": 0, "EXISTENCE": 0}
        self._seen_copy_milestones = set()

        self.world_drag = {"is_dragging": False, "last_mouse_pos": (0, 0)}
        self._shop_info = InfoBox(self.shop_panel.info_rect)
        self._hand_info = InfoBox(self.hand_panel.info_rect)
        self._hover = {"panel": None, "slot_idx": -1, "coord": None, "elapsed_ms": 0.0, "active": False}
        self.drag_state = {
            "is_dragging": False,
            "source_panel": None,
            "source_index": -1,
            "mouse_pos": (0, 0),
            "card_rect": None,
            "rotation": 0,
            "card_data": None,
        }
        self._board_flips = {}

        self.versus_overlay = None
        self.combat_overlay = None
        self.endgame_overlay = None
        self.ready_btn_rect = self.shop_panel.ready_rect

        # Persistent surfaces to avoid per-frame allocations
        self._sidebar_bg = pygame.Surface((Layout.SIDEBAR_LEFT_W, Screen.H), pygame.SRCALPHA).convert_alpha()
        self._sidebar_bg.fill((10, 12, 18, 235))

        # Text surface cache for copy labels — invalidated on sync_view()
        self._copy_label_cache: dict[tuple[str, int], pygame.Surface] = {}

        self.sync_view()

    @property
    def phase(self) -> str:
        return self.phase_machine.current_phase

    def on_enter(self) -> None:
        try:
            self._audio_loader = AssetLoader.get()
            self._audio_loader.preload_scene(
                Paths.SFX_BUY,
                Paths.SFX_SELL,
                Paths.SFX_PLACE,
                Paths.SFX_REROLL,
                Paths.SFX_COMBAT_HIT,
                Paths.SFX_COMBAT_WIN,
                Paths.SFX_COMBAT_LOSE,
                Paths.MUSIC_SHOP,
                Paths.MUSIC_COMBAT,
                Paths.MUSIC_LOBBY,
            )
        except AutochessException:
            self._audio_loader = None

        if self.controller.get_turn() == 0:
            self._apply_phase_context("STATE_PREPARATION", self.controller.handle_phase_change("STATE_PREPARATION"))
        else:
            self.sync_view()

    def on_exit(self) -> None:
        """Cleanup resources when exiting the scene."""
        if self._game_state:
            self._game_state.cleanup()

    def set_phase(self, new_phase: str) -> None:
        self.phase_machine.transition_to(new_phase)

    def _refresh_public_state(self):
        """Her zaman GameState'den yeniden inşa eder. Sadece action/phase sonrası çağrılmalı."""
        self._public_state = self.controller.refresh_public_state()
        return self._public_state

    def _current_public_state(self):
        """Cache'den döner; yoksa bir kez inşa eder. update/draw içinde kullanılmalı."""
        if self._public_state is None:
            self._public_state = self.controller.refresh_public_state()
        return self._public_state

    def _apply_phase_context(self, new_phase: str, context) -> None:
        self._public_state = context.state

        if context.removed_coords:
            for coord in context.removed_coords:
                self._board_flips.pop(coord, None)

        if new_phase == "STATE_PREPARATION":
            self.versus_overlay = None
            self.combat_overlay = None
            self.endgame_overlay = None
            self.sync_view(context.state)
            return

        if new_phase == "STATE_VERSUS":
            self.combat_overlay = None
            self.endgame_overlay = None
            from v2.ui.overlays.versus_overlay import VersusOverlay

            self.versus_overlay = VersusOverlay("Player", "Opponent", 2000)
            return

        if new_phase == "STATE_COMBAT":
            self.versus_overlay = None
            self.endgame_overlay = None
            from v2.ui.overlays.combat_overlay import CombatOverlay

            self.combat_overlay = CombatOverlay(list(context.combat_logs), 80)
            return

        if new_phase == "STATE_ENDGAME":
            self.versus_overlay = None
            self.combat_overlay = None
            from v2.ui.overlays.endgame_overlay import EndgameOverlay

            self.endgame_overlay = EndgameOverlay(list(context.endgame_stats))

    def _on_phase_change(self, new_phase: str) -> None:
        """Phase değişimi (PREPARATION <-> VERSUS <-> COMBAT)."""
        res = self.controller.handle_phase_change(new_phase)
        self._apply_phase_context(new_phase, res)

    def handle_event(self, event: pygame.event.Event):
        phase = self.phase
        if phase != "STATE_PREPARATION":
            if phase == "STATE_VERSUS" and self.versus_overlay:
                self.versus_overlay.handle_event(event)
            elif phase == "STATE_COMBAT" and self.combat_overlay:
                self.combat_overlay.handle_event(event)
            elif phase == "STATE_ENDGAME" and self.endgame_overlay:
                self.endgame_overlay.handle_event(event)
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_v:
                self.phase_machine.transition_to("STATE_VERSUS")
                return
            elif event.key == pygame.K_r:
                self.camera.offset_x = 0
                self.camera.offset_y = 0
                self.camera.zoom = 1.0

        if event.type == pygame.MOUSEWHEEL:
            self._apply_zoom(0.1 if event.y > 0 else -0.1)
            return

        if event.type == pygame.MOUSEMOTION:
            if self.drag_state["is_dragging"]:
                self.drag_state["mouse_pos"] = event.pos
                return
            if self.world_drag["is_dragging"]:
                dx = event.pos[0] - self.world_drag["last_mouse_pos"][0]
                dy = event.pos[1] - self.world_drag["last_mouse_pos"][1]
                self.camera.offset_x += dx
                self.camera.offset_y += dy
                self.world_drag["last_mouse_pos"] = event.pos
                return
            self._handle_hover(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and self.drag_state["is_dragging"]:
            self.drag_state["rotation"] = (self.drag_state["rotation"] + 1) % 6
            return

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.world_drag["is_dragging"]:
                self.world_drag["is_dragging"] = False
                return
            if self.drag_state["is_dragging"]:
                self._drop_dragged_card()
                return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._handle_mouse_down(event):
                return

        shop_action = self.shop_panel.get_action_for_event(event)
        if shop_action:
            outcome = self.controller.handle_shop_action(shop_action)
            if shop_action.kind == "ready":
                self._public_state = outcome.state
                self.phase_machine.transition_to("STATE_VERSUS")
                return

            state = self.sync_view(outcome.state)
            if shop_action.kind == "reroll":
                if outcome.result == ActionResult.OK:
                    rx, ry = self.shop_panel.reroll_rect.center
                    self.ft_manager.spawn("-2G", rx, ry - 10, (210, 70, 55), font_size=13, coord_key=("reroll",))
                    self._play_sfx(Paths.SFX_REROLL)
            elif shop_action.kind == "buy" and outcome.result == ActionResult.OK and shop_action.slot_index >= 0 and shop_action.card_name:
                buy_card = shop_action.card_name
                buy_slot = shop_action.slot_index
                self._play_sfx(Paths.SFX_BUY)
                count = state.active_player.copies_by_name.get(buy_card, 0)
                slot_rect = self.shop_panel.card_rects[buy_slot]
                sx, sy = slot_rect.centerx, slot_rect.top + 12
                if count == 3:
                    self.ft_manager.spawn("COPY 3/3", sx, sy, (255, 160, 30), font_size=16, coord_key=(buy_slot, "shop"))
                elif count == 2:
                    self.ft_manager.spawn("COPY 2/3", sx, sy, (255, 210, 60), font_size=14, coord_key=(buy_slot, "shop"))
            return

        if hasattr(self.hand_panel, "handle_event") and self.hand_panel.handle_event(event):
            return

    def _apply_zoom(self, zoom_delta: float) -> None:
        old_zoom = self.camera.zoom
        if zoom_delta > 0:
            self.camera.zoom = min(self.camera.MAX_ZOOM, old_zoom + zoom_delta)
        else:
            self.camera.zoom = max(self.camera.MIN_ZOOM, old_zoom + zoom_delta)
        new_zoom = self.camera.zoom
        if old_zoom == new_zoom:
            return

        mx, my = pygame.mouse.get_pos()
        rel_x, rel_y = mx - GridMath.ORIGIN_X, my - GridMath.ORIGIN_Y
        ratio = new_zoom / old_zoom
        self.camera.offset_x = rel_x - ratio * (rel_x - self.camera.offset_x)
        self.camera.offset_y = rel_y - ratio * (rel_y - self.camera.offset_y)

    def _handle_hover(self, mouse_pos: tuple[int, int]) -> None:
        hover_shop_idx = self.shop_panel.handle_hover(mouse_pos)
        hover_hand_idx = self.hand_panel.handle_hover(mouse_pos)
        hover_board_coord = next((coord for coord, flip in self._board_flips.items() if flip.dest_rect.collidepoint(mouse_pos)), None)

        if hover_shop_idx != -1:
            if self._hover["panel"] != "shop" or self._hover["slot_idx"] != hover_shop_idx:
                self._hover.update({"panel": "shop", "slot_idx": hover_shop_idx, "coord": None, "elapsed_ms": 0.0, "active": False})
                self._shop_info.set_card(None)
            return

        if hover_hand_idx != -1:
            if self._hover["panel"] != "hand" or self._hover["slot_idx"] != hover_hand_idx:
                self._hover.update({"panel": "hand", "slot_idx": hover_hand_idx, "coord": None, "elapsed_ms": 0.0, "active": False})
                self._hand_info.set_card(None)
            return

        if hover_board_coord is not None:
            if self._hover["panel"] != "board" or self._hover.get("coord") != hover_board_coord:
                self._hover.update({"panel": "board", "slot_idx": -1, "coord": hover_board_coord, "elapsed_ms": 0.0, "active": False})
                self._hand_info.set_card(None)
            return

        if self._hover["panel"] is not None:
            self._hover.update({"panel": None, "slot_idx": -1, "coord": None, "elapsed_ms": 0.0, "active": False})
            self._shop_info.set_card(None)
            self._hand_info.set_card(None)

    def _drop_dragged_card(self) -> None:
        if self.drag_state["source_panel"] != "hand":
            self.drag_state.update({"is_dragging": False, "source_panel": None, "source_index": -1, "rotation": 0, "card_data": None})
            return

        src_idx = self.drag_state["source_index"]
        drop_pos = self.drag_state["mouse_pos"]
        coord = pixel_to_axial(*drop_pos, self.camera)
        if coord in self._hex_config.valid_coords:
            outcome = self.controller.place_card_from_hand(src_idx, coord, rotation=self.drag_state["rotation"])
            if outcome.result == ActionResult.OK:
                state = self.sync_view(outcome.state)
                if outcome.placed_card:
                    self._spawn_placement_float(coord, outcome.placed_card["name"], state.active_player.synergy.total)
                self._play_sfx(Paths.SFX_PLACE)

        self.drag_state.update({"is_dragging": False, "source_panel": None, "source_index": -1, "rotation": 0, "card_data": None})

    def _handle_mouse_down(self, event: pygame.event.Event) -> bool:
        on_lobby = self.lobby_panel.rect.collidepoint(event.pos)
        on_ui = (
            self.shop_panel.rect.collidepoint(event.pos)
            or self.hand_panel.rect.collidepoint(event.pos)
            or self.player_hub.rect.collidepoint(event.pos)
            or self.synergy_hud.rect.collidepoint(event.pos)
            or on_lobby
        )

        if on_lobby:
            target_idx = self.lobby_panel.handle_event(event, self._last_lobby_players)
            if target_idx is not None:
                if self._current_public_state().view_index != target_idx:
                    self.sync_view(self.controller.set_view_index(target_idx).state)
            return True

        if not on_ui:
            self.world_drag.update({"is_dragging": True, "last_mouse_pos": event.pos})
            return True

        for idx, slot_rect in enumerate(self.hand_panel.card_rects):
            if slot_rect.collidepoint(event.pos):
                card_name = self.hand_panel.get_card_name(idx)
                from v2.core.engine_adapter import EngineAdapter
                card_data = EngineAdapter.get_card_info(card_name) if card_name else None
                
                self.drag_state.update(
                    {
                        "is_dragging": True,
                        "source_panel": "hand",
                        "source_index": idx,
                        "mouse_pos": event.pos,
                        "card_rect": pygame.Rect(slot_rect),
                        "card_data": card_data,
                    }
                )
                return True

        return False

    def update(self, dt_ms: float):
        # Sürekli (Continuous) Kamera Kontrolleri
        keys = pygame.key.get_pressed()
        dt_sec = dt_ms / 1000.0
        cam_speed = (1000 / self.camera.zoom) * dt_sec
        zoom_speed = 1.5 * dt_sec
        
        if keys[pygame.K_w]: self.camera.offset_y += cam_speed
        if keys[pygame.K_s]: self.camera.offset_y -= cam_speed
        if keys[pygame.K_a]: self.camera.offset_x += cam_speed
        if keys[pygame.K_d]: self.camera.offset_x -= cam_speed
        
        if keys[pygame.K_q] or keys[pygame.K_MINUS]: self._apply_zoom(-zoom_speed)
        if keys[pygame.K_e] or keys[pygame.K_PLUS] or keys[pygame.K_KP_PLUS]: self._apply_zoom(zoom_speed)

        # Frame başında cache'i kullan — _refresh_public_state() sadece action sonrası çağrılır.
        state = self._current_public_state()
        active_player = state.active_player
        current_board = active_player.board_cards

        stale_coords = [coord for coord in self._board_flips if coord not in current_board]
        for coord in stale_coords:
            del self._board_flips[coord]
        for coord in current_board:
            if coord not in self._board_flips:
                self._add_board_flip(coord, state)

        phase = self.phase
        if phase == "STATE_VERSUS" and self.versus_overlay:
            self.versus_overlay.update(dt_ms)
            if getattr(self.versus_overlay, "is_finished", False):
                self.phase_machine.transition_to("STATE_COMBAT")
        elif phase == "STATE_COMBAT" and self.combat_overlay:
            self.combat_overlay.update(dt_ms)
            if getattr(self.combat_overlay, "is_finished", False):
                outcome = self.controller.finish_combat_overlay()
                self._public_state = outcome.state
                for coord in outcome.removed_coords:
                    self._board_flips.pop(coord, None)
                if outcome.next_phase:
                    self.phase_machine.transition_to(outcome.next_phase)
        elif phase == "STATE_ENDGAME" and self.endgame_overlay:
            self.endgame_overlay.update(dt_ms)
            if getattr(self.endgame_overlay, "restart_clicked", False):
                self.phase_machine.transition_to("STATE_PREPARATION")

        self.shop_panel.update(dt_ms)
        self.hand_panel.update(dt_ms)
        self.player_hub.update(dt_ms)
        self.player_hub.update_view(self._build_hub_data(state))
        self.synergy_hud.update(dt_ms, active_player.synergy)
        self.minimap.update(dt_ms, active_player.board_cards, pygame.mouse.get_pos())
        self.lobby_panel.update(pygame.mouse.get_pos())
        self.ft_manager.update(dt_ms)
        self._check_tier_milestones()

        self._income_data = (
            active_player.gold,
            active_player.hp,
            active_player.hud.win_streak,
            active_player.hud.interest_multiplier,
        )
        self._lobby_players = list(state.lobby_players)

        if self.drag_state["is_dragging"] and self.drag_state["source_panel"] == "hand":
            self.hand_panel.handle_hover(self.drag_state["mouse_pos"], ghost_index=self.drag_state["source_index"])

        if self._hover["panel"] is not None and not self._hover["active"]:
            self._hover["elapsed_ms"] += dt_ms
            if self._hover["elapsed_ms"] >= self._HOVER_DELAY_MS:
                self._hover["active"] = True

        if self._hover["active"] and self._hover["panel"] is not None:
            source = self._hover["panel"]
            key = self._hover.get("coord") if source == "board" else self._hover["slot_idx"]
            card_info = active_player.get_card_info(source, key)
            if source == "shop":
                self._shop_info.set_card(card_info)
            else:
                self._hand_info.set_card(card_info)

        if self._board_flips:
            mouse_pos = pygame.mouse.get_pos()
            zoom = self.camera.zoom
            for coord, flip in self._board_flips.items():
                cx, cy = axial_to_pixel(*coord, self.camera)
                w = int(GridMath.HEX_SIZE * zoom * 1.55)
                h = int(GridMath.HEX_SIZE * zoom * 1.85)
                flip.dest_rect.update(int(cx - w // 2), int(cy - h // 2), w, h)
                if flip.dest_rect.collidepoint(mouse_pos):
                    flip.hover_start()
                else:
                    flip.hover_end()
                flip.update(dt_ms)

    def _cleanup_dead_cards(self):
        outcome = self.controller.cleanup_dead_cards()
        for coord in outcome.removed_coords:
            self._board_flips.pop(coord, None)
        return self.sync_view(outcome.state)

    def sync_view(self, state=None):
        state = state or self._refresh_public_state()
        self._public_state = state
        active_player = state.active_player
        self.shop_panel.sync(active_player.shop, gold=active_player.gold, phase=state.phase)
        self.hand_panel.set_hand(active_player.hand.slots)
        self.player_hub.update_view(self._build_hub_data(state))
        self._board_flips.clear()
        for coord in active_player.board_cards:
            self._add_board_flip(coord, state)
        
        # Invalidate text surface cache when card names change
        self._copy_label_cache.clear()
        
        return state

    def _add_board_flip(self, coord: tuple[int, int], state=None) -> None:
        state = state or self._current_public_state()
        item = state.active_player.board_cards.get(coord)
        if not item:
            return

        card_name = item["name"]
        cx, cy = axial_to_pixel(*coord, self.camera)
        zoom = self.camera.zoom
        w = int(GridMath.HEX_SIZE * zoom * 1.55)
        h = int(GridMath.HEX_SIZE * zoom * 1.85)
        rect = pygame.Rect(int(cx - w // 2), int(cy - h // 2), w, h)

        try:
            loader = AssetLoader.get()
            back = loader.get_card_back(card_name)
            front = loader.get_card_front(card_name)
            from v2.core.engine_adapter import EngineAdapter

            card_data = EngineAdapter.get_card_info(card_name)
            evolved = bool(card_data and card_data.rarity == "E")
        except AutochessException:
            back = self._fallback_card_surface((38, 42, 62), w, h)
            front = self._fallback_card_surface((20, 60, 100), w, h)
            evolved = False

        self._board_flips[coord] = CardFlip(back, front, rect, evolved=evolved, evolved_color=Colors.PLATINUM)

    @staticmethod
    def _fallback_card_surface(color: tuple[int, int, int], w: int, h: int) -> pygame.Surface:
        import math

        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2
        points = [
            (
                cx + h / 2 * math.cos(math.radians(60 * i - 30)),
                cy + h / 2 * math.sin(math.radians(60 * i - 30)),
            )
            for i in range(6)
        ]
        pygame.draw.polygon(surf, color, points)
        return surf.convert_alpha()

    def _build_hub_data(self, state) -> PlayerHubData:
        hud = state.active_player.hud
        return PlayerHubData(
            hp=hud.hp,
            gold=hud.gold,
            win_streak=hud.win_streak,
            total_pts=hud.total_pts,
            turn=state.turn,
            next_gold=hud.next_gold,
            board_used=len(state.active_player.board_cards),
        )

    def _play_sfx(self, sfx_name: str) -> None:
        try:
            if self._audio_loader is None:
                self._audio_loader = AssetLoader.get()
            self._audio_loader.get_sfx(sfx_name).play()
        except AutochessException:
            pass

    def draw(self, surface: pygame.Surface):
        # update() zaten bu frame'de state'i oluşturdu; aynı cache'i kullan.
        state = self._current_public_state()
        active_player = state.active_player

        BackgroundManager.get().render(surface, zoom=self.camera.zoom, offset=(self.camera.offset_x, self.camera.offset_y))
        render_hex_grid(surface, active_player.board_cards, camera=self.camera)
        for _, flip in sorted(self._board_flips.items(), key=lambda item: item[1].hover_progress):
            flip.render(surface)
        render_synergy_lines(surface, active_player.adjacency_pairs, self.camera)

        if self.drag_state["is_dragging"]:
            src_panel = self.drag_state["source_panel"]
            src_idx = self.drag_state["source_index"]
            drag_rot = self.drag_state["rotation"]
            card_data = self.drag_state["card_data"]
            card_name = self.hand_panel.get_card_name(src_idx) if src_panel == "hand" else self.shop_panel.get_card_name(src_idx)
            
            if card_name:
                render_ghost_preview(surface, card_name, self.drag_state["mouse_pos"], rotation=drag_rot, card_data=card_data, camera=self.camera)
                try:
                    render_synergy_preview(
                        surface,
                        pixel_to_axial(*self.drag_state["mouse_pos"], self.camera),
                        card_name,
                        active_player.board_card_info, # Use pre-fetched CardData
                        drag_rotation=drag_rot,
                        board_rotations=active_player.board_rotations,
                        card_data=card_data,
                        camera=self.camera,
                    )
                except AutochessException:
                    pass

        ghost_idx = self.drag_state["source_index"] if self.drag_state["is_dragging"] and self.drag_state["source_panel"] == "hand" else -1
        self.shop_panel.render(surface)
        self.hand_panel.render(surface, ghost_index=ghost_idx)
        self._render_copy_labels(surface)
        self._shop_info.render(surface)
        self._hand_info.render(surface)

        surface.blit(self._sidebar_bg, (0, 0))
        pygame.draw.line(surface, (50, 41, 61, 100), (Layout.SIDEBAR_LEFT_W - 1, 0), (Layout.SIDEBAR_LEFT_W - 1, Screen.H), 1)  # Karbon-mor
        self.player_hub.render(surface)
        self.synergy_hud.render(surface)
        self.minimap.render(surface)

        self.lobby_panel.render(surface, self._lobby_players)
        self._last_lobby_players = self._lobby_players

        self.timer_bar.render(surface, ratio=0.65)
        self.ft_manager.render(surface)

        if self.drag_state["is_dragging"]:
            idx = self.drag_state["source_index"]
            pos = self.drag_state["mouse_pos"]
            flip = self.hand_panel.get_flip(idx)
            if flip:
                old_center = flip.dest_rect.center
                flip.dest_rect.center = pos
                flip.render(surface)
                flip.dest_rect.center = old_center

        if self.phase == "STATE_VERSUS" and self.versus_overlay:
            self.versus_overlay.render(surface)
        elif self.phase == "STATE_COMBAT" and self.combat_overlay:
            self.combat_overlay.render(surface)
        elif self.phase == "STATE_ENDGAME" and self.endgame_overlay:
            self.endgame_overlay.render(surface)

    def _spawn_placement_float(self, coord: tuple[int, int], card_name: str, new_synergy_total: int | None = None) -> None:
        from v2.core.engine_adapter import EngineAdapter
        from v2.ui.hex_grid import axial_to_pixel

        dom_grp = "EXISTENCE"
        try:
            card_data = EngineAdapter.get_card_info(card_name)
            if card_data:
                counts = defaultdict(int)
                for stat, value in card_data.stats.items():
                    if value > 0:
                        group = STAT_TO_GROUP.get(stat)
                        if group:
                            counts[group] += 1
                if counts:
                    dom_grp = max(counts, key=counts.get)
        except AutochessException:
            pass

        color = {"MIND": Colors.MIND, "CONNECTION": Colors.CONNECTION, "EXISTENCE": Colors.EXISTENCE}.get(dom_grp, Colors.GOLD_TEXT)
        new_syn = new_synergy_total if new_synergy_total is not None else self._current_public_state().active_player.synergy.total
        delta = new_syn - self._prev_synergy_total
        self._prev_synergy_total = new_syn
        text = f"+{delta} SYN" if delta > 0 else "PLACED"
        cx, cy = axial_to_pixel(*coord, self.camera)
        self.ft_manager.spawn(text, cx, cy - 50, color, font_size=14, coord_key=coord)

    def _check_tier_milestones(self) -> None:
        for group_state in self._current_public_state().active_player.synergy.groups:
            group = group_state.key
            count = group_state.count
            prev = self._prev_group_counts.get(group, 0)
            if count > prev and count in self._TIER_SET:
                text = f"{self._TIER_SHORT.get(group, group)} +{group_state.bonus}pts UP"
                x = GridMath.ORIGIN_X + self.camera.offset_x
                y = GridMath.ORIGIN_Y + self.camera.offset_y - 120
                self.ft_manager.spawn(text, x, y, self._TIER_COLORS.get(group, Colors.GOLD_TEXT), font_size=13, coord_key=("board_center",))
            self._prev_group_counts[group] = count

        try:
            milestones = self._current_public_state().active_player.copy_milestones
            for milestone in milestones:
                key = (milestone.get("trigger", ""), milestone.get("card", ""))
                if key in self._seen_copy_milestones:
                    continue
                self._seen_copy_milestones.add(key)
                title = "3-COPY POWER UP" if milestone.get("trigger") == "copy_3" else "2-COPY POWER UP"
                x = GridMath.ORIGIN_X + self.camera.offset_x
                y = GridMath.ORIGIN_Y + self.camera.offset_y - 90
                self.ft_manager.spawn(title, x, y, Colors.PLATINUM, font_size=15, coord_key=("copy_strengthen", milestone.get("card")))
        except AutochessException:
            pass

    def _render_copy_labels(self, surface: pygame.Surface) -> None:
        from v2.ui import font_cache

        font = font_cache.mono(9)
        copies_by_name = self._current_public_state().active_player.copies_by_name
        
        # Render shop copy labels
        for slot_rect, name in zip(self.shop_panel.card_rects, self.shop_panel.get_card_names()):
            if name:
                count = copies_by_name.get(name, 0)
                cache_key = (name, count)
                
                # Check cache first
                if cache_key not in self._copy_label_cache:
                    # Render to cache
                    text = f"Copies: {count}/3"
                    color = Colors.GOLD_TEXT if count >= 3 else (200, 205, 230)
                    self._copy_label_cache[cache_key] = font.render(text, True, color)
                
                # Blit cached surface
                text_surf = self._copy_label_cache[cache_key]
                tw, th = text_surf.get_size()
                x = slot_rect.x + (slot_rect.w - tw) // 2
                y = slot_rect.bottom - 16 + (14 - th) // 2
                surface.blit(text_surf, (x, y))
        
        # Render hand copy labels
        for slot_rect, name in zip(self.hand_panel.card_rects, self.hand_panel.get_card_names()):
            if name:
                count = copies_by_name.get(name, 0)
                cache_key = (name, count)
                
                # Check cache first
                if cache_key not in self._copy_label_cache:
                    # Render to cache
                    text = f"Copies: {count}/3"
                    color = Colors.GOLD_TEXT if count >= 3 else (200, 205, 230)
                    self._copy_label_cache[cache_key] = font.render(text, True, color)
                
                # Blit cached surface
                text_surf = self._copy_label_cache[cache_key]
                tw, th = text_surf.get_size()
                x = slot_rect.x + (slot_rect.w - tw) // 2
                y = slot_rect.bottom - 16 + (14 - th) // 2
                surface.blit(text_surf, (x, y))

    def render(self, surface: pygame.Surface) -> None:
        self.draw(surface)
