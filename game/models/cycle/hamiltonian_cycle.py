"""
Hamiltonian cycles on the snake board, and a local search that reshapes them.

Everything here works on the free part of the board: a w x h grid of cells
(x, y) with 0 <= x < w, 0 <= y < h. A cycle is stored as `order`, a list of all
w*h cells in which neighbours in the list (and the last and first cell) are
neighbours on the grid.

The snake is tied to the cycle by one invariant:

    order[0] is the head, and the rest of the body is the END of the list,
    tail first and neck last: order[n-L+1] is the tail, order[n-1] the neck.

So the head walks the list forwards, and the cells it reaches last are exactly
the ones its own body leaves, in the order the body leaves them. A snake that
steps to order[1] keeps the invariant (rotate the list by one), whether or not
it eats. Following the cycle can therefore never kill the snake, and any cycle
that respects the invariant is as safe as any other.

That leaves one free choice: WHICH cycle. `improve` searches for one on which
the apple comes early; `improve_with_restarts` searches harder.
"""

import random
import time


def zigzag_cycle(w, h):
    """A fixed Hamiltonian cycle on a w x h grid. Needs w or h to be even."""
    if h % 2 == 1:
        if w % 2 == 1:
            raise ValueError("a grid with an odd number of cells has no Hamiltonian cycle")
        return [(x, y) for (y, x) in zigzag_cycle(h, w)]
    if w == 1:
        raise ValueError("grid too narrow for a cycle")
    order = []
    for y in range(h):  # rows snake left-right through columns 1..w-1
        xs = range(1, w) if y % 2 == 0 else range(w - 1, 0, -1)
        order += [(x, y) for x in xs]
    order += [(0, y) for y in range(h - 1, -1, -1)]  # column 0 is the way back
    return order


def is_cycle(order, w, h):
    """True if `order` visits every cell once and only steps to grid neighbours."""
    n = w * h
    if len(order) != n or len(set(order)) != n:
        return False
    return all(abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1
               for a, b in zip(order, order[1:] + order[:1]))


def rotate_to(order, head):
    """The same cycle, written starting at `head`."""
    k = order.index(head)
    return order[k:] + order[:k]


def _parallel_pairs(order, pos, w, h):
    """
    All unit squares of the grid on which the cycle runs along two opposite
    sides. Returned as pairs (k1, k2), k1 < k2, of edge numbers, where edge k
    is the step order[k] -> order[k+1] (edge n-1 closes the cycle).

    On a closed curve two such edges always run in opposite directions, so
    order[k1] is next to order[k2+1] and order[k1+1] is next to order[k2].
    """
    n = len(order)

    def edge(a, b):  # edge number if a-b is a cycle edge, else -1
        pa, pb = pos[a], pos[b]
        if pb - pa == 1 or pa - pb == n - 1:
            return pa
        if pa - pb == 1 or pb - pa == n - 1:
            return pb
        return -1

    pairs = []
    for y in range(h - 1):
        for x in range(w - 1):
            p, q, r, s = (x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)
            for k1, k2 in ((edge(p, q), edge(r, s)), (edge(p, r), edge(q, s))):
                if k1 >= 0 and k2 >= 0:
                    pairs.append((k1, k2) if k1 < k2 else (k2, k1))
    return pairs


def _best_move(order, pos, body_len, apple, w, h):
    """
    Best "cut and re-insert" move for bringing the apple forward.

    Cutting the two cycle edges of a square pair (i, j) and joining the ends
    the other way splits the cycle in two: A keeps the head and the body, B is
    the stretch order[i+1..j]. A second square pair, with one edge on A and one
    on B, joins them again, which inserts B into A at a new place. The snake's
    own edges (from the tail to the head) are never cut, so the invariant holds.

    Returns (new position of the apple, i, j, ka, kb) or None if nothing helps.
    """
    n = len(order)
    last_free = n - body_len  # edges 0..last_free may be cut
    pa = pos[apple]
    pairs = _parallel_pairs(order, pos, w, h)
    best = None
    best_pos = pa
    for i, j in pairs:
        if j > last_free:
            continue
        m = j - i  # size of B
        apple_in_b = i < pa <= j
        apple_a = pa if pa <= i else pa - m  # apple's place within A, if it is there
        for k1, k2 in pairs:
            # one edge strictly inside B (i < k < j), the other on A (k < i or k > j)
            in1, in2 = i < k1 < j, i < k2 < j
            if in1 == in2:
                continue
            ka, kb = (k2, k1) if in1 else (k1, k2)
            if i <= ka <= j or ka > last_free:
                continue
            ka_a = ka if ka < i else ka - m  # the A edge, counted within A
            if apple_in_b:
                new = ka_a + 1 + (pa - (kb + 1)) % m
            else:
                new = apple_a + (m if apple_a > ka_a else 0)
            if new < best_pos:
                best_pos, best = new, (new, i, j, ka, kb)
    return best


def _apply_move(order, i, j, ka, kb):
    a_list = order[:i + 1] + order[j + 1:]
    m = j - i
    ka_a = ka if ka < i else ka - m
    b_from_entry = order[kb + 1:j + 1] + order[i + 1:kb + 1]
    return a_list[:ka_a + 1] + b_from_entry + a_list[ka_a + 1:]


def improve(order, body_len, apple, w, h, time_limit=None):
    """
    Reshape the cycle so the apple comes as early as possible after the head.

    order     -- current cycle, obeying the invariant in the module docstring
    body_len  -- snake length L (head included)
    apple     -- cell of the apple (a free cell)
    Returns a cycle obeying the same invariant. It is never worse than the
    input, and stopping early (time_limit, in seconds) is always safe.
    """
    n = len(order)
    deadline = None if time_limit is None else time.time() + time_limit
    while True:
        pos = {c: k for k, c in enumerate(order)}
        if body_len == 1 and n - pos[apple] < pos[apple]:
            # a snake of length 1 may walk the cycle in either direction
            order = order[:1] + order[:0:-1]
            continue
        if pos[apple] == 1:
            return order
        move = _best_move(order, pos, body_len, apple, w, h)
        if move is None:
            return order
        order = _apply_move(order, *move[1:])
        if deadline is not None and time.time() > deadline:
            return order


def _random_move(order, pos, body_len, w, h, rng):
    """A random cut-and-re-insert move (see _best_move), or None if there is none."""
    last_free = len(order) - body_len
    pairs = _parallel_pairs(order, pos, w, h)
    moves = []
    for i, j in pairs:
        if j > last_free:
            continue
        for k1, k2 in pairs:
            in1, in2 = i < k1 < j, i < k2 < j
            if in1 == in2:
                continue
            ka, kb = (k2, k1) if in1 else (k1, k2)
            if not (i <= ka <= j or ka > last_free):
                moves.append((i, j, ka, kb))
    return rng.choice(moves) if moves else None


def improve_with_restarts(order, body_len, apple, w, h, restarts=60, kicks=2, rng=random):
    """
    `improve`, then try to escape its dead end: shake the best cycle with a few
    random moves, improve again, and keep the result if the apple comes earlier.
    Slower than `improve` and a little better; just as safe.
    """
    best = improve(order, body_len, apple, w, h)
    best_pos = best.index(apple)
    for _ in range(restarts):
        if best_pos <= 1:
            break
        candidate = best
        for _ in range(kicks):
            pos = {c: k for k, c in enumerate(candidate)}
            move = _random_move(candidate, pos, body_len, w, h, rng)
            if move is None:
                break
            candidate = _apply_move(candidate, *move)
        candidate = improve(candidate, body_len, apple, w, h)
        if candidate.index(apple) < best_pos:
            best, best_pos = candidate, candidate.index(apple)
    return best
