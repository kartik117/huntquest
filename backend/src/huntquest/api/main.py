import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from huntquest.api.deps import get_redis
from huntquest.api.schemas import HuntOut, JoinRequest, JoinResponse, LocationPingIn, TeamScore
from huntquest.api.ws_manager import ConnectionManager
from huntquest.config import settings
from huntquest.models.orm import Hunt
from huntquest.services.checkpoints import check_for_discoveries
from huntquest.services.geo import record_position
from huntquest.services.join import HuntNotFoundError, join_hunt, player_for_token
from huntquest.services.leaderboard import leaderboard_for_hunt
from huntquest.storage.db import get_db

manager = ConnectionManager(f"redis://{settings.redis_host}:{settings.redis_port}")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await manager.start()
    yield
    await manager.stop()


app = FastAPI(title="HuntQuest API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/hunts/{hunt_id}", response_model=HuntOut)
def get_hunt(hunt_id: uuid.UUID, db: Session = Depends(get_db)) -> Hunt:
    hunt = db.get(Hunt, hunt_id)
    if hunt is None:
        raise HTTPException(404, "Hunt not found")
    return hunt


@app.post("/hunts/{hunt_id}/join", response_model=JoinResponse)
def join(hunt_id: uuid.UUID, body: JoinRequest, db: Session = Depends(get_db)) -> JoinResponse:
    try:
        player = join_hunt(db, hunt_id, body.display_name, body.team_name)
    except HuntNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    return JoinResponse(player_id=player.id, team_id=player.team_id, session_token=player.session_token)


@app.get("/hunts/{hunt_id}/teams", response_model=list[TeamScore])
def teams(hunt_id: uuid.UUID, db: Session = Depends(get_db)) -> list[TeamScore]:
    return leaderboard_for_hunt(db, hunt_id)


@app.websocket("/ws/hunts/{hunt_id}")
async def hunt_websocket(
    websocket: WebSocket,
    hunt_id: uuid.UUID,
    token: str = Query(...),
    db: Session = Depends(get_db),
) -> None:
    player = player_for_token(db, token)
    if player is None or player.team.hunt_id != hunt_id:
        await websocket.close(code=4401)
        return

    r = get_redis()
    await manager.connect(str(hunt_id), websocket)
    try:
        while True:
            payload = await websocket.receive_json()
            if payload.get("type") != "location":
                continue
            try:
                ping = LocationPingIn(lat=payload["lat"], lng=payload["lng"])
            except (KeyError, ValueError):
                continue

            record_position(r, str(hunt_id), str(player.id), ping.lat, ping.lng)
            await manager.publish(
                str(hunt_id),
                {
                    "type": "location",
                    "player_id": str(player.id),
                    "team_id": str(player.team_id),
                    "display_name": player.display_name,
                    "lat": ping.lat,
                    "lng": ping.lng,
                },
            )

            discoveries = check_for_discoveries(db, r, hunt_id, player.team_id, player.id)
            for checkpoint in discoveries:
                await manager.publish(
                    str(hunt_id),
                    {
                        "type": "checkpoint_found",
                        "team_id": str(player.team_id),
                        "checkpoint_id": str(checkpoint.id),
                        "checkpoint_name": checkpoint.name,
                        "found_by": player.display_name,
                    },
                )
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(str(hunt_id), websocket)
