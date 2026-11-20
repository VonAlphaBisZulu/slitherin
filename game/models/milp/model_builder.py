"""
MILP for the best Hamiltonian cycle (SCIP).

Same question the local search in game/models/cycle answers heuristically,
asked exactly: among all Hamiltonian cycles of the board that contain the
snake's body as one stretch (tail -> ... -> neck -> head), which one reaches
the apple soonest?

Model, on the directed grid graph of the w*h free cells:

    y[a,b] in {0,1}   the cycle steps from cell a to neighbour b
    u[c]   in [0,n-1] number of steps from the head to cell c along the cycle

    every cell has exactly one outgoing and one incoming step
    y[b_k+1, b_k] = 1 along the body       (the snake itself is part of the cycle)
    u[head] = 0
    u[b] >= u[a] + 1 - n * (1 - y[a,b])    for b != head   (Miller-Tucker-Zemlin:
                                           one single cycle, no separate loops)
    minimise u[apple]

The cycle the snake is currently on is always a feasible solution, so it is
handed to SCIP as a start. Whatever happens (time limit, no improvement), the
result is a valid cycle, so stopping the solver early is always safe.
"""

from pyscipopt import Model, quicksum


def _neighbours(cell, w, h):
    x, y = cell
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if 0 <= x + dx < w and 0 <= y + dy < h:
            yield (x + dx, y + dy)


def solve_best_cycle(order, body_len, apple, w, h, time_limit=1.0):
    """
    order     -- current cycle: order[0] is the head, the body is the end of
                 the list (tail first, neck last)
    body_len  -- snake length, head included
    Returns (cycle, proven_optimal). The cycle obeys the same convention and is
    never worse than `order`.
    """
    n = len(order)
    head = order[0]
    pos = {c: k for k, c in enumerate(order)}
    if pos[apple] == 1:
        return order, True

    model = Model("best_hamiltonian_cycle")
    model.hideOutput()
    model.setRealParam("limits/time", time_limit)

    y = {(a, b): model.addVar(vtype="B") for a in order for b in _neighbours(a, w, h)}
    u = {c: model.addVar(vtype="C", lb=0, ub=n - 1) for c in order}

    for c in order:
        model.addCons(quicksum(y[c, b] for b in _neighbours(c, w, h)) == 1)
        model.addCons(quicksum(y[a, c] for a in _neighbours(c, w, h)) == 1)
    for k in range(n - body_len + 1, n):  # tail .. neck, each steps to the next
        model.addCons(y[order[k], order[(k + 1) % n]] == 1)
    model.addCons(u[head] == 0)
    for (a, b), var in y.items():
        if b != head:
            model.addCons(u[b] >= u[a] + 1 - n * (1 - var))
    model.setObjective(u[apple], "minimize")

    start = model.createSol()
    for (a, b), var in y.items():
        model.setSolVal(start, var, 1.0 if pos[b] == (pos[a] + 1) % n else 0.0)
    for c in order:
        model.setSolVal(start, u[c], pos[c])
    model.addSol(start, free=True)

    model.optimize()
    if model.getNSols() == 0:
        return order, False
    succ = {a: b for (a, b), var in y.items() if model.getVal(var) > 0.5}
    new_order = [head]
    while len(new_order) < n:
        new_order.append(succ[new_order[-1]])
    if new_order.index(apple) >= pos[apple]:
        new_order = order
    return new_order, model.getStatus() == "optimal"
