"""
Simplified A* pathfinding for mobs.

Much simpler than flow fields: each mob gets a cached path that's recomputed
when terrain changes or the mob diverges too far from the expected path.
"""

from typing import Dict, List, Tuple, Set
from services.simple_pathfinder import SimplePathfinder


class PathfindingManager:
    """Manages pathfinding for all mobs using simple A*."""

    def __init__(self, map_obj, pathfinding_config: Dict):
        self.map = map_obj
        self.config = pathfinding_config
        self.pathfinder = SimplePathfinder(pathfinding_config)
        
        # Blocked tiles from turrets
        self.blocked_tiles: Set[Tuple[int, int]] = set()

    def update_blocked_tiles(self, buildings: List) -> None:
        """Update blocked tiles from turret placements.

        Turrets are 3x3 buildings, so block the tile and surrounding tiles.

        Args:
            buildings: List of Building/Turret objects from the map
        """
        self.blocked_tiles.clear()

        for building in buildings:
            if building.building_type == "turret":
                # Block the turret tile and surrounding 3x3 area
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        x = building.x + dx
                        y = building.y + dy
                        if 0 <= x < self.map.width and 0 <= y < self.map.height:
                            self.blocked_tiles.add((x, y))

    def compute_path(
        self,
        mob_id: str,
        mob_x: float,
        mob_y: float,
        target_x: int,
        target_y: int,
    ) -> List[Tuple[int, int]]:
        """Get or compute a path for a mob.

        Args:
            mob_id: Unique mob identifier
            mob_x: Mob X coordinate (float)
            mob_y: Mob Y coordinate (float)
            target_x: Target X tile coordinate
            target_y: Target Y tile coordinate

        Returns:
            List of (x, y) tiles from start to target
        """
        return self.pathfinder.compute_path(
            mob_id,
            mob_x,
            mob_y,
            target_x,
            target_y,
            self.map,
            self.blocked_tiles,
        )

    def clear_cache(self) -> None:
        """Clear all cached paths (call when terrain changes)."""
        self.pathfinder.clear_cache()

    def invalidate_mob_path(self, mob_id: str) -> None:
        """Invalidate path for a specific mob (e.g., when moving away from path)."""
        self.pathfinder.invalidate_mob_path(mob_id)

    def get_next_waypoint(
        self, mob_id: str, mob_x: float, mob_y: float, target_x: int, target_y: int
    ) -> Tuple[int, int]:
        """Get the next waypoint for a mob.

        Args:
            mob_id: Unique mob identifier
            mob_x: Mob X coordinate (float)
            mob_y: Mob Y coordinate (float)
            target_x: Target X tile coordinate
            target_y: Target Y tile coordinate

        Returns:
            Next waypoint as (x, y) coordinates
        """
        return self.pathfinder.get_next_waypoint(
            mob_id, mob_x, mob_y, target_x, target_y, self.map, self.blocked_tiles
        )

    def advance_waypoint(self, mob_id: str) -> None:
        """Advance to the next waypoint for a mob."""
        self.pathfinder.advance_waypoint(mob_id)

    def reached_target(self, mob_id: str) -> None:
        """Notify that a mob reached its target."""
        self.pathfinder.reached_target(mob_id)

