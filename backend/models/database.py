from pathlib import Path
from typing import List, Optional
from models.game import Game
from tinydb import TinyDB, Query


class GameDatabase:
    """Database utility for saving and loading games using TinyDB."""

    def __init__(self, db_folder: str = "data"):
        """
        Initialize the game database.

        Args:
            db_folder: Path to the folder where the database will be stored
        """
        self.db_folder = Path(db_folder)
        self.db_folder.mkdir(parents=True, exist_ok=True)

        # Initialize TinyDB with the database file
        self.db = TinyDB(self.db_folder / "games.json")

    def save_game(self, game_obj: Game) -> Game:
        """
        Save a game to the database.

        Args:
            game_obj: The Game object to save

        Returns:
            The saved Game object

        Raises:
            ValueError: If game already exists with the same ID
        """
        Game_query = Query()
        existing = self.db.search(Game_query.id == game_obj.id)

        if existing:
            raise ValueError(f"Game with ID '{game_obj.id}' already exists")

        # Insert the game data
        self.db.insert(game_obj.to_dict())
        return game_obj

    def update_game(self, game_obj: Game) -> Game:
        """
        Update a game in the database.

        Args:
            game_obj: The Game object to update

        Returns:
            The updated Game object
        """
        Game_query = Query()
        self.db.update(game_obj.to_dict(), Game_query.id == game_obj.id)
        return game_obj

    def get_game(self, game_id: str) -> Optional[Game]:
        """
        Load a game from the database.

        Args:
            game_id: The ID of the game to load

        Returns:
            The loaded Game object, or None if not found
        """
        Game_query = Query()
        result = self.db.search(Game_query.id == game_id)

        if not result:
            return None

        return Game.from_dict(result[0])

    def get_all_games(self) -> List[Game]:
        """
        Load all games from the database.

        Returns:
            A list of all Game objects in the database, sorted by creation date
        """
        all_records = self.db.all()
        games = [Game.from_dict(record) for record in all_records]
        return sorted(games, key=lambda g: g.created_at, reverse=True)

    def delete_game(self, game_id: str) -> bool:
        """
        Delete a game from the database.

        Args:
            game_id: The ID of the game to delete

        Returns:
            True if the game was deleted, False if it didn't exist
        """
        Game_query = Query()
        removed = self.db.remove(Game_query.id == game_id)
        return len(removed) > 0
