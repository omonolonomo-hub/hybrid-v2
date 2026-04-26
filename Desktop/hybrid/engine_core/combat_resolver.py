"""
engine_core/combat_resolver.py
═══════════════════════════════════════════════════════════════════
Combat Phase çözümünün TEK KAYNAK (Single Source of Truth) implementasyonu.

Daha önce aynı kod iki yerde kopyalanmıştı:
  ✗  engine_core/board.py::combat_phase()           — 55 satırlık tam kopya (stale)
  ✗  engine_core/combat_engine.py::_resolve_combat_phase() — 55 satırlık tam kopya (güncel)

Artık bu modül tek yetkili kaynaktır.
board.py ve combat_engine.py yalnızca bu modülü çağırır.

Kural: Başka bir yerde combat phase çözüm kodu görürseniz silin.
═══════════════════════════════════════════════════════════════════
"""

from typing import Callable, Optional

from engine_core.damage_calculator import resolve_single_combat
from engine_core.constants import KILL_PTS


def resolve_combat_phase(
    board_a,
    board_b,
    combo_bonus_a,
    combo_bonus_b,
    player_a=None,
    player_b=None,
    ctx=None,
    trigger_passive_fn: Optional[Callable] = None,
) -> tuple[int, int, int]:
    """Resolve combat at every overlapping coordinate.

    Tek yetkili combat phase implementasyonu.
    board.combat_phase() ve CombatEngine._resolve_combat_phase() buraya delegate eder.

    Args:
        board_a: Player A'nın Board objesi
        board_b: Player B'nın Board objesi
        combo_bonus_a: A'nın combo bonus dict'i (coord → dict)
        combo_bonus_b: B'nın combo bonus dict'i (coord → dict)
        player_a: Player A objesi (passive trigger için)
        player_b: Player B objesi (passive trigger için)
        ctx: Bağlam dict'i (turn, game, vb.)
        trigger_passive_fn: Passive trigger fonksiyonu. None ise
                           engine_core.passive_trigger.trigger_passive kullanılır.

    Returns:
        (kill_pts_a, kill_pts_b, draw_count) tuple.
    """
    if trigger_passive_fn is None:
        from engine_core.passive_trigger import trigger_passive as _default_trigger
        trigger_passive_fn = _default_trigger

    if ctx is None:
        ctx = {}

    kill_a = 0
    kill_b = 0
    draws = 0

    grid_a = board_a.grid
    grid_b = board_b.grid
    shared_coords = set(grid_a.keys()) & set(grid_b.keys())

    for coord in shared_coords:
        if coord not in grid_a or coord not in grid_b:
            continue
        card_a = grid_a[coord]
        card_b = grid_b[coord]

        ba = combo_bonus_a.get(coord, {})
        bb = combo_bonus_b.get(coord, {})

        a_wins, b_wins = resolve_single_combat(card_a, card_b, ba, bb)

        if a_wins > b_wins:
            kill_a += trigger_passive_fn(card_a, "combat_win", player_a, player_b, ctx, verbose=False)
            kill_b += trigger_passive_fn(card_b, "combat_lose", player_b, player_a, ctx, verbose=False)

            card_b.lose_highest_edge()
            if card_b.is_eliminated():
                trigger_passive_fn(card_b, "card_killed", player_b, player_a, ctx, verbose=False)
                if card_b.is_eliminated():
                    board_b.remove(coord)
                    kill_a += KILL_PTS
        elif b_wins > a_wins:
            kill_b += trigger_passive_fn(card_b, "combat_win", player_b, player_a, ctx, verbose=False)
            kill_a += trigger_passive_fn(card_a, "combat_lose", player_a, player_b, ctx, verbose=False)

            card_a.lose_highest_edge()
            if card_a.is_eliminated():
                trigger_passive_fn(card_a, "card_killed", player_a, player_b, ctx, verbose=False)
                if card_a.is_eliminated():
                    board_a.remove(coord)
                    kill_b += KILL_PTS
        else:
            draws += 1

    return kill_a, kill_b, draws
