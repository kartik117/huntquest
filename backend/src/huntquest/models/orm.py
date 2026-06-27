import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Float, DateTime, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Hunt(Base):
    __tablename__ = "hunts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120))
    city: Mapped[str] = mapped_column(String(120))
    join_code: Mapped[str] = mapped_column(String(8), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    checkpoints: Mapped[list["Checkpoint"]] = relationship(back_populates="hunt", cascade="all, delete-orphan")
    teams: Mapped[list["Team"]] = relationship(back_populates="hunt", cascade="all, delete-orphan")


class Checkpoint(Base):
    __tablename__ = "checkpoints"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    hunt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("hunts.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    clue: Mapped[str] = mapped_column(String(500))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    radius_m: Mapped[float] = mapped_column(Float)

    hunt: Mapped["Hunt"] = relationship(back_populates="checkpoints")


class Team(Base):
    __tablename__ = "teams"
    __table_args__ = (UniqueConstraint("hunt_id", "name", name="uq_team_hunt_name"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    hunt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("hunts.id"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    hunt: Mapped["Hunt"] = relationship(back_populates="teams")
    players: Mapped[list["Player"]] = relationship(back_populates="team", cascade="all, delete-orphan")
    found_checkpoints: Mapped[list["CheckpointFound"]] = relationship(
        back_populates="team", cascade="all, delete-orphan"
    )


class Player(Base):
    __tablename__ = "players"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), index=True)
    display_name: Mapped[str] = mapped_column(String(80))
    session_token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    team: Mapped["Team"] = relationship(back_populates="players")


class CheckpointFound(Base):
    """One row per (team, checkpoint) -- a checkpoint only counts once per team, however many members walk past it."""

    __tablename__ = "checkpoints_found"
    __table_args__ = (UniqueConstraint("team_id", "checkpoint_id", name="uq_found_team_checkpoint"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), index=True)
    checkpoint_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("checkpoints.id"), index=True)
    found_by_player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id"))
    found_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    team: Mapped["Team"] = relationship(back_populates="found_checkpoints")


class LocationPing(Base):
    """Historical log of every accepted location ping, for replay/audit -- Redis GEO holds the live/current position."""

    __tablename__ = "location_pings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    player_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("players.id"), index=True)
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)
