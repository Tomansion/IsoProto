"""Map generation service using Perlin noise."""

import random

from perlin_noise import PerlinNoise
from config import (
    MAP_SIZE,
    MAP_CENTER,
    BASE_RADIUS,
    PERLIN_SCALE,
    PERLIN_OCTAVES,
    PERLIN_TREE_THRESHOLD,
    ELEVATION_SCALE,
    ELEVATION_OCTAVES,
    ELEVATION_MIN,
    ELEVATION_MAX,
    TILE_EMPTY,
    TILE_TREE,
)
from typing import Tuple, List


class MapGenerator:
    """Service for generating game maps using Perlin noise."""

    def __init__(self, width: int = MAP_SIZE, height: int = MAP_SIZE, seed: int = 0):
        self.width = width
        self.height = height
        self.seed = seed

        # Initialize Perlin noise generators
        self.tree_noise = PerlinNoise(octaves=PERLIN_OCTAVES, seed=seed)
        self.elevation_noise = PerlinNoise(octaves=ELEVATION_OCTAVES, seed=seed + 100)

    def generate(self) -> Tuple[List[List[int]], List[List[float]]]:
        """Generate map tiles and elevation.

        Returns:
            Tuple of (tiles, elevation) where tiles is a 2D list of tile types
            and elevation is a 2D list of elevation values.
        """
        tiles = []
        elevation = []

        for y in range(self.height):
            row = []
            elevation_row = []
            for x in range(self.width):
                # Generate elevation using Perlin noise
                elevation_value_raw = self.elevation_noise(
                    [x / ELEVATION_SCALE, y / ELEVATION_SCALE]
                )

                # Normalize elevation to desired range
                normalized_elevation = (elevation_value_raw + 1) / 2
                elevation_value = ELEVATION_MIN + normalized_elevation * (
                    ELEVATION_MAX - ELEVATION_MIN
                )

                # Check if this is in the center clear zone (base area)
                distance_from_center = (
                    (x - MAP_CENTER) ** 2 + (y - MAP_CENTER) ** 2
                ) ** 0.5

                if distance_from_center <= BASE_RADIUS:
                    # Clear area for base - no trees - elevation > 0
                    tile = TILE_EMPTY
                    elevation_value = max(
                        elevation_value, 2
                    )  # Ensure some elevation for base
                else:
                    if normalized_elevation > PERLIN_TREE_THRESHOLD:
                        tile = TILE_TREE
                    elif normalized_elevation > PERLIN_TREE_THRESHOLD - 0.1:
                        diff = normalized_elevation - (PERLIN_TREE_THRESHOLD - 0.1)
                        probability = diff / 0.1
                        if random.random() < probability:
                            tile = TILE_TREE
                        else:
                            tile = TILE_EMPTY
                    else:
                        tile = TILE_EMPTY

                row.append(tile)
                elevation_row.append(round(elevation_value / 2, 0) * 2)

            tiles.append(row)
            elevation.append(elevation_row)

        # Adjust elevation to ensure minimum is 0
        min_elevation = min(min(row) for row in elevation)
        for y in range(self.height):
            for x in range(self.width):
                elevation[y][x] = max(0, elevation[y][x] - min_elevation - 8)

        return tiles, elevation
