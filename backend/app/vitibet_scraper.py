"""
Vitibet Scraper and Mathematical Matcher Service.
Scrapes mathematical algorithms, confidence indices, and exact projected scores from vitibet.com.
"""
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
from datetime import datetime
from thefuzz import fuzz
from unidecode import unidecode

logger = logging.getLogger("vitibet_scraper")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
}

_cache = {
    "matches": [],
    "updated_at": None
}

def scrape_vitibet_football() -> List[Dict[str, Any]]:
    """Scrapes football mathematical predictions, confidence index, and projected scores from Vitibet."""
    url = 'https://www.vitibet.com/index.php?clanek=quicktips&sekce=fotbal&lang=ru'
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code != 200:
            logger.warning(f"Vitibet returned status {r.status_code}")
            return []

        soup = BeautifulSoup(r.text, 'html.parser')
        rows = soup.find_all(class_='livescore-match-row')
        
        results = []
        for row in rows:
            try:
                teams_el = row.find_all(class_='livescore-team-name')
                if len(teams_el) < 2:
                    continue
                team1 = teams_el[0].get_text(strip=True)
                team2 = teams_el[1].get_text(strip=True)
                
                tip_el = row.find(class_='tip-indicator-circle')
                score_el = row.find(class_='livescore-score-combined')
                idx_el = row.find(class_='idx-val')

                tip = tip_el.get_text(strip=True) if tip_el else ""
                proj_score = score_el.get_text(strip=True) if score_el else ""
                idx_str = idx_el.get_text(strip=True) if idx_el else ""

                index_float = 0.0
                if idx_str:
                    try:
                        index_float = float(idx_str.replace('+', '').replace(',', '.'))
                    except ValueError:
                        pass

                results.append({
                    "team1": team1,
                    "team2": team2,
                    "tip": tip,
                    "proj_score": proj_score,
                    "index_str": idx_str,
                    "index_val": index_float
                })
            except Exception as e:
                continue

        logger.info(f"Scraped {len(results)} matches from Vitibet")
        return results

    except Exception as e:
        logger.error(f"Error scraping Vitibet: {e}")
        return []

def get_vitibet_cached(force: bool = False) -> List[Dict[str, Any]]:
    """Returns cached Vitibet predictions with 20 min TTL."""
    now = datetime.now()
    if (
        not force
        and _cache["updated_at"] is not None
        and _cache["matches"]
        and (now - _cache["updated_at"]).total_seconds() < 1200
    ):
        return _cache["matches"]

    matches = scrape_vitibet_football()
    if matches:
        _cache["matches"] = matches
        _cache["updated_at"] = now
    return _cache["matches"] or matches

def find_vitibet_match(team1: str, team2: str, viti_matches: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Fuzzy matches Robobet teams against Vitibet teams."""
    if not team1 or not team2 or not viti_matches:
        return None

    t1_clean = unidecode(team1).lower().strip()
    t2_clean = unidecode(team2).lower().strip()

    best_match = None
    best_score = 0.0

    for vm in viti_matches:
        vm1 = unidecode(vm["team1"]).lower().strip()
        vm2 = unidecode(vm["team2"]).lower().strip()

        score1 = fuzz.token_set_ratio(t1_clean, vm1)
        score2 = fuzz.token_set_ratio(t2_clean, vm2)
        total_score = (score1 + score2) / 2.0

        if total_score > 68 and total_score > best_score:
            best_score = total_score
            best_match = vm

    return best_match

def check_mathematical_consensus(robo_rec: str, viti_tip: str) -> bool:
    """Checks if Robobet and Vitibet recommendations agree mathematically."""
    if not robo_rec or not viti_tip:
        return False

    r = robo_rec.upper().strip().replace('Х', 'X')
    v = viti_tip.upper().strip().replace('Х', 'X')

    if r in ['П1', '1'] and v in ['1', '1X']:
        return True
    if r in ['П2', '2'] and v in ['2', 'X2']:
        return True
    if r in ['1X'] and v in ['1X', '1']:
        return True
    if r in ['X2'] and v in ['X2', '2']:
        return True
    if r in ['12'] and v in ['12', '1', '2']:
        return True
    if r in ['X', 'НИЧЬЯ'] and v in ['X']:
        return True

    return False
