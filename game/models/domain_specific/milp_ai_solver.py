"""
MILP solver: the Hamilton Cycle solver with an exact optimiser on top.

Plays exactly like HamiltonCycleSolver (the snake stays on a Hamiltonian cycle
and cannot die). Each time a new apple appears, the cycle found by the local
search is additionally handed to SCIP, which looks for the cycle that reaches
the apple soonest (see game/models/milp/model_builder.py). SCIP may run out of
time; the cycle it started from is then kept, so a time limit costs moves but
never safety.
"""

from game.models.domain_specific.hamilton_cycle_ai_solver import HamiltonCycleSolver
from game.models.milp.model_builder import solve_best_cycle


class MILPAISolver(HamiltonCycleSolver):

    def __init__(self, milp_time_limit=1.0):
        HamiltonCycleSolver.__init__(self, "MILP (SCIP)", "milp", "milp")
        self.milp_time_limit = milp_time_limit  # seconds of SCIP per apple
        self.reset()

    def reset(self):
        HamiltonCycleSolver.reset(self)
        self.solved_apple = None
        self.solves = 0           # SCIP runs
        self.proven_optimal = 0   # ... that proved their cycle is the best one
        self.improved = 0         # ... that beat the local search

    def _improve(self, order, body, apple, w, h):
        order = HamiltonCycleSolver._improve(self, order, body, apple, w, h)
        if apple != self.solved_apple and order[1] != apple:
            self.solved_apple = apple
            before = order.index(apple)
            order, optimal = solve_best_cycle(order, len(body), apple, w, h, self.milp_time_limit)
            self.solves += 1
            self.proven_optimal += int(optimal)
            self.improved += int(order.index(apple) < before)
        return order
