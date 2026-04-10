from models.game import Game
from models.player import Player
from services.game_manager import game_manager
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
import asyncio

# Import the WebSocket manager
from ws.game_ws import manager as ws_manager

# Initialize router
router = APIRouter(tags=["games"])


class GameResponse(BaseModel):
    id: str
    name: str
    creator_id: str
    created_at: str
    nb_players: int

    @classmethod
    def from_game(cls, game: Game) -> "GameResponse":
        return cls(
            id=game.id,
            name=game.name,
            creator_id=game.creator_id,
            created_at=game.created_at,
            nb_players=game.nb_players,
        )


@router.get("/", response_model=List[GameResponse])
async def get_games():
    """Get all games."""
    try:
        games = game_manager.get_all_games()
        return [GameResponse.from_game(g) for g in games]
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=GameResponse)
async def create_game(player_name: str = Query(...)):
    """Create a new game."""
    try:
        # Create a new game in RAM
        new_game = game_manager.create_game(
            name=player_name,
            creator_id=player_name,
        )

        # Broadcast to lobby
        asyncio.create_task(ws_manager.broadcast_lobby({
            "type": "game_created",
            "data": {
                "id": new_game.id,
                "name": new_game.name,
                "creator_id": new_game.creator_id,
                "created_at": new_game.created_at,
                "nb_players": new_game.nb_players,
            }
        }))

        return GameResponse.from_game(new_game)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

        return GameResponse.from_game(saved_game)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{game_id}/join/", response_model=GameResponse)
async def join_game(game_id: str, player_name: str = Query(...)):
    """Join an existing game."""
    try:
        # Get the game from RAM
        game = game_manager.get_game(game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Create player and add to game
        player = Player(username=player_name)
        game_manager.add_player_to_game(game_id, player)

        # Broadcast to lobby
        asyncio.create_task(ws_manager.broadcast_lobby({
            "type": "game_updated",
            "data": {
                "id": game.id,
                "name": game.name,
                "creator_id": game.creator_id,
                "created_at": game.created_at,
                "nb_players": game.nb_players,
            }
        }))

        # Broadcast to game that player joined
        asyncio.create_task(ws_manager.broadcast_game(
            game_id,
            {
                "type": "player_joined",
                "player": player_name,
                "data": {
                    "nb_players": game.nb_players,
                    "players": [{"id": p.id, "username": p.username} for p in game.players],
                },
            }
        ))

        return GameResponse.from_game(game)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
