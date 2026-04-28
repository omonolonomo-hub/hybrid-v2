"""
Base strategy interface and AI dispatcher.
"""

from typing import List

from engine_core.card import Card
from engine_core.player import Player


class BaseStrategy:
    """Interface for AI strategies."""
    def buy_cards(self, player: Player, market: List[Card], max_cards: int,
                  market_obj=None, rng=None, trigger_passive_fn=None,
                  ai_instance=None, next_uid_fn=None, game_ref=None):
        raise NotImplementedError

    def place_cards(self, player: Player, rng=None, **kwargs):
        raise NotImplementedError


# Import all strategy implementations
from engine_core.ai.strategies.random import RandomStrategy
from engine_core.ai.strategies.warrior import WarriorStrategy
from engine_core.ai.strategies.economist import EconomistStrategy
from engine_core.ai.strategies.builder import BuilderStrategy
from engine_core.ai.strategies.evolver import EvolverStrategy
from engine_core.ai.strategies.balancer import BalancerStrategy
from engine_core.ai.strategies.rare_hunter import RareHunterStrategy
from engine_core.ai.strategies.tempo import TempoStrategy

# Strategy map populated with all strategy instances
STRATEGY_MAP = {
    "random":      RandomStrategy(),
    "warrior":     WarriorStrategy(),
    "builder":     BuilderStrategy(),
    "evolver":     EvolverStrategy(),
    "economist":   EconomistStrategy(),
    "balancer":    BalancerStrategy(),
    "rare_hunter": RareHunterStrategy(),
    "tempo":       TempoStrategy(),
}


class AI:
    """AI dispatcher class for buying and placing cards."""
    
    @staticmethod
    def buy_cards(player: Player, market: List[Card], max_cards: int = 1, next_uid_fn=None,
                  market_obj=None, rng=None, trigger_passive_fn=None,
                  ai_instance=None, game_ref=None):
        """Buy from market according to player.strategy.
        market_obj: Market instance for hand-overflow pool returns (optional).
        trigger_passive_fn: Function to trigger passive abilities (injected dependency).
        ai_instance: ParameterizedAI instance for parameter access (optional).
                     Phase 1: tüm stratejiler ai_instance alır.
        game_ref: Game instance reference for context injection (replaces player.game).
        """
        strat_name = player.strategy
        strat_obj = STRATEGY_MAP.get(strat_name, STRATEGY_MAP.get("random"))
        
        if strat_obj is None:
            raise ValueError(f"No strategy found for '{strat_name}' and no random fallback")
        
        strat_obj.buy_cards(
            player, market, max_cards,
            market_obj=market_obj,
            rng=rng,
            trigger_passive_fn=trigger_passive_fn,
            ai_instance=ai_instance,
            next_uid_fn=next_uid_fn,
            game_ref=game_ref
        )

    @staticmethod
    def place_cards(player: Player, rng=None, **kwargs):
        """Place hand cards onto the board per strategy."""
        strat_name = player.strategy
        strat_obj = STRATEGY_MAP.get(strat_name, STRATEGY_MAP.get("random"))
        
        if strat_obj is None:
            raise ValueError(f"No strategy found for '{strat_name}' and no random fallback")
        
        strat_obj.place_cards(player, rng, **kwargs)
    
    @staticmethod
    def _economy_phase_controls(player: Player, market: List[Card], max_cards: int,
                                market_obj=None, trigger_passive_fn=None,
                                ai_instance=None, strategy: str = "economist"):
        """Backward compatibility wrapper for _economy_phase_controls.
        
        This method delegates to the utils module to maintain backward compatibility
        with code that calls AI._economy_phase_controls directly.
        """
        from engine_core.ai.utils import _economy_phase_controls
        return _economy_phase_controls(player, market, max_cards, market_obj,
                                       trigger_passive_fn, ai_instance, strategy)
    
    @staticmethod
    def _get_param_with_fallback(ai_instance, strategy: str, key: str,
                                 default, fallback_strategy=None):
        """Backward compatibility wrapper for _get_param_with_fallback.
        
        This method delegates to the utils module to maintain backward compatibility
        with code that calls AI._get_param_with_fallback directly.
        """
        from engine_core.ai.utils import _get_param_with_fallback
        return _get_param_with_fallback(ai_instance, strategy, key, default, fallback_strategy)
