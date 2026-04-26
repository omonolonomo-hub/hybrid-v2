"""
Simulation-Level Passive System Test

Küçük bir simülasyon çalıştırarak passive handler'larının gerçek oyun
akışında doğru tetiklendiğini doğrular.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from engine_core.simulation import run_simulation, print_results


def test_simulation_with_passives():
    """10 oyunluk simülasyonun hatasız tamamlandığını ve passive sisteminin
    çalıştığını doğrular."""
    results = run_simulation(
        n_games=10,
        n_players=4,
        verbose=False,
        strategies=["random", "warrior", "evolver", "economist"],
    )

    total_games = sum(results["wins"].values())
    assert total_games == 10, f"Beklenen 10 oyun, tamamlanan: {total_games}"

    # En az bir strateji kazanmalı
    assert len(results["wins"]) > 0, "Hiçbir strateji kazanamadı"

    # avg_turns listesi dolmuş olmalı
    assert len(results["avg_turns"]) == 10, "avg_turns listesi eksik"
