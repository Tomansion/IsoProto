"""Map model for game maps."""

import numpy as np
from noise import pnoise2
from config import (
    MAP_SIZE, MAP_CENTER, BASE_RADIUS, PERLIN_SCALE, PERLIN_FREQUENCY,
    PERLIN_OCTAVES, PERLIN_PERSISTENCE, PERLIN_LACUNARITY, PERLIN_TREE_THRESHOLD,
    TILE_EMPTY, TILE_TREE
)
from typing import List


class Map:
    """Represents a game map with tiles (trees, empty ground, etc)."""

    def __init__(self, width: int = MAP_SIZE, height: int = MAP_SIZE, seed: int = 0):
        self.width = width
        self.height = height
        self.seed = seed
        self.tiles: List[List[int]] = []
        self._generate_map()

    def _generate_map(self) -> None:
        """Generate map using Perlin noise."""
        self.tiles = []
        
        for y in range(self.height):
            row = []
            for x in range(self.width):
                # Generate Perlin noise value
                noise_value = pnoise2(
                    x / PERLIN_SCALE + self.seed,
                    y / PERLIN_SCALE + self.seed,
                    octaves=PERLIN_OCTAVES,
                    persistence=PERLIN_PERSISTENCE,
                    lacunarity=PERLIN_LACUNARITY,
                    repeatx=MAP_SIZE,
                    repeaty=MAP_SIZE,
                    base=0
                )
                
                # Normalize noise value to 0-1 range
                normalized_value = (noise_value + 1) / 2
                
                # Check if this is in the center clear zone (base area)
                distance_from_center = ((x - MAP_CENTER) ** 2 + (y - MAP_CENTER) ** 2) ** 0.5
                if distance_from_center <= BASE_RADIUS:
                    # Clear area for base
                    tile = TILE_EMPTY
                else:
                    # Use noise threshold for trees
                    tile = TILE_TREE if normalized_value > PERLIN_TREE_THRESHOLD else TILE_EMPTY
                
                row.append(tile)
            self.tiles.append(row)

    def to_dict(self) -> dict:
        """Convert map to dictionary for serialization."""
        return {
            "width": self.width,
            "height": self.height,
            "tiles": self.tiles,
            "center": {"x": MAP_CENTER, "y": MAP_CENTER},
            "base_radius": BASE_RADIUS,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Map":
        """Create a Map from dictionary (for loading from storage)."""
        map_obj = cls(data["width"], data["height"])
        map_obj.tiles = data["tiles"]
        return map_obj
