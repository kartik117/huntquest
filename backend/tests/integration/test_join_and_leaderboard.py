from huntquest.models.orm import CheckpointFound, Hunt, Team
from huntquest.services.join import HuntNotFoundError, join_hunt, player_for_token
from huntquest.services.leaderboard import leaderboard_for_hunt
import uuid

import pytest


def make_hunt(db):
    hunt = Hunt(name="Test Hunt", city="Seattle", join_code="TEST1")
    db.add(hunt)
    db.commit()
    return hunt


def test_join_creates_a_new_team_when_none_exists_with_that_name(db_session):
    hunt = make_hunt(db_session)
    player = join_hunt(db_session, hunt.id, "Avery", "Trailblazers")

    assert player.display_name == "Avery"
    team = db_session.get(Team, player.team_id)
    assert team.name == "Trailblazers"


def test_join_reuses_an_existing_team_with_the_same_name(db_session):
    hunt = make_hunt(db_session)
    p1 = join_hunt(db_session, hunt.id, "Avery", "Trailblazers")
    p2 = join_hunt(db_session, hunt.id, "Bo", "Trailblazers")

    assert p1.team_id == p2.team_id
    assert db_session.query(Team).filter_by(hunt_id=hunt.id, name="Trailblazers").count() == 1


def test_join_raises_for_an_unknown_hunt(db_session):
    with pytest.raises(HuntNotFoundError):
        join_hunt(db_session, uuid.uuid4(), "Avery", "Trailblazers")


def test_session_tokens_are_unique_and_resolve_back_to_the_right_player(db_session):
    hunt = make_hunt(db_session)
    p1 = join_hunt(db_session, hunt.id, "Avery", "Trailblazers")
    p2 = join_hunt(db_session, hunt.id, "Bo", "Map Nerds")

    assert p1.session_token != p2.session_token
    assert player_for_token(db_session, p1.session_token).display_name == "Avery"
    assert player_for_token(db_session, p2.session_token).display_name == "Bo"


def test_player_for_token_returns_none_for_an_unknown_token(db_session):
    assert player_for_token(db_session, "not-a-real-token") is None


def test_leaderboard_ranks_teams_by_checkpoints_found(db_session):
    hunt = make_hunt(db_session)
    leader = join_hunt(db_session, hunt.id, "Avery", "Trailblazers")
    join_hunt(db_session, hunt.id, "Casey", "Map Nerds")

    from huntquest.models.orm import Checkpoint

    cp1 = Checkpoint(hunt_id=hunt.id, name="A", clue="", lat=0, lng=0, radius_m=10)
    cp2 = Checkpoint(hunt_id=hunt.id, name="B", clue="", lat=0, lng=0, radius_m=10)
    db_session.add_all([cp1, cp2])
    db_session.flush()
    db_session.add_all(
        [
            CheckpointFound(team_id=leader.team_id, checkpoint_id=cp1.id, found_by_player_id=leader.id),
            CheckpointFound(team_id=leader.team_id, checkpoint_id=cp2.id, found_by_player_id=leader.id),
        ]
    )
    db_session.commit()

    board = leaderboard_for_hunt(db_session, hunt.id)

    assert board[0].name == "Trailblazers"
    assert board[0].checkpoints_found == 2
    assert board[1].name == "Map Nerds"
    assert board[1].checkpoints_found == 0
