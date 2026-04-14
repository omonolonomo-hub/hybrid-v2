"""
HUD Renderer Module

This module contains all UI rendering functions extracted from run_game.py
for reuse across scenes in the Scene-based architecture.

The module provides two interfaces:
1. Module-level functions: Direct function calls for maximum flexibility
2. HUDRenderer class: Encapsulated interface with cached fonts

Rendering Functions:
-------------------
- draw_cyber_victorian_hud: Main HUD with corner frames, HP bar, gold, XP
- draw_player_panel: Player list with HP/status (right side panel)
- draw_player_info: Detailed player stats (left side panel)
- draw_combat_breakdown: Combat results breakdown (center overlay)
- draw_turn_popup: Turn end popup with fade animation
- draw_game_over: Game over screen with winner announcement
- draw_passive_buff_panel: Passive buff log (scrollable list)
- draw_synergy_hud: Active synergies display (bottom center badges)
- draw_hand_panel: Hand cards display (left side vertical list)

Helper Functions:
----------------
- hp_color: Calculate HP bar color based on HP percentage
- _active_synergy_counts: Count active synergies on player's board
- _hand_card_rects: Calculate rectangles for hand card layout
- get_hovered_synergy_group: Determine which synergy badge is hovered
- _draw_text: Simple text rendering helper

HUDRenderer Class:
-----------------
Optional encapsulation class that caches fonts and provides a clean interface
for rendering all HUD elements. Useful for scenes that need consistent styling.

Example Usage:
-------------
    # Module-level functions
    from ui.hud_renderer import draw_cyber_victorian_hud, draw_player_panel
    
    draw_cyber_victorian_hud(screen, player, turn, fonts)
    draw_player_panel(screen, players, selected_idx, font_md, font_sm, px, py)
    
    # HUDRenderer class
    from ui.hud_renderer import HUDRenderer
    
    hud = HUDRenderer(fonts)
    hud.draw_hud(screen, player, turn)
    hud.draw_players(screen, players, selected_idx, px=1300, py=20)

Extraction Status:
-----------------
✓ All drawing functions extracted from run_game.py
✓ All helper functions extracted
✓ HUDRenderer class provides encapsulated interface
✓ Comprehensive docstrings added
✓ Test suite created and passing
✓ Visual output matches original run_game.py implementation

Migration Notes:
---------------
This extraction was completed as part of Task T4.2 in the run-game-scene-integration
spec. The functions maintain backward compatibility with run_game.py while enabling
reuse in GameLoopScene, CombatScene, and other scenes.
"""

import pygame
from typing import Optional, Dict, Any, List, Tuple
from collections import Counter


# ── Placeholder functions (to be implemented) ──────────────────

def draw_cyber_victorian_hud(surface, player, game_turn, fonts, fast_mode=False,
                             status_msg="", renderer=None):
    """Draw the main Cyber-Victorian HUD with corner frames, HP bar, gold, XP, shop button.
    
    Args:
        surface: pygame Surface to draw on
        player: Current player instance
        game_turn: Current turn number
        fonts: Dictionary of fonts
        fast_mode: Whether fast mode is active
        status_msg: Status message to display
        renderer: Optional renderer instance
    """
    # Color constants for Cyber-Victorian theme
    C_BRONZE = (180, 140, 100)
    C_MAGENTA = (255, 50, 150)
    C_GOLD = (255, 215, 0)
    
    W_, H_  = surface.get_size()
    fm_bold = fonts["sm_bold"]
    fm_xs   = fonts["xs_bold"]
    fm_md   = fonts["md_bold"]
    fm_lg   = fonts["lg"]

    # ═ 1. SOL UST KOŞE PANELI (Player info + HP) ═══════════════════
    panel_w, panel_h = 300, 130
    pygame.draw.rect(surface, (20, 10,  5), (0, 0, panel_w, panel_h),
                     border_bottom_right_radius=28)
    pygame.draw.rect(surface, C_BRONZE,    (0, 0, panel_w, panel_h),
                     width=3, border_bottom_right_radius=28)
    # Kose percinleri
    for ppx, ppy in [(6, 6), (panel_w - 6, 6), (6, panel_h - 6)]:
        pygame.draw.circle(surface, C_BRONZE, (ppx, ppy), 5)

    # Baslik
    title_s = fm_md.render(f"P{player.pid+1}  {player.strategy.upper()}", True, C_WHITE)
    surface.blit(title_s, (18, 12))

    # HP bar (macenta sivi)
    max_hp  = getattr(player, "max_hp", 150)
    hp_pct  = max(0.0, player.hp / max_hp)
    bar_x, bar_y = 18, 42
    bar_w,  bar_h_ = 240, 18
    pygame.draw.rect(surface, (60, 0, 30),   (bar_x, bar_y, bar_w, bar_h_), border_radius=4)
    fill_w = int(bar_w * hp_pct)
    pygame.draw.rect(surface, C_MAGENTA,     (bar_x, bar_y, fill_w, bar_h_), border_radius=4)
    # Parlama seridi
    shine = pygame.Surface((fill_w, 3), pygame.SRCALPHA)
    shine.fill((255, 255, 255, 80))
    surface.blit(shine, (bar_x, bar_y))
    pygame.draw.rect(surface, C_BRONZE, (bar_x, bar_y, bar_w, bar_h_), 1, border_radius=4)
    hp_txt = fm_bold.render(f"CORE INTEGRITY: {player.hp}/{max_hp}", True, C_WHITE)
    surface.blit(hp_txt, (bar_x, bar_y - 16))

    # Gold (buharli sayac)
    gold_txt = fm_lg.render(f"⟲ {player.gold} CR", True, C_GOLD)
    surface.blit(gold_txt, (18, 74))
    turn_txt = fm_xs.render(f"TURN {game_turn}", True, C_DIM)
    surface.blit(turn_txt, (18, 106))
    if fast_mode:
        fast_s = fm_xs.render("⚡ HIZLI MOD", True, (240, 200, 60))
        surface.blit(fast_s, (140, 106))

    # ═ 2. ALT BAR (XP + Shop Butonu) ══════════════════════════
    bar_y2 = H_ - 90
    pygame.draw.rect(surface, (25, 15, 10), (0, bar_y2, W_, 90))
    pygame.draw.line(surface, C_BRONZE, (0, bar_y2), (W_, bar_y2), 4)

    # Status mesaji
    st_s = fonts["sm"].render(status_msg, True, C_DIM)
    surface.blit(st_s, (18, H_ - 22))

    # XP bar (ekran ortasi)
    xp_val = getattr(player, "xp", 0)
    xp_max = max(1, getattr(player, "xp_max", 10))
    xp_w   = 320
    xp_bx  = W_ // 2 - xp_w // 2
    xp_by  = H_ - 28
    pygame.draw.rect(surface, (0, 50, 60),    (xp_bx, xp_by, xp_w, 10), border_radius=4)
    xp_fill = int((xp_val / xp_max) * xp_w)
    pygame.draw.rect(surface, C_ACCENT,       (xp_bx, xp_by, xp_fill, 10), border_radius=4)
    pygame.draw.rect(surface, C_BRONZE,       (xp_bx, xp_by, xp_w, 10), 1, border_radius=4)
    xp_lbl = fm_xs.render(f"XP {xp_val}/{xp_max}", True, (100, 200, 220))
    surface.blit(xp_lbl, (xp_bx + xp_w + 8, xp_by - 2))

    # Buyuk Mekanik Shop Butonu (sag alt)
    btn = pygame.Rect(W_ - 220, H_ - 78, 195, 55)
    pygame.draw.rect(surface, (100, 50, 20), btn, border_radius=10)
    pygame.draw.rect(surface, C_BRONZE,     btn, width=3, border_radius=10)
    # Kose percinleri
    for ppx, ppy in [(btn.x + 6, btn.y + 6), (btn.right - 6, btn.y + 6),
                     (btn.x + 6, btn.bottom - 6), (btn.right - 6, btn.bottom - 6)]:
        pygame.draw.circle(surface, C_BRONZE, (ppx, ppy), 4)
    btn_txt = fm_md.render("OPEN MARKET", True, C_WHITE)
    surface.blit(btn_txt, (btn.centerx - btn_txt.get_width() // 2,
                            btn.centery - btn_txt.get_height() // 2))
    sub_txt = fonts["xs"].render("[S] veya [SPACE]", True, C_DIM)
    surface.blit(sub_txt, (btn.centerx - sub_txt.get_width() // 2, btn.bottom + 3))


def draw_player_panel(surface, players, selected, font_md, font_sm, px, py):
    """Draw the player panel showing all players with HP/status.
    
    Args:
        surface: pygame Surface to draw on
        players: List of all players
        selected: Index of currently selected player
        font_md: Medium font
        font_sm: Small font
        px: X position
        py: Y position
    
    Returns:
        List[pygame.Rect]: List of rectangles for each player row (for hit testing)
    """
    from ui.renderer import STRATEGY_COLORS
    
    ROW_H   = 64
    panel_w = 280
    box_h   = len(players) * ROW_H + 28
    pygame.draw.rect(surface, C_PANEL,
                     (px - 8, py - 8, panel_w, box_h), border_radius=8)
    pygame.draw.rect(surface, C_LINE,
                     (px - 8, py - 8, panel_w, box_h), 1, border_radius=8)
    _draw_text(surface, font_sm, "PLAYERS", px, py, C_DIM)
    py += 18
    
    # Store player rectangles for hit testing
    player_rects = []
    
    for i, p in enumerate(players):
        row_y  = py + i * ROW_H
        is_sel = (i == selected)
        
        # Create rectangle for this player row
        player_rect = pygame.Rect(px - 4, row_y - 2, panel_w - 8, ROW_H - 4)
        player_rects.append(player_rect)
        
        bg_col = (38, 42, 62) if is_sel else C_PANEL
        pygame.draw.rect(surface, bg_col, player_rect, border_radius=6)
        if is_sel:
            pygame.draw.rect(surface, C_ACCENT, player_rect, 1, border_radius=6)
        dot_col = STRATEGY_COLORS.get(p.strategy, (120, 120, 120))
        if not p.alive:
            dot_col = (60, 60, 60)
        pygame.draw.circle(surface, dot_col, (px + 6, row_y + 10), 5)
        name_col = C_WHITE if p.alive else C_DIM
        _draw_text(surface, font_sm, f"P{i+1}  {p.strategy}",
                   px + 18, row_y + 1, name_col)

        bar_w = 130
        bar_x = px + 18
        bar_y = row_y + 16
        ratio = max(0, p.hp / 150)
        pygame.draw.rect(surface, (40, 44, 60),
                         (bar_x, bar_y, bar_w, 7), border_radius=4)
        if p.alive and ratio > 0:
            pygame.draw.rect(surface, hp_color(p.hp),
                             (bar_x, bar_y, int(bar_w * ratio), 7),
                             border_radius=4)
        surface.blit(font_sm.render(f"{p.hp} HP", True, C_DIM),
                     (bar_x + bar_w + 5, bar_y - 1))

        wins   = p.stats.get("wins", 0)
        losses = p.stats.get("losses", 0)
        board  = p.board.alive_count()
        streak = p.win_streak
        pwr    = sum(c.total_power() for c in p.board.alive_cards())
        extra  = f"W:{wins} L:{losses}  Deck:{board}  Seri:{streak}  PWR:{pwr}"
        surface.blit(font_sm.render(extra, True,
                                    (80, 160, 180) if p.alive else C_DIM),
                     (bar_x, bar_y + 11))
        gold_s = font_sm.render(f"{p.gold}g", True,
                                (200, 170, 50) if p.alive else C_DIM)
        surface.blit(gold_s, (px + 18, bar_y + 24))
    
    return player_rects


def draw_player_info(surface, player, turn, font_md, font_sm, px, py):
    """Draw detailed player info (left side, current player details).
    
    Args:
        surface: pygame Surface to draw on
        player: Player instance
        turn: Current turn number
        font_md: Medium font
        font_sm: Small font
        px: X position
        py: Y position
    """
    from collections import Counter
    from ui.renderer import STRATEGY_COLORS
    
    alive_cards = player.board.alive_cards()
    rarity_cnt  = Counter(c.rarity for c in alive_cards)
    group_cnt   = Counter(c.dominant_group() for c in alive_cards)
    combat_pwr  = sum(c.total_power() for c in alive_cards)

    info_w = 260
    lines  = [
        ("Altin",       f"{player.gold}"),
        ("El",          f"{len(player.hand)} kart"),
        ("Board",       f"{player.board.alive_count()} kart"),
        ("Combat PWR",  f"{combat_pwr}"),
        ("Puan",        f"{player.total_pts}"),
        ("Win Streak",  f"{player.win_streak}"),
        ("Maks Streak", f"{player.stats.get('win_streak_max', 0)}"),
        ("G / M",       f"{player.stats.get('wins',0)} / {player.stats.get('losses',0)}"),
        ("Nadir.",      (f"1:{rarity_cnt.get('1',0)} 2:{rarity_cnt.get('2',0)}"
                         f" 3:{rarity_cnt.get('3',0)} 4:{rarity_cnt.get('4',0)}"
                         f" 5:{rarity_cnt.get('5',0)}")),
        ("Grup",        (f"E:{group_cnt.get('EXISTENCE',0)}"
                         f" M:{group_cnt.get('MIND',0)}"
                         f" C:{group_cnt.get('CONNECTION',0)}")),
        ("Evrimler",    f"{len(player.evolved_card_names)}"),
        ("Market Roll", f"{player.stats.get('market_rolls',0)}"),
        ("Hasar Al.",   f"{player.stats.get('damage_taken',0)}"),
    ]
    box_h = len(lines) * 20 + 30
    pygame.draw.rect(surface, C_PANEL,
                     (px - 8, py - 8, info_w, box_h), border_radius=8)
    pygame.draw.rect(surface, C_LINE,
                     (px - 8, py - 8, info_w, box_h), 1, border_radius=8)
    strat_col = STRATEGY_COLORS.get(player.strategy, C_WHITE)
    _draw_text(surface, font_sm,
               f"P{player.pid+1}  {player.strategy.upper()}", px, py, strat_col)
    py += 20
    pygame.draw.line(surface, C_LINE,
                     (px - 4, py - 4), (px + info_w - 20, py - 4), 1)
    for label, val in lines:
        _draw_text(surface, font_sm, label,  px,       py, C_DIM)
        _draw_text(surface, font_sm, str(val), px + 110, py, C_WHITE)
        py += 20


def draw_combat_breakdown(surface, r, view_pid, players, font_md, font_sm):
    """Draw combat breakdown showing match results.
    
    Args:
        surface: pygame Surface to draw on
        r: Combat results
        view_pid: Viewing player ID
        players: List of all players
        font_md: Medium font
        font_sm: Small font
    """
    W_, H_ = surface.get_size()
    BOX_W  = 640
    BOX_H  = 114
    bx     = (W_ // 2) - (BOX_W // 2)
    by     = H_ - BOX_H - 44

    bg = pygame.Surface((BOX_W, BOX_H), pygame.SRCALPHA)
    bg.fill((14, 16, 28, 215))
    surface.blit(bg, (bx, by))

    me  = "a" if r.get("pid_a") == view_pid else "b"
    opp = "b" if me == "a" else "a"

    pid_me    = r.get(f"pid_{me}", 0)
    pid_opp   = r.get(f"pid_{opp}", 0)
    pts_me    = r.get(f"pts_{me}", 0)
    pts_opp   = r.get(f"pts_{opp}", 0)
    kill_me   = r.get(f"kill_{me}", 0)
    combo_me  = r.get(f"combo_{me}", 0)
    syn_me    = r.get(f"synergy_{me}", 0)
    kill_opp  = r.get(f"kill_{opp}", 0)
    combo_opp = r.get(f"combo_{opp}", 0)
    syn_opp   = r.get(f"synergy_{opp}", 0)
    winner_pid = r.get("winner_pid", -1)
    dmg        = r.get("dmg", 0)

    if winner_pid == view_pid:
        border_col = (60, 200, 100)
        result_txt = f"WON  +{dmg} damage"
        result_col = (80, 230, 110)
    elif winner_pid == -1:
        border_col = (160, 160, 70)
        result_txt = "TIE  +1 gold"
        result_col = (210, 200, 60)
    else:
        border_col = (220, 70, 60)
        result_txt = f"LOST  -{dmg} HP"
        result_col = (230, 90, 70)

    pygame.draw.rect(surface, border_col, (bx, by, BOX_W, BOX_H), 1, border_radius=6)

    p_me  = players[pid_me]  if pid_me  < len(players) else None
    p_opp = players[pid_opp] if pid_opp < len(players) else None
    surface.blit(font_sm.render(f"P{pid_me+1} vs P{pid_opp+1}", True, C_DIM),
                 (bx + 10, by + 8))
    rs = font_sm.render(result_txt, True, result_col)
    surface.blit(rs, (bx + BOX_W - rs.get_width() - 10, by + 8))
    pygame.draw.line(surface, (50, 53, 72),
                     (bx + 8, by + 24), (bx + BOX_W - 8, by + 24), 1)

    col_l = bx + 16
    col_r = bx + BOX_W // 2 + 8
    y2    = by + 30
    me_str  = p_me.strategy.upper()[:9]  if p_me  else "?"
    opp_str = p_opp.strategy.upper()[:9] if p_opp else "?"
    surface.blit(font_sm.render(f"ME — P{pid_me+1} {me_str}", True, C_WHITE),
                 (col_l, y2))
    surface.blit(font_sm.render(f"OPPONENT — P{pid_opp+1} {opp_str}", True, C_DIM),
                 (col_r, y2))
    y2 += 16

    for lbl, vm, vo, col in [
        ("Kill",    kill_me,  kill_opp,  (230, 100, 70)),
        ("Combo",   combo_me, combo_opp, (80,  210, 150)),
        ("Synergy", syn_me,   syn_opp,   (90,  160, 250)),
        ("TOPLAM",  pts_me,   pts_opp,   C_WHITE),
    ]:
        surface.blit(font_md.render(lbl,     True, C_DIM),       (col_l,      y2))
        surface.blit(font_md.render(str(vm), True, col),         (col_l + 90, y2))
        surface.blit(font_md.render(lbl,     True, (45, 48, 65)),(col_r,      y2))
        surface.blit(font_md.render(str(vo), True, C_DIM),       (col_r + 90, y2))
        y2 += 13


def draw_turn_popup(surface, results, view_pid, players,
                    font_lg, font_md, font_sm, alpha):
    """Draw turn popup with combat results (fades in/out).
    
    Args:
        surface: pygame Surface to draw on
        results: Combat results
        view_pid: Viewing player ID
        players: List of all players
        font_lg: Large font
        font_md: Medium font
        font_sm: Small font
        alpha: Alpha value for fade effect
    """
    W_, H_  = surface.get_size()
    n_rows  = len(results)
    ROW_H   = 40
    PAD     = 16
    BOX_W   = 580
    BOX_H   = PAD * 2 + 34 + n_rows * ROW_H + 8
    bx      = (W_ - BOX_W) // 2
    by      = 76

    popup = pygame.Surface((BOX_W, BOX_H), pygame.SRCALPHA)
    popup.fill((10, 12, 24, min(215, alpha)))
    pygame.draw.rect(popup, (80, 160, 240, min(200, alpha)),
                     (0, 0, BOX_W, BOX_H), 1, border_radius=8)

    hs = font_md.render("TURN END — BATTLE RESULTS", True, (80, 160, 240))
    popup.blit(hs, ((BOX_W - hs.get_width()) // 2, PAD))
    pygame.draw.line(popup, (50, 53, 72),
                     (PAD, PAD + 22), (BOX_W - PAD, PAD + 22), 1)

    y = PAD + 30
    for r in results:
        pid_a      = r.get("pid_a", 0)
        pid_b      = r.get("pid_b", 0)
        winner_pid = r.get("winner_pid", -1)
        dmg        = r.get("dmg", 0)
        pts_a      = r.get("pts_a", 0)
        pts_b      = r.get("pts_b", 0)
        hp_before_a = r.get("hp_before_a", "?")
        hp_before_b = r.get("hp_before_b", "?")
        hp_after_a  = r.get("hp_after_a",  "?")
        hp_after_b  = r.get("hp_after_b",  "?")

        if pid_a == view_pid or pid_b == view_pid:
            rb = pygame.Surface((BOX_W - PAD * 2, ROW_H - 4), pygame.SRCALPHA)
            rb.fill((40, 46, 72, min(150, alpha)))
            popup.blit(rb, (PAD, y))

        if winner_pid == pid_a:
            ic_a, ic_b = "▲", "▽"
            ca, cb = (80, 220, 100), (190, 80, 60)
            note = f"−{dmg} HP"
        elif winner_pid == pid_b:
            ic_a, ic_b = "▽", "▲"
            ca, cb = (190, 80, 60), (80, 220, 100)
            note = f"−{dmg} HP"
        else:
            ic_a = ic_b = "="
            ca = cb = (200, 190, 60)
            note = "+1g"

        ta = f"{ic_a} P{pid_a+1}  {pts_a}p  {hp_before_a}→{hp_after_a}HP"
        tb = f"{ic_b} P{pid_b+1}  {pts_b}p  {hp_before_b}→{hp_after_b}HP"
        mid = BOX_W // 2
        ry  = y + 8
        popup.blit(font_sm.render(ta,   True, ca),             (PAD,       ry))
        popup.blit(font_sm.render("vs", True, (75, 80, 110)),  (mid - 8,   ry))
        popup.blit(font_sm.render(tb,   True, cb),             (mid + 14,  ry))
        ns = font_sm.render(note, True, (155, 155, 155))
        popup.blit(ns, (BOX_W - ns.get_width() - PAD, ry))
        y += ROW_H

    surface.blit(popup, (bx, by))


def draw_game_over(surface, winner, font_lg, font_md):
    """Draw game over screen with winner announcement.
    
    Args:
        surface: pygame Surface to draw on
        winner: Winner player instance
        font_lg: Large font
        font_md: Medium font
    """
    from ui.renderer import STRATEGY_COLORS
    
    W_, H_ = surface.get_size()
    ov = pygame.Surface((W_, H_), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 160))
    surface.blit(ov, (0, 0))
    box_w, box_h = 440, 160
    bx = (W_ - box_w) // 2
    by = (H_ - box_h) // 2
    pygame.draw.rect(surface, (22, 26, 44), (bx, by, box_w, box_h), border_radius=12)
    pygame.draw.rect(surface, C_ACCENT,     (bx, by, box_w, box_h), 2, border_radius=12)
    col = STRATEGY_COLORS.get(winner.strategy, C_WHITE)
    t1  = font_lg.render("GAME OVER", True, C_ACCENT)
    t2  = font_md.render(f"Winner: P{winner.pid+1}  ({winner.strategy})", True, col)
    t3  = font_md.render(f"HP: {winner.hp}   |   R key → new game", True, C_DIM)
    surface.blit(t1, (bx + (box_w - t1.get_width()) // 2, by + 24))
    surface.blit(t2, (bx + (box_w - t2.get_width()) // 2, by + 68))
    surface.blit(t3, (bx + (box_w - t3.get_width()) // 2, by + 104))


def draw_passive_buff_panel(surface, player, font_sm, px, py, max_h):
    """Draw passive buff panel showing passive and copy-strengthen buffs.
    
    Scrollable list for left sidebar (vertical layout).
    
    Args:
        surface: pygame Surface to draw on
        player: Player instance
        font_sm: Small font
        px: X position (left edge)
        py: Y position (top edge)
        max_h: Maximum height
    
    Returns:
        int: Height of the rendered panel
    """
    from ui.card_meta import get_passive_desc
    
    logs = player.passive_buff_log
    if not logs or max_h < 30:
        return 0

    PANEL_W  = 200
    ROW_H    = 14
    HEADER_H = 20
    PAD      = 8

    entries  = logs[-10:]           # Last 10 entries
    box_h    = min(max_h, HEADER_H + len(entries) * ROW_H + PAD * 2)

    pygame.draw.rect(surface, C_PANEL,
                     (px - 4, py - 2, PANEL_W + 8, box_h), border_radius=6)
    pygame.draw.rect(surface, (60, 80, 120),
                     (px - 4, py - 2, PANEL_W + 8, box_h), 1, border_radius=6)

    _draw_text(surface, font_sm, "✶ PASSIVE BUFFS", px, py, C_ACCENT)
    y = py + HEADER_H

    TRIGGER_LABELS = {
        "copy_2":          "2x+2",
        "copy_3":          "3x+3",
        "income":          "inc",
        "combat_win":      "win",
        "combat_lose":     "lose",
        "card_buy":        "buy",
        "market_refresh":  "ref",
        "pre_combat":      "pre",
    }

    for entry in entries:
        if y + ROW_H > py + box_h - PAD:
            break
        turn    = entry["turn"]
        card    = entry["card"]
        trig    = TRIGGER_LABELS.get(entry["trigger"], entry["trigger"][:3])
        delta   = entry["delta"]
        passive = entry["passive"]

        # copy_strengthen = yellow, passive = green
        col = (220, 200, 60) if passive == "copy_strengthen" else (80, 210, 130)

        # Show card name (truncated) + trigger + delta
        card_short = card[:8] if len(card) <= 8 else card[:6] + ".."
        line = f"T{turn:>2} {card_short:<8} {trig:<3} +{delta}"
        _draw_text(surface, font_sm, line, px, y, col)
        y += ROW_H
    
    return box_h


def draw_synergy_hud(surface, player, fonts, hovered_group=None):
    """Draw synergy HUD showing active synergies from board composition.
    
    Compact badge style positioned at bottom center of screen.
    
    Args:
        surface: pygame Surface to draw on
        player: Player instance
        fonts: Dictionary of fonts
        hovered_group: Optional hovered group name
    """
    """Draw synergy HUD showing active synergies from board composition.
    
    Compact badge style positioned at bottom center of screen.
    
    Args:
        surface: pygame Surface to draw on
        player: Player instance
        fonts: Dictionary of fonts
        hovered_group: Optional hovered group name
    """
    from ui.renderer_v3 import GROUP_COLORS
    
    counts = _active_synergy_counts(player)
    
    # Group metadata with icons
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
        is_hover = hovered_group == group
        alpha = 255 if cnt > 0 else 70
        rect = pygame.Rect(start_x + i * (box_w + gap), y, box_w, 32)

        bg = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(bg, (18, 24, 44, max(45, alpha // 3)), bg.get_rect(), border_radius=6)
        border_width = 2 if is_hover else 1
        pygame.draw.rect(bg, (*color, alpha), bg.get_rect(), width=border_width, border_radius=6)
        surface.blit(bg, rect)

        txt_col = color if cnt > 0 else (110, 120, 140)
        text = fonts["xs_bold"].render(f"{icon}  {cnt}", True, txt_col)
        surface.blit(text, (rect.x + 12, rect.y + 8))
    
    # Return height of synergy HUD (header + boxes + margin)
    return 32 + 22 + 10  # box_height + header_height + margin


def draw_hand_panel(surface, player, fonts, selected_idx, mouse_pos, current_rotation=0):
    """Draw hand panel showing player's hand cards.
    
    Args:
        surface: pygame Surface to draw on
        player: Player instance
        fonts: Dictionary of fonts
        selected_idx: Index of selected card (or None)
        mouse_pos: Current mouse position
        current_rotation: Current rotation of selected card
    """
    from ui.renderer import GROUP_COLORS, RARITY_COLORS
    
    HAND_PANEL_X = 20
    HAND_PANEL_Y = 430
    HAND_CARD_W = 210
    HAND_CARD_H = 70
    C_SELECT = (0, 242, 255)
    
    hand = player.hand
    if not hand:
        pygame.draw.rect(surface, C_PANEL,
                         (HAND_PANEL_X - 4, HAND_PANEL_Y - 24,
                          HAND_CARD_W + 8, 48), border_radius=6)
        s = fonts["sm"].render("Hand empty", True, C_DIM)
        surface.blit(s, (HAND_PANEL_X + 4, HAND_PANEL_Y - 16))
        return

    # Başlık
    title_s = fonts["sm"].render(f"HAND  {len(hand)}/6  — click → select", True, C_DIM)
    surface.blit(title_s, (HAND_PANEL_X, HAND_PANEL_Y - 18))

    rects = _hand_card_rects(len(hand))

    for i, (card, rect) in enumerate(zip(hand, rects)):
        hovered  = rect.collidepoint(mouse_pos)
        selected = (i == selected_idx)

        dom  = card.dominant_group()
        gcol = GROUP_COLORS.get(dom, (80, 80, 120))

        if selected:
            bg = (50, 54, 30)
        elif hovered:
            bg = (38, 42, 62)
        else:
            bg = C_PANEL

        pygame.draw.rect(surface, bg, rect, border_radius=6)

        if selected:
            pygame.draw.rect(surface, C_SELECT, rect, 2, border_radius=6)
        elif hovered:
            pygame.draw.rect(surface, C_ACCENT, rect, 1, border_radius=6)
        else:
            pygame.draw.rect(surface, C_LINE, rect, 1, border_radius=6)

        # Rarity şeridi
        rc = RARITY_COLORS.get(card.rarity, C_DIM)
        pygame.draw.rect(surface, rc,
                         (rect.x + 6, rect.y + 2, rect.width - 12, 3),
                         border_radius=2)

        # Grup renk noktası
        pygame.draw.circle(surface, gcol, (rect.x + 10, rect.y + 16), 4)

        # Kart adı
        name = card.name if len(card.name) <= 20 else card.name[:18] + "…"
        ns = fonts["sm"].render(name, True, C_SELECT if selected else C_WHITE)
        surface.blit(ns, (rect.x + 18, rect.y + 8))

        # PWR + passive
        rot_deg = (current_rotation * 60) if selected else (card.rotation * 60)
        pwr_txt = f"PWR {card.total_power()}  ↻{rot_deg}°"
        if card.passive_type and card.passive_type != "none":
            pwr_txt += "  ✦"
        ps = fonts["sm"].render(pwr_txt, True, gcol)
        surface.blit(ps, (rect.x + 18, rect.y + 28))

        # Seçiliyse ipucu
        if selected:
            tip = fonts["sm"].render("→hex / R:rotate / RClick:rotate", True, C_SELECT)
            surface.blit(tip, (rect.right + 6, rect.y + 18))


# ── Helper functions ───────────────────────────────────────────

# Color constants (from run_game.py)
C_HP_OK  = ( 70, 225, 140)
C_HP_LOW = (255,  95, 110)
C_PANEL  = ( 16,  20,  34)
C_LINE   = ( 42,  58,  92)
C_DIM    = (130, 140, 170)
C_WHITE  = (245, 245, 255)
C_ACCENT = (  0, 242, 255)


# ── Helper functions ───────────────────────────────────────────

def _draw_text(surface, font, text, x, y, color):
    """Helper function to draw text on surface.
    
    Args:
        surface: pygame Surface to draw on
        font: pygame Font to use
        text: Text string to render
        x: X position
        y: Y position
        color: RGB color tuple
    """
    surface.blit(font.render(text, True, color), (x, y))


def hp_color(hp: int, max_hp: int = 150) -> tuple:
    ratio = hp / max_hp
    if ratio > 0.5:
        return C_HP_OK
    elif ratio > 0.25:
        return (220, 180, 40)
    return C_HP_LOW


def _active_synergy_counts(player) -> Counter:
    """Count active synergies on player's board.
    
    Args:
        player: Player instance
    
    Returns:
        Counter of group names to counts
    """
    from engine_core.constants import STAT_TO_GROUP
    
    counts = Counter()
    for card in player.board.grid.values():
        for stat_name, value in card.stats.items():
            if value <= 0 or str(stat_name).startswith("_"):
                continue
            group = STAT_TO_GROUP.get(stat_name)
            if group:
                counts[group] += 1
    return counts


def _hand_card_rects(hand_size: int) -> List[pygame.Rect]:
    """Calculate rectangles for hand cards.
    
    Args:
        hand_size: Number of cards in hand
    
    Returns:
        List of pygame.Rect for each card
    """
    HAND_PANEL_X = 20
    HAND_PANEL_Y = 430
    HAND_CARD_W = 210
    HAND_CARD_H = 70
    HAND_CARD_GAP = 6
    
    rects = []
    for i in range(hand_size):
        x = HAND_PANEL_X
        y = HAND_PANEL_Y + i * (HAND_CARD_H + HAND_CARD_GAP)
        rects.append(pygame.Rect(x, y, HAND_CARD_W, HAND_CARD_H))
    return rects


def get_hovered_synergy_group(surface, mouse_pos) -> Optional[str]:
    """Determine which synergy group is being hovered over.
    
    Args:
        surface: pygame Surface (used to get dimensions)
        mouse_pos: Tuple of (x, y) mouse coordinates
    
    Returns:
        Group name if hovering over a synergy badge, None otherwise
    """
    meta = ["EXISTENCE", "MIND", "CONNECTION"]
    box_w = 140
    gap = 14
    total_w = len(meta) * box_w + (len(meta) - 1) * gap
    start_x = (surface.get_width() - total_w) // 2
    y = surface.get_height() - 92
    mx, my = mouse_pos
    
    for i, group in enumerate(meta):
        rect = pygame.Rect(start_x + i * (box_w + gap), y, box_w, 32)
        if rect.collidepoint(mx, my):
            return group
    return None


# ── HUDRenderer class (optional encapsulation) ─────────────────

class HUDRenderer:
    """HUD rendering utility class that encapsulates fonts, colors, and surfaces.
    
    This class provides a convenient interface for rendering all HUD elements
    with cached fonts and consistent styling. It delegates to module-level
    functions for the actual rendering logic.
    
    Attributes:
        fonts: Dictionary of pygame fonts (xs_bold, sm_bold, md_bold, lg, etc.)
    
    Example:
        >>> fonts = load_fonts()
        >>> hud = HUDRenderer(fonts)
        >>> hud.draw_hud(screen, player, game_turn)
        >>> hud.draw_players(screen, players, selected_idx, px=1300, py=20)
    """
    
    def __init__(self, fonts: Dict[str, pygame.font.Font]):
        """Initialize HUD renderer with fonts.
        
        Args:
            fonts: Dictionary of fonts with keys:
                - xs_bold: Extra small bold font
                - sm_bold: Small bold font
                - md_bold: Medium bold font
                - lg: Large font
                - sm: Small font
                - md: Medium font
                - xs: Extra small font
        """
        self.fonts = fonts
    
    def draw_hud(self, surface, player, game_turn, fast_mode=False, status_msg="", renderer=None):
        """Draw main Cyber-Victorian HUD.
        
        Args:
            surface: pygame Surface to draw on
            player: Current player instance
            game_turn: Current turn number
            fast_mode: Whether fast mode is active
            status_msg: Status message to display
            renderer: Optional renderer instance
        """
        draw_cyber_victorian_hud(surface, player, game_turn, self.fonts, 
                                fast_mode, status_msg, renderer)
    
    def draw_players(self, surface, players, selected, px, py):
        """Draw player panel showing all players.
        
        Args:
            surface: pygame Surface to draw on
            players: List of all players
            selected: Index of currently selected player
            px: X position
            py: Y position
        
        Returns:
            List[pygame.Rect]: List of rectangles for each player row
        """
        return draw_player_panel(surface, players, selected, 
                                self.fonts["md_bold"], self.fonts["sm_bold"], px, py)
    
    def draw_player_details(self, surface, player, turn, px, py):
        """Draw detailed player info panel.
        
        Args:
            surface: pygame Surface to draw on
            player: Player instance
            turn: Current turn number
            px: X position
            py: Y position
        """
        draw_player_info(surface, player, turn, 
                        self.fonts["md_bold"], self.fonts["sm_bold"], px, py)
    
    def draw_breakdown(self, surface, results, view_pid, players):
        """Draw combat breakdown.
        
        Args:
            surface: pygame Surface to draw on
            results: Combat results dictionary
            view_pid: Viewing player ID
            players: List of all players
        """
        draw_combat_breakdown(surface, results, view_pid, players,
                             self.fonts["md_bold"], self.fonts["sm_bold"])
    
    def draw_popup(self, surface, results, view_pid, players, alpha):
        """Draw turn popup with fade effect.
        
        Args:
            surface: pygame Surface to draw on
            results: List of combat results
            view_pid: Viewing player ID
            players: List of all players
            alpha: Alpha value for fade effect (0-255)
        """
        draw_turn_popup(surface, results, view_pid, players,
                       self.fonts["lg"], self.fonts["md_bold"], 
                       self.fonts["sm_bold"], alpha)
    
    def draw_winner(self, surface, winner):
        """Draw game over screen.
        
        Args:
            surface: pygame Surface to draw on
            winner: Winner player instance
        """
        draw_game_over(surface, winner, self.fonts["lg"], self.fonts["md_bold"])
    
    def draw_passives(self, surface, player, px, py, max_h):
        """Draw passive buff panel.
        
        Args:
            surface: pygame Surface to draw on
            player: Player instance
            px: X position
            py: Y position
            max_h: Maximum height
        
        Returns:
            int: Height of rendered panel
        """
        return draw_passive_buff_panel(surface, player, self.fonts["sm_bold"], 
                                      px, py, max_h)
    
    def draw_synergies(self, surface, player, hovered_group=None):
        """Draw synergy HUD.
        
        Args:
            surface: pygame Surface to draw on
            player: Player instance
            hovered_group: Optional hovered group name
        """
        draw_synergy_hud(surface, player, self.fonts, hovered_group)
    
    def draw_hand(self, surface, player, selected_idx, mouse_pos, current_rotation=0):
        """Draw hand panel.
        
        Args:
            surface: pygame Surface to draw on
            player: Player instance
            selected_idx: Index of selected card (or None)
            mouse_pos: Current mouse position
            current_rotation: Current rotation of selected card
        """
        draw_hand_panel(surface, player, self.fonts, selected_idx, 
                       mouse_pos, current_rotation)
