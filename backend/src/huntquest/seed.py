"""One-shot seed: creates the demo hunt with real Seattle landmark checkpoints, if it doesn't exist yet.

Real coordinates, not placeholders -- pulled from public landmark listings,
same "anchor demo data in something real" approach used for the rivers in
PNWater and the regulation PDFs in Reel'em In AI.
"""

import uuid

from huntquest.models.orm import Checkpoint, Hunt
from huntquest.storage.db import SessionLocal

# Fixed, not random -- docker-compose's simulator service and the CI
# integration job both need to address this exact hunt without scraping a
# generated id out of another container's stdout.
DEMO_HUNT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")

SEATTLE_LANDMARKS = [
    ("Space Needle", "600 ft up since 1962 -- find the tower that started as a World's Fair centerpiece.", 47.6205, -122.3493),
    ("Pike Place Market", "Fish get thrown here. Find the market that's been open continuously since 1907.", 47.6097, -122.3422),
    ("Pioneer Square", "Seattle's oldest neighborhood, named for the totem pole in its square.", 47.6015, -122.3334),
    ("Kerry Park", "The viewpoint on every Seattle postcard -- skyline in front, mountain behind.", 47.6295, -122.3608),
    ("Gas Works Park", "A former coal gasification plant, now a park with a view across Lake Union.", 47.6456, -122.3344),
]


def seed() -> None:
    db = SessionLocal()
    try:
        existing = db.query(Hunt).filter_by(join_code="SEATTLE1").one_or_none()
        if existing:
            print(f"Demo hunt already exists: {existing.id}")
            return

        hunt = Hunt(id=DEMO_HUNT_ID, name="Seattle Landmarks Hunt", city="Seattle, WA", join_code="SEATTLE1")
        db.add(hunt)
        db.flush()

        for name, clue, lat, lng in SEATTLE_LANDMARKS:
            db.add(Checkpoint(hunt_id=hunt.id, name=name, clue=clue, lat=lat, lng=lng, radius_m=60.0))

        db.commit()
        print(f"Seeded demo hunt {hunt.id} (join code SEATTLE1) with {len(SEATTLE_LANDMARKS)} checkpoints.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
