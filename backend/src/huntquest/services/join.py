import secrets
import uuid

from sqlalchemy.orm import Session

from huntquest.models.orm import Hunt, Player, Team


class HuntNotFoundError(Exception):
    pass


def join_hunt(db: Session, hunt_id: uuid.UUID, display_name: str, team_name: str) -> Player:
    hunt = db.get(Hunt, hunt_id)
    if hunt is None:
        raise HuntNotFoundError(f"No hunt {hunt_id}")

    team = db.query(Team).filter_by(hunt_id=hunt_id, name=team_name).one_or_none()
    if team is None:
        team = Team(hunt_id=hunt_id, name=team_name)
        db.add(team)
        db.flush()

    player = Player(
        team_id=team.id,
        display_name=display_name,
        session_token=secrets.token_urlsafe(32),
    )
    db.add(player)
    db.commit()
    return player


def player_for_token(db: Session, session_token: str) -> Player | None:
    return db.query(Player).filter_by(session_token=session_token).one_or_none()
