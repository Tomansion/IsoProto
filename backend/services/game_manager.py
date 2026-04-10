from typing import Dict, Optional, List, Set
from models.game import Game
from models.player import Player


class GameManager:
    """Manages active game sessions and player connections."""

    def __init__(self):
        self.active_games: Dict[str, Game] = {}  # game_id -> Game
        self.player_connections: Dict[str, Set[str]] = {}  # player_id -> Set[game_ids]
        self.game_ws_connections: Dict[str, List] = {}  # game_id -> List[WebSocket]

    def add_player_to_game(self, game_id: str, player: Player) -> None:
        """Add a player to a game."""
        if game_id not in self.active_games:
            raise ValueError(f"Game {game_id} not found")

        game = self.active_games[game_id]
        if player not in game.players:
            game.players.append(player)
            game.nb_players = len(game.players)

        if player.id not in self.player_connections:
            self.player_connections[player.id] = set()
        self.player_connections[player.id].add(game_id)

    def remove_player_from_game(self, game_id: str, player_id: str) -> None:
        """Remove a player from a game."""
        if game_id not in self.active_games:
            return

        game = self.active_games[game_id]
        game.players = [p for p in game.players if p.id != player_id]
        game.nb_players = len(game.players)

        if player_id in self.player_connections:
            self.player_connections[player_id].discard(game_id)

    def create_active_game(self, game: Game) -> None:
        """Register a game as active."""
        self.active_games[game.id] = game
        self.game_ws_connections[game.id] = []

    def get_active_game(self, game_id: str) -> Optional[Game]:
        """Get an active game."""
        return self.active_games.get(game_id)

    def is_game_active(self, game_id: str) -> bool:
        """Check if a game is active."""
        return game_id in self.active_games

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


# Global game manager instance
game_manager = GameManager()
