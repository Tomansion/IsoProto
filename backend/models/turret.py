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
        turret_type: str = "basic",
        range: float = 20.0,
        rotation_speed: float = 0.5,  # Rotations per tick (0-1 = partial, >1 = multiple per tick)
        damage: int = 30,
        fire_cooldown: int = 10,
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
        # Load config from TURRET_TYPE_CONFIG if available
        from config import TURRET_TYPE_CONFIG

        turret_config = TURRET_TYPE_CONFIG.get(turret_type, {})

        self.turret_type = turret_type
        self.target_mob_id: Optional[str] = None
        self.range = range or turret_config.get(
            "range", 20.0
        )  # Maximum targeting distance
        self.rotation_speed = rotation_speed or turret_config.get("rotation_speed", 0.5)
        self.damage = damage or turret_config.get("damage", 30)  # Damage per shot
        self.fire_cooldown = fire_cooldown or turret_config.get(
            "fire_cooldown", 10
        )  # Ticks between shots
        self.current_angle = orientation * (2 * math.pi / 8)  # Current angle in radians
        self.idle_duration = 60  # Ticks before choosing new idle direction
        self.idle_timer = self.idle_duration  # Counter for idle rotation
        self.idle_target_angle = None  # Target angle when idle
        self.last_shot_tick = 0  # Track when last shot was fired

    def update_target(self, mobs: List, current_tick: int = 0) -> tuple:
        """Update turret to target the closest mob within range, rotate toward it, and fire if aimed.

        Args:
            mobs: List of mobs to target
            current_tick: Current game tick (for firing cooldown)

        Returns:
            Tuple of (new_orientation or None, shot_event or None)
            - new_orientation: (0-7) if orientation changed, or None
            - shot_event: Dict with shot data if fired, or None
        """
        if not mobs:
            self.target_mob_id = None
            # Start idle rotation if no target
            orientation_changed = self._update_idle_rotation()
            return (orientation_changed, None)

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
            orientation_changed = self._update_idle_rotation()
            return (orientation_changed, None)

        self.target_mob_id = closest_mob.id
        self.idle_timer = 0
        self.idle_target_angle = None

        # Calculate target angle from turret to mob
        dx = closest_mob.x - self.x
        dy = closest_mob.y - self.y
        target_angle = math.atan2(dy, dx)  # In radians

        # Smooth rotation toward target angle
        orientation_changed = self._rotate_toward_angle(target_angle)

        # Check if aimed and fire if off cooldown
        shot_event = None
        if (
            self._is_aimed_at_target(target_angle)
            and current_tick - self.last_shot_tick >= self.fire_cooldown
        ):
            shot_event = self._fire(closest_mob, current_tick)

        return (orientation_changed, shot_event)

    def _is_aimed_at_target(self, target_angle: float) -> bool:
        """Check if current angle is within tolerance of target angle.

        Tolerance is 22.5 degrees (π/8 radians) = one orientation bin.
        This means the turret fires when rotated to face the target orientation.
        """
        # Normalize angles to [0, 2π)
        while target_angle < 0:
            target_angle += 2 * math.pi
        while target_angle >= 2 * math.pi:
            target_angle -= 2 * math.pi

        current = self.current_angle
        while current < 0:
            current += 2 * math.pi
        while current >= 2 * math.pi:
            current -= 2 * math.pi

        # Calculate difference
        diff = target_angle - current
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi

        # Tolerance is one orientation bin (π/8 radians)
        aim_tolerance = math.pi / 8
        return abs(diff) <= aim_tolerance

    def _fire(self, target_mob, current_tick: int) -> dict:
        """Fire at target mob, dealing damage.

        Args:
            target_mob: Mob to shoot
            current_tick: Current game tick

        Returns:
            Shot event dict {turret_id, mob_id, turret_x, turret_y, orientation, damage}
        """
        self.last_shot_tick = current_tick

        # Deal damage to mob
        target_mob.hp -= self.damage

        return {
            "turret_id": self.id,
            "turret_x": self.x,
            "turret_y": self.y,
            "orientation": self.orientation,
            "mob_id": target_mob.id,
            "damage": self.damage,
        }

    def _update_idle_rotation(self) -> Optional[int]:
        """Update idle rotation timer and pick random direction when needed.

        Returns the new orientation (0-7) if it changed, None otherwise.
        """
        self.idle_timer += 1
        if self.idle_timer >= self.idle_duration:
            # Pick a random direction
            import random

            random_orientation = random.randint(0, 7)
            self.idle_target_angle = random_orientation * (2 * math.pi / 8)
            self.idle_timer = 0 + random.randint(
                0, self.idle_duration
            )  # Add some randomness to next idle duration

        if (
            self.idle_target_angle is not None
            and self.current_angle != self.idle_target_angle
        ):
            return self._rotate_toward_angle(self.idle_target_angle)

        return None

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
