import pygame
from v2.constants import Layout, Colors
from v2.ui.shop_panel import ShopPanel
from v2.ui.hand_panel import HandPanel
from v2.ui.player_hub import PlayerHub
from v2.ui.synergy_hud import SynergyHud
from v2.ui.lobby_panel import LobbyPanel
from v2.ui.timer_bar import TimerBar
from v2.ui.info_box import InfoBox
from v2.ui.widgets import FloatingTextManager

class ShopScene:
    _HOVER_DELAY_MS = 150   # 0.15 saniye - çok daha hızlı tepki

    def __init__(self):
        self.shop_panel     = ShopPanel()
        self.hand_panel     = HandPanel()
        self.player_hub     = PlayerHub()
        self.synergy_hud    = SynergyHud()
        self.lobby_panel    = LobbyPanel(player_count=8)
        self.timer_bar      = TimerBar()
        from v2.ui.income_preview import IncomePreview
        self.income_preview = IncomePreview()
        self.ft_manager     = FloatingTextManager()

        # ── FloatingText önceki durum takibi ──────────────────────
        self._prev_synergy_total: int            = 0
        self._prev_group_counts: dict[str, int]  = {
            "MIND": 0, "CONNECTION": 0, "EXISTENCE": 0
        }

        # ── World Drag State ──────────────────────────────────
        self.world_drag = {
            "is_dragging": False,
            "last_mouse_pos": (0, 0)
        }

        # ── Shared InfoBox (shop ve hand için ortak) ────────────────
        self._shop_info   = InfoBox(self.shop_panel.info_rect)
        self._hand_info   = InfoBox(self.hand_panel.info_rect)

        # ── Hover Delay State Machine ──────────────────────────
        self._hover       = {
            "panel":      None,   # "shop" | "hand" | None
            "slot_idx":   -1,
            "elapsed_ms": 0.0,
            "active":     False,  # Delay geçti mi?
        }

        # ── Drag & Drop State Machine ──────────────────────────
        self.drag_state = {
            "is_dragging":  False,
            "source_panel": None,
            "source_index": -1,
            "mouse_pos":    (0, 0),
            "card_rect":    None,
            "rotation":     0,       # 0-5: sağ tık her seferinde +1 (mod 6)
        }

        # Board Kart Animatorleri: (q,r) -> CardFlip, dest_rect her frame guncellenir
        self._board_flips: dict = {}

    def handle_event(self, event: pygame.event.Event):
        from v2.constants import GridMath

        # 0. Keyboard Controls (Camera & Zoom)
        if event.type == pygame.KEYDOWN:
            cam_speed = 40 / GridMath.camera.zoom
            zoom_step = 0.1

            # W, A, S, D: Camera Offset (Intuitive: W moves world objects down = camera up)
            if event.key == pygame.K_w: GridMath.camera.offset_y += cam_speed
            elif event.key == pygame.K_s: GridMath.camera.offset_y -= cam_speed
            elif event.key == pygame.K_a: GridMath.camera.offset_x += cam_speed
            elif event.key == pygame.K_d: GridMath.camera.offset_x -= cam_speed

            # Q, E or Plus/Minus: Zoom
            elif event.key == pygame.K_q or event.key == pygame.K_MINUS:
                old_zoom = GridMath.camera.zoom
                GridMath.camera.zoom = max(GridMath.camera.MIN_ZOOM, old_zoom - zoom_step)
                # Mouse-centered zoom
                mx, my = pygame.mouse.get_pos()
                ratio = GridMath.camera.zoom / old_zoom
                rel_x, rel_y = mx - GridMath.ORIGIN_X, my - GridMath.ORIGIN_Y
                GridMath.camera.offset_x = rel_x - ratio * (rel_x - GridMath.camera.offset_x)
                GridMath.camera.offset_y = rel_y - ratio * (rel_y - GridMath.camera.offset_y)

            elif event.key == pygame.K_e or event.key == pygame.K_PLUS or event.key == pygame.K_KP_PLUS:
                old_zoom = GridMath.camera.zoom
                GridMath.camera.zoom = min(GridMath.camera.MAX_ZOOM, old_zoom + zoom_step)
                # Mouse-centered zoom
                mx, my = pygame.mouse.get_pos()
                ratio = GridMath.camera.zoom / old_zoom
                rel_x, rel_y = mx - GridMath.ORIGIN_X, my - GridMath.ORIGIN_Y
                GridMath.camera.offset_x = rel_x - ratio * (rel_x - GridMath.camera.offset_x)
                GridMath.camera.offset_y = rel_y - ratio * (rel_y - GridMath.camera.offset_y)

            # R: Reset Camera
            elif event.key == pygame.K_r:
                GridMath.camera.offset_x = 0
                GridMath.camera.offset_y = 0
                GridMath.camera.zoom = 1.0

        # 0.1 Zoom Control (Mouse Wheel - Mouse-Centered)
        if event.type == pygame.MOUSEWHEEL:
            old_zoom = GridMath.camera.zoom
            zoom_step = 0.1
            if event.y > 0: # Zoom In
                GridMath.camera.zoom = min(GridMath.camera.MAX_ZOOM, old_zoom + zoom_step)
            else: # Zoom Out
                GridMath.camera.zoom = max(GridMath.camera.MIN_ZOOM, old_zoom - zoom_step)

            # Zoom Delta
            new_zoom = GridMath.camera.zoom
            if old_zoom != new_zoom:
                # Fare pozisyonuna göre offset'i ayarla (Mouse-Centered Zoom)
                mx, my = pygame.mouse.get_pos()
                # Dünya koordinatındaki fare pozisyonu sabit kalmalı:
                # (mx - origin - old_off) / old_zoom = (mx - origin - new_off) / new_zoom
                # new_off = mx - origin - (new_zoom / old_zoom) * (mx - origin - old_off)

                rel_x = mx - GridMath.ORIGIN_X
                rel_y = my - GridMath.ORIGIN_Y

                ratio = new_zoom / old_zoom
                GridMath.camera.offset_x = rel_x - ratio * (rel_x - GridMath.camera.offset_x)
                GridMath.camera.offset_y = rel_y - ratio * (rel_y - GridMath.camera.offset_y)
            return

        # 1. Fare Hareketi
        if event.type == pygame.MOUSEMOTION:
            if self.drag_state["is_dragging"]:
                self.drag_state["mouse_pos"] = event.pos
                return

            if self.world_drag["is_dragging"]:
                dx = event.pos[0] - self.world_drag["last_mouse_pos"][0]
                dy = event.pos[1] - self.world_drag["last_mouse_pos"][1]
                GridMath.camera.offset_x += dx
                GridMath.camera.offset_y += dy
                self.world_drag["last_mouse_pos"] = event.pos
                return

            hover_shop_idx = self.shop_panel.handle_hover(event.pos)
            hover_hand_idx = self.hand_panel.handle_hover(event.pos)

            # Hover değişimi kontrolü
            if hover_shop_idx != -1:
                if self._hover["panel"] != "shop" or self._hover["slot_idx"] != hover_shop_idx:
                    self._hover["panel"]    = "shop"
                    self._hover["slot_idx"] = hover_shop_idx
                    self._hover["elapsed_ms"] = 0.0
                    self._hover["active"]   = False
                    self._shop_info.set_card(None)
            elif hover_hand_idx != -1:
                if self._hover["panel"] != "hand" or self._hover["slot_idx"] != hover_hand_idx:
                    self._hover["panel"]    = "hand"
                    self._hover["slot_idx"] = hover_hand_idx
                    self._hover["elapsed_ms"] = 0.0
                    self._hover["active"]   = False
                    self._hand_info.set_card(None)
            else:
                if self._hover["panel"] is not None:
                    self._hover["panel"]    = None
                    self._hover["slot_idx"] = -1
                    self._shop_info.set_card(None)
                    self._hand_info.set_card(None)

        # 1.5 Sağ Tık → Drag sırasında rotate
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            if self.drag_state["is_dragging"]:
                self.drag_state["rotation"] = (self.drag_state["rotation"] + 1) % 6
                return

        # 2. Fare Butonu Bırakıldı (Drop - Bırakma Aksiyonu)
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.world_drag["is_dragging"]:
                self.world_drag["is_dragging"] = False
                return

            if self.drag_state["is_dragging"]:
                src_idx = self.drag_state["source_index"]
                drop_pos = self.drag_state["mouse_pos"]

                if self.drag_state["source_panel"] == "hand":
                    from v2.ui.hex_grid import pixel_to_axial, VALID_HEX_COORDS
                    from v2.core.game_state import GameState, ActionResult
                    q, r = pixel_to_axial(*drop_pos)
                    coord = (q, r)

                    if coord in VALID_HEX_COORDS:
                        result = GameState.get().place_card(src_idx, coord, rotation=self.drag_state["rotation"])
                        if result == ActionResult.OK:
                            # Trigger 1: kart yerleşince synergy delta float
                            placed_card = GameState.get().get_board_cards().get(coord)
                            if placed_card:
                                self._spawn_placement_float(coord, placed_card)
                            self.hand_panel.sync()
                            self.player_hub.sync()
                            self._add_board_flip(coord)
                        # Yerleştirme başarısız olsa da drag biter (snap-back)

                self.drag_state["is_dragging"] = False
                self.drag_state["source_panel"] = None
                self.drag_state["source_index"] = -1
                self.drag_state["rotation"]     = 0   # rotasyonu sıfırla
                return

        # 3. Fare Butonuna Tıklandı (Drag Başlatma veya Tıklama)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Önce Drag (Sürükle) hedefini HandPanel üzerinden kontrol et
            if not self.drag_state["is_dragging"]:
                # UI elemanlarına tıklandı mı kontrol et (Panel geçişleri için)
                on_ui = (self.shop_panel.rect.collidepoint(event.pos) or
                         self.hand_panel.rect.collidepoint(event.pos) or
                         self.player_hub.rect.collidepoint(event.pos) or
                         self.synergy_hud.rect.collidepoint(event.pos))

                if not on_ui:
                    # Boş alana tıklandı -> World Drag Başlat
                    self.world_drag["is_dragging"] = True
                    self.world_drag["last_mouse_pos"] = event.pos
                    return

                for idx, slot_rect in enumerate(self.hand_panel.card_rects):
                    if slot_rect.collidepoint(event.pos):
                        # Drag Başlat!
                        self.drag_state["is_dragging"] = True
                        self.drag_state["source_panel"] = "hand"
                        self.drag_state["source_index"] = idx
                        self.drag_state["mouse_pos"] = event.pos
                        self.drag_state["card_rect"] = pygame.Rect(slot_rect) # boyutları kopyala
                        return # Click eventini yut

        # 4. Yukarıdaki Drag&Drop durumlarından hiçbiri eşleşmediyse mevcut panellere ileti aktar
        if hasattr(self.shop_panel, "handle_event"):
            # Trigger 2/3/5 için olay tipini önceden tespit et
            _is_reroll  = False
            _buy_slot   = -1
            _buy_card   = None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.shop_panel.reroll_rect.collidepoint(event.pos):
                    _is_reroll = True
                else:
                    for _i, _sr in enumerate(self.shop_panel.card_rects):
                        if _sr.collidepoint(event.pos):
                            _buy_slot = _i
                            _buy_card = (self.shop_panel._card_names[_i]
                                         if _i < len(self.shop_panel._card_names) else None)
                            break

            if self.shop_panel.handle_event(event):
                # Reroll veya satın alma oldu — görsel olarak yenile
                self.shop_panel.sync()
                self.hand_panel.sync()
                self.player_hub.sync()

                # Trigger 5: Reroll maliyeti
                if _is_reroll:
                    rx, ry = self.shop_panel.reroll_rect.center
                    self.ft_manager.spawn(
                        "-2G", rx, ry - 10,
                        (210, 70, 55), font_size=13,
                        coord_key=("reroll",),
                    )

                # Trigger 2 / 3: Kopya milestone
                elif _buy_slot >= 0 and _buy_card:
                    try:
                        from v2.core.game_state import GameState as _GS
                        copies = _GS.get().get_copies(_buy_card, 0)
                        slot_r = self.shop_panel.card_rects[_buy_slot]
                        sx, sy = slot_r.centerx, slot_r.top + 12
                        if copies == 3:
                            self.ft_manager.spawn(
                                "★★ Kopya 3/3", sx, sy,
                                (255, 160, 30), font_size=16,
                                coord_key=(_buy_slot, "shop"),
                            )
                        elif copies == 2:
                            self.ft_manager.spawn(
                                "★ Kopya 2/3", sx, sy,
                                (255, 210, 60), font_size=14,
                                coord_key=(_buy_slot, "shop"),
                            )
                    except Exception:
                        pass

                return
        if hasattr(self.hand_panel, "handle_event"):
            if self.hand_panel.handle_event(event):
                return

    def update(self, dt_ms: float):
        """dt_ms: milisaniye cinsinden delta time (SceneManager spec). """
        # dt_ms zaten ms cinsinden gelir (clock.tick(60) → SceneManager → buraya)
        self.shop_panel.update(dt_ms)
        self.hand_panel.update(dt_ms)
        self.player_hub.sync()          # Gold / HP barı canlı güncelle
        self.synergy_hud.update(dt_ms)  # Flash animasyonları
        self.ft_manager.update(dt_ms)   # FloatingText yaşam döngüsü
        self._check_tier_milestones()   # Trigger 4: synergy tier atlayışı

        # Drag sırasında ghost slot hover fizik kilidi (deterministik)
        if self.drag_state["is_dragging"] and self.drag_state["source_panel"] == "hand":
            ghost_idx = self.drag_state["source_index"]
            self.hand_panel.handle_hover(self.drag_state["mouse_pos"], ghost_index=ghost_idx)

        # Delay timer kontrolü
        if self._hover["panel"] is not None and not self._hover["active"]:
            self._hover["elapsed_ms"] += dt_ms
            if self._hover["elapsed_ms"] >= self._HOVER_DELAY_MS:
                self._hover["active"] = True
                try:
                    from v2.core.card_database import CardDatabase
                    db = CardDatabase.get()
                except Exception:
                    db = None

                if db:
                    if self._hover["panel"] == "shop":
                        card_name = self.shop_panel._card_names[self._hover["slot_idx"]]
                        self._shop_info.set_card(db.lookup(card_name) if card_name else None)
                    elif self._hover["panel"] == "hand":
                        card_name = self.hand_panel._card_names[self._hover["slot_idx"]]
                        self._hand_info.set_card(db.lookup(card_name) if card_name else None)

        # Board kartlari: dest_rect'i kameraya gore guncelle + hover + animasyon
        if self._board_flips:
            from v2.ui.hex_grid import axial_to_pixel
            from v2.constants import GridMath
            mouse_pos = pygame.mouse.get_pos()
            zoom = GridMath.camera.zoom
            for coord, flip in self._board_flips.items():
                q, r = coord
                cx, cy = axial_to_pixel(q, r)
                w = int(GridMath.HEX_SIZE * zoom * 1.55)
                h = int(GridMath.HEX_SIZE * zoom * 1.85)
                flip.dest_rect.update(int(cx - w // 2), int(cy - h // 2), w, h)
                if flip.dest_rect.collidepoint(mouse_pos):
                    flip.hover_start()
                else:
                    flip.hover_end()
                flip.update(dt_ms)

    def _add_board_flip(self, coord: tuple) -> None:
        """Basarili place_card sonrasi o hex icin CardFlip animatoru olusturur."""
        from v2.ui.hex_grid import axial_to_pixel
        from v2.ui.card_flip import CardFlip
        from v2.core.game_state import GameState
        from v2.constants import GridMath
        import math

        card_name = GameState.get().get_board_cards().get(coord)
        if not card_name:
            return

        q, r = coord
        cx, cy = axial_to_pixel(q, r)
        zoom = GridMath.camera.zoom
        w = int(GridMath.HEX_SIZE * zoom * 1.55)
        h = int(GridMath.HEX_SIZE * zoom * 1.85)
        rect = pygame.Rect(int(cx - w // 2), int(cy - h // 2), w, h)

        try:
            from v2.assets.loader import AssetLoader
            loader = AssetLoader.get()
            back  = loader.get_card_back(card_name)
            front = loader.get_card_front(card_name)
        except Exception:
            # Fallback: dolu renk + isim
            def _fb(color):
                s = pygame.Surface((w, h), pygame.SRCALPHA)
                cx2, cy2 = w // 2, h // 2
                pts = [(cx2 + h/2 * math.cos(math.radians(60*i - 30)),
                        cy2 + h/2 * math.sin(math.radians(60*i - 30))) for i in range(6)]
                pygame.draw.polygon(s, color, pts)
                return s
            back  = _fb((38, 42, 62))
            front = _fb((20, 60, 100))

        self._board_flips[coord] = CardFlip(back, front, rect)

    def render(self, surface: pygame.Surface):
        # 1. Siberpunk Hacimli Arka Plan (Dinamik Unified Grid)
        from v2.ui.background_manager import BackgroundManager
        from v2.constants import GridMath
        from v2.ui.hex_grid import render_hex_grid, axial_to_pixel

        BackgroundManager.get().render(
            surface,
            zoom=GridMath.camera.zoom,
            offset=(GridMath.camera.offset_x, GridMath.camera.offset_y)
        )

        # 1.1 Aktif Board Hücrelerini Çiz (Premium Render)
        render_hex_grid(surface)

        # 1.2 Board kartlari — hover_progress'e gore sirala: upscale olan en uste ciksin
        from v2.core.game_state import GameState
        sorted_flips = sorted(self._board_flips.items(), key=lambda kv: kv[1].hover_progress)
        for coord, flip in sorted_flips:
            flip.render(surface)

        # 1.3 Synergy baglantiları kartlarin ÜSTÜNDE çizilir (kart assetleri altinda kalmamasi icin)
        from v2.ui.hex_grid import render_synergy_lines
        render_synergy_lines(surface, GameState.get().get_adjacency_pairs())

        if self.drag_state["is_dragging"]:
            src_panel = self.drag_state["source_panel"]
            src_idx = self.drag_state["source_index"]
            card_name = None

            if src_panel == "hand":
                card_name = self.hand_panel._card_names[src_idx]
            elif src_panel == "shop":
                card_name = self.shop_panel._card_names[src_idx]

            if card_name:
                from v2.ui.hex_grid import render_ghost_preview, render_synergy_preview
                from v2.ui.hex_grid import pixel_to_axial
                from v2.core.game_state import GameState
                drag_rot = self.drag_state["rotation"]
                render_ghost_preview(surface, card_name, self.drag_state["mouse_pos"], rotation=drag_rot)
                # Synergy önizleme: rotasyonla birlikte oluşacak synergy bağlantıları
                try:
                    hover_coord = pixel_to_axial(*self.drag_state["mouse_pos"])
                    render_synergy_preview(
                        surface,
                        hover_coord,
                        card_name,
                        GameState.get().get_board_cards(),
                        drag_rotation=drag_rot,
                        board_rotations=GameState.get().get_board_rotations(),
                    )
                except Exception:
                    pass

        # 2. Üst ve Alt Paneller (Ghosting logic dahil edildi)
        ghost_idx = self.drag_state["source_index"] if (self.drag_state["is_dragging"] and self.drag_state["source_panel"] == "hand") else -1

        self.shop_panel.render(surface)
        self.hand_panel.render(surface, ghost_index=ghost_idx)

        # 2.5 Copy count etiketleri — her kart slotunun altına
        self._render_copy_labels(surface)

        self._shop_info.render(surface)
        self._hand_info.render(surface)

        # 3. Sol Sidebar Blokları Çizimi
        self.player_hub.render(surface)
        self.synergy_hud.render(surface)

        # 3. Sağ Sidebar (Lobby / Scoreboard) Çizimi (Dependency Injection üzerinden)
        mock_players = [
            {"name": "YOU",       "hp": 150, "max_hp": 150, "gold": 10, "rank": 1},
            {"name": "Player 2",  "hp": 120, "max_hp": 150, "gold":  8, "rank": 2},
            {"name": "Player 3",  "hp": 105, "max_hp": 150, "gold":  6, "rank": 3},
            {"name": "Player 4",  "hp":  90, "max_hp": 150, "gold":  7, "rank": 4},
            {"name": "Player 5",  "hp":  75, "max_hp": 150, "gold":  5, "rank": 5},
            {"name": "Player 6",  "hp":  60, "max_hp": 150, "gold":  4, "rank": 6},
            {"name": "Player 7",  "hp":  30, "max_hp": 150, "gold":  3, "rank": 7},
            {"name": "Player 8",  "hp":  15, "max_hp": 150, "gold":  2, "rank": 8},
        ]
        self.lobby_panel.render(surface, mock_players)

        # 5. Timer Bar (Eriyen Çubuk)
        self.timer_bar.render(surface, ratio=0.65) # Mock %65 dolu atesli bar gorunumu

        # 5.5 IncomePreview — TimerBar hemen altında, tüm panellerin üstünde
        _ip_r = self.income_preview.rect
        _backdrop = pygame.Surface((_ip_r.w + 24, _ip_r.h + 8), pygame.SRCALPHA)
        _backdrop.fill((8, 10, 16, 200))
        surface.blit(_backdrop, (_ip_r.x - 12, _ip_r.y - 4))
        self.income_preview.render(surface)

        # 6. TOP LAYER (En Üst Z-INDEX): Sürüklenen Kart (Gerçek Sprite)
        # 6.1 FloatingText — drag card'ın da üstünde, mutlak en üst katman
        self.ft_manager.render(surface)

        if self.drag_state["is_dragging"]:
            src_idx = self.drag_state["source_index"]
            mx, my  = self.drag_state["mouse_pos"]
            cw, ch  = Layout.HAND_CARD_W, Layout.HAND_CARD_H

            # Orijinal flip animatörü ile render et: hover fizik (scale + lift) korunur
            if 0 <= src_idx < len(self.hand_panel._flips):
                flip = self.hand_panel._flips[src_idx]
                flip.hover_start()
                old_center = flip.dest_rect.center
                flip.dest_rect.center = (mx, my)
                flip.render(surface)
                flip.dest_rect.center = old_center
                # Not: PNG'lerin kendi neon kenarlıkları var,
                # dikdörtgen çerçeve eklenmez (altıgen şeffaflığını bozar).

    # ── FloatingText yardımcı metodları ──────────────────────────────────

    def _spawn_placement_float(self, coord: tuple, card_name: str) -> None:
        """Trigger 1: Kart board'a yerleştirilince synergy delta FloatingText."""
        from v2.ui.hex_grid import axial_to_pixel
        from v2.core.card_database import CardDatabase
        from v2.constants import STAT_TO_GROUP
        from collections import defaultdict

        # Dominant grup rengi
        dom_grp = "EXISTENCE"
        try:
            db   = CardDatabase.get()
            data = db.lookup(card_name)
            if data:
                cnt: dict = defaultdict(int)
                for stat, val in data.stats.items():
                    if val > 0:
                        g = STAT_TO_GROUP.get(stat)
                        if g:
                            cnt[g] += 1
                if cnt:
                    dom_grp = max(cnt, key=cnt.get)
        except Exception:
            pass

        color_map = {
            "MIND":       Colors.MIND,
            "CONNECTION": Colors.CONNECTION,
            "EXISTENCE":  Colors.EXISTENCE,
        }
        color = color_map.get(dom_grp, Colors.GOLD_TEXT)

        # Synergy delta
        try:
            new_state = self.synergy_hud._compute_state()
            new_syn   = new_state["total"]
            delta     = new_syn - self._prev_synergy_total
            self._prev_synergy_total = new_syn
            text = f"+{delta} SYN" if delta > 0 else "⬡ YERLEŞTİ"
        except Exception:
            text = "⬡ YERLEŞTİ"

        cx, cy = axial_to_pixel(*coord)
        self.ft_manager.spawn(
            text, cx, cy - 50, color,
            font_size=14, coord_key=coord,
        )

    def _check_tier_milestones(self) -> None:
        """Trigger 4: Synergy grup tier atlayışlarını tespit et → FloatingText."""
        from v2.constants import GridMath

        _tier_bonuses  = {2: 3, 3: 7, 4: 11, 5: 16, 6: 18}
        _tier_set      = {2, 3, 4, 5, 6}
        _group_colors  = {
            "MIND":       Colors.MIND,
            "CONNECTION": Colors.CONNECTION,
            "EXISTENCE":  Colors.EXISTENCE,
        }
        _short = {"MIND": "MIND", "CONNECTION": "CONN", "EXISTENCE": "EXST"}

        try:
            state  = self.synergy_hud._compute_state()
            counts = state["group_counts"]
            bonuses= state["group_bonus"]
        except Exception:
            return

        for grp, count in counts.items():
            prev = self._prev_group_counts.get(grp, 0)
            if count > prev and count in _tier_set:
                bonus = bonuses.get(grp, _tier_bonuses.get(count, 0))
                color = _group_colors.get(grp, Colors.GOLD_TEXT)
                text  = f"{_short.get(grp, grp)} +{bonus}pts ▲"
                x = GridMath.ORIGIN_X + GridMath.camera.offset_x
                y = GridMath.ORIGIN_Y + GridMath.camera.offset_y - 120
                self.ft_manager.spawn(
                    text, x, y, color,
                    font_size=13, coord_key=("board_center",),
                )
            self._prev_group_counts[grp] = count

    def _render_copy_labels(self, surface: "pygame.Surface") -> None:
        """Her kart slotu üzerinde 'Copies: N/3' etiketi çizer (Phase 3 item 16)."""
        import pygame
        from v2.ui import font_cache
        from v2.constants import Colors
        try:
            from v2.core.game_state import GameState
            gs = GameState.get()
        except Exception:
            return

        fnt = font_cache.mono(9)

        # ── Shop slotları ────────────────────────────────────────────
        for i, slot_rect in enumerate(self.shop_panel.card_rects):
            name = self.shop_panel._card_names[i] if i < len(self.shop_panel._card_names) else None
            if not name:
                continue
            n = gs.get_copies(name, 0)
            text  = f"Copies: {n}/3"
            color = Colors.GOLD_TEXT if n >= 3 else (200, 205, 230)
            label_rect = pygame.Rect(slot_rect.x, slot_rect.bottom - 16, slot_rect.w, 14)
            font_cache.render_text(surface, text, fnt, color, label_rect, align="center")

        # ── Hand slotları ────────────────────────────────────────────
        for i, slot_rect in enumerate(self.hand_panel.card_rects):
            name = self.hand_panel._card_names[i] if i < len(self.hand_panel._card_names) else None
            if not name:
                continue
            n = gs.get_copies(name, 0)
            text  = f"Copies: {n}/3"
            color = Colors.GOLD_TEXT if n >= 3 else (200, 205, 230)
            label_rect = pygame.Rect(slot_rect.x, slot_rect.bottom - 16, slot_rect.w, 14)
            font_cache.render_text(surface, text, fnt, color, label_rect, align="center")
