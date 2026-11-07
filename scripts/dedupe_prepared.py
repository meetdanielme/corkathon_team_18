"""Remove pre-#31 prepared demo rows that now duplicate the current seed.

Why this exists: #31 stopped baking "(fictional demo)" into the stored event title. The dedupe
key is title|date|venue, so after that change a prepared import no longer matched the rows a
previous import had written, and inserted a second copy of every prepared event instead. A
fresh database is unaffected; only a long-lived one such as the hosted Turso database shows it.

The stale rows are identifiable: their generated id still contains "fictional_demo". Nothing
written after #31 does, and no live event ever does.

Usage:
    python -m scripts.dedupe_prepared            # dry run, prints what it would delete
    python -m scripts.dedupe_prepared --apply    # actually delete

Reads the same env as the app, so it targets Turso when TURSO_DATABASE_URL is set.
"""
import os
import sys

from footfall import db
from footfall.config import load_env

STALE = "%fictional_demo%"


def main() -> int:
    load_env()
    apply = "--apply" in sys.argv
    con = db.connect(os.getenv("FOOTFALL_DB", "footfall.sqlite3"))

    rows = con.execute(
        "SELECT id, title, data_mode FROM events WHERE id LIKE ? ORDER BY id", (STALE,)
    ).fetchall()
    if not rows:
        print("Nothing to do: no pre-#31 prepared rows found.")
        return 0

    live = [r for r in rows if r["data_mode"] != "prepared"]
    if live:
        print(f"Refusing to run: {len(live)} matching row(s) are not prepared data.")
        for r in live:
            print(f"  {r['data_mode']:<9} {r['id']}")
        return 1

    print(f"{len(rows)} stale prepared row(s){'' if apply else ' (dry run)'}:")
    for r in rows:
        n = con.execute("SELECT COUNT(*) FROM event_evidence WHERE event_id=?", (r["id"],)).fetchone()[0]
        print(f"  {r['title'][:46]:<46} {n} evidence row(s)")

    if not apply:
        print("\nRe-run with --apply to delete. Nothing was changed.")
        return 0

    # Count first: the remote libSQL cursor wrapper exposes no rowcount, so reading it would
    # raise against Turso, which is the only database that actually has this problem.
    ev_before = con.execute("SELECT COUNT(*) FROM event_evidence WHERE event_id IN "
                            "(SELECT id FROM events WHERE id LIKE ?)", (STALE,)).fetchone()[0]
    # event_evidence.event_id references events(id) with no ON DELETE CASCADE, so evidence first.
    con.execute("DELETE FROM event_evidence WHERE event_id IN "
                "(SELECT id FROM events WHERE id LIKE ?)", (STALE,))
    con.execute("DELETE FROM events WHERE id LIKE ?", (STALE,))
    con.commit()
    n, ev = len(rows), ev_before
    print(f"\nDeleted {n} event(s) and {ev} evidence row(s).")
    print("Now click Load Sample Data once so the current seed is present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
