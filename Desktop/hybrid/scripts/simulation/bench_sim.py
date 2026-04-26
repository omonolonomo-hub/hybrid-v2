import sys, time
sys.path.insert(0, 'engine_core')
from autochess_sim_v06 import run_simulation

N_GAMES = 300
N_PLAYERS = 8
REPS = 5
SEED = 42

# Warmup
run_simulation(n_games=N_GAMES, n_players=N_PLAYERS, verbose=False, seed=SEED)

times = []
for _ in range(REPS):
    t0 = time.perf_counter()
    run_simulation(n_games=N_GAMES, n_players=N_PLAYERS, verbose=False, seed=SEED)
    times.append(time.perf_counter() - t0)

avg = sum(times) / REPS
print(f"Average Time: {avg:.3f}s")
print(f"Min Time:     {min(times):.3f}s")
print(f"Max Time:     {max(times):.3f}s")
print(f"Games/sec:    {N_GAMES / avg:.1f}")
