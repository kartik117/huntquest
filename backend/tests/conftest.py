import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from huntquest.models.orm import Base


@pytest.fixture()
def db_session():
    # In-memory SQLite, real schema via the same Base.metadata used in
    # production -- StaticPool so the single in-memory connection is reused
    # across the session's lifetime instead of each connection getting its
    # own throwaway database.
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def fake_redis():
    import fakeredis

    return fakeredis.FakeStrictRedis()
