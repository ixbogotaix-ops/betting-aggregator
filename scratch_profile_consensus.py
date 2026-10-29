import asyncio
import time
import sys
import os

sys.path.insert(0, '/opt/betting_aggregator/backend')
from app.database import AsyncSessionLocal
from app.consensus import calculate_daily_top_bets

async def main():
    print("[*] Starting profiling of calculate_daily_top_bets...")
    t0 = time.time()
    async with AsyncSessionLocal() as session:
        t_db = time.time()
        print(f"[+] Session created in {t_db - t0:.3f}s")
        res = await calculate_daily_top_bets(session)
        t_end = time.time()
        print(f"[+] calculate_daily_top_bets finished in {t_end - t_db:.3f}s! Returned {len(res)} bets.")
        for b in res[:3]:
            print(f"  Rank {b.daily_rank}: {b.home_team} vs {b.away_team} ({b.slot_label}) | {b.recommended_outcome} ({b.average_odds})")

asyncio.run(main())
