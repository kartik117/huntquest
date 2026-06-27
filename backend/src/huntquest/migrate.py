"""One-shot schema creation, run as its own service/job before api or simulator start.

Letting every service independently call create_all() raced CREATE TABLE
statements against a fresh Postgres in an earlier project in this batch
(PulsePay) -- a dedicated single-writer migrate step avoids repeating that.
"""

from huntquest.models.orm import Base
from huntquest.storage.db import engine


def main() -> None:
    Base.metadata.create_all(engine)
    print("HuntQuest schema migrated.")


if __name__ == "__main__":
    main()
