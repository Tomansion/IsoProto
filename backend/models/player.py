import uuid
from typing import Dict
from config import CURRENCY_CONFIG


class Player:
    """Represents a player in a game."""

    def __init__(self, username: str, id: str = None, wallet: int = None):
        self.id = id or str(uuid.uuid4())
        self.username = username
        self.wallet = CURRENCY_CONFIG["starting_amount"] if wallet is None else wallet

    def to_dict(self) -> Dict:
        """Convert the Player object to a dictionary for storage."""
        return {
            "id": self.id,
            "username": self.username,
            "wallet": self.wallet,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Player":
        """Create a Player object from a dictionary."""
        return cls(
            username=data["username"],
            id=data.get("id"),
            wallet=data.get("wallet"),
        )

    def __repr__(self):
        return f"Player(id={self.id}, username={self.username})"
