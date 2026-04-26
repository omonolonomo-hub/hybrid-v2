import pytest
from engine_core.player import Player
from engine_core.card import Card
from engine_core.inventory import Inventory
from engine_core.economy import Economy
from engine_core.game import Game
from v2.core.game_state import GameState
from v2.core.engine_adapter import EngineAdapter
from v2.core.public_state import PublicState

def test_inventory_clear_slot_position_integrity():
    """
    Paket 1 & 4: clear_slot metodunun eldeki kartların pozisyonunu bozmadığını doğrular.
    """
    inv = Inventory()
    # Mock nesneler kullanarak Card.__init__ karmaşasından kaçın
    c1 = type('obj', (object,), {'name': 'Card 1'})
    c2 = type('obj', (object,), {'name': 'Card 2'})
    c3 = type('obj', (object,), {'name': 'Card 3'})
    
    inv.hand = [c1, c2, c3]
    
    # Ortadaki kartı sil (index 1)
    inv.clear_slot(1)
    
    assert len(inv.hand) == 3, "Hand size should remain constant"
    assert inv.hand[0] == c1, "First card should stay at index 0"
    assert inv.hand[1] is None, "Index 1 should be None"
    assert inv.hand[2] == c3, "Third card should stay at index 2"

def test_economy_spend_gold_signal_emitted():
    """
    Paket 4: spend_gold çağrıldığında economy_changed sinyalinin yayıldığını doğrular.
    """
    p = Player(pid=0)
    p.economy.gold = 10
    
    signal_fired = False
    def on_change():
        nonlocal signal_fired
        signal_fired = True
        
    p.economy._on_change = on_change
    
    success = p.economy.spend_gold(2)
    
    assert success is True
    assert p.economy.gold == 8
    assert signal_fired is True, "Economy signal should be emitted on spend_gold"

def test_public_state_immutability():
    """
    Paket 3 & 4: PublicState içindeki koleksiyonların tuple olduğunu ve değiştirilemediğini doğrular.
    """
    from v2.core.public_state import ShopViewState, SynergyViewState
    
    # Basit bir snapshot simülasyonu
    shop = ShopViewState(slots=("Card A", "Card B"), is_locked=False, rarity_probabilities={})
    
    with pytest.raises(TypeError):
        # Tuple immutable olmalı
        shop.slots[0] = "Hacked"
        
    syn = SynergyViewState(groups=(), total=0, passive_feed=(), active_effects=())
    assert isinstance(syn.groups, tuple)
    assert isinstance(syn.passive_feed, tuple)

def test_adapter_reroll_uses_formal_api():
    """
    Paket 1: EngineAdapter.perform_reroll'un economy API'sini kullandığını doğrular.
    """
    p = Player(pid=0)
    p.economy.gold = 10
    game = Game(players=[p])
    adapter = EngineAdapter(game)
    
    # Sinyali dinle
    signal_fired = False
    def on_change():
        nonlocal signal_fired
        signal_fired = True
    p.economy._on_change = on_change
    
    adapter.perform_reroll(0)
    
    assert p.economy.gold == 8
    assert signal_fired is True, "Reroll should trigger economy signal via spend_gold"

def test_game_init_signal_safety_and_connection():
    """
    Paket: Game.__init__ içindeki SignalBus yarış durumunu ve sinyal bağlantılarını doğrular.
    """
    p = Player(pid=0)
    # Game init sırasında _deal_starting_hands tetiklenir, bu da add_to_hand çağırır, 
    # o da _emit_change çağırır. Eğer signals henüz atanmamışsa AttributeError fırlatır.
    game = Game(players=[p])
    
    # AttributeError fırlatmadan buraya gelmiş olması ilk aşama doğrulamadır.
    assert hasattr(game, "signals"), "Game should have signals attribute"
    assert game.signals is not None
    
    # Sinyallerin gerçekten bağlandığını doğrula (AAA Kalite)
    assert p.economy._on_change is not None, "Economy signal should be connected"
    assert p.inventory._on_change is not None, "Inventory signal should be connected"
    assert p.board._mutation_callback is not None, "Board mutation signal should be connected"

def test_turn_manager_isolated_independence():
    """
    TurnManager'ın Game nesnesi ve sinyaller olmadan da (None enjeksiyonuyla) 
    güvenli bir şekilde çalışabildiğini doğrular.
    """
    from engine_core.turn_manager import TurnManager
    from engine_core.player import Player
    from engine_core.market import Market
    import random
    
    players = [Player(pid=0), Player(pid=1)]
    market = Market([], rng=random.Random(42))
    
    # signals ve action_log None geçilmesine rağmen start_turn çökmemeli (defensive checks)
    tm = TurnManager(
        players=players,
        market=market,
        rng=random.Random(42),
        trigger_passive_fn=None,
        next_card_uid_fn=lambda: 1,
        ai_class=None,
        signals=None,
        action_log=None
    )
    
    tm.start_turn()
    assert tm.turn == 1

def test_selective_cache_invalidation_by_pid():
    """
    GameState'in yalnızca pid=0 sinyallerinde cache invalidate ettiğini, 
    AI mutasyonlarını (pid=1) yok saydığını doğrular.
    """
    from engine_core.game import Game
    from engine_core.player import Player
    from v2.core.game_state import GameState
    
    p0 = Player(pid=0)
    p1 = Player(pid=1)
    game = Game(players=[p0, p1])
    gs = GameState()
    gs.hook_engine(game)
    
    # 1. Cache'i oluştur
    state = gs.get_public_state()
    assert gs._cached_public_state is not None
    
    # 2. AI mutasyonu (pid=1) tetikle -> Cache BOZULMAMALI
    game.signals.economy_changed.emit(pid=1)
    assert gs._cached_public_state is not None, "AI mutation should not invalidate UI cache"
    
    # 3. İnsan mutasyonu (pid=0) tetikle -> Cache BOZULMALI
    game.signals.economy_changed.emit(pid=0)
    assert gs._cached_public_state is None, "Human mutation MUST invalidate UI cache"
    
    # 4. Global sinyal (pid yok) -> Cache BOZULMALI
    gs.get_public_state() # rebuild
    game.signals.turn_started.emit(turn=1)
    assert gs._cached_public_state is None, "Global signal MUST invalidate UI cache"
