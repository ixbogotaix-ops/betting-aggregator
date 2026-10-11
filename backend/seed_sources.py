import asyncio  
from app.database import AsyncSessionLocal  
from app.models import Source, SourceType  
from sqlalchemy import select  
TARGET_WEBSITES = ['Vprognoze', 'VseProSport', 'Bookmaker-Ratings', 'Legalbet', 'Stavka TV', 'Championat', 'Metaratings', 'OddsPortal', 'WhoScored', 'Forebet', 'Flashscore']  
TARGET_CHANNELS = ['legalbet', 'bookmaker_ratings', 'vprognoze', 'intelbet', 'stavka_tv', 'bet_itors', 'capper_control', 'odds_portal_ru', 'metaratings_ru', 'championat_com', 'football_hub_ru', 'capper_football', 'goal_forecast', 'euro_football_chat', 'russian_premier_league', 'champions_league_bets', 'tactical_board', 'corner_cards_bets', 'xG_football_analytics', 'foot_analytics_pro', 'ice_hockey_bets', 'khl_analytics_pro', 'nhl_expert_tips', 'puck_and_goal', 'tennis_expert_pro', 'court_side_bets', 'tennis_stat_lab', 'basket_analytics', 'nba_night_picks', 'volleyball_expert_bets', 'mma_ufc_predictions', 'smart_betting_lab', 'value_bets_channel', 'roi_tracker_bot', 'betting_strategy_ru', 'math_betting_club', 'pro_capper_union', 'sure_bets_monitor']  
async def main():  
    async with AsyncSessionLocal() as db:  
        # get existing names  
        res = await db.execute(select(Source.name))  
        existing = set(res.scalars().all())  
        for w in TARGET_WEBSITES:  
            if w not in existing:  
                db.add(Source(name=w, source_type=SourceType.prediction_site, is_active=True))  
        for c in TARGET_CHANNELS:  
            if c not in existing:  
                db.add(Source(name=c, source_type=SourceType.telegram_channel, is_active=True))  
        await db.commit()  
asyncio.run(main())  
