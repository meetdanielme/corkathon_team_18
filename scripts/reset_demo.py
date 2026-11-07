"""Delete and rebuild the local demo database, then load prepared data. Usage: python -m scripts.reset_demo"""
import os
from pathlib import Path

from footfall import db
from footfall.scout.refresh import run_prepared


def main() -> None:
    path = Path(os.getenv("FOOTFALL_DB", "footfall.sqlite3"))
    path.unlink(missing_ok=True)
    con = db.connect(str(path))
    db.init(con)
    db.seed(con)
    run = run_prepared(con)
    print(f"Rebuilt {path}: prepared run {run['status']}, {run['events_upserted']} events")


if __name__ == "__main__":
    main()
