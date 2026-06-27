"""Wraps Redis's native geospatial commands -- GEOADD/GEOSEARCH do exactly what this app needs
(store a player's last known position, find who's within N meters of a point) without
hand-rolling haversine distance math or a spatial index ourselves.
"""

from redis import Redis

POSITIONS_KEY_TEMPLATE = "hunt:{hunt_id}:positions"


def positions_key(hunt_id: str) -> str:
    return POSITIONS_KEY_TEMPLATE.format(hunt_id=hunt_id)


def record_position(r: Redis, hunt_id: str, player_id: str, lat: float, lng: float) -> None:
    # Redis GEOADD takes (longitude, latitude) -- the opposite order of how
    # humans usually say "lat, lng" -- easy to get backwards silently since
    # both are valid floats; got this right by reading the GEOADD docs twice.
    r.geoadd(positions_key(hunt_id), [lng, lat, player_id])


def get_position(r: Redis, hunt_id: str, player_id: str) -> tuple[float, float] | None:
    result = r.geopos(positions_key(hunt_id), player_id)
    if not result or result[0] is None:
        return None
    lng, lat = result[0]
    return lat, lng


def players_within_radius(r: Redis, hunt_id: str, lat: float, lng: float, radius_m: float) -> set[str]:
    """Returns the set of player ids currently within radius_m meters of (lat, lng)."""
    members = r.geosearch(
        positions_key(hunt_id),
        longitude=lng,
        latitude=lat,
        radius=radius_m,
        unit="m",
    )
    return {m.decode() if isinstance(m, bytes) else m for m in members}
