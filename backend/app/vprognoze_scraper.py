import logging
import asyncio
from typing import List, Dict, Any
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
        
        # прямая проверка
        score1 = (fuzz.partial_ratio(team1_clean, r_home) + fuzz.partial_ratio(team2_clean, r_away)) / 2
        # реверс (вдруг перепутаны местами)
        score2 = (fuzz.partial_ratio(team1_clean, r_away) + fuzz.partial_ratio(team2_clean, r_home)) / 2
        
        max_score = max(score1, score2)
        if max_score > best_score and max_score > 75:  # Порог 75
            best_score = max_score
            best_match = rm
            
    return best_match

async def scrape_vprognoze():
    logger.info("Starting Vprognoze scraper...")
    scraper = cloudscraper.create_scraper()
    
    try:
        response = scraper.get('https://vprognoze.ru/forecast/football/', timeout=30)
        html = response.text
        logger.info(f"Downloaded Vprognoze HTML: {len(html)} bytes, Status Code: {response.status_code}")
        open('vprognoze_debug.html', 'w', encoding='utf-8').write(html)
    except Exception as e:
        logger.error(f"Error fetching Vprognoze: {e}")
        return
        
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.select('.v3-forecast-card')
    
    logger.info(f"Found {len(cards)} prediction cards on Vprognoze.")
    
    async with AsyncSessionLocal() as session:
        # Get source ID for Vprognoze
        res = await session.execute(select(Source).where(Source.name == "Vprognoze"))
        source = res.scalars().first()
        if not source:
            logger.error("Source 'Vprognoze' not found in database! Make sure it was added.")
            return
            
        # Get all upcoming matches
        result = await session.execute(select(Match).where(Match.status != "Finished"))
        real_matches = result.scalars().all()
        
        new_predictions = 0
        
        for card in cards:
            try:
                teams_el = card.select_one('.v3-forecast-card-commands')
                if not teams_el:
                    continue
                teams_text = teams_el.text.strip().replace('\n', ' ')
                
                # Обычно разделяется через " - "
                parts = teams_text.split(' - ')
                if len(parts) != 2:
                    continue
                team1, team2 = parts[0].strip(), parts[1].strip()
                
                bets = card.select('.v3-forecast-card-bets__item')
                if len(bets) < 2:
                    continue
                    
                # Структура: bets[0] - odds, bets[1] - outcome, bets[2] - stake
                odds_str = bets[0].text.strip()
                outcome_str = bets[1].text.strip()
                
                try:
                    odds = float(odds_str)
                except:
                    odds = 1.0
                    
                matched_match = match_teams(team1, team2, real_matches)
                if matched_match:
                    # Check if prediction already exists
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
                            predicted_outcome=outcome_str.strip(),
                            odds=odds,
                            confidence_score=60.0,
                            created_at=datetime.now(timezone.utc)
                        )
                        session.add(pred)
                        new_predictions += 1
                        logger.info(f"Added Vprognoze prediction for {team1} vs {team2}: {outcome_str}")
            except Exception as e:
                logger.warning(f"Error parsing card: {e}")
                
        if new_predictions > 0:
            await session.commit()
            logger.info(f"Successfully saved {new_predictions} new predictions from Vprognoze!")
        else:
            logger.info("No new predictions matched from Vprognoze.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(scrape_vprognoze())
