import pygame
import pytest

from v2.ui.combat_terminal import CombatTerminal


def _set_payload(terminal, lines, footer):
    if hasattr(terminal, "set_payload"):
        terminal.set_payload(lines, footer)
        return
    if hasattr(terminal, "load_payload"):
        terminal.load_payload(lines, footer)
        return
    if hasattr(terminal, "enqueue"):
        terminal.enqueue(lines, footer)
        return
    raise AssertionError("CombatTerminal should expose a payload-loading method.")


def _get_visible_lines(terminal):
    for attr in ("visible_lines", "lines_visible", "render_lines", "_visible_lines"):
        if hasattr(terminal, attr):
            return list(getattr(terminal, attr))
    raise AssertionError("CombatTerminal should expose visible streamed lines.")


def _get_visible_footer(terminal):
    for attr in ("visible_footer", "footer_visible", "footer", "_visible_footer"):
        if hasattr(terminal, attr):
            return getattr(terminal, attr)
    raise AssertionError("CombatTerminal should expose its visible footer state.")


@pytest.fixture(autouse=True)
def init_pygame():
    pygame.init()
    pygame.font.init()
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
    yield
    pygame.font.quit()
    pygame.quit()


@pytest.mark.xfail(reason="CombatTerminal widget is still a stub.")
def test_combat_terminal_streams_preformatted_lines_before_footer():
    terminal = CombatTerminal()
    _set_payload(
        terminal,
        ["P0 clashes with P1", "+2 combat points", "P1 takes 4 damage"],
        footer="[Base] + [Alive/2] + [Rarity/2] = 4",
    )

    assert hasattr(terminal, "update")
    assert _get_visible_lines(terminal) == []

    terminal.update(80)
    assert _get_visible_lines(terminal) == ["P0 clashes with P1"]
    assert _get_visible_footer(terminal) in (None, "", False)

    terminal.update(160)
    assert _get_visible_lines(terminal) == [
        "P0 clashes with P1",
        "+2 combat points",
        "P1 takes 4 damage",
    ]
    assert _get_visible_footer(terminal) in (None, "", False)

    terminal.update(1)
    assert _get_visible_footer(terminal) == "[Base] + [Alive/2] + [Rarity/2] = 4"


@pytest.mark.xfail(reason="CombatTerminal widget is still a stub.")
def test_combat_terminal_render_contract_is_non_interactive_and_safe():
    terminal = CombatTerminal()
    surface = pygame.Surface((640, 240))
    _set_payload(terminal, ["Line 1"], footer="Footer")

    assert hasattr(terminal, "render")
    terminal.render(surface)

    if hasattr(terminal, "handle_event"):
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
        handled = terminal.handle_event(event)
        assert handled in (None, False)
