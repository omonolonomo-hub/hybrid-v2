"""
Hafta 3 Faz 1 Testleri — H3-1 + H3-2 doğrulama.

H3-1: UIAdapter._next_tier() ile engine_core/synergy.tier_bonus() parity.
H3-2: EngineAdapter.get_hand() slot pozisyonu korunuyor.
"""

import pytest
from unittest.mock import MagicMock, PropertyMock

# ── H3-1: Tier Bonus Parity ─────────────────────────────────────────

class TestTierBonusParity:
    """UIAdapter._next_tier() ile engine synergy.tier_bonus() aynı değerleri döndürmeli."""

    def test_tier_bonus_n2_matches(self):
        from engine_core.synergy import tier_bonus
        from v2.core.ui_adapter import UIAdapter
        # count=1 → next tier N=2
        threshold, ui_bonus = UIAdapter._next_tier(1)
        assert threshold == 2
        assert ui_bonus == tier_bonus(2), f"N=2: UI={ui_bonus} != engine={tier_bonus(2)}"

    def test_tier_bonus_n3_matches(self):
        from engine_core.synergy import tier_bonus
        from v2.core.ui_adapter import UIAdapter
        # count=2 → next tier N=3
        threshold, ui_bonus = UIAdapter._next_tier(2)
        assert threshold == 3
        assert ui_bonus == tier_bonus(3), f"N=3: UI={ui_bonus} != engine={tier_bonus(3)}"

    def test_tier_bonus_n4_matches(self):
        from engine_core.synergy import tier_bonus
        from v2.core.ui_adapter import UIAdapter
        # count=3 → next tier N=4
        threshold, ui_bonus = UIAdapter._next_tier(3)
        assert threshold == 4
        assert ui_bonus == tier_bonus(4), f"N=4: UI={ui_bonus} != engine={tier_bonus(4)}"

    def test_tier_bonus_n5_matches(self):
        from engine_core.synergy import tier_bonus
        from v2.core.ui_adapter import UIAdapter
        # count=4 → next tier N=5
        threshold, ui_bonus = UIAdapter._next_tier(4)
        assert threshold == 5
        assert ui_bonus == tier_bonus(5), f"N=5: UI={ui_bonus} != engine={tier_bonus(5)}"

    def test_tier_bonus_n6_matches(self):
        from engine_core.synergy import tier_bonus
        from v2.core.ui_adapter import UIAdapter
        # count=5 → next tier N=6
        threshold, ui_bonus = UIAdapter._next_tier(5)
        assert threshold == 6
        assert ui_bonus == tier_bonus(6), f"N=6: UI={ui_bonus} != engine={tier_bonus(6)}"

    def test_tier_beyond_max_returns_none(self):
        from v2.core.ui_adapter import UIAdapter
        # count=6 → beyond all thresholds
        threshold, ui_bonus = UIAdapter._next_tier(6)
        assert threshold is None
        assert ui_bonus is None

    def test_tier_bonus_values_are_correct(self):
        """engine_core/synergy.tier_bonus() sabit değerlerini doğrula."""
        from engine_core.synergy import tier_bonus
        assert tier_bonus(2) == 3    # SYNERGY_TIER_SMALL
        assert tier_bonus(3) == 9    # SYNERGY_TIER_MED
        assert tier_bonus(4) == 16   # SYNERGY_TIER_LARGE
        assert tier_bonus(5) == 16   # SYNERGY_TIER_LARGE
        assert tier_bonus(6) == 25   # SYNERGY_TIER_HUGE

    def test_old_hardcoded_values_were_wrong(self):
        """Eski hardcoded [3,7,11,16,18] değerlerinin engine ile uyuşmadığını doğrula."""
        from engine_core.synergy import tier_bonus
        old_bonuses = [3, 7, 11, 16, 18]
        thresholds = [2, 3, 4, 5, 6]
        mismatches = []
        for threshold, old_bonus in zip(thresholds, old_bonuses):
            engine_value = tier_bonus(threshold)
            if old_bonus != engine_value:
                mismatches.append(f"N={threshold}: old={old_bonus}, engine={engine_value}")
        # En az 2 uyumsuzluk bekliyoruz (N=3: 7≠9, N=6: 18≠25)
        assert len(mismatches) >= 2, f"Beklenen en az 2 uyumsuzluk, bulunan: {mismatches}"


# ── H3-2: Hand Slot Position Preservation ───────────────────────────

class _FakeCard:
    def __init__(self, name):
        self.name = name
        self.uid = id(self)

class _FakeHand(list):
    """list subclass — player.hand tipi normalde list."""
    pass

class TestGetHandSlotPreservation:
    """EngineAdapter.get_hand() None slot pozisyonlarını korumalı."""

    def _make_adapter(self, hand_list):
        from v2.core.engine_adapter import EngineAdapter
        adapter = MagicMock(spec=EngineAdapter)
        adapter._engine = MagicMock()
        player = MagicMock()
        player.hand = hand_list
        adapter._engine.players = [player]
        # Gerçek metodu kullan
        return EngineAdapter(adapter._engine)

    def test_full_hand_no_none(self):
        """6 kartlı elde tüm isimler doğru sırada."""
        adapter = self._make_adapter([_FakeCard("A"), _FakeCard("B"), _FakeCard("C"),
                                       _FakeCard("D"), _FakeCard("E"), _FakeCard("F")])
        result = adapter.get_hand(0)
        assert result == ["A", "B", "C", "D", "E", "F"]

    def test_middle_none_preserved(self):
        """Ortadaki None slot pozisyonu korunuyor."""
        adapter = self._make_adapter([_FakeCard("A"), _FakeCard("B"), None,
                                       _FakeCard("D"), _FakeCard("E"), _FakeCard("F")])
        result = adapter.get_hand(0)
        assert result == ["A", "B", None, "D", "E", "F"], f"Slot kayması oldu: {result}"

    def test_first_none_preserved(self):
        """İlk slot None ise pozisyon korunuyor."""
        adapter = self._make_adapter([None, _FakeCard("B"), _FakeCard("C"),
                                       _FakeCard("D"), _FakeCard("E"), _FakeCard("F")])
        result = adapter.get_hand(0)
        assert result == [None, "B", "C", "D", "E", "F"]

    def test_last_none_preserved(self):
        """Son slot None ise pozisyon korunuyor."""
        adapter = self._make_adapter([_FakeCard("A"), _FakeCard("B"), _FakeCard("C"),
                                       _FakeCard("D"), _FakeCard("E"), None])
        result = adapter.get_hand(0)
        assert result == ["A", "B", "C", "D", "E", None]

    def test_short_hand_padded(self):
        """6'dan az kart varsa trailing None ile tamamlanır."""
        adapter = self._make_adapter([_FakeCard("A"), _FakeCard("B")])
        result = adapter.get_hand(0)
        assert result == ["A", "B", None, None, None, None]

    def test_empty_hand(self):
        """Boş el → 6 None slot."""
        adapter = self._make_adapter([])
        result = adapter.get_hand(0)
        assert result == [None, None, None, None, None, None]

    def test_multiple_none_preserved(self):
        """Birden fazla None slot arada olsa bile korunuyor."""
        adapter = self._make_adapter([_FakeCard("A"), None, None, _FakeCard("D"), None, _FakeCard("F")])
        result = adapter.get_hand(0)
        assert result == ["A", None, None, "D", None, "F"]

    def test_invalid_player_index(self):
        """Geçersiz player_index → PlayerNotFoundError."""
        from v2.core.engine_adapter import EngineAdapter
        from v2.core.exceptions import PlayerNotFoundError
        import pytest
        
        adapter = MagicMock(spec=EngineAdapter)
        adapter._engine = MagicMock()
        adapter._engine.players = []
        real = EngineAdapter(adapter._engine)
        
        # get_hand now raises exception for invalid player
        with pytest.raises(PlayerNotFoundError):
            real.get_hand(0)
