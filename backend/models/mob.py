"""Mob models for game entities (enemies)."""

import uuid
import math
from typing import Dict, Tuple
from services.pathfinding_manager import PathfindingManager


class Mob:
    """Base class for all moving game entities (enemies)."""

    def __init__(
        self,
        x: float,
        y: float,
        hp: int = 100,
        speed: float = 0.3,
        target_x: float = 0.0,
        target_y: float = 0.0,
        mob_type: str = "mob",
        elevation: float = 0.0,
        id: str = None,
        pathfinding_manager=None,
        map_obj=None,
        terrain_multipliers: Dict[str, float] = None,
        pathfinding_config: Dict = None,
    ):
        self.id = id or str(uuid.uuid4())
        self.x = float(x)
        self.y = float(y)
        self.hp = hp
        self.speed = speed
        self.target_x = float(target_x)
        self.target_y = float(target_y)
        self.mob_type = mob_type
        self.elevation = elevation
        self.pathfinding_manager: PathfindingManager = pathfinding_manager
        self.map_obj = map_obj
        self.orientation = 0  # 0-7 direction based on movement
        self.terrain_multipliers = terrain_multipliers or {
            "tree": 1.0,
            "water": 1.0,
            "default": 1.0,
        }
        self.pathfinding_config = pathfinding_config or {
            "base_cost": 1.0,
            "tree_cost": 0.5,
            "water_cost": 10.0,
            "randomness": 0.0,
        }

    def get_current_waypoint(self) -> Tuple[float, float]:
        """Get the current waypoint from the mob's pathfinding manager.

        Returns:
            (waypoint_x, waypoint_y) as float coordinates, or target if no
            pathfinding manager available
        """
        if self.pathfinding_manager:
            waypoint_x, waypoint_y = self.pathfinding_manager.get_next_waypoint(
                self.id,
                self.x,
                self.y,
                int(self.target_x),
                int(self.target_y),
                self.mob_type,
                self.pathfinding_config,
            )
            return (waypoint_x, waypoint_y)

        # Fallback: return target if no pathfinding manager
        return (self.target_x, self.target_y)

    def _get_terrain_multiplier(self) -> float:
        """Get speed multiplier based on current terrain."""
        if not self.map_obj:
            return self.terrain_multipliers.get("default", 1.0)
        
        tx = max(0, min(self.map_obj.width - 1, round(self.x)))
        ty = max(0, min(self.map_obj.height - 1, round(self.y)))
        
        # Check if there's a tree at this location
        if self.map_obj.tiles[ty][tx] == 1:  # TILE_TREE
            return self.terrain_multipliers.get("tree", 1.0)
        
        # Check if it's water (elevation <= 0)
        if self.map_obj.elevation[ty][tx] <= 0:
            return self.terrain_multipliers.get("water", 1.0)
        
        return self.terrain_multipliers.get("default", 1.0)

    def _calculate_orientation(self, dx: float, dy: float) -> int:
        """Calculate orientation (0-7) from movement direction in isometric space.
        
        Converts cartesian (map) direction to isometric screen direction.
        In isometric projection, world cardinal directions map to screen diagonals:
        - World +x → screen down-right diagonal
        - World +y → screen down-left diagonal
        - World -x → screen up-left diagonal
        - World -y → screen up-right diagonal
        
        Orientation mapping (screen direction):
        0=DOWN, 1=DOWN_LEFT, 2=LEFT, 3=UP_LEFT,
        4=UP, 5=UP_RIGHT, 6=RIGHT, 7=DOWN_RIGHT
        
        Isometric projection:
        screen_dx = dx - dy (positive = right on screen)
        screen_dy = dx + dy (positive = down on screen)
        """
        if dx == 0 and dy == 0:
            return self.orientation
        
        # Convert to isometric screen direction
        screen_dx = dx - dy
        screen_dy = dx + dy
        
         # Use angle-based approach for 8 directions on screen
        # atan2 gives angle in [-π, π] where 0 = right, π/2 = down
        angle = math.atan2(screen_dy, screen_dx)
        
        # Normalize to [0, 2π)
        if angle < 0:
            angle += 2 * math.pi
        
        # Map angle to orientation (0-7)
        # bin size = 2π/8 = π/4 = 45 degrees
        # center each bin: add π/8 before quantizing
        bin_size = 2 * math.pi / 8
        bin_index = int((angle + bin_size / 2) / bin_size) % 8
        
        # Convert bin index to orientation
        # bin 0 (angle ~0): RIGHT (6)
        # bin 1 (angle ~π/4): DOWN_RIGHT (7)
        # bin 2 (angle ~π/2): DOWN (0)
        # bin 3 (angle ~3π/4): DOWN_LEFT (1)
        # bin 4 (angle ~π): LEFT (2)
        # bin 5 (angle ~5π/4): UP_LEFT (3)
        # bin 6 (angle ~3π/2): UP (4)
        # bin 7 (angle ~7π/4): UP_RIGHT (5)
        
        bin_to_orientation = [6, 7, 0, 1, 2, 3, 4, 5]
        return bin_to_orientation[bin_index]

    def move_toward_target(self) -> bool:
        """Move the mob one step along its path toward the target.

        The mob requests waypoints from its pathfinding_manager.
        When reaching a waypoint, it advances in the path cache.
        When reaching the target, it notifies the pathfinding_manager.
        
        Updates orientation based on movement direction.

        Returns:
            True if the mob has reached the target or died (should be removed),
            False otherwise.
        """
        # Check if mob is dead
        if self.hp <= 0:
            # Notify pathfinding manager that we're being removed
            if self.pathfinding_manager:
                self.pathfinding_manager.reached_target(self.id)
            return True
        
        # Check if reached main target
        dx_target = self.target_x - self.x
        dy_target = self.target_y - self.y
        dist_to_target = math.sqrt(dx_target * dx_target + dy_target * dy_target)

        if dist_to_target <= self.speed:
            # Reached target
            self.x = self.target_x
            self.y = self.target_y
            # Notify pathfinding manager that we reached the target
            if self.pathfinding_manager:
                self.pathfinding_manager.reached_target(self.id)
            return True

        # Get current waypoint from pathfinding manager
        waypoint_x, waypoint_y = self.get_current_waypoint()

        dx = waypoint_x - self.x
        dy = waypoint_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        # Apply terrain multiplier to speed
        terrain_mult = self._get_terrain_multiplier()
        adjusted_speed = self.speed * terrain_mult

        if dist <= adjusted_speed:
            # Reached current waypoint, advance path in pathfinding manager
            if self.pathfinding_manager:
                self.pathfinding_manager.advance_waypoint(self.id)

            # Move toward target (will get next waypoint on next tick)
            if dist_to_target > 0:
                self.x += (dx_target / dist_to_target) * adjusted_speed
                self.y += (dy_target / dist_to_target) * adjusted_speed
                # Update orientation based on final movement
                self.orientation = self._calculate_orientation(dx_target, dy_target)
        else:
            # Move toward waypoint
            self.x += (dx / dist) * adjusted_speed
            self.y += (dy / dist) * adjusted_speed
            # Update orientation based on waypoint direction
            self.orientation = self._calculate_orientation(dx, dy)

        return False

    def to_dict(self) -> Dict:
        """Serialize mob to dictionary for WS broadcasting."""
        return {
            "id": self.id,
            "x": round(self.x, 3),
            "y": round(self.y, 3),
            "hp": self.hp,
            "mob_type": self.mob_type,
            "elevation": round(self.elevation, 2),
            "orientation": self.orientation,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Mob":
        """Deserialize mob from dictionary."""
        return cls(
            x=data["x"],
            y=data["y"],
            hp=data.get("hp", 100),
            speed=data.get("speed", 0.3),
            target_x=data.get("target_x", 0.0),
            target_y=data.get("target_y", 0.0),
            mob_type=data.get("mob_type", "mob"),
            elevation=data.get("elevation", 0.0),
            id=data.get("id"),
        )


class Zombie(Mob):
    """A zombie enemy that walks toward the target coordinate."""

    def __init__(
        self,
        x: float,
        y: float,
        target_x: float = 0.0,
        target_y: float = 0.0,
        elevation: float = 0.0,
        id: str = None,
        pathfinding_manager=None,
        map_obj=None,
    ):
        # Import config here to get terrain multipliers and pathfinding config
        from config import MOB_TYPE_CONFIG
        
        zombie_config = MOB_TYPE_CONFIG.get("zombie", {})
        hp = zombie_config.get("hp", 100)
        speed = zombie_config.get("speed", 0.3)
        terrain_multipliers = zombie_config.get("terrain_multipliers")
        pathfinding_config = zombie_config.get("pathfinding")
        
        super().__init__(
            x=x,
            y=y,
            hp=hp,
            speed=speed,
            target_x=target_x,
            target_y=target_y,
            mob_type="zombie",
            elevation=elevation,
            id=id,
            pathfinding_manager=pathfinding_manager,
            map_obj=map_obj,
            terrain_multipliers=terrain_multipliers,
            pathfinding_config=pathfinding_config,
        )
