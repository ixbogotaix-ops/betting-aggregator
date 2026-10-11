import logging
import asyncio
import re
from typing import List
from thefuzz import fuzz
from unidecode import unidecode
import cloudscraper
from bs4 import BeautifulSoup

from app.database import AsyncSessionLocal
from app.models import Match, Source, Prediction, SourceType
from sqlalchemy import select
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def clean_name(name: str) -> str:
    name = unidecode(name).lower()
    for char in ['-', '.', ',', 'fc', 'фк', '«', '»']:
        name = name.replace(char, ' ')
    return ' '.join(name.split())

def match_teams(team1: str, team2: str, real_matches: List[Match]) -> Match:
    team1_clean = clean_name(team1)
    team2_clean = clean_name(team2)
    
    best_match = None
    best_score = 0
    
    for rm in real_matches:
        r_home = clean_name(rm.home_team)
        r_away = clean_name(rm.away_team)
        
        score1 = (fuzz.partial_ratio(team1_clean, r_home) + fuzz.partial_ratio(team2_clean, r_away)) / 2
        score2 = (fuzz.partial_ratio(team1_clean, r_away) + fuzz.partial_ratio(team2_clean, r_home)) / 2
        
        max_score = max(score1, score2)
        if max_score > 75 and max_score > best_score:
            best_score = max_score
            best_match = rm
            
    return best_match

async def scrape_bookmaker_ratings():
    logger.info("Starting Bookmaker-Ratings scraper...")
    scraper = cloudscraper.create_scraper()
    
    try:
        response = scraper.get('https://bookmaker-ratings.ru/tips/', timeout=30)
        html = response.text
    except Exception as e:
        logger.error(f"Error fetching Bookmaker-Ratings: {e}")
        return
        
    soup = BeautifulSoup(html, 'html.parser')
    articles = soup.select('article')
    
    logger.info(f"Found {len(articles)} prediction cards on Bookmaker-Ratings.")
    
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Source).where(Source.name.ilike("bookmaker-ratings%"), Source.source_type == SourceType.prediction_site))
        source = res.scalars().first()
        if not source:
            res = await session.execute(select(Source).where(Source.name == "Bookmaker-Ratings"))
            source = res.scalars().first()
        if not source:
            logger.error("Source 'Bookmaker-Ratings' not found in database!")
            return
            
        result = await session.execute(select(Match).where(Match.status != "Finished"))
        real_matches = result.scalars().all()
        
        new_predictions = 0
        
        for a in articles:
            try:
                strings = list(a.stripped_strings)
                if len(strings) < 6:
                    continue
                    
                odds_str = strings[-1]
                outcome_str = strings[-2]
                
                try:
                    odds = float(odds_str)
                except:
                    continue
                    
                # Look for teams
                t1_str = strings[-5]
                if '—' in t1_str or '-' in t1_str:
                    sep = '—' if '—' in t1_str else '-'
                    parts = t1_str.split(sep)
                    team1 = parts[0].strip()
                    team2 = parts[1].strip()
                else:
                    team2 = strings[-5].strip()
                    team1 = strings[-6].strip()
                    
                matched_match = match_teams(team1, team2, real_matches)
                if matched_match:
                    existing = await session.execute(
                        select(Prediction).where(
                            Prediction.match_id == matched_match.id,
                            Prediction.source_id == source.id
                        )
                    )
                    if existing.scalars().first() is None:
                        pred = Prediction(
                            match_id=matched_match.id,
                            source_id=source.id,
                            predicted_outcome=f"{outcome_str} (BR)",
                            odds=odds,
                            confidence_score=60.0,
                            created_at=datetime.now(timezone.utc)
                        )
                        session.add(pred)
                        new_predictions += 1
                        logger.info(f"Added BR prediction for {team1} vs {team2}: {outcome_str}")
            except Exception as e:
                logger.warning(f"Error parsing BR card: {e}")
                
        if new_predictions > 0:
            await session.commit()
            logger.info(f"Successfully saved {new_predictions} new predictions from Bookmaker-Ratings!")
        else:
            logger.info("No new predictions matched from Bookmaker-Ratings.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(scrape_bookmaker_ratings())
