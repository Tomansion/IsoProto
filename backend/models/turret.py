"""Turret model for defensive buildings."""

import math
from typing import List, Optional
from models.map import Building


class Turret(Building):
    """Represents a turret that can target and track mobs."""

    def __init__(
        self,
        x: int,
        y: int,
        building_id: int = 0,
        id: str = None,
        player_id: str = None,
        orientation: int = 0,
        range: float = 20.0,
    ):
        super().__init__(
            x=x,
            y=y,
            building_id=building_id,
            id=id,
            building_type="turret",
            player_id=player_id,
            orientation=orientation,
        )
        self.target_mob_id: Optional[str] = None
        self.range = range  # Maximum targeting distance

    def update_target(self, mobs: List) -> Optional[int]:
        """Update turret to target the closest mob within range and rotate toward it.

        Returns the new orientation (0-7) if a mob was found and orientation changed,
        or None if no mob found within range or orientation didn't change.
        """
        if not mobs:
            self.target_mob_id = None
            return None

        # Find closest mob within range
        closest_mob = None
        closest_distance = float("inf")

        for mob in mobs:
            dx = mob.x - self.x
            dy = mob.y - self.y
            distance = math.sqrt(dx * dx + dy * dy)

            # Only consider mobs within range
            if distance > self.range:
                continue

            if distance < closest_distance:
                closest_distance = distance
                closest_mob = mob

        if closest_mob is None:
            self.target_mob_id = None
            return None

        self.target_mob_id = closest_mob.id

        # Calculate angle from turret to mob
        dx = closest_mob.x - self.x
        dy = closest_mob.y - self.y
        angle = math.atan2(dy, dx)  # In radians, 0 = right, PI/2 = down

        # Convert to 8-direction orientation (0-7)
        # Each orientation covers 45 degrees (PI/4 radians)
        # Orientation 0 = right (angle ~0)
        # Orientation 1 = down-right (angle ~PI/4)
        # Orientation 2 = down (angle ~PI/2)
        # etc.
        normalized_angle = angle + math.pi / 8  # Offset by 22.5 degrees to center bins
        if normalized_angle < 0:
            normalized_angle += 2 * math.pi

        new_orientation = int((normalized_angle / (2 * math.pi)) * 8) % 8

        # Return orientation if it changed
        if new_orientation != self.orientation:
            self.orientation = new_orientation
            return new_orientation

        return None
