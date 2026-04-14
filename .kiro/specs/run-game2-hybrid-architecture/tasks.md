# Implementation Plan: run_game2.py Hybrid Architecture

## Overview

This plan implements a hybrid architecture that combines run_game.py's proven game loop logic with scene-based UI components. Scenes are treated as modal dialogs rather than loop controllers, maintaining deterministic turn flow in a single main loop.

## Tasks

- [x] 1. Temel iskelet — pygame init, 1600x960, font cache, build_game()
  - Initialize pygame and create 1600x960 window
  - Create font cache dictionary (title, lg, md, sm, xs, icon sizes)
  - Import build_game() from run_game.py
  - Create HybridGameState dataclass with view_player, selected_hand_idx, pending_rotation, placed_this_turn, locked_coords_per_player
  - Basic main loop with clock.tick(60) and event handling
  - _Requirements: 1.1, 2.1, 6.1, 7.1, 19.3_

- [x] 2. render_main_screen() — BoardRendererV3, draw_hand_panel, draw_synergy_hud, draw_player_info, draw_passive_buff_panel, draw_cyber_victorian_hud
  - Import BoardRendererV3 from ui.board_renderer_v3
  - Copy draw_hand_panel() from run_game.py
  - Copy draw_synergy_hud() from run_game.py
  - Copy draw_player_info() from run_game.py
  - Copy draw_passive_buff_panel() from run_game.py
  - Copy draw_cyber_victorian_hud() from run_game.py
  - Implement render_main_screen() function that calls all rendering functions
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

- [x] 3a. Input handling (state-only) — TAB, 1-8, R, ESC, hover
  - TAB cycles view_player, 1-8 switches to specific player
  - R rotates selected card, ESC deselects card
  - Mouse hover for tooltips, left/right click for card selection
  - Update HybridGameState only (no game logic yet)
  - _Requirements: 5.1, 5.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 8.11, 14.1, 14.2_

- [x] 4. ShopSceneModal wrapper — scenes/shop_scene_modal.py
  - Create new file scenes/shop_scene_modal.py
  - Import ShopScene from scenes.shop_scene
  - Create ShopSceneModal class with run_modal() static method
  - Mock SceneManager: `scene.scene_manager = SimpleNamespace(request_transition=lambda *a: None)`
  - Implement internal while loop until shop phase complete
  - Call scene.on_exit() to apply interest (lifecycle requirement)
  - Return dict with {"purchased": [...], "gold_spent": int}
  - _Requirements: 3.1, 3.4, 3.5_

- [x] 5. CombatSceneModal wrapper — scenes/combat_scene_modal.py
  - Create new file scenes/combat_scene_modal.py
  - Import CombatScene from scenes.combat_scene
  - Create CombatSceneModal class with run_modal() static method
  - Accept last_combat_results parameter
  - Scale CombatScene from 1920x1080 to 1600x960 using pygame.transform.scale()
  - Implement internal while loop with SPACE/ESC to exit
  - Return dict with {"viewed": bool, "skipped": bool}
  - _Requirements: 3.2, 3.3, 11.2, 11.3, 11.4, 11.5, 11.6_

- [x] 6. step_turn_hybrid() — shop → AI → combat → cleanup
  - Implement step_turn_hybrid() function
  - Phase 1: clear_passive_trigger_log(), player.income(), ShopSceneModal.run_modal()
  - Phase 2: game.turn += 1
  - Phase 3: AI player loop (income, buy, interest, evolution, place, strengthen)
  - Phase 4: game.combat_phase()
  - Phase 5: CombatSceneModal.run_modal(game.last_combat_results)
  - Phase 6: Clear locked_coords_per_player for all players
  - NOTE: player.apply_interest() handled by ShopSceneModal.on_exit() - do NOT call again
  - _Requirements: 1.2, 1.3, 1.4, 1.5, 5.7, 9.1, 9.2, 9.3, 9.4, 9.5, 10.1_

- [x] 3b. Input handling (game logic) — SPACE → step_turn_hybrid()
  - SPACE key triggers step_turn_hybrid() (now that it exists)
  - S key opens ShopSceneModal.run_modal()
  - R key restarts game if no card selected
  - _Requirements: 5.4, 8.1, 8.2, 8.5_

- [x] 7. Game over + restart — display_game_over(), R tuşu → build_game()
  - Implement game over detection (alive count <= 1 or turn >= 50)
  - Determine winner as player with highest HP
  - Display game over screen with winner info
  - R key restarts game by calling build_game() and resetting state
  - _Requirements: 1.6, 8.5, 13.1, 13.2, 13.3, 13.4, 13.5_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Implementation language: Python (matching existing codebase)
- DO NOT modify existing ShopScene or CombatScene files
- Create wrapper classes in new _modal.py files
- Wrapper strategy: Create temporary scene instance, run internal loop, call on_exit()
- Scale strategy: CombatScene renders to temp surface, then scale to 1600x960
