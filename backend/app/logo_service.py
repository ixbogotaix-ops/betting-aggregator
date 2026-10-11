"""
Сервис получения эмблем спортивных команд и флагов стран.
Использует базу TheSportsDB, ESPN CDN, FlagCDN и умный кэш.
"""
import urllib.request
import urllib.parse
import json
import logging
import re
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Кэш в оперативной памяти для быстрого отклика
_LOGO_CACHE: Dict[str, str] = {}

# Предустановленные эмблемы популярных клубов (высокое качество, мгновенная отдача)
KNOWN_TEAM_LOGOS = {
    # Футбол - Франция
    "marseille": "https://r2.thesportsdb.com/images/media/team/badge/c6bazh1779212287.png",
    "troyes": "https://r2.thesportsdb.com/images/media/team/badge/sl5kzg1766617559.png",
    "paris saint germain": "https://a.espncdn.com/i/teamlogos/soccer/500/160.png",
    "psg": "https://a.espncdn.com/i/teamlogos/soccer/500/160.png",
    "monaco": "https://a.espncdn.com/i/teamlogos/soccer/500/175.png",
    "lyon": "https://a.espncdn.com/i/teamlogos/soccer/500/167.png",
    "lille": "https://a.espncdn.com/i/teamlogos/soccer/500/166.png",
    "rennes": "https://a.espncdn.com/i/teamlogos/soccer/500/171.png",
    "angers": "https://a.espncdn.com/i/teamlogos/soccer/500/174.png",
    
    # Футбол - Англия
    "newcastle united": "https://a.espncdn.com/i/teamlogos/soccer/500/364.png",
    "newcastle": "https://a.espncdn.com/i/teamlogos/soccer/500/364.png",
    "coventry city": "https://r2.thesportsdb.com/images/media/team/badge/55u6l31599313271.png",
    "coventry": "https://r2.thesportsdb.com/images/media/team/badge/55u6l31599313271.png",
    "arsenal": "https://a.espncdn.com/i/teamlogos/soccer/500/359.png",
    "chelsea": "https://a.espncdn.com/i/teamlogos/soccer/500/363.png",
    "liverpool": "https://a.espncdn.com/i/teamlogos/soccer/500/364.png",
    "manchester united": "https://a.espncdn.com/i/teamlogos/soccer/500/360.png",
    "manchester city": "https://a.espncdn.com/i/teamlogos/soccer/500/382.png",
    "tottenham": "https://a.espncdn.com/i/teamlogos/soccer/500/367.png",

    # Хоккей - NHL
    "new york rangers": "https://a.espncdn.com/i/teamlogos/nhl/500/nyr.png",
    "vancouver canucks": "https://a.espncdn.com/i/teamlogos/nhl/500/van.png",
    "boston bruins": "https://a.espncdn.com/i/teamlogos/nhl/500/bos.png",
    "toronto maple leafs": "https://a.espncdn.com/i/teamlogos/nhl/500/tor.png",
    "edmonton oilers": "https://a.espncdn.com/i/teamlogos/nhl/500/edm.png",
    "florida panthers": "https://a.espncdn.com/i/teamlogos/nhl/500/fla.png",
    "vegas golden knights": "https://a.espncdn.com/i/teamlogos/nhl/500/vgk.png",
    "tampa bay lightning": "https://a.espncdn.com/i/teamlogos/nhl/500/tb.png",
    "washington capitals": "https://a.espncdn.com/i/teamlogos/nhl/500/wsh.png",

    # Американский футбол - NFL
    "green bay packers": "https://a.espncdn.com/i/teamlogos/nfl/500/gb.png",
    "chicago bears": "https://a.espncdn.com/i/teamlogos/nfl/500/chi.png",
    "new york giants": "https://a.espncdn.com/i/teamlogos/nfl/500/nyg.png",
    "new orleans saints": "https://a.espncdn.com/i/teamlogos/nfl/500/no.png",
    "kansas city chiefs": "https://a.espncdn.com/i/teamlogos/nfl/500/kc.png",
    "san francisco 49ers": "https://a.espncdn.com/i/teamlogos/nfl/500/sf.png",
    "dallas cowboys": "https://a.espncdn.com/i/teamlogos/nfl/500/dal.png",
    "philadelphia eagles": "https://a.espncdn.com/i/teamlogos/nfl/500/phi.png",

    # Баскетбол - NBA / Евролига
    "asvel lyon villeurbanne": "https://r2.thesportsdb.com/images/media/team/badge/10s47o1611139483.png",
    "asvel": "https://r2.thesportsdb.com/images/media/team/badge/10s47o1611139483.png",
    "kk crvena zvezda": "https://r2.thesportsdb.com/images/media/team/badge/osgmbz1781157114.png",
    "crvena zvezda": "https://r2.thesportsdb.com/images/media/team/badge/osgmbz1781157114.png",
    "los angeles lakers": "https://a.espncdn.com/i/teamlogos/nba/500/lal.png",
    "golden state warriors": "https://a.espncdn.com/i/teamlogos/nba/500/gsw.png",
    "boston celtics": "https://a.espncdn.com/i/teamlogos/nba/500/bos.png",
    "miami heat": "https://a.espncdn.com/i/teamlogos/nba/500/mia.png",
    "denver nuggets": "https://a.espncdn.com/i/teamlogos/nba/500/den.png",

    # Испания, Италия, Германия
    "real madrid": "https://a.espncdn.com/i/teamlogos/soccer/500/86.png",
    "barcelona": "https://a.espncdn.com/i/teamlogos/soccer/500/83.png",
    "atletico madrid": "https://a.espncdn.com/i/teamlogos/soccer/500/1068.png",
    "inter milan": "https://a.espncdn.com/i/teamlogos/soccer/500/110.png",
    "ac milan": "https://a.espncdn.com/i/teamlogos/soccer/500/103.png",
    "juventus": "https://a.espncdn.com/i/teamlogos/soccer/500/111.png",
    "bayern munich": "https://a.espncdn.com/i/teamlogos/soccer/500/132.png",
    "borussia dortmund": "https://a.espncdn.com/i/teamlogos/soccer/500/124.png",
}

def _clean_team_key(name: str) -> str:
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', name.lower())
    return " ".join(cleaned.split())

def get_team_logo(team_name: str, sport: str = "") -> str:
    """
    Возвращает прямую ссылку на прозрачную PNG эмблему команды.
    Проверяет предустановленную базу, кэш, затем TheSportsDB API, и в конце fallback.
    """
    if not team_name:
        return "https://ui-avatars.com/api/?name=Team&background=1e293b&color=38bdf8&size=128&bold=true&rounded=true"

    clean_key = _clean_team_key(team_name)

    # 1. Поиск по известным клубам
    if clean_key in KNOWN_TEAM_LOGOS:
        return KNOWN_TEAM_LOGOS[clean_key]

    for known_key, logo_url in KNOWN_TEAM_LOGOS.items():
        if known_key in clean_key or clean_key in known_key:
            return logo_url

    # 2. Проверка оперативного кэша
    if clean_key in _LOGO_CACHE:
        return _LOGO_CACHE[clean_key]

    # 3. Запрос в бесплатное API TheSportsDB
    try:
        query = urllib.parse.quote(team_name.split()[-1] if len(team_name.split()) > 2 else team_name)
        url = f"https://www.thesportsdb.com/api/v1/json/123/searchteams.php?t={query}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data and data.get("teams"):
                badge = data["teams"][0].get("strBadge")
                if badge and badge.startswith("http"):
                    _LOGO_CACHE[clean_key] = badge
                    return badge
    except Exception:
        pass

    # 4. Стильный Fallback с инициалами команды
    fallback_url = f"https://ui-avatars.com/api/?name={urllib.parse.quote(team_name)}&background=1e293b&color=38bdf8&size=128&bold=true&rounded=true"
    _LOGO_CACHE[clean_key] = fallback_url
    return fallback_url

def get_league_country(league: str = "", sport: str = "") -> Dict[str, str]:
    """
    Определяет страну, код флага для FlagCDN и флаг-эмодзи по лиге и виду спорта.
    """
    l_lower = (league or "").lower()
    s_lower = (sport or "").lower()
    combined = f"{l_lower} {s_lower}"

    # Франция
    if any(x in combined for x in ["france", "ligue 1", "ligue 2", "франци", "ligue_one"]):
        return {
            "name": "Франция",
            "code": "fr",
            "flag_url": "https://flagcdn.com/w40/fr.png",
            "emoji": "🇫🇷"
        }

    # Англия / Великобритания
    if any(x in combined for x in ["england", "epl", "premier", "championship", "англия"]):
        return {
            "name": "Англия",
            "code": "gb-eng",
            "flag_url": "https://flagcdn.com/w40/gb-eng.png",
            "emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"
        }

    # Испания
    if any(x in combined for x in ["spain", "la liga", "laliga", "испани"]):
        return {
            "name": "Испания",
            "code": "es",
            "flag_url": "https://flagcdn.com/w40/es.png",
            "emoji": "🇪🇸"
        }

    # Италия
    if any(x in combined for x in ["italy", "serie a", "serie_a", "италия"]):
        return {
            "name": "Италия",
            "code": "it",
            "flag_url": "https://flagcdn.com/w40/it.png",
            "emoji": "🇮🇹"
        }

    # Германия
    if any(x in combined for x in ["germany", "bundesliga", "германи"]):
        return {
            "name": "Германия",
            "code": "de",
            "flag_url": "https://flagcdn.com/w40/de.png",
            "emoji": "🇩🇪"
        }

    # США / Северная Америка (NHL, NFL, NBA, MLS)
    if any(x in combined for x in ["nhl", "nfl", "nba", "mls", "american", "сша"]):
        return {
            "name": "США",
            "code": "us",
            "flag_url": "https://flagcdn.com/w40/us.png",
            "emoji": "🇺🇸"
        }

    # Россия
    if any(x in combined for x in ["khl", "rpl", "кхл", "рпл", "росси"]):
        return {
            "name": "Россия",
            "code": "ru",
            "flag_url": "https://flagcdn.com/w40/ru.png",
            "emoji": "🇷🇺"
        }

    # Европа (Евролига, ЛЧ, ЛЕ)
    if any(x in combined for x in ["euroleague", "champions_league", "europa_league", "uefa", "европ"]):
        return {
            "name": "Европа",
            "code": "eu",
            "flag_url": "https://flagcdn.com/w40/eu.png",
            "emoji": "🇪🇺"
        }

    # ММА / Теннис / Международные
    if any(x in combined for x in ["mma", "ufc", "atp", "wta", "tennis", "турнир"]):
        return {
            "name": "Международный",
            "code": "un",
            "flag_url": "https://flagcdn.com/w40/un.png",
            "emoji": "🌍"
        }

    # По умолчанию
    return {
        "name": "Спорт",
        "code": "un",
        "flag_url": "https://flagcdn.com/w40/un.png",
        "emoji": "🌐"
    }
