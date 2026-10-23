"""
Zulubet Scraper and Mathematical Matcher Service.
Scrapes mathematical probabilities, algorithmic tips, and odds from zulubet.com.
Part of the Triple AI Consensus Engine (Robobet + Vitibet + Zulubet).
"""
import logging
import re
import cloudscraper
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
from datetime import datetime
from thefuzz import fuzz
from unidecode import unidecode

logger = logging.getLogger("zulubet_scraper")

_cache = {
    "matches": [],
    "updated_at": None
}

def scrape_zulubet_matches() -> List[Dict[str, Any]]:
    """
    Scrapes all mathematical predictions and probabilities from Zulubet.
    """
    url = "http://www.zulubet.com/"
    try:
        scraper = cloudscraper.create_scraper()
        r = scraper.get(url, timeout=12)
        if r.status_code != 200:
            logger.warning(f"Zulubet returned status {r.status_code}")
            return []

        soup = BeautifulSoup(r.content, "html.parser")
        rows = soup.find_all("tr")
        
        results = []
        for row in rows:
            try:
                cols = row.find_all("td")
                if len(cols) < 15:
                    continue

                teams_text = cols[1].get_text(strip=True)
                if " - " not in teams_text:
                    continue

                teams = teams_text.split(" - ")
                team1 = teams[0].strip()
                team2 = teams[1].strip()

                # Probabilities
                p1_str = re.sub(r'[^\d]', '', cols[6].get_text()) if len(cols) > 6 else ""
                px_str = re.sub(r'[^\d]', '', cols[7].get_text()) if len(cols) > 7 else ""
                p2_str = re.sub(r'[^\d]', '', cols[8].get_text()) if len(cols) > 8 else ""

                prob_1 = int(p1_str) if p1_str.isdigit() else 0
                prob_x = int(px_str) if px_str.isdigit() else 0
                prob_2 = int(p2_str) if p2_str.isdigit() else 0

                # Algorithmic Tip: '1', 'X', '2', '1X', 'X2', '12' (очищаем от префиксов минут live)
                tip_raw = cols[9].get_text(strip=True) if len(cols) > 9 else ""
                tip = re.sub(r'^[-\d\']+', '', tip_raw).strip()

                # Odds
                odds_1_str = cols[12].get_text(strip=True).replace(',', '.') if len(cols) > 12 else "1.0"
                odds_x_str = cols[13].get_text(strip=True).replace(',', '.') if len(cols) > 13 else "1.0"
                odds_2_str = cols[14].get_text(strip=True).replace(',', '.') if len(cols) > 14 else "1.0"

                try:
                    odds_1 = float(odds_1_str)
                except ValueError:
                    odds_1 = 1.0
                try:
                    odds_x = float(odds_x_str)
                except ValueError:
                    odds_x = 1.0
                try:
                    odds_2 = float(odds_2_str)
                except ValueError:
                    odds_2 = 1.0

                results.append({
                    "team1": team1,
                    "team2": team2,
                    "tip": tip,
                    "prob_1": prob_1,
                    "prob_x": prob_x,
                    "prob_2": prob_2,
                    "odds_1": odds_1,
                    "odds_x": odds_x,
                    "odds_2": odds_2
                })
            except Exception:
                continue

        logger.info(f"Scraped {len(results)} matches from Zulubet")
        return results

    except Exception as e:
        logger.error(f"Error scraping Zulubet: {e}")
        return []

def get_zulubet_cached(force: bool = False) -> List[Dict[str, Any]]:
    """Returns cached Zulubet predictions with 20 min TTL."""
    now = datetime.now()
    if (
        not force
        and _cache["updated_at"] is not None
        and _cache["matches"]
        and (now - _cache["updated_at"]).total_seconds() < 1200
    ):
        return _cache["matches"]

    matches = scrape_zulubet_matches()
    if matches:
        _cache["matches"] = matches
        _cache["updated_at"] = now
    return _cache["matches"] or matches

def find_zulubet_match(team1: str, team2: str, zulu_matches: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Fuzzy matches Robobet teams against Zulubet teams with strict two-sided verification."""
    if not team1 or not team2 or not zulu_matches:
        return None

    def clean_t(name: str) -> str:
        s = unidecode(name).lower()
        for noise in ['fc', 'fk', 'tc', 'sc', 'cf', 'bc', 'jk', 'фк', 'бк']:
            s = re.sub(rf'\b{noise}\b', '', s)
        return ' '.join(s.split())

    t1_clean = clean_t(team1)
    t2_clean = clean_t(team2)

    best_match = None
    best_score = 0.0

    for zm in zulu_matches:
        zm1 = clean_t(zm["team1"])
        zm2 = clean_t(zm["team2"])

        score1 = fuzz.token_set_ratio(t1_clean, zm1)
        score2 = fuzz.token_set_ratio(t2_clean, zm2)

        # Обе команды обязаны совпадать с порогом >= 70!
        if score1 >= 70 and score2 >= 70:
            total_score = (score1 + score2) / 2.0
            if total_score > 75 and total_score > best_score:
                best_score = total_score
                best_match = zm

    return best_match

def check_zulu_consensus(robobet_tip: str, zulu_tip: str) -> bool:
    """Verifies agreement between Robobet recommendation and Zulubet tip."""
    if not robobet_tip or not zulu_tip:
        return False

    r = robobet_tip.strip().upper().replace('Х', 'X')
    z = zulu_tip.strip().upper().replace('Х', 'X')

    if r == "П1" and z in ["1", "1X"]:
        return True
    if r == "П2" and z in ["2", "X2"]:
        return True
    if r in ["1X", "X1"] and z in ["1", "1X"]:
        return True
    if r in ["X2", "2X"] and z in ["2", "X2"]:
        return True
    if r in ["X", "НИЧЬЯ"] and z == "X":
        return True
    if r == "12" and z in ["1", "2", "12"]:
        return True

    return False
