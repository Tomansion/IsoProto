import json
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from services.game_manager import game_manager

router = APIRouter(tags=["game"])


class GameConnectionManager:
    """Manages WebSocket connections for game sessions and lobby."""

    def __init__(self):
        self.game_connections: dict[str, list[WebSocket]] = {}  # game_id -> connections
        self.lobby_connections: list[WebSocket] = []  # All lobby viewers

    async def connect_game(self, game_id: str, websocket: WebSocket):
        """Accept a new WebSocket connection for a game."""
        await websocket.accept()
        if game_id not in self.game_connections:
            self.game_connections[game_id] = []
        self.game_connections[game_id].append(websocket)
        game_manager.add_ws_connection(game_id, websocket)

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
        await websocket.send_json({
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
            ]
        })
        
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

        # Send welcome message with map details
        game = game_manager.get_active_game(game_id)
        if game:
            await websocket.send_json(
                {
                    "type": "welcome",
                    "message": f"Welcome {player_name}!",
                    "timestamp": datetime.utcnow().isoformat(),
                    "map": game.map.to_dict(),
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
                            {"id": p.id, "username": p.username}
                            for p in game.players
                        ],
                    },
                }
            )

        # Listen for messages (will handle tick updates and player actions later)
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle different message types
            if message.get("type") == "player_action":
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
                # Delete game if empty
                game_manager.delete_game(game_id)
                # Notify lobby of deletion
                await manager.broadcast_lobby({
                    "type": "game_deleted",
                    "game_id": game_id,
                })
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
                            "players": [{"id": p.id, "username": p.username} for p in game.players],
                        },
                    },
                )
