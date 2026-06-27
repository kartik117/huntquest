from huntquest.services.geo import get_position, players_within_radius, record_position


def test_record_and_get_position(fake_redis):
    record_position(fake_redis, "hunt-1", "player-1", lat=47.6205, lng=-122.3493)
    lat, lng = get_position(fake_redis, "hunt-1", "player-1")
    assert round(lat, 3) == round(47.6205, 3)
    assert round(lng, 3) == round(-122.3493, 3)


def test_get_position_returns_none_for_unknown_player(fake_redis):
    assert get_position(fake_redis, "hunt-1", "ghost") is None


def test_players_within_radius_finds_nearby_and_excludes_far(fake_redis):
    # Space Needle
    record_position(fake_redis, "hunt-1", "near", lat=47.6205, lng=-122.3493)
    # Pike Place Market -- roughly 1.3km away, well outside a 100m radius
    record_position(fake_redis, "hunt-1", "far", lat=47.6097, lng=-122.3422)

    nearby = players_within_radius(fake_redis, "hunt-1", lat=47.6206, lng=-122.3494, radius_m=100)
    assert nearby == {"near"}


def test_players_within_radius_is_scoped_to_one_hunt(fake_redis):
    record_position(fake_redis, "hunt-1", "p1", lat=47.6205, lng=-122.3493)
    record_position(fake_redis, "hunt-2", "p2", lat=47.6205, lng=-122.3493)

    nearby = players_within_radius(fake_redis, "hunt-1", lat=47.6205, lng=-122.3493, radius_m=50)
    assert nearby == {"p1"}
