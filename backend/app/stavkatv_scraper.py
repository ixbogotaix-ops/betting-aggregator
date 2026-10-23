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
    if any(k in s for k in ["хоккей", "кхл", "нхл", "вхл", "мхл", "hockey", "nhl", "khl", "шайб", "буллит", "овертайм", "ска-", "нефтяник"]):
        return "Hockey"
    if any(k in s for k in ["баскетбол", "nba", "нба", "евролига", "втб", "basketball", "euroleague"]):
        return "Basketball"
    if any(k in s for k in ["теннис", "atp", "wta", "itf", "tennis", "сет", "гейм", "паолини", "картал", "джокович", "алькарас"]):
        return "Tennis"
    if any(k in s for k in ["mma", "ufc", "мма", "юфс", "бокс", "boxing", "боевых", "единоборств", "нокаут"]) or re.search(r'\bбо[яеий]\b', s):
        return "MMA"
    if any(k in s for k in ["esport", "киберспорт", "cs:go", "cs2", "dota", "valorant"]):
        return "Esports"
    return "Football"

def clean_name(name: str) -> str:
    name = unidecode(name).lower()
    for char in ['-', '.', ',', 'fc', 'фк', 'tc', 'sc', 'cf', 'bc', 'jk', 'бк']:
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
        
        # прямая проверка (обе команды обязаны совпасть!)
        sh1 = fuzz.token_set_ratio(team1_clean, r_home)
        sa1 = fuzz.token_set_ratio(team2_clean, r_away)
        score1 = (sh1 + sa1) / 2.0 if (sh1 >= 65 and sa1 >= 65) else 0.0
        
        # реверс (вдруг перепутаны местами)
        sh2 = fuzz.token_set_ratio(team1_clean, r_away)
        sa2 = fuzz.token_set_ratio(team2_clean, r_home)
        score2 = (sh2 + sa2) / 2.0 if (sh2 >= 65 and sa2 >= 65) else 0.0
        
        max_score = max(score1, score2)
        if max_score > 75 and max_score > best_score:
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
                    m_o = re.search(r'\b([1-9]\d*[\.,]\d{1,2})\b', odds_str)
                    odds = float(m_o.group(1).replace(',', '.')) if m_o else 1.85
                    
                matched_match = match_teams(team1, team2, real_matches)
                if not matched_match:
                    sport_name = detect_sport(card.text, teams=f"{team1} {team2}")
                    matched_match = Match(
                        sport_type=sport_name,
                        league="Линия экспертов",
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
                    reasoning_el = card.select_one('.prediction-text') or card.select_one('.PredictionsItem__text') or card.select_one('.description')
                    reasoning_text = reasoning_el.text.strip() if reasoning_el else card.text.strip()
                    pred = Prediction(
                        match_id=matched_match.id,
                        source_id=source.id,
                        predicted_outcome=outcome_str.strip(),
                        odds=odds,
                        confidence_score=75.0,
                        reasoning=reasoning_text[:600],
                        created_at=datetime.now(timezone.utc)
                    )
                    session.add(pred)
                    new_predictions += 1
                    logger.info(f"Added Stavka TV prediction for {team1} vs {team2}: {outcome_str} (odds={odds})")
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
