import pygame
from collections import defaultdict
from typing import Optional, Any

from v2.constants import Colors, Layout, Paths, Screen, GridMath, STAT_TO_GROUP
from v2.core.action_result import ActionResult
from v2.core.exceptions import AutochessException
from v2.core.game_state import GameState
from v2.core.phase_machine import PhaseMachine
from v2.core.scene_manager import Scene
from v2.core.shop_controller import ShopController, ShopUIAction
from v2.ui.hand_panel import HandPanel
from v2.ui.info_box_new1 import InfoBox
from v2.ui.lobby_panel import LobbyPanel
from v2.ui.minimap_hud import MinimapHUD
from v2.ui.player_hub import PlayerHub, PlayerHubData, build_hub_data
from v2.ui.shop_panel import ShopPanel
from v2.ui.synergy_hud import SynergyHud
from v2.ui.timer_bar import TimerBar
from v2.ui.ui_feedback_manager import UIFeedbackManager
from v2.ui.copy_label_renderer import CopyLabelRenderer
from v2.assets.loader import AssetLoader
from v2.ui.background_manager import BackgroundManager
from v2.ui.hex_math import axial_to_pixel, pixel_to_axial
from v2.ui.hex_grid import (
    render_ghost_preview,
    render_hex_grid,
    render_hex_grid_cached,
    render_synergy_lines,
    render_synergy_lines_cached,
    render_synergy_preview
)
from v2.ui.hex_grid_config import HexGridConfig
from v2.ui.card_flip import CardFlip
from v2.ui.board_surface_cache import BoardSurfaceCache
from v2.ui.audio_system import AudioSystem
from v2.ui.hover_control import HoverControl
from v2.ui.drag_drop_handler import DragDropHandler
from v2.ui.camera_controller import CameraController
from v2.ui.board_renderer import BoardRenderer


class ShopScene(Scene):
    _HOVER_DELAY_MS = 150

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
        self._feedback = UIFeedbackManager()
        self._copy_renderer = CopyLabelRenderer()

        self.phase_machine = PhaseMachine()
        self.phase_machine.set_callback(self._on_phase_change)
        self.controller = ShopController(self._game_state)

        self._audio_loader = None
        self._public_state = None
        # PlayerHub view is derived from PublicState; avoid rebuilding every frame.
        self._hub_last_state = None
        self._lobby_players = []
        # Snapshot of lobby players as last rendered; used for click hit-testing
        # so UI interactions match what the player actually saw on screen.
        self._rendered_lobby_players = []
        self._income_data = (10, 150, 0, 1.0)

        # InfoBox'lar mouse takipli tooltip olarak kullanılıyor
        # Başlangıç rect'i sadece boyut için — konum set_anchor_at_mouse ile dinamik
        tooltip_rect = pygame.Rect(0, 0, 320, 440)
        self._shop_info = InfoBox(tooltip_rect)
        self._hand_info = InfoBox(tooltip_rect)
        
        # Refactored components
        self._hover_control = HoverControl(delay_ms=self._HOVER_DELAY_MS)
        self._audio = AudioSystem()
        self._drag_handler = DragDropHandler()
        self.camera = CameraController()
        self.board_renderer = BoardRenderer()
        # Board render cache (static grid + synergy geometry)
        self._board_cache = BoardSurfaceCache(Screen.W, Screen.H)
        self._hover_coord: tuple[int, int] | None = None

        self.versus_overlay = None
        self.combat_overlay = None
        self.endgame_overlay = None
        self.ready_btn_rect = self.shop_panel.ready_rect

        # Persistent surfaces to avoid per-frame allocations
        self._sidebar_bg = pygame.Surface((Layout.SIDEBAR_LEFT_W, Screen.H), pygame.SRCALPHA).convert_alpha()
        self._sidebar_bg.fill((10, 12, 18, 235))

        self.sync_view()

    @property
    def phase(self) -> str:
        return self.phase_machine.current_phase

    def on_enter(self) -> None:
        # Preload audio assets
        try:
            self._audio.preload(Paths.SFX_BUY)
            self._audio.preload(Paths.SFX_SELL)
            self._audio.preload(Paths.SFX_PLACE)
            self._audio.preload(Paths.SFX_REROLL)
            self._audio.preload(Paths.SFX_COMBAT_HIT)
            self._audio.preload(Paths.SFX_COMBAT_WIN)
            self._audio.preload(Paths.SFX_COMBAT_LOSE)
            
            # Music still handled by AssetLoader for now
            self._audio_loader = AssetLoader.get()
            self._audio_loader.preload_scene(
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

        # Hook board_mutated signal to invalidate board render cache (best-effort)
        try:
            if self._game_state and getattr(self._game_state, "_adapter", None):
                game = getattr(self._game_state._adapter, "_engine", None)
                if game is not None and hasattr(game, "signals"):
                    game.signals.board_mutated.connect(self._on_board_mutated_for_cache)
                    game.signals.milestone_reached.connect(self._on_milestone_reached)
        except Exception:
            # Signals are optional; cache will still rebuild via key checks.
            pass

    def on_exit(self) -> None:
        """Cleanup resources when exiting the scene.
        
        Nulls out heavy references to break reference cycles and allow GC
        to reclaim memory (GameState, Pygame Surfaces, UI components).
        Requirements: 2.7, 2.8
        """
        # Unhook cache signal first to avoid bound-method cycles.
        try:
            if self._game_state and getattr(self._game_state, "_adapter", None):
                game = getattr(self._game_state._adapter, "_engine", None)
                if game is not None and hasattr(game, "signals"):
                    game.signals.board_mutated.disconnect(self._on_board_mutated_for_cache)
                    game.signals.milestone_reached.disconnect(self._on_milestone_reached)
        except Exception:
            pass

        if self._game_state:
            self._game_state.cleanup()
        
        # Null out GameState reference to allow GC
        self._game_state = None
        
        # Null out controller (holds GameState reference)
        self.controller = None
        
        # Null out public state cache
        self._public_state = None
        
        # Release Pygame Surfaces
        self._sidebar_bg = None
        
        # Null out UI component references
        self.shop_panel = None
        self.hand_panel = None
        self.player_hub = None
        self.synergy_hud = None
        self.lobby_panel = None
        self.timer_bar = None
        self.minimap = None
        self._feedback = None
        
        # Null out overlay references
        self.versus_overlay = None
        self.combat_overlay = None
        self.endgame_overlay = None
        
        # Clear board renderer (CardFlip objects hold Pygame Surfaces)
        if self.board_renderer:
            self.board_renderer.clear()
        self.board_renderer = None
        
        # Null out audio loader reference
        self._audio_loader = None

    def _on_board_mutated_for_cache(self, **kwargs) -> None:
        self._board_cache.mark_board_dirty()

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

    def _get_cached_card_info(self, location: str, index: int):
        """Retrieve cached card data from _public_state.
        
        Args:
            location: The location of the card ("hand", "shop", or "board")
            index: The index/coordinate of the card
            
        Returns:
            CardDataSnapshot if found in cache, else None
        """
        state = self._current_public_state()
        if location == "hand":
            return state.active_player.hand_card_info.get(index)
        elif location == "shop":
            return state.active_player.shop_card_info.get(index)
        elif location == "board":
            return state.active_player.board_card_info.get(index)
        return None

    def _apply_phase_context(self, new_phase: str, context) -> None:
        self._public_state = context.state

        if context.removed_coords:
            for coord in context.removed_coords:
                self.board_renderer.remove(coord)

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
                from v2.constants import Config
                if Config.DEBUG_MODE:
                    # Debug modda bile doğru yoldan git - commit_human_turn() çağrılmalı
                    outcome = self.controller.handle_shop_action(ShopUIAction(kind="ready"))
                    self._public_state = outcome.state
                    self.phase_machine.transition_to("STATE_VERSUS")
                return
            elif event.key == pygame.K_r:
                self.camera.reset()
                self._board_cache.mark_camera_dirty()

        if event.type == pygame.MOUSEWHEEL:
            if self.camera.handle_scroll(event, pygame.mouse.get_pos(), (GridMath.ORIGIN_X, GridMath.ORIGIN_Y)):
                self._board_cache.mark_camera_dirty()
            return

        if event.type == pygame.MOUSEMOTION:
            if self._drag_handler.is_active:
                self._drag_handler.update_position(event.pos)
                return
            if self.camera.is_dragging:
                if self.camera.handle_drag_move(event.pos):
                    self._board_cache.mark_camera_dirty()
                return
            self._handle_hover(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and self._drag_handler.is_active:
            self._drag_handler.rotate()
            return

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.camera.is_dragging:
                self.camera.handle_drag_end()
                return
            if self._drag_handler.is_active:
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
                    self._feedback.ft_manager.spawn("-2G", rx, ry - 10, (210, 70, 55), font_size=13, coord_key=("reroll",))
                    self._audio.play(Paths.SFX_REROLL)
            elif shop_action.kind == "buy" and outcome.result == ActionResult.OK and shop_action.slot_index >= 0 and shop_action.card_name:
                buy_card = shop_action.card_name
                buy_slot = shop_action.slot_index
                self._audio.play(Paths.SFX_BUY)
                count = state.active_player.copies_by_name.get(buy_card, 0)
                slot_rect = self.shop_panel.card_rects[buy_slot]
                sx, sy = slot_rect.centerx, slot_rect.top + 12
                if count == 3:
                    self._feedback.ft_manager.spawn("COPY 3/3", sx, sy, (255, 160, 30), font_size=16, coord_key=(buy_slot, "shop"))
                elif count == 2:
                    self._feedback.ft_manager.spawn("COPY 2/3", sx, sy, (255, 210, 60), font_size=14, coord_key=(buy_slot, "shop"))
            return

        if hasattr(self.hand_panel, "handle_event") and self.hand_panel.handle_event(event):
            return

    def _handle_hover(self, mouse_pos: tuple[int, int]) -> None:
        hover_shop_idx = self.shop_panel.handle_hover(mouse_pos)
        hover_hand_idx = self.hand_panel.handle_hover(mouse_pos)
        hover_board_coord = self.board_renderer.get_hover_coord(mouse_pos)

        if hover_shop_idx != -1:
            self._hover_control.start("shop", item=hover_shop_idx)
            if not self._hover_control.is_active():
                self._shop_info.set_card(None)
            return

        if hover_hand_idx != -1:
            self._hover_control.start("hand", item=hover_hand_idx)
            if not self._hover_control.is_active():
                self._hand_info.set_card(None)
            return

        if hover_board_coord is not None:
            self._hover_control.start("board", item=hover_board_coord)
            if not self._hover_control.is_active():
                self._hand_info.set_card(None)
            return

        # No hover target
        self._hover_control.reset()
        self._shop_info.set_card(None)
        self._hand_info.set_card(None)

    def _drop_dragged_card(self) -> None:
        # drop() çağrısından ÖNCE mouse_pos'u al
        drop_pos = self._drag_handler.mouse_pos
        
        result = self._drag_handler.drop()
        if not result:
            return

        source_panel, source_idx, rotation, card_data = result
        
        if source_panel != "hand":
            return

        coord = pixel_to_axial(*drop_pos, self.camera.get_state())
        if coord in self._hex_config.valid_coords:
            outcome = self.controller.place_card_from_hand(source_idx, coord, rotation=rotation)
            if outcome.result == ActionResult.OK:
                state = self.sync_view(outcome.state)
                if outcome.placed_card:
                    self._feedback.spawn_placement(
                        coord,
                        outcome.placed_card["name"],
                        state.active_player.synergy.total,
                        self.camera.get_state(),
                    )
                self._audio.play(Paths.SFX_PLACE)

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
            target_idx = self.lobby_panel.handle_event(event, self._rendered_lobby_players)
            if target_idx is not None:
                if self._current_public_state().view_index != target_idx:
                    self.sync_view(self.controller.set_view_index(target_idx).state)
            return True

        if not on_ui:
            self.camera.handle_drag_start(event.pos)
            return True

        for idx, slot_rect in enumerate(self.hand_panel.card_rects):
            if slot_rect.collidepoint(event.pos):
                card_name = self.hand_panel.get_card_name(idx)
                
                # Use cached card data from _public_state instead of redundant DB lookup
                card_data = self._get_cached_card_info("hand", idx)
                
                # Fallback: if cache miss (shouldn't happen in normal flow), fetch from DB
                if card_data is None and card_name:
                    from v2.core.engine_adapter import EngineAdapter
                    card_data = EngineAdapter.get_card_info(card_name)
                
                self._drag_handler.start(
                    source_panel="hand",
                    source_index=idx,
                    mouse_pos=event.pos,
                    card_rect=pygame.Rect(slot_rect),
                    card_data=card_data,
                )
                return True

        return False

    def update(self, dt_ms: float):
        # Continuous camera controls
        if self.camera.update(dt_ms, pygame.key.get_pressed(), origin=(GridMath.ORIGIN_X, GridMath.ORIGIN_Y)):
            self._board_cache.mark_camera_dirty()

        # Frame başında cache'i kullan — _refresh_public_state() sadece action sonrası çağrılır.
        state = self._current_public_state()
        active_player = state.active_player
        current_board = active_player.board_cards
        cam_state = self.camera.get_state()

        # Per-frame hover coord for cheap overlay
        mq, mr = pixel_to_axial(*pygame.mouse.get_pos(), cam_state)
        self._hover_coord = (mq, mr) if (mq, mr) in self._hex_config.valid_coords else None

        # Sync and update board renderer
        self.board_renderer.sync(current_board, state, cam_state)
        self.board_renderer.update(dt_ms, cam_state, pygame.mouse.get_pos())

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
                    self.board_renderer.remove(coord)
                if outcome.next_phase:
                    self.phase_machine.transition_to(outcome.next_phase)
        elif phase == "STATE_ENDGAME" and self.endgame_overlay:
            self.endgame_overlay.update(dt_ms)
            if getattr(self.endgame_overlay, "restart_clicked", False):
                self.phase_machine.transition_to("STATE_PREPARATION")

        self.shop_panel.update(dt_ms)
        self.hand_panel.update(dt_ms)
        self.player_hub.update(dt_ms)
        # Only rebuild hub view when PublicState snapshot changes.
        if state is not self._hub_last_state:
            self._hub_last_state = state
            self.player_hub.update_view(build_hub_data(state))
        self.synergy_hud.update(dt_ms, active_player.synergy)
        self.minimap.update(dt_ms, active_player.board_cards, pygame.mouse.get_pos())
        self.lobby_panel.update(pygame.mouse.get_pos())
        self._feedback.update(dt_ms)

        self._income_data = (
            active_player.gold,
            active_player.hp,
            active_player.hud.win_streak,
            active_player.hud.interest_multiplier,
        )
        self._lobby_players = list(state.lobby_players)

        if self._drag_handler.is_active and self._drag_handler.source_panel == "hand":
            self.hand_panel.handle_hover(self._drag_handler.mouse_pos, ghost_index=self._drag_handler.source_index)

        # Update hover timer
        self._hover_control.update(dt_ms)

        # Show info box when hover is active
        if self._hover_control.is_active():
            source = self._hover_control.get_panel()
            key = self._hover_control.get_item()
            card_info = active_player.get_card_info(source, key)
            
            # Mouse pozisyonunu al ve tooltip'i konumlandır
            mx, my = pygame.mouse.get_pos()
            
            if source == "shop":
                self._shop_info.set_anchor_at_mouse(mx, my, Screen.W, Screen.H)
                self._shop_info.set_card(card_info)
            else:
                self._hand_info.set_anchor_at_mouse(mx, my, Screen.W, Screen.H)
                self._hand_info.set_card(card_info)

    def _cleanup_dead_cards(self):
        outcome = self.controller.cleanup_dead_cards()
        for coord in outcome.removed_coords:
            self.board_renderer.remove(coord)
        return self.sync_view(outcome.state)

    def sync_view(self, state=None):
        state = state or self._refresh_public_state()
        self._public_state = state
        active_player = state.active_player
        
        # Debug: Gold değerini logla
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"SYNC_VIEW: active_player.gold={active_player.gold} | hud.gold={active_player.hud.gold}")
        
        self.shop_panel.sync(active_player.shop, gold=active_player.gold, phase=state.phase)
        self.hand_panel.set_hand(active_player.hand.slots)
        self.player_hub.update_view(build_hub_data(state))
        self._hub_last_state = state
        
        # Sync board renderer
        cam_state = self.camera.get_state()
        self.board_renderer.clear()
        self.board_renderer.sync(active_player.board_cards, state, cam_state)
        
        # Invalidate copy label cache when card names change
        self._copy_renderer.invalidate()
        
        return state

    def draw(self, surface: pygame.Surface):
        # update() zaten bu frame'de state'i oluşturdu; aynı cache'i kullan.
        state = self._current_public_state()
        active_player = state.active_player
        cam_state = self.camera.get_state()

        BackgroundManager.get().render(surface, zoom=cam_state.zoom, offset=(cam_state.offset_x, cam_state.offset_y))
        render_hex_grid_cached(
            surface,
            self._board_cache,
            active_player.board_cards,
            self._hover_coord,
            cam_state,
            self._hex_config,
        )
        self.board_renderer.draw(surface)
        render_synergy_lines_cached(
            surface,
            self._board_cache,
            list(active_player.adjacency_pairs),
            active_player.board_cards,
            cam_state,
        )

        if self._drag_handler.is_active:
            src_panel = self._drag_handler.source_panel
            src_idx = self._drag_handler.source_index
            drag_rot = self._drag_handler.rotation
            card_data = self._drag_handler.card_data
            card_name = self.hand_panel.get_card_name(src_idx) if src_panel == "hand" else self.shop_panel.get_card_name(src_idx)
            
            if card_name:
                render_ghost_preview(surface, card_name, self._drag_handler.mouse_pos, rotation=drag_rot, card_data=card_data, camera=cam_state)
                try:
                    render_synergy_preview(
                        surface,
                        pixel_to_axial(*self._drag_handler.mouse_pos, cam_state),
                        card_name,
                        active_player.board_card_info, # Use pre-fetched CardData
                        drag_rotation=drag_rot,
                        board_rotations=active_player.board_rotations,
                        card_data=card_data,
                        camera=cam_state,
                    )
                except AutochessException:
                    pass

        ghost_idx = self._drag_handler.source_index if self._drag_handler.is_active and self._drag_handler.source_panel == "hand" else -1
        self.shop_panel.render(surface)
        self.hand_panel.render(surface, ghost_index=ghost_idx)
        
        # Render copy labels for both shop and hand panels
        copies_by_name = self._current_public_state().active_player.copies_by_name
        self._copy_renderer.render(
            surface,
            self.shop_panel.card_rects + self.hand_panel.card_rects,
            self.shop_panel.get_card_names() + self.hand_panel.get_card_names(),
            copies_by_name
        )

        surface.blit(self._sidebar_bg, (0, 0))
        pygame.draw.line(surface, (50, 41, 61, 100), (Layout.SIDEBAR_LEFT_W - 1, 0), (Layout.SIDEBAR_LEFT_W - 1, Screen.H), 1)  # Karbon-mor
        self.player_hub.render(surface)
        self.synergy_hud.render(surface)
        self.minimap.render(surface)

        self._rendered_lobby_players = self._lobby_players
        self.lobby_panel.render(surface, self._rendered_lobby_players)

        self.timer_bar.render(surface, ratio=0.65)
        self._feedback.render(surface)

        if self._drag_handler.is_active:
            idx = self._drag_handler.source_index
            pos = self._drag_handler.mouse_pos
            flip = self.hand_panel.get_flip(idx)
            if flip:
                old_center = flip.dest_rect.center
                flip.dest_rect.center = pos
                flip.render(surface)
                flip.dest_rect.center = old_center

        # InfoBox'lar en üstte (tooltip olarak) - overlay'lerden hemen önce
        # Drag işlemi sırasında gizle (board görünümünü engelliyor)
        if not self._drag_handler.is_active:
            self._shop_info.render(surface)
            self._hand_info.render(surface)

        if self.phase == "STATE_VERSUS" and self.versus_overlay:
            self.versus_overlay.render(surface)
        elif self.phase == "STATE_COMBAT" and self.combat_overlay:
            self.combat_overlay.render(surface)
        elif self.phase == "STATE_ENDGAME" and self.endgame_overlay:
            self.endgame_overlay.render(surface)

    def _on_milestone_reached(self, **kwargs) -> None:
        """Signal handler — milestone_reached sinyalini UIFeedbackManager'a delege eder."""
        self._feedback.on_milestone(self.camera.get_state(), **kwargs)

    def render(self, surface: pygame.Surface) -> None:
        self.draw(surface)
