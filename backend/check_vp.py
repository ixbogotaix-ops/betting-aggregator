import asyncio
from app.database import AsyncSessionLocal
from app.models import Match, Source, Prediction
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as s:
        vp = (await s.execute(select(Source).where(Source.name == 'Vprognoze'))).scalars().first()
        preds = (await s.execute(select(Prediction).where(Prediction.source_id == vp.id))).scalars().all()
        for p in preds:
            m = (await s.execute(select(Match).where(Match.id == p.match_id))).scalars().first()
            print(f"{m.home_team} vs {m.away_team} -> {p.predicted_outcome}")

asyncio.run(main())
