import uuid
import random
from typing import Dict, Optional, List
from models.player import Player
from models.map import Map
from models.mob import Zombie
from datetime import datetime

TILE_TREE = 1  # Keep local to avoid circular import
MOB_SPAWN_COUNT = 50


class Game:
    def __init__(
        self,
        name: str,
        id: str = None,
        creator_id: str = None,
        created_at: str = None,
        seed: int = None,
    ):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.creator_id = creator_id
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.players: List[Player] = []
        self.nb_players = 0
        self.mobs: List[Zombie] = []
        if seed is None:
            seed = random.randint(0, 2**31 - 1)
        self.map = Map(seed=seed)
        self._spawn_mobs(MOB_SPAWN_COUNT)

    def _spawn_mobs(self, count: int = 5) -> None:
        """Spawn initial zombies at random valid positions on the map."""
        spawned = 0
        attempts = 0
        while spawned < count and attempts < 2000:
            attempts += 1
            x = random.randint(0, self.map.width - 1)
            y = random.randint(0, self.map.height - 1)

            # Skip tree tiles
            if self.map.tiles[y][x] == TILE_TREE:
                continue

            # Skip water tiles (elevation <= 0)
            elevation = self.map.elevation[y][x]
            if elevation <= 0:
                continue

            zombie = Zombie(
                x=float(x),
                y=float(y),
                target_x=self.map.width / 2,
                target_y=self.map.height / 2,
                elevation=elevation,
            )
            self.mobs.append(zombie)
            spawned += 1

    def to_dict(self) -> Dict:
        """Convert the Game object to a dictionary for storage."""
        return {
            "id": self.id,
            "name": self.name,
            "creator_id": self.creator_id,
            "created_at": self.created_at,
            "nb_players": self.nb_players,
            "players": [p.to_dict() for p in self.players],
            "map": self.map.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Game":
        """Create a Game object from a dictionary."""
        game = cls(
            name=data["name"],
            id=data["id"],
            creator_id=data.get("creator_id"),
            created_at=data.get("created_at"),
        )
        game.nb_players = data.get("nb_players", 0)
        game.players = [Player.from_dict(p) for p in data.get("players", [])]
        if "map" in data:
            game.map = Map.from_dict(data["map"])
        return game
