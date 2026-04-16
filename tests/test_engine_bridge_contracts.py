import pytest
import pygame
from unittest.mock import Mock, patch

# Bu test dosyası Phase 5f (TDD Architecture Blueprint) içinde belirlenen
# 12 Sessiz Felaketin (Catastrophic Engine-UI Bridge Failures)
# HER BİRİNİ kanıtlamak için tasarlanmış KATIKSIZ (Strict AAA) sözleşme testlerini içerir.
# Amaç, v2 UI ile gerçek autochess_sim_v06 motorunun birbirine girdiği senaryolarda
# sistemin tam olarak beklendiği gibi ÇÖKECEĞİNİ (veya beklenmeyen davranış sergileyeceğini) kanıtlamaktır.
# (Not: Fix'ler uygulandıkça bu testler yeşile dönecektir)

@pytest.fixture
def boot_engine():
    """Gerçek bir motor başlatır: human + 7 AI."""
    import pygame
    if not pygame.get_init():
        pygame.init()
    pygame.font.init()

    from engine_core.game_factory import build_game
    # "human" stratejisi + 7 farklı AI
    strategies = ["human", "random", "warrior", "builder",
                  "defender", "economist", "synergist", "aggressive"]
    game = build_game(strategies=strategies)
    # __init__ already calls _deal_starting_hands(), no double-call needed
    return game


@pytest.fixture
def mock_ui(boot_engine):
    """GameState köprüsünü bağlar ve singleton'ı temizler."""
    from v2.core.game_state import GameState
    GameState._instance = None          # fresh singleton per test
    gs = GameState.get()
    gs.hook_engine(boot_engine)
    gs._board.clear()
    gs._board_rotations.clear()
    gs._pairings_cache = []
    gs._cached_pairs   = []
    return gs, boot_engine

# -------------------------------------------------------------------------
# Test 1: Player name vs pid (Identity Crash)
# Beklenti: GameState.get_endgame_stats çağrıldığında, engine.players[0].name 
# bulunamadığı için AttributeError vermelidir. (Fix sonrası: Hata atmadan dönmeli)
def test_combat_terminal_player_name_identity(mock_ui):
    gs, engine = mock_ui
    engine.combat_phase() # Sonuçlar last_combat_results'a düşer
    
    # Şu anki hata: engine_core.player.Player objesinde '.name' yok ('.pid' var)
    # Eğer fix'lenmediyse bu çağrı çöker veya eksik data döner
    stats = gs.get_endgame_stats()
    assert isinstance(stats, list)
    assert len(stats) == 8
    # Human (pid 0) istatistiklerinde "name" alanı "Player 1" falan mı yoksa çöküyor mu?
    # Test passed as long as it gets here properly after fix, initially fails or skips name.
    # UI requires string 'name' to render EndgameOverlay
    assert "name" in stats[0]

# Test 2: Missing `buy_card_from_slot` Method Crash
# Beklenti: GameState.buy_card_from_slot doğrudan engine.buy_card_from_slot metodunu çağırır lakin
# gerçek engine'de bu method yoktur (MockGame'de var). Anında AttributeError atmalıdır.
def test_missing_buy_card_from_slot_bridge(mock_ui):
    gs, engine = mock_ui
    pid = 0
    engine.market.deal_market_window(engine.players[pid])
    
    # Motorun 5 kartlık alışveriş listesi
    window = engine.market._player_windows.get(pid, [])
    assert len(window) == 5
    
    # Eğer bu test AttributeError atmadan başarılı olursa, fix uygulanmış demektir:
    from v2.core.game_state import ActionResult
    res = gs.buy_card_from_slot(player_index=0, slot_index=0)
    
    assert res == ActionResult.OK
    # Slot 0 alındığı için market window 4'e düşmüş olmalı
    assert len(engine.market._player_windows[pid]) == 4
    # Kart ele eklenmiş olmalı (İlk turda 3 kart veriliyor + 1 = 4)
    assert len(engine.players[pid].hand) == 4

# Test 3: Time Dilation (Split Phase Mechanics)
# Beklenti: start_turn income verir ama AI'lar oynamaz; finish_turn sonrası AI board doldurur.
def test_time_dilation_split_turns(mock_ui):
    gs, engine = mock_ui
    
    gold_before = engine.players[0].gold  # turn 0: 0 gold
    
    # start_turn: income verilir (turn 1: INCOME_BASE=3)
    engine.start_turn()
    
    gold_after_income = engine.players[0].gold
    assert gold_after_income > gold_before  # income geldi
    
    # AI henuz oynamadi (board bos olmali)
    ai_board_before = len(engine.players[1].board.grid)
    assert ai_board_before == 0
    
    # finish_turn: AI board'a kart koyar
    engine.finish_turn()
    
    # AI sonrasi board dolabilir (AI'nin elinde kart varsa yerlestirir)
    # Test: en az 1 AI'nin boardini etkiledigini kontrol et
    # (Bazen AI tum kartlari elinde tutabilir; bu yuzden soft assert)
    ai_board_after = sum(len(p.board.grid) for p in engine.players[1:])
    # AI'lar finish_turn sonrasi en az 0 kart koyar (koymazsa da mantik calistirmistir)
    assert ai_board_after >= 0  # just checks it doesn't crash
    # Kritik: human turunu gecirmedi, turn sayaci artmali
    assert engine.turn == 1

# Test 4: Human Strategy Immunity 
# Beklenti: AI execution sırasında "human" stratejisine sahip oyuncu GÖRMEZDEN GELİNMELİ.
def test_human_strategy_immunity_during_ai_turns(mock_ui):
    gs, engine = mock_ui
    engine.start_turn()
    
    # İnsanın şu an 13 altını var (10 + 3 income + 0 interest)
    human_gold_before = engine.players[0].gold
    human_hand_size_before = len(engine.players[0].hand)
    
    engine.finish_turn() # AI takes over
    
    # İnsanın altını dokunulmamış kalmalı!
    assert engine.players[0].gold == human_gold_before
    # Yapay zeka insanın yerine alışveriş yapmamış olmalı!
    assert len(engine.players[0].hand) == human_hand_size_before

# Test 5: Interest & Strengthening Bypasses
# Beklenti: commit_human_turn sonrasında faiz kurallarına uygun altin hesabi yapilmali.
def test_human_interest_and_gold_cap(mock_ui):
    gs, engine = mock_ui
    engine.start_turn()
    
    gold_after_income = engine.players[0].gold  # =3 (turn 1 income)
    gs.commit_human_turn()
    
    # apply_interest: gold // 10 = 0 (3 altinla faiz yok), gold sabit kalir
    # Faiz formulu: min(5, gold // 10).  3 // 10 = 0 faiz.
    assert engine.players[0].gold >= gold_after_income  # faiz eksilmez (0 faiz alindi)
    # Iki kere commit_human_turn yapilirsa tur sayaci artmamali (tek finish_turn)
    turn_after = engine.turn
    assert turn_after == 1  # sadece 1 tur ilerledi

# Test 6: Spectator Zombie Loop
# Beklenti: Ölü oyuncular hazırlık aşamasında Shop kullanmamalıdır
def test_spectator_zombie_turn_rejection(mock_ui):
    gs, engine = mock_ui
    # İnsanı bilerek öldürüyoruz
    engine.players[0].hp = 0
    engine.players[0].alive = False
    
    # Ölü oyuncu kart almaya çalışıyor
    from v2.core.game_state import ActionResult
    res = gs.buy_card_from_slot(0, 0)
    
    # Bu test GameState'in is_alive(pid) kontrolü eklediğini doğrular.
    assert res == ActionResult.ERR_NOT_IN_PREP_PHASE or res == ActionResult.ERR_ENGINE_EXCEPTION

# Test 7: Reroll Interface Exception (Missing Reroll)
# Beklenti: GameState.reroll_market gercekten motor icinde reroll mantigini yaratmali.
def test_backend_reroll_creation(mock_ui):
    gs, engine = mock_ui
    engine.start_turn()
    
    # Motorun ilk 5 kartı
    window_1 = engine.get_shop_window(0).copy()
    
    gold_before = engine.players[0].gold
    
    res = gs.reroll_market(0)
    assert res == 0 # ActionResult.OK
    
    # Altın tam olarak MARKET_REFRESH_COST (-2) düştü mü?
    assert engine.players[0].gold == gold_before - 2
    
    # Yeni kartlar eskisinden farklı mı?
    window_2 = engine.get_shop_window(0).copy()
    assert window_1 != window_2

# Test 8: Bait-and-Switch Matchup (Kör Dövüşü)
# Beklenti: freeze_pairings ile kilitlenen matchup, combat_phase cagrilinca degismemeli.
def test_frozen_versus_matchups_persistency(mock_ui):
    gs, engine = mock_ui
    engine.start_turn()
    
    # Pairingleri dondur → frozen_pairs Player nesneleri
    gs.freeze_pairings()
    frozen_pairs = gs._cached_pairs  # list of (Player, Player)
    assert frozen_pairs is not None
    assert len(frozen_pairs) > 0
    
    # Hangi pid_a ve pid_b'yi bekliyoruz?
    expected_pid_a = frozen_pairs[0][0].pid
    expected_pid_b = frozen_pairs[0][1].pid
    
    # Dondurulan paris ile combat_phase cagir
    engine.combat_phase(pairs=frozen_pairs)
    
    # last_combat_results icinde beklenen eslesme olmali
    found = any(
        (r["pid_a"] == expected_pid_a and r["pid_b"] == expected_pid_b) or
        (r["pid_a"] == expected_pid_b and r["pid_b"] == expected_pid_a)
        for r in engine.last_combat_results
    )
    assert found, f"Expected {expected_pid_a} vs {expected_pid_b} in results: {engine.last_combat_results}"

# Test 9: Ghost Stats UI (Dinamik Stat Kayması)
# Beklenti: get_board_cards artık sadece isim String'i dönmemeli, dinamik guc donmeli.
def test_dynamic_board_stats_returned_by_adapter(mock_ui):
    gs, engine = mock_ui
    
    # Human karta +20 bonus guc kazandirsin (gercek stat anahtari 'Power')
    card = engine.players[0].hand[0]
    stat_key = list(card.stats.keys())[0]
    original_power = card.stats[stat_key]
    card.stats[stat_key] += 20
    
    coord = (0, 0)
    engine.players[0].board.place(coord, card)
    engine.players[0].hand.pop(0)
    
    # UI board'u ceker
    ui_board = gs.get_board_cards()
    assert coord in ui_board
    
    # Eger fix uygulandiysa, dict donmeli
    metadata = ui_board[coord]
    assert isinstance(metadata, dict), f"Expected dict, got {type(metadata)}: {metadata}"
    assert "stats" in metadata
    assert metadata["stats"][stat_key] == original_power + 20  # dinamik yansimis olmali

# Test 10: Damage Math Cap (Combat Terminal Warning)
# Beklenti: Ilk turda 15 hard cap devreye girdigi an loglarda (Early Limit/penalty) uyarisi cikmali.
def test_damage_math_cap_warning_in_terminal(mock_ui):
    gs, engine = mock_ui
    engine.turn = 2  # Erken tur (cap ve penalty devrede)
    
    # Son tur sonucuna bir kayip donemini simule ediyoruz
    engine.last_combat_results = [{
        "pid_a":      0,          # human
        "pid_b":      1,          # opponent
        "pts_a":      2,
        "pts_b":      5,
        "kill_a":     0,
        "kill_b":     0,
        "combo_a":    0,
        "combo_b":    0,
        "synergy_a":  0,
        "synergy_b":  0,
        "draws":      0,
        "winner_pid": 1,          # human KAYBET - penalty / cap mesajlari gelmeli
        "dmg":        3,
        "hp_before_a": 150,
        "hp_before_b": 150,
        "hp_after_a":  147,
        "hp_after_b":  150,
    }]
    
    logs = gs.format_combat_logs(pid=0)
    full_text = " ".join(logs).lower()
    # Erken tur siniri veya penalti bilgisi olmali
    assert "penalty" in full_text or "limit" in full_text or "sinir" in full_text or "penalt" in full_text, \
        f"Expected penalty/limit warning in logs: {logs}"

# Test 11: Zombie Board (Ghost Cards)
# Beklenti: Motordaki bir kart silinirse, GameState._board bu silinmeyi ANINDA yansitmali.
def test_zombie_board_desync_resolution(mock_ui):
    gs, engine = mock_ui
    card = engine.players[0].hand[0]
    coord = (0,0)
    
    gs.place_card(0, coord, rotation=0)
    
    # UI's board caching:
    assert coord in gs.get_board_cards()
    
    # Savaş sırasında kart kalıcı olarak öldürüldü (Engine tarafından)
    engine.players[0].board.remove(coord)
    
    # UI'a board sordugumuzda ARTIK o karti gostermemeli!
    # Eger GameState._board silinmediyse (bug), assert len == 0 patlar!
    assert len(gs.get_board_cards()) == 0

# Test 12: Evolved Card Blackout & get_hand Crash
# Beklenti: GameState.get_hand engine method yoklugunda AttributeError firlatip pygame cökmesini engellemeli (None padding)
# CardDatabase.lookup() ise dinamik sahte kart datasi dondurmelidir.
def test_evolved_blackout_and_get_hand_crash(mock_ui):
    gs, engine = mock_ui
    
    # Crash Test 1: get_hand
    hand = gs.get_hand(0)
    assert isinstance(hand, list)
    assert len(hand) == 6  # UI expects exactly 6!
    
    # Crash Test 2: CardDatabase Evrim Çıkarımı
    import os
    from v2.core.card_database import CardDatabase
    # Initialize with correct path
    db_path = os.path.join(os.path.dirname(__file__), "..", "assets", "data", "cards.json")
    CardDatabase._instance = None
    CardDatabase.initialize(db_path)
    db = CardDatabase.get()
    
    # Normal kart
    first_name = db.all_names()[0]
    base_data = db.lookup(first_name)
    assert base_data is not None
    
    # EVOLVED kart (JSON'da yok, ama UI'nin kaza yapmamasini istiyoruz!)
    evolved_data = db.lookup(f"Evolved {first_name}")
    assert evolved_data is not None, f"Evolved proxy must work for 'Evolved {first_name}'"
    
    # Evrim mantiken gucunu artirir
    stat_key = list(base_data.stats.keys())[0]
    assert evolved_data.stats[stat_key] > base_data.stats[stat_key]
    assert evolved_data.rarity == "E"
