import os
import logging
import requests
from datetime import datetime
import dateutil.parser
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv(override=True)

class SportsAPIClient:
    def __init__(self):
        self.api_key = os.getenv("SPORTS_API_KEY")
        self.base_url = "https://api.the-odds-api.com/v4/sports/upcoming/odds/"
        
    def fetch_today_matches(self):
        """
        Получает реальные матчи и базовые коэффициенты на сегодня.
        Возвращает список словарей с данными матчей.
        """
        if not self.api_key:
            logger.warning("SPORTS_API_KEY не задан в .env! API не будет работать.")
            return []
            
        params = {
            "apiKey": self.api_key,
            "regions": "eu",
            "markets": "h2h",
            "oddsFormat": "decimal",
            "dateFormat": "iso"
        }
        
        try:
            logger.info("Запрашиваем линию реальных матчей из The-Odds-API...")
            
            sports_to_fetch = [
                "upcoming", 
                "soccer_epl", 
                "soccer_spain_la_liga", 
                "basketball_nba", 
                "icehockey_nhl", 
                "soccer_italy_serie_a",
                "soccer_germany_bundesliga",
                "soccer_france_ligue_one",
                "soccer_uefa_champs_league",
                "soccer_uefa_europa_league",
                "soccer_england_championship",
                "basketball_euroleague",
                "icehockey_khl",
                "icehockey_sweden_allsvenskan",
                "tennis_atp_wimbledon",
                "tennis_atp_us_open",
                "tennis_atp_french_open",
                "tennis_atp_aus_open",
                "americanfootball_nfl",
                "mma_mixed_martial_arts",
                "cricket_test_match",
                "cricket_odi",
                "cricket_t20"
            ]
            matches = []
            
            for sport in sports_to_fetch:
                url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/"
                response = requests.get(url, params=params, timeout=15)
                
                if response.status_code != 200:
                    continue
                    
                data = response.json()
                
                from datetime import timezone, timedelta
                moscow_tz = timezone(timedelta(hours=3))
                now_moscow = datetime.now(moscow_tz).replace(tzinfo=None)

                for item in data:
                    match_time = dateutil.parser.isoparse(item["commence_time"])
                    if match_time.tzinfo is not None:
                        match_time_msk = match_time.astimezone(moscow_tz).replace(tzinfo=None)
                    else:
                        match_time_msk = match_time + timedelta(hours=3)

                    if (match_time_msk - now_moscow).days > 7:
                        continue
                    
                    favored_outcome = None
                    best_odds = 0.0
                    if "bookmakers" in item and len(item["bookmakers"]) > 0:
                        bookmaker = item["bookmakers"][0]
                        if "markets" in bookmaker and len(bookmaker["markets"]) > 0:
                            outcomes = bookmaker["markets"][0].get("outcomes", [])
                            if outcomes:
                                favored = min(outcomes, key=lambda x: x["price"])
                                favored_outcome = favored["name"]
                                best_odds = favored["price"]

                    matches.append({
                        "id": item["id"],
                        "sport": item["sport_title"],
                        "league": item["sport_key"],
                        "home": item["home_team"],
                        "away": item["away_team"],
                        "time": match_time_msk,
                        "favored_outcome": favored_outcome,
                        "best_odds": best_odds
                    })
                
            logger.info(f"Загружено {len(matches)} актуальных матчей из API.")
            return matches
            
        except Exception as e:
            logger.error(f"Сбой при работе с The-Odds-API: {e}")
            return []
