from huntquest.models.orm import Checkpoint, CheckpointFound, Hunt, Player, Team
from huntquest.services.checkpoints import check_for_discoveries
from huntquest.services.geo import record_position


def make_hunt_with_checkpoint(db, lat=47.6205, lng=-122.3493, radius_m=60.0):
    hunt = Hunt(name="Test Hunt", city="Seattle", join_code="TEST1")
    db.add(hunt)
    db.flush()
    checkpoint = Checkpoint(hunt_id=hunt.id, name="Space Needle", clue="...", lat=lat, lng=lng, radius_m=radius_m)
    db.add(checkpoint)
    team = Team(hunt_id=hunt.id, name="Trailblazers")
    db.add(team)
    db.flush()
    player = Player(team_id=team.id, display_name="Avery", session_token="tok-1")
    db.add(player)
    db.commit()
    return hunt, checkpoint, team, player


def test_discovers_checkpoint_when_player_is_within_radius(db_session, fake_redis):
    hunt, checkpoint, team, player = make_hunt_with_checkpoint(db_session)
    record_position(fake_redis, str(hunt.id), str(player.id), lat=checkpoint.lat, lng=checkpoint.lng)

    found = check_for_discoveries(db_session, fake_redis, hunt.id, team.id, player.id)

    assert [c.id for c in found] == [checkpoint.id]
    assert db_session.query(CheckpointFound).filter_by(team_id=team.id, checkpoint_id=checkpoint.id).count() == 1


def test_does_not_discover_checkpoint_when_player_is_far_away(db_session, fake_redis):
    hunt, checkpoint, team, player = make_hunt_with_checkpoint(db_session)
    # Pike Place Market -- well outside the checkpoint's 60m radius
    record_position(fake_redis, str(hunt.id), str(player.id), lat=47.6097, lng=-122.3422)

    found = check_for_discoveries(db_session, fake_redis, hunt.id, team.id, player.id)

    assert found == []
    assert db_session.query(CheckpointFound).count() == 0


def test_does_not_rediscover_an_already_found_checkpoint(db_session, fake_redis):
    hunt, checkpoint, team, player = make_hunt_with_checkpoint(db_session)
    record_position(fake_redis, str(hunt.id), str(player.id), lat=checkpoint.lat, lng=checkpoint.lng)

    first = check_for_discoveries(db_session, fake_redis, hunt.id, team.id, player.id)
    second = check_for_discoveries(db_session, fake_redis, hunt.id, team.id, player.id)

    assert len(first) == 1
    assert second == []
    assert db_session.query(CheckpointFound).count() == 1


def test_a_second_teammate_does_not_double_count_a_checkpoint(db_session, fake_redis):
    hunt, checkpoint, team, player = make_hunt_with_checkpoint(db_session)
    teammate = Player(team_id=team.id, display_name="Bo", session_token="tok-2")
    db_session.add(teammate)
    db_session.commit()

    record_position(fake_redis, str(hunt.id), str(player.id), lat=checkpoint.lat, lng=checkpoint.lng)
    check_for_discoveries(db_session, fake_redis, hunt.id, team.id, player.id)

    record_position(fake_redis, str(hunt.id), str(teammate.id), lat=checkpoint.lat, lng=checkpoint.lng)
    second_found = check_for_discoveries(db_session, fake_redis, hunt.id, team.id, teammate.id)

    assert second_found == []
    assert db_session.query(CheckpointFound).count() == 1
