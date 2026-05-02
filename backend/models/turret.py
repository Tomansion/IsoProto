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
        rotation_speed: float = 0.5,  # Rotations per tick (0-1 = partial, >1 = multiple per tick)
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
        self.rotation_speed = rotation_speed  # Speed of rotation in orientations per tick
        self.current_angle = orientation * (2 * math.pi / 8)  # Current angle in radians
        self.idle_timer = 0  # Counter for idle rotation
        self.idle_duration = 60  # Ticks before choosing new idle direction
        self.idle_target_angle = None  # Target angle when idle

    def update_target(self, mobs: List) -> Optional[int]:
        """Update turret to target the closest mob within range and rotate toward it.

        Returns the new orientation (0-7) if orientation changed after smooth rotation,
        or None if no change.
        """
        if not mobs:
            self.target_mob_id = None
            # Start idle rotation if no target
            self._update_idle_rotation()
            return self._update_orientation_from_angle()

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
            # Start idle rotation
            self._update_idle_rotation()
            return self._update_orientation_from_angle()

        self.target_mob_id = closest_mob.id
        self.idle_timer = 0  # Reset idle timer when we have a target
        self.idle_target_angle = None

        # Calculate target angle from turret to mob
        dx = closest_mob.x - self.x
        dy = closest_mob.y - self.y
        target_angle = math.atan2(dy, dx)  # In radians

        # Smooth rotation toward target angle
        return self._rotate_toward_angle(target_angle)

    def _update_idle_rotation(self) -> None:
        """Update idle rotation timer and pick random direction when needed."""
        self.idle_timer += 1
        if self.idle_timer >= self.idle_duration:
            # Pick a random direction
            import random
            random_orientation = random.randint(0, 7)
            self.idle_target_angle = random_orientation * (2 * math.pi / 8)
            self.idle_timer = 0

    def _rotate_toward_angle(self, target_angle: float) -> Optional[int]:
        """Smoothly rotate current angle toward target angle.
        
        Returns the new orientation (0-7) if it changed, None otherwise.
        """
        # Normalize angles to [0, 2π)
        while target_angle < 0:
            target_angle += 2 * math.pi
        while target_angle >= 2 * math.pi:
            target_angle -= 2 * math.pi
        while self.current_angle < 0:
            self.current_angle += 2 * math.pi
        while self.current_angle >= 2 * math.pi:
            self.current_angle -= 2 * math.pi

        # Calculate shortest rotation direction
        diff = target_angle - self.current_angle
        
        # Normalize diff to [-π, π] to find shortest path
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi

        # Rotate toward target by rotation_speed amount
        rotation_radians = self.rotation_speed * (2 * math.pi / 8)
        
        if abs(diff) <= rotation_radians:
            # Close enough, snap to target
            self.current_angle = target_angle
        else:
            # Rotate by speed amount in the right direction
            self.current_angle += rotation_radians if diff > 0 else -rotation_radians

        return self._update_orientation_from_angle()

    def _update_orientation_from_angle(self) -> Optional[int]:
        """Convert current angle to discrete orientation (0-7) and return if changed."""
        # Normalize current_angle to [0, 2π)
        while self.current_angle < 0:
            self.current_angle += 2 * math.pi
        while self.current_angle >= 2 * math.pi:
            self.current_angle -= 2 * math.pi

        # Convert angle to orientation (0-7)
        # Offset by 22.5 degrees to center bins on the orientation values
        normalized_angle = self.current_angle + math.pi / 8
        new_orientation = int((normalized_angle / (2 * math.pi)) * 8) % 8

        # Return orientation if it changed
        if new_orientation != self.orientation:
            self.orientation = new_orientation
            return new_orientation

        return None
