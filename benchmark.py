#!/usr/bin/env python3
"""
Headless benchmark for Slitherin solvers.

Plays full games without a window and reports what actually happened: the
score of each game (snake length; the maximum is the number of free tiles,
100 on the default 12x12 board with walls), whether the game was won, and how
many moves it took.

    python benchmark.py hamilton_cycle --games 20
    python benchmark.py shortest_path_bfs hamilton_cycle --games 50 --seed 1
    python benchmark.py hamilton_cycle --games 100 --save

With --save, per-game results go to scores/benchmark_<solver>.csv and the
moves spent on every single apple go to scores/benchmark_<solver>_apples.csv.
"""

import argparse
import csv
import importlib
import random
import statistics
import time

from game.environment.environment import Environment
from game.helpers.constants import Constants

# short name -> (module, class). Imported lazily so that one solver's missing
# optional dependency (TensorFlow, SCIP) does not stop the others from running.
SOLVERS = {
    "random": ("game.models.general_purpose.random_ai_solver", "RandomSolver"),
    "monte_carlo": ("game.models.general_purpose.monte_carlo_ai_solver", "MonteCarloSolver"),
    "shortest_path_bfs": ("game.models.domain_specific.shortest_path_bfs_ai_solver", "ShortestPathBFSSolver"),
    "shortest_path_dfs": ("game.models.domain_specific.shortest_path_dfs_ai_solver", "ShortestPathDFSSolver"),
    "longest_path": ("game.models.domain_specific.longest_path_ai_solver", "LongestPathSolver"),
    "hamilton": ("game.models.domain_specific.hamilton_ai_solver", "HamiltonSolver"),
    "hamilton_cycle": ("game.models.domain_specific.hamilton_cycle_ai_solver", "HamiltonCycleSolver"),
    "milp": ("game.models.domain_specific.milp_ai_solver", "MILPAISolver"),
}


def make_solver(name):
    module, cls = SOLVERS[name]
    return getattr(importlib.import_module(module), cls)()


def play_game(solver, width, height, stall_factor=4):
    """Play one game. Returns (score, won, moves, moves_per_apple)."""
    env = Environment(width=width, height=height)
    env.snake_action = None
    env.set_wall()
    env.set_fruit()
    env.set_snake()
    solver.reset()
    tiles = env._available_tiles_count()
    moves, since_apple, per_apple = 0, 0, []
    while True:
        if env.eat_fruit_if_possible():
            per_apple.append(since_apple)
            since_apple = 0
            if env.reward() == tiles:
                return env.reward(), True, moves, per_apple
        if since_apple > stall_factor * tiles:  # going in circles
            return env.reward(), False, moves, per_apple
        action = solver.move(env)
        if not env.step(action):
            return env.reward(), False, moves, per_apple
        moves += 1
        since_apple += 1


def benchmark(name, games, seed, width, height, save):
    solver = make_solver(name)
    rows, apple_rows = [], []
    started = time.time()
    for game in range(games):
        if seed is not None:
            random.seed(seed + game)
        score, won, moves, per_apple = play_game(solver, width, height)
        rows.append((game, score, int(won), moves))
        apple_rows += [(game, length + 1, m) for length, m in enumerate(per_apple)]
    elapsed = time.time() - started

    scores = [r[1] for r in rows]
    wins = [r for r in rows if r[2]]
    line = (f"{name}: {games} games, score min/mean/max "
            f"{min(scores)}/{statistics.mean(scores):.1f}/{max(scores)}, "
            f"won {len(wins)}/{games}")
    if wins:
        line += f", mean moves to win {statistics.mean(r[3] for r in wins):.0f}"
    print(line + f", {elapsed / games:.1f}s per game")

    if save:
        with open(f"scores/benchmark_{name}.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["game", "score", "won", "moves"])
            w.writerows(rows)
        with open(f"scores/benchmark_{name}_apples.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["game", "snake_length", "moves_to_apple"])
            w.writerows(apple_rows)
    return rows, apple_rows


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("solvers", nargs="+", choices=sorted(SOLVERS))
    parser.add_argument("--games", type=int, default=10)
    parser.add_argument("--seed", type=int, default=None,
                        help="make runs repeatable (game i uses seed + i)")
    parser.add_argument("--width", type=int, default=Constants.ENV_WIDTH,
                        help="board width including walls")
    parser.add_argument("--height", type=int, default=Constants.ENV_HEIGHT,
                        help="board height including walls")
    parser.add_argument("--save", action="store_true",
                        help="write results to scores/benchmark_<solver>*.csv")
    args = parser.parse_args()
    for name in args.solvers:
        benchmark(name, args.games, args.seed, args.width, args.height, args.save)


if __name__ == "__main__":
    main()
