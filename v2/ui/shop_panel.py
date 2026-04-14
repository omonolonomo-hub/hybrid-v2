import pygame
import math
from v2.constants import Layout, Colors
from v2.ui.card_flip import CardFlip
from v2.ui import font_cache

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
        # ── Ana Panel Rect ──────────────────────────────────────────────
        self.rect = pygame.Rect(
            Layout.CENTER_ORIGIN_X,
            Layout.SHOP_PANEL_Y,
            Layout.CENTER_W + Layout.SIDEBAR_RIGHT_W,
            Layout.SHOP_PANEL_H,
        )

        # ── 5 Kart Slotu ───────────────────────────────────────────────
        self.card_rects: list[pygame.Rect] = []
        start_x = self.rect.x + 20
        start_y = self.rect.y + 10
        for i in range(Layout.SHOP_SLOTS):
            cx = start_x + (Layout.SHOP_CARD_W + Layout.SHOP_CARD_GAP) * i
            self.card_rects.append(pygame.Rect(cx, start_y, Layout.SHOP_CARD_W, Layout.SHOP_CARD_H))

        # ── Sağ Kenar: Reroll + Lock dikey yığın — panelin sağına yaslanır
        btn_x  = self.rect.right - Layout.REROLL_BTN_W - 20
        btn_top = self.rect.y + 12
        self.reroll_rect = pygame.Rect(btn_x, btn_top, Layout.REROLL_BTN_W, Layout.REROLL_BTN_H)
        self.lock_rect   = pygame.Rect(
            btn_x,
            self.reroll_rect.bottom + 8,
            Layout.REROLL_BTN_W,
            Layout.LOCK_BTN_H,
        )

        # ── Info / Hover Paneli ────────────────────────────────────────
        info_w = Layout.SHOP_INFO_W
        info_x = self.reroll_rect.x - info_w - 14

        self.info_rect = pygame.Rect(
            info_x,
            self.rect.y + 10,
            info_w,
            self.rect.h - 20
        )

        # ── AAA Cyberpunk Gradient Arkaplan (LobbyPanel Kalitesi) ──
        from v2.ui.ui_utils import UIUtils
        self.bg_surface = UIUtils.create_gradient_panel(
            self.rect.w, self.rect.h,
            color_top=(20, 24, 34, 252),
            color_bottom=(10, 12, 18, 255),
            border_radius=8,
            border_color=(42, 58, 92, 255) # Unified soft stroke
        )

        # ── Üst Dekoratif Çizgi (panel sınırı içinde) ─────────────────────
        decal_color = (55, 70, 96, 180)
        pygame.draw.line(self.bg_surface, decal_color, (12, 5), (self.rect.w - 12, 5), 1)

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

        # ── Orta: Stats (Info ile Reroll arası) — kalan genisligin tamamı
        stats_x = self.info_rect.right + 8
        stats_w = self.reroll_rect.x - stats_x - 8
        # Stats'i dikey ortala: sadece reroll+lock yığının yuksekligi kadar
        stack_h  = self.lock_rect.bottom - self.rect.y
        self.stats_rect = pygame.Rect(stats_x, self.rect.y + 10, stats_w,
                                      min(stack_h - 12, Layout.SHOP_PANEL_H - 20))

        # ── Kart isimleri: GameState'ten oku (varsa), yoksa boş ─────────
        try:
            from v2.core.game_state import GameState
            shop_data = GameState.get().get_shop(player_index=0)
        except Exception:
            shop_data = [None] * Layout.SHOP_SLOTS

        self._card_names: list[str | None] = list(shop_data[:Layout.SHOP_SLOTS])
        while len(self._card_names) < Layout.SHOP_SLOTS:
            self._card_names.append(None)

        self._flips: list[CardFlip] = []
        self._build_flips()

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

            flip = CardFlip(back, front, slot_rect)
            # Shop kartların başlangıç durumu front göster (flip_progress=1.0)
            flip.flip_progress = 1.0
            flip._target = 1.0
            self._flips.append(flip)

    def assign_shop(self, card_names: list[str | None]) -> None:
        """Dükkan yenilenince tüm slotları güncelle."""
        for i, name in enumerate(card_names[:Layout.SHOP_SLOTS]):
            self._card_names[i] = name
        self._build_flips()

    def sync(self) -> None:
        """
        GameState'ten güncel dükkan verisini çek.
        Veri değiştiyse CardFlip'leri yeniden oluştur — her frame çağrılmamalı,
        sadece reroll/buy gibi değişim olayları sonrasında çağrılır.
        """
        try:
            from v2.core.game_state import GameState
            new_names = GameState.get().get_shop(player_index=0)
        except Exception:
            return
        if new_names != self._card_names:
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
    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            from v2.core.game_state import GameState
            state = GameState.get()

            if self.reroll_rect.collidepoint(event.pos):
                if hasattr(state, "reroll_market"):
                    state.reroll_market(player_index=0)
                return True

            if self.lock_rect.collidepoint(event.pos):
                if hasattr(state, "toggle_lock_shop"):
                    state.toggle_lock_shop(player_index=0)
                return True

            for idx, card_rect in enumerate(self.card_rects):
                if card_rect.collidepoint(event.pos):
                    if hasattr(state, "buy_card_from_slot"):
                        state.buy_card_from_slot(player_index=0, slot_index=idx)
                    return True

        return False

    # ------------------------------------------------------------------ #
    # Render                                                               #
    # ------------------------------------------------------------------ #
    def render(self, surface: pygame.Surface) -> None:
        # 1. AAA Cam Zemini ve Soketleri Tek Seferde Çiz
        surface.blit(self.bg_surface, self.rect)

        # 2. Kart Slotları (CardFlip renderer)
        for flip in self._flips:
            flip.render(surface)

        # 3. Reroll Butonu
        try:
            from v2.core.game_state import GameState
            gold = GameState.get().get_gold(0)
        except Exception:
            gold = 0
        can_reroll  = gold >= 2
        reroll_bg   = (80, 60, 20) if can_reroll else (40, 40, 40)
        reroll_bd   = Colors.GOLD_TEXT if can_reroll else (70, 70, 70)
        pygame.draw.rect(surface, reroll_bg, self.reroll_rect, border_radius=8)
        pygame.draw.rect(surface, reroll_bd, self.reroll_rect, width=1, border_radius=8)
        font_cache.render_text(
            surface, "REROLL  [2G]",
            font_cache.bold(12), reroll_bd,
            self.reroll_rect, align="center", v_align="center",
        )

        # 4. Info Paneli (Artık InfoBox renderlıyor, ShopPanel sadece statik arkaplan çizmeyebilir)
        # Sadece zemin bırakabiliriz veya ShopScene halletiği için tamamen silebiliriz.
        # InfoBox kendi zeminini çizdiği için buradan tamamen kaldırıldı.

        # 5. Stats (Gold / Turn)
        pygame.draw.rect(surface, (30, 35, 50), self.stats_rect, border_radius=8)
        pygame.draw.rect(surface, (70, 80, 100), self.stats_rect, width=1, border_radius=8)
        s_lbl1 = pygame.Rect(self.stats_rect.x + 6, self.stats_rect.y + 6, self.stats_rect.w - 12, 16)
        s_lbl2 = pygame.Rect(self.stats_rect.x + 6, self.stats_rect.y + 26, self.stats_rect.w - 12, 16)
        font_cache.render_text(surface, f"Gold: {gold}G", font_cache.bold(11),
                               Colors.GOLD_TEXT, s_lbl1)
        font_cache.render_text(surface, "Drop: R1 70%", font_cache.mono(10),
                               (160, 170, 190), s_lbl2)

        # 6. Lock Butonu
        pygame.draw.rect(surface, (120, 90, 40), self.lock_rect, border_radius=4)
        pygame.draw.rect(surface, (180, 140, 60), self.lock_rect, width=1, border_radius=4)
        font_cache.render_text(
            surface, "🔒 LOCK",
            font_cache.bold(11), (220, 180, 80),
            self.lock_rect, align="center", v_align="center",
        )
