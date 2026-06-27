"""Interpolates a smooth walking path between real waypoints, so a simulated player's
position moves continuously instead of teleporting between checkpoints.
"""

from collections.abc import Iterator


def interpolate_path(
    waypoints: list[tuple[float, float]], steps_per_leg: int
) -> Iterator[tuple[float, float]]:
    """Yields (lat, lng) points along straight-line legs between consecutive waypoints."""
    for (lat1, lng1), (lat2, lng2) in zip(waypoints, waypoints[1:]):
        for step in range(steps_per_leg):
            t = step / steps_per_leg
            yield (lat1 + (lat2 - lat1) * t, lng1 + (lng2 - lng1) * t)
    yield waypoints[-1]
