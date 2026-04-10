from models.game import Game
from models.player import Player
from models.database import GameDatabase
from services.game_manager import game_manager
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional

# Initialize router and database
router = APIRouter(tags=["games"])
db = GameDatabase("data")


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
        games = db.get_all_games()
        return [GameResponse.from_game(g) for g in games]
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=GameResponse)
async def create_game(player_name: str = Query(...)):
    """Create a new game."""
    try:
        # Create a new game with player as creator
        new_game = Game(
            name=player_name,
            creator_id=player_name,
        )
        # Add creator as first player
        creator = Player(username=player_name)
        new_game.players.append(creator)
        new_game.nb_players = 1

        # Save it to the database
        saved_game = db.save_game(new_game)

        # Make it active
        game_manager.create_active_game(saved_game)

        return GameResponse.from_game(saved_game)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{game_id}/join/", response_model=GameResponse)
async def join_game(game_id: str, player_name: str = Query(...)):
    """Join an existing game."""
    try:
        # Get the game from database
        game = db.get_game(game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Create player and add to game
        player = Player(username=player_name)
        game.players.append(player)
        game.nb_players = len(game.players)

        # Update database
        db.update_game(game)

        # Make sure game is in active manager
        if not game_manager.is_game_active(game_id):
            game_manager.create_active_game(game)
        else:
            game_manager.add_player_to_game(game_id, player)

        return GameResponse.from_game(game)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
