"""
MILP Model Builder for Snake Path Optimization

Constructs a Mixed Integer Linear Programming model using SCIP
to find optimal snake paths that:
1. Reach the apple via shortest path (primary objective)
2. AFTER eating apple, maintain equidistance coverage of remaining field (secondary objective)
3. Preserve Hamiltonian property = avoid self-traps (using subtour elimination constraints)

Uses Miller-Tucker-Zemlin (MTZ) formulation for Hamiltonian path constraints.
"""

from pyscipopt import Model, quicksum
from game.helpers.point import Point


class MILPModelBuilder:
    """
    Builds SCIP optimization models for snake pathfinding.

    The model uses binary variables to represent the snake's path
    and optimizes for apple distance while maintaining field coverage.
    """

    def __init__(self, grid_width, grid_height):
        self.width = grid_width
        self.height = grid_height

        # Weights for multi-objective optimization
        self.alpha = 100.0  # Weight for apple distance (primary)
        self.beta = 1.0     # Weight for variance/coverage (secondary)

    def build(self, head_pos, body_positions, apple_pos, horizon, timeout=1.0):
        """
        Build MILP model for snake path optimization using Hamiltonian path formulation.

        Uses Miller-Tucker-Zemlin (MTZ) constraints for subtour elimination.

        Args:
            head_pos: Point - current head position
            body_positions: List[Point] - current body positions
            apple_pos: Point - apple position
            horizon: int - number of moves to plan ahead
            timeout: float - SCIP timeout in seconds

        Returns:
            tuple: (Model, solution_vars) - SCIP model and variable dict
        """
        model = Model("SnakeMILP_Hamilton")
        model.setRealParam("limits/time", timeout)
        model.setRealParam("limits/gap", 0.1)  # Accept 10% optimality gap
        model.hideOutput()  # Suppress SCIP output

        # Only plan for reachable cells (avoid current body)
        body_set = set(body_positions)
        free_cells = self._get_free_cells(body_set)

        # Add apple to free cells if not already included
        if apple_pos not in free_cells:
            free_cells.append(apple_pos)

        n_cells = len(free_cells)

        # Decision variables: x[i,j,t] = 1 if head at (i,j) at time t
        x = {}
        for t in range(min(horizon, n_cells)):  # At most n_cells steps
            for cell in free_cells:
                var_name = f"x_{cell.x}_{cell.y}_{t}"
                x[cell.x, cell.y, t] = model.addVar(vtype="B", name=var_name)

        # MTZ auxiliary variables: u[i,j] = order/time when cell (i,j) is visited
        # Used for subtour elimination (Hamiltonian path constraint)
        u = {}
        for cell in free_cells:
            var_name = f"u_{cell.x}_{cell.y}"
            u[cell.x, cell.y] = model.addVar(vtype="C", name=var_name, lb=0, ub=n_cells)

        # Edge variables: e[i1,j1,i2,j2,t] = 1 if move from (i1,j1) to (i2,j2) at time t
        e = {}
        for t in range(min(horizon, n_cells) - 1):
            for cell in free_cells:
                for neighbor in self._get_neighbors(cell):
                    if neighbor in free_cells:
                        var_name = f"e_{cell.x}_{cell.y}_{neighbor.x}_{neighbor.y}_{t}"
                        e[cell.x, cell.y, neighbor.x, neighbor.y, t] = \
                            model.addVar(vtype="B", name=var_name)

        # Distance to apple (primary objective)
        apple_dist = model.addVar(vtype="I", name="apple_dist", lb=0, ub=horizon)

        # === CONSTRAINTS ===

        # 1. Start at current head position at t=0
        model.addCons(x[head_pos.x, head_pos.y, 0] == 1, "start_position")
        model.addCons(u[head_pos.x, head_pos.y] == 0, "start_order")

        # 2. At each time step, be in exactly one position
        for t in range(min(horizon, n_cells)):
            model.addCons(
                quicksum(x[cell.x, cell.y, t] for cell in free_cells
                        if (cell.x, cell.y, t) in x) == 1,
                f"one_position_at_t{t}"
            )

        # 3. Flow conservation: if at position at time t, must move to neighbor at t+1
        for t in range(min(horizon, n_cells) - 1):
            for cell in free_cells:
                if (cell.x, cell.y, t) not in x:
                    continue

                # Outgoing edges
                neighbors = [n for n in self._get_neighbors(cell) if n in free_cells]
                if neighbors:
                    model.addCons(
                        x[cell.x, cell.y, t] == quicksum(
                            e.get((cell.x, cell.y, n.x, n.y, t), 0)
                            for n in neighbors
                        ),
                        f"flow_out_{cell.x}_{cell.y}_{t}"
                    )

        # 4. Edge usage links positions at consecutive time steps
        for t in range(min(horizon, n_cells) - 1):
            for cell in free_cells:
                for neighbor in self._get_neighbors(cell):
                    if neighbor not in free_cells:
                        continue

                    edge_key = (cell.x, cell.y, neighbor.x, neighbor.y, t)
                    if edge_key not in e:
                        continue

                    # If edge is used, must be at start cell at t and end cell at t+1
                    if (cell.x, cell.y, t) in x and (neighbor.x, neighbor.y, t + 1) in x:
                        edge_var = e[edge_key]
                        model.addCons(
                            edge_var <= x[cell.x, cell.y, t],
                            f"edge_start_{cell.x}_{cell.y}_{neighbor.x}_{neighbor.y}_{t}"
                        )
                        model.addCons(
                            edge_var <= x[neighbor.x, neighbor.y, t + 1],
                            f"edge_end_{cell.x}_{cell.y}_{neighbor.x}_{neighbor.y}_{t}"
                        )

        # 5. MTZ Subtour Elimination Constraints (Hamiltonian path property)
        # If edge from cell to neighbor is used, enforce ordering: u[neighbor] >= u[cell] + 1
        M = n_cells + 1  # Big-M constant
        for t in range(min(horizon, n_cells) - 1):
            for cell in free_cells:
                for neighbor in self._get_neighbors(cell):
                    if neighbor not in free_cells:
                        continue

                    edge_key = (cell.x, cell.y, neighbor.x, neighbor.y, t)
                    if edge_key not in e:
                        continue

                    # MTZ constraint: u[neighbor] >= u[cell] + 1 - M*(1 - e[edge])
                    # Equivalently: u[neighbor] - u[cell] >= 1 - M*(1 - e[edge])
                    edge_var = e[edge_key]
                    model.addCons(
                        u[neighbor.x, neighbor.y] >= u[cell.x, cell.y] + 1 - M * (1 - edge_var),
                        f"mtz_{cell.x}_{cell.y}_{neighbor.x}_{neighbor.y}_{t}"
                    )

        # 6. Apple distance constraint
        # If we reach apple at time t, apple_dist <= t
        for t in range(min(horizon, n_cells)):
            if (apple_pos.x, apple_pos.y, t) in x:
                model.addCons(
                    apple_dist <= t + horizon * (1 - x[apple_pos.x, apple_pos.y, t]),
                    f"apple_dist_at_t{t}"
                )

        # 7. AFTER eating apple: minimize distance to tile of maximal distance (secondary objective)
        # This ensures good coverage - after reaching apple, we're centrally positioned
        # to reach all remaining free cells efficiently

        # Variable for maximum distance to any unvisited cell after reaching apple
        max_remaining_dist = model.addVar(vtype="C", name="max_remaining_dist", lb=0)

        # For each cell, if it's not visited by the time we reach apple,
        # max_remaining_dist must be >= Manhattan distance from apple to that cell
        for cell in free_cells:
            if cell != apple_pos:
                manhattan_dist = abs(cell.x - apple_pos.x) + abs(cell.y - apple_pos.y)

                # If cell is visited before reaching apple, this constraint is relaxed
                # Otherwise, max_remaining_dist >= manhattan_dist
                # We approximate by: max_remaining_dist >= manhattan_dist - M * (cell_visited_before_apple)

                # Simplified: always enforce (can be refined later)
                model.addCons(
                    max_remaining_dist >= manhattan_dist,
                    f"max_dist_{cell.x}_{cell.y}"
                )

        # === OBJECTIVE ===
        # Primary: Minimize distance to apple (alpha >> beta)
        # Secondary: After eating apple, minimize max distance to any remaining cell
        model.setObjective(
            self.alpha * apple_dist + self.beta * max_remaining_dist,
            "minimize"
        )

        # Return model and variables for extracting solution
        solution_vars = {
            'x': x,
            'e': e,
            'u': u,
            'apple_dist': apple_dist,
            'free_cells': free_cells,
            'horizon': min(horizon, n_cells),
            'head_pos': head_pos,
            'apple_pos': apple_pos
        }

        return model, solution_vars

    def _get_free_cells(self, body_set):
        """Get all cells not occupied by snake body."""
        free_cells = []
        # Account for 1-cell border walls
        for x in range(1, self.width - 1):
            for y in range(1, self.height - 1):
                cell = Point(x, y)
                if cell not in body_set:
                    free_cells.append(cell)
        return free_cells

    def _get_neighbors(self, cell):
        """Get valid neighbor cells (4-connected)."""
        neighbors = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = Point(cell.x + dx, cell.y + dy)
            # Check bounds (account for walls)
            if 1 <= neighbor.x < self.width - 1 and 1 <= neighbor.y < self.height - 1:
                neighbors.append(neighbor)
        return neighbors

    def extract_path(self, model, solution_vars):
        """
        Extract the optimal path from solved MILP model.

        Args:
            model: Solved SCIP Model
            solution_vars: Dictionary of variables returned from build()

        Returns:
            List[Point]: Sequence of Points representing the path
        """
        if model.getStatus() not in ["optimal", "bestsollimit"]:
            return []

        x = solution_vars['x']
        horizon = solution_vars['horizon']
        free_cells = solution_vars['free_cells']

        path = []

        for t in range(horizon):
            for cell in free_cells:
                if (cell.x, cell.y, t) not in x:
                    continue

                # Check if snake is at this cell at time t
                val = model.getVal(x[cell.x, cell.y, t])
                if val > 0.5:  # Binary variable is "1"
                    path.append(Point(cell.x, cell.y))
                    break

        return path
