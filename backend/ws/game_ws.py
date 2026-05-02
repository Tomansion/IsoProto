import asyncio
import json
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from services.game_manager import game_manager
from models.player import Player

router = APIRouter(tags=["game"])


class GameConnectionManager:
    """Manages WebSocket connections for game sessions and lobby."""

    def __init__(self):
        self.game_connections: dict[str, list[WebSocket]] = {}  # game_id -> connections
        self.lobby_connections: list[WebSocket] = []  # All lobby viewers
        self.game_loop_tasks: dict[str, asyncio.Task] = (
            {}
        )  # game_id -> running loop task

    async def connect_game(self, game_id: str, websocket: WebSocket):
        """Accept a new WebSocket connection for a game."""
        await websocket.accept()
        if game_id not in self.game_connections:
            self.game_connections[game_id] = []
        self.game_connections[game_id].append(websocket)
        game_manager.add_ws_connection(game_id, websocket)
        # Start the game loop when the first player connects
        self.start_game_loop(game_id)

    def start_game_loop(self, game_id: str) -> None:
        """Start the game tick loop for a game if not already running."""
        existing = self.game_loop_tasks.get(game_id)
        if existing is None or existing.done():
            task = asyncio.create_task(self._game_loop(game_id))
            self.game_loop_tasks[game_id] = task

    def stop_game_loop(self, game_id: str) -> None:
        """Cancel the game tick loop for a game."""
        task = self.game_loop_tasks.pop(game_id, None)
        if task and not task.done():
            task.cancel()

    async def _game_loop(self, game_id: str) -> None:
        """Game tick loop: spawn mobs, move mobs, update turrets and broadcast changes every iteration."""
        try:
            while True:
                await asyncio.sleep(0.1)

                # Stop if the game no longer has active connections
                connections = self.game_connections.get(game_id)
                if not connections:
                    break

                game = game_manager.get_game(game_id)
                if not game:
                    break

                # Increment game tick
                game_manager.tick_game(game_id)

                # Spawn new mobs from waves
                spawned_mobs = game_manager.spawn_mobs(game_id)
                if spawned_mobs:
                    await self.broadcast_game(
                        game_id,
                        {"type": "mob_spawned", "data": spawned_mobs},
                    )

                # Update mobs
                mob_dicts, dead_mob_ids = game_manager.tick_mobs(game_id)
                await self.broadcast_game(
                    game_id,
                    {"type": "mob_update", "data": mob_dicts},
                )
                if dead_mob_ids:
                    await self.broadcast_game(
                        game_id,
                        {"type": "mob_died", "data": dead_mob_ids},
                    )

                # Update turrets and broadcast rotation changes and shots
                turret_rotations, turret_shots = game_manager.tick_turrets(game_id)
                if turret_rotations:
                    await self.broadcast_game(
                        game_id,
                        {"type": "turret_rotation", "data": turret_rotations},
                    )
                if turret_shots:
                    await self.broadcast_game(
                        game_id,
                        {"type": "turret_shot", "data": turret_shots},
                    )
        except asyncio.CancelledError:
            pass  # Graceful shutdown

    async def connect_lobby(self, websocket: WebSocket):
        """Accept a new WebSocket connection for lobby."""
        await websocket.accept()
        self.lobby_connections.append(websocket)

    def disconnect_game(self, game_id: str, websocket: WebSocket):
        """Remove a WebSocket connection from a game."""
        if game_id in self.game_connections:
            try:
                self.game_connections[game_id].remove(websocket)
            except ValueError:
                pass
            game_manager.remove_ws_connection(game_id, websocket)

    def disconnect_lobby(self, websocket: WebSocket):
        """Remove a WebSocket connection from lobby."""
        try:
            self.lobby_connections.remove(websocket)
        except ValueError:
            pass

    async def broadcast_game(self, game_id: str, message: dict):
        """Broadcast a message to all connections for a game."""
        if game_id in self.game_connections:
            disconnected = []
            for connection in self.game_connections[game_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)

            for connection in disconnected:
                self.disconnect_game(game_id, connection)

    async def broadcast_lobby(self, message: dict):
        """Broadcast a message to all lobby connections."""
        disconnected = []
        for connection in self.lobby_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect_lobby(connection)


manager = GameConnectionManager()


@router.websocket("/ws/lobby")
async def lobby_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for lobby updates."""
    try:
        await manager.connect_lobby(websocket)

        # Send initial games list
        games = game_manager.get_all_games()
        await websocket.send_json(
            {
                "type": "games_update",
                "data": [
                    {
                        "id": g.id,
                        "name": g.name,
                        "creator_id": g.creator_id,
                        "created_at": g.created_at,
                        "nb_players": g.nb_players,
                    }
                    for g in games
                ],
            }
        )

        # Keep connection alive
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_lobby(websocket)


@router.websocket("/ws/game/{game_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    game_id: str,
    player_name: str = Query(...),
):
    """WebSocket endpoint for game communication."""
    try:
        await manager.connect_game(game_id, websocket)

        # Get or create the game
        game = game_manager.get_active_game(game_id)
        if not game:
            # Create new game with this ID if it doesn't exist
            game = game_manager.create_game(
                name=f"{player_name}'s game", creator_id=player_name
            )
            # Override the generated ID with the requested one
            game.id = game_id
            game_manager.games[game_id] = game
            game_manager.game_ws_connections[game_id] = [websocket]
            print(f"Created new game {game_id} for player {player_name}")
        else:
            # Game exists, check if player is already in the game, if not add them
            player_exists = any(p.username == player_name for p in game.players)
            if not player_exists:
                player = Player(username=player_name)
                game_manager.add_player_to_game(game_id, player)
                print(f"Player {player_name} rejoined game {game_id}")

        # Send welcome message with map details and initial mob state
        await websocket.send_json(
            {
                "type": "welcome",
                "message": f"Welcome {player_name}!",
                "timestamp": datetime.utcnow().isoformat(),
                "map": game.map.to_dict(),
                "mobs": [m.to_dict() for m in game.mobs],
            }
        )

        # Send initial game state without map
        await websocket.send_json(
            {
                "type": "game_state",
                "data": {
                    "id": game.id,
                    "name": game.name,
                    "nb_players": game.nb_players,
                    "players": [
                        {"id": p.id, "username": p.username} for p in game.players
                    ],
                },
            }
        )

        # Notify other players that a player joined (only if they were re-joining to existing game)
        if (
            game
            and any(p.username == player_name for p in game.players)
            and game_id in game_manager.games
        ):
            await manager.broadcast_game(
                game_id,
                {
                    "type": "player_joined",
                    "player": player_name,
                    "data": {
                        "nb_players": game.nb_players,
                        "players": [
                            {"id": p.id, "username": p.username} for p in game.players
                        ],
                    },
                },
            )

        # Listen for messages (will handle tick updates and player actions later)
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle different message types
            if message.get("type") == "player_action":
                action_type = message.get("action_type")

                # Handle turret placement
                if action_type == "place_turret":
                    action_data = message.get("data", {})
                    x = action_data.get("x")
                    y = action_data.get("y")

                    # Get the current game and player
                    game = game_manager.get_game(game_id)
                    if game is None:
                        continue

                    # Find player ID for this player_name
                    player = next(
                        (p for p in game.players if p.username == player_name), None
                    )
                    if player is None:
                        continue

                    # Attempt to place turret
                    turret = game_manager.add_turret_to_game(game_id, player.id, x, y)

                    if turret:
                        # Broadcast turret placement to all players in game
                        await manager.broadcast_game(
                            game_id,
                            {
                                "type": "turret_placed",
                                "player": player_name,
                                "data": turret.to_dict(),
                            },
                        )
                    else:
                        # Send error back to requesting player
                        await websocket.send_json(
                            {
                                "type": "action_error",
                                "message": "Cannot place turret at this location",
                                "data": {"x": x, "y": y},
                            }
                        )
                else:
                    # Broadcast generic player action
                    await manager.broadcast_game(
                        game_id,
                        {
                            "type": "action",
                            "player": player_name,
                            "data": message.get("data"),
                        },
                    )

    except WebSocketDisconnect:
        manager.disconnect_game(game_id, websocket)

        # Get current game state
        game = game_manager.get_game(game_id)
        if game:
            # Remove player from game
            game.players = [p for p in game.players if p.username != player_name]
            game.nb_players = len(game.players)

            if game.nb_players == 0:
                # Stop the game loop and delete the game
                manager.stop_game_loop(game_id)
                game_manager.delete_game(game_id)
                # Notify lobby of deletion
                await manager.broadcast_lobby(
                    {
                        "type": "game_deleted",
                        "game_id": game_id,
                    }
                )
            else:
                # Update game in RAM
                game_manager.update_game(game)
                # Notify remaining players
                await manager.broadcast_game(
                    game_id,
                    {
                        "type": "player_left",
                        "player": player_name,
                        "data": {
                            "nb_players": game.nb_players,
                            "players": [
                                {"id": p.id, "username": p.username}
                                for p in game.players
                            ],
                        },
                    },
                )
