from typing import Dict, Optional, List, Set
import random
from models.game import Game
from models.player import Player
from models.map import Building
from config import TILE_TREE


class GameManager:
    """Manages all game sessions in RAM (no database)."""

    def __init__(self):
        self.games: Dict[str, Game] = {}  # game_id -> Game (source of truth)
        self.player_connections: Dict[str, Set[str]] = {}  # player_id -> Set[game_ids]
        self.game_ws_connections: Dict[str, List] = {}  # game_id -> List[WebSocket]

    # Game CRUD operations
    def create_game(self, name: str, creator_id: str) -> Game:
        """Create a new game."""
        game = Game(name=name, creator_id=creator_id)
        creator = Player(username=creator_id)
        game.players.append(creator)
        game.nb_players = 1
        self.games[game.id] = game
        self.game_ws_connections[game.id] = []
        return game

    def get_game(self, game_id: str) -> Optional[Game]:
        """Get a game by ID."""
        return self.games.get(game_id)

    def get_all_games(self) -> List[Game]:
        """Get all games, sorted by creation date."""
        return sorted(self.games.values(), key=lambda g: g.created_at, reverse=True)

    def delete_game(self, game_id: str) -> bool:
        """Delete a game."""
        if game_id in self.games:
            del self.games[game_id]
            if game_id in self.game_ws_connections:
                del self.game_ws_connections[game_id]
            return True
        return False

    def update_game(self, game: Game) -> None:
        """Update a game (nb_players sync, etc)."""
        if game.id in self.games:
            self.games[game.id] = game

    # Player management
    def add_player_to_game(self, game_id: str, player: Player) -> None:
        """Add a player to a game."""
        game = self.games.get(game_id)
        if game and player not in game.players:
            game.players.append(player)
            game.nb_players = len(game.players)

        if player.id not in self.player_connections:
            self.player_connections[player.id] = set()
        self.player_connections[player.id].add(game_id)

    def remove_player_from_game(self, game_id: str, player_id: str) -> None:
        """Remove a player from a game."""
        game = self.games.get(game_id)
        if game:
            game.players = [p for p in game.players if p.id != player_id]
            game.nb_players = len(game.players)

        if player_id in self.player_connections:
            self.player_connections[player_id].discard(game_id)

    def is_game_active(self, game_id: str) -> bool:
        """Check if a game exists."""
        return game_id in self.games

    def get_active_game(self, game_id: str) -> Optional[Game]:
        """Get a game (for backward compatibility)."""
        return self.games.get(game_id)

    # WebSocket connection management
    def remove_ws_connection(self, game_id: str, ws) -> None:
        """Remove a WebSocket connection from a game."""
        if game_id in self.game_ws_connections:
            try:
                self.game_ws_connections[game_id].remove(ws)
            except ValueError:
                pass

    def add_ws_connection(self, game_id: str, ws) -> None:
        """Add a WebSocket connection to a game."""
        if game_id not in self.game_ws_connections:
            self.game_ws_connections[game_id] = []
        self.game_ws_connections[game_id].append(ws)

    # Turret management
    def add_turret_to_game(
        self, game_id: str, player_id: str, x: int, y: int
    ) -> Optional[Building]:
        """Add a turret to a game map at the given coordinates.
        
        Validates placement: tile must be empty (no trees/buildings) and not water.
        Assigns random orientation (0-7).
        
        Returns the created turret Building object or None if validation fails.
        """
        game = self.games.get(game_id)
        if not game:
            return None

        map_obj = game.map
        
        # Validate coordinates are within map
        if x < 0 or y < 0 or x >= map_obj.width or y >= map_obj.height:
            return None

        # Validate tile is not water (elevation > 0)
        elevation = map_obj.elevation[y][x]
        if elevation <= 0:
            return None

        # Validate tile has no trees
        tile = map_obj.tiles[y][x]
        if tile == TILE_TREE:
            return None

        # Validate no building already at this location
        if any(b.x == x and b.y == y for b in map_obj.buildings):
            return None

        # All validation passed - create turret with random orientation
        orientation = random.randint(0, 7)
        turret = Building(
            x=x,
            y=y,
            building_id=0,  # Turret base frame
            building_type="turret",
            player_id=player_id,
            orientation=orientation,
        )
        
        map_obj.buildings.append(turret)
        return turret


# Global game manager instance
game_manager = GameManager()
