import pygame
import math
from v2.constants import Layout, Colors, Screen
from v2.ui.card_flip import CardFlip
from v2.ui import font_cache
from v2.core.game_state import GameState

_FALLBACK_BACK_COLOR  = (12, 14, 20)
_FALLBACK_FRONT_COLOR = (20, 60, 100)

def _make_fallback_surface(color: tuple, w: int, h: int) -> pygame.Surface:
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w // 2, h // 2
    radius = h / 2
    points = [(cx + radius * math.cos(math.radians(60 * i - 30)),
               cy + radius * math.sin(math.radians(60 * i - 30))) for i in range(6)]
    pygame.draw.polygon(surf, color, points)
    pygame.draw.polygon(surf, (60, 65, 75), points, 2)
    return surf


class ShopPanel:
    def __init__(self):
        # ── Ana Panel Rect (Full Width Bar) ───────────────────────────
        self.rect = pygame.Rect(0, Layout.SHOP_PANEL_Y, 1920, Layout.SHOP_PANEL_H)

        # ── 5 Kart Slotu (Merkezi alana hizalı) ───────────────────────
        self.card_rects: list[pygame.Rect] = []
        # Kartların dikeyde ortalanması: (210 - 186) / 2 = 12px padding
        start_x = Layout.CENTER_ORIGIN_X + 20 
        start_y = self.rect.y + 12
        for i in range(Layout.SHOP_SLOTS):
            cx = start_x + (Layout.SHOP_CARD_W + Layout.SHOP_CARD_GAP) * i
            self.card_rects.append(pygame.Rect(cx, start_y, Layout.SHOP_CARD_W, Layout.SHOP_CARD_H))

        # ── Info / Hover Paneli (Aksiyona yakın, orantılı) ────────────
        info_w = 340
        self.info_rect = pygame.Rect(1570, self.rect.y + 12, info_w, self.rect.h - 24)
        
        # ── Butonlar (Dikey ortalı) ──────────────────────────────────
        btn_w, btn_h = 140, 42
        btn_x = 1415 
        # Buton bloğu: 3*42 + 2*15(gap) = 156. Padding: (210 - 156)/2 = 27
        btn_y_start = self.rect.y + 27 
        
        self.reroll_rect = pygame.Rect(btn_x, btn_y_start, btn_w, btn_h)
        self.lock_rect   = pygame.Rect(btn_x, btn_y_start + 42 + 15, btn_w, btn_h)
        self.ready_rect  = pygame.Rect(btn_x, btn_y_start + 84 + 30, btn_w, btn_h)

        # ── Stats (Butonların solunda) ───────────────────────────────
        self.stats_rect = pygame.Rect(1290, self.rect.y + 27, 130, 156)
        self._probabilities = {}

        # ── DCI Tactical Shelf (Top-Attached) ──────────────────────────
        from v2.ui.ui_utils import UIUtils
        self.bg_surface = UIUtils.create_gradient_panel(
            1920, Layout.SHOP_PANEL_H,
            color_top=(15, 18, 26, 255),
            color_bottom=(10, 12, 18, 255),
            border_radius=0,
            border_color=(42, 58, 92, 255)
        )
        
        # ── Alt Parlama Hattı (DCI Rim Light) ──────────────────────────
        pygame.draw.line(self.bg_surface, (80, 140, 255, 180), (0, Layout.SHOP_PANEL_H - 1), (1920, Layout.SHOP_PANEL_H - 1), 2)
        
        # ── Animasyon & State ───────────────────────────────────────────
        self._time = 0.0
        self._last_tick = pygame.time.get_ticks()
        self._locked_state = False # Sync'i render içinde çekelim
        
        # ── Dekoratif Elementler (Alt kenara yakın) ─────────────────────
        decal_color = (55, 70, 96, 120)
        pygame.draw.line(self.bg_surface, decal_color, (12, self.rect.h - 15), (self.rect.w - 12, self.rect.h - 15), 1)

        # Sci-fi Decal Yazısı (sol, subtle)
        from v2.ui.font_cache import mono, render_text as _rt
        try:
            decal_fnt = mono(9)
        except Exception:
            pygame.font.init()
            decal_fnt = pygame.font.SysFont("Courier", 9)
        _rt(self.bg_surface, "SHOP_BAY // ONLINE", decal_fnt,
            (80, 100, 130, 120),
            pygame.Rect(14, 8, 180, 14))

        # Kart Yuvaları (Sadece içeriye doğru göçük/karanlık insets, sade tasarım)
        for s_rect in self.card_rects:
            # ShopPanel.rect referansıyla lokal/göreceli konumlara çevir
            lx = s_rect.x - self.rect.x
            ly = s_rect.y - self.rect.y
            lw, lh = s_rect.w, s_rect.h

            # İç Zemin Çukuru (Rounded inset shadow)
            pygame.draw.rect(self.bg_surface, (4, 6, 8, 180), (lx, ly, lw, lh), border_radius=4)
            # İnset derinlik hissi için çerçeve (Optional shading)
            pygame.draw.rect(self.bg_surface, (0, 0, 0, 200), (lx, ly, lw, lh), width=1, border_radius=4)

        # ── Kart isimleri: GameState'ten oku (varsa), yoksa boş ─────────
        try:
            shop_data = GameState.get().get_shop(player_index=0)
        except Exception as e:
            print(f"[ShopPanel] sync hatası: {e}")
            import traceback
            traceback.print_exc()
            shop_data = [None] * Layout.SHOP_SLOTS

        self._card_names: list[str | None] = list(shop_data[:Layout.SHOP_SLOTS])
        while len(self._card_names) < Layout.SHOP_SLOTS:
            self._card_names.append(None)

        self._flips: list[CardFlip] = []
        self._build_flips()

    def _is_evolved_card(self, card_name: str | None) -> bool:
        if not card_name:
            return False
        try:
            from v2.core.card_database import CardDatabase
            data = CardDatabase.get().lookup(card_name)
            if not data:
                return False
            return getattr(data, "rarity", None) == "E" or getattr(data, "rarity_level", None) == "E"
        except Exception:
            return False

    # ------------------------------------------------------------------ #
    def _build_flips(self) -> None:
        self._flips.clear()
        try:
            from v2.assets.loader import AssetLoader
            loader = AssetLoader.get()
            loader_ok = True
        except Exception:
            loader_ok = False

        for i, slot_rect in enumerate(self.card_rects):
            w, h = slot_rect.width, slot_rect.height
            name = self._card_names[i] if hasattr(self, "_card_names") else None
            evolved = self._is_evolved_card(name)

            if loader_ok and name:
                try:
                    front_raw = loader.get_card_front(name)
                    back_raw  = loader.get_card_back(name)
                    front = pygame.transform.scale(front_raw, (w, h))
                    back  = pygame.transform.scale(back_raw,  (w, h))
                except FileNotFoundError:
                    front = _make_fallback_surface(_FALLBACK_FRONT_COLOR, w, h)
                    back  = _make_fallback_surface(_FALLBACK_BACK_COLOR,  w, h)
            else:
                front = _make_fallback_surface(_FALLBACK_FRONT_COLOR, w, h)
                back  = _make_fallback_surface(_FALLBACK_BACK_COLOR,  w, h)

            flip = CardFlip(back, front, slot_rect, evolved=evolved,
                            evolved_color=Colors.PLATINUM)
            # Shop kartların başlangıç durumu front göster (flip_progress=1.0)
            flip.flip_progress = 1.0
            flip._flip_target = 1.0
            self._flips.append(flip)

    def assign_shop(self, card_names: list[str | None]) -> None:
        """Dükkan yenilenince tüm slotları güncelle."""
        for i, name in enumerate(card_names[:Layout.SHOP_SLOTS]):
            self._card_names[i] = name
        self._build_flips()

    def sync(self) -> None:
        """
        GameState'ten güncel dükkan verisini çek.
        Veri değiştiyse CardFlip'leri akıllıca güncelle.
        """
        try:
            new_names = GameState.get().get_shop() # Defaults to view_index
        except Exception:
            return
            
        if new_names != self._card_names:
            # Sadece satın alınmış (None) kartların CardFlip nesnelerini MockCardBox ile değiştir
            # Eğer gerçek bir reroll ise (yani isimler tamamen farklıysa) tam yenileme yap
            is_just_purchase = True
            for i in range(Layout.SHOP_SLOTS):
                if new_names[i] != self._card_names[i]:
                    if new_names[i] is not None:
                        is_just_purchase = False
                        break
                        
            if is_just_purchase:
                # Sadece satın alım olmuş (isim eskisiyle aynı veya None)
                for i in range(Layout.SHOP_SLOTS):
                    self._card_names[i] = new_names[i]
                    if new_names[i] is None and i < len(self._flips):
                        from v2.ui.card_flip import MockCardBox
                        if not isinstance(self._flips[i], MockCardBox):
                            self._flips[i] = MockCardBox(self.card_rects[i], (30, 30, 30))
            else:
                # Gerçekten kartlar değişmiş, tam yenile (Reroll, Turn Start)
                self.assign_shop(new_names)

    # ------------------------------------------------------------------ #
    # Güncelleme                                                           #
    # ------------------------------------------------------------------ #
    def update(self, dt_ms: float) -> None:
        for flip in self._flips:
            flip.update(dt_ms)

    def handle_hover(self, mouse_pos: tuple[int, int]) -> int:
        """Hover → kart yukarı kalkar ve flip başlar. Tutulan slot indeksini dön (-1 = boş)."""
        hovered_idx = -1
        for i, (slot_rect, flip) in enumerate(zip(self.card_rects, self._flips)):
            if slot_rect.collidepoint(mouse_pos):
                flip.hover_start()  # üzerindeki kart: scale-up + flip
                hovered_idx = i
            else:
                flip.hover_end()    # diğerleri: normal boyuta dön
        return hovered_idx

    # ------------------------------------------------------------------ #
    # Events                                                               #
    # ------------------------------------------------------------------ #
    def handle_event(self, event: pygame.event.Event) -> str | bool:
        """Olayı işler ve gerekirse bir sinyal döner."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            import traceback
            state = GameState.get()

            # -- READY --
            if self.ready_rect.collidepoint(event.pos):
                if state.get_phase() == "STATE_PREPARATION":
                    print("[DEBUG] >>> READY tiklandi (via ShopPanel)")
                    return "READY"

            # -- REROLL --
            if self.reroll_rect.collidepoint(event.pos):
                print("[DEBUG] >>> REROLL tiklandi")
                try:
                    result = state.reroll_market(player_index=0)
                    print(f"[DEBUG]     reroll_market -> {result}")
                except Exception as e:
                    print(f"[DEBUG] !!! REROLL HATASI: {e}")
                    traceback.print_exc()
                return True

            # -- LOCK --
            if self.lock_rect.collidepoint(event.pos):
                print("[DEBUG] >>> LOCK tiklandi")
                try:
                    state.toggle_lock_shop(player_index=0)
                    from v2.core.game_state import GameState as _GS
                    locked = getattr(_GS.get()._engine.players[0], "shop_locked", "?")
                    print(f"[DEBUG]     shop_locked -> {locked}")
                except Exception as e:
                    print(f"[DEBUG] !!! LOCK HATASI: {e}")
                    traceback.print_exc()
                return True

            # -- BUY --
            for idx, card_rect in enumerate(self.card_rects):
                if card_rect.collidepoint(event.pos):
                    card_name = self._card_names[idx] if idx < len(self._card_names) else None
                    safe_name = str(card_name).encode('ascii', 'ignore').decode('ascii')
                    print(f"[DEBUG] >>> SATIN AL: slot={idx}  kart='{safe_name}'")
                    try:
                        result = state.buy_card_from_slot(player_index=0, slot_index=idx)
                        gold = state.get_gold(0)
                        hand_count = sum(1 for n in state.get_hand(0) if n is not None)
                        print(f"[DEBUG]     buy_card_from_slot -> {result}  | altin={gold}  el={hand_count} kart")
                    except Exception as e:
                        print(f"[DEBUG] !!! SATIN ALMA HATASI: {e}")
                        traceback.print_exc()
                    return True

        return False



    # ------------------------------------------------------------------ #
    # Render                                                               #
    # ------------------------------------------------------------------ #
    def render(self, surface: pygame.Surface) -> None:
        # ShopScene'den dt verilmiyor olabilir, o yüzden iç saatle update tetikle
        now = pygame.time.get_ticks()
        dt = (now - self._last_tick) / 1000.0
        self._last_tick = now
        self._time += dt
        
        # 1. Background
        surface.blit(self.bg_surface, self.rect)

        # 2. Kart Slotları (CardFlip renderer)
        for flip in self._flips:
            flip.render(surface)

        # ── DCI Buton Grubu ────────────────────────────────────────────
        state = GameState.get()
        gold  = state.get_gold(0)
        phase = state.get_phase()
        try:
            is_locked = state._engine.players[0].shop_locked
        except: is_locked = False

        # 3. Reroll Butonu (DCI Refit)
        can_reroll = gold >= 2
        r_col = (255, 180, 50) if can_reroll else (100, 100, 100)
        self._render_dci_button(surface, self.reroll_rect, f"REROLL [2G]", r_col, can_reroll, icon_name="SYNC")

        # 4. Lock Butonu (DCI Refit)
        l_col = (255, 50, 50) if is_locked else (180, 140, 60)
        l_lbl = "LOCKED" if is_locked else "LOCK SHOP"
        self._render_dci_button(surface, self.lock_rect, l_lbl, l_col, True, icon_name="LOCK")

        # 5. Hazır Butonu (DCI Refit)
        if phase == "STATE_PREPARATION":
            self._render_dci_button(surface, self.ready_rect, "READY PHASE", (80, 255, 160), True, icon_name="READY")

        # 6. Stats (Minimal Rarity Matrix)
        # Sadece silik beyaz yazılar
        try:
            probs = state.get_rarity_probabilities()
        except Exception:
            probs = {"1": 100.0}

        row_h = 24
        sy = self.stats_rect.y + 10
        for i, r in enumerate(["1", "2", "3", "4", "5"]):
            p = probs.get(r, 0.0)
            if p <= 0 and r not in ["1", "2"]: continue
            
            txt = f"Tier {r}: %{p:.1f}"
            color = (160, 160, 180) if p > 0 else (60, 65, 80)
            font_cache.render_text(surface, txt, font_cache.mono(9), color, 
                                    pygame.Rect(self.stats_rect.x, sy + i * row_h, 150, 20), v_align="center")

    def _render_dci_button(self, surface: pygame.Surface, rect: pygame.Rect, label: str, color: tuple, enabled: bool, icon_name: str = None):
        """DCI-REFIT: Digital Combat Interface Buton Standartı (Premium Upgrade)."""
        mouse_pos = pygame.mouse.get_pos()
        is_hover = rect.collidepoint(mouse_pos) and enabled
        
        # 1. Geometri Hazırlığı (Octagon)
        w, h = rect.size
        cut = 8
        points = [
            (rect.x+cut, rect.y), (rect.right-cut, rect.y), (rect.right, rect.y+cut),
            (rect.right, rect.bottom-cut), (rect.right-cut, rect.bottom), (rect.left+cut, rect.bottom),
            (rect.left, rect.bottom-cut), (rect.left, rect.y+cut)
        ]
        
        # 2. [LAYER 1] Outer Glow (KALDIRILDI)
        
        # 3. [LAYER 2] Glass Body (Gövde)
        bg_col = (10, 15, 25, 235) if enabled else (20, 22, 28, 180)
        pygame.draw.polygon(surface, bg_col, points)
        
        # İç Yüzey Parlaması (Glass Inset)
        if enabled:
            inner_col = (*color, 20) if not is_hover else (*color, 45)
            pygame.draw.polygon(surface, inner_col, points)

        # 4. [LAYER 3] Borders & Rim Light (Okunabilirlik İçin Ton Kaydırma)
        # Kenarlığı sadece karartmak yerine, sistem lacivertine (25, 35, 55) doğru kaydırıyoruz (Hue Shift)
        # Bu, butonun rengini bir "vurgu" olarak bırakıp okumayı kolaylaştırır
        bd_col = (
            int(color[0] * 0.2 + 25 * 0.8),
            int(color[1] * 0.2 + 35 * 0.8),
            int(color[2] * 0.2 + 55 * 0.8),
            180
        ) if enabled else (50, 55, 70, 120)
        pygame.draw.polygon(surface, bd_col, points, width=1)
        
        if enabled:
            # Üst Keskin Kenar (Rim Light)
            pygame.draw.line(surface, (255, 255, 255, 60), (rect.x+cut, rect.y+1), (rect.right-cut, rect.y+1), 1)
            
            # Hover Durumunda Köşe Vurguları
            if is_hover:
                pygame.draw.polygon(surface, (255, 255, 255, 100), points, width=2)

        # 5. [LAYER 4] Label & Icon (Max Contrast)
        # Metni saf beyaza çekiyoruz ki karanlık panelde bıçak gibi keskin olsun
        lbl_col = (255, 255, 255) if enabled else (120, 125, 140)
        # İkonu bir tık daha parlak (vibrant) yapıyoruz
        icon_col = tuple(min(255, int(c * 1.1)) for c in color) if enabled else (80, 85, 100)
        
        text_rect = pygame.Rect(rect)
        if icon_name:
            icon_size = 13
            icon_y_off = (rect.h - icon_size) // 2
            # Çift gölge efekti (subtle)
            font_cache.render_icon(surface, icon_name, icon_size, icon_col, (rect.x + 10, rect.y + icon_y_off), shadow=enabled)
            text_rect.x += 16
            text_rect.w -= 16

        font_cache.render_text(surface, label, font_cache.bold(12), lbl_col, text_rect, align="center", v_align="center", shadow=enabled)
        
