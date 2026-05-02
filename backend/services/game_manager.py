from typing import Dict, Optional, List, Set
import random
from models.game import Game
from models.player import Player
from models.turret import Turret
from models.mob import Zombie
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

    # Mob management
    def tick_mobs(self, game_id: str) -> list:
        """Move all mobs one tick toward their target.

        Updates blocked tiles from turrets, moves mobs along their paths.
        Removes mobs that have reached their target.
        Updates each mob's elevation from the current map tile.
        Returns list of mob dicts for WS broadcasting.
        """
        game = self.games.get(game_id)
        if not game:
            return []

        alive_mobs = []
        for mob in game.mobs:
            reached = mob.move_toward_target()
            if not reached:
                # Update elevation based on current map tile
                tx = max(0, min(game.map.width - 1, int(mob.x)))
                ty = max(0, min(game.map.height - 1, int(mob.y)))
                mob.elevation = game.map.elevation[ty][tx]
                alive_mobs.append(mob)

        game.mobs = alive_mobs
        return [m.to_dict() for m in game.mobs]

    # Turret management
    def add_turret_to_game(
        self, game_id: str, player_id: str, x: int, y: int
    ) -> Optional[Turret]:
        """Add a turret to a game map at the given coordinates.

        Validates placement: tile must be empty (no trees/buildings) and not water.
        Sets orientation based on closest mob position.
        
        Optimizes pathfinding: only invalidates paths affected by new blocked tiles.

        Returns the created turret Turret object or None if validation fails.
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
        turret = Turret(
            x=x,
            y=y,
            building_id=0,  # Turret base frame
            player_id=player_id,
            orientation=orientation,
        )

        # Set correct orientation based on closest mob
        turret.update_target(game.mobs)

        map_obj.buildings.append(turret)

        # Update blocked tiles and track newly blocked ones
        game.pathfinding.update_blocked_tiles(game.map.buildings)

        # Only invalidate paths affected by newly blocked tiles
        for mob in game.mobs:
            cached_path = game.pathfinding.pathfinder.path_cache.get(mob.id, [])
            if cached_path:
                game.pathfinding.invalidate_affected_paths(
                    mob.x, mob.y, mob.id, cached_path
                )

        return turret

    def tick_turrets(self, game_id: str) -> list:
        """Update all turrets to track closest mobs.

        Returns list of turret rotation updates [{id, orientation}, ...]
        for only turrets that changed orientation.
        """
        game = self.games.get(game_id)
        if not game:
            return []

        rotations = []
        for building in game.map.buildings:
            # Only update turrets
            if isinstance(building, Turret):
                new_orientation = building.update_target(game.mobs)
                if new_orientation is not None:
                    rotations.append(
                        {
                            "id": building.id,
                            "orientation": new_orientation,
                        }
                    )

        return rotations

    def spawn_mobs(self, game_id: str) -> list:
        """Process mob spawning based on spawner waves.

        The spawner manages wave timing and spawn sequencing internally.
        This method creates Zombie objects at spawn positions returned by the spawner.
        Returns list of newly spawned mob dicts for WS broadcasting.
        """
        game = self.games.get(game_id)
        if not game:
            return []

        spawner = game.mob_spawner

        # Check if we can spawn more mobs (respects max_mobs limit)
        if not spawner.can_spawn_more(len(game.mobs)):
            return []

        # Tick the spawner - it returns spawn positions for this tick
        spawn_positions = spawner.tick()
        if not spawn_positions:
            return []

        # Create Zombie objects at each spawn position
        new_mobs = []
        for x, y in spawn_positions:
            elevation = game.map.elevation[y][x]
            zombie = Zombie(
                x=float(x),
                y=float(y),
                target_x=game.map.width / 2,
                target_y=game.map.height / 2,
                elevation=elevation,
                pathfinding_manager=game.pathfinding,
                map_obj=game.map,
            )
            game.mobs.append(zombie)
            new_mobs.append(zombie)

        return [m.to_dict() for m in new_mobs]


game_manager = GameManager()
