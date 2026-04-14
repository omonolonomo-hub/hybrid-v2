"""
================================================================
  ⚠️  DEPRECATED - MIGRATION IN PROGRESS  ⚠️
================================================================
  This file is being migrated to Scene-based architecture.
  Use main.py with USE_SCENE_ARCHITECTURE=True instead.
  
  See MIGRATION.md for details on the migration plan.
================================================================

  Autochess Hybrid - run_game.py (Legacy)
  Oyunu başlat:  python run_game.py
================================================================
  Kontroller:
    SPACE      → tur ilerlet (önce Shop ekranı açılır)
    S          → Shop ekranını manuel aç
    F          → hızlı mod (Shop atlanır, otomatik tur)
    1-8        → oyuncular arası geçiş
    R          → yeni oyun  |  seçili kart varken: döndür (60°)
    ESC        → seçimi iptal et / çıkış

  Mouse:
    Sol tık el kartı  → kartı seç (sarı çerçeve)
    Sol tık boş hex   → seçili kartı o hexe yerleştir (KİLİTLENİR)
    Sağ tık           → seçili kartı döndür (60°)
    [Yerleştirilen kartlar geri alınamaz / taşınamaz]

  Kart yerleştirme:
    • Her hex'e en fazla 1 kart
    • Bir kez yerleştirilen kart kilitlenir
    • Yerleştirmeden önce R veya sağ tık ile yönünü ayarla
    • Tooltip'te her kenarın yönü (N/NE/SE/S/SW/NW) görünür
================================================================
"""

import sys
import os
from collections import Counter
import pygame

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from engine_core.card        import get_card_pool
from engine_core.player      import Player
from engine_core.game        import Game
from engine_core.board       import combat_phase, BOARD_COORDS
from engine_core.constants   import STRATEGIES, MARKET_REFRESH_COST, PLACE_PER_TURN, STAT_TO_GROUP
from engine_core.passive_trigger import trigger_passive, clear_passive_trigger_log
from ui.board_renderer_v3 import (BoardRendererV3 as BoardRenderer, hex_to_pixel, pixel_to_hex, HEX_SIZE)
from ui.renderer_v3 import (CyberRendererV3 as CyberRenderer, GROUP_COLORS, RARITY_COLORS)
from ui.renderer import (COLOR_BG, COLOR_TEXT, COLOR_TEXT_DIM, STRATEGY_COLORS)
from ui.screens.shop_screen  import ShopScreen
from ui.screens.lobby_screen import LobbyScreen
from ui.card_meta import get_passive_desc
from ui.hud_renderer import hp_color, _active_synergy_counts, draw_player_info, draw_player_panel, draw_synergy_hud, draw_combat_breakdown, draw_turn_popup, draw_game_over, draw_passive_buff_panel, draw_hand_panel, draw_cyber_victorian_hud

# ── Pencere ───────────────────────────────────────────────────
W, H       = 1600, 960
FPS        = 60
TITLE      = "Autochess Hybrid  // Neon Circuit"
BOARD_ORIGIN = (800, H // 2 - 10)   # ← ortalandı (640→800)

# ── Renkler ───────────────────────────────────────────────────
C_PANEL  = ( 16,  20,  34)
C_LINE   = ( 42,  58,  92)
C_ACCENT = (  0, 242, 255)
C_HP_OK  = ( 70, 225, 140)
C_HP_LOW = (255,  95, 110)
C_WHITE  = (245, 245, 255)
C_DIM    = (130, 140, 170)
C_GOLD   = (255, 204,   0)
C_SELECT = (255,   0, 255)   # seçili kart çerçevesi
C_LOCKED = (255, 180,  40)   # kilitli kart rengi

# El kartı paneli sabitleri
HAND_PANEL_X  = 20           # sol kenar
HAND_PANEL_Y  = 430          # dikey başlangıç
HAND_CARD_W   = 210
HAND_CARD_H   = 70
HAND_CARD_GAP = 6


# ── Cyber-Victorian HUD renkler ──────────────────────────────
C_BRONZE = (150,  80,  40)
C_RUST   = ( 60,  30,  20)
C_MAGENTA = (255,   0, 150)


def build_game(strategies: list = None):
    import random
    rng  = random.Random()
    pool = get_card_pool()
    if strategies is None:
        strategies = STRATEGIES[:]
        rng.shuffle(strategies)
    players = [Player(pid=i, strategy=strategies[i]) for i in range(len(strategies))]
    game = Game(
        players,
        verbose=False,
        rng=rng,
        trigger_passive_fn=trigger_passive,
        combat_phase_fn=combat_phase,
        card_pool=pool,
    )
    return game




def _draw_synergy_hud_legacy(surface, player, fonts):
    """Board altındaki aktif/potansiyel sinerji paneli."""
    counts = _active_synergy_counts(player)
    meta = [
        ("EXISTENCE", "EX", GROUP_COLORS.get("EXISTENCE", C_ACCENT)),
        ("MIND", "MN", GROUP_COLORS.get("MIND", C_ACCENT)),
        ("CONNECTION", "CN", GROUP_COLORS.get("CONNECTION", C_ACCENT)),
    ]

    box_w = 140
    gap = 14
    total_w = len(meta) * box_w + (len(meta) - 1) * gap
    start_x = (surface.get_width() - total_w) // 2
    y = surface.get_height() - 92

    header = fonts["xs_bold"].render("ACTIVE_SYNERGIES", True, C_ACCENT)
    surface.blit(header, (start_x, y - 22))

    for i, (group, icon, color) in enumerate(meta):
        cnt = counts.get(group, 0)
        alpha = 255 if cnt > 0 else 70
        rect = pygame.Rect(start_x + i * (box_w + gap), y, box_w, 32)

        bg = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(bg, (18, 24, 44, max(45, alpha // 3)), bg.get_rect(), border_radius=6)
        pygame.draw.rect(bg, (*color, alpha), bg.get_rect(), width=1, border_radius=6)
        surface.blit(bg, rect)

        txt_col = color if cnt > 0 else (110, 120, 140)
        text = fonts["xs_bold"].render(f"{icon}  {cnt}", True, txt_col)
        surface.blit(text, (rect.x + 12, rect.y + 8))


# ── El kartı dikdörtgenlerini hesapla ─────────────────────────
def _hand_card_rects(hand_size: int):
    rects = []
    for i in range(hand_size):
        y = HAND_PANEL_Y + i * (HAND_CARD_H + HAND_CARD_GAP)
        rects.append(pygame.Rect(HAND_PANEL_X, y, HAND_CARD_W, HAND_CARD_H))
    return rects


# ── El panelini çiz ───────────────────────────────────────────

def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption(TITLE)
    clock  = pygame.time.Clock()

    def _font(name, size, bold=False):
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            return pygame.font.SysFont("consolas", size, bold=bold)

    fonts = {
        "title":   _font("bahnschrift", 28, bold=True),
        "lg":      _font("consolas", 24, bold=True),
        "md":      _font("consolas", 16),
        "md_bold": _font("consolas", 16, bold=True),
        "sm":      _font("consolas", 13),
        "sm_bold": _font("consolas", 13, bold=True),
        "xs":      _font("consolas", 12),
        "xs_bold": _font("consolas", 12, bold=True),
        "icon":    _font("segoeuisymbol", 18, bold=True),
    }
    font_lg = fonts["lg"]
    font_md = fonts["md"]
    font_sm = fonts["sm"]
    cyber   = CyberRenderer(fonts)

    game        = build_game(LobbyScreen(screen).run())
    view_player = 0
    fast_mode   = False
    fast_timer  = 0
    FAST_DELAY  = 600

    renderer = BoardRenderer(BOARD_ORIGIN, game.players[view_player].strategy,
                             cyber_renderer=cyber)
    renderer.init_fonts()

    game_over  = False
    winner     = None
    status_msg = "SPACE → tur  |  S → Shop  |  F → hız  |  1-8 → oyuncu"

    # ── Kart yerleştirme state ────────────────────────────────
    selected_hand_idx  = None   # seçili el kartı indeksi
    pending_rotation   = 0      # yerleştirme öncesi geçici rotasyon (0-5)
    placed_this_turn   = 0      # bu turda kaç kart yerleştirildi (PLACE_PER_TURN sınırı)

    # Her oyuncu için kilitli hexler: pid -> set of (q,r)
    # Bir kez yerleştirilen kartın hex'i kilitlenir
    locked_coords_per_player = {p.pid: set() for p in game.players}

    # ── Popup state ───────────────────────────────────────────
    popup_timer    = 0
    POPUP_DURATION = 3000
    popup_data     = None
    last_breakdown = None

    # ─────────────────────────────────────────────────────────
    def open_shop_for_player(player: Player):
        nonlocal selected_hand_idx, pending_rotation
        selected_hand_idx = None
        pending_rotation  = 0
        market = game.market
        while True:
            window = market.deal_market_window(player, 5)
            shop   = ShopScreen(screen, game, player, window, renderer=cyber, fonts=fonts)
            result = shop.run()
            if result == "refresh":
                cost = MARKET_REFRESH_COST
                if player.gold >= cost:
                    player.gold -= cost
                    player.stats["gold_earned"] -= cost
                    player.stats["market_rolls"] = player.stats.get("market_rolls", 0) + 1
                    market._return_window(player.pid)
                    continue
                else:
                    break
            else:
                bought_names = getattr(player, "_window_bought", [])
                bought_cards = [c for c in player.hand if c.name in bought_names]
                market.return_unsold(player, bought=bought_cards)
                break

    def step_turn(with_shop: bool = True):
        nonlocal game_over, winner, status_msg
        nonlocal popup_timer, popup_data, last_breakdown
        nonlocal selected_hand_idx, pending_rotation, placed_this_turn

        selected_hand_idx = None
        pending_rotation  = 0
        placed_this_turn  = 0   # her yeni turda sıfırla

        alive = [p for p in game.players if p.alive]
        if len(alive) <= 1 or game.turn >= 50:
            game_over = True
            winner    = max(game.players, key=lambda p: p.hp)
            status_msg = (f"OYUN BİTTİ  →  Kazanan: P{winner.pid+1}"
                          f" ({winner.strategy})  HP: {winner.hp}")
            return

        clear_passive_trigger_log()

        if with_shop and not fast_mode:
            player = game.players[view_player]
            if player.alive:
                player.income()
                open_shop_for_player(player)
                player.apply_interest()
                player.check_copy_strengthening(
                    game.turn + 1, trigger_passive_fn=trigger_passive)

            game.turn += 1

            for p in game.players:
                if not p.alive or p.pid == view_player:
                    continue
                window_ai = game.market.deal_market_window(p, 5)
                p.income()
                from engine_core.ai import AI
                AI.buy_cards(p, window_ai, market_obj=game.market,
                             rng=game.rng, trigger_passive_fn=trigger_passive)
                game.market.return_unsold(p)
                p.apply_interest()
                card_by_name = {c.name: c for c in game.card_pool}
                p.check_evolution(market=game.market, card_by_name=card_by_name)
                AI.place_cards(p, rng=game.rng)
                p.check_copy_strengthening(
                    game.turn, trigger_passive_fn=trigger_passive)

            game.combat_phase()

            # Tur sonunda kilitleri sıfırla (yeni tura temiz başla)
            for pid in locked_coords_per_player:
                locked_coords_per_player[pid] = set()

        else:
            game.preparation_phase()
            game.combat_phase()
            for pid in locked_coords_per_player:
                locked_coords_per_player[pid] = set()

        status_msg = (f"Turn {game.turn}  |  SPACE: tur  |"
                      f"  S: shop  |  F: hız  |  1-8: oyuncu")

        popup_timer = POPUP_DURATION
        popup_data  = list(getattr(game, "last_combat_results", []))
        last_breakdown = None
        for r in popup_data:
            if r.get("pid_a") == view_player or r.get("pid_b") == view_player:
                last_breakdown = r
                break

    # ─────────────────────────────────────────────────────────
    running = True
    while running:
        dt         = clock.tick(FPS)
        mouse_pos  = pygame.mouse.get_pos()
        player     = game.players[view_player]
        locked_set = locked_coords_per_player[player.pid]

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False

            # ── Klavye ────────────────────────────────────────
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    if selected_hand_idx is not None:
                        selected_hand_idx = None
                        pending_rotation  = 0
                        status_msg = "Seçim iptal edildi"
                    else:
                        running = False

                elif ev.key == pygame.K_r:
                    if selected_hand_idx is not None:
                        # Seçili kart varken R → döndür
                        pending_rotation = (pending_rotation + 1) % 6
                        hand = player.hand
                        if selected_hand_idx < len(hand):
                            cname = hand[selected_hand_idx].name
                            status_msg = (f"{cname} yönü: {pending_rotation * 60}°"
                                          f"  (R ile devam, hex seç)  ")
                    else:
                        # Seçili kart yoksa R → yeni oyun (lobby ile)
                        chosen_strats = LobbyScreen(screen).run()
                        game              = build_game(chosen_strats)
                        game_over         = False
                        winner            = None
                        view_player       = 0
                        popup_timer       = 0
                        popup_data        = None
                        last_breakdown    = None
                        selected_hand_idx = None
                        pending_rotation  = 0
                        locked_coords_per_player = {p.pid: set() for p in game.players}
                        status_msg        = "Yeni oyun  |  SPACE → tur ilerlet"
                        renderer          = BoardRenderer(
                            BOARD_ORIGIN,
                            game.players[0].strategy,
                            cyber_renderer=cyber,
                        )
                        renderer.init_fonts()

                elif ev.key == pygame.K_SPACE and not game_over:
                    step_turn(with_shop=True)

                elif ev.key == pygame.K_s and not game_over:
                    if player.alive:
                        open_shop_for_player(player)

                elif ev.key == pygame.K_f:
                    fast_mode  = not fast_mode
                    fast_timer = 0
                    selected_hand_idx = None
                    pending_rotation  = 0
                    status_msg = f"Hızlı mod: {'AÇIK' if fast_mode else 'KAPALI'}"

                elif pygame.K_1 <= ev.key <= pygame.K_8:
                    idx = ev.key - pygame.K_1
                    if idx < len(game.players):
                        view_player       = idx
                        selected_hand_idx = None
                        pending_rotation  = 0
                        renderer.strategy = game.players[idx].strategy
                        last_breakdown    = None
                        if popup_data:
                            for r in popup_data:
                                if r.get("pid_a") == view_player or r.get("pid_b") == view_player:
                                    last_breakdown = r
                                    break

            # ── Mouse hareket → hover ──────────────────────────
            elif ev.type == pygame.MOUSEMOTION:
                renderer.update_hover(ev.pos, BOARD_COORDS)

            # ── SAĞ TIK → seçili kart varsa döndür ───────────
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 3:
                if selected_hand_idx is not None and not game_over and not fast_mode:
                    pending_rotation = (pending_rotation + 1) % 6
                    hand = player.hand
                    if selected_hand_idx < len(hand):
                        cname = hand[selected_hand_idx].name
                        status_msg = (f"{cname} yönü: {pending_rotation * 60}°"
                                      f"  (sağ tık ile devam, hex seç)")

            # ── SOL TIK ───────────────────────────────────────
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos

                if game_over or fast_mode:
                    pass
                else:
                    hand  = player.hand
                    rects = _hand_card_rects(len(hand))

                    # El kartına tıklandı mı?
                    clicked_hand = None
                    for i, rect in enumerate(rects):
                        if rect.collidepoint(mx, my):
                            clicked_hand = i
                            break

                    if clicked_hand is not None:
                        if selected_hand_idx == clicked_hand:
                            # Aynı kart → seçimi iptal
                            selected_hand_idx = None
                            pending_rotation  = 0
                            status_msg = "Seçim iptal edildi"
                        else:
                            selected_hand_idx = clicked_hand
                            pending_rotation  = hand[clicked_hand].rotation
                            cname = hand[clicked_hand].name
                            status_msg = (f"{cname} seçildi  |"
                                          f"  R / sağ tık: döndür  |  boş hex: yerleştir")

                    else:
                        # Board hex'ine tıklandı mı?
                        q, r = pixel_to_hex(mx, my, *BOARD_ORIGIN)
                        coord = (q, r)

                        if coord in BOARD_COORDS:
                            if coord in player.board.grid:
                                # Dolu hex'e tık → her zaman kilitli, sökülemez
                                card = player.board.grid[coord]
                                status_msg = (f"{card.name} kilitli — "
                                              f"yerleştirilen kartlar taşınamaz")

                            elif selected_hand_idx is not None:
                                # Boş hex + seçili kart → yerleştir ve kilitle
                                if placed_this_turn >= PLACE_PER_TURN:
                                    status_msg = (f"Bu turda zaten {PLACE_PER_TURN} kart "
                                                  f"yerleştirdin — sınıra ulaşıldı")
                                else:
                                    card = hand.pop(selected_hand_idx)
                                    card.rotation = pending_rotation
                                    player.board.place(coord, card)
                                    locked_set.add(coord)       # ← KİLİTLE
                                    placed_this_turn += 1
                                    remaining = PLACE_PER_TURN - placed_this_turn
                                    selected_hand_idx = None
                                    pending_rotation  = 0
                                    status_msg = (f"{card.name} yerleştirildi "
                                                  f"({card.rotation * 60}°) — kilitlendi"
                                                  + (f"  |  Bu tur {remaining} hak kaldı"
                                                     if remaining > 0 else
                                                     "  |  Bu turun yerleştirme limiti doldu"))

                            else:
                                status_msg = "Önce el'den bir kart seç"

        # ── Hızlı mod ──────────────────────────────────────────
        if fast_mode and not game_over:
            fast_timer += dt
            if fast_timer >= FAST_DELAY:
                fast_timer = 0
                step_turn(with_shop=False)

        # ── Popup geri sayım ───────────────────────────────────
        if popup_timer > 0:
            popup_timer = max(0, popup_timer - dt)

        # ══════════════════════════════════════════════════════
        #  RENDER
        # ══════════════════════════════════════════════════════
        screen.fill(COLOR_BG)
        cyber.draw_vfx_base(screen)
        renderer.highlight_group = _get_hovered_synergy_group(screen, player)

        # Board (Cyber-Victorian)
        renderer.draw(
            screen,
            player.board,
            BOARD_COORDS,
            locked_coords=locked_set,
            show_tooltip=False,
        )

        # Seçili kart önizlemesi: hover hex üzerinde rotasyonlu görünüm
        if selected_hand_idx is not None and not game_over and not fast_mode:
            hand = player.hand
            if selected_hand_idx < len(hand):
                q, r = pixel_to_hex(*mouse_pos, *BOARD_ORIGIN)
                coord = (q, r)
                if coord in BOARD_COORDS and coord not in player.board.grid:
                    cx, cy = hex_to_pixel(q, r, *BOARD_ORIGIN)
                    # Sarı highlight
                    pts = _hex_corners_flat(cx, cy, HEX_SIZE - 4)
                    pygame.draw.polygon(screen, (50, 45, 15), pts)
                    pygame.draw.polygon(screen, C_SELECT, pts, 2)
                    # Rotasyon önizlemesi
                    renderer.draw_placement_preview(
                        screen, cx, cy,
                        hand[selected_hand_idx],
                        pending_rotation
                    )

        # Baslik (orta ust - CV)
        _draw_text(screen, font_lg, TITLE, W // 2 - 200, 14, C_SELECT)

        draw_player_panel(screen, game.players, view_player,
                           font_md, font_sm, px=W - 300, py=20)

        # Sol detay paneli (HUD altina)
        draw_player_info(screen, player, game.turn,
                          font_md, font_sm, px=20, py=145)

        # El kartları
        draw_hand_panel(screen, player, fonts, selected_hand_idx,
                         mouse_pos, current_rotation=pending_rotation)

        # Board altı sinerji HUD
        draw_synergy_hud(screen, player, fonts, renderer.highlight_group)

        # Passive güçlendirme logu — el panelinin altına
        _hand_bottom = HAND_PANEL_Y + len(player.hand) * (HAND_CARD_H + HAND_CARD_GAP) + 10
        _log_max_h   = H - 100 - _hand_bottom - 4
        draw_passive_buff_panel(screen, player, font_sm,
                                 px=HAND_PANEL_X, py=_hand_bottom, max_h=_log_max_h)

        # Board hover karti icin priority popup
        if renderer.hovered_card is not None:
            cyber.draw_priority_popup(
                screen,
                renderer.hovered_card,
                mouse_pos[0],
                mouse_pos[1],
            )

        # Cyber-Victorian HUD en uste (sol ust kose + alt bar)
        draw_cyber_victorian_hud(screen, player, game.turn, fonts,
                     fast_mode=fast_mode, status_msg=status_msg)

        # Combat breakdown
        if last_breakdown is not None:
            draw_combat_breakdown(screen, last_breakdown, view_player,
                                   game.players, font_md, font_sm)

        # Tur sonu popup
        if popup_timer > 0 and popup_data:
            alpha = min(255, int(popup_timer / POPUP_DURATION * 510))
            draw_turn_popup(screen, popup_data, view_player, game.players,
                             font_lg, font_md, font_sm, alpha)

        if game_over and winner:
            draw_game_over(screen, winner, font_lg, font_md)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


# ── Hex köşe hesabı ───────────────────────────────────────────
def _hex_corners_flat(cx, cy, size):
    import math
    return [
        (int(cx + size * math.cos(math.radians(60 * i))),
         int(cy + size * math.sin(math.radians(60 * i))))
        for i in range(6)
    ]


# ── Yardımcı çizim fonksiyonları ──────────────────────────────
def _draw_text(surface, font, text, x, y, color):
    surface.blit(font.render(text, True, color), (x, y))




def _get_hovered_synergy_group(surface, player):
    meta = [
        "EXISTENCE",
        "MIND",
        "CONNECTION",
    ]
    box_w = 140
    gap = 14
    total_w = len(meta) * box_w + (len(meta) - 1) * gap
    start_x = (surface.get_width() - total_w) // 2
    y = surface.get_height() - 92
    mx, my = pygame.mouse.get_pos()
    for i, group in enumerate(meta):
        rect = pygame.Rect(start_x + i * (box_w + gap), y, box_w, 32)
        if rect.collidepoint(mx, my):
            return group
    return None


if __name__ == "__main__":
    main()
