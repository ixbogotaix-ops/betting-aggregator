"""
Сервис получения эмблем спортивных команд и флагов стран.
Использует базу TheSportsDB (API v3), локальный кэш на диске, ESPN CDN и умную нормализацию названий.
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
                    _LOGO_CACHE.update(data)
                    logger.info(f"Загружено {len(_LOGO_CACHE)} эмблем из дискового кэша")
        except Exception as e:
            logger.warning(f"Ошибка загрузки дискового кэша эмблем: {e}")

def _save_to_disk_cache(key: str, url: str):
    global _LOGO_CACHE
    _LOGO_CACHE[key] = url
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_LOGO_CACHE, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Ошибка сохранения эмблемы в дисковый кэш: {e}")

# Загружаем кэш при импорте модуля
_load_disk_cache()

# Предустановленные эмблемы популярных клубов (высокое качество, мгновенная отдача без запросов)
KNOWN_TEAM_LOGOS = {
    # Португалия, Испания
    "porto": "https://r2.thesportsdb.com/images/media/team/badge/xu47rb1628855600.png",
    "fc porto": "https://r2.thesportsdb.com/images/media/team/badge/xu47rb1628855600.png",
    "benfica": "https://r2.thesportsdb.com/images/media/team/badge/d94i0u1628855734.png",
    "sporting cp": "https://r2.thesportsdb.com/images/media/team/badge/5k99p81628855849.png",
    "real betis": "https://r2.thesportsdb.com/images/media/team/badge/2oqulv1663245386.png",
    "betis": "https://r2.thesportsdb.com/images/media/team/badge/2oqulv1663245386.png",
    "real madrid": "https://a.espncdn.com/i/teamlogos/soccer/500/86.png",
    "barcelona": "https://a.espncdn.com/i/teamlogos/soccer/500/83.png",
    "atletico madrid": "https://a.espncdn.com/i/teamlogos/soccer/500/1068.png",
    "athletic club": "https://r2.thesportsdb.com/images/media/team/badge/myl7c31677056352.png",
    "athletic bilbao": "https://r2.thesportsdb.com/images/media/team/badge/myl7c31677056352.png",
    "sevilla": "https://a.espncdn.com/i/teamlogos/soccer/500/243.png",
    "valencia": "https://a.espncdn.com/i/teamlogos/soccer/500/94.png",
    "villarreal": "https://a.espncdn.com/i/teamlogos/soccer/500/102.png",
    "real sociedad": "https://a.espncdn.com/i/teamlogos/soccer/500/89.png",

    # Англия
    "liverpool": "https://r2.thesportsdb.com/images/media/team/badge/kfaher1737969724.png",
    "manchester city": "https://a.espncdn.com/i/teamlogos/soccer/500/382.png",
    "manchester united": "https://a.espncdn.com/i/teamlogos/soccer/500/360.png",
    "arsenal": "https://a.espncdn.com/i/teamlogos/soccer/500/359.png",
    "chelsea": "https://a.espncdn.com/i/teamlogos/soccer/500/363.png",
    "tottenham": "https://a.espncdn.com/i/teamlogos/soccer/500/367.png",
    "newcastle united": "https://a.espncdn.com/i/teamlogos/soccer/500/364.png",
    "newcastle": "https://a.espncdn.com/i/teamlogos/soccer/500/364.png",
    "aston villa": "https://a.espncdn.com/i/teamlogos/soccer/500/362.png",

    # Италия
    "inter milan": "https://a.espncdn.com/i/teamlogos/soccer/500/110.png",
    "inter": "https://a.espncdn.com/i/teamlogos/soccer/500/110.png",
    "ac milan": "https://a.espncdn.com/i/teamlogos/soccer/500/103.png",
    "milan": "https://a.espncdn.com/i/teamlogos/soccer/500/103.png",
    "juventus": "https://a.espncdn.com/i/teamlogos/soccer/500/111.png",
    "roma": "https://a.espncdn.com/i/teamlogos/soccer/500/104.png",
    "napoli": "https://a.espncdn.com/i/teamlogos/soccer/500/114.png",
    "lazio": "https://a.espncdn.com/i/teamlogos/soccer/500/112.png",
    "atalanta": "https://a.espncdn.com/i/teamlogos/soccer/500/107.png",
    "como": "https://r2.thesportsdb.com/images/media/team/badge/02x81t1627405841.png",
    "como 1907": "https://r2.thesportsdb.com/images/media/team/badge/02x81t1627405841.png",

    # Германия
    "bayern munich": "https://r2.thesportsdb.com/images/media/team/badge/01ogkh1716960412.png",
    "bayern munchen": "https://r2.thesportsdb.com/images/media/team/badge/01ogkh1716960412.png",
    "fc bayern munchen": "https://r2.thesportsdb.com/images/media/team/badge/01ogkh1716960412.png",
    "bayern": "https://r2.thesportsdb.com/images/media/team/badge/01ogkh1716960412.png",
    "borussia dortmund": "https://a.espncdn.com/i/teamlogos/soccer/500/124.png",
    "dortmund": "https://a.espncdn.com/i/teamlogos/soccer/500/124.png",
    "bayer leverkusen": "https://a.espncdn.com/i/teamlogos/soccer/500/131.png",
    "leverkusen": "https://a.espncdn.com/i/teamlogos/soccer/500/131.png",
    "rb leipzig": "https://a.espncdn.com/i/teamlogos/soccer/500/11420.png",

    # Франция
    "paris saint germain": "https://a.espncdn.com/i/teamlogos/soccer/500/160.png",
    "psg": "https://a.espncdn.com/i/teamlogos/soccer/500/160.png",
    "marseille": "https://r2.thesportsdb.com/images/media/team/badge/c6bazh1779212287.png",
    "monaco": "https://a.espncdn.com/i/teamlogos/soccer/500/175.png",
    "lyon": "https://a.espncdn.com/i/teamlogos/soccer/500/167.png",
    "lille": "https://a.espncdn.com/i/teamlogos/soccer/500/166.png",
    "rennes": "https://a.espncdn.com/i/teamlogos/soccer/500/171.png",
    "troyes": "https://r2.thesportsdb.com/images/media/team/badge/sl5kzg1766617559.png",
    "rc lens": "https://r2.thesportsdb.com/images/media/team/badge/3pxoum1598797195.png",
    "lens": "https://r2.thesportsdb.com/images/media/team/badge/3pxoum1598797195.png",

    # Нидерланды, Австрия, Турция, прочие футбольные
    "feyenoord": "https://r2.thesportsdb.com/images/media/team/badge/uturtx1473534803.png",
    "ajax": "https://r2.thesportsdb.com/images/media/team/badge/gr473g1737969749.png",
    "psv": "https://r2.thesportsdb.com/images/media/team/badge/a0w0h71578342416.png",
    "lask": "https://r2.thesportsdb.com/images/media/team/badge/oox26l1683556395.png",
    "lask linz": "https://r2.thesportsdb.com/images/media/team/badge/oox26l1683556395.png",
    "besiktas": "https://r2.thesportsdb.com/images/media/team/badge/svo05k1776827439.png",
    "besiktas jk": "https://r2.thesportsdb.com/images/media/team/badge/svo05k1776827439.png",
    "fenerbahce": "https://r2.thesportsdb.com/images/media/team/badge/7f692v1776827429.png",
    "galatasaray": "https://r2.thesportsdb.com/images/media/team/badge/0gnhj61776827417.png",
    "melbourne victory": "https://r2.thesportsdb.com/images/media/team/badge/wwvsqx1473454564.png",
    "fc seoul": "https://r2.thesportsdb.com/images/media/team/badge/31z1zf1579473186.png",
    "seoul": "https://r2.thesportsdb.com/images/media/team/badge/31z1zf1579473186.png",
    "londrina": "https://r2.thesportsdb.com/images/media/team/badge/xp2z9j1740846583.png",

    # Баскетбол (Евролига & NBA)
    "anadolu efes": "https://r2.thesportsdb.com/images/media/team/badge/uldz0d1782050729.png",
    "hapoel tel aviv": "https://r2.thesportsdb.com/images/media/team/badge/yrrsml1767366305.png",
    "paris basketball": "https://r2.thesportsdb.com/images/media/team/badge/9q0d6x1726681476.png",
    "virtus bologna": "https://r2.thesportsdb.com/images/media/team/badge/kqfwqq1659402893.png",
    "virtus segafredo bologna": "https://r2.thesportsdb.com/images/media/team/badge/kqfwqq1659402893.png",
    "olimpia milano": "https://r2.thesportsdb.com/images/media/team/badge/aurbi61790186853.png",
    "pallacanestro olimpia milano": "https://r2.thesportsdb.com/images/media/team/badge/aurbi61790186853.png",
    "dubai basketball": "https://r2.thesportsdb.com/images/media/team/badge/9q0d6x1726681476.png",
    "panathinaikos": "https://r2.thesportsdb.com/images/media/team/badge/9m26w61659402928.png",
    "olympiacos": "https://r2.thesportsdb.com/images/media/team/badge/j5v0e21659402919.png",
    "maccabi tel aviv": "https://r2.thesportsdb.com/images/media/team/badge/4v43z91659402909.png",
    "crvena zvezda": "https://r2.thesportsdb.com/images/media/team/badge/osgmbz1781157114.png",
    "partizan": "https://r2.thesportsdb.com/images/media/team/badge/w3i01b1660995200.png",
    "zalgiris": "https://r2.thesportsdb.com/images/media/team/badge/047f0x1659402947.png",
    "asvel": "https://r2.thesportsdb.com/images/media/team/badge/10s47o1611139483.png",
    "los angeles lakers": "https://a.espncdn.com/i/teamlogos/nba/500/lal.png",
    "golden state warriors": "https://a.espncdn.com/i/teamlogos/nba/500/gsw.png",
    "boston celtics": "https://a.espncdn.com/i/teamlogos/nba/500/bos.png",

    # Американский футбол NFL
    "denver broncos": "https://r2.thesportsdb.com/images/media/team/badge/zy3m9v1784718707.png",
    "seattle seahawks": "https://r2.thesportsdb.com/images/media/team/badge/1t84c51784752684.png",

    # Хоккей (Швеция Allsvenskan / SHL / KHL / NHL)
    "leksands if": "https://r2.thesportsdb.com/images/media/team/badge/ruij751571478402.png",
    "leksands": "https://r2.thesportsdb.com/images/media/team/badge/ruij751571478402.png",
    "vimmerby hc": "https://r2.thesportsdb.com/images/media/team/badge/fu3agb1718712090.png",
    "vimmerby": "https://r2.thesportsdb.com/images/media/team/badge/fu3agb1718712090.png",
    "mora ik": "https://r2.thesportsdb.com/images/media/team/badge/3p58o01571572794.png",
    "mora": "https://r2.thesportsdb.com/images/media/team/badge/3p58o01571572794.png",
    "visby roma hk": "https://r2.thesportsdb.com/images/media/team/badge/gx7bzm1719659863.png",
    "visby roma": "https://r2.thesportsdb.com/images/media/team/badge/gx7bzm1719659863.png",
    "nybro vikings if": "https://r2.thesportsdb.com/images/media/team/badge/lxq87h1700826490.png",
    "nybro vikings": "https://r2.thesportsdb.com/images/media/team/badge/lxq87h1700826490.png",
    "ik oskarshamn": "https://r2.thesportsdb.com/images/media/team/badge/g047d01571572694.png",
    "oskarshamn": "https://r2.thesportsdb.com/images/media/team/badge/g047d01571572694.png",
    "kalmar hc": "https://r2.thesportsdb.com/images/media/team/badge/1oop2f1700826368.png",
    "kalmar": "https://r2.thesportsdb.com/images/media/team/badge/1oop2f1700826368.png",
    "sodertalje sk": "https://r2.thesportsdb.com/images/media/team/badge/5jkc0q1700826206.png",
    "sodertalje": "https://r2.thesportsdb.com/images/media/team/badge/5jkc0q1700826206.png",
    "vasteras ik": "https://r2.thesportsdb.com/images/media/team/badge/mscha61644586515.png",
    "vasteras": "https://r2.thesportsdb.com/images/media/team/badge/mscha61644586515.png",
    "modo hockey": "https://r2.thesportsdb.com/images/media/team/badge/wpvvyr1421609878.png",
    "modo": "https://r2.thesportsdb.com/images/media/team/badge/wpvvyr1421609878.png",
    "brynas": "https://r2.thesportsdb.com/images/media/team/badge/i0jebc1571477785.png",
    "farjestad": "https://r2.thesportsdb.com/images/media/team/badge/r70w0v1571477884.png",
    "frolunda": "https://r2.thesportsdb.com/images/media/team/badge/66g8g61644586397.png",
    "djurgarden": "https://r2.thesportsdb.com/images/media/team/badge/951iha1571477840.png",
    "ska st petersburg": "https://r2.thesportsdb.com/images/media/team/badge/vwwtxq1421612444.png",
    "cska moscow": "https://r2.thesportsdb.com/images/media/team/badge/sstrts1421612411.png",
    "new york rangers": "https://a.espncdn.com/i/teamlogos/nhl/500/nyr.png",
    "edmonton oilers": "https://a.espncdn.com/i/teamlogos/nhl/500/edm.png",
    "florida panthers": "https://a.espncdn.com/i/teamlogos/nhl/500/fla.png",
}

def normalize_team_name(name: str) -> List[str]:
    """
    Нормализует название команды, удаляя диакритические знаки (акценты),
    специальные символы, и спортивные суффиксы/префиксы (FC, CF, IF, IK, HK, J.K. и т.д.).
    Возвращает упорядоченный список вариантов для поиска.
    """
    if not name:
        return []

    # 1. Убираем акценты (München -> Munchen, Beşiktaş -> Besiktas)
    nfkd = unicodedata.normalize('NFKD', name)
    no_accents = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    
    # Заменяем слэши и дефисы на пробелы
    cleaned_base = no_accents.replace('/', ' ').replace('-', ' ')
    cleaned_base = re.sub(r'[^a-zA-Z0-9\s]', ' ', cleaned_base)
    cleaned_base = ' '.join(cleaned_base.split()).lower()

    # 2. Убираем распространенные спортивные приставки и суффиксы
    # (J.K., F.C., I.F., I.K., H.K., S.K., H.C., B.K., A.C., C.F.)
    pattern = r'\b(jk|fc|cf|if|ik|hk|sk|hc|bk|fk|ac|bc|kk|sc|as|cd|ud|rb|afc|vfb|vfl|tsv|1907|1899)\b'
    stripped = re.sub(pattern, '', cleaned_base, flags=re.IGNORECASE)
    stripped = ' '.join(stripped.split()).lower()

    variants = []
    # Вариант 1: Очищенное имя без приставок (напр. "besiktas", "porto", "vasteras", "sodertalje")
    if stripped and stripped not in variants:
        variants.append(stripped)

    # Вариант 2: Базовое имя без акцентов (напр. "visby roma hk", "nybro vikings if")
    if cleaned_base and cleaned_base not in variants:
        variants.append(cleaned_base)

    # Вариант 3: Первые 2 слова, если название длинное (напр. "virtus segafredo bologna" -> "virtus bologna")
    parts = stripped.split()
    if len(parts) >= 2:
        short_two = f"{parts[0]} {parts[-1]}"
        if short_two not in variants:
            variants.append(short_two)

    # Вариант 4: Первое главное слово (если это не стоп-слово)
    if parts and len(parts[0]) > 3 and parts[0] not in variants:
        variants.append(parts[0])

    return variants

def get_team_logo(team_name: str, sport: str = "") -> str:
    """
    Возвращает прямую ссылку на прозрачную PNG эмблему команды.
    Проверяет:
      1. Предустановленный словарь известных клубов.
      2. Дисковый и оперативный кэш.
      3. TheSportsDB API v3 с несколькими попытками нормализации.
      4. Стилизованный Fallback с уникальным градиентом.
    """
    if not team_name:
        return "https://ui-avatars.com/api/?name=Team&background=1e293b&color=38bdf8&size=128&bold=true&rounded=true"

    search_variants = normalize_team_name(team_name)

    # 1. Поиск по предустановленному словарю известных клубов
    for var in search_variants:
        if var in KNOWN_TEAM_LOGOS:
            return KNOWN_TEAM_LOGOS[var]
        for known_k, known_url in KNOWN_TEAM_LOGOS.items():
            if var == known_k or (len(var) > 4 and var in known_k) or (len(known_k) > 4 and known_k in var):
                return known_url

    # 2. Проверка кэша (в памяти и на диске)
    for var in search_variants:
        if var in _LOGO_CACHE:
            return _LOGO_CACHE[var]

    # Для единоборств (UFC / MMA) и тенниса возвращаем официальные значки организаций
    s_low = (sport or "").lower()
    if any(x in s_low for x in ["mma", "ufc"]):
        return "https://a.espncdn.com/combiner/i?img=/i/teamlogos/mma/500/ufc.png"
    if any(x in s_low for x in ["tennis", "теннис", "atp", "wta"]):
        return "https://a.espncdn.com/combiner/i?img=/i/teamlogos/tennis/500/atp.png"

    # 3. Поиск через TheSportsDB API v3 (официальный ключ '3')
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SportsAggregator/2.0"}
    
    for query_candidate in search_variants:
        if len(query_candidate) < 3:
            continue
        try:
            url = f"https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t={urllib.parse.quote(query_candidate)}"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if data and data.get("teams"):
                    badge = data["teams"][0].get("strBadge")
                    if badge and badge.startswith("http"):
                        # Сохраняем во все варианты для мгновенного нахождения в будущем
                        for v in search_variants:
                            _save_to_disk_cache(v, badge)
                        return badge
        except Exception:
            continue

    # 4. Стильный Fallback с цветами спортивного приложения
    fallback_url = f"https://ui-avatars.com/api/?name={urllib.parse.quote(team_name)}&background=1e293b&color=38bdf8&size=128&bold=true&rounded=true"
    if search_variants:
        _save_to_disk_cache(search_variants[0], fallback_url)
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

    # Швеция (Allsvenskan, SHL)
    if any(x in combined for x in ["sweden", "allsvensk", "shl", "швеци"]):
        return {
            "name": "Швеция",
            "code": "se",
            "flag_url": "https://flagcdn.com/w40/se.png",
            "emoji": "🇸🇪"
        }

    # Португалия
    if any(x in combined for x in ["portugal", "primeira", "португал"]):
        return {
            "name": "Португалия",
            "code": "pt",
            "flag_url": "https://flagcdn.com/w40/pt.png",
            "emoji": "🇵🇹"
        }

    # Нидерланды
    if any(x in combined for x in ["netherlands", "eredivisie", "нидерланд"]):
        return {
            "name": "Нидерланды",
            "code": "nl",
            "flag_url": "https://flagcdn.com/w40/nl.png",
            "emoji": "🇳🇱"
        }

    # Турция
    if any(x in combined for x in ["turkey", "super lig", "турци"]):
        return {
            "name": "Турция",
            "code": "tr",
            "flag_url": "https://flagcdn.com/w40/tr.png",
            "emoji": "🇹🇷"
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
