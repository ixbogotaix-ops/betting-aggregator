import logging
import asyncio
from typing import List
from thefuzz import fuzz
from unidecode import unidecode
import cloudscraper
from bs4 import BeautifulSoup

from app.database import AsyncSessionLocal
from app.models import Match, Source, Prediction
from sqlalchemy import select
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def clean_name(name: str) -> str:
    name = unidecode(name).lower()
    for char in ['-', '.', ',', 'fc', 'фк']:
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
        if max_score > best_score and max_score > 75:
            best_score = max_score
            best_match = rm
            
    return best_match

async def scrape_stavkatv():
    logger.info("Starting Stavka TV scraper...")
    scraper = cloudscraper.create_scraper()
    
    try:
        response = scraper.get('https://stavka.tv/predictions', timeout=30)
        html = response.text
    except Exception as e:
        logger.error(f"Error fetching Stavka TV: {e}")
        return
        
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.select('.PredictionsItem')
    
    logger.info(f"Found {len(cards)} prediction cards on Stavka TV.")
    
    async with AsyncSessionLocal() as session:
        # Check source
        res = await session.execute(select(Source).where(Source.name == "Stavka TV"))
        source = res.scalars().first()
        if not source:
            logger.error("Source 'Stavka TV' not found in database!")
            return
            
        result = await session.execute(select(Match).where(Match.status != "Finished"))
        real_matches = result.scalars().all()
        
        new_predictions = 0
        
        for card in cards:
            try:
                home_el = card.select_one('.team--home')
                away_el = card.select_one('.team--away')
                odds_el = card.select_one('.Rate')
                outcome_el = card.select_one('.outcome')
                
                if not (home_el and away_el and odds_el and outcome_el):
                    continue
                    
                team1 = home_el.text.strip()
                team2 = away_el.text.strip()
                odds_str = odds_el.text.strip()
                outcome_str = outcome_el.text.strip()
                
                try:
                    odds = float(odds_str)
                except:
                    odds = 1.0
                    
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
                            predicted_outcome=f"{outcome_str} (Stavka TV)",
                            odds=odds,
                            confidence_score=60.0,
                            created_at=datetime.now(timezone.utc)
                        )
                        session.add(pred)
                        new_predictions += 1
                        logger.info(f"Added Stavka TV prediction for {team1} vs {team2}: {outcome_str}")
            except Exception as e:
                logger.warning(f"Error parsing Stavka TV card: {e}")
                
        if new_predictions > 0:
            await session.commit()
            logger.info(f"Successfully saved {new_predictions} new predictions from Stavka TV!")
        else:
            logger.info("No new predictions matched from Stavka TV.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(scrape_stavkatv())
