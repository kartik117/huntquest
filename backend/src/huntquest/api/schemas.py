import uuid

from pydantic import BaseModel, Field


class CheckpointOut(BaseModel):
    id: uuid.UUID
    name: str
    clue: str
    lat: float
    lng: float
    radius_m: float

    model_config = {"from_attributes": True}


class TeamScore(BaseModel):
    team_id: uuid.UUID
    name: str
    checkpoints_found: int
    player_count: int


class HuntOut(BaseModel):
    id: uuid.UUID
    name: str
    city: str
    join_code: str
    checkpoints: list[CheckpointOut]


class JoinRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)
    team_name: str = Field(min_length=1, max_length=80)


class JoinResponse(BaseModel):
    player_id: uuid.UUID
    team_id: uuid.UUID
    session_token: str


class LocationPingIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
