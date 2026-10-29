"""
Сервис получения эмблем спортивных команд и флагов стран.
Использует высококачественные CDN (ESPN, TheSportsDB, FlagCDN),
локальный кэш на диске и алгоритм интеллектуальной нормализации названий.
"""
import urllib.request
import urllib.parse
import json
import logging
import re
import os
import unicodedata
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Путь к файлу постоянного кэша на диске
CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logos_cache.json")

# Кэш в оперативной памяти
_LOGO_CACHE: Dict[str, str] = {}

def _load_disk_cache():
    global _LOGO_CACHE
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # Отфильтровываем старые ui-avatars из кэша
                    valid = {k: v for k, v in data.items() if "ui-avatars.com" not in v}
                    _LOGO_CACHE.update(valid)
                    logger.info(f"Загружено {len(_LOGO_CACHE)} эмблем из дискового кэша")
        except Exception as e:
            logger.warning(f"Ошибка загрузки дискового кэша эмблем: {e}")

def _save_to_disk_cache(key: str, url: str):
    global _LOGO_CACHE
    if not url or "ui-avatars.com" in url:
        return
    _LOGO_CACHE[key] = url
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_LOGO_CACHE, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Ошибка сохранения эмблемы в дисковый кэш: {e}")

_load_disk_cache()

# Предустановленные официальные эмблемы (ESPN CDN & TheSportsDB CDN)
KNOWN_TEAM_LOGOS = {
    # --- Топ-3 Ставки Дня (сегодняшние и актуальные клубы) ---
    "аль-шулла": "https://upload.wikimedia.org/wikipedia/en/0/0c/Al_Shoulla_FC_logo.png",
    "al-shoulla": "https://upload.wikimedia.org/wikipedia/en/0/0c/Al_Shoulla_FC_logo.png",
    "al shoulla": "https://upload.wikimedia.org/wikipedia/en/0/0c/Al_Shoulla_FC_logo.png",
    "аль шула": "https://upload.wikimedia.org/wikipedia/en/0/0c/Al_Shoulla_FC_logo.png",
    "shoulla": "https://upload.wikimedia.org/wikipedia/en/0/0c/Al_Shoulla_FC_logo.png",

    "аль-вашм": "https://www.saff.com.sa/uploadcenter/saffteamlarge1661723269.png",
    "al-washm": "https://www.saff.com.sa/uploadcenter/saffteamlarge1661723269.png",
    "al washm": "https://www.saff.com.sa/uploadcenter/saffteamlarge1661723269.png",
    "аль вашм": "https://www.saff.com.sa/uploadcenter/saffteamlarge1661723269.png",
    "washm": "https://www.saff.com.sa/uploadcenter/saffteamlarge1661723269.png",

    "хантерс": "https://upload.wikimedia.org/wikipedia/en/e/e2/Hunters_FC_logo.png",
    "hunters": "https://upload.wikimedia.org/wikipedia/en/e/e2/Hunters_FC_logo.png",
    "hunters fc": "https://upload.wikimedia.org/wikipedia/en/e/e2/Hunters_FC_logo.png",

    "сентрал сталлионс": "https://upload.wikimedia.org/wikipedia/en/a/ac/Central_Stallions_FC_Logo.png",
    "central stallions": "https://upload.wikimedia.org/wikipedia/en/a/ac/Central_Stallions_FC_Logo.png",
    "central stallions fc": "https://upload.wikimedia.org/wikipedia/en/a/ac/Central_Stallions_FC_Logo.png",
    "stallions": "https://upload.wikimedia.org/wikipedia/en/a/ac/Central_Stallions_FC_Logo.png",
    "тюв буганууд": "https://upload.wikimedia.org/wikipedia/en/a/ac/Central_Stallions_FC_Logo.png",
    "tuv buganuud": "https://upload.wikimedia.org/wikipedia/en/a/ac/Central_Stallions_FC_Logo.png",

    "каса пиа": "https://a.espncdn.com/i/teamlogos/soccer/500/21581.png",
    "casa pia": "https://a.espncdn.com/i/teamlogos/soccer/500/21581.png",
    "casa pia ac": "https://a.espncdn.com/i/teamlogos/soccer/500/21581.png",

    "спортинг": "https://a.espncdn.com/i/teamlogos/soccer/500/2250.png",
    "спортинг лиссабон": "https://a.espncdn.com/i/teamlogos/soccer/500/2250.png",
    "sporting cp": "https://a.espncdn.com/i/teamlogos/soccer/500/2250.png",
    "sporting lisbon": "https://a.espncdn.com/i/teamlogos/soccer/500/2250.png",

    # --- Трек-рекорд и архивные матчи ---
    "рыбакина": "https://a.espncdn.com/i/headshots/tennis/players/full/3126.png",
    "елена рыбакина": "https://a.espncdn.com/i/headshots/tennis/players/full/3126.png",
    "elena rybakina": "https://a.espncdn.com/i/headshots/tennis/players/full/3126.png",
    "путинцева": "https://a.espncdn.com/i/headshots/tennis/players/full/1802.png",
    "юлия путинцева": "https://a.espncdn.com/i/headshots/tennis/players/full/1802.png",
    "yulia putintseva": "https://a.espncdn.com/i/headshots/tennis/players/full/1802.png",
    "сент-луис блюз": "https://a.espncdn.com/i/teamlogos/nhl/500/stl.png",
    "st louis blues": "https://a.espncdn.com/i/teamlogos/nhl/500/stl.png",
    "монреаль канадиенс": "https://a.espncdn.com/i/teamlogos/nhl/500/mtl.png",
    "montreal canadiens": "https://a.espncdn.com/i/teamlogos/nhl/500/mtl.png",

    # --- Другие популярные клубы ---
    "абха": "https://a.espncdn.com/i/teamlogos/soccer/500/19532.png",
    "abha": "https://a.espncdn.com/i/teamlogos/soccer/500/19532.png",
    "аделаида юнайтед": "https://a.espncdn.com/i/teamlogos/soccer/500/3932.png",
    "adelaide united": "https://a.espncdn.com/i/teamlogos/soccer/500/3932.png",
    "сеара": "https://a.espncdn.com/i/teamlogos/soccer/500/6078.png",
    "ceara": "https://a.espncdn.com/i/teamlogos/soccer/500/6078.png",
    "сантос": "https://a.espncdn.com/i/teamlogos/soccer/500/2674.png",
    "santos": "https://a.espncdn.com/i/teamlogos/soccer/500/2674.png",
    "атлетико минейро": "https://a.espncdn.com/i/teamlogos/soccer/500/3445.png",
    "atletico mineiro": "https://a.espncdn.com/i/teamlogos/soccer/500/3445.png",
    "крузейро": "https://a.espncdn.com/i/teamlogos/soccer/500/3446.png",
    "cruzeiro": "https://a.espncdn.com/i/teamlogos/soccer/500/3446.png",
    "бостон брюинз": "https://a.espncdn.com/i/teamlogos/nhl/500/bos.png",
    "boston bruins": "https://a.espncdn.com/i/teamlogos/nhl/500/bos.png",
    "кливленд кавальерс": "https://a.espncdn.com/i/teamlogos/nba/500/cle.png",
    "cleveland cavaliers": "https://a.espncdn.com/i/teamlogos/nba/500/cle.png",

    # --- Киберспорт ---
    "mouz": "https://img-cdn.hltv.org/teamlogo/k1k_nO29XF1wB4T-sBwD2i.png?ixlib=java-2.1.0&s=1c67e813a3ea5a60e1ad6d7e29bb37fe",
    "liquid": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/esports/500/teamliquid.png",
    "team liquid": "https://a.espncdn.com/combiner/i?img=/i/teamlogos/esports/500/teamliquid.png",
    "eternal fire": "https://img-cdn.hltv.org/teamlogo/v1V0vLhGj9Wl1zK_X9R7dY.png?ixlib=java-2.1.0&s=a49e9c8bc460eece7f642457c1ecde0f",
    "spirit": "https://img-cdn.hltv.org/teamlogo/8jP2lQJj042F7Yx9Qp6N_L.png?ixlib=java-2.1.0&s=e60bf764f5e7c2a71f005e83ec55172f",
    "team spirit": "https://img-cdn.hltv.org/teamlogo/8jP2lQJj042F7Yx9Qp6N_L.png?ixlib=java-2.1.0&s=e60bf764f5e7c2a71f005e83ec55172f",
    "nemiga": "https://img-cdn.hltv.org/teamlogo/qCflR529iYm_vH661k1_dZ.png?ixlib=java-2.1.0&s=47b777a8848dcf7d7da8fb15ba5fa095",
    "parivision": "https://img-cdn.hltv.org/teamlogo/zK16k7G_y08iL_mZ6E74_M.png?ixlib=java-2.1.0&s=f366184d081f26f6eb8b75f8f533925c",
    # --- Американский футбол NFL (Все 32 команды) ---
    "arizona cardinals": "https://a.espncdn.com/i/teamlogos/nfl/500/ari.png",
    "atlanta falcons": "https://a.espncdn.com/i/teamlogos/nfl/500/atl.png",
    "baltimore ravens": "https://a.espncdn.com/i/teamlogos/nfl/500/bal.png",
    "buffalo bills": "https://a.espncdn.com/i/teamlogos/nfl/500/buf.png",
    "carolina panthers": "https://a.espncdn.com/i/teamlogos/nfl/500/car.png",
    "chicago bears": "https://a.espncdn.com/i/teamlogos/nfl/500/chi.png",
    "cincinnati bengals": "https://a.espncdn.com/i/teamlogos/nfl/500/cin.png",
    "cleveland browns": "https://a.espncdn.com/i/teamlogos/nfl/500/cle.png",
    "dallas cowboys": "https://a.espncdn.com/i/teamlogos/nfl/500/dal.png",
    "denver broncos": "https://a.espncdn.com/i/teamlogos/nfl/500/den.png",
    "detroit lions": "https://a.espncdn.com/i/teamlogos/nfl/500/det.png",
    "green bay packers": "https://a.espncdn.com/i/teamlogos/nfl/500/gb.png",
    "houston texans": "https://a.espncdn.com/i/teamlogos/nfl/500/hou.png",
    "indianapolis colts": "https://a.espncdn.com/i/teamlogos/nfl/500/ind.png",
    "jacksonville jaguars": "https://a.espncdn.com/i/teamlogos/nfl/500/jax.png",
    "kansas city chiefs": "https://a.espncdn.com/i/teamlogos/nfl/500/kc.png",
    "las vegas raiders": "https://a.espncdn.com/i/teamlogos/nfl/500/lv.png",
    "los angeles chargers": "https://a.espncdn.com/i/teamlogos/nfl/500/lac.png",
    "los angeles rams": "https://a.espncdn.com/i/teamlogos/nfl/500/lar.png",
    "miami dolphins": "https://a.espncdn.com/i/teamlogos/nfl/500/mia.png",
    "minnesota vikings": "https://a.espncdn.com/i/teamlogos/nfl/500/min.png",
    "new england patriots": "https://a.espncdn.com/i/teamlogos/nfl/500/ne.png",
    "new orleans saints": "https://a.espncdn.com/i/teamlogos/nfl/500/no.png",
    "new york giants": "https://a.espncdn.com/i/teamlogos/nfl/500/nyg.png",
    "new york jets": "https://a.espncdn.com/i/teamlogos/nfl/500/nyj.png",
    "philadelphia eagles": "https://a.espncdn.com/i/teamlogos/nfl/500/phi.png",
    "pittsburgh steelers": "https://a.espncdn.com/i/teamlogos/nfl/500/pit.png",
    "san francisco 49ers": "https://a.espncdn.com/i/teamlogos/nfl/500/sf.png",
    "seattle seahawks": "https://a.espncdn.com/i/teamlogos/nfl/500/sea.png",
    "tampa bay buccaneers": "https://a.espncdn.com/i/teamlogos/nfl/500/tb.png",
    "tennessee titans": "https://a.espncdn.com/i/teamlogos/nfl/500/ten.png",
    "washington commanders": "https://a.espncdn.com/i/teamlogos/nfl/500/wsh.png",

    # --- Англия (Premier League & Championship) ---
    "arsenal": "https://a.espncdn.com/i/teamlogos/soccer/500/359.png",
    "aston villa": "https://a.espncdn.com/i/teamlogos/soccer/500/362.png",
    "brentford": "https://a.espncdn.com/i/teamlogos/soccer/500/337.png",
    "brighton": "https://a.espncdn.com/i/teamlogos/soccer/500/331.png",
    "brighton and hove albion": "https://a.espncdn.com/i/teamlogos/soccer/500/331.png",
    "bournemouth": "https://a.espncdn.com/i/teamlogos/soccer/500/349.png",
    "chelsea": "https://a.espncdn.com/i/teamlogos/soccer/500/363.png",
    "crystal palace": "https://a.espncdn.com/i/teamlogos/soccer/500/384.png",
    "everton": "https://a.espncdn.com/i/teamlogos/soccer/500/368.png",
    "fulham": "https://a.espncdn.com/i/teamlogos/soccer/500/370.png",
    "ipswich": "https://a.espncdn.com/i/teamlogos/soccer/500/375.png",
    "ipswich town": "https://a.espncdn.com/i/teamlogos/soccer/500/375.png",
    "leicester": "https://a.espncdn.com/i/teamlogos/soccer/500/375.png",
    "liverpool": "https://r2.thesportsdb.com/images/media/team/badge/kfaher1737969724.png",
    "manchester city": "https://a.espncdn.com/i/teamlogos/soccer/500/382.png",
    "man city": "https://a.espncdn.com/i/teamlogos/soccer/500/382.png",
    "manchester united": "https://a.espncdn.com/i/teamlogos/soccer/500/360.png",
    "man utd": "https://a.espncdn.com/i/teamlogos/soccer/500/360.png",
    "newcastle": "https://a.espncdn.com/i/teamlogos/soccer/500/364.png",
    "newcastle united": "https://a.espncdn.com/i/teamlogos/soccer/500/364.png",
    "nottingham forest": "https://a.espncdn.com/i/teamlogos/soccer/500/393.png",
    "nottingham": "https://a.espncdn.com/i/teamlogos/soccer/500/393.png",
    "southampton": "https://a.espncdn.com/i/teamlogos/soccer/500/376.png",
    "tottenham": "https://a.espncdn.com/i/teamlogos/soccer/500/367.png",
    "tottenham hotspur": "https://a.espncdn.com/i/teamlogos/soccer/500/367.png",
    "west ham": "https://a.espncdn.com/i/teamlogos/soccer/500/371.png",
    "west ham united": "https://a.espncdn.com/i/teamlogos/soccer/500/371.png",
    "wolverhampton": "https://a.espncdn.com/i/teamlogos/soccer/500/380.png",
    "wolves": "https://a.espncdn.com/i/teamlogos/soccer/500/380.png",
    "leeds united": "https://a.espncdn.com/i/teamlogos/soccer/500/357.png",
    "leeds": "https://a.espncdn.com/i/teamlogos/soccer/500/357.png",
    "hull city": "https://a.espncdn.com/i/teamlogos/soccer/500/306.png",
    "coventry city": "https://a.espncdn.com/i/teamlogos/soccer/500/389.png",

    # --- Испания (La Liga & Segunda) ---
    "real madrid": "https://a.espncdn.com/i/teamlogos/soccer/500/86.png",
    "barcelona": "https://a.espncdn.com/i/teamlogos/soccer/500/83.png",
    "atletico madrid": "https://a.espncdn.com/i/teamlogos/soccer/500/1068.png",
    "athletic bilbao": "https://r2.thesportsdb.com/images/media/team/badge/myl7c31677056352.png",
    "athletic club": "https://r2.thesportsdb.com/images/media/team/badge/myl7c31677056352.png",
    "real sociedad": "https://a.espncdn.com/i/teamlogos/soccer/500/89.png",
    "real betis": "https://a.espncdn.com/i/teamlogos/soccer/500/244.png",
    "betis": "https://a.espncdn.com/i/teamlogos/soccer/500/244.png",
    "villarreal": "https://a.espncdn.com/i/teamlogos/soccer/500/102.png",
    "valencia": "https://a.espncdn.com/i/teamlogos/soccer/500/94.png",
    "sevilla": "https://a.espncdn.com/i/teamlogos/soccer/500/243.png",
    "girona": "https://a.espncdn.com/i/teamlogos/soccer/500/9812.png",
    "celta vigo": "https://a.espncdn.com/i/teamlogos/soccer/500/85.png",
    "celta": "https://a.espncdn.com/i/teamlogos/soccer/500/85.png",
    "сельта": "https://a.espncdn.com/i/teamlogos/soccer/500/85.png",
    "сельта виго": "https://a.espncdn.com/i/teamlogos/soccer/500/85.png",
    "osasuna": "https://a.espncdn.com/i/teamlogos/soccer/500/97.png",
    "ca osasuna": "https://a.espncdn.com/i/teamlogos/soccer/500/97.png",
    "getafe": "https://r2.thesportsdb.com/images/media/team/badge/eyh2891655594452.png",
    "хетафе": "https://r2.thesportsdb.com/images/media/team/badge/eyh2891655594452.png",
    "universitatea craiova": "https://r2.thesportsdb.com/images/media/team/badge/1jdz2y1579793710.png",
    "кс университатя крайова": "https://r2.thesportsdb.com/images/media/team/badge/1jdz2y1579793710.png",
    "университатя крайова": "https://r2.thesportsdb.com/images/media/team/badge/1jdz2y1579793710.png",
    "крайова": "https://r2.thesportsdb.com/images/media/team/badge/1jdz2y1579793710.png",
    "craiova": "https://r2.thesportsdb.com/images/media/team/badge/1jdz2y1579793710.png",
    "rayo vallecano": "https://a.espncdn.com/i/teamlogos/soccer/500/101.png",
    "alaves": "https://a.espncdn.com/i/teamlogos/soccer/500/96.png",
    "deportivo alaves": "https://a.espncdn.com/i/teamlogos/soccer/500/96.png",
    "espanyol": "https://a.espncdn.com/i/teamlogos/soccer/500/88.png",
    "mallorca": "https://a.espncdn.com/i/teamlogos/soccer/500/84.png",
    "las palmas": "https://a.espncdn.com/i/teamlogos/soccer/500/90.png",
    "leganes": "https://r2.thesportsdb.com/images/media/team/badge/tm0adr1616443898.png",
    "valladolid": "https://a.espncdn.com/i/teamlogos/soccer/500/100.png",
    "levante": "https://a.espncdn.com/i/teamlogos/soccer/500/91.png",
    "malaga": "https://a.espncdn.com/i/teamlogos/soccer/500/92.png",
    "deportivo la coruna": "https://a.espncdn.com/i/teamlogos/soccer/500/87.png",
    "deportivo": "https://a.espncdn.com/i/teamlogos/soccer/500/87.png",
    "racing santander": "https://a.espncdn.com/i/teamlogos/soccer/500/98.png",
    "real racing club de santander": "https://a.espncdn.com/i/teamlogos/soccer/500/98.png",
    "elche": "https://a.espncdn.com/i/teamlogos/soccer/500/3751.png",
    "elche cf": "https://a.espncdn.com/i/teamlogos/soccer/500/3751.png",

    # --- Италия (Serie A & Serie B) ---
    "inter milan": "https://a.espncdn.com/i/teamlogos/soccer/500/110.png",
    "inter": "https://a.espncdn.com/i/teamlogos/soccer/500/110.png",
    "интер": "https://a.espncdn.com/i/teamlogos/soccer/500/110.png",
    "интер милан": "https://a.espncdn.com/i/teamlogos/soccer/500/110.png",
    "ac milan": "https://a.espncdn.com/i/teamlogos/soccer/500/103.png",
    "milan": "https://a.espncdn.com/i/teamlogos/soccer/500/103.png",
    "милан": "https://a.espncdn.com/i/teamlogos/soccer/500/103.png",
    "juventus": "https://a.espncdn.com/i/teamlogos/soccer/500/111.png",
    "ювентус": "https://a.espncdn.com/i/teamlogos/soccer/500/111.png",
    "napoli": "https://a.espncdn.com/i/teamlogos/soccer/500/114.png",
    "наполи": "https://a.espncdn.com/i/teamlogos/soccer/500/114.png",
    "roma": "https://a.espncdn.com/i/teamlogos/soccer/500/104.png",
    "рома": "https://a.espncdn.com/i/teamlogos/soccer/500/104.png",
    "lazio": "https://a.espncdn.com/i/teamlogos/soccer/500/112.png",
    "лацио": "https://a.espncdn.com/i/teamlogos/soccer/500/112.png",
    "atalanta": "https://a.espncdn.com/i/teamlogos/soccer/500/107.png",
    "fiorentina": "https://a.espncdn.com/i/teamlogos/soccer/500/109.png",
    "bologna": "https://a.espncdn.com/i/teamlogos/soccer/500/108.png",
    "torino": "https://a.espncdn.com/i/teamlogos/soccer/500/239.png",
    "genoa": "https://a.espncdn.com/i/teamlogos/soccer/500/3263.png",
    "monza": "https://r2.thesportsdb.com/images/media/team/badge/bxearg1603170113.png",
    "parma": "https://a.espncdn.com/i/teamlogos/soccer/500/115.png",
    "udinese": "https://a.espncdn.com/i/teamlogos/soccer/500/118.png",
    "cagliari": "https://a.espncdn.com/i/teamlogos/soccer/500/2925.png",
    "empoli": "https://a.espncdn.com/i/teamlogos/soccer/500/2698.png",
    "verona": "https://a.espncdn.com/i/teamlogos/soccer/500/119.png",
    "hellas verona": "https://a.espncdn.com/i/teamlogos/soccer/500/119.png",
    "lecce": "https://a.espncdn.com/i/teamlogos/soccer/500/113.png",
    "como": "https://r2.thesportsdb.com/images/media/team/badge/02x81t1627405841.png",
    "como 1907": "https://r2.thesportsdb.com/images/media/team/badge/02x81t1627405841.png",
    "venezia": "https://r2.thesportsdb.com/images/media/team/badge/vbiget1781026964.png",
    "sassuolo": "https://r2.thesportsdb.com/images/media/team/badge/xystvp1448806138.png",
    "frosinone": "https://a.espncdn.com/i/teamlogos/soccer/500/3874.png",

    # --- Германия (Bundesliga & 2. Bundesliga) ---
    "bayern munich": "https://r2.thesportsdb.com/images/media/team/badge/01ogkh1716960412.png",
    "bayern munchen": "https://r2.thesportsdb.com/images/media/team/badge/01ogkh1716960412.png",
    "bayern": "https://r2.thesportsdb.com/images/media/team/badge/01ogkh1716960412.png",
    "borussia dortmund": "https://a.espncdn.com/i/teamlogos/soccer/500/124.png",
    "dortmund": "https://a.espncdn.com/i/teamlogos/soccer/500/124.png",
    "bayer leverkusen": "https://a.espncdn.com/i/teamlogos/soccer/500/131.png",
    "leverkusen": "https://a.espncdn.com/i/teamlogos/soccer/500/131.png",
    "rb leipzig": "https://a.espncdn.com/i/teamlogos/soccer/500/11420.png",
    "eintracht frankfurt": "https://a.espncdn.com/i/teamlogos/soccer/500/125.png",
    "frankfurt": "https://a.espncdn.com/i/teamlogos/soccer/500/125.png",
    "stuttgart": "https://a.espncdn.com/i/teamlogos/soccer/500/134.png",
    "vfb stuttgart": "https://a.espncdn.com/i/teamlogos/soccer/500/134.png",
    "freiburg": "https://r2.thesportsdb.com/images/media/team/badge/urwtup1473453288.png",
    "sc freiburg": "https://r2.thesportsdb.com/images/media/team/badge/urwtup1473453288.png",
    "werder bremen": "https://a.espncdn.com/i/teamlogos/soccer/500/137.png",
    "bremen": "https://a.espncdn.com/i/teamlogos/soccer/500/137.png",
    "augsburg": "https://a.espncdn.com/i/teamlogos/soccer/500/3841.png",
    "wolfsburg": "https://a.espncdn.com/i/teamlogos/soccer/500/138.png",
    "borussia monchengladbach": "https://a.espncdn.com/i/teamlogos/soccer/500/268.png",
    "mainz": "https://a.espncdn.com/i/teamlogos/soccer/500/130.png",
    "fsv mainz 05": "https://a.espncdn.com/i/teamlogos/soccer/500/130.png",
    "union berlin": "https://r2.thesportsdb.com/images/media/team/badge/q0o5001599679795.png",
    "hoffenheim": "https://a.espncdn.com/i/teamlogos/soccer/500/7911.png",
    "st pauli": "https://a.espncdn.com/i/teamlogos/soccer/500/133.png",
    "heidenheim": "https://r2.thesportsdb.com/images/media/team/badge/lbj7g01608236988.png",
    "bochum": "https://a.espncdn.com/i/teamlogos/soccer/500/121.png",
    "holstein kiel": "https://a.espncdn.com/i/teamlogos/soccer/500/6722.png",
    "koln": "https://a.espncdn.com/i/teamlogos/soccer/500/122.png",
    "1. fc koln": "https://a.espncdn.com/i/teamlogos/soccer/500/122.png",
    "fc koln": "https://a.espncdn.com/i/teamlogos/soccer/500/122.png",
    "hamburger sv": "https://a.espncdn.com/i/teamlogos/soccer/500/127.png",
    "schalke 04": "https://a.espncdn.com/i/teamlogos/soccer/500/133.png",
    "sc paderborn": "https://r2.thesportsdb.com/images/media/team/badge/kddvva1566048058.png",
    "elversberg": "https://r2.thesportsdb.com/images/media/team/badge/z079go1677573926.png",

    # --- Франция (Ligue 1 & Ligue 2) ---
    "paris saint germain": "https://a.espncdn.com/i/teamlogos/soccer/500/160.png",
    "psg": "https://a.espncdn.com/i/teamlogos/soccer/500/160.png",
    "marseille": "https://r2.thesportsdb.com/images/media/team/badge/c6bazh1779212287.png",
    "monaco": "https://a.espncdn.com/i/teamlogos/soccer/500/175.png",
    "lyon": "https://a.espncdn.com/i/teamlogos/soccer/500/167.png",
    "lille": "https://a.espncdn.com/i/teamlogos/soccer/500/166.png",
    "lens": "https://r2.thesportsdb.com/images/media/team/badge/3pxoum1598797195.png",
    "rc lens": "https://r2.thesportsdb.com/images/media/team/badge/3pxoum1598797195.png",
    "nice": "https://r2.thesportsdb.com/images/media/team/badge/msy7ly1621593859.png",
    "rennes": "https://a.espncdn.com/i/teamlogos/soccer/500/171.png",
    "brest": "https://r2.thesportsdb.com/images/media/team/badge/z69be41598797026.png",
    "strasbourg": "https://a.espncdn.com/i/teamlogos/soccer/500/173.png",
    "toulouse": "https://a.espncdn.com/i/teamlogos/soccer/500/174.png",
    "auxerre": "https://r2.thesportsdb.com/images/media/team/badge/lzdtbf1658753355.png",
    "le havre": "https://a.espncdn.com/i/teamlogos/soccer/500/272.png",
    "lorient": "https://a.espncdn.com/i/teamlogos/soccer/500/273.png",
    "troyes": "https://r2.thesportsdb.com/images/media/team/badge/sl5kzg1766617559.png",
    "le mans": "https://r2.thesportsdb.com/images/media/team/badge/wjhziv1700145026.png",
    "le mans fc": "https://r2.thesportsdb.com/images/media/team/badge/wjhziv1700145026.png",

    # --- Еврокубки и другие европейские клубы ---
    "porto": "https://r2.thesportsdb.com/images/media/team/badge/xu47rb1628855600.png",
    "benfica": "https://a.espncdn.com/i/teamlogos/soccer/500/1929.png",
    "sporting cp": "https://r2.thesportsdb.com/images/media/team/badge/5hiuk71783137875.png",
    "ajax": "https://r2.thesportsdb.com/images/media/team/badge/zg9tii1755495289.png",
    "psv": "https://r2.thesportsdb.com/images/media/team/badge/xfsz6i1721297428.png",
    "feyenoord": "https://r2.thesportsdb.com/images/media/team/badge/uturtx1473534803.png",
    "nec nijmegen": "https://r2.thesportsdb.com/images/media/team/badge/t5qjle1701019868.png",
    "nijmegen": "https://r2.thesportsdb.com/images/media/team/badge/t5qjle1701019868.png",
    "olympiakos": "https://a.espncdn.com/i/teamlogos/soccer/500/449.png",
    "olympiakos piraeus": "https://a.espncdn.com/i/teamlogos/soccer/500/449.png",
    "panathinaikos": "https://r2.thesportsdb.com/images/media/team/badge/vtpwwt1448208397.png",
    "ofi crete": "https://r2.thesportsdb.com/images/media/team/badge/02xrl91602773672.png",
    "ferencvaros": "https://r2.thesportsdb.com/images/media/team/badge/wk17od1688115265.png",
    "ferencvaros tc": "https://r2.thesportsdb.com/images/media/team/badge/wk17od1688115265.png",
    "viktoria plzen": "https://r2.thesportsdb.com/images/media/team/badge/5tawzs1782981979.png",
    "plzen": "https://r2.thesportsdb.com/images/media/team/badge/5tawzs1782981979.png",
    "pfc levski sofia": "https://r2.thesportsdb.com/images/media/team/badge/evevzv1626443555.png",
    "levski sofia": "https://r2.thesportsdb.com/images/media/team/badge/evevzv1626443555.png",
    "omonoia fc": "https://r2.thesportsdb.com/images/media/team/badge/1rijst1707410501.png",
    "omonia": "https://r2.thesportsdb.com/images/media/team/badge/1rijst1707410501.png",
    "fc ararat-armenia": "https://r2.thesportsdb.com/images/media/team/badge/2jawis1742401717.png",
    "ararat armenia": "https://r2.thesportsdb.com/images/media/team/badge/2jawis1742401717.png",
    "besiktas": "https://r2.thesportsdb.com/images/media/team/badge/svo05k1776827439.png",
    "fenerbahce": "https://r2.thesportsdb.com/images/media/team/badge/twxxvs1448199691.png",
    "galatasaray": "https://r2.thesportsdb.com/images/media/team/badge/io7jk21767941298.png",

    # --- Российская Премьер-Лига (РПЛ) ---
    "spartak moscow": "https://r2.thesportsdb.com/images/media/team/badge/zpj2el1754674286.png",
    "spartak": "https://r2.thesportsdb.com/images/media/team/badge/zpj2el1754674286.png",
    "zenit": "https://r2.thesportsdb.com/images/media/team/badge/utp0wo1742329861.png",
    "zenit st petersburg": "https://r2.thesportsdb.com/images/media/team/badge/utp0wo1742329861.png",
    "cska moscow": "https://r2.thesportsdb.com/images/media/team/badge/1hf19s1681319986.png",
    "cska": "https://r2.thesportsdb.com/images/media/team/badge/1hf19s1681319986.png",
    "lokomotiv moscow": "https://r2.thesportsdb.com/images/media/team/badge/tuyrur1473452310.png",
    "lokomotiv": "https://r2.thesportsdb.com/images/media/team/badge/tuyrur1473452310.png",
    "dynamo moscow": "https://r2.thesportsdb.com/images/media/team/badge/j27vke1782186818.png",
    "krasnodar": "https://r2.thesportsdb.com/images/media/team/badge/srxryu1473452272.png",
    "rostov": "https://r2.thesportsdb.com/images/media/team/badge/yysryx1473452299.png",
    "rubin kazan": "https://r2.thesportsdb.com/images/media/team/badge/hp9kw81579347672.png",
    "krylya sovetov": "https://r2.thesportsdb.com/images/media/team/badge/tuhwpi1627702883.png",
    "akhmat grozny": "https://r2.thesportsdb.com/images/media/team/badge/ake14u1579347653.png",
    "sochi": "https://r2.thesportsdb.com/images/media/team/badge/l5056o1565093226.png",

    # --- Баскетбол (Евролига & NBA) ---
    "saski baskonia": "https://r2.thesportsdb.com/images/media/team/badge/p4x3o61767366090.png",
    "baskonia": "https://r2.thesportsdb.com/images/media/team/badge/p4x3o61767366090.png",
    "anadolu efes": "https://r2.thesportsdb.com/images/media/team/badge/uldz0d1782050729.png",
    "hapoel tel aviv": "https://r2.thesportsdb.com/images/media/team/badge/yrrsml1767366305.png",
    "paris basketball": "https://r2.thesportsdb.com/images/media/team/badge/9q0d6x1726681476.png",
    "virtus bologna": "https://r2.thesportsdb.com/images/media/team/badge/kqfwqq1659402893.png",
    "olimpia milano": "https://r2.thesportsdb.com/images/media/team/badge/aurbi61790186853.png",
    "olympiacos": "https://r2.thesportsdb.com/images/media/team/badge/xckasq1721291508.png",
    "maccabi tel aviv": "https://r2.thesportsdb.com/images/media/team/badge/oeer261781239315.png",
    "crvena zvezda": "https://r2.thesportsdb.com/images/media/team/badge/osgmbz1781157114.png",
    "partizan": "https://r2.thesportsdb.com/images/media/team/badge/iwpdh11614284091.png",
    "zalgiris": "https://r2.thesportsdb.com/images/media/team/badge/4x8gap1579201999.png",
    "asvel": "https://r2.thesportsdb.com/images/media/team/badge/830lrz1757669895.png",
    "los angeles lakers": "https://a.espncdn.com/i/teamlogos/nba/500/lal.png",
    "golden state warriors": "https://a.espncdn.com/i/teamlogos/nba/500/gsw.png",
    "boston celtics": "https://a.espncdn.com/i/teamlogos/nba/500/bos.png",

    # --- Хоккей (Швеция Allsvenskan, KHL, NHL) ---
    "leksands if": "https://r2.thesportsdb.com/images/media/team/badge/ruij751571478402.png",
    "vimmerby hc": "https://r2.thesportsdb.com/images/media/team/badge/fu3agb1718712090.png",
    "mora ik": "https://r2.thesportsdb.com/images/media/team/badge/3p58o01571572794.png",
    "visby roma hk": "https://r2.thesportsdb.com/images/media/team/badge/gx7bzm1719659863.png",
    "nybro vikings if": "https://r2.thesportsdb.com/images/media/team/badge/lxq87h1700826490.png",
    "ik oskarshamn": "https://r2.thesportsdb.com/images/media/team/badge/g047d01571572694.png",
    "kalmar hc": "https://r2.thesportsdb.com/images/media/team/badge/1oop2f1700826368.png",
    "sodertalje sk": "https://r2.thesportsdb.com/images/media/team/badge/5jkc0q1700826206.png",
    "vasteras ik": "https://r2.thesportsdb.com/images/media/team/badge/mscha61644586515.png",
    "modo hockey": "https://r2.thesportsdb.com/images/media/team/badge/wpvvyr1421609878.png",
    "ska st petersburg": "https://r2.thesportsdb.com/images/media/team/badge/6k17p41771447068.png",
    "new york rangers": "https://a.espncdn.com/i/teamlogos/nhl/500/nyr.png",
    "edmonton oilers": "https://a.espncdn.com/i/teamlogos/nhl/500/edm.png",
    "florida panthers": "https://a.espncdn.com/i/teamlogos/nhl/500/fla.png",

    # --- Южная Америка / Аргентина / Резервные клубы ---
    "colon": "https://r2.thesportsdb.com/images/media/team/badge/l72gz21712750680.png",
    "colon de santa fe": "https://r2.thesportsdb.com/images/media/team/badge/l72gz21712750680.png",
    "колон": "https://r2.thesportsdb.com/images/media/team/badge/l72gz21712750680.png",
    "колон де сф": "https://r2.thesportsdb.com/images/media/team/badge/l72gz21712750680.png",
    "independiente rivadavia": "https://r2.thesportsdb.com/images/media/team/badge/5i8ske1754031322.png",
    "индепендьенте ривадавия": "https://r2.thesportsdb.com/images/media/team/badge/5i8ske1754031322.png",
    "псж": "https://a.espncdn.com/i/teamlogos/soccer/500/160.png",
    "psg": "https://a.espncdn.com/i/teamlogos/soccer/500/160.png",
    "слован братислава": "https://r2.thesportsdb.com/images/media/team/badge/uzkg701781199823.png",

    # --- Топ клубы Европы и текущие матчи (Прямые CDN ссылки) ---
    "fremad amager": "https://r2.thesportsdb.com/images/media/team/badge/vdhccy1580134704.png",
    "фремад амагер": "https://r2.thesportsdb.com/images/media/team/badge/vdhccy1580134704.png",
    "nykobing": "https://r2.thesportsdb.com/images/media/team/badge/vzlg4g1580134909.png",
    "nykobing fc": "https://r2.thesportsdb.com/images/media/team/badge/vzlg4g1580134909.png",
    "нюкёбинг": "https://r2.thesportsdb.com/images/media/team/badge/vzlg4g1580134909.png",
    "estudiantes": "https://r2.thesportsdb.com/images/media/team/badge/linsx31718390472.png",
    "estudiantes l.p.": "https://r2.thesportsdb.com/images/media/team/badge/linsx31718390472.png",
    "эстудиантес": "https://r2.thesportsdb.com/images/media/team/badge/linsx31718390472.png",
    "эстудиантес ла-плата": "https://r2.thesportsdb.com/images/media/team/badge/linsx31718390472.png",
    "flamengo": "https://a.espncdn.com/i/teamlogos/soccer/500/819.png",
    "фламенго": "https://a.espncdn.com/i/teamlogos/soccer/500/819.png",
    "celtic": "https://r2.thesportsdb.com/images/media/team/badge/3uv1641758780002.png",
    "celtic fc": "https://r2.thesportsdb.com/images/media/team/badge/3uv1641758780002.png",
    "селтик": "https://r2.thesportsdb.com/images/media/team/badge/3uv1641758780002.png",
    "sturm graz": "https://r2.thesportsdb.com/images/media/team/badge/ppg0j71578585847.png",
    "sturm": "https://r2.thesportsdb.com/images/media/team/badge/ppg0j71578585847.png",
    "штурм": "https://r2.thesportsdb.com/images/media/team/badge/ppg0j71578585847.png",
    "штурм грац": "https://r2.thesportsdb.com/images/media/team/badge/ppg0j71578585847.png",
    "salzburg": "https://r2.thesportsdb.com/images/media/team/badge/01l4jm1781541633.png",
    "red bull salzburg": "https://r2.thesportsdb.com/images/media/team/badge/01l4jm1781541633.png",
    "зальцбург": "https://r2.thesportsdb.com/images/media/team/badge/01l4jm1781541633.png",
    "ред булл зальцбург": "https://r2.thesportsdb.com/images/media/team/badge/01l4jm1781541633.png",
    "anderlecht": "https://r2.thesportsdb.com/images/media/team/badge/auindn1771129464.png",
    "rsc anderlecht": "https://r2.thesportsdb.com/images/media/team/badge/auindn1771129464.png",
    "андерлехт": "https://r2.thesportsdb.com/images/media/team/badge/auindn1771129464.png",
    "braga": "https://r2.thesportsdb.com/images/media/team/badge/skbiwo1785775946.png",
    "sc braga": "https://r2.thesportsdb.com/images/media/team/badge/skbiwo1785775946.png",
    "брага": "https://r2.thesportsdb.com/images/media/team/badge/skbiwo1785775946.png",
    "gent": "https://r2.thesportsdb.com/images/media/team/badge/48e27o1750703124.png",
    "kaa gent": "https://r2.thesportsdb.com/images/media/team/badge/48e27o1750703124.png",
    "гент": "https://r2.thesportsdb.com/images/media/team/badge/48e27o1750703124.png",
    "twente": "https://r2.thesportsdb.com/images/media/team/badge/rsrxrt1473534783.png",
    "fc twente": "https://r2.thesportsdb.com/images/media/team/badge/rsrxrt1473534783.png",
    "твенте": "https://r2.thesportsdb.com/images/media/team/badge/rsrxrt1473534783.png",
    "az alkmaar": "https://r2.thesportsdb.com/images/media/team/badge/wtqwvv1473534757.png",
    "az": "https://r2.thesportsdb.com/images/media/team/badge/wtqwvv1473534757.png",
    "аз алкмар": "https://r2.thesportsdb.com/images/media/team/badge/wtqwvv1473534757.png",
    "hajduk split": "https://r2.thesportsdb.com/images/media/team/badge/23mvtk1579955412.png",
    "hnk hajduk split": "https://r2.thesportsdb.com/images/media/team/badge/23mvtk1579955412.png",
    "хайдук сплит": "https://r2.thesportsdb.com/images/media/team/badge/23mvtk1579955412.png",
    "хайдук": "https://r2.thesportsdb.com/images/media/team/badge/23mvtk1579955412.png",
    "sunderland": "https://r2.thesportsdb.com/images/media/team/badge/tprtus1448813498.png",
    "сандерленд": "https://r2.thesportsdb.com/images/media/team/badge/tprtus1448813498.png",
    "midtjylland": "https://r2.thesportsdb.com/images/media/team/badge/lvkl8g1783533167.png",
    "fc midtjylland": "https://r2.thesportsdb.com/images/media/team/badge/lvkl8g1783533167.png",
    "мидтъюлланн": "https://r2.thesportsdb.com/images/media/team/badge/lvkl8g1783533167.png",
    "nordsjaelland": "https://r2.thesportsdb.com/images/media/team/badge/p2hof41579460164.png",
    "fc nordsjaelland": "https://r2.thesportsdb.com/images/media/team/badge/p2hof41579460164.png",
    "норшелланн": "https://r2.thesportsdb.com/images/media/team/badge/p2hof41579460164.png",
    "lugano": "https://r2.thesportsdb.com/images/media/team/badge/2kh2if1567615581.png",
    "fc lugano": "https://r2.thesportsdb.com/images/media/team/badge/2kh2if1567615581.png",
    "лугано": "https://r2.thesportsdb.com/images/media/team/badge/2kh2if1567615581.png",
    "lech poznan": "https://r2.thesportsdb.com/images/media/team/badge/8zfxyx1685597440.png",
    "kks lech poznan": "https://r2.thesportsdb.com/images/media/team/badge/8zfxyx1685597440.png",
    "лех": "https://r2.thesportsdb.com/images/media/team/badge/8zfxyx1685597440.png",
    "лех познань": "https://r2.thesportsdb.com/images/media/team/badge/8zfxyx1685597440.png",
    "hearts": "https://r2.thesportsdb.com/images/media/team/badge/v3eyvw1617287212.png",
    "heart of midlothian": "https://r2.thesportsdb.com/images/media/team/badge/v3eyvw1617287212.png",
    "хартс": "https://r2.thesportsdb.com/images/media/team/badge/v3eyvw1617287212.png",
    "copenhagen": "https://a.espncdn.com/i/teamlogos/soccer/500/519.png",
    "fc copenhagen": "https://a.espncdn.com/i/teamlogos/soccer/500/519.png",
    "копенгаген": "https://a.espncdn.com/i/teamlogos/soccer/500/519.png",
    "фк копенгаген": "https://a.espncdn.com/i/teamlogos/soccer/500/519.png",
    "aarhus": "https://r2.thesportsdb.com/images/media/team/badge/x9axpr1624623878.png",
    "agf aarhus": "https://r2.thesportsdb.com/images/media/team/badge/x9axpr1624623878.png",
    "орхус": "https://r2.thesportsdb.com/images/media/team/badge/x9axpr1624623878.png",
    "thun": "https://r2.thesportsdb.com/images/media/team/badge/sovjgl1699462359.png",
    "fc thun": "https://r2.thesportsdb.com/images/media/team/badge/sovjgl1699462359.png",
    "тун": "https://r2.thesportsdb.com/images/media/team/badge/sovjgl1699462359.png",
    "brann": "https://r2.thesportsdb.com/images/media/team/badge/ovuad71690695412.png",
    "sk brann": "https://r2.thesportsdb.com/images/media/team/badge/ovuad71690695412.png",
    "бранн": "https://r2.thesportsdb.com/images/media/team/badge/ovuad71690695412.png",
    "fatih karagumruk": "https://r2.thesportsdb.com/images/media/team/badge/bfb84y1580847945.png",
    "фатих карагюмрюк": "https://r2.thesportsdb.com/images/media/team/badge/bfb84y1580847945.png",
    "cska sofia": "https://a.espncdn.com/i/teamlogos/soccer/500/449.png",
    "цска софия": "https://a.espncdn.com/i/teamlogos/soccer/500/449.png",
    "dinamo zagreb": "https://r2.thesportsdb.com/images/media/team/badge/zcb6f61784988620.png",
    "динамо загреб": "https://r2.thesportsdb.com/images/media/team/badge/zcb6f61784988620.png",
    "sparta praha": "https://r2.thesportsdb.com/images/media/team/badge/j00qct1718287150.png",
    "спарта прага": "https://r2.thesportsdb.com/images/media/team/badge/j00qct1718287150.png",
    "ференцварош": "https://r2.thesportsdb.com/images/media/team/badge/wk17od1688115265.png",
    "виктория пльзень": "https://r2.thesportsdb.com/images/media/team/badge/5tawzs1782981979.png",
    "пльзень": "https://r2.thesportsdb.com/images/media/team/badge/5tawzs1782981979.png",
    "бенфика": "https://a.espncdn.com/i/teamlogos/soccer/500/1929.png",
    "аякс": "https://r2.thesportsdb.com/images/media/team/badge/zg9tii1755495289.png",
    "бешикташ": "https://r2.thesportsdb.com/images/media/team/badge/svo05k1776827439.png",
    "панатинаикос": "https://r2.thesportsdb.com/images/media/team/badge/vtpwwt1448208397.png",
    "олимпиакос": "https://a.espncdn.com/i/teamlogos/soccer/500/449.png",
    "црвена звезда": "https://r2.thesportsdb.com/images/media/team/badge/osgmbz1781157114.png",
    "сельта": "https://a.espncdn.com/i/teamlogos/soccer/500/85.png",
    "милан": "https://a.espncdn.com/i/teamlogos/soccer/500/103.png",
    "ювентус": "https://a.espncdn.com/i/teamlogos/soccer/500/111.png",
    "интер": "https://a.espncdn.com/i/teamlogos/soccer/500/110.png",
    "лацио": "https://a.espncdn.com/i/teamlogos/soccer/500/110.png",
    "рома": "https://a.espncdn.com/i/teamlogos/soccer/500/104.png",
    "аталанта": "https://a.espncdn.com/i/teamlogos/soccer/500/125.png",
    "наполи": "https://a.espncdn.com/i/teamlogos/soccer/500/114.png",
    "фиорентина": "https://a.espncdn.com/i/teamlogos/soccer/500/109.png",
    "борнмут": "https://a.espncdn.com/i/teamlogos/soccer/500/349.png",
    "брайтон": "https://a.espncdn.com/i/teamlogos/soccer/500/331.png",
    "хоффенхайм": "https://a.espncdn.com/i/teamlogos/soccer/500/7911.png",
    "фрайбург": "https://a.espncdn.com/i/teamlogos/soccer/500/126.png",
    "лион": "https://a.espncdn.com/i/teamlogos/soccer/500/167.png",
    "марсель": "https://a.espncdn.com/i/teamlogos/soccer/500/166.png",
    "ренн": "https://a.espncdn.com/i/teamlogos/soccer/500/266.png",
    "кристал пэлас": "https://a.espncdn.com/i/teamlogos/soccer/500/384.png",
    "сент-жиллауз": "https://r2.thesportsdb.com/images/media/team/badge/ljszp41654601742.png",
    "сент-триден": "https://a.espncdn.com/i/teamlogos/soccer/500/228.png",
    "ст. трёйден": "https://a.espncdn.com/i/teamlogos/soccer/500/228.png",
    "ст трейден": "https://a.espncdn.com/i/teamlogos/soccer/500/228.png",
    "ст. трейден": "https://a.espncdn.com/i/teamlogos/soccer/500/228.png",
    "пафос": "https://r2.thesportsdb.com/images/media/team/badge/1rijst1707410501.png",
    "фк пафос": "https://r2.thesportsdb.com/images/media/team/badge/1rijst1707410501.png",
    "иберия 1999": "https://r2.thesportsdb.com/images/media/team/badge/2jawis1742401717.png",
    "яблонец": "https://r2.thesportsdb.com/images/media/team/badge/5tawzs1782981979.png",
    "кайрат": "https://r2.thesportsdb.com/images/media/team/badge/evevzv1626443555.png",
    "кайрат-алматы": "https://r2.thesportsdb.com/images/media/team/badge/evevzv1626443555.png",
    "жальгирис": "https://r2.thesportsdb.com/images/media/team/badge/4x8gap1579201999.png",
    "жальгирис каунас": "https://r2.thesportsdb.com/images/media/team/badge/4x8gap1579201999.png",
    "каунас": "https://r2.thesportsdb.com/images/media/team/badge/4x8gap1579201999.png",
    "бока хуниорс": "https://a.espncdn.com/i/teamlogos/soccer/500/5.png",
    "ривер плейт": "https://a.espncdn.com/i/teamlogos/soccer/500/16.png",
    "сан-паулу": "https://r2.thesportsdb.com/images/media/team/badge/sxpupx1473538135.png",
    "палмейрас": "https://a.espncdn.com/i/teamlogos/soccer/500/2029.png",
    "гремио": "https://a.espncdn.com/i/teamlogos/soccer/500/6273.png",
    "интернасьонал": "https://r2.thesportsdb.com/images/media/team/badge/yprvxx1473538097.png",
    "атлетико минейро": "https://a.espncdn.com/i/teamlogos/soccer/500/1068.png",
    "крузейро": "https://r2.thesportsdb.com/images/media/team/badge/upsvvu1473538059.png",
    "коринтианс": "https://a.espncdn.com/i/teamlogos/soccer/500/874.png",
    "сантос": "https://a.espncdn.com/i/teamlogos/soccer/500/2674.png",
    "васко да гама": "https://a.espncdn.com/i/teamlogos/soccer/500/3454.png",
    "флуминенсе": "https://r2.thesportsdb.com/images/media/team/badge/stvvwp1473538082.png",
    "ботафого": "https://r2.thesportsdb.com/images/media/team/badge/bs5mbw1733004596.png",
    "индепендьенте": "https://a.espncdn.com/i/teamlogos/soccer/500/9.png",
    "расинг": "https://a.espncdn.com/i/teamlogos/soccer/500/15.png",
    "сан-лоренсо": "https://a.espncdn.com/i/teamlogos/soccer/500/18.png",
    "велес сарсфилд": "https://a.espncdn.com/i/teamlogos/soccer/500/21.png",
    "сент-жиллуаз": "https://r2.thesportsdb.com/images/media/team/badge/ljszp41654601742.png",
    "юнион сент-жиллуаз": "https://r2.thesportsdb.com/images/media/team/badge/ljszp41654601742.png",
}

TRANSLIT_CYRILLIC = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '',
    'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
}

def transliterate_ru(text: str) -> str:
    res = []
    for ch in text.lower():
        res.append(TRANSLIT_CYRILLIC.get(ch, ch))
    return "".join(res)

RU_TO_LATIN_TEAMS: Dict[str, str] = {
    # Нидерланды и дополнительные европейские клубы
    "сент-жиллуаз": "union saint-gilloise",
    "юнион сент-жиллуаз": "union saint-gilloise",
    "неймеген": "nec nijmegen",
    "нек неймеген": "nec nijmegen",
    "нек": "nec nijmegen",
    "бенфика": "benfica",
    "асвел": "asvel",
    "асвел лион": "asvel",
    "асвел лион-виллербан": "asvel",
    # Испания
    "хетафе": "getafe",
    "жирона": "girona",
    "хихон": "sporting gijon",
    "спортинг хихон": "sporting gijon",
    "сельта": "celta vigo",
    "севилья": "sevilla",
    "вильярреал": "villarreal",
    "сосьедад": "real sociedad",
    "реал сосьедад": "real sociedad",
    "атлетико": "atletico madrid",
    "атлетико мадрид": "atletico madrid",
    "атлетик": "athletic club",
    "атлетик бильбао": "athletic club",
    "эспаньол": "espanyol",
    "мальорка": "mallorca",
    "осасуна": "osasuna",
    "райо вальекано": "rayo vallecano",
    "депортиво алавес": "deportivo alaves",
    "алавес": "deportivo alaves",
    "кадис": "cadiz",
    "гранада": "granada",
    "эльче": "elche",
    "леванте": "levante",
    "валенсия": "valencia",
    "бетис": "real betis",
    "реал бетис": "real betis",
    "барселона": "barcelona",
    "реал мадрид": "real madrid",
    "лас пальмас": "las palmas",
    "леганес": "leganes",
    "вальядолид": "valladolid",
    
    # Румыния и Восточная Европа
    "кс университатя крайова": "universitatea craiova",
    "университатя крайова": "universitatea craiova",
    "крайова": "universitatea craiova",
    "кс крайова": "universitatea craiova",
    "фксб": "fcsb",
    "стяуа": "fcsb",
    "чфр клуж": "cfr cluj",
    "клуж": "cfr cluj",
    "рапид бухарест": "rapid bucuresti",
    "динамо бухарест": "dinamo bucuresti",
    "фарул": "farul constanta",
    "сепси": "sepsi osk",
    "оцелул": "otelul galati",
    "университатя клуж": "universitatea cluj",
    
    # Италия
    "ювентус": "juventus",
    "интер": "inter milan",
    "интер милан": "inter milan",
    "милан": "ac milan",
    "наполи": "napoli",
    "рома": "as roma",
    "лацио": "lazio",
    "аталанта": "atalanta",
    "фиорентина": "fiorentina",
    "болонья": "bologna",
    "торино": "torino",
    "сассуоло": "sassuolo",
    "кальяри": "cagliari",
    "эмполи": "empoli",
    "верона": "hellas verona",
    "эллас верона": "hellas verona",
    "удинезе": "udinese",
    "дженоа": "genoa",
    "монца": "monza",
    "лечче": "lecce",
    "парма": "parma",
    "комо": "como",
    "венеция": "venezia",
    
    # Франция
    "псж": "paris saint germain",
    "пари сен жермен": "paris saint germain",
    "пари сен-жермен": "paris saint germain",
    "марсель": "marseille",
    "олимпик марсель": "marseille",
    "лион": "lyon",
    "олимпик лион": "lyon",
    "монако": "monaco",
    "лилль": "lille",
    "ренн": "rennes",
    "ницца": "nice",
    "ланс": "lens",
    "страсбур": "strasbourg",
    "брест": "stade brestois",
    "тулуза": "toulouse",
    "реймс": "stade de reims",
    "монтпелье": "montpellier",
    "сент-этьен": "saint etienne",
    "осер": "auxerre",
    "анже": "angers",
    "гавр": "le havre",
    
    # Германия
    "бавария": "bayern munich",
    "боруссия д": "borussia dortmund",
    "боруссия дортмунд": "borussia dortmund",
    "боруссия м": "borussia monchengladbach",
    "боруссия менхенгладбах": "borussia monchengladbach",
    "байер": "bayer leverkusen",
    "байер леверкузен": "bayer leverkusen",
    "рб лейпциг": "rb leipzig",
    "лейпциг": "rb leipzig",
    "айнтрахт": "eintracht frankfurt",
    "айнтрахт франкфурт": "eintracht frankfurt",
    "штутгарт": "vfb stuttgart",
    "вольфсбург": "vfl wolfsburg",
    "фрайбург": "sc freiburg",
    "хоффенхайм": "tsg hoffenheim",
    "вердер": "werder bremen",
    "унион берлин": "union berlin",
    "аугсбург": "fc augsburg",
    "майнц": "mainz 05",
    "санкт паули": "st pauli",
    "санкт-паули": "st pauli",
    "холштайн киль": "holstein kiel",
    "хайденхайм": "heidenheim",
    "бохум": "vfl bochum",
    
    # Англия
    "арсенал": "arsenal",
    "манчестер сити": "manchester city",
    "ман сити": "manchester city",
    "манчестер юнайтед": "manchester united",
    "мю": "manchester united",
    "ливерпуль": "liverpool",
    "челси": "chelsea",
    "тоттенхэм": "tottenham hotspur",
    "ньюкасл": "newcastle united",
    "астон вилла": "aston villa",
    "брайтон": "brighton",
    "вест хэм": "west ham united",
    "брентфорд": "brentford",
    "кристал пэлас": "crystal palace",
    "борнмут": "bournemouth",
    "фулхэм": "fulham",
    "вулверхэмптон": "wolverhampton wanderers",
    "эвертон": "everton",
    "лестер": "leicester city",
    "саутгемптон": "southampton",
    "ипсвич": "ipswich town",
    
    # Южная Америка / MLS / Другие
    "хуниор": "junior barranquilla",
    "хуниор барранкилья": "junior barranquilla",
    "атлетико хуниор": "junior barranquilla",
    "депортиво перейра": "deportivo pereira",
    "перейра": "deportivo pereira",
    "сармьенто": "sarmiento",
    "сармьенто хунин": "sarmiento",
    "ривер плейт": "river plate",
    "бока хуниорс": "boca juniors",
    "атлетико минейро": "atletico mineiro",
    "монтевидео сити торке": "montevideo city torque",
    "интер майами": "inter miami",
    "нью-йорк сити": "new york city fc",
    "нью йорк сити": "new york city fc",
    "ди си юнайтед": "dc united",
    "нью-йорк ред буллз": "new york red bulls",
    "нью йорк ред буллз": "new york red bulls",
    "шанхай шеньхуа": "shanghai shenhua",
    "шанхай шэньхуа": "shanghai shenhua",
    "комуникасьонес": "comunicaciones",
    "гуастатоя": "guastatoya",
    "антигуа": "antigua gfc",
    "депортиво миско": "deportivo mixco",
    "монагас": "monagas",
    "динамо пуэрто": "dynamo puerto",
    "аль-райян": "al rayyan",
    "аль-хор": "al khor",

    # Европа / Еврокубки
    "ференцварош": "ferencvaros",
    "виктория пльзень": "viktoria plzen",
    "пльзень": "viktoria plzen",
    "бенфика": "benfica",
    "аякс": "ajax",
    "селтик": "celtic",
    "штурм": "sturm graz",
    "штурм грац": "sturm graz",
    "зальцбург": "salzburg",
    "ред булл зальцбург": "salzburg",
    "бешикташ": "besiktas",
    "андерлехт": "anderlecht",
    "брага": "braga",
    "гент": "gent",
    "твенте": "twente",
    "аз алкмар": "az alkmaar",
    "аз": "az alkmaar",
    "панатинаикос": "panathinaikos",
    "олимпиакос": "olympiakos",
    "црвена звезда": "crvena zvezda",
    "хайдук сплит": "hajduk split",
    "сандерленд": "sunderland",
    "мидтъюлланн": "midtjylland",
    "норшелланн": "nordsjaelland",
    "лугано": "lugano",
    "лех": "lech poznan",
    "хартс": "hearts",
    "фремад амагер": "fremad amager",
    "нюкёбинг": "nykobing",
    "эстудиантес": "estudiantes",
    "фламенго": "flamengo",
    "копенгаген": "copenhagen",
    "фк копенгаген": "copenhagen",
    "орхус": "aarhus",
    "тун": "thun",
    "бранн": "brann",
    "фатих карагюмрюк": "fatih karagumruk",
    "цска софия": "cska sofia",
    "динамо загреб": "dinamo zagreb",
    "спарта прага": "sparta praha",
    "яблонец": "jablonec",
    "пафос": "pafos",
    "фк пафос": "pafos",
    "иберия 1999": "ararat armenia",
    "купс": "kups",
    "сент-жиллауз": "union saint-gilloise",
    "сент-триден": "sint-truidense",
    "ст. трёйден": "sint-truidense",
    "ст трейден": "sint-truidense",
    "ст. трейден": "sint-truidense",
    "кайрат": "kairat",
    "кайрат-алматы": "kairat",
    "жальгирис": "zalgiris",
    "жальгирис каунас": "zalgiris"
}

# База официальных русских названий клубов для перевода на русский язык
LATIN_TO_RU_TEAMS: Dict[str, str] = {
    "real madrid": "Реал Мадрид",
    "barcelona": "Барселона",
    "atletico madrid": "Атлетико Мадрид",
    "benfica": "Бенфика",
    "sl benfica": "Бенфика",
    "celtic": "Селтик",
    "celtic fc": "Селтик",
    "asvel": "АСВЕЛ Лион",
    "asvel lyon": "АСВЕЛ Лион",
    "asvel lyon villeurbanne": "АСВЕЛ Лион",
    "asvel lyon-villeurbanne": "АСВЕЛ Лион",
    "ldlc asvel": "АСВЕЛ Лион",
    "nec nijmegen": "Неймеген",
    "nijmegen": "Неймеген",
    "nec": "Неймеген",
    "levski sofia": "Левски София",
    "pfc levski sofia": "Левски София",
    "levski": "Левски София",
    "sporting cp": "Спортинг",
    "ajax": "Аякс",
    "psv": "ПСВ",
    "feyenoord": "Фейеноорд",
    "salzburg": "Зальцбург",
    "red bull salzburg": "Зальцбург",
    "sturm graz": "Штурм",
    "olympiacos": "Олимпиакос",
    "panathinaikos": "Панатинаикос",
    "fenerbahce": "Фенербахче",
    "galatasaray": "Галатасарай",
    "besiktas": "Бешикташ",
    "dinamo zagreb": "Динамо Загреб",
    "sparta praha": "Спарта Прага",
    "sparta prague": "Спарта Прага",
    "slavia praha": "Славия Прага",
    "slavia prague": "Славия Прага",
    "zalgiris": "Жальгирис",
    "maccabi tel aviv": "Маккаби Тель-Авив",
    "partizan": "Партизан",
    "crvena zvezda": "Црвена Звезда",
    "union saint-gilloise": "Сент-Жиллуаз",
    "royale union saint-gilloise": "Сент-Жиллуаз",
    "anderlecht": "Андерлехт",
    "club brugge": "Брюгге",
    "gent": "Гент",
    "braga": "Брага",
    "porto": "Порту",
}

for ru_k, lat_v in RU_TO_LATIN_TEAMS.items():
    if lat_v not in LATIN_TO_RU_TEAMS and len(ru_k) >= 3:
        LATIN_TO_RU_TEAMS[lat_v] = ru_k.title()

def translate_team_name_to_ru(name: str) -> str:
    """
    Если название команды на латинице/английском, переводит его на красивый русский язык.
    """
    if not name:
        return name
    name_strip = name.strip()
    if len(re.findall(r'[а-яёА-ЯЁ]', name_strip)) >= 2:
        return name_strip
    name_low = name_strip.lower()
    if name_low in LATIN_TO_RU_TEAMS:
        return LATIN_TO_RU_TEAMS[name_low]
    variants = normalize_team_name(name_strip)
    for v in variants:
        if v in LATIN_TO_RU_TEAMS:
            return LATIN_TO_RU_TEAMS[v]
    return name_strip

def normalize_team_name(name: str) -> List[str]:
    """
    Интеллектуальная нормализация названия команды:
    - Поиск в таблице RU_TO_LATIN_TEAMS
    - Очищает от маркеров резервных составов, дублей и U19/U21
    - Удаляет диакритические знаки (Plzeň -> Plzen, Köln -> Koln)
    - Убирает префиксы: 1. FC, PFC, CA, CD, RC, SC, CS, CSU, FSV, FC, FK, КС, ЦС, ФК, ПФК
    - Убирает суффиксы: TC, IF, IK, HK, SK, HC, BK, CF
    - Поддерживает вариации испанской транслитерации (х -> g, ж -> g, ху -> ju)
    - Возвращает упорядоченный список кандидатов поиска
    """
    if not name:
        return []

    # 0. Очистка от маркеров резервных, молодежных и дублирующих составов:
    raw_cleaned = re.sub(
        r'\(?\s*\b(резерв|рез|мол|молодежь|дубль|reserves|reserve|res|youth|u\s*19|u\s*20|u\s*21|u\s*23|19|20|21|23|ii|2|b)\b\s*\)?',
        '', name, flags=re.IGNORECASE
    ).strip()
    raw_cleaned = re.sub(r'^(жк|уг|угл|угловые|фолы|в\s+створ|офсайды|ауты)\s+', '', raw_cleaned, flags=re.IGNORECASE).strip()
    raw_cleaned = re.sub(r'[\(\)]', ' ', raw_cleaned).strip()
    raw_cleaned = ' '.join(raw_cleaned.split())
    if not raw_cleaned:
        raw_cleaned = name

    # Специфические сокращения (например, де СФ -> de Santa Fe)
    raw_cleaned_sf = re.sub(r'\bде\s+сф\b', 'de santa fe', raw_cleaned, flags=re.IGNORECASE).strip()

    variants: List[str] = []

    # 1. Проверяем точное соответствие и подстроки в таблице RU_TO_LATIN_TEAMS
    name_low = raw_cleaned.lower().strip()
    if name_low in RU_TO_LATIN_TEAMS:
        lat = RU_TO_LATIN_TEAMS[name_low]
        if lat not in variants:
            variants.append(lat)
    for ru_k, lat_v in RU_TO_LATIN_TEAMS.items():
        if ru_k == name_low or (len(ru_k) >= 5 and ru_k in name_low) or (len(name_low) >= 5 and name_low in ru_k):
            if lat_v not in variants:
                variants.append(lat_v)

    # Специальные морфологические правила для популярных клубов
    if 'крайов' in name_low:
        for x in ['universitatea craiova', 'craiova']:
            if x not in variants:
                variants.append(x)
    if 'хетаф' in name_low:
        if 'getafe' not in variants:
            variants.append('getafe')
    if 'хуниор' in name_low:
        for x in ['junior barranquilla', 'junior']:
            if x not in variants:
                variants.append(x)
    if 'перейр' in name_low:
        if 'deportivo pereira' not in variants:
            variants.append('deportivo pereira')
    if 'сармьент' in name_low:
        if 'sarmiento' not in variants:
            variants.append('sarmiento')
    if 'неймег' in name_low or 'nijmeg' in name_low:
        for x in ['nec nijmegen', 'nijmegen']:
            if x not in variants:
                variants.append(x)
    if 'минейр' in name_low:
        if 'atletico mineiro' not in variants:
            variants.append('atletico mineiro')

    # Пробуем как полное очищенное имя, так и имя без "де СФ"
    candidates_to_try = [raw_cleaned]
    if raw_cleaned_sf != raw_cleaned:
        candidates_to_try.append(raw_cleaned_sf)
        without_sf = re.sub(r'\bде\s+сф\b', '', raw_cleaned, flags=re.IGNORECASE).strip()
        if without_sf:
            candidates_to_try.append(without_sf)

    for cand in candidates_to_try:
        cand_low = cand.lower()
        if cand_low and cand_low not in variants:
            variants.append(cand_low)

        # Транслитерация с русского, если есть кириллица
        latin_name = transliterate_ru(cand) if re.search(r'[а-яё]', cand, re.IGNORECASE) else cand

        # Нормализация диакритических знаков (Unicode NFKD)
        nfkd = unicodedata.normalize('NFKD', latin_name)
        no_accents = ''.join([c for c in nfkd if not unicodedata.combining(c)])

        # Базовая очистка знаков
        clean_str = no_accents.replace('/', ' ').replace('-', ' ').replace('_', ' ')
        clean_str = re.sub(r'[^a-zA-Z0-9\s]', ' ', clean_str)
        base_clean = ' '.join(clean_str.split()).lower()

        if base_clean and base_clean not in variants:
            variants.append(base_clean)

        # Испанские/латинские варианты транскрипции
        if base_clean.startswith('he'):
            ge_var = 'ge' + base_clean[2:]
            if ge_var not in variants:
                variants.append(ge_var)
        if base_clean.startswith('hu'):
            ju_var = 'ju' + base_clean[2:]
            if ju_var not in variants:
                variants.append(ju_var)
        if base_clean.startswith('zhi'):
            gi_var = 'gi' + base_clean[3:]
            if gi_var not in variants:
                variants.append(gi_var)

        # Вариант с заменой начального 'k' на 'c' (испанские/английские клубы типа Kolon -> Colon, Kadis -> Cadiz)
        if 'k' in base_clean:
            c_variant = re.sub(r'\bk', 'c', base_clean)
            if c_variant not in variants:
                variants.append(c_variant)

        # 1. Убираем ведущие префиксы (включая румынские cs/csu и русские кс/цс/фк)
        prefix_pattern = r'^(1\.\s*|1\s+fc\s+|pfc\s+|cf\s+|ca\s+|cd\s+|rc\s+|sc\s+|cs\s+|csu\s+|fsv\s+|ssv\s+|fk\s+|fc\s+|bc\s+|hc\s+|кс\s+|цс\s+|фк\s+|пфк\s+|ск\s+)'
        without_prefix = re.sub(prefix_pattern, '', base_clean, flags=re.IGNORECASE).strip()
        if without_prefix and without_prefix not in variants:
            variants.append(without_prefix)

        # 2. Убираем хвостовые суффиксы
        suffix_pattern = r'\b(tc|jk|fc|cf|if|ik|hk|sk|hc|bk|fk|ac|bc|kk|sc|as|cd|ud|rb|afc|vfb|vfl|tsv|1907|1899)\b'
        without_suffix = re.sub(suffix_pattern, '', without_prefix, flags=re.IGNORECASE).strip()
        without_suffix = ' '.join(without_suffix.split()).lower()
        if without_suffix and without_suffix not in variants:
            variants.append(without_suffix)

        # 3. Первое главное слово (если > 3 символов)
        parts = without_suffix.split()
        if parts and len(parts[0]) > 3:
            p0 = parts[0]
            if p0 not in variants:
                variants.append(p0)
            if p0.startswith('k'):
                p0_c = 'c' + p0[1:]
                if p0_c not in variants:
                    variants.append(p0_c)

    return variants

def get_team_logo(team_name: str, sport: str = "", fast_only: bool = False) -> Optional[str]:
    """
    Возвращает прямую ссылку на прозрачную эмблему команды из ESPN / TheSportsDB CDN.
    Если не найдено — возвращает None, чтобы фронтенд отобразил стильный SVG/CSS векторный бейдж.
    fast_only: если True, ищет только в памяти и дисковом кэше без сетевых запросов.
    """
    if not team_name:
        return None

    search_variants = normalize_team_name(team_name)

    # Баскетбольный Лион / АСВЕЛ
    s_low = (sport or "").lower()
    t_low = (team_name or "").lower().strip()
    if any(b in s_low for b in ["basket", "баскет", "nba", "euroleague", "евролиг"]):
        if any(w in t_low for w in ["лион", "lyon", "asvel", "асвел"]):
            return "https://r2.thesportsdb.com/images/media/team/badge/830lrz1757669895.png"

    # 1. Проверяем предустановленную базу топовых клубов
    for var in search_variants:
        if var in KNOWN_TEAM_LOGOS:
            return KNOWN_TEAM_LOGOS[var]
        for known_k, known_url in KNOWN_TEAM_LOGOS.items():
            if var == known_k or (len(var) > 4 and var in known_k) or (len(known_k) > 4 and known_k in var):
                return known_url

    # 2. Проверяем дисковый и оперативный кэш
    for var in search_variants:
        if var in _LOGO_CACHE:
            return _LOGO_CACHE[var]

    # Единоборства и теннис
    s_low = (sport or "").lower()
    if any(x in s_low for x in ["mma", "ufc"]):
        return "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mma/500/ufc.png"
    if any(x in s_low for x in ["tennis", "теннис", "atp", "wta"]):
        return "https://a.espncdn.com/combiner/i?img=/i/teamlogos/tennis/500/atp.png"

    if fast_only:
        return None

    # 3. Динамический поиск через официальный ESPN Search API (быстро, надежно, охватывает все лиги)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    for query_candidate in search_variants:
        if len(query_candidate) < 3:
            continue
        try:
            url = f"https://site.web.api.espn.com/apis/search/v2?query={urllib.parse.quote(query_candidate)}"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                for sec in data.get('results', []):
                    if sec.get('type') in ['team', 'athlete']:
                        for item in sec.get('contents', []):
                            img = item.get('image', {}).get('default')
                            if img and ('teamlogos' in img or 'headshots' in img):
                                for v in search_variants:
                                    _save_to_disk_cache(v, img)
                                return img
        except Exception:
            continue

    return None

COUNTRY_CODES_MAP: Dict[str, Dict[str, str]] = {
    "DZ": {"name": "Алжир", "code": "dz", "flag_url": "https://flagcdn.com/w40/dz.png", "emoji": "🇩🇿"},
    "ES": {"name": "Испания", "code": "es", "flag_url": "https://flagcdn.com/w40/es.png", "emoji": "🇪🇸"},
    "EN": {"name": "Англия", "code": "gb-eng", "flag_url": "https://flagcdn.com/w40/gb-eng.png", "emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    "GB": {"name": "Англия", "code": "gb-eng", "flag_url": "https://flagcdn.com/w40/gb-eng.png", "emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    "UK": {"name": "Англия", "code": "gb-eng", "flag_url": "https://flagcdn.com/w40/gb-eng.png", "emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    "IT": {"name": "Италия", "code": "it", "flag_url": "https://flagcdn.com/w40/it.png", "emoji": "🇮🇹"},
    "DE": {"name": "Германия", "code": "de", "flag_url": "https://flagcdn.com/w40/de.png", "emoji": "🇩🇪"},
    "FR": {"name": "Франция", "code": "fr", "flag_url": "https://flagcdn.com/w40/fr.png", "emoji": "🇫🇷"},
    "RU": {"name": "Россия", "code": "ru", "flag_url": "https://flagcdn.com/w40/ru.png", "emoji": "🇷🇺"},
    "PT": {"name": "Португалия", "code": "pt", "flag_url": "https://flagcdn.com/w40/pt.png", "emoji": "🇵🇹"},
    "NL": {"name": "Нидерланды", "code": "nl", "flag_url": "https://flagcdn.com/w40/nl.png", "emoji": "🇳🇱"},
    "TR": {"name": "Турция", "code": "tr", "flag_url": "https://flagcdn.com/w40/tr.png", "emoji": "🇹🇷"},
    "BR": {"name": "Бразилия", "code": "br", "flag_url": "https://flagcdn.com/w40/br.png", "emoji": "🇧🇷"},
    "AR": {"name": "Аргентина", "code": "ar", "flag_url": "https://flagcdn.com/w40/ar.png", "emoji": "🇦🇷"},
    "CL": {"name": "Чили", "code": "cl", "flag_url": "https://flagcdn.com/w40/cl.png", "emoji": "🇨🇱"},
    "CO": {"name": "Колумбия", "code": "co", "flag_url": "https://flagcdn.com/w40/co.png", "emoji": "🇨🇴"},
    "MX": {"name": "Мексика", "code": "mx", "flag_url": "https://flagcdn.com/w40/mx.png", "emoji": "🇲🇽"},
    "US": {"name": "США", "code": "us", "flag_url": "https://flagcdn.com/w40/us.png", "emoji": "🇺🇸"},
    "USA": {"name": "США", "code": "us", "flag_url": "https://flagcdn.com/w40/us.png", "emoji": "🇺🇸"},
    "EG": {"name": "Египет", "code": "eg", "flag_url": "https://flagcdn.com/w40/eg.png", "emoji": "🇪🇬"},
    "MA": {"name": "Марокко", "code": "ma", "flag_url": "https://flagcdn.com/w40/ma.png", "emoji": "🇲🇦"},
    "TN": {"name": "Тунис", "code": "tn", "flag_url": "https://flagcdn.com/w40/tn.png", "emoji": "🇹🇳"},
    "SA": {"name": "Саудовская Аравия", "code": "sa", "flag_url": "https://flagcdn.com/w40/sa.png", "emoji": "🇸🇦"},
    "GR": {"name": "Греция", "code": "gr", "flag_url": "https://flagcdn.com/w40/gr.png", "emoji": "🇬🇷"},
    "BE": {"name": "Бельгия", "code": "be", "flag_url": "https://flagcdn.com/w40/be.png", "emoji": "🇧🇪"},
    "SE": {"name": "Швеция", "code": "se", "flag_url": "https://flagcdn.com/w40/se.png", "emoji": "🇸🇪"},
    "NO": {"name": "Норвегия", "code": "no", "flag_url": "https://flagcdn.com/w40/no.png", "emoji": "🇳🇴"},
    "DK": {"name": "Дания", "code": "dk", "flag_url": "https://flagcdn.com/w40/dk.png", "emoji": "🇩🇰"},
    "PL": {"name": "Польша", "code": "pl", "flag_url": "https://flagcdn.com/w40/pl.png", "emoji": "🇵🇱"},
    "CZ": {"name": "Чехия", "code": "cz", "flag_url": "https://flagcdn.com/w40/cz.png", "emoji": "🇨🇿"},
    "AT": {"name": "Австрия", "code": "at", "flag_url": "https://flagcdn.com/w40/at.png", "emoji": "🇦🇹"},
    "CH": {"name": "Швейцария", "code": "ch", "flag_url": "https://flagcdn.com/w40/ch.png", "emoji": "🇨🇭"},
    "UA": {"name": "Украина", "code": "ua", "flag_url": "https://flagcdn.com/w40/ua.png", "emoji": "🇺🇦"},
    "KZ": {"name": "Казахстан", "code": "kz", "flag_url": "https://flagcdn.com/w40/kz.png", "emoji": "🇰🇿"},
    "BY": {"name": "Беларусь", "code": "by", "flag_url": "https://flagcdn.com/w40/by.png", "emoji": "🇧🇾"},
    "JP": {"name": "Япония", "code": "jp", "flag_url": "https://flagcdn.com/w40/jp.png", "emoji": "🇯🇵"},
    "KR": {"name": "Южная Корея", "code": "kr", "flag_url": "https://flagcdn.com/w40/kr.png", "emoji": "🇰🇷"},
    "CN": {"name": "Китай", "code": "cn", "flag_url": "https://flagcdn.com/w40/cn.png", "emoji": "🇨🇳"},
    "AU": {"name": "Австралия", "code": "au", "flag_url": "https://flagcdn.com/w40/au.png", "emoji": "🇦🇺"},
    "IN": {"name": "Индия", "code": "in", "flag_url": "https://flagcdn.com/w40/in.png", "emoji": "🇮🇳"},
    "RS": {"name": "Сербия", "code": "rs", "flag_url": "https://flagcdn.com/w40/rs.png", "emoji": "🇷🇸"},
    "HR": {"name": "Хорватия", "code": "hr", "flag_url": "https://flagcdn.com/w40/hr.png", "emoji": "🇭🇷"},
    "VE": {"name": "Венесуэла", "code": "ve", "flag_url": "https://flagcdn.com/w40/ve.png", "emoji": "🇻🇪"},
    "WORLD": {"name": "Международные", "code": "un", "flag_url": "https://flagcdn.com/w40/un.png", "emoji": "🌍"},
    "RO": {"name": "Румыния", "code": "ro", "flag_url": "https://flagcdn.com/w40/ro.png", "emoji": "🇷🇴"},
    "BG": {"name": "Болгария", "code": "bg", "flag_url": "https://flagcdn.com/w40/bg.png", "emoji": "🇧🇬"},
    "HU": {"name": "Венгрия", "code": "hu", "flag_url": "https://flagcdn.com/w40/hu.png", "emoji": "🇭🇺"},
    "IL": {"name": "Израиль", "code": "il", "flag_url": "https://flagcdn.com/w40/il.png", "emoji": "🇮🇱"},
    "CY": {"name": "Кипр", "code": "cy", "flag_url": "https://flagcdn.com/w40/cy.png", "emoji": "🇨🇾"},
    "AZ": {"name": "Азербайджан", "code": "az", "flag_url": "https://flagcdn.com/w40/az.png", "emoji": "🇦🇿"},
    "GE": {"name": "Грузия", "code": "ge", "flag_url": "https://flagcdn.com/w40/ge.png", "emoji": "🇬🇪"},
    "AM": {"name": "Армения", "code": "am", "flag_url": "https://flagcdn.com/w40/am.png", "emoji": "🇦🇲"},
    "UZ": {"name": "Узбекистан", "code": "uz", "flag_url": "https://flagcdn.com/w40/uz.png", "emoji": "🇺🇿"},
    "FI": {"name": "Финляндия", "code": "fi", "flag_url": "https://flagcdn.com/w40/fi.png", "emoji": "🇫🇮"},
    "IS": {"name": "Исландия", "code": "is", "flag_url": "https://flagcdn.com/w40/is.png", "emoji": "🇮🇸"},
    "IE": {"name": "Ирландия", "code": "ie", "flag_url": "https://flagcdn.com/w40/ie.png", "emoji": "🇮🇪"},
    "EU": {"name": "Лига Европы", "code": "eu", "flag_url": "https://flagcdn.com/w40/eu.png", "emoji": "🇪🇺"},
    "EUROPEANUNION": {"name": "Лига Европы", "code": "eu", "flag_url": "https://flagcdn.com/w40/eu.png", "emoji": "🇪🇺"},
    "EUROPEAN UNION": {"name": "Лига Европы", "code": "eu", "flag_url": "https://flagcdn.com/w40/eu.png", "emoji": "🇪🇺"},
    "EUROPE": {"name": "Лига Европы", "code": "eu", "flag_url": "https://flagcdn.com/w40/eu.png", "emoji": "🇪🇺"},
    "UEFA": {"name": "Лига Европы", "code": "eu", "flag_url": "https://flagcdn.com/w40/eu.png", "emoji": "🇪🇺"},
    "ЛИГА ЕВРОПЫ": {"name": "Лига Европы", "code": "eu", "flag_url": "https://flagcdn.com/w40/eu.png", "emoji": "🇪🇺"},
    "ЛИГА ЕВРОПЫ УЕФА": {"name": "Лига Европы", "code": "eu", "flag_url": "https://flagcdn.com/w40/eu.png", "emoji": "🇪🇺"},
    "ЛИГА ЧЕМПИОНОВ": {"name": "Лига Чемпионов", "code": "eu", "flag_url": "https://flagcdn.com/w40/eu.png", "emoji": "🇪🇺"},
    "ЛИГА КОНФЕРЕНЦИЙ": {"name": "Лига Конференций", "code": "eu", "flag_url": "https://flagcdn.com/w40/eu.png", "emoji": "🇪🇺"},
    # Английские полные названия (из vprognoze и зарубежных источников)
    "ENGLAND": {"name": "Англия", "code": "gb-eng", "flag_url": "https://flagcdn.com/w40/gb-eng.png", "emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    "SCOTLAND": {"name": "Шотландия", "code": "gb-sct", "flag_url": "https://flagcdn.com/w40/gb-sct.png", "emoji": "🏴󠁧󠁢󠁳󠁣󠁴󠁿"},
    "WALES": {"name": "Уэльс", "code": "gb-wls", "flag_url": "https://flagcdn.com/w40/gb-wls.png", "emoji": "🏴󠁧󠁢󠁷󠁬󠁳󠁿"},
    "SPAIN": {"name": "Испания", "code": "es", "flag_url": "https://flagcdn.com/w40/es.png", "emoji": "🇪🇸"},
    "GERMANY": {"name": "Германия", "code": "de", "flag_url": "https://flagcdn.com/w40/de.png", "emoji": "🇩🇪"},
    "ITALY": {"name": "Италия", "code": "it", "flag_url": "https://flagcdn.com/w40/it.png", "emoji": "🇮🇹"},
    "FRANCE": {"name": "Франция", "code": "fr", "flag_url": "https://flagcdn.com/w40/fr.png", "emoji": "🇫🇷"},
    "RUSSIA": {"name": "Россия", "code": "ru", "flag_url": "https://flagcdn.com/w40/ru.png", "emoji": "🇷🇺"},
    "PORTUGAL": {"name": "Португалия", "code": "pt", "flag_url": "https://flagcdn.com/w40/pt.png", "emoji": "🇵🇹"},
    "NETHERLANDS": {"name": "Нидерланды", "code": "nl", "flag_url": "https://flagcdn.com/w40/nl.png", "emoji": "🇳🇱"},
    "HOLLAND": {"name": "Нидерланды", "code": "nl", "flag_url": "https://flagcdn.com/w40/nl.png", "emoji": "🇳🇱"},
    "TURKEY": {"name": "Турция", "code": "tr", "flag_url": "https://flagcdn.com/w40/tr.png", "emoji": "🇹🇷"},
    "BRAZIL": {"name": "Бразилия", "code": "br", "flag_url": "https://flagcdn.com/w40/br.png", "emoji": "🇧🇷"},
    "ARGENTINA": {"name": "Аргентина", "code": "ar", "flag_url": "https://flagcdn.com/w40/ar.png", "emoji": "🇦🇷"},
    "BELGIUM": {"name": "Бельгия", "code": "be", "flag_url": "https://flagcdn.com/w40/be.png", "emoji": "🇧🇪"},
    "ALGERIA": {"name": "Алжир", "code": "dz", "flag_url": "https://flagcdn.com/w40/dz.png", "emoji": "🇩🇿"},
    "EGYPT": {"name": "Египет", "code": "eg", "flag_url": "https://flagcdn.com/w40/eg.png", "emoji": "🇪🇬"},
    "MOROCCO": {"name": "Марокко", "code": "ma", "flag_url": "https://flagcdn.com/w40/ma.png", "emoji": "🇲🇦"},
    "TUNISIA": {"name": "Тунис", "code": "tn", "flag_url": "https://flagcdn.com/w40/tn.png", "emoji": "🇹🇳"},
    "SAUDI ARABIA": {"name": "Саудовская Аравия", "code": "sa", "flag_url": "https://flagcdn.com/w40/sa.png", "emoji": "🇸🇦"},
    "GREECE": {"name": "Греция", "code": "gr", "flag_url": "https://flagcdn.com/w40/gr.png", "emoji": "🇬🇷"},
    "SWEDEN": {"name": "Швеция", "code": "se", "flag_url": "https://flagcdn.com/w40/se.png", "emoji": "🇸🇪"},
    "NORWAY": {"name": "Норвегия", "code": "no", "flag_url": "https://flagcdn.com/w40/no.png", "emoji": "🇳🇴"},
    "DENMARK": {"name": "Дания", "code": "dk", "flag_url": "https://flagcdn.com/w40/dk.png", "emoji": "🇩🇰"},
    "POLAND": {"name": "Польша", "code": "pl", "flag_url": "https://flagcdn.com/w40/pl.png", "emoji": "🇵🇱"},
    "CZECH": {"name": "Чехия", "code": "cz", "flag_url": "https://flagcdn.com/w40/cz.png", "emoji": "🇨🇿"},
    "AUSTRIA": {"name": "Австрия", "code": "at", "flag_url": "https://flagcdn.com/w40/at.png", "emoji": "🇦🇹"},
    "SWITZERLAND": {"name": "Швейцария", "code": "ch", "flag_url": "https://flagcdn.com/w40/ch.png", "emoji": "🇨🇭"},
    "UKRAINE": {"name": "Украина", "code": "ua", "flag_url": "https://flagcdn.com/w40/ua.png", "emoji": "🇺🇦"},
    "KAZAKHSTAN": {"name": "Казахстан", "code": "kz", "flag_url": "https://flagcdn.com/w40/kz.png", "emoji": "🇰🇿"},
    "JAPAN": {"name": "Япония", "code": "jp", "flag_url": "https://flagcdn.com/w40/jp.png", "emoji": "🇯🇵"},
    "AUSTRALIA": {"name": "Австралия", "code": "au", "flag_url": "https://flagcdn.com/w40/au.png", "emoji": "🇦🇺"},
    "CHINA": {"name": "Китай", "code": "cn", "flag_url": "https://flagcdn.com/w40/cn.png", "emoji": "🇨🇳"},
}

def get_country_info(country_str: str) -> Dict[str, str]:
    """
    Разрешает буквенный код страны (DZ, ES, RU, EN) или полное название (ENGLAND, SPAIN)
    в название на русском, код флага и эмодзи.
    """
    if not country_str:
        return {"name": "Спорт", "code": "un", "flag_url": "https://flagcdn.com/w40/un.png", "emoji": "🌍"}
    c_up = country_str.strip().upper()
    if c_up in COUNTRY_CODES_MAP:
        return COUNTRY_CODES_MAP[c_up]
    c_low = country_str.strip().lower()
    for code, info in COUNTRY_CODES_MAP.items():
        if info["name"].lower() == c_low or info["code"].lower() == c_low or code.lower() == c_low:
            return info
    return {"name": country_str, "code": "un", "flag_url": "https://flagcdn.com/w40/un.png", "emoji": "🌍"}

def get_league_country(league: str = "", sport: str = "") -> Dict[str, str]:
    """
    Определяет страну, русское человекопонятное название лиги/чемпионата, код флага для FlagCDN и эмодзи.
    """
    l_lower = (league or "").lower().strip()
    s_lower = (sport or "").lower().strip()
    combined = f"{l_lower} {s_lower}"

    # 1. Еврокубки и международные турниры
    if any(k in l_lower for k in ["champs_league", "champions_league", "лига чемпионов", "лиге чемпионов"]):
        return {"name": "Европа", "code": "eu", "flag_url": "https://flagcdn.com/w40/eu.png", "emoji": "🇪🇺", "league_ru": "Лига чемпионов УЕФА"}
    if any(k in l_lower for k in ["europa_league", "лига европы", "лиге европы"]):
        return {"name": "Европа", "code": "eu", "flag_url": "https://flagcdn.com/w40/eu.png", "emoji": "🇪🇺", "league_ru": "Лига Европы УЕФА"}
    if any(k in l_lower for k in ["conference_league", "лига конференций"]):
        return {"name": "Европа", "code": "eu", "flag_url": "https://flagcdn.com/w40/eu.png", "emoji": "🇪🇺", "league_ru": "Лига конференций УЕФА"}
    if any(k in l_lower for k in ["nations_league", "лига наций"]):
        return {"name": "Европа", "code": "eu", "flag_url": "https://flagcdn.com/w40/eu.png", "emoji": "🇪🇺", "league_ru": "Лига наций УЕФА"}
    if any(k in l_lower for k in ["copa_libertadores", "либертадорес"]):
        return {"name": "Юж. Америка", "code": "un", "flag_url": "https://flagcdn.com/w40/un.png", "emoji": "🌎", "league_ru": "Кубок Либертадорес"}
    if any(k in l_lower for k in ["copa_sudamericana", "судамерикана"]):
        return {"name": "Юж. Америка", "code": "un", "flag_url": "https://flagcdn.com/w40/un.png", "emoji": "🌎", "league_ru": "Южноамериканский кубок"}

    # 2. Англия
    if any(k in l_lower for k in ["soccer_epl", "epl", "premier_league", "премьер-лига англия", "апл"]):
        return {"name": "Англия", "code": "gb-eng", "flag_url": "https://flagcdn.com/w40/gb-eng.png", "emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "league_ru": "АПЛ • Чемпионат Англии"}
    if any(k in l_lower for k in ["championship", "чемпионшип"]):
        return {"name": "Англия", "code": "gb-eng", "flag_url": "https://flagcdn.com/w40/gb-eng.png", "emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "league_ru": "Чемпионшип • Англия"}
    if any(k in l_lower for k in ["fa_cup", "кубок англии"]):
        return {"name": "Англия", "code": "gb-eng", "flag_url": "https://flagcdn.com/w40/gb-eng.png", "emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "league_ru": "Кубок Англии"}
    if any(k in l_lower for k in ["efl_cup", "кубок лиги англ"]):
        return {"name": "Англия", "code": "gb-eng", "flag_url": "https://flagcdn.com/w40/gb-eng.png", "emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "league_ru": "Кубок лиги • Англия"}

    # 3. Испания
    if any(k in l_lower for k in ["spain_la_liga", "la_liga", "laliga", "ла лига", "примера испания"]):
        return {"name": "Испания", "code": "es", "flag_url": "https://flagcdn.com/w40/es.png", "emoji": "🇪🇸", "league_ru": "Ла Лига • Чемпионат Испании"}
    if any(k in l_lower for k in ["segunda", "сегунда"]):
        return {"name": "Испания", "code": "es", "flag_url": "https://flagcdn.com/w40/es.png", "emoji": "🇪🇸", "league_ru": "Сегунда • Испания"}
    if any(k in l_lower for k in ["copa_del_rey", "кубок короля", "кубок испании"]):
        return {"name": "Испания", "code": "es", "flag_url": "https://flagcdn.com/w40/es.png", "emoji": "🇪🇸", "league_ru": "Кубок Испании"}

    # 4. Италия
    if any(k in l_lower for k in ["italy_serie_a", "serie_a", "серия а", "серия a"]):
        return {"name": "Италия", "code": "it", "flag_url": "https://flagcdn.com/w40/it.png", "emoji": "🇮🇹", "league_ru": "Серия А • Чемпионат Италии"}
    if any(k in l_lower for k in ["italy_serie_b", "serie_b", "серия б", "серия b"]):
        return {"name": "Италия", "code": "it", "flag_url": "https://flagcdn.com/w40/it.png", "emoji": "🇮🇹", "league_ru": "Серия B • Чемпионат Италии"}
    if any(k in l_lower for k in ["coppa_italia", "кубок италии"]):
        return {"name": "Италия", "code": "it", "flag_url": "https://flagcdn.com/w40/it.png", "emoji": "🇮🇹", "league_ru": "Кубок Италии"}

    # 5. Германия
    if any(k in l_lower for k in ["germany_bundesliga2", "bundesliga2", "вторая бундеслига"]):
        return {"name": "Германия", "code": "de", "flag_url": "https://flagcdn.com/w40/de.png", "emoji": "🇩🇪", "league_ru": "Вторая Бундеслига • Германия"}
    if any(k in l_lower for k in ["germany_bundesliga", "bundesliga", "бундеслига"]):
        return {"name": "Германия", "code": "de", "flag_url": "https://flagcdn.com/w40/de.png", "emoji": "🇩🇪", "league_ru": "Бундеслига • Чемпионат Германии"}
    if any(k in l_lower for k in ["dfb_pokal", "кубок германии"]):
        return {"name": "Германия", "code": "de", "flag_url": "https://flagcdn.com/w40/de.png", "emoji": "🇩🇪", "league_ru": "Кубок Германии"}

    # 6. Франция
    if any(k in l_lower for k in ["france_ligue_two", "ligue_2", "лига 2"]):
        return {"name": "Франция", "code": "fr", "flag_url": "https://flagcdn.com/w40/fr.png", "emoji": "🇫🇷", "league_ru": "Лига 2 • Чемпионат Франции"}
    if any(k in l_lower for k in ["france_ligue_one", "ligue_1", "лига 1"]):
        return {"name": "Франция", "code": "fr", "flag_url": "https://flagcdn.com/w40/fr.png", "emoji": "🇫🇷", "league_ru": "Лига 1 • Чемпионат Франции"}
    if any(k in l_lower for k in ["coupe_de_france", "кубок франции"]):
        return {"name": "Франция", "code": "fr", "flag_url": "https://flagcdn.com/w40/fr.png", "emoji": "🇫🇷", "league_ru": "Кубок Франции"}

    # 7. Россия
    if any(k in l_lower for k in ["russia_premier_league", "rpl", "рпл", "премьер-лига россия"]):
        return {"name": "Россия", "code": "ru", "flag_url": "https://flagcdn.com/w40/ru.png", "emoji": "🇷🇺", "league_ru": "РПЛ • Чемпионат России"}
    if any(k in l_lower for k in ["fnl", "фнл", "первая лига россия"]):
        return {"name": "Россия", "code": "ru", "flag_url": "https://flagcdn.com/w40/ru.png", "emoji": "🇷🇺", "league_ru": "Первая лига • Россия"}
    if any(k in l_lower for k in ["кубок россии", "russian_cup"]):
        return {"name": "Россия", "code": "ru", "flag_url": "https://flagcdn.com/w40/ru.png", "emoji": "🇷🇺", "league_ru": "Кубок России"}

    # 8. Другие европейские и мировые чемпионаты
    if any(k in l_lower for k in ["eredivisie", "нидерланд"]):
        return {"name": "Нидерланды", "code": "nl", "flag_url": "https://flagcdn.com/w40/nl.png", "emoji": "🇳🇱", "league_ru": "Эредивизи • Чемпионат Нидерландов"}
    if any(k in l_lower for k in ["primeira_liga", "португал"]):
        return {"name": "Португалия", "code": "pt", "flag_url": "https://flagcdn.com/w40/pt.png", "emoji": "🇵🇹", "league_ru": "Примейра • Чемпионат Португалии"}
    if any(k in l_lower for k in ["super_league_turkey", "super_lig", "турци"]):
        return {"name": "Турция", "code": "tr", "flag_url": "https://flagcdn.com/w40/tr.png", "emoji": "🇹🇷", "league_ru": "Суперлига • Чемпионат Турции"}
    if any(k in l_lower for k in ["belgium_first_div", "бельги"]):
        return {"name": "Бельгия", "code": "be", "flag_url": "https://flagcdn.com/w40/be.png", "emoji": "🇧🇪", "league_ru": "Про-Лига • Чемпионат Бельгии"}
    if any(k in l_lower for k in ["scotland", "шотланд"]):
        return {"name": "Шотландия", "code": "gb-sct", "flag_url": "https://flagcdn.com/w40/gb-sct.png", "emoji": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "league_ru": "Премьершип • Шотландия"}
    if any(k in l_lower for k in ["switzerland", "швейцар"]):
        return {"name": "Швейцария", "code": "ch", "flag_url": "https://flagcdn.com/w40/ch.png", "emoji": "🇨🇭", "league_ru": "Суперлига • Швейцария"}
    if any(k in l_lower for k in ["austria", "австри"]):
        return {"name": "Австрия", "code": "at", "flag_url": "https://flagcdn.com/w40/at.png", "emoji": "🇦🇹", "league_ru": "Бундеслига • Австрия"}
    if any(k in l_lower for k in ["greece", "греци"]):
        return {"name": "Греция", "code": "gr", "flag_url": "https://flagcdn.com/w40/gr.png", "emoji": "🇬🇷", "league_ru": "Суперлига • Греция"}
    if any(k in l_lower for k in ["brazil", "бразил", "brasileirao"]):
        return {"name": "Бразилия", "code": "br", "flag_url": "https://flagcdn.com/w40/br.png", "emoji": "🇧🇷", "league_ru": "Серия А • Чемпионат Бразилии"}
    if any(k in l_lower for k in ["argentina", "аргентин"]):
        return {"name": "Аргентина", "code": "ar", "flag_url": "https://flagcdn.com/w40/ar.png", "emoji": "🇦🇷", "league_ru": "Примера • Чемпионат Аргентины"}
    if any(k in l_lower for k in ["mls", "млс"]):
        return {"name": "США", "code": "us", "flag_url": "https://flagcdn.com/w40/us.png", "emoji": "🇺🇸", "league_ru": "МЛС • Чемпионат США"}
    if any(k in l_lower for k in ["saudi", "саудов"]):
        return {"name": "Саудовская Аравия", "code": "sa", "flag_url": "https://flagcdn.com/w40/sa.png", "emoji": "🇸🇦", "league_ru": "Про-Лига • Саудовская Аравия"}

    # 9. Хоккей
    if any(k in l_lower for k in ["icehockey_nhl", "nhl", "нхл"]):
        return {"name": "США / Канада", "code": "us", "flag_url": "https://flagcdn.com/w40/us.png", "emoji": "🇺🇸", "league_ru": "НХЛ • Регулярный чемпионат"}
    if any(k in l_lower for k in ["icehockey_khl", "khl", "кхл"]):
        return {"name": "Россия", "code": "ru", "flag_url": "https://flagcdn.com/w40/ru.png", "emoji": "🇷🇺", "league_ru": "КХЛ • Континентальная лига"}
    if any(k in l_lower for k in ["vhl", "вхл"]):
        return {"name": "Россия", "code": "ru", "flag_url": "https://flagcdn.com/w40/ru.png", "emoji": "🇷🇺", "league_ru": "ВХЛ • Чемпионат России"}
    if any(k in l_lower for k in ["mhl", "мхл"]):
        return {"name": "Россия", "code": "ru", "flag_url": "https://flagcdn.com/w40/ru.png", "emoji": "🇷🇺", "league_ru": "МХЛ • Молодежная лига"}
    if any(k in l_lower for k in ["allsvenskan", "швеци"]):
        return {"name": "Швеция", "code": "se", "flag_url": "https://flagcdn.com/w40/se.png", "emoji": "🇸🇪", "league_ru": "Allsvenskan • Чемпионат Швеции"}
    if any(k in l_lower for k in ["shl", "шхл"]):
        return {"name": "Швеция", "code": "se", "flag_url": "https://flagcdn.com/w40/se.png", "emoji": "🇸🇪", "league_ru": "ШХЛ • Чемпионат Швеции"}
    if any(k in l_lower for k in ["liiga", "финлянд"]):
        return {"name": "Финляндия", "code": "fi", "flag_url": "https://flagcdn.com/w40/fi.png", "emoji": "🇫🇮", "league_ru": "Лиига • Чемпионат Финляндии"}

    # 10. Баскетбол
    if any(k in l_lower for k in ["basketball_nba", "nba", "нба"]):
        return {"name": "США", "code": "us", "flag_url": "https://flagcdn.com/w40/us.png", "emoji": "🇺🇸", "league_ru": "НБА • Чемпионат США"}
    if any(k in l_lower for k in ["euroleague", "евролига"]):
        return {"name": "Европа", "code": "eu", "flag_url": "https://flagcdn.com/w40/eu.png", "emoji": "🇪🇺", "league_ru": "Евролига • Баскетбол"}
    if any(k in l_lower for k in ["vtb", "втб"]):
        return {"name": "Россия", "code": "ru", "flag_url": "https://flagcdn.com/w40/ru.png", "emoji": "🇷🇺", "league_ru": "Единая лига ВТБ"}

    # 11. Американский футбол
    if any(k in l_lower for k in ["nfl", "нфл"]):
        return {"name": "США", "code": "us", "flag_url": "https://flagcdn.com/w40/us.png", "emoji": "🇺🇸", "league_ru": "НФЛ • Американский футбол"}
    if any(k in l_lower for k in ["ncaa", "ncaaf"]):
        return {"name": "США", "code": "us", "flag_url": "https://flagcdn.com/w40/us.png", "emoji": "🇺🇸", "league_ru": "NCAA • Американский футбол"}

    # 12. Единоборства и теннис
    if any(k in combined for k in ["ufc", "юфс", "mma", "мма"]):
        return {"name": "Международный", "code": "un", "flag_url": "https://flagcdn.com/w40/un.png", "emoji": "🥊", "league_ru": "UFC • Бои"}
    if any(k in combined for k in ["atp", "wta", "tennis", "теннис"]):
        return {"name": "Международный", "code": "un", "flag_url": "https://flagcdn.com/w40/un.png", "emoji": "🎾", "league_ru": "ATP / WTA Тур • Теннис"}

    # Если есть читаемое название лиги без технических префиксов soccer_
    clean_l = league.replace("soccer_", "").replace("basketball_", "").replace("icehockey_", "").replace("americanfootball_", "").replace("_", " ").title().strip()
    return {"name": "Спорт", "code": "un", "flag_url": "https://flagcdn.com/w40/un.png", "emoji": "🌐", "league_ru": clean_l or "Лига"}
