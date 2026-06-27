from huntquest.simulator.walker import interpolate_path


def test_interpolate_path_starts_and_ends_at_waypoints():
    waypoints = [(0.0, 0.0), (10.0, 10.0)]
    points = list(interpolate_path(waypoints, steps_per_leg=4))
    assert points[0] == (0.0, 0.0)
    assert points[-1] == (10.0, 10.0)


def test_interpolate_path_visits_every_waypoint_in_a_multi_leg_route():
    waypoints = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)]
    points = list(interpolate_path(waypoints, steps_per_leg=5))
    for wp in waypoints:
        assert wp in points


def test_interpolate_path_step_count_matches_legs_times_steps_plus_final_point():
    waypoints = [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0)]
    points = list(interpolate_path(waypoints, steps_per_leg=3))
    # 2 legs * 3 steps each, plus the final waypoint appended once at the end
    assert len(points) == 2 * 3 + 1
