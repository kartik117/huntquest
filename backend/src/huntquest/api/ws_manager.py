"""Fans out real-time events to WebSocket clients via Redis pub/sub.

Each API process only knows about the WebSocket connections it's holding
locally -- it can't push to a socket opened on a different replica. Redis
pub/sub bridges that: every process publishes location/checkpoint events to
a per-hunt channel and subscribes to the same channel, so a player connected
to replica A still sees an update that arrived on replica B. This is the
piece that makes the EKS HorizontalPodAutoscaler (see k8s/) safe to scale
past one replica -- without it, broadcasts would only reach whichever pod
happened to receive that one player's WebSocket connection.
"""

import asyncio
import json
import logging

import redis.asyncio as aioredis
from fastapi import WebSocket

logger = logging.getLogger("huntquest.ws")


def channel_for_hunt(hunt_id: str) -> str:
    return f"hunt:{hunt_id}:events"


class ConnectionManager:
    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url
        self._connections: dict[str, set[WebSocket]] = {}
        self._redis: aioredis.Redis | None = None
        self._listener_task: asyncio.Task | None = None

    async def start(self) -> None:
        self._redis = aioredis.from_url(self._redis_url)
        self._listener_task = asyncio.create_task(self._listen())

    async def stop(self) -> None:
        if self._listener_task:
            self._listener_task.cancel()
        if self._redis:
            await self._redis.close()

    async def connect(self, hunt_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.setdefault(hunt_id, set()).add(ws)

    def disconnect(self, hunt_id: str, ws: WebSocket) -> None:
        self._connections.get(hunt_id, set()).discard(ws)

    async def publish(self, hunt_id: str, message: dict) -> None:
        assert self._redis is not None
        await self._redis.publish(channel_for_hunt(hunt_id), json.dumps(message))

    async def _listen(self) -> None:
        assert self._redis is not None
        pubsub = self._redis.pubsub()
        await pubsub.psubscribe("hunt:*:events")
        async for message in pubsub.listen():
            if message["type"] != "pmessage":
                continue
            channel = message["channel"]
            channel = channel.decode() if isinstance(channel, bytes) else channel
            hunt_id = channel.removeprefix("hunt:").removesuffix(":events")
            data = message["data"]
            data = data.decode() if isinstance(data, bytes) else data
            await self._broadcast_local(hunt_id, data)

    async def _broadcast_local(self, hunt_id: str, raw_message: str) -> None:
        dead: list[WebSocket] = []
        for ws in self._connections.get(hunt_id, set()):
            try:
                await ws.send_text(raw_message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections.get(hunt_id, set()).discard(ws)
