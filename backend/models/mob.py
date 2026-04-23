"""Mob models for game entities (enemies)."""

import uuid
import math
from typing import Dict, Optional


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

    def move_toward_target(self) -> bool:
        """Move the mob one step toward its target.

        Returns True if the mob has reached the target (should be removed).
        """
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist <= self.speed:
            # Reached target
            self.x = self.target_x
            self.y = self.target_y
            return True

        self.x += (dx / dist) * self.speed
        self.y += (dy / dist) * self.speed
        return False

    def to_dict(self) -> Dict:
        """Serialize mob to dictionary for WS broadcasting."""
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        # In isometric space, screenX = (x - y) * constant
        # so the horizontal screen direction is proportional to (dx - dy)
        screen_dx = dx - dy
        if screen_dx < 0:
            direction_x = -1
        elif screen_dx > 0:
            direction_x = 1
        else:
            direction_x = 0
        return {
            "id": self.id,
            "x": round(self.x, 3),
            "y": round(self.y, 3),
            "hp": self.hp,
            "mob_type": self.mob_type,
            "elevation": round(self.elevation, 2),
            "direction_x": direction_x,
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
    ):
        super().__init__(
            x=x,
            y=y,
            hp=100,
            speed=0.1,
            target_x=target_x,
            target_y=target_y,
            mob_type="zombie",
            elevation=elevation,
            id=id,
        )
