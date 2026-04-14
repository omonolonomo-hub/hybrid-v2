from enum import IntEnum

class ActionResult(IntEnum):
    OK              = 0
    ERR_INSUFFICIENT_GOLD  = 1
    ERR_SLOT_OCCUPIED      = 2
    ERR_POOL_EMPTY         = 3
    ERR_INVALID_COORD      = 4
    ERR_PLACE_LOCKED       = 5
    ERR_INVALID_HAND_IDX   = 6
    ERR_NOT_IN_PREP_PHASE  = 7
    ERR_ENGINE_EXCEPTION   = 99

class GameState:
    _instance = None

    def __init__(self):
        self._engine = None
        self._board: dict[tuple[int, int], str] = {}       # (q,r) → card_name
        self._board_rotations: dict[tuple[int, int], int] = {}  # (q,r) → rotation (0-5)
        self.place_locked: bool = False

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = GameState()
        return cls._instance

    def hook_engine(self, engine):
        """MockGame veya gerçek engine_core motorunu UI'a bağlar."""
        self._engine = engine

    def get_gold(self, player_index: int = 0) -> int:
        if not self._engine:
            return 0
        return self._engine.players[player_index].gold

    def get_hp(self, player_index: int = 0) -> int:
        if not self._engine:
            return 0
        return self._engine.get_hp(player_index)

    def get_shop(self, player_index: int = 0) -> list:
        """Dükkan penceresi: 5 elemanlı liste [card_name | None]"""
        if not self._engine:
            return [None] * 5
        return self._engine.get_shop_window(player_index)

    def get_hand(self, player_index: int = 0) -> list:
        """El: HAND_MAX_CARDS elemanlı liste [card_name | None]"""
        if not self._engine:
            return [None] * 6
        return self._engine.get_hand(player_index)

    def buy_card(self, player_index: int, card_id: int, cost: int) -> ActionResult:
        """Kullanıcının kart alım isteğini motora iletir ve güvenli Enum yanıtı döner."""
        if not self._engine:
            return ActionResult.ERR_ENGINE_EXCEPTION
        player = self._engine.players[player_index]
        if player.gold >= cost:
            player.gold -= cost
            return ActionResult.OK
        return ActionResult.ERR_INSUFFICIENT_GOLD

    def buy_card_from_slot(self, player_index: int, slot_index: int) -> ActionResult:
        if not self._engine:
            return ActionResult.ERR_ENGINE_EXCEPTION
        ok = self._engine.buy_card_from_slot(player_index, slot_index)
        return ActionResult.OK if ok else ActionResult.ERR_POOL_EMPTY

    def reroll_market(self, player_index: int = 0) -> ActionResult:
        if not self._engine:
            return ActionResult.ERR_ENGINE_EXCEPTION
        ok = self._engine.reroll_market(player_index)
        return ActionResult.OK if ok else ActionResult.ERR_INSUFFICIENT_GOLD

    def toggle_lock_shop(self, player_index: int = 0) -> None:
        if self._engine:
            self._engine.toggle_lock_shop(player_index)

    # ── Board / Placement ───────────────────────────────────────────────

    def get_board_cards(self) -> dict[tuple[int, int], str]:
        """Board üzerindeki kartlar: {(q, r): card_name}"""
        return self._board

    def get_board_rotations(self) -> dict[tuple[int, int], int]:
        """Board üzerindeki kartların rotasyonları: {(q, r): rotation (0-5)}"""
        return self._board_rotations

    def place_card(self, hand_index: int, coord: tuple[int, int],
                   rotation: int = 0) -> 'ActionResult':
        """
        Elden kartı board'a yerleştirir.
        Spec Section 2.1 — tek kart/tur kuralı (place_locked).
        """
        if self.place_locked:
            return ActionResult.ERR_PLACE_LOCKED
        if coord in self._board:
            return ActionResult.ERR_SLOT_OCCUPIED
        if not self._engine:
            return ActionResult.ERR_ENGINE_EXCEPTION

        player = self._engine.players[0]
        if hand_index < 0 or hand_index >= len(player.hand):
            return ActionResult.ERR_INVALID_HAND_IDX

        card_name = player.hand[hand_index]
        if card_name is None:
            return ActionResult.ERR_INVALID_HAND_IDX

        self._board[coord] = card_name
        self._board_rotations[coord] = rotation % 6
        # Engine board sync (gerçek Card nesnesi varsa — Section 2.4 çift-yazma sözleşmesi)
        raw = player.hand[hand_index]
        if hasattr(raw, 'rotation'):      # gerçek Card nesnesi (MockGame'de string, skip)
            raw.rotation = rotation % 6
            player.board.place(coord, raw)
        player.hand[hand_index] = None
        # self.place_locked = True  # DEV: çok kart testi için devre dışı
        return ActionResult.OK

    def reset_turn(self) -> None:
        """Tur başında place_locked sıfırlanır."""
        self.place_locked = False

    def get_adjacency_pairs(self) -> list[tuple]:
        """
        Board'daki komşu kart çiftleri için karşılıklı KENAR bilgilerini döndürür.
        Dönen format: [(coord_a, coord_b, group_a, group_b), ...]
          group_a = A'nın B'ye bakan kenarının stat grubu
          group_b = B'nin A'ya bakan kenarının stat grubu
        Her çift yalnızca bir kez görünür (dedupe).
        Motor gibi: card.edges[dir] = (stat_name, value), rotation=0 varsayımı.
        """
        from v2.core.card_database import CardDatabase
        from v2.constants import ENGINE_HEX_DIRS, OPP_DIR, STAT_TO_GROUP

        try:
            db = CardDatabase.get()
        except RuntimeError:
            return []

        pairs: list[tuple] = []
        seen:  set = set()

        for coord, card_name in self._board.items():
            data = db.lookup(card_name)
            if not data:
                continue
            edges_a = list(data.stats.items())   # [(stat_name, val), ...] len=6, orijinal sıra
            if len(edges_a) < 6:
                continue
            rot_a = self._board_rotations.get(coord, 0)

            q, r = coord
            for dir_idx, (dq, dr) in enumerate(ENGINE_HEX_DIRS):
                nb = (q + dq, r + dr)
                if nb not in self._board:
                    continue

                pair_key = (min(coord, nb), max(coord, nb))
                if pair_key in seen:
                    continue
                seen.add(pair_key)

                nb_data = db.lookup(self._board[nb])
                if not nb_data:
                    continue
                edges_b = list(nb_data.stats.items())
                if len(edges_b) < 6:
                    continue
                rot_b = self._board_rotations.get(nb, 0)

                # Rotation uygulaması:
                # Kart rot adım döndürülmüşse, dir_idx yönündeki gerçek kenar
                # orijinal karttaki (dir_idx - rot) % 6 indexindedir.
                real_idx_a = (dir_idx - rot_a) % 6
                real_idx_b = (OPP_DIR[dir_idx] - rot_b) % 6

                group_a = STAT_TO_GROUP.get(edges_a[real_idx_a][0], "")
                group_b = STAT_TO_GROUP.get(edges_b[real_idx_b][0], "")
                pairs.append((coord, nb, group_a, group_b))

        return pairs

    # ── Yeni accessor'lar (Phase 3c / Section 2.4) ──────────────────────────

    def get_turn(self) -> int:
        try:
            return self._engine.turn
        except Exception:
            return 1

    def get_alive_pids(self) -> list:
        try:
            return [p.pid for p in self._engine.players if getattr(p, 'alive', True)]
        except Exception:
            return list(range(8))

    def get_win_streak(self, player_index: int = 0) -> int:
        try:
            return self._engine.players[player_index].win_streak
        except Exception:
            return 0

    def get_copies(self, card_name: str, player_index: int = 0) -> int:
        try:
            return self._engine.players[player_index].copies.get(card_name, 0)
        except Exception:
            return 0

    def is_alive(self, player_index: int = 0) -> bool:
        try:
            return bool(self._engine.players[player_index].alive)
        except Exception:
            return True

    def get_total_pts(self, player_index: int = 0) -> int:
        try:
            return self._engine.players[player_index].total_pts
        except Exception:
            return 0

    def get_turn_pts(self, player_index: int = 0) -> int:
        try:
            return self._engine.players[player_index].turn_pts
        except Exception:
            return 0

    def get_last_combat_results(self) -> list:
        try:
            return self._engine.last_combat_results
        except Exception:
            return []

    def get_passive_buff_log(self, player_index: int = 0) -> list:
        try:
            return self._engine.players[player_index].passive_buff_log
        except Exception:
            return []

    def get_stats(self, player_index: int = 0) -> dict:
        try:
            return self._engine.players[player_index].stats
        except Exception:
            return {"wins": 0, "losses": 0, "draws": 0,
                    "market_rolls": 0, "evolutions": 0, "win_streak_max": 0}

    def has_catalyst(self, player_index: int = 0) -> bool:
        try:
            return bool(self._engine.players[player_index].board.has_catalyst)
        except Exception:
            return False

    def has_eclipse(self, player_index: int = 0) -> bool:
        try:
            return bool(self._engine.players[player_index].board.has_eclipse)
        except Exception:
            return False

    def get_interest_multiplier(self, player_index: int = 0) -> float:
        try:
            return float(self._engine.players[player_index].interest_multiplier)
        except Exception:
            return 1.0

    def get_turns_played(self, player_index: int = 0) -> int:
        try:
            return self._engine.players[player_index].turns_played
        except Exception:
            return 0

    def get_current_pairings(self) -> list:
        """Swiss pairing sonucunu PID çifti listesi olarak döndür."""
        try:
            pairs = self._engine.swiss_pairs()
            return [(a.pid, b.pid) for a, b in pairs]
        except Exception:
            return []

    def get_pool_copies(self) -> dict:
        try:
            return dict(self._engine.market.pool_copies)
        except Exception:
            return {}
