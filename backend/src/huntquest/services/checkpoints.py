import uuid

from redis import Redis
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from huntquest.models.orm import Checkpoint, CheckpointFound
from huntquest.services.geo import players_within_radius


def check_for_discoveries(
    db: Session, r: Redis, hunt_id: uuid.UUID, team_id: uuid.UUID, player_id: uuid.UUID
) -> list[Checkpoint]:
    """Call after recording a player's new position. Returns any checkpoint this ping just discovered for the team."""
    already_found = {
        row.checkpoint_id for row in db.query(CheckpointFound.checkpoint_id).filter_by(team_id=team_id)
    }
    candidates = db.query(Checkpoint).filter(Checkpoint.hunt_id == hunt_id).all()

    newly_found: list[Checkpoint] = []
    for checkpoint in candidates:
        if checkpoint.id in already_found:
            continue
        nearby = players_within_radius(r, str(hunt_id), checkpoint.lat, checkpoint.lng, checkpoint.radius_m)
        if str(player_id) not in nearby:
            continue

        found = CheckpointFound(team_id=team_id, checkpoint_id=checkpoint.id, found_by_player_id=player_id)
        db.add(found)
        try:
            db.commit()
        except IntegrityError:
            # Another player on the same team pinged into the same radius in
            # the same instant -- the unique constraint on (team_id,
            # checkpoint_id) means only one of the two concurrent commits
            # wins, which is exactly the "found once per team" behavior we
            # want, just arriving as a race instead of the already_found
            # check catching it.
            db.rollback()
            continue
        newly_found.append(checkpoint)

    return newly_found
