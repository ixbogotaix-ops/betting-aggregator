import logging
import asyncio
import re
from typing import List
from thefuzz import fuzz
from unidecode import unidecode
import cloudscraper
from bs4 import BeautifulSoup

from app.database import AsyncSessionLocal
from app.models import Match, Source, Prediction, MatchStatus
from sqlalchemy import select
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

def detect_sport(text: str = "", league: str = "", teams: str = "") -> str:
    s = f"{text} {league} {teams}".lower()
    if any(k in s for k in ["хоккей", "кхл", "нхл", "вхл", "мхл", "hockey", "nhl", "khl", "шайб", "буллит", "овертайм"]):
        return "Hockey"
    if any(k in s for k in ["баскетбол", "nba", "нба", "евролига", "втб", "basketball", "euroleague"]):
        return "Basketball"
    if any(k in s for k in ["теннис", "atp", "wta", "itf", "tennis", "сет", "гейм"]):
        return "Tennis"
    if any(k in s for k in ["mma", "ufc", "мма", "юфс", "бокс", "boxing", "бой"]):
        return "MMA"
    if any(k in s for k in ["esport", "киберспорт", "cs:go", "cs2", "dota", "valorant"]):
        return "Esports"
    return "Football"

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

async def scrape_legalbet():
    logger.info("Starting Legalbet scraper...")
    scraper = cloudscraper.create_scraper()
    
    try:
        response = scraper.get('https://legalbet.ru/tips/', timeout=30)
        html = response.text
    except Exception as e:
        logger.error(f"Error fetching Legalbet: {e}")
        return
        
    soup = BeautifulSoup(html, 'html.parser')
    forecasts = soup.select('.exp-forecast')
    
    logger.info(f"Found {len(forecasts)} prediction cards on Legalbet.")
    
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Source).where(Source.name == "Legalbet"))
        source = res.scalars().first()
        if not source:
            logger.error("Source 'Legalbet' not found in database!")
            return
            
        result = await session.execute(select(Match).where(Match.status != "Finished"))
        real_matches = result.scalars().all()
        
        new_predictions = 0
        
        for f in forecasts:
            try:
                # Extract text
                full_text = f.text.replace('\n', ' ')
                
                # Try to extract teams using regex "Прогноз на матч X — Y"
                match_info = re.search(r'Прогноз на матч (.*?) — (.*?)(?:\s\d{1,2}\s|\t|$)', full_text)
                if not match_info:
                    continue
                    
                team1 = match_info.group(1).strip()
                team2 = match_info.group(2).strip()
                
                # Extract odds
                odds_match = f.find(string=re.compile(r'^\d+\.\d+$'))
                odds_str = odds_match.strip() if odds_match else "1.0"
                try:
                    odds = float(odds_str)
                except:
                    m_o = re.search(r'\b([1-9]\d*[\.,]\d{1,2})\b', odds_str)
                    odds = float(m_o.group(1).replace(',', '.')) if m_o else 1.85
                    
                # Extract outcome
                outcome_el = f.select_one('.exp-forecast__bet-text')
                if not outcome_el:
                    continue
                outcome_str = outcome_el.text.strip().replace('\n', ' ')
                
                matched_match = match_teams(team1, team2, real_matches)
                if not matched_match:
                    sport_name = detect_sport(full_text, teams=f"{team1} {team2}")
                    matched_match = Match(
                        sport_type=sport_name,
                        league="Линия Legalbet",
                        home_team=team1,
                        away_team=team2,
                        match_date=datetime.now(timezone.utc) + timedelta(hours=3),
                        status=MatchStatus.upcoming
                    )
                    session.add(matched_match)
                    await session.flush()
                    real_matches.append(matched_match)

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
                        confidence_score=75.0,
                        reasoning=full_text.strip()[:600],
                        created_at=datetime.now(timezone.utc)
                    )
                    session.add(pred)
                    new_predictions += 1
                    logger.info(f"Added Legalbet prediction for {team1} vs {team2}: {outcome_str} (odds={odds})")
            except Exception as e:
                logger.warning(f"Error parsing Legalbet card: {e}")
                
        if new_predictions > 0:
            await session.commit()
            logger.info(f"Successfully saved {new_predictions} new predictions from Legalbet!")
        else:
            logger.info("No new predictions matched from Legalbet.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(scrape_legalbet())
