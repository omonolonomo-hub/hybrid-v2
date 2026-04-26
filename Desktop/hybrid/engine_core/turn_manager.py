"""
engine_core/turn_manager.py
═══════════════════════════════════════════════════════════════════════
Faz 3 — TurnManager Ayrımı

game.py'den ayrıştırılan tur yönetim mantığı.  Sorumlulukları:

  • start_turn()          — tur sayacı, gelir dağıtımı, market açılışı
  • finish_turn()         — AI satın alma / yerleştirme, faiz, evrim
  • preparation_phase()  — start_turn + finish_turn zinciri (AI sim. yolu)
  • swiss_pairs()         — canlı oyuncu eşleştirmesi
  • _deal_starting_hands() — başlangıç kartı dağıtımı (init'te çağrılır)
  • _clear_transient_board_state() — combat öncesi/sonrası kart temizleme

game.py bu sınıfı oluşturur ve start/finish/preparation/swiss
çağrılarını buraya delege eder.

Bağımlılık kuralı:
  TurnManager → players, market, rng, trigger_passive_fn, ai_class
  TurnManager DOES NOT import game.py  (ters yön yok)
═══════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import warnings
import logging
from typing import Callable, Dict, List, Optional, Tuple

from engine_core.board_utils import iter_board_cards, clear_transient_board_state
from engine_core.progression_system import ProgressionSystem

logger = logging.getLogger(__name__)


class TurnManager:
    """Tur akışını yöneten bağımsız sınıf.

    Game nesnesi olmadan doğrudan örneklenebilir; dependency injection ile
    tüm bağımlılıkları dışarıdan alır.
    """

    def __init__(
        self,
        players,
        market,
        rng,
        trigger_passive_fn: Optional[Callable],
        next_card_uid_fn: Callable,
        ai_class,
        verbose: bool = False,
        signals: Optional[SignalBus] = None,
        action_log: Optional[ActionLog] = None,
    ) -> None:
        """
        Args:
            players:            Player listesi (Game ile paylaşılır).
            market:             Market nesnesi (Game ile paylaşılır).
            rng:                random.Random() örneği.
            trigger_passive_fn: passive_trigger.trigger_passive veya None.
            next_card_uid_fn:   Benzersiz kart UID üreteci (Game.next_card_uid).
            ai_class:           AI sınıfı (veya ParameterizedAI örneği).
            verbose:            Ayrıntılı log açık/kapalı.
            signals:            SignalBus örneği (opsiyonel).
            action_log:         ActionLog örneği (opsiyonel).
        """
        self._players          = players
        self._market           = market
        self._rng              = rng
        self._trigger_passive  = trigger_passive_fn
        self._next_card_uid_fn = next_card_uid_fn
        self._ai               = ai_class
        self._verbose          = verbose
        self._signals          = signals
        self._action_log       = action_log

        # Tur sayacı — tek gerçek kaynak; Game.turn bu değeri property ile okur
        self.turn: int = 0

        # start_turn()'ün açtığı pencereler, finish_turn()'ün tüketmesi için saklanır
        self._current_player_markets: Dict[int, list] = {}

        # Dahili log tamponu
        self._log_buf: List[str] = []

        # Evrim kontrolü için ad→kart haritası (market.pool'dan türetilir)
        self._card_by_name = {c.name: c for c in market.pool}

        # Lobby: her oyuncuya 3 başlangıç kartı dağıt
        self._deal_starting_hands()

    # ── Yardımcı: loglama ────────────────────────────────────────────────────

    def _log(self, msg: str) -> None:
        if self._verbose:
            print(msg)
        self._log_buf.append(msg)

    # ── Yardımcı: canlı oyuncular ────────────────────────────────────────────

    def alive_players(self):
        return [p for p in self._players if p.alive]

    # ── Yardımcı: board kart iteratörü ──────────────────────────────────────

    @staticmethod
    def _iter_board_cards(players):
        """Backward-compat — delegates to board_utils.iter_board_cards()."""
        warnings.warn(
            "_iter_board_cards is deprecated; use board_utils.iter_board_cards() directly.",
            DeprecationWarning, stacklevel=2
        )
        return iter_board_cards(players)

    # ── Yardımcı: geçici board state temizleme ───────────────────────────────

    def _clear_transient_board_state(
        self,
        players,
        *,
        current_turn: int,
        clear_combat_meta: bool,
    ) -> None:
        """Backward-compat — delegates to board_utils.clear_transient_board_state()."""
        warnings.warn(
            "_clear_transient_board_state is deprecated; use board_utils.clear_transient_board_state() directly.",
            DeprecationWarning, stacklevel=2
        )
        clear_transient_board_state(players, current_turn=current_turn, clear_combat_meta=clear_combat_meta)

    # ── Başlangıç kartı dağıtımı ─────────────────────────────────────────────

    def _deal_starting_hands(self) -> None:
        """Her oyuncuya 3 adet common (rarity='1') başlangıç kartı dağıt."""
        common_cards = [c for c in self._market.pool if c.rarity == "1"]
        for player in self._players:
            chosen = self._rng.sample(common_cards, min(3, len(common_cards)))
            for card in chosen:
                cloned      = card.clone()
                cloned.uid  = self._next_card_uid_fn()
                
                # Use formal API to ensure signal emission and state consistency
                dropped = player.inventory.add_to_hand(cloned)
                if dropped is not None:
                    logger.warning(
                        "Starting hand overflow: card '%s' dropped for P%d",
                        dropped.name, player.pid
                    )
            self._log(
                f"  P{player.pid} starting cards: "
                f"{', '.join(c.name for c in chosen)}"
            )

    # ── Swiss eşleştirme ─────────────────────────────────────────────────────

    def swiss_pairs(self) -> List[Tuple]:
        """Canlı oyuncuları HP'ye göre sırala, en yakın rakipleri eşleştir."""
        alive = self.alive_players()
        # Aynı HP bandında varyasyon için hafif jitter
        alive.sort(key=lambda p: p.hp + self._rng.random() * 0.5, reverse=True)
        pairs: List[Tuple] = []
        used: set = set()
        for i, p1 in enumerate(alive):
            if p1.pid in used:
                continue
            for j in range(i + 1, len(alive)):
                p2 = alive[j]
                if p2.pid not in used:
                    pairs.append((p1, p2))
                    used.add(p1.pid)
                    used.add(p2.pid)
                    break
        return pairs

    # ══════════════════════════════════════════════════════════════════════════
    # start_turn() — Faz 1/2: tur sayacı + gelir + market
    # ══════════════════════════════════════════════════════════════════════════

    def start_turn(self) -> None:
        """Tur sayacını artır, gelir dağıt, market pencerelerini aç.

        AI satın alma/yerleştirme mantığı çalıştırmaz — bu finish_turn()'e aittir.
        Human oyuncunun dükkanı görmesine izin vermek için ikiye bölünmüş tasarım.
        """
        self.turn += 1
        _turn            = self.turn
        _log             = self._log

        # ActionLog record
        if self._action_log:
            self._action_log.record("turn_start", {"turn": _turn}, turn=_turn)
        
        # Signal emission
        if self._signals:
            self._signals.turn_started.emit(turn=_turn)

        _verbose         = self._verbose
        _trigger_passive = self._trigger_passive
        _market          = self._market

        _log(f"\n{'-'*50}\n  TURN {_turn} — PREPARATION START\n{'-'*50}")

        alive = self.alive_players()
        self._clear_transient_board_state(alive, current_turn=_turn, clear_combat_meta=True)

        # Market pencerelerini aç (shop_locked olanları atla)
        self._current_player_markets = {}
        for player in alive:
            if not getattr(player, "shop_locked", False):
                self._current_player_markets[player.pid] = _market.deal_market_window(player, 5)
            else:
                # Kilitli dükkan: mevcut pencereyi koru, gelecek tur için kilidi aç
                self._current_player_markets[player.pid] = _market._player_windows.get(
                    player.pid, []
                )
                player.shop_locked = False
            
            # ActionLog record market deal
            if self._action_log:
                market_cards = [c.name if c else None for c in self._current_player_markets[player.pid]]
                self._action_log.record("market_deal", {"pid": player.pid, "cards": market_cards}, turn=_turn)

        # Tüm canlı oyunculara gelir ver (human dahil)
        for player in alive:
            player.income()
            # H3-2: Provide market_window and market ref for passive triggers
            player_market = self._current_player_markets.get(player.pid, [])
            _ctx = {
                "turn": _turn,
                "game": None,
                "market": _market,
                "market_window": player_market,
                "card_by_name": self._card_by_name
            }
            
            if _trigger_passive:
                for card in tuple(player.board.grid.values()):
                    _trigger_passive(card, "income", player, None, _ctx, verbose=_verbose)
            if _trigger_passive:
                for card in tuple(player.board.grid.values()):
                    _trigger_passive(card, "market_refresh", player, None, _ctx, verbose=_verbose)

    # ══════════════════════════════════════════════════════════════════════════
    # finish_turn() — Faz 2/2: AI eylemleri + faiz + evrim
    # ══════════════════════════════════════════════════════════════════════════

    def finish_turn(self) -> None:
        """Human olmayan oyuncular için AI mantığını çalıştır; ardından tüm
        oyuncular için faiz, evrim, copy-strengthening ve istatistik güncelle.

        Human oyuncunun altınına veya eline dokunulmaz.
        """
        if not self._current_player_markets:
            import logging
            logging.getLogger(__name__).warning(
                "TurnManager.finish_turn() called before start_turn() — "
                "player markets are empty. This is likely a call order bug."
            )

        _turn            = self.turn
        _log             = self._log
        _verbose         = self._verbose
        _trigger_passive = self._trigger_passive
        _market          = self._market
        _rng             = self._rng
        _ai              = self._ai
        _next_uid        = self._next_card_uid_fn
        _card_by_name    = self._card_by_name

        alive          = self.alive_players()
        player_markets = self._current_player_markets  # start_turn'ün açtığı pencereler

        for player in alive:
            player_market = player_markets.get(player.pid, [])

            # ── Satın alma ────────────────────────────────────────────────────
            if player.strategy == "human":
                # Human kendi satın almalarını GameState.buy_card_from_slot ile yapar
                newly_bought = None
            else:
                hand_before  = len(player.hand)
                _ai.buy_cards(
                    player, player_market,
                    market_obj=_market,
                    next_uid_fn=_next_uid,
                    rng=_rng,
                    trigger_passive_fn=_trigger_passive,
                )
                newly_bought = player.hand[hand_before:]

            # ── Satılmayan kartları pool'a iade et ───────────────────────────
            if not getattr(player, "shop_locked", False):
                _market.return_unsold(player, bought=newly_bought)
            else:
                if hasattr(player, "_window_bought"):
                    player._window_bought = []

            # ── Ekonomi ───────────────────────────────────────────────────────
            player.apply_interest()

            evos = ProgressionSystem.check_evolution(player, market=_market, card_by_name=_card_by_name)
            if evos and _verbose:
                for base_name in evos:
                    _log(
                        f"  *** EVOLUTION: P{player.pid} evolved "
                        f"{base_name} -> Evolved {base_name}! ***"
                    )

            # ── Yerleştirme (yalnızca AI) ─────────────────────────────────────
            if player.strategy != "human":
                _ai.place_cards(player, rng=_rng)

            # ── Copy güçlendirme ──────────────────────────────────────────────
            if _trigger_passive:
                ProgressionSystem.check_copy_strengthening(player, _turn, trigger_passive_fn=_trigger_passive)

            # ── Tur sonu istatistikleri ───────────────────────────────────────
            for _c in player.board.grid.values():
                player.card_turns_alive[_c.name] = (
                    player.card_turns_alive.get(_c.name, 0) + 1
                )
                player.stats["board_power"] += _c.total_power()
                player.stats["unit_count"]  += 1
            player.stats["gold_per_turn"] += player.gold

    # ══════════════════════════════════════════════════════════════════════════
    # preparation_phase() — Tam hazırlık turu (AI simülasyon yolu)
    # ══════════════════════════════════════════════════════════════════════════

    def preparation_phase(self) -> None:
        """start_turn() + finish_turn() zincirine eşdeğer.

        game.run() (tam AI simülasyonu) bu yöntemi çağırır.
        Human oyunlu UI akışı start_turn / finish_turn'ü ayrı çağırır.
        """
        self.start_turn()
        self.finish_turn()
