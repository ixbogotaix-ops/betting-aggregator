import sqlite3
import datetime

conn = sqlite3.connect('/opt/betting_aggregator/backend/betting_db.sqlite')
c = conn.cursor()

# 1. Inspect Match Себако vs Манагуа
print("=== ИНСПЕКЦИЯ МАТЧА СЕБАКО vs МАНАГУА ===")
c.execute("SELECT id, sport_type, league, home_team, away_team, match_date, status, final_score_home, final_score_away FROM matches WHERE home_team LIKE '%Себако%' OR away_team LIKE '%Себако%'")
for r in c.fetchall():
    print("Match:", r)
    m_id = r[0]
    c.execute("SELECT p.id, s.name, p.predicted_outcome, p.odds, p.confidence_score, p.created_at FROM predictions p JOIN sources s ON p.source_id = s.id WHERE p.match_id=?", (m_id,))
    for p in c.fetchall():
        print("  Prediction:", p)

# 2. Inspect all matches for today (2026-10-29) with highest number of predictions
print("\n=== ТОП МАТЧЕЙ ПО КОЛИЧЕСТВУ ПРОГНОЗОВ НА 29 ОКТЯБРЯ ===")
c.execute("""
    SELECT m.id, m.sport_type, m.league, m.home_team, m.away_team, m.match_date, m.status, COUNT(p.id) as pred_count
    FROM matches m
    JOIN predictions p ON m.id = p.match_id
    WHERE date(m.match_date) = '2026-10-29'
    GROUP BY m.id
    ORDER BY pred_count DESC
    LIMIT 15
""")
for r in c.fetchall():
    print(r)

# 3. Check settlement service and missing scores
print("\n=== МАТЧИ ЗА СЕГОДНЯ, КОТОРЫЕ НАЧАЛИСЬ БОЛЕЕ 3 ЧАСОВ НАЗАД И НЕ ЗАВЕРШЕНЫ ===")
now_str = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
c.execute("""
    SELECT id, sport_type, league, home_team, away_team, match_date, status, final_score_home, final_score_away
    FROM matches
    WHERE date(match_date) = '2026-10-29' 
      AND match_date < datetime('now', '-3 hours')
      AND status != 'finished'
    LIMIT 10
""")
for r in c.fetchall():
    print(r)

conn.close()
