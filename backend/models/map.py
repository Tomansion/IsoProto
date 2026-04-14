"""Map model for game maps."""

import uuid
from config import MAP_SIZE, MAP_CENTER, BASE_RADIUS
from services.map_generator import MapGenerator
from typing import List


class Building:
    """Represents a building placed on the map."""

    def __init__(
        self, x: int, y: int, building_id: int = 0, elevation: float = 0, id: str = None
    ):
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

        self._generate_map()
        self._place_buildings()

    def _generate_map(self) -> None:
        """Generate map using MapGenerator service."""
        generator = MapGenerator(self.width, self.height, self.seed)
        self.tiles, self.elevation = generator.generate()

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
        map_obj.elevation = data.get(
            "elevation", []
        )  # Handle old data without elevation
        map_obj.buildings = [Building.from_dict(b) for b in data.get("buildings", [])]
        return map_obj
