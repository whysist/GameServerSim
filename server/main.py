from fastapi import FastAPI, HTTPException

from server.models import (
    LoginRequest,
    MatchmakingRequest,
    GameStartRequest,
    PlayerActionRequest,
    GameEndRequest,
    ReconnectRequest,
)

from server.state import (
    create_player,
    get_player,
    create_match,
)


app = FastAPI(
    title="Game Backend Simulator",
    description="A minimal multiplayer game backend for load testing.",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy"
    }


@app.post("/login")
async def login(request: LoginRequest):

    create_player(request.player_id)

    return {
        "success": True,
        "player_id": request.player_id,
        "status": "LOBBY",
    }


@app.get("/profile/{player_id}")
async def get_profile(player_id: int):

    player = get_player(player_id)

    if player is None:
        raise HTTPException(
            status_code=404,
            detail="Player not found",
        )

    return player


@app.post("/matchmaking")
async def matchmaking(request: MatchmakingRequest):

    player = get_player(request.player_id)

    if player is None:
        raise HTTPException(
            status_code=404,
            detail="Player not found",
        )

    match_id = create_match(request.player_id)

    player["status"] = "MATCHMAKING"
    player["match_id"] = match_id

    return {
        "success": True,
        "match_id": match_id,
        "status": "MATCHMAKING",
    }


@app.post("/game/start")
async def start_game(request: GameStartRequest):

    player = get_player(request.player_id)

    if player is None:
        raise HTTPException(
            status_code=404,
            detail="Player not found",
        )

    player["status"] = "IN_GAME"

    return {
        "success": True,
        "player_id": request.player_id,
        "match_id": request.match_id,
        "status": "IN_GAME",
    }


@app.post("/game/action")
async def player_action(request: PlayerActionRequest):

    player = get_player(request.player_id)

    if player is None:
        raise HTTPException(
            status_code=404,
            detail="Player not found",
        )

    if player["status"] != "IN_GAME":
        raise HTTPException(
            status_code=400,
            detail="Player is not currently in a game",
        )

    return {
        "success": True,
        "player_id": request.player_id,
        "action": request.action,
    }


@app.post("/game/end")
async def end_game(request: GameEndRequest):

    player = get_player(request.player_id)

    if player is None:
        raise HTTPException(
            status_code=404,
            detail="Player not found",
        )

    player["status"] = "LOBBY"
    player["match_id"] = None

    return {
        "success": True,
        "player_id": request.player_id,
        "status": "LOBBY",
    }


@app.post("/reconnect")
async def reconnect(request: ReconnectRequest):

    player = get_player(request.player_id)

    if player is None:
        raise HTTPException(
            status_code=404,
            detail="Player not found",
        )

    return {
        "success": True,
        "player_id": request.player_id,
        "status": player["status"],
    }