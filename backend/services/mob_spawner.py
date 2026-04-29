"""Mob spawning system for progressive wave-based spawning."""

import random
from typing import List, Dict, Optional


class MobSpawner:
    """Manages progressive mob spawning in waves from map borders."""

    def __init__(self, map_obj, spawn_config: Dict):
        """Initialize the spawner with a map and spawn configuration.

        Args:
            map_obj: The game map object with width, height, tiles, elevation
            spawn_config: Dictionary containing:
                - initial_wave_size: Number of mobs in first wave
                - wave_increment: Additional mobs per subsequent wave
                - wave_delay_ticks: Game ticks between starting waves
                - spawn_rate_ticks: Game ticks between individual mob spawns
                - max_mobs: Maximum concurrent mobs on the map
                - border_distance: Distance from edge to spawn position
                - spawn_spread: Random offset along the edge (±N)
                - total_waves: Total number of waves to spawn
        """
        self.map = map_obj
        self.config = spawn_config
        
        self.current_wave = 0
        self.ticks_since_last_wave = 0
        self.is_complete = False

        # Active spawning sequence state
        # Format: {"edge": str, "base_x": int, "base_y": int, "mobs_to_spawn": int, "mobs_spawned": int, "ticks_since_last_spawn": int}
        self.active_sequence: Optional[Dict] = None

    def should_start_wave(self) -> bool:
        """Check if the next wave should start.

        Returns:
            True if enough ticks have passed and we haven't hit total_waves limit
        """
        if self.is_complete or self.active_sequence is not None:
            return False

        if self.current_wave >= self.config["total_waves"]:
            self.is_complete = True
            return False

        # First wave starts immediately
        if self.current_wave == 0:
            return True

        return self.ticks_since_last_wave >= self.config["wave_delay_ticks"]

    def get_wave_size(self) -> int:
        """Calculate the number of mobs to spawn in the current wave.

        Returns:
            Number of mobs for this wave
        """
        return (
            self.config["initial_wave_size"]
            + (self.current_wave * self.config["wave_increment"])
        )

    def get_border_spawn_point(self) -> tuple:
        """Get a random spawn point on the map border with edge info.

        Returns:
            Tuple of (edge, base_x, base_y) where edge is "top", "bottom", "left", or "right"
        """
        border_dist = self.config["border_distance"]
        width = self.map.width
        height = self.map.height

        # Choose a random edge
        edge = random.choice(["top", "bottom", "left", "right"])

        if edge == "top":
            x = random.randint(border_dist, width - 1 - border_dist)
            y = border_dist
        elif edge == "bottom":
            x = random.randint(border_dist, width - 1 - border_dist)
            y = height - 1 - border_dist
        elif edge == "left":
            x = border_dist
            y = random.randint(border_dist, height - 1 - border_dist)
        else:  # right
            x = width - 1 - border_dist
            y = random.randint(border_dist, height - 1 - border_dist)

        return (edge, x, y)

    def is_valid_spawn_position(self, x: int, y: int) -> bool:
        """Check if a position is valid for spawning.

        A valid spawn position must:
        - Be within map bounds
        - Not be a tree or water
        - Be on land (elevation > 0)

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            True if the position is valid for spawning
        """
        if x < 0 or x >= self.map.width or y < 0 or y >= self.map.height:
            return False

        # Check if it's a tree
        if self.map.tiles[y][x] == 1:  # TILE_TREE
            return False

        # Check if it's water (elevation <= 0)
        if self.map.elevation[y][x] <= 0:
            return False

        return True

    def get_sequence_spawn_position(self, edge: str, base_x: int, base_y: int) -> Optional[tuple]:
        """Get a valid spawn position for the active sequence.

        Applies random spread along the edge direction:
        - For top/bottom edges: spread is applied to X coordinate
        - For left/right edges: spread is applied to Y coordinate

        Args:
            edge: "top", "bottom", "left", or "right"
            base_x: X coordinate of the base spawn point
            base_y: Y coordinate of the base spawn point

        Returns:
            Tuple of (x, y) if valid position found, None otherwise
        """
        spread = self.config["spawn_spread"]

        for _ in range(10):  # Try up to 10 times to find valid position
            if edge == "top" or edge == "bottom":
                # Spread along X axis for top/bottom edges
                offset_x = random.randint(-spread, spread)
                x = base_x + offset_x
                y = base_y
            else:  # left or right
                # Spread along Y axis for left/right edges
                x = base_x
                offset_y = random.randint(-spread, spread)
                y = base_y + offset_y

            if self.is_valid_spawn_position(x, y):
                return (x, y)

        return None

    def start_spawn_sequence(self) -> None:
        """Start a new spawning sequence for the current wave."""
        if not self.should_start_wave():
            return

        edge, base_x, base_y = self.get_border_spawn_point()
        wave_size = self.get_wave_size()

        self.active_sequence = {
            "edge": edge,
            "base_x": base_x,
            "base_y": base_y,
            "mobs_to_spawn": wave_size,
            "mobs_spawned": 0,
            "ticks_since_last_spawn": 0,
        }

    def tick(self) -> List[tuple]:
        """Update spawner state and return new spawn positions for this tick.

        Returns:
            List of (x, y) spawn positions for mobs to spawn this tick
        """
        self.ticks_since_last_wave += 1

        # Start a new sequence if needed
        if self.should_start_wave():
            self.start_spawn_sequence()

        # Process active spawning sequence
        positions = []
        if self.active_sequence:
            positions = self._tick_active_sequence()

        return positions

    def _tick_active_sequence(self) -> List[tuple]:
        """Process the active spawning sequence.

        Returns:
            List of spawn positions for this tick (0 or 1 position)
        """
        if not self.active_sequence:
            return []

        seq = self.active_sequence
        spawn_rate = self.config["spawn_rate_ticks"]
        positions = []

        seq["ticks_since_last_spawn"] += 1

        # Check if it's time to spawn the next mob
        if seq["ticks_since_last_spawn"] >= spawn_rate:
            if seq["mobs_spawned"] < seq["mobs_to_spawn"]:
                pos = self.get_sequence_spawn_position(
                    seq["edge"], seq["base_x"], seq["base_y"]
                )
                if pos:
                    positions.append(pos)
                    seq["mobs_spawned"] += 1

                seq["ticks_since_last_spawn"] = 0

            # Check if sequence is complete
            if seq["mobs_spawned"] >= seq["mobs_to_spawn"]:
                self.current_wave += 1
                self.ticks_since_last_wave = 0
                self.active_sequence = None

        return positions

    def can_spawn_more(self, current_mob_count: int) -> bool:
        """Check if more mobs can be spawned based on max_mobs limit.

        Args:
            current_mob_count: Current number of mobs on the map

        Returns:
            True if we haven't reached the max_mobs limit
        """
        return current_mob_count < self.config["max_mobs"]
