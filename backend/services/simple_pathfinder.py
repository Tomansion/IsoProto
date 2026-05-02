"""
Simple A* pathfinding for mobs.

Much simpler than Dijkstra flow fields: direct A* search with minimal costs.
"""

import heapq
from typing import List, Tuple, Dict, Set
from random import random


class SimplePathfinder:
    """A* pathfinding algorithm - direct path computation."""

    def __init__(self):
        # Cache: mob_id -> path (list of tiles)
        self.path_cache: Dict[str, List[Tuple[int, int]]] = {}
        # Track current waypoint index per mob
        self.path_index: Dict[str, int] = {}

    def is_passable(
        self, x: int, y: int, map_obj, blocked_tiles: Set[Tuple[int, int]]
    ) -> bool:
        """Check if a tile is passable."""
        # Bounds check
        if x < 0 or x >= map_obj.width or y < 0 or y >= map_obj.height:
            return False

        # Turrets block movement
        if (x, y) in blocked_tiles:
            return False

        return True

    def get_cost(self, x: int, y: int, map_obj, pathfinding_config: dict = None) -> float:
        """Get cost to enter a tile based on mob-specific configuration.
        
        Args:
            x, y: Tile coordinates
            map_obj: Game map
            pathfinding_config: Mob-specific pathfinding config with:
                - base_cost: Base cost (default 1.0)
                - tree_cost: Additional cost for trees (default 0.5)
                - water_cost: Additional cost for water (default 10.0)
                - randomness: Random variation factor (default 0.0)
        
        Returns:
            Cost to enter the tile
        """
        if pathfinding_config is None:
            pathfinding_config = {
                "base_cost": 1.0,
                "tree_cost": 0.5,
                "water_cost": 10.0,
                "randomness": 0.0,
            }
        
        base_cost = pathfinding_config.get("base_cost", 1.0)
        tree_cost = pathfinding_config.get("tree_cost", 0.5)
        water_cost = pathfinding_config.get("water_cost", 10.0)
        randomness = pathfinding_config.get("randomness", 0.0)
        
        cost = base_cost
        
        # Add randomness if configured
        if randomness > 0:
            cost += (random() - 0.5) * 2 * randomness * base_cost

        # Trees add cost but are passable
        if map_obj.tiles[y][x] == 1:  # TILE_TREE
            cost += tree_cost
            if randomness > 0:
                cost += (random() - 0.5) * 2 * randomness * tree_cost

        # Water (elevation <= 0) is hard to cross
        if map_obj.elevation[y][x] <= 0:
            cost += water_cost

        return cost

    def heuristic(self, x: int, y: int, goal_x: int, goal_y: int) -> float:
        """Chebyshev distance heuristic (admissible for 8-neighbor grids)."""
        return max(abs(x - goal_x), abs(y - goal_y))

    def find_path(
        self,
        start_x: int,
        start_y: int,
        goal_x: int,
        goal_y: int,
        map_obj,
        blocked_tiles: Set[Tuple[int, int]],
        pathfinding_config: dict = None,
    ) -> List[Tuple[int, int]]:
        """Find path from start to goal using A*.

        Args:
            start_x, start_y: Starting position
            goal_x, goal_y: Goal position
            map_obj: Game map
            blocked_tiles: Set of impassable tiles (turrets)
            pathfinding_config: Mob-specific pathfinding configuration

        Returns:
            List of (x, y) tiles from start to goal (excluding start)
        """
        # If start == goal, no path needed
        if start_x == goal_x and start_y == goal_y:
            return []

        # If start is blocked, can't move
        if not self.is_passable(start_x, start_y, map_obj, blocked_tiles):
            return []

        # Open set: priority queue of (f_score, counter, x, y)
        open_set = []
        counter = 0
        heapq.heappush(open_set, (0, counter, start_x, start_y))

        # Track visited nodes
        closed_set: Set[Tuple[int, int]] = set()

        # g_score: actual cost from start to each node
        g_score = {(start_x, start_y): 0.0}

        # came_from: for path reconstruction
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}

        MAX_ITERATIONS = 8000
        iterations = 0

        while open_set and iterations < MAX_ITERATIONS:
            iterations += 1
            _, _, x, y = heapq.heappop(open_set)

            # Skip if already processed
            if (x, y) in closed_set:
                continue

            closed_set.add((x, y))

            # Success: reached goal
            if x == goal_x and y == goal_y:
                # Reconstruct path
                path = []
                current = (x, y)
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path

            # Explore 8 neighbors
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue

                    nx, ny = x + dx, y + dy

                    # Skip if already explored
                    if (nx, ny) in closed_set:
                        continue

                    # Skip if not passable
                    if not self.is_passable(nx, ny, map_obj, blocked_tiles):
                        continue

                    # Calculate cost using mob-specific config
                    move_cost = self.get_cost(nx, ny, map_obj, pathfinding_config)

                    # Diagonal moves cost slightly more
                    if dx != 0 and dy != 0:
                        move_cost *= 1.4

                    new_g_score = g_score[(x, y)] + move_cost

                    # If we found a better path to this neighbor
                    if (nx, ny) not in g_score or new_g_score < g_score[(nx, ny)]:
                        came_from[(nx, ny)] = (x, y)
                        g_score[(nx, ny)] = new_g_score
                        f_score = new_g_score + self.heuristic(nx, ny, goal_x, goal_y)
                        counter += 1
                        heapq.heappush(open_set, (f_score, counter, nx, ny))

        # No path found
        print("Path Not found")
        return []

    def compute_path(
        self,
        mob_id: str,
        mob_x: float,
        mob_y: float,
        goal_x: int,
        goal_y: int,
        map_obj,
        blocked_tiles: Set[Tuple[int, int]],
        mob_type: str = "zombie",
        pathfinding_config: dict = None,
    ) -> List[Tuple[int, int]]:
        """Compute or retrieve cached path for a mob.

        Args:
            mob_id: Unique mob identifier
            mob_x, mob_y: Mob's current position (float)
            goal_x, goal_y: Goal tile coordinates
            map_obj: Game map
            blocked_tiles: Set of blocked tiles
            mob_type: Type of mob (for determining cost function)
            pathfinding_config: Mob-specific pathfinding configuration

        Returns:
            Path from current position to goal
        """
        start_x = int(round(mob_x))
        start_y = int(round(mob_y))

        # Check if we have a cached path for this mob
        cached = self.path_cache.get(mob_id)
        if cached and len(cached) > 0:
            return cached
            # If mob hasn't moved far, reuse cached path
            next_x, next_y = cached[0]
            dist = abs(mob_x - next_x) + abs(mob_y - next_y)
            if dist < 2:  # Still close to expected waypoint
                return cached

        # Compute new path
        path = self.find_path(start_x, start_y, goal_x, goal_y, map_obj, blocked_tiles, pathfinding_config)
        self.path_cache[mob_id] = path
        return path

    def get_next_waypoint(
        self,
        mob_id: str,
        mob_x: float,
        mob_y: float,
        goal_x: int,
        goal_y: int,
        map_obj,
        blocked_tiles: Set[Tuple[int, int]],
        mob_type: str = "zombie",
        pathfinding_config: dict = None,
    ) -> Tuple[float, float]:
        """Get the next waypoint for a mob.

        Computes path if needed and returns the next waypoint coordinate.
        Handles path recomputation if mob diverges from cached path.

        Args:
            mob_id: Unique mob identifier
            mob_x, mob_y: Mob's current position (float)
            goal_x, goal_y: Goal tile coordinates
            map_obj: Game map
            blocked_tiles: Set of blocked tiles
            mob_type: Type of mob (for determining cost function)
            pathfinding_config: Mob-specific pathfinding configuration

        Returns:
            Next waypoint as (x, y) float coordinates
        """
        # Get or compute path
        path = self.compute_path(
            mob_id, mob_x, mob_y, goal_x, goal_y, map_obj, blocked_tiles, mob_type, pathfinding_config
        )

        # Initialize path index if not exists
        if mob_id not in self.path_index:
            self.path_index[mob_id] = 0

        path_idx = self.path_index[mob_id]

        # Return next waypoint or goal if path exhausted
        if path_idx < len(path):
            tile_x, tile_y = path[path_idx]
            return (float(tile_x), float(tile_y))
        else:
            return (float(goal_x), float(goal_y))

    def advance_waypoint(self, mob_id: str) -> None:
        """Advance to the next waypoint in the path.

        Args:
            mob_id: Unique mob identifier
        """
        if mob_id in self.path_index:
            self.path_index[mob_id] += 1

    def reached_target(self, mob_id: str) -> None:
        """Notify that mob reached its target - clear cached path and index.

        Args:
            mob_id: Unique mob identifier
        """
        self.path_cache.pop(mob_id, None)
        self.path_index.pop(mob_id, None)

    def clear_cache(self) -> None:
        """Clear all cached paths."""
        self.path_cache.clear()
        self.path_index.clear()

    def invalidate_mob_path(self, mob_id: str) -> None:
        """Invalidate path for a specific mob."""
        self.path_cache.pop(mob_id, None)
        self.path_index.pop(mob_id, None)
