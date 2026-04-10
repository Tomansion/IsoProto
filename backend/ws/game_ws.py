import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from services.game_manager import game_manager
from models.player import Player

router = APIRouter(tags=["game"])


class GameConnectionManager:
    """Manages WebSocket connections for game sessions."""

    def __init__(self):
        self.connections: dict[str, list[WebSocket]] = {}

    async def connect(self, game_id: str, websocket: WebSocket):
        """Accept a new WebSocket connection for a game."""
        await websocket.accept()
        if game_id not in self.connections:
            self.connections[game_id] = []
        self.connections[game_id].append(websocket)
        game_manager.add_ws_connection(game_id, websocket)

    def disconnect(self, game_id: str, websocket: WebSocket):
        """Remove a WebSocket connection from a game."""
        if game_id in self.connections:
            self.connections[game_id].remove(websocket)
            game_manager.remove_ws_connection(game_id, websocket)

    async def broadcast(self, game_id: str, message: dict):
        """Broadcast a message to all connections for a game."""
        if game_id in self.connections:
            disconnected = []
            for connection in self.connections[game_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    disconnected.append(connection)

            # Clean up disconnected connections
            for connection in disconnected:
                self.disconnect(game_id, connection)


manager = GameConnectionManager()


@router.websocket("/ws/game/{game_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    game_id: str,
    player_name: str = Query(...),
):
    """WebSocket endpoint for game communication."""
    try:
        await manager.connect(game_id, websocket)

        # Send initial game state
        game = game_manager.get_active_game(game_id)
        if game:
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

        # Listen for messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle different message types
            if message.get("type") == "player_action":
                # Broadcast to all connected players
                await manager.broadcast(
                    game_id,
                    {
                        "type": "action",
                        "player": player_name,
                        "data": message.get("data"),
                    },
                )
            elif message.get("type") == "chat":
                # Broadcast chat message
                await manager.broadcast(
                    game_id,
                    {
                        "type": "chat",
                        "player": player_name,
                        "message": message.get("message"),
                    },
                )

    except WebSocketDisconnect:
        manager.disconnect(game_id, websocket)
        # Notify other players
        await manager.broadcast(
            game_id,
            {
                "type": "player_disconnected",
                "player": player_name,
            },
        )
