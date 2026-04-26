from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from engine_core.constants import (
    STARTING_HP, CATEGORY_DISPLAY_MAP, COPY_THRESH, COPY_THRESH_C, SYNERGY_THRESHOLDS
)
from engine_core.synergy import tier_bonus as _engine_tier_bonus
from v2.constants import Colors, Paths
from v2.core.card_database import CardDatabase
from v2.core.exceptions import AutochessException, DatabaseError
from v2.core.synergy_calculator import SynergyCalculator, SynergyComputeResult
from v2.core.public_state import (
    ActivePlayerViewState,
    CombatViewState,
    EffectViewState,
    HandViewState,
    PassiveFeedEntryViewState,
    PlayerHudViewState,
    PublicState,
    ShopViewState,
    SynergyGroupViewState,
    SynergyViewState,
)


class UIAdapter:
    """Builds immutable-ish UI-facing snapshots from the engine facade."""
    # Renkler constants.py::Colors sınıfıyla birebir eş tutulmalıdır.
    # Buraya hardcode renk YAZMAYIN — Colors'tan referans alın.
    _SYNERGY_GROUPS = [
        ("MIND",       "MIND",       "MIND", Colors.MIND),
        ("CONNECTION", "CONNECTION", "CONN", Colors.CONNECTION),
        ("EXISTENCE",  "EXISTENCE",  "EXST", Colors.EXISTENCE),
    ]
    # Tier hesaplaması artık engine_core/synergy.tier_bonus()'a delegate eder.
    # Hardcoded _TIER_THRESHOLDS kaldırıldı; engine_core.constants.SYNERGY_THRESHOLDS kullanılır (H3-1).
    _TIER_THRESHOLDS = SYNERGY_THRESHOLDS

    @staticmethod
    def _iter_board_items(player):
        board = getattr(player, "board", None)
        grid = getattr(board, "grid", None)
        if isinstance(grid, dict):
            return list(grid.items())
        return []

    @staticmethod
    def _card_name(card_obj) -> str:
        return getattr(card_obj, "name", str(card_obj))

    @staticmethod
    def _card_stats(card_obj) -> Dict[str, Any]:
        stats = getattr(card_obj, "stats", {})
        try:
            return dict(stats)
        except (TypeError, ValueError):
            return {}

    @staticmethod
    def _safe_int(value: Any, default: int = 0) -> int:
        return int(value) if isinstance(value, (int, float)) else default

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        return float(value) if isinstance(value, (int, float)) else default

    @classmethod
    def _next_tier(cls, count: int) -> tuple[int | None, int | None]:
        """Bir sonraki tier eşik değerini ve bonusunu döndür.

        Bonus hesaplaması engine_core/synergy.tier_bonus()'a delegate eder.
        Böylece UI ile engine arasındaki tier bonus değerleri her zaman eşleşir.
        """
        for threshold in cls._TIER_THRESHOLDS:
            if count < threshold:
                return threshold, _engine_tier_bonus(threshold)
        return None, None

    def build_public_state(self, adapter, store, formatter) -> PublicState:
        if adapter is None:
            return self._empty_state(store)

        phase = store.phase
        turn = int(adapter.get_turn())
        view_index = store.view_index
        player = adapter.get_player(view_index)

        active_player = self._build_active_player(adapter, formatter, player, view_index, turn)
        # H3-5: store.update_board() kaldırıldı — board verisi artık PublicState.active_player üzerinden erişiliyor

        return PublicState(
            phase=phase,
            turn=turn,
            view_index=view_index,
            place_locked=store.place_locked,
            alive_pids=tuple(p.pid for p in adapter.get_alive_players()),
            pairings=tuple(store.get_pairings()),
            active_player=active_player,
            lobby_players=tuple(self._build_lobby_players(adapter)),
            endgame_stats=tuple(self._build_endgame_stats(adapter)),
        )

    def _empty_state(self, store) -> PublicState:
        empty_shop = ShopViewState(slots=tuple([None] * 5), is_locked=False, rarity_probabilities={"1": 100.0})
        empty_hand = HandViewState(slots=tuple([None] * 6))
        empty_hud = PlayerHudViewState(
            hp=STARTING_HP,
            gold=10,
            win_streak=0,
            total_pts=0,
            turn=0,
            next_gold=3,
            interest_multiplier=1.0,
        )
        empty_combat = CombatViewState(last_results=(), logs=(), passive_feed=())
        empty_synergy = SynergyViewState(groups=(), total=0, passive_feed=(), active_effects=())
        active_player = ActivePlayerViewState(
            index=store.view_index,
            pid=store.view_index,
            display_name=f"P{store.view_index}",
            strategy="unknown",
            hp=0,
            gold=0,
            alive=False,
            turns_played=0,
            stats={},
            has_catalyst=False,
            has_eclipse=False,
            board_cards={},
            board_rotations={},
            adjacency_pairs=(),
            eliminated_coords=(),
            shop=empty_shop,
            hand=empty_hand,
            hud=empty_hud,
            combat=empty_combat,
            synergy=empty_synergy,
            copies_by_name={},
            copy_milestones=(),
            prefix_bonus=0,
        )
        return PublicState(
            phase=store.phase,
            turn=0,
            view_index=store.view_index,
            place_locked=store.place_locked,
            alive_pids=(),
            pairings=tuple(store.get_pairings()),
            active_player=active_player,
            lobby_players=(),
            endgame_stats=(),
        )

    def _build_active_player(self, adapter, formatter, player, view_index: int, turn: int) -> ActivePlayerViewState:
        if player is None:
            return ActivePlayerViewState(
                index=view_index,
                pid=view_index,
                display_name=f"P{view_index}",
                strategy="unknown",
                hp=0,
                gold=0,
                alive=False,
                turns_played=0,
                stats={},
                has_catalyst=False,
                has_eclipse=False,
                board_cards={},
                board_rotations={},
                adjacency_pairs=(),
                eliminated_coords=(),
                shop=ShopViewState(slots=tuple([None] * 5), is_locked=False, rarity_probabilities={"1": 100.0}),
                hand=HandViewState(slots=tuple([None] * 6)),
                hud=PlayerHudViewState(
                    hp=0,
                    gold=0,
                    win_streak=0,
                    total_pts=0,
                    turn=turn,
                    next_gold=3,
                    interest_multiplier=1.0,
                ),
                combat=CombatViewState(last_results=(), logs=(), passive_feed=()),
                synergy=SynergyViewState(groups=(), total=0, passive_feed=(), active_effects=()),
                copies_by_name={},
                copy_milestones=(),
                prefix_bonus=0,
            )

        board_cards = self._build_board_cards(player)
        board_rotations = {coord: item["rotation"] for coord, item in board_cards.items()}

        # Synergy TEK yerde hesaplanır — SynergyCalculator tek kaynak
        try:
            db = CardDatabase.get()
            syn_result = SynergyCalculator.compute(board_cards, db)
        except AutochessException:
            # CardDatabase başlatılmadıysa ya da hesaplama hatası: boş synergy dön
            syn_result = SynergyComputeResult.empty()
        shop_slots = adapter.get_shop_window(view_index)
        hand_slots = adapter.get_hand(view_index)
        passive_feed = adapter.get_passive_buff_log(view_index)
        last_results = list(adapter.get_last_results())
        board = getattr(player, "board", None)
        board_grid = getattr(board, "grid", {}) if board is not None else {}

        shop_view = ShopViewState(
            slots=tuple(shop_slots),
            is_locked=adapter.is_shop_locked(view_index),
            rarity_probabilities=formatter.format_rarity_probs(
                lambda rarity, current_turn: adapter.get_rarity_weight(rarity, current_turn),
                turn,
            ),
        )
        hand_view = HandViewState(slots=tuple(hand_slots[:6]))
        hp = adapter.get_player_hp(view_index)
        gold = adapter.get_player_gold(view_index)
        win_streak = self._safe_int(getattr(player, "win_streak", 0))
        total_pts = self._safe_int(getattr(player, "total_pts", 0))
        interest_multiplier = self._safe_float(getattr(player, "interest_multiplier", 1.0), default=1.0)
        
        econ = getattr(player, "economy", None)
        next_gold = econ.calculate_total_next_income(win_streak, hp) if econ else 3

        hud_view = PlayerHudViewState(
            hp=hp,
            gold=gold,
            win_streak=win_streak,
            total_pts=total_pts,
            turn=turn,
            next_gold=next_gold,
            interest_multiplier=interest_multiplier,
        )
        combat_view = CombatViewState(
            last_results=tuple(last_results),
            logs=tuple(formatter.format_combat_logs(last_results, view_index, turn, passive_feed)),
            passive_feed=tuple(passive_feed),
        )
        # syn_result zaten yukarıda hesaplandı — _build_synergy_view çağrılmaz
        synergy_view = self._synergy_view_from_result(syn_result, passive_feed)

        return ActivePlayerViewState(
            index=view_index,
            pid=self._safe_int(getattr(player, "pid", view_index), default=view_index),
            display_name=f"P{self._safe_int(getattr(player, 'pid', view_index), default=view_index)}",
            strategy=str(getattr(player, "strategy", "unknown")),
            hp=hp,
            gold=gold,
            alive=bool(player.alive),
            turns_played=self._safe_int(getattr(player, "turns_played", 0)),
            stats=dict(getattr(player, "stats", {})),
            has_catalyst=bool(getattr(board, "has_catalyst", False)),
            has_eclipse=bool(getattr(board, "has_eclipse", False)),
            board_cards=board_cards,
            board_rotations=board_rotations,
            adjacency_pairs=tuple(tuple(pair) for pair in syn_result.adjacency_pairs),
            eliminated_coords=tuple(adapter.get_eliminated_coords(view_index)),
            shop=shop_view,
            hand=hand_view,
            hud=hud_view,
            combat=combat_view,
            synergy=synergy_view,
            copies_by_name=dict(getattr(player, "copies", {})),
            copy_milestones=tuple(self._build_copy_milestones(player, turn, board_cards)),
            prefix_bonus=sum(
                self._safe_int(card.get_combat_bonus_total())
                for card in board_grid.values()
                if hasattr(card, "get_combat_bonus_total")
            ),
            shop_card_info=self._build_shop_card_info(adapter, formatter, player),
            hand_card_info=self._build_hand_card_info(formatter, player),
            board_card_info=self._build_board_card_info(formatter, player),
        )

    def _synergy_view_from_result(
        self,
        result: SynergyComputeResult,
        passive_feed: List[Dict[str, Any]],
    ) -> SynergyViewState:
        """SynergyComputeResult → SynergyViewState dönüşümü.
        BFS hesabı YOKTUR — o iş SynergyCalculator'a aittir.
        """
        groups: List[SynergyGroupViewState] = []
        active_effects: List[EffectViewState] = []

        for key, label, short_label, color in self._SYNERGY_GROUPS:
            count = result.group_counts.get(key, 0)
            bonus = result.group_bonuses.get(key, 0)
            next_tier_count, next_tier_bonus = self._next_tier(count)
            groups.append(SynergyGroupViewState(
                key=key, label=label, short_label=short_label, color=color,
                count=count, bonus=bonus,
                next_tier_count=next_tier_count, next_tier_bonus=next_tier_bonus,
            ))
            if next_tier_count is not None:
                active_effects.append(EffectViewState(
                    label=f"{short_label} {count}/{next_tier_count}",
                    value=f"+{next_tier_bonus}",
                    color=color, icon_key="BOLT",
                ))

        passive_entries = [
            PassiveFeedEntryViewState(
                trigger  = str(entry.get("trigger", "")),
                card     = str(entry.get("card",    "")),
                delta    = self._safe_int(entry.get("delta", 0)),
                res      = self._safe_int(entry.get("res",   0)),
                color    = Colors.PASSIVE_EFFECTS.get(str(entry.get("trigger", "")), (160, 165, 195)),
                icon_key = Paths.PASSIVE_ICONS.get( str(entry.get("trigger", "")), "GEAR"),
            )
            for entry in passive_feed
        ]

        return SynergyViewState(
            groups=tuple(groups), total=result.total,
            passive_feed=tuple(passive_entries), active_effects=tuple(active_effects),
        )

    # _build_synergy_view KALDIRILDI — SynergyCalculator kullanın
    # _build_adjacency_pairs KALDIRILDI — SynergyComputeResult.adjacency_pairs kullanın

    def _build_board_cards(self, player) -> Dict[Tuple[int, int], Dict[str, Any]]:
        result: Dict[Tuple[int, int], Dict[str, Any]] = {}
        for coord, card in self._iter_board_items(player):
            result[coord] = {
                "name": self._card_name(card),
                "stats": self._card_stats(card),
                "rotation": getattr(card, "rotation", 0),
            }
        return result

    def _build_shop_card_info(self, adapter, formatter, player) -> Dict[int, Any]:
        market = adapter.get_market()
        if market is None:
            return {}
        window = market.get_window(player.pid)
        return {
            idx: formatter.get_card_data_snapshot(card_obj)
            for idx, card_obj in enumerate(window)
        }

    def _build_hand_card_info(self, formatter, player) -> Dict[int, Any]:
        return {
            idx: formatter.get_card_data_snapshot(card_obj)
            for idx, card_obj in enumerate(getattr(player, "hand", []))
        }

    def _build_board_card_info(self, formatter, player) -> Dict[Tuple[int, int], Any]:
        return {
            coord: formatter.get_card_data_snapshot(card_obj)
            for coord, card_obj in self._iter_board_items(player)
        }

    def _build_lobby_players(self, adapter) -> List[Dict[str, Any]]:
        players = []
        for player in adapter.get_alive_players():
            pid = self._safe_int(getattr(player, "pid", 0))
            players.append(
                {
                    "name": f"P{pid}",
                    "hp": adapter.get_player_hp(pid),
                    "max_hp": STARTING_HP,
                    "gold": adapter.get_player_gold(pid),
                    "rank": 0,
                    "index": pid,
                    "categories": self._build_player_composition(self._build_board_cards(player)),
                }
            )
        players.sort(key=lambda item: item["hp"], reverse=True)
        for index, entry in enumerate(players, start=1):
            entry["rank"] = index
        return players

    def _build_endgame_stats(self, adapter) -> List[Dict[str, Any]]:
        stats = []
        for player in adapter.get_all_players():
            pid = self._safe_int(getattr(player, "pid", 0))
            stats.append(
                {
                    "name": f"P{pid}",
                    "strategy": getattr(player, "strategy", "unknown"),
                    "hp": adapter.get_player_hp(pid),
                    "total_pts": self._safe_int(getattr(player, "total_pts", 0)),
                    "alive": bool(getattr(player, "alive", False)),
                }
            )
        stats.sort(key=lambda item: (item["alive"], item["hp"], item["total_pts"]), reverse=True)
        for index, item in enumerate(stats, start=1):
            item["rank"] = index
        return stats

    def _build_player_composition(self, board_cards: Dict[Tuple[int, int], Dict[str, Any]]) -> Dict[str, int]:
        try:
            db = CardDatabase.get()
        except DatabaseError:
            return {}

        counts: Dict[str, int] = {}
        for info in board_cards.values():
            card = db.lookup(info["name"])
            if card is None:
                continue
            category = CATEGORY_DISPLAY_MAP.get(card.category, card.category.upper().split(" & ")[0])
            counts[category] = counts.get(category, 0) + 1
        return counts

    def _build_copy_milestones(
        self,
        player,
        turn: int,
        board_cards: Dict[Tuple[int, int], Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        board = getattr(player, "board", None)
        thresholds = COPY_THRESH_C if (board and getattr(board, "has_catalyst", False)) else COPY_THRESH
        
        if turn not in thresholds:
            return []

        milestones = []
        board_names = {info["name"] for info in board_cards.values()}
        copies = getattr(player, "copies", {})
        copy_applied = getattr(player, "copy_applied", {})
        for card_name, count in copies.items():
            if card_name not in board_names:
                continue
            applied = copy_applied.get(card_name, {"2": False, "3": False})
            
            # Use thresh indices to determine if it's the 2nd or 3rd copy milestone
            if turn == thresholds[0] and count >= 2 and not applied.get("2", False):
                milestones.append({"card": card_name, "trigger": "copy_2", "count": count, "turn": turn})
            if turn == thresholds[1] and count >= 3 and not applied.get("3", False):
                milestones.append({"card": card_name, "trigger": "copy_3", "count": count, "turn": turn})
        return milestones

    def _compute_next_gold(self, gold: int, hp: int, win_streak: int, interest_multiplier: float) -> int:
        """Deprecated: use player.economy.calculate_total_next_income instead."""
        return 0
