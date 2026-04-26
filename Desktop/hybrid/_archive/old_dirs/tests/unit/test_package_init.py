"""engine_core paket import'unun ve public API'sinin doğruluğunu test eder."""
import sys
import os
import io
import importlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def test_version_and_all_exports():
    import engine_core
    assert hasattr(engine_core, '__version__'), "__version__ yok"
    assert hasattr(engine_core, '__all__'), "__all__ yok"
    assert len(engine_core.__all__) > 0


def test_all_symbols_importable():
    from engine_core import (
        Card, build_card_pool, Board, Player, Market, Game,
        run_simulation, combat_phase,
    )
    pool = build_card_pool()
    assert len(pool) > 0

    board = Board()
    board.place((0, 0), pool[0].clone())
    assert board.alive_count() == 1

    market = Market(pool)
    window = market.get_cards_for_player(5)
    assert 0 < len(window) <= 5

    player = Player(pid=0, strategy='warrior')
    assert player.pid == 0

    assert callable(run_simulation)
    assert callable(combat_phase)
    assert Game.__name__ == 'Game'


def test_no_stdout_on_import():
    """engine_core import edildiğinde stdout'a hiçbir şey yazmamalı."""
    # Önce modülü temizle
    to_remove = [k for k in sys.modules if k.startswith('engine_core')]
    for k in to_remove:
        del sys.modules[k]

    buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        import engine_core  # noqa: F401
    finally:
        sys.stdout = old_stdout

    output = buf.getvalue()
    assert output == '', f"Import sırasında stdout'a yazıldı: {repr(output)}"
