from pydantic import BaseModel


class LoginRequest(BaseModel):
    player_id: int


class MatchmakingRequest(BaseModel):
    player_id: int


class GameStartRequest(BaseModel):
    player_id: int
    match_id: str


class PlayerActionRequest(BaseModel):
    player_id: int
    action: str


class GameEndRequest(BaseModel):
    player_id: int
    match_id: str


class ReconnectRequest(BaseModel):
    player_id: int