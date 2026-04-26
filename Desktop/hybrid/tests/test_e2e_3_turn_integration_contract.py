import random
import pytest

# pytestmark removed (H4-1)

from engine_core.board import combat_phase
from engine_core.card import get_card_pool
from engine_core.game import Game
from engine_core.passive_trigger import trigger_passive
from engine_core.player import Player
from v2.core.game_state import GameState


def _build_real_game(n_players=4, seed=42):
    rng = random.Random(seed)
    strategies = ["random", "builder", "economist", "warrior"][:n_players]
    players = [Player(pid=i, strategy=s) for i, s in enumerate(strategies)]
    return Game(
        players,
        verbose=False,
        rng=rng,
        trigger_passive_fn=trigger_passive,
        combat_phase_fn=combat_phase,
        card_pool=get_card_pool(),
    )


@pytest.fixture
def gs_with_real_engine():
    gs = GameState()
    game = _build_real_game()
    gs.hook_engine(game)
    yield gs, game


def test_e2e_real_engine_commit_triggers_preparation_phase(gs_with_real_engine):
    """
    Phase 5 Split-Turn Architecture:
    start_turn() tur numarasini artirip income verir.
    commit_human_turn() AI'lari calistirir ve eslesmeleri dondurur.

    Arrange: Gercek engine bagli.
    Act:     game.start_turn() + gs.commit_human_turn() cagrilir.
    Assert:  engine.turn 1 artar.
    """
    gs, game = gs_with_real_engine
    assert game.turn == 0

    # Yeni split-turn: once start_turn (income + market), sonra commit (AI + freeze)
    game.start_turn()
    gs.commit_human_turn()

    assert game.turn == 1
    pairings = gs.get_current_pairings()
    assert len(pairings) > 0
    # Her eşleşme farklı oyunculardan oluşmalı
    for pid_a, pid_b in pairings:
        assert pid_a != pid_b


def test_e2e_real_engine_hp_syncs_after_combat(gs_with_real_engine):
    """
    Phase 5 Madde 35: HP değerleri engine ile UI arasında eşleşmeli.
    Arrange: preparation_phase + combat_phase çalıştırıldı.
    Act:     PublicState üzerinden HP okunur.
    Assert:  Her oyuncu için UI'dan okunan HP, engine'deki ile aynı olmalı.
    """
    gs, game = gs_with_real_engine
    game.preparation_phase()
    game.combat_phase()

    state = gs.get_public_state()
    for p in game.players:
        if p.pid == state.view_index:
            assert state.active_player.hp == p.hp
        else:
            # Non-active players: read from engine directly via adapter
            assert gs._adapter.get_player_hp(p.pid) == p.hp


def test_e2e_real_engine_combat_results_have_correct_shape(gs_with_real_engine):
    """
    Phase 5 Madde 37: combat_phase() sonrası last_combat_results formatsı doğru olmalı.
    """
    gs, game = gs_with_real_engine
    game.preparation_phase()
    game.combat_phase()

    results = gs.get_last_combat_results()
    assert len(results) > 0
    required_keys = {"pid_a", "pid_b", "winner_pid", "dmg", "hp_after_a", "hp_after_b"}
    for r in results:
        assert required_keys.issubset(r.keys()), f"Eksik alanlar: {required_keys - r.keys()}"


def test_e2e_pairings_frozen_stable_within_same_turn(gs_with_real_engine):
    """
    Phase 5 Madde 36: Eşleşmeler bir tur boyunca değişmemeli (freeze).
    """
    gs, game = gs_with_real_engine
    gs.commit_human_turn()

    # Aynı tur içinde 5 kez sorulsa da aynı eşleşme gelmelidir
    pairings_snapshots = [tuple(gs.get_current_pairings()) for _ in range(5)]
    assert len(set(pairings_snapshots)) == 1, "Eşleşmeler tur içinde değişmemeli!"


def test_e2e_3_turn_full_game_loop_no_crash(gs_with_real_engine):
    """
    Phase 5 Madde 42: 3 tur boyunca hatasız çalışan tam oyun döngüsü.
    Arrange: Gerçek engine 4 oyuncuyla başlatıldı.
    Act:     3 kez preparation + combat döngüsü.
    Assert:  Herhangi bir exception fırlatılmamalı, alive_pid listesi geçerli olmalı.
    """
    gs, game = gs_with_real_engine

    for turn_num in range(1, 4):
        game.preparation_phase()
        frozen_pairs = game.swiss_pairs()
        game.combat_phase(pairs=frozen_pairs)

        alive = gs.get_alive_pids()
        assert isinstance(alive, list)
        for pid in alive:
            assert isinstance(pid, int)
            hp = gs._adapter.get_player_hp(pid) if gs._adapter else 0
            assert hp > 0, f"Tur {turn_num}: P{pid} öldü ama hala alive listesinde!"

    assert game.turn == 3
