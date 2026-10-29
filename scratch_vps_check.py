import sqlite3
import os
import glob

db_paths = [
    "/opt/betting_aggregator/backend/betting_db.sqlite",
    "/opt/betting_aggregator/backend/betting.db",
    "/opt/betting_aggregator/betting_db.sqlite"
]

db_path = None
for p in db_paths:
    if os.path.exists(p):
        db_path = p
        break

print(f"Connecting to DB: {db_path}")
if not db_path:
    print("Database not found!")
    exit(1)

conn = sqlite3.connect(db_path)
c = conn.cursor()

# 1. Check for Mock matches
print("=== 1. MOCK MATCHES ===")
c.execute("SELECT id, league, home_team, away_team, match_date, status FROM matches WHERE league LIKE '%Mock%' OR home_team LIKE '%Манчестер%' OR away_team LIKE '%Арсенал%'")
mock_rows = c.fetchall()
print(f"Total found: {len(mock_rows)}")
for r in mock_rows:
    print(r)

# 2. Check for predictions associated with mock matches
if mock_rows:
    match_ids = [r[0] for r in mock_rows]
    q = f"SELECT id, match_id, source_id, predicted_outcome, odds FROM predictions WHERE match_id IN ({','.join(map(str, match_ids))})"
    c.execute(q)
    print("Predictions for mock matches:")
    for p in c.fetchall():
        print(p)

# 3. Check sources status
print("\n=== 2. SOURCES SUMMARY ===")
c.execute("SELECT id, name, source_type, is_active FROM sources")
for s in c.fetchall():
    s_id, s_name, s_type, s_active = s
    c.execute("SELECT count(*) FROM predictions WHERE source_id=?", (s_id,))
    count = c.fetchone()[0]
    c.execute("SELECT max(created_at) FROM predictions WHERE source_id=?", (s_id,))
    last_dt = c.fetchone()[0]
    print(f"Source #{s_id} [{s_name}] ({s_type}): {count} preds, last: {last_dt}, active: {s_active}")

# 4. Check today's matches
print("\n=== 3. TODAY MATCHES (2026-10-29) ===")
c.execute("SELECT count(*) FROM matches WHERE date(match_date) = '2026-10-29'")
print(f"Matches for 2026-10-29: {c.fetchone()[0]}")

c.execute("SELECT count(*) FROM predictions WHERE date(created_at) = '2026-10-29'")
print(f"Predictions for 2026-10-29: {c.fetchone()[0]}")

conn.close()
