from typing import Dict, Optional, List, Set, cast
import uuid
import random
from models.game import Game
from models.player import Player
from models.map import Building
from models.turret import Turret
from models.mob import Zombie
from config import BUILDING_TYPE_CONFIG


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
    def tick_mobs(self, game_id: str) -> tuple:
        """Move all mobs one tick toward their target.

        Updates blocked tiles from turrets, moves mobs along their paths.
        Removes mobs that have reached their target or died.
        Updates each mob's elevation from the current map tile.

        Returns:
            Tuple of (mob_list, dead_mob_ids)
            - mob_list: list of mob dicts for WS broadcasting
            - dead_mob_ids: list of IDs of mobs that died this tick (for frontend feedback)
        """
        game = self.games.get(game_id)
        if not game:
            return ([], [])

        alive_mobs = []
        dead_mob_ids = []

        for mob in game.mobs:
            reached = mob.move_toward_target()
            if reached:
                # Mob removed (reached target or died)
                if mob.hp <= 0:
                    dead_mob_ids.append(mob.id)
            else:
                # Update elevation based on current map tile
                tx = max(0, min(game.map.width - 1, round(mob.x)))
                ty = max(0, min(game.map.height - 1, round(mob.y)))
                mob.elevation = game.map.elevation[ty][tx]
                alive_mobs.append(mob)

        game.mobs = alive_mobs
        return ([m.to_dict() for m in game.mobs], dead_mob_ids)

    # Turret management
    def _get_building_tiles(
        self, game: Game, x: int, y: int, building_type: str
    ) -> List[tuple[int, int]]:
        """Return all tile coordinates occupied by a building."""
        building_config = BUILDING_TYPE_CONFIG.get(building_type)
        if not building_config:
            return []

        footprint_radius = building_config.get("footprint_radius", 0)
        tiles = []
        for dx in range(-footprint_radius, footprint_radius + 1):
            for dy in range(-footprint_radius, footprint_radius + 1):
                tiles.append((x + dx, y + dy))
        return tiles

    def _get_existing_building_tiles(
        self, game: Game, building
    ) -> set[tuple[int, int]]:
        """Return all occupied tiles for an existing building instance."""
        return set(
            self._get_building_tiles(
                game, building.x, building.y, building.building_type
            )
        )

    def can_place_building(
        self,
        game_id: str,
        x: int,
        y: int,
        building_type: str,
        ignore_pending_id: Optional[str] = None,
    ) -> bool:
        """Validate whether a building can be placed or queued on a tile."""
        game = self.games.get(game_id)
        if not game:
            return False

        building_tiles = self._get_building_tiles(game, x, y, building_type)
        if not building_tiles:
            return False

        map_obj = game.map

        for tile_x, tile_y in building_tiles:
            if (
                tile_x < 0
                or tile_y < 0
                or tile_x >= map_obj.width
                or tile_y >= map_obj.height
            ):
                return False

            if map_obj.elevation[tile_y][tile_x] <= 0:
                return False

        requested_tiles = set(building_tiles)

        for building in map_obj.buildings:
            if requested_tiles & self._get_existing_building_tiles(game, building):
                return False

        for pending_building in game.pending_buildings:
            if pending_building["id"] == ignore_pending_id:
                continue
            pending_tiles = set(
                self._get_building_tiles(
                    game,
                    pending_building["x"],
                    pending_building["y"],
                    pending_building["building_type"],
                )
            )
            if requested_tiles & pending_tiles:
                return False

        return True

    def can_place_turret(self, game_id: str, x: int, y: int) -> bool:
        """Validate whether a turret can be placed or queued on a tile."""
        return self.can_place_building(game_id, x, y, "turret")

    def queue_building_build(
        self, game_id: str, player_id: str, x: int, y: int, building_type: str
    ) -> Optional[dict]:
        """Queue a building build and return the pending payload."""
        game = self.games.get(game_id)
        building_config = BUILDING_TYPE_CONFIG.get(building_type)
        if not game or not building_config:
            return None

        if not self.can_place_building(game_id, x, y, building_type):
            return None

        cooldown_ticks = building_config["build_cooldown_ticks"]
        pending_building = {
            "id": str(uuid.uuid4()),
            "x": x,
            "y": y,
            "elevation": game.map.elevation[y][x],
            "player_id": player_id,
            "building_type": building_type,
            "building_id": building_config.get("building_id", 0),
            "started_at_tick": game.current_tick,
            "complete_at_tick": game.current_tick + cooldown_ticks,
            "cooldown_ticks": cooldown_ticks,
            "cooldown_ms": int(cooldown_ticks * 100),
        }
        game.pending_buildings.append(pending_building)
        return pending_building

    def queue_turret_build(
        self,
        game_id: str,
        player_id: str,
        x: int,
        y: int,
        cooldown_ticks: Optional[int] = None,
    ) -> Optional[dict]:
        """Queue a turret build and return the pending placement payload."""
        resolved_cooldown_ticks = cooldown_ticks
        if resolved_cooldown_ticks is None:
            resolved_cooldown_ticks = int(
                BUILDING_TYPE_CONFIG["turret"]["build_cooldown_ticks"]
            )

        pending_building = self.queue_building_build(game_id, player_id, x, y, "turret")
        if pending_building:
            pending_building["cooldown_ticks"] = resolved_cooldown_ticks
            pending_building["complete_at_tick"] = (
                self.games[game_id].current_tick + resolved_cooldown_ticks
            )
            pending_building["cooldown_ms"] = int(resolved_cooldown_ticks * 100)
        return pending_building

    def _create_building(
        self,
        game: Game,
        player_id: str,
        x: int,
        y: int,
        building_type: str,
        id: Optional[str] = None,
    ) -> Building:
        """Create and register a building in a game without placement validation."""
        building_config = BUILDING_TYPE_CONFIG.get(building_type, {})

        if building_type == "turret":
            orientation = random.randint(0, 7)
            building = Turret(
                x=x,
                y=y,
                building_id=building_config.get("building_id", 0),
                player_id=player_id,
                orientation=orientation,
                targetable_environments=building_config.get(
                    "targetable_environments"
                ),
                id=id,
            )
            building.update_target(game.mobs, game.current_tick)
        else:
            building = Building(
                x=x,
                y=y,
                building_id=building_config.get("building_id", 0),
                player_id=player_id,
                building_type=building_type,
                id=id,
            )

        game.map.buildings.append(building)

        game.pathfinding.update_blocked_tiles(game.map.buildings)

        for mob in game.mobs:
            cached_path = game.pathfinding.pathfinder.path_cache.get(mob.id, [])
            if cached_path:
                game.pathfinding.invalidate_affected_paths(
                    mob.x, mob.y, mob.id, cached_path
                )

        return building

    def _create_turret(
        self,
        game: Game,
        player_id: str,
        x: int,
        y: int,
        id: Optional[str] = None,
    ) -> Turret:
        """Create and register a turret in a game without placement validation."""
        return cast(
            Turret,
            self._create_building(game, player_id, x, y, "turret", id=id),
        )

    def _kill_mobs_on_tiles(
        self, game: Game, building_tiles: List[tuple[int, int]]
    ) -> List[str]:
        """Kill mobs standing on the provided tiles and return their ids."""
        occupied_tiles = set(building_tiles)
        surviving_mobs = []
        dead_mob_ids = []

        for mob in game.mobs:
            mob_tile = (round(mob.x), round(mob.y))
            if mob_tile in occupied_tiles:
                mob.hp = 0
                if mob.pathfinding_manager:
                    mob.pathfinding_manager.reached_target(mob.id)
                dead_mob_ids.append(mob.id)
                continue

            surviving_mobs.append(mob)

        game.mobs = surviving_mobs
        return dead_mob_ids

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

        if not self.can_place_building(game_id, x, y, "turret"):
            return None

        return self._create_turret(game, player_id, x, y)

    def process_pending_buildings(
        self, game_id: str
    ) -> tuple[list, List[dict], List[str]]:
        """Finalize pending building builds whose cooldown has completed."""
        game = self.games.get(game_id)
        if not game or not game.pending_buildings:
            return ([], [], [])

        ready_buildings = []
        changed_tiles = []
        dead_mob_ids = []
        still_pending = []

        for pending_building in game.pending_buildings:
            if game.current_tick < pending_building["complete_at_tick"]:
                still_pending.append(pending_building)
                continue

            if not self.can_place_building(
                game_id,
                pending_building["x"],
                pending_building["y"],
                pending_building["building_type"],
                ignore_pending_id=pending_building["id"],
            ):
                continue

            building_tiles = self._get_building_tiles(
                game,
                pending_building["x"],
                pending_building["y"],
                pending_building["building_type"],
            )
            changed_tiles.extend(game.map.clear_trees_at_tiles(building_tiles))
            dead_mob_ids.extend(self._kill_mobs_on_tiles(game, building_tiles))

            building = self._create_building(
                game,
                pending_building["player_id"],
                pending_building["x"],
                pending_building["y"],
                pending_building["building_type"],
                id=pending_building["id"],
            )
            ready_buildings.append(building.to_dict())

        game.pending_buildings = still_pending
        return (ready_buildings, changed_tiles, dead_mob_ids)

    def process_pending_turrets(self, game_id: str) -> list:
        """Backward-compatible wrapper for pending turret processing."""
        ready_buildings, _, _ = self.process_pending_buildings(game_id)
        return ready_buildings

    def tick_turrets(self, game_id: str) -> tuple:
        """Update all turrets to track closest mobs and fire when ready.

        Returns tuple of (rotations, shots) where:
        - rotations: list of turret rotation updates [{id, orientation}, ...]
        - shots: list of shot events [{turret_id, turret_x, turret_y, orientation, mob_id, damage}, ...]
        """
        game = self.games.get(game_id)
        if not game:
            return ([], [])

        rotations = []
        shots = []

        for building in game.map.buildings:
            # Only update turrets
            if isinstance(building, Turret):
                orientation_changed, shot_event = building.update_target(
                    game.mobs, game.current_tick
                )

                if orientation_changed is not None:
                    rotations.append(
                        {
                            "id": building.id,
                            "orientation": orientation_changed,
                        }
                    )

                if shot_event is not None:
                    shots.append(shot_event)

        return (rotations, shots)

    def tick_game(self, game_id: str) -> None:
        """Increment game tick counter."""
        game = self.games.get(game_id)
        if game:
            game.current_tick += 1

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
