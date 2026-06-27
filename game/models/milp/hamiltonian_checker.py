"""
Hamiltonian Path Verification for Snake MILP Solver

This module checks if a planned path maintains the Hamiltonian property,
ensuring the snake doesn't trap itself with no path from head to tail.
"""

from collections import deque
from game.helpers.point import Point


class HamiltonianChecker:
    """
    Verifies that a planned snake path maintains connectivity.

    Strategy:
        After executing a planned path, the snake's tail will have moved.
        We check if there exists a path from the new head position to
        the new tail position, avoiding the body in between.

        If no path exists, the snake will eventually trap itself.
    """

    def __init__(self, grid_width, grid_height):
        self.width = grid_width
        self.height = grid_height

    def verify(self, planned_path, current_body, current_tail):
        """
        Verify that planned path doesn't create self-trap.

        Args:
            planned_path: List of Points representing planned moves
            current_body: List of Points representing current snake body
            current_tail: Point representing current tail position

        Returns:
            bool: True if path is safe (no self-trap), False otherwise
        """
        if not planned_path:
            return True

        # Simulate snake movement after executing planned path
        future_head = planned_path[-1]
        future_body = self._simulate_body_after_path(
            current_body,
            planned_path,
            len(current_body)  # Assume length stays same (no apple)
        )

        if not future_body:
            return True

        future_tail = future_body[-1]

        # Check if path exists from future head to future tail
        # Exclude the tail itself as it will move away
        obstacles = set(future_body[:-1])

        path_exists = self._bfs_path_exists(
            start=future_head,
            end=future_tail,
            obstacles=obstacles
        )

        return path_exists

    def _simulate_body_after_path(self, current_body, planned_path, length):
        """
        Simulate snake body positions after executing planned path.

        Args:
            current_body: Current snake body (list of Points)
            planned_path: Planned moves (list of Points)
            length: Snake length

        Returns:
            List of Points representing future body positions
        """
        if not planned_path:
            return current_body

        # New head is at end of planned path
        new_head = planned_path[-1]

        # Body follows the head along the planned path
        # Take last 'length' positions from current body + planned path
        all_positions = list(current_body) + list(planned_path)

        # Keep only the last 'length' positions
        future_body = all_positions[-length:]

        return future_body

    def _bfs_path_exists(self, start, end, obstacles):
        """
        Check if path exists from start to end using BFS.

        Args:
            start: Starting Point
            end: Ending Point
            obstacles: Set of Points to avoid

        Returns:
            bool: True if path exists
        """
        if start == end:
            return True

        # BFS queue
        queue = deque([start])
        visited = {start}

        # Four directions: up, down, left, right
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        while queue:
            current = queue.popleft()

            # Check all neighbors
            for dx, dy in directions:
                next_point = Point(current.x + dx, current.y + dy)

                # Check bounds
                if not self._in_bounds(next_point):
                    continue

                # Check if already visited or obstacle
                if next_point in visited or next_point in obstacles:
                    continue

                # Found the end!
                if next_point == end:
                    return True

                # Add to queue
                visited.add(next_point)
                queue.append(next_point)

        # No path found
        return False

    def _in_bounds(self, point):
        """Check if point is within grid bounds."""
        # Account for walls (1 cell border)
        return (1 <= point.x < self.width - 1 and
                1 <= point.y < self.height - 1)

    def check_simple_connectivity(self, head, tail, body):
        """
        Quick check: Is there currently a path from head to tail?

        This is useful for immediate verification without simulation.

        Args:
            head: Current head Point
            tail: Current tail Point
            body: Current body (list of Points)

        Returns:
            bool: True if path exists
        """
        # Exclude tail and head from obstacles
        obstacles = set(body[1:-1])  # Body without head and tail

        return self._bfs_path_exists(head, tail, obstacles)
