import sqlite3

conn = sqlite3.connect('/opt/betting_aggregator/backend/betting_db.sqlite')
c = conn.cursor()

c.execute("""
    SELECT m.id, m.sport_type, m.league, m.home_team, m.away_team, m.match_date, m.status, 
           p.id, s.name, p.predicted_outcome, p.odds, p.confidence_score, p.created_at
    FROM matches m 
    LEFT JOIN predictions p ON m.id = p.match_id 
    LEFT JOIN sources s ON p.source_id = s.id 
    WHERE m.id = 3092
""")
for r in c.fetchall():
    print(r)

conn.close()
