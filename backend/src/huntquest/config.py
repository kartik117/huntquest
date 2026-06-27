from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HUNTQUEST_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://huntquest:huntquest@localhost:5432/huntquest"
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Meters -- how close a team's player has to get to a checkpoint's
    # lat/lng before it counts as found. Real GPS on a phone is accurate to
    # roughly 5-10m in good conditions, so anything tighter is unreliable.
    default_checkpoint_radius_m: float = 40.0

    # A player who never moves more than this many meters from their last
    # accepted ping within this many seconds is rate-limited -- prevents a
    # buggy or malicious client from flooding GEOADD calls.
    min_ping_interval_seconds: float = 1.0


settings = Settings()
