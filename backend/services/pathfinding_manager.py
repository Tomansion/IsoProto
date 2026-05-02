"""
Simplified A* pathfinding for mobs.

Much simpler than flow fields: each mob gets a cached path that's recomputed
when terrain changes or the mob diverges too far from the expected path.
"""

from typing import Dict, List, Tuple, Set
from services.simple_pathfinder import SimplePathfinder


class PathfindingManager:
    """Manages pathfinding for all mobs using simple A*."""

    def __init__(self, map_obj):
        self.map = map_obj
        self.pathfinder = SimplePathfinder()
        
        # Blocked tiles from turrets
        self.blocked_tiles: Set[Tuple[int, int]] = set()
        self.previously_blocked_tiles: Set[Tuple[int, int]] = set()

    def update_blocked_tiles(self, buildings: List) -> List[Tuple[int, int]]:
        """Update blocked tiles from turret placements.

        Turrets are 3x3 buildings, so block the tile and surrounding tiles.

        Args:
            buildings: List of Building/Turret objects from the map

        Returns:
            List of newly blocked tiles
        """
        self.previously_blocked_tiles = self.blocked_tiles.copy()
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
        
        # Return newly blocked tiles
        return list(self.blocked_tiles - self.previously_blocked_tiles)

    def get_newly_blocked_tiles(self) -> List[Tuple[int, int]]:
        """Get tiles that became blocked since last update."""
        return list(self.blocked_tiles - self.previously_blocked_tiles)

    def should_invalidate_path(self, mob_x: float, mob_y: float, path: List[Tuple[int, int]]) -> bool:
        """Check if a path is affected by newly blocked tiles.
        
        A path is affected if any waypoint or nearby tiles are blocked.
        Uses spatial proximity check with a buffer zone.
        
        Args:
            mob_x, mob_y: Mob's current position
            path: List of waypoint tiles in the path
            
        Returns:
            True if path should be invalidated and recalculated
        """
        if not path or not self.get_newly_blocked_tiles():
            return False
        
        newly_blocked = self.get_newly_blocked_tiles()
        
        # Check if any waypoint or nearby tiles are blocked
        # Include a 2-tile buffer around each waypoint
        for tile_x, tile_y in path:
            for dx in [-2, -1, 0, 1, 2]:
                for dy in [-2, -1, 0, 1, 2]:
                    if (tile_x + dx, tile_y + dy) in newly_blocked:
                        return True
        
        # Also check tiles near current position
        cur_x = int(mob_x)
        cur_y = int(mob_y)
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                if (cur_x + dx, cur_y + dy) in newly_blocked:
                    return True
        
        return False

    def compute_path(
        self,
        mob_id: str,
        mob_x: float,
        mob_y: float,
        target_x: int,
        target_y: int,
        mob_type: str = "zombie",
        pathfinding_config: dict = None,
    ) -> List[Tuple[int, int]]:
        """Get or compute a path for a mob.

        Args:
            mob_id: Unique mob identifier
            mob_x: Mob X coordinate (float)
            mob_y: Mob Y coordinate (float)
            target_x: Target X tile coordinate
            target_y: Target Y tile coordinate
            mob_type: Type of mob (for determining cost function)
            pathfinding_config: Mob-specific pathfinding configuration

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
            mob_type,
            pathfinding_config,
        )

    def clear_cache(self) -> None:
        """Clear all cached paths (call when terrain changes)."""
        self.pathfinder.clear_cache()

    def invalidate_mob_path(self, mob_id: str) -> None:
        """Invalidate path for a specific mob (e.g., when moving away from path)."""
        self.pathfinder.invalidate_mob_path(mob_id)

    def invalidate_affected_paths(self, mob_x: float, mob_y: float, mob_id: str, cached_path: List[Tuple[int, int]]) -> None:
        """Invalidate path only if it's affected by newly blocked tiles.
        
        Args:
            mob_x, mob_y: Mob's current position
            mob_id: Mob identifier
            cached_path: Current cached path for the mob
        """
        if self.should_invalidate_path(mob_x, mob_y, cached_path):
            self.invalidate_mob_path(mob_id)

    def get_next_waypoint(
        self, mob_id: str, mob_x: float, mob_y: float, target_x: int, target_y: int, mob_type: str = "zombie", pathfinding_config: dict = None
    ) -> Tuple[int, int]:
        """Get the next waypoint for a mob.

        Args:
            mob_id: Unique mob identifier
            mob_x: Mob X coordinate (float)
            mob_y: Mob Y coordinate (float)
            target_x: Target X tile coordinate
            target_y: Target Y tile coordinate
            mob_type: Type of mob (for determining cost function)
            pathfinding_config: Mob-specific pathfinding configuration

        Returns:
            Next waypoint as (x, y) coordinates
        """
        return self.pathfinder.get_next_waypoint(
            mob_id, mob_x, mob_y, target_x, target_y, self.map, self.blocked_tiles, mob_type, pathfinding_config
        )

    def advance_waypoint(self, mob_id: str) -> None:
        """Advance to the next waypoint for a mob."""
        self.pathfinder.advance_waypoint(mob_id)

    def reached_target(self, mob_id: str) -> None:
        """Notify that a mob reached its target."""
        self.pathfinder.reached_target(mob_id)

