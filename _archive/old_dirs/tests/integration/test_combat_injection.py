"""Test combat_phase_fn injection in Game"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from engine_core import Game, Player, build_card_pool, combat_phase


def test_combat_phase_injection():
    """spy_combat wrapper'ının her combat turn'de çağrıldığını doğrular."""
    call_log = []

    def spy_combat(board_a, board_b, bonus_a, bonus_b, p_a, p_b, ctx):
        """Çağrıları kaydedip asıl combat_phase'e devreder."""
        call_log.append(ctx.get('turn', 0))
        return combat_phase(board_a, board_b, bonus_a, bonus_b, p_a, p_b, ctx)

    players = [Player(pid=i, strategy='random') for i in range(4)]
    game = Game(
        players,
        combat_phase_fn=spy_combat,
        card_pool=build_card_pool(),
    )
    game.run()

    assert len(call_log) > 0, "spy_combat hiç çağrılmadı — injection çalışmıyor"
    # Her turn en az bir combat pair beklenir
    assert len(set(call_log)) > 1, f"Sadece {set(call_log)} turn'de çağrıldı, birden fazla bekleniyor"
