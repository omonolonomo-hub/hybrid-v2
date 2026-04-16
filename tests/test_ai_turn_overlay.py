import pytest

@pytest.mark.xfail(reason="Phase 4 Opponents deciding overlay is not implemented yet.")
def test_opponents_deciding_overlay_blocks_input_events_during_ai_turns():
    # Covers: "Opponents deciding... overlay: GameState.run_ai_turns() çalışırken tam ekran yarı saydam siyah overlay... hiçbir input event iletilmez."
    pass

@pytest.mark.xfail(reason="Phase 4 Opponents deciding overlay is not implemented yet.")
def test_opponents_deciding_overlay_dismissed_automatically_after_run_ai_turns():
    # Covers: "run_ai_turns() döndüğünde overlay otomatik kalkar."
    pass
