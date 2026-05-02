import uuid
import random
from typing import Dict, Optional, List
from models.player import Player
from models.map import Map
from models.mob import Zombie
from services.mob_spawner import MobSpawner
from services.pathfinding_manager import PathfindingManager
from config import MOB_SPAWN_CONFIG
from datetime import datetime


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
        
        # Initialize mob spawner for progressive wave-based spawning
        self.mob_spawner = MobSpawner(self.map, MOB_SPAWN_CONFIG)
        
        # Initialize pathfinding manager for weighted flow-field pathfinding
        self.pathfinding = PathfindingManager(self.map)

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
