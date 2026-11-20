"""
Hamilton Cycle solver: never dies, and reshapes its cycle to reach the apple sooner.

The snake always lies along a Hamiltonian cycle of the board (see
game/models/cycle/hamiltonian_cycle.py for the exact invariant) and always
steps to the next cell of that cycle, so it cannot trap itself and wins every
game. Before each step the cycle is reshaped by a local search so that the
apple comes as early on it as possible.
"""

from game.helpers.point import Point
from game.models.base_game_model import BaseGameModel
from game.models.cycle.hamiltonian_cycle import zigzag_cycle, rotate_to, improve


class HamiltonCycleSolver(BaseGameModel):

    def __init__(self, long_name="Hamilton Cycle", short_name="hamilton_cycle", abbreviation="hc",
                 time_limit=0.05):
        BaseGameModel.__init__(self, long_name, short_name, abbreviation)
        self.time_limit = time_limit  # seconds of search per move
        self.order = None
        self.size = None

    def reset(self):
        self.order = None

    def move(self, environment):
        BaseGameModel.move(self, environment)
        w, h = environment.width - 2, environment.height - 2  # board without walls
        body = [(p.x - 1, p.y - 1) for p in environment.snake]  # head first
        apple = (environment.fruit[0].x - 1, environment.fruit[0].y - 1)

        order = self._synced_cycle(body, w, h)
        if len(body) < w * h and apple not in body:
            order = self._improve(order, body, apple, w, h)
        if len(body) == 1 and self._is_reverse(order, environment):
            # the game refuses a U-turn, even for a snake of length 1
            order = order[:1] + order[:0:-1]
        self.order = order
        return (order[1][0] - order[0][0], order[1][1] - order[0][1])

    def cycle_points(self):
        """The current cycle as board points, head first (for drawing)."""
        return [Point(x + 1, y + 1) for x, y in self.order or []]

    def _improve(self, order, body, apple, w, h):
        return improve(order, len(body), apple, w, h, self.time_limit)

    def _synced_cycle(self, body, w, h):
        """Our cycle, rotated to the snake's head; a fresh one if they disagree."""
        n = w * h
        order = self.order
        if order is not None and self.size == (w, h):
            order = rotate_to(order, body[0])
            if order[n - len(body) + 1:] == body[:0:-1]:
                return order
        if len(body) > 1:
            raise RuntimeError("the snake does not lie on the solver's cycle; "
                               "this solver has to play a game from its start")
        self.size = (w, h)
        return rotate_to(zigzag_cycle(w, h), body[0])

    @staticmethod
    def _is_reverse(order, environment):
        step = (order[1][0] - order[0][0], order[1][1] - order[0][1])
        current = environment.snake_action
        return current is not None and step == (-current[0], -current[1])
