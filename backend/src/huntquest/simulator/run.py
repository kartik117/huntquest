"""Simulates 2 teams of simulated players walking a real route between the demo
hunt's Seattle checkpoints and pinging their location over the real WebSocket
API -- so the live map and leaderboard have something to show without needing
actual phones with GPS. Same role as the IoT sensor simulator in PNWater.
"""

import asyncio
import json
import logging
import os
import time

import httpx
import websockets

from huntquest.simulator.walker import interpolate_path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger("huntquest.simulator")

API_HTTP = os.environ.get("HUNTQUEST_API_HTTP", "http://localhost:8000")
API_WS = os.environ.get("HUNTQUEST_API_WS", "ws://localhost:8000")
JOIN_CODE = "SEATTLE1"
STEP_SECONDS = float(os.environ.get("HUNTQUEST_SIM_STEP_SECONDS", "0.5"))
STEPS_PER_LEG = int(os.environ.get("HUNTQUEST_SIM_STEPS_PER_LEG", "8"))

# Real checkpoint coordinates from seed.py, walked in two different orders so
# the two simulated teams don't move in lockstep.
WAYPOINTS = [
    (47.6205, -122.3493),  # Space Needle
    (47.6097, -122.3422),  # Pike Place Market
    (47.6015, -122.3334),  # Pioneer Square
    (47.6295, -122.3608),  # Kerry Park
    (47.6456, -122.3344),  # Gas Works Park
]

TEAM_ROUTES = {
    "Trailblazers": WAYPOINTS,
    "Map Nerds": list(reversed(WAYPOINTS)),
}


async def find_demo_hunt(client: httpx.AsyncClient) -> str:
    # The seed script prints the hunt id but doesn't expose a "find by join
    # code" endpoint (out of scope -- this is a single-demo-hunt app for
    # now), so the simulator takes the hunt id directly as an env var.
    hunt_id = os.environ["HUNTQUEST_DEMO_HUNT_ID"]
    resp = await client.get(f"{API_HTTP}/hunts/{hunt_id}")
    resp.raise_for_status()
    return hunt_id


async def join_team(client: httpx.AsyncClient, hunt_id: str, display_name: str, team_name: str) -> str:
    resp = await client.post(
        f"{API_HTTP}/hunts/{hunt_id}/join",
        json={"display_name": display_name, "team_name": team_name},
    )
    resp.raise_for_status()
    return resp.json()["session_token"]


async def walk_player(hunt_id: str, token: str, display_name: str, route: list[tuple[float, float]]) -> None:
    uri = f"{API_WS}/ws/hunts/{hunt_id}?token={token}"
    async with websockets.connect(uri) as ws:
        for lat, lng in interpolate_path(route, STEPS_PER_LEG):
            await ws.send(json.dumps({"type": "location", "lat": lat, "lng": lng}))
            try:
                reply = await asyncio.wait_for(ws.recv(), timeout=0.05)
                event = json.loads(reply)
                if event.get("type") == "checkpoint_found":
                    logger.info("%s's team found %s!", display_name, event["checkpoint_name"])
            except asyncio.TimeoutError:
                pass
            await asyncio.sleep(STEP_SECONDS)
    logger.info("%s finished their route.", display_name)


async def main() -> None:
    async with httpx.AsyncClient() as client:
        for attempt in range(30):
            try:
                hunt_id = await find_demo_hunt(client)
                break
            except (httpx.ConnectError, httpx.HTTPStatusError):
                logger.info("Waiting for API (attempt %d)...", attempt + 1)
                time.sleep(2)
        else:
            raise RuntimeError("API never became reachable")

        walkers = []
        for team_name, route in TEAM_ROUTES.items():
            for player_name in (f"{team_name}-1", f"{team_name}-2"):
                token = await join_team(client, hunt_id, player_name, team_name)
                walkers.append(walk_player(hunt_id, token, player_name, route))

        await asyncio.gather(*walkers)


if __name__ == "__main__":
    asyncio.run(main())
