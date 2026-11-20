#!/usr/bin/env python3
"""
Pictures from real games (no window needed).

    python visualize.py gif hamilton_cycle            # assets/gifs/hamilton_cycle.gif
    python visualize.py plot hamilton hamilton_cycle  # scores/benchmark_moves_per_apple.png

`gif` plays one game and records every move. `plot` reads the files written by
`python benchmark.py <solver> --save` and shows how many moves each solver needs
per apple as the snake grows.
"""

import argparse
import csv
import random
from collections import defaultdict

from benchmark import SOLVERS, make_solver
from game.environment.environment import Environment
from game.helpers.constants import Constants


def record_gif(name, seed, cell, path):
    from PIL import Image, ImageDraw
    random.seed(seed)
    solver = make_solver(name)
    env = Environment(width=Constants.ENV_WIDTH, height=Constants.ENV_HEIGHT)
    env.snake_action = None
    env.set_wall()
    env.set_fruit()
    env.set_snake()
    solver.reset()
    tiles = env._available_tiles_count()

    def frame():
        img = Image.new("P", (env.width * cell, env.height * cell), 0)
        img.putpalette([255, 255, 255, 60, 60, 60, 46, 160, 67, 20, 90, 40, 220, 50, 50])
        draw = ImageDraw.Draw(img)
        box = lambda p, colour: draw.rectangle(
            [p.x * cell, p.y * cell, (p.x + 1) * cell - 2, (p.y + 1) * cell - 2], fill=colour)
        for p in env.wall:
            box(p, 1)
        for p in env.snake[1:]:
            box(p, 2)
        box(env.snake[0], 3)
        if env.fruit[0] not in env.snake:
            box(env.fruit[0], 4)
        return img

    frames, since_apple = [frame()], 0
    while env.reward() < tiles and since_apple <= 4 * tiles:
        if env.eat_fruit_if_possible():
            since_apple = 0
            continue
        if not env.step(solver.move(env)):
            break
        since_apple += 1
        frames.append(frame())
    frames += [frames[-1]] * 30  # hold the final picture
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=40, loop=0, optimize=True)
    print(f"{path}: {len(frames) - 30} moves, final score {env.reward()} of {tiles}")


def plot(names, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for name in names:
        by_length = defaultdict(list)
        with open(f"scores/benchmark_{name}_apples.csv") as f:
            for row in csv.DictReader(f):
                by_length[int(row["snake_length"])].append(int(row["moves_to_apple"]))
        lengths = sorted(by_length)
        games = len(by_length[lengths[0]])
        ax.plot(lengths, [sum(by_length[n]) / len(by_length[n]) for n in lengths],
                label=f"{name} ({games} games)")
    ax.set_xlabel("snake length when the apple appears")
    ax.set_ylabel("moves to reach the apple (mean)")
    ax.set_title("Moves per apple")
    ax.legend(loc="upper right")
    ax.grid(alpha=0.3)
    fig.savefig(path, dpi=120, bbox_inches="tight")
    print(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    g = sub.add_parser("gif")
    g.add_argument("solver", choices=sorted(SOLVERS))
    g.add_argument("--seed", type=int, default=1)
    g.add_argument("--cell", type=int, default=16, help="pixels per tile")
    p = sub.add_parser("plot")
    p.add_argument("solvers", nargs="+", choices=sorted(SOLVERS))
    args = parser.parse_args()
    if args.command == "gif":
        record_gif(args.solver, args.seed, args.cell, f"assets/gifs/{args.solver}.gif")
    else:
        plot(args.solvers, "scores/benchmark_moves_per_apple.png")


if __name__ == "__main__":
    main()
