"""Map model for game maps."""

from perlin_noise import PerlinNoise
import uuid
from config import (
    MAP_SIZE, MAP_CENTER, BASE_RADIUS, PERLIN_SCALE, PERLIN_FREQUENCY,
    PERLIN_OCTAVES, PERLIN_PERSISTENCE, PERLIN_LACUNARITY, PERLIN_TREE_THRESHOLD,
    ELEVATION_SCALE, ELEVATION_OCTAVES, ELEVATION_PERSISTENCE, ELEVATION_LACUNARITY,
    ELEVATION_MIN, ELEVATION_MAX,
    TILE_EMPTY, TILE_TREE
)
from typing import List


class Building:
    """Represents a building placed on the map."""
    
    def __init__(self, x: int, y: int, building_id: int = 0, elevation: float = 0, id: str = None):
        self.id = id or str(uuid.uuid4())
        self.x = x
        self.y = y
        self.building_id = building_id  # Index into tileset
    
    def to_dict(self) -> dict:
        """Convert building to dictionary for serialization."""
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "building_id": self.building_id,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Building":
        """Create a Building from dictionary."""
        return cls(
            x=data["x"],
            y=data["y"],
            building_id=data.get("building_id", 0),
            id=data.get("id"),
        )


class Map:
    """Represents a game map with tiles (trees, empty ground, etc)."""

    def __init__(self, width: int = MAP_SIZE, height: int = MAP_SIZE, seed: int = 0):
        self.width = width
        self.height = height
        self.seed = seed
        self.tiles: List[List[int]] = []
        self.elevation: List[List[float]] = []
        self.buildings: List[Building] = []
        
        # Initialize Perlin noise generators
        # Note: perlin-noise library handles persistence and lacunarity internally
        self.tree_noise = PerlinNoise(
            octaves=PERLIN_OCTAVES,
            seed=seed
        )
        self.elevation_noise = PerlinNoise(
            octaves=ELEVATION_OCTAVES,
            seed=seed + 100
        )
        
        self._generate_map()
        self._place_buildings()

    def _generate_map(self) -> None:
        """Generate map using Perlin noise."""
        self.tiles = []
        self.elevation = []
        
        for y in range(self.height):
            row = []
            elevation_row = []
            for x in range(self.width):
                # Generate Perlin noise value for trees
                noise_value = self.tree_noise([x / PERLIN_SCALE, y / PERLIN_SCALE])
                
                # Normalize noise value to 0-1 range
                normalized_value = (noise_value + 1) / 2
                
                # Generate elevation using separate Perlin noise
                elevation_value_raw = self.elevation_noise(
                    [x / ELEVATION_SCALE, y / ELEVATION_SCALE]
                )
                
                # Normalize elevation to desired range
                normalized_elevation = (elevation_value_raw + 1) / 2
                elevation_value = ELEVATION_MIN + normalized_elevation * (ELEVATION_MAX - ELEVATION_MIN)
                
                # Check if this is in the center clear zone (base area)
                distance_from_center = ((x - MAP_CENTER) ** 2 + (y - MAP_CENTER) ** 2) ** 0.5
                if distance_from_center <= BASE_RADIUS:
                    # Clear area for base - use natural elevation but no trees
                    tile = TILE_EMPTY
                else:
                    # Use noise threshold for trees
                    tile = TILE_TREE if normalized_value > PERLIN_TREE_THRESHOLD else TILE_EMPTY
                
                row.append(tile)
                elevation_row.append(round(elevation_value/2, 0)*2)
            self.tiles.append(row)
            self.elevation.append(elevation_row)

    def _place_buildings(self) -> None:
        """Place base building at the center of the map."""
        base_building = Building(x=MAP_CENTER, y=MAP_CENTER, building_id=0)
        self.buildings.append(base_building)

    def to_dict(self) -> dict:
        """Convert map to dictionary for serialization."""
        return {
            "width": self.width,
            "height": self.height,
            "tiles": self.tiles,
            "elevation": self.elevation,
            "buildings": [b.to_dict() for b in self.buildings],
            "center": {"x": MAP_CENTER, "y": MAP_CENTER},
            "base_radius": BASE_RADIUS,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Map":
        """Create a Map from dictionary (for loading from storage)."""
        map_obj = cls(data["width"], data["height"])
        map_obj.tiles = data["tiles"]
        map_obj.elevation = data.get("elevation", [])  # Handle old data without elevation
        map_obj.buildings = [
            Building.from_dict(b) for b in data.get("buildings", [])
        ]
        return map_obj
