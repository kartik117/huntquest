import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from huntquest.api.schemas import TeamScore
from huntquest.models.orm import CheckpointFound, Player, Team


def leaderboard_for_hunt(db: Session, hunt_id: uuid.UUID) -> list[TeamScore]:
    teams = db.query(Team).filter_by(hunt_id=hunt_id).all()

    found_counts = dict(
        db.query(CheckpointFound.team_id, func.count(CheckpointFound.id))
        .join(Team, Team.id == CheckpointFound.team_id)
        .filter(Team.hunt_id == hunt_id)
        .group_by(CheckpointFound.team_id)
        .all()
    )
    player_counts = dict(
        db.query(Player.team_id, func.count(Player.id))
        .join(Team, Team.id == Player.team_id)
        .filter(Team.hunt_id == hunt_id)
        .group_by(Player.team_id)
        .all()
    )

    scores = [
        TeamScore(
            team_id=team.id,
            name=team.name,
            checkpoints_found=found_counts.get(team.id, 0),
            player_count=player_counts.get(team.id, 0),
        )
        for team in teams
    ]
    return sorted(scores, key=lambda s: s.checkpoints_found, reverse=True)
