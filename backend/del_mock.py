import asyncio  
from app.database import AsyncSessionLocal  
from app.models import Source, Prediction  
from sqlalchemy import delete, select  
async def main():  
    async with AsyncSessionLocal() as db:  
        res = await db.execute(select(Source).where(Source.id < 30))  
        sources = res.scalars().all()  
        for s in sources:  
            await db.execute(delete(Prediction).where(Prediction.source_id == s.id))  
            await db.execute(delete(Source).where(Source.id == s.id))  
        await db.commit()  
asyncio.run(main())  
