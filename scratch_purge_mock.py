import sqlite3
import json
import os

db_path = "/opt/betting_aggregator/backend/betting_db.sqlite"
lock_path = "/opt/betting_aggregator/backend/daily_top3_lock.json"

print("=== 1. PURGING MOCK FROM SQLITE ===")
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Find mock match IDs
    c.execute("SELECT id, league, home_team, away_team FROM matches WHERE id = 274 OR league LIKE '%Mock%' OR home_team LIKE '%Манчестер Юнайтед%' AND away_team LIKE '%Арсенал%'")
    rows = c.fetchall()
    print(f"Found {len(rows)} mock matches to delete:")
    for r in rows:
        print(" ", r)
        m_id = r[0]
        c.execute("DELETE FROM predictions WHERE match_id = ?", (m_id,))
        c.execute("DELETE FROM historical_results WHERE match_id = ?", (m_id,))
        c.execute("DELETE FROM matches WHERE id = ?", (m_id,))

    conn.commit()
    conn.close()
    print("[+] Database mock records purged successfully!")
else:
    print(f"[-] DB not found at {db_path}")

print("\n=== 2. PURGING 274 FROM daily_top3_lock.json ===")
if os.path.exists(lock_path):
    with open(lock_path, "r", encoding="utf-8") as f:
        locks = json.load(f)

    changed = False
    for dt, ids in list(locks.items()):
        new_ids = [i for i in ids if i != 274]
        if new_ids != ids:
            locks[dt] = new_ids
            changed = True
            print(f"  Cleaned {dt}: {ids} -> {new_ids}")

    # Remove 2026-10-29 lock so today is recalculated with REAL high-consensus matches
    if "2026-10-29" in locks:
        print("  Removing 2026-10-29 lock to force fresh high-consensus selection!")
        del locks["2026-10-29"]
        changed = True

    if changed:
        with open(lock_path, "w", encoding="utf-8") as f:
            json.dump(locks, f, indent=2)
        print("[+] daily_top3_lock.json updated successfully!")
else:
    print(f"[-] Lock file not found at {lock_path}")
