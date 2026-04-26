"""
engine_core/board_utils.py
═══════════════════════════════════════════════════════════════════
Board yardımcı fonksiyonlarının TEK KAYNAK (Single Source of Truth) modülü.

Daha önce aynı kod üç yerde kopyalanmıştı:
  ✗  engine_core/game.py::_iter_board_cards() + _clear_transient_board_state()
  ✗  engine_core/combat_engine.py::_iter_board_cards() + _clear_transient_board_state()
  ✗  engine_core/turn_manager.py::_iter_board_cards() + _clear_transient_board_state()

Artık bu modül tek yetkili kaynaktır.
Her üç sınıf bu modülü import eder.

Kural: Başka bir yerde iter_board_cards veya clear_transient_board_state
       fonksiyonu görürseniz silin ve buradan import edin.
═══════════════════════════════════════════════════════════════════
"""

from typing import Iterable


def iter_board_cards(players) -> Iterable:
    """Tüm oyuncuların board'larındaki kartları iter et.

    Args:
        players: Player nesnesi listesi. Her birinin .board.grid dict'i olmalı.

    Yields:
        Board üzerindeki Card nesneleri.
    """
    for player in players:
        for card in tuple(player.board.grid.values()):
            yield card


def clear_transient_board_state(
    players,
    *,
    current_turn: int,
    clear_combat_meta: bool,
) -> None:
    """Oyuncuların board'larındaki kartların geçici durumunu temizle.

    Args:
        players: Player nesnesi listesi.
        current_turn: Mevcut tur sayısı (süresi dolan efektler için).
        clear_combat_meta: True ise combat kapsamlı meta verileri de temizle.
    """
    for card in iter_board_cards(players):
        card.clear_expired_effects(current_turn)
        if clear_combat_meta:
            card.clear_meta_scope("combat")
