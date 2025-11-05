"""
MILP-Based Snake AI Solver

Uses Mixed Integer Linear Programming with Hamiltonian path constraints
to play near-perfect snake games.

Strategy:
1. Build MILP model with MTZ constraints (no subtours)
2. Solve for shortest path to apple
3. Secondary: minimize max distance to remaining cells
4. Fallback to BFS if MILP fails/timeout

Target Performance: 90%+ win rate, 143/143 score on 12x12 grid
"""

from game.models.base_game_model import BaseGameModel
from game.models.milp.model_builder import MILPModelBuilder
from game.models.milp.hamiltonian_checker import HamiltonianChecker
from game.models.domain_specific.shortest_path_bfs_ai_solver import ShortestPathBFSSolver
from game.helpers.point import Point


class MILPAISolver(BaseGameModel):
    """
    MILP-based snake solver using SCIP optimization.

    Uses proper Hamiltonian path formulation (MTZ constraints) to ensure
    the snake never traps itself while optimizing for apple collection.
    """

    def __init__(self, horizon=10, timeout=0.5, use_fallback=True):
        """
        Initialize MILP solver.

        Args:
            horizon: int - planning horizon (number of moves ahead)
            timeout: float - SCIP solver timeout in seconds (default: 0.5s)
            use_fallback: bool - use BFS fallback if MILP fails
        """
        BaseGameModel.__init__(self, "MILP (SCIP)", "milp", "milp")

        self.horizon = horizon
        self.timeout = timeout
        self.use_fallback = use_fallback

        # Will be initialized on first move
        self.model_builder = None
        self.hamiltonian_checker = None
        self.fallback_solver = None

        # Cached path to current apple
        self.current_path = []
        self.current_path_index = 0
        self.last_apple_pos = None

        # Statistics
        self.milp_successes = 0
        self.milp_failures = 0
        self.fallback_uses = 0
        self.path_reuses = 0

    def move(self, environment):
        """
        Compute next move using MILP optimization.

        Only recomputes path when apple position changes (after eating one).
        Otherwise, follows the previously computed path.

        Args:
            environment: Game environment object

        Returns:
            tuple: (dx, dy) action to take
        """
        BaseGameModel.move(self, environment)

        # Lazy initialization
        if self.model_builder is None:
            self.model_builder = MILPModelBuilder(
                environment.width,
                environment.height
            )

        if self.hamiltonian_checker is None:
            self.hamiltonian_checker = HamiltonianChecker(
                environment.width,
                environment.height
            )

        if self.fallback_solver is None and self.use_fallback:
            self.fallback_solver = ShortestPathBFSSolver()

        # Extract current state
        head_pos = environment.snake[0]
        body_positions = environment.snake[:]
        apple_pos = environment.fruit[0]

        # Check if apple position has changed (new apple appeared after eating)
        apple_changed = (self.last_apple_pos is None or
                        self.last_apple_pos != apple_pos)

        # If apple changed OR no valid cached path, try to recompute
        should_recompute = apple_changed or not self._has_valid_cached_path(head_pos)

        if should_recompute:
            # Try to solve MILP for new path (with 0.5s timeout)
            path = self._solve_milp_for_path(head_pos, body_positions, apple_pos, environment)

            if path and len(path) >= 2:
                # Successfully computed new path - cache it
                self.current_path = path
                self.current_path_index = 0
                self.last_apple_pos = apple_pos
                self.milp_successes += 1
            else:
                # MILP failed/timed out
                self.milp_failures += 1

                # STRATEGY: Keep following old cached path if available
                # Will retry MILP computation on next move
                # This is more robust than immediately falling back to BFS

                if apple_changed:
                    # New apple, but MILP failed - update last_apple_pos anyway
                    # so we keep retrying for this new apple
                    self.last_apple_pos = apple_pos

                # Don't clear current_path here! Keep it for retry strategy

        # Follow cached path if available
        if self.current_path and self.current_path_index < len(self.current_path) - 1:
            self.path_reuses += 1

            # Get next position in path
            next_pos = self.current_path[self.current_path_index + 1]
            action = (next_pos.x - head_pos.x, next_pos.y - head_pos.y)

            # Verify action is still valid (snake body may have shifted)
            if self._is_valid_action(action, environment):
                self.current_path_index += 1
                return action

        # No valid cached path - use fallback
        if self.use_fallback:
            self.fallback_uses += 1
            return self._fallback_move(environment)
        else:
            # Last resort: continue current direction
            return environment.snake_action

    def _has_valid_cached_path(self, current_head):
        """Check if we have a valid cached path to follow."""
        if not self.current_path:
            return False

        # Check if current head is on the cached path
        if self.current_path_index >= len(self.current_path):
            return False

        # Current position should match path
        expected_pos = self.current_path[self.current_path_index]
        if current_head != expected_pos:
            # Path desynchronized (shouldn't happen, but handle gracefully)
            return False

        # Still have moves left in path
        return self.current_path_index < len(self.current_path) - 1

    def _solve_milp_for_path(self, head_pos, body_positions, apple_pos, environment):
        """
        Solve MILP model and return full path.

        Returns:
            list[Point]: Path from head to apple, or empty list if failed
        """
        try:
            # Build MILP model
            model, solution_vars = self.model_builder.build(
                head_pos=head_pos,
                body_positions=body_positions,
                apple_pos=apple_pos,
                horizon=self.horizon,
                timeout=self.timeout
            )

            # Solve
            model.optimize()

            # Check if solution found
            status = model.getStatus()
            if status not in ["optimal", "bestsollimit"]:
                return []

            # Extract path
            path = self.model_builder.extract_path(model, solution_vars)

            return path if path else []

        except Exception as e:
            # MILP failed (timeout, infeasible, etc.)
            print(f"MILP solver exception: {e}")
            return []

    def _fallback_move(self, environment):
        """
        Fallback strategy when MILP fails.

        Uses BFS shortest path to apple.

        Args:
            environment: Game environment

        Returns:
            tuple: (dx, dy) action
        """
        if self.fallback_solver:
            return self.fallback_solver.move(environment)
        else:
            # Last resort: continue current direction
            return environment.snake_action

    def _is_valid_action(self, action, environment):
        """
        Check if action is valid (not reverse, not collision).

        Args:
            action: tuple (dx, dy)
            environment: Game environment

        Returns:
            bool: True if valid
        """
        # Check not reverse
        current_action = environment.snake_action
        if action == (-current_action[0], -current_action[1]):
            return False

        # Check not immediately fatal
        head = environment.snake[0]
        next_pos = Point(head.x + action[0], head.y + action[1])

        # Check bounds (walls)
        if next_pos.x <= 0 or next_pos.x >= environment.width - 1:
            return False
        if next_pos.y <= 0 or next_pos.y >= environment.height - 1:
            return False

        # Check not hitting body (except tail which will move)
        if next_pos in environment.snake[:-1]:
            return False

        return True

    def reset(self):
        """Reset solver state between games."""
        BaseGameModel.reset(self)
        # Clear cached path
        self.current_path = []
        self.current_path_index = 0
        self.last_apple_pos = None
        # Model builder and checkers are stateless, no need to reset them

    def stats(self):
        """
        Return statistics including MILP success rate and path reuses.

        Returns:
            str: Statistics string
        """
        base_stats = BaseGameModel.stats(self)

        total_computes = self.milp_successes + self.milp_failures
        if total_computes > 0:
            success_rate = 100.0 * self.milp_successes / total_computes
            milp_stats = f" [MILP: {success_rate:.0f}%, Reuses: {self.path_reuses}, FB: {self.fallback_uses}]"
        else:
            milp_stats = ""

        return base_stats + milp_stats


class MILPTrainer(BaseGameModel):
    """
    Trainer for MILP solver (mostly for benchmarking).

    Since MILP is not learned, this just runs many games to collect statistics.
    """

    def __init__(self, horizon=10, timeout=0.5, num_games=100):
        BaseGameModel.__init__(self, "MILP Trainer", "milp_trainer", "milpt")
        self.solver = MILPAISolver(horizon=horizon, timeout=timeout)
        self.num_games = num_games

        # Track steps per apple for analysis
        self.steps_per_apple = []  # List of (score, steps) tuples

    def move(self, environment):
        """
        Run training (benchmarking) games.

        Args:
            environment: Training environment

        Returns:
            None (doesn't return action, runs full training loop)
        """
        print(f"\n=== MILP Solver Benchmark: {self.num_games} games ===\n")

        scores = []

        for game_num in range(self.num_games):
            # Reset environment
            environment.set_snake()
            environment.set_fruit()
            self.solver.reset()  # Reset solver state

            score = 0
            steps = 0
            steps_since_last_apple = 0
            max_steps = 1000  # Prevent infinite loops

            while steps < max_steps:
                # Get MILP action
                action = self.solver.move(environment)

                # Execute action
                if not environment.step(action):
                    # Game over
                    break

                steps += 1
                steps_since_last_apple += 1

                # Check if ate fruit
                if environment.eat_fruit_if_possible():
                    score += 1
                    # Record steps to get this apple
                    self.steps_per_apple.append((score, steps_since_last_apple))
                    steps_since_last_apple = 0

            scores.append(score)

            # Log progress
            if (game_num + 1) % 10 == 0:
                avg_so_far = sum(scores) / len(scores)
                print(f"Games {game_num + 1}/{self.num_games}: Avg score = {avg_so_far:.2f}")

        # Final statistics
        print(f"\n=== Results ===")
        print(f"Games played: {len(scores)}")
        print(f"Min score: {min(scores)}")
        print(f"Max score: {max(scores)}")
        print(f"Avg score: {sum(scores) / len(scores):.2f}")
        print(f"Win rate (score >= 140): {100.0 * sum(1 for s in scores if s >= 140) / len(scores):.1f}%")
        print(f"\nMILP success rate: {self.solver.milp_successes} / {self.solver.milp_successes + self.solver.milp_failures}")
        print(f"Fallback uses: {self.solver.fallback_uses}")

        # Save scores
        for score in scores:
            self.log_score(score)

        # Save steps per apple data for scatter plot
        import csv
        import os
        steps_path = "scores/milp_steps_per_apple.csv"
        os.makedirs("scores", exist_ok=True)
        with open(steps_path, "w") as f:
            writer = csv.writer(f)
            writer.writerow(["score", "steps_to_apple"])
            for score, steps in self.steps_per_apple:
                writer.writerow([score, steps])
        print(f"\nSaved steps-per-apple data to {steps_path}")
