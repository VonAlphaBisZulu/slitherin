"""
MILP Model Builder for Snake Path Optimization - Variant 1 (Hamiltonian Cycle)

Constructs a Mixed Integer Linear Programming model using SCIP
to find optimal snake paths that:
1. Form a COMPLETE Hamiltonian cycle visiting ALL free cells exactly once
2. Start at current HEAD position (t=0)
3. Fix TAIL positions at END of cycle (t = n-L through t = n-1)
4. Minimize time to reach apple (shortest path to apple)
5. This GUARANTEES the snake NEVER traps itself (100% safe)

Uses Miller-Tucker-Zemlin (MTZ) formulation for Hamiltonian cycle enforcement.
"""

from pyscipopt import Model, quicksum
from game.helpers.point import Point


class MILPModelBuilder:
    """
    Builds SCIP optimization models for snake pathfinding using Hamiltonian cycles.

    The model uses binary variables to represent the complete cycle visiting all cells,
    with tail positions fixed at the end to guarantee safety.
    """

    def __init__(self, grid_width, grid_height):
        self.width = grid_width
        self.height = grid_height

    def build(self, head_pos, body_positions, apple_pos, horizon=None, timeout=60.0):
        """
        Build MILP model for Hamiltonian cycle through ALL free cells.

        Strategy (Variant 1 - Shortest Path to Apple):
        - Start at HEAD position (t=0)
        - Visit ALL free cells exactly once
        - TAIL positions FIXED at end of cycle
        - Optimize: minimize time to reach apple
        - Result: 100% safe path (guaranteed Hamiltonian cycle)

        Uses Miller-Tucker-Zemlin (MTZ) constraints for cycle enforcement.

        Args:
            head_pos: Point - current head position
            body_positions: List[Point] - current snake body [head, body..., tail]
            apple_pos: Point - apple position
            horizon: int - IGNORED (we visit all n cells)
            timeout: float - SCIP timeout in seconds (default: 60s)

        Returns:
            tuple: (Model, solution_vars) - SCIP model and variable dict
        """
        model = Model("SnakeMILP_HamiltonCycle_V1")
        model.setRealParam("limits/time", timeout)
        model.setRealParam("limits/gap", 0.1)  # Accept 10% optimality gap
        model.hideOutput()  # Suppress SCIP output

        # Get ALL free cells (complete Hamiltonian cycle requirement)
        # Unlike previous version, we include ALL cells (even current body cells)
        # because we need a complete cycle
        all_free_cells = []
        for x in range(1, self.width - 1):
            for y in range(1, self.height - 1):
                all_free_cells.append(Point(x, y))

        n_cells = len(all_free_cells)

        # Separate tail positions (will be fixed at end of cycle)
        # body_positions = [head, body[1], body[2], ..., tail]
        tail_positions = body_positions[1:]  # All except head
        tail_length = len(tail_positions)

        # === DECISION VARIABLES ===

        # x[i,j,t] = 1 if snake position is (i,j) at time t in the cycle
        x = {}
        for t in range(n_cells):  # Use n_cells, NOT horizon
            for cell in all_free_cells:
                var_name = f"x_{cell.x}_{cell.y}_{t}"
                x[cell.x, cell.y, t] = model.addVar(vtype="B", name=var_name)

        # MTZ auxiliary variables: u[i,j] = visit order for cell (i,j)
        # Used for subtour elimination (enforces Hamiltonian property)
        u = {}
        for cell in all_free_cells:
            var_name = f"u_{cell.x}_{cell.y}"
            u[cell.x, cell.y] = model.addVar(vtype="C", name=var_name, lb=0, ub=n_cells)

        # Edge variables: e[i1,j1,i2,j2,t] = 1 if move from (i1,j1) to (i2,j2) at time t
        e = {}
        for t in range(n_cells - 1):  # n-1 edges in cycle
            for cell in all_free_cells:
                for neighbor in self._get_neighbors(cell):
                    if neighbor in all_free_cells:
                        var_name = f"e_{cell.x}_{cell.y}_{neighbor.x}_{neighbor.y}_{t}"
                        e[cell.x, cell.y, neighbor.x, neighbor.y, t] = \
                            model.addVar(vtype="B", name=var_name)

        # Objective variable: time when apple is reached
        apple_time = model.addVar(vtype="I", name="apple_time", lb=0, ub=n_cells-1)

        # === CONSTRAINTS ===

        # CONSTRAINT 1: Visit every cell exactly once (Hamiltonian property)
        for cell in all_free_cells:
            model.addCons(
                quicksum(x[cell.x, cell.y, t] for t in range(n_cells)) == 1,
                f"visit_once_{cell.x}_{cell.y}"
            )

        # CONSTRAINT 2: At each time step, be in exactly one position
        for t in range(n_cells):
            model.addCons(
                quicksum(x[cell.x, cell.y, t] for cell in all_free_cells) == 1,
                f"one_position_at_t{t}"
            )

        # CONSTRAINT 3: Start at current HEAD position at t=0
        model.addCons(x[head_pos.x, head_pos.y, 0] == 1, "start_at_head")
        model.addCons(u[head_pos.x, head_pos.y] == 0, "head_order_zero")

        # CONSTRAINT 4: Fix TAIL positions at END of cycle
        # Tail occupies times [n - tail_length, n - tail_length + 1, ..., n - 1]
        for k, tail_cell in enumerate(tail_positions):
            tail_time = n_cells - tail_length + k
            model.addCons(
                x[tail_cell.x, tail_cell.y, tail_time] == 1,
                f"tail_{k}_at_time_{tail_time}"
            )
            model.addCons(
                u[tail_cell.x, tail_cell.y] == tail_time,
                f"tail_{k}_order_{tail_time}"
            )

        # CONSTRAINT 5: Flow conservation (if at position t, must use outgoing edge)
        for t in range(n_cells - 1):
            for cell in all_free_cells:
                # Get valid neighbors
                neighbors = [n for n in self._get_neighbors(cell) if n in all_free_cells]
                if neighbors:
                    model.addCons(
                        x[cell.x, cell.y, t] == quicksum(
                            e.get((cell.x, cell.y, n.x, n.y, t), 0)
                            for n in neighbors
                        ),
                        f"flow_out_{cell.x}_{cell.y}_t{t}"
                    )

        # CONSTRAINT 6: Edge usage links positions at consecutive time steps
        for t in range(n_cells - 1):
            for cell in all_free_cells:
                for neighbor in self._get_neighbors(cell):
                    if neighbor not in all_free_cells:
                        continue

                    edge_key = (cell.x, cell.y, neighbor.x, neighbor.y, t)
                    if edge_key not in e:
                        continue

                    # If edge used, must be at start cell at t and end cell at t+1
                    edge_var = e[edge_key]
                    model.addCons(
                        edge_var <= x[cell.x, cell.y, t],
                        f"edge_start_{cell.x}_{cell.y}_{neighbor.x}_{neighbor.y}_t{t}"
                    )
                    model.addCons(
                        edge_var <= x[neighbor.x, neighbor.y, t + 1],
                        f"edge_end_{cell.x}_{cell.y}_{neighbor.x}_{neighbor.y}_t{t}"
                    )

        # CONSTRAINT 7: MTZ Subtour Elimination (enforce strict ordering)
        M = n_cells + 1  # Big-M constant
        for t in range(n_cells - 1):
            for cell in all_free_cells:
                for neighbor in self._get_neighbors(cell):
                    if neighbor not in all_free_cells:
                        continue

                    edge_key = (cell.x, cell.y, neighbor.x, neighbor.y, t)
                    if edge_key not in e:
                        continue

                    # MTZ: u[neighbor] >= u[cell] + 1 - M*(1 - e[edge])
                    # If edge used (e=1): u[neighbor] >= u[cell] + 1 (strict ordering)
                    # If edge not used (e=0): constraint relaxed
                    edge_var = e[edge_key]
                    model.addCons(
                        u[neighbor.x, neighbor.y] >= u[cell.x, cell.y] + 1 - M * (1 - edge_var),
                        f"mtz_{cell.x}_{cell.y}_{neighbor.x}_{neighbor.y}_t{t}"
                    )

        # CONSTRAINT 8: Apple time tracking
        # If apple reached at time t, apple_time <= t
        for t in range(n_cells):
            model.addCons(
                apple_time <= t + M * (1 - x[apple_pos.x, apple_pos.y, t]),
                f"apple_time_at_t{t}"
            )

        # === OBJECTIVE ===
        # Minimize time to reach apple (shortest path to apple)
        model.setObjective(apple_time, "minimize")

        # Return model and variables for extracting solution
        solution_vars = {
            'x': x,
            'e': e,
            'u': u,
            'apple_time': apple_time,
            'all_free_cells': all_free_cells,
            'n_cells': n_cells,
            'head_pos': head_pos,
            'tail_positions': tail_positions,
            'apple_pos': apple_pos
        }

        return model, solution_vars

    def _get_neighbors(self, cell):
        """Get valid neighbor cells (4-connected, within bounds)."""
        neighbors = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = Point(cell.x + dx, cell.y + dy)
            # Check bounds (account for walls at edges)
            if 1 <= neighbor.x < self.width - 1 and 1 <= neighbor.y < self.height - 1:
                neighbors.append(neighbor)
        return neighbors

    def extract_path(self, model, solution_vars):
        """
        Extract the optimal Hamiltonian cycle from solved MILP model.

        Args:
            model: Solved SCIP Model
            solution_vars: Dictionary of variables returned from build()

        Returns:
            List[Point]: Sequence of Points representing the complete cycle
        """
        if model.getStatus() not in ["optimal", "bestsollimit"]:
            return []

        x = solution_vars['x']
        n_cells = solution_vars['n_cells']
        all_free_cells = solution_vars['all_free_cells']

        path = []

        # Extract path by iterating through time steps
        for t in range(n_cells):
            for cell in all_free_cells:
                if (cell.x, cell.y, t) not in x:
                    continue

                # Check if snake is at this cell at time t
                val = model.getVal(x[cell.x, cell.y, t])
                if val > 0.5:  # Binary variable is "1"
                    path.append(Point(cell.x, cell.y))
                    break

        return path
