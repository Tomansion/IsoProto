import uuid
from typing import Dict, Optional, List
from models.player import Player
from datetime import datetime


class Game:
    def __init__(
        self,
        name: str,
        id: str = None,
        creator_id: str = None,
        created_at: str = None,
    ):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.creator_id = creator_id
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.players: List[Player] = []
        self.nb_players = 0

    def to_dict(self) -> Dict:
        """Convert the Game object to a dictionary for storage."""
        return {
            "id": self.id,
            "name": self.name,
            "creator_id": self.creator_id,
            "created_at": self.created_at,
            "nb_players": self.nb_players,
            "players": [p.to_dict() for p in self.players],
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
        game.players = [
            Player.from_dict(p) for p in data.get("players", [])
        ]
        return game