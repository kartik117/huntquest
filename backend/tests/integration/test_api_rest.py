from fastapi.testclient import TestClient

from huntquest.api.deps import get_redis
from huntquest.api.main import app
from huntquest.models.orm import Hunt, Checkpoint
from huntquest.storage.db import get_db


def make_client(db_session, fake_redis):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = lambda: fake_redis
    return TestClient(app)


def test_health():
    # Deliberately not using TestClient as a context manager here -- that
    # would run the app's lifespan, which starts ConnectionManager and tries
    # to open a real Redis connection for the pub/sub listener. /health
    # doesn't need any of that, so a plain client (no lifespan) is enough
    # and keeps this test from depending on a real Redis being up.
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_get_hunt_returns_its_checkpoints(db_session, fake_redis):
    hunt = Hunt(name="Test Hunt", city="Seattle", join_code="TEST1")
    db_session.add(hunt)
    db_session.flush()
    db_session.add(Checkpoint(hunt_id=hunt.id, name="Space Needle", clue="...", lat=47.6, lng=-122.3, radius_m=60))
    db_session.commit()

    client = make_client(db_session, fake_redis)
    resp = client.get(f"/hunts/{hunt.id}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Test Hunt"
    assert len(body["checkpoints"]) == 1
    assert body["checkpoints"][0]["name"] == "Space Needle"


def test_get_hunt_404s_for_an_unknown_id(db_session, fake_redis):
    client = make_client(db_session, fake_redis)
    resp = client.get("/hunts/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_join_then_appears_on_the_leaderboard_with_zero_score(db_session, fake_redis):
    hunt = Hunt(name="Test Hunt", city="Seattle", join_code="TEST1")
    db_session.add(hunt)
    db_session.commit()

    client = make_client(db_session, fake_redis)
    join_resp = client.post(f"/hunts/{hunt.id}/join", json={"display_name": "Avery", "team_name": "Trailblazers"})
    assert join_resp.status_code == 200
    body = join_resp.json()
    assert "session_token" in body

    board_resp = client.get(f"/hunts/{hunt.id}/teams")
    assert board_resp.status_code == 200
    board = board_resp.json()
    assert len(board) == 1
    assert board[0]["name"] == "Trailblazers"
    assert board[0]["checkpoints_found"] == 0
    assert board[0]["player_count"] == 1
