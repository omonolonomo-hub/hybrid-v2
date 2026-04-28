from dataclasses import dataclass
from typing import Any, Optional

from v2.core.action_result import ActionResult
from v2.core.game_state import GameState
from v2.core.public_state import Coord, PublicState


@dataclass(frozen=True)
class ShopUIAction:
    kind: str
    slot_index: int = -1
    card_name: Optional[str] = None


@dataclass(frozen=True)
class ShopControllerResult:
    state: PublicState
    result: Optional[ActionResult] = None
    action: Optional[ShopUIAction] = None
    placed_card: Optional[dict[str, Any]] = None
    combat_logs: tuple[str, ...] = ()
    endgame_stats: tuple[dict[str, Any], ...] = ()
    removed_coords: tuple[Coord, ...] = ()
    next_phase: Optional[str] = None


class ShopController:
    def __init__(self, game_state: Optional[GameState] = None):
        if game_state is None:
             raise ValueError("ShopController requires a GameState instance.")
        self._game_state = game_state

    def refresh_public_state(self) -> PublicState:
        return self._game_state.get_public_state()

    def get_turn(self) -> int:
        return int(self.refresh_public_state().turn)

    def handle_phase_change(self, new_phase: str) -> ShopControllerResult:
        """Handle phase transition and trigger associated actions.
        
        Phase setting and action triggering are now decoupled:
        - mirror_phase() sets the phase state
        - Specific actions (combat, turn start) are called explicitly
        
        This allows dry-runs, previews, or deferred execution patterns.
        
        Phase transitions are atomic: if any step in the sequence fails,
        the phase is rolled back to its previous value to prevent inconsistent state.
        """
        # Store previous phase for rollback on exception
        # Use get_phase() instead of get_public_state().phase to avoid expensive computation
        # (get_public_state() triggers full UIAdapter BFS + DB + triple-iteration)
        previous_phase = self._game_state.get_phase()
        
        try:
            self._game_state.mirror_phase(new_phase)

            if new_phase == "STATE_PREPARATION":
                cleanup = self.cleanup_dead_cards()
                self._game_state.start_turn()
                self._game_state.reset_turn()
                return ShopControllerResult(
                    state=self.refresh_public_state(),
                    removed_coords=cleanup.removed_coords,
                )

            if new_phase == "STATE_COMBAT":
                self.trigger_combat()
                state = self.refresh_public_state()
                return ShopControllerResult(
                    state=state,
                    combat_logs=tuple(state.active_player.combat.logs),
                )

            state = self.refresh_public_state()
            if new_phase == "STATE_ENDGAME":
                return ShopControllerResult(
                    state=state,
                    endgame_stats=tuple(state.endgame_stats),
                )

            return ShopControllerResult(state=state)
            
        except Exception as e:
            # Rollback: restore phase to previous value to prevent inconsistent state
            # 
            # ROLLBACK SCOPE:
            # - Only StateStore._phase is rolled back
            # - Engine-level mutations (board changes, market updates) are NOT undone
            # - This is intentional: they are idempotent or logged
            # 
            # RATIONALE:
            # Phase inconsistency is the critical bug - if mirror_phase() succeeds but
            # start_turn() fails, the phase is "PREPARATION" but the turn hasn't started.
            # Rolling back the phase prevents this inconsistent state.
            # 
            # Engine mutations (board/market) are either:
            # 1. Idempotent (can be safely repeated)
            # 2. Logged (can be debugged)
            # So partial execution is acceptable for engine state, but not for phase state.
            self._game_state.mirror_phase(previous_phase)
            
            # Re-raise exception for logging/debugging
            raise

    def trigger_combat(self) -> None:
        """Trigger combat execution independently of phase change.
        
        Separated from handle_phase_change() to allow:
        - Dry-run phase transitions without combat
        - Deferred combat execution
        - Combat preview/simulation
        """
        self._game_state.run_combat_phase()

    def handle_shop_action(self, action: ShopUIAction) -> ShopControllerResult:
        if action.kind == "ready":
            self._game_state.commit_human_turn()
            return ShopControllerResult(
                state=self.refresh_public_state(),
                action=action,
            )

        if action.kind == "reroll":
            result = self._game_state.reroll_market(player_index=0)
            return ShopControllerResult(
                state=self.refresh_public_state(),
                result=result,
                action=action,
            )

        if action.kind == "lock":
            self._game_state.toggle_lock_shop(player_index=0)
            return ShopControllerResult(
                state=self.refresh_public_state(),
                action=action,
            )

        if action.kind == "buy":
            result = self._game_state.buy_card_from_slot(player_index=0, slot_index=action.slot_index)
            return ShopControllerResult(
                state=self.refresh_public_state(),
                result=result,
                action=action,
            )

        return ShopControllerResult(state=self.refresh_public_state(), action=action)

    def place_card_from_hand(
        self,
        hand_index: int,
        coord: Coord,
        rotation: int = 0,
    ) -> ShopControllerResult:
        result = self._game_state.place_card(hand_index, coord, rotation=rotation)
        state = self.refresh_public_state()
        placed_card = state.active_player.board_cards.get(coord) if result == ActionResult.OK else None
        return ShopControllerResult(
            state=state,
            result=result,
            placed_card=placed_card,
        )

    def set_view_index(self, target_idx: int) -> ShopControllerResult:
        self._game_state.view_index = target_idx
        return ShopControllerResult(state=self.refresh_public_state())

    def cleanup_dead_cards(self) -> ShopControllerResult:
        state = self.refresh_public_state()
        player_index = state.active_player.index
        to_remove = tuple(state.active_player.eliminated_coords)
        if to_remove:
            self._game_state.remove_eliminated_cards(player_index, list(to_remove))
        return ShopControllerResult(
            state=self.refresh_public_state(),
            removed_coords=to_remove,
        )

    def finish_combat_overlay(self) -> ShopControllerResult:
        cleanup = self.cleanup_dead_cards()
        alive_count = len(self._game_state.get_alive_pids())
        next_phase = "STATE_ENDGAME" if alive_count <= 1 else "STATE_PREPARATION"
        return ShopControllerResult(
            state=cleanup.state,
            removed_coords=cleanup.removed_coords,
            next_phase=next_phase,
        )
