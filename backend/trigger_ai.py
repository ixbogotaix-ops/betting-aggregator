import asyncio  
from app.database import AsyncSessionLocal  
from app.consensus import calculate_daily_top_bets  
from app.ai_analyzer import auto_analyze_matches_for_scraper  
from app.models import Match  
from sqlalchemy.future import select  
async def main():  
    async with AsyncSessionLocal() as session:  
        top_bets = await calculate_daily_top_bets(session, date_str='ALL')  
        ai_result = await auto_analyze_matches_for_scraper(top_bets)  
        if ai_result:  
            best_ids_dict = ai_result.get('bet_of_the_day_match_ids', {})  
            best_ids = [int(v) for v in best_ids_dict.values() if str(v).isdigit()] if isinstance(best_ids_dict, dict) else []  
            insights = ai_result.get('insights', {})  
            reasonings = ai_result.get('reasoning', {})  
            for t_bet in top_bets:  
                match_id = t_bet.match_id  
                stmt = select(Match).where(Match.id == match_id)  
                db_match = (await session.execute(stmt)).scalar_one_or_none()  
                if db_match:  
                    db_match.ai_insight = insights.get(str(match_id), '')  
                    db_match.cappers_reasoning = reasonings.get(str(match_id), '')  
                    if match_id in best_ids:  
                        db_match.is_bet_of_the_day = True  
            await session.commit()  
            print('AI Analysis complete. Best IDs:', best_ids)  
asyncio.run(main())  
