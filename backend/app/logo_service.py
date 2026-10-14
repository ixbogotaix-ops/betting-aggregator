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
    "osasuna": "https://a.espncdn.com/i/teamlogos/soccer/500/97.png",
    "ca osasuna": "https://a.espncdn.com/i/teamlogos/soccer/500/97.png",
    "getafe": "https://a.espncdn.com/i/teamlogos/soccer/500/2922.png",
    "rayo vallecano": "https://a.espncdn.com/i/teamlogos/soccer/500/101.png",
    "alaves": "https://a.espncdn.com/i/teamlogos/soccer/500/96.png",
    "deportivo alaves": "https://a.espncdn.com/i/teamlogos/soccer/500/96.png",
    "espanyol": "https://a.espncdn.com/i/teamlogos/soccer/500/88.png",
    "mallorca": "https://a.espncdn.com/i/teamlogos/soccer/500/84.png",
    "las palmas": "https://a.espncdn.com/i/teamlogos/soccer/500/90.png",
    "leganes": "https://a.espncdn.com/i/teamlogos/soccer/500/2876.png",
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
    "ac milan": "https://a.espncdn.com/i/teamlogos/soccer/500/103.png",
    "milan": "https://a.espncdn.com/i/teamlogos/soccer/500/103.png",
    "juventus": "https://a.espncdn.com/i/teamlogos/soccer/500/111.png",
    "napoli": "https://a.espncdn.com/i/teamlogos/soccer/500/114.png",
    "roma": "https://a.espncdn.com/i/teamlogos/soccer/500/104.png",
    "lazio": "https://a.espncdn.com/i/teamlogos/soccer/500/112.png",
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
    "union berlin": "https://a.espncdn.com/i/teamlogos/soccer/500/8980.png",
    "hoffenheim": "https://a.espncdn.com/i/teamlogos/soccer/500/7911.png",
    "st pauli": "https://a.espncdn.com/i/teamlogos/soccer/500/133.png",
    "heidenheim": "https://a.espncdn.com/i/teamlogos/soccer/500/10260.png",
    "bochum": "https://a.espncdn.com/i/teamlogos/soccer/500/121.png",
    "holstein kiel": "https://a.espncdn.com/i/teamlogos/soccer/500/6722.png",
    "koln": "https://a.espncdn.com/i/teamlogos/soccer/500/122.png",
    "1. fc koln": "https://a.espncdn.com/i/teamlogos/soccer/500/122.png",
    "fc koln": "https://a.espncdn.com/i/teamlogos/soccer/500/122.png",
    "hamburger sv": "https://a.espncdn.com/i/teamlogos/soccer/500/127.png",
    "schalke 04": "https://a.espncdn.com/i/teamlogos/soccer/500/133.png",
    "sc paderborn": "https://r2.thesportsdb.com/images/media/team/badge/kddvva1566048058.png",
    "elversberg": "https://r2.thesportsdb.com/images/media/team/badge/6t292u1685958784.png",

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
    "auxerre": "https://a.espncdn.com/i/teamlogos/soccer/500/163.png",
    "le havre": "https://a.espncdn.com/i/teamlogos/soccer/500/272.png",
    "lorient": "https://a.espncdn.com/i/teamlogos/soccer/500/273.png",
    "troyes": "https://r2.thesportsdb.com/images/media/team/badge/sl5kzg1766617559.png",
    "le mans": "https://r2.thesportsdb.com/images/media/team/badge/wjhziv1700145026.png",
    "le mans fc": "https://r2.thesportsdb.com/images/media/team/badge/wjhziv1700145026.png",

    # --- Еврокубки и другие европейские клубы ---
    "porto": "https://r2.thesportsdb.com/images/media/team/badge/xu47rb1628855600.png",
    "benfica": "https://r2.thesportsdb.com/images/media/team/badge/d94i0u1628855734.png",
    "sporting cp": "https://r2.thesportsdb.com/images/media/team/badge/5k99p81628855849.png",
    "ajax": "https://r2.thesportsdb.com/images/media/team/badge/gr473g1737969749.png",
    "psv": "https://r2.thesportsdb.com/images/media/team/badge/a0w0h71578342416.png",
    "feyenoord": "https://r2.thesportsdb.com/images/media/team/badge/uturtx1473534803.png",
    "nec nijmegen": "https://r2.thesportsdb.com/images/media/team/badge/t5qjle1701019868.png",
    "nijmegen": "https://r2.thesportsdb.com/images/media/team/badge/t5qjle1701019868.png",
    "olympiakos": "https://a.espncdn.com/i/teamlogos/soccer/500/449.png",
    "olympiakos piraeus": "https://a.espncdn.com/i/teamlogos/soccer/500/449.png",
    "panathinaikos": "https://r2.thesportsdb.com/images/media/team/badge/9m26w61659402928.png",
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
    "fenerbahce": "https://r2.thesportsdb.com/images/media/team/badge/7f692v1776827429.png",
    "galatasaray": "https://r2.thesportsdb.com/images/media/team/badge/0gnhj61776827417.png",

    # --- Российская Премьер-Лига (РПЛ) ---
    "spartak moscow": "https://r2.thesportsdb.com/images/media/team/badge/swqtsq1421612470.png",
    "spartak": "https://r2.thesportsdb.com/images/media/team/badge/swqtsq1421612470.png",
    "zenit": "https://r2.thesportsdb.com/images/media/team/badge/rwptxx1421612497.png",
    "zenit st petersburg": "https://r2.thesportsdb.com/images/media/team/badge/rwptxx1421612497.png",
    "cska moscow": "https://r2.thesportsdb.com/images/media/team/badge/sstrts1421612411.png",
    "cska": "https://r2.thesportsdb.com/images/media/team/badge/sstrts1421612411.png",
    "lokomotiv moscow": "https://r2.thesportsdb.com/images/media/team/badge/vyurvt1421612431.png",
    "lokomotiv": "https://r2.thesportsdb.com/images/media/team/badge/vyurvt1421612431.png",
    "dynamo moscow": "https://r2.thesportsdb.com/images/media/team/badge/uuwyqu1421612419.png",
    "krasnodar": "https://r2.thesportsdb.com/images/media/team/badge/xuvuvy1421612423.png",
    "rostov": "https://r2.thesportsdb.com/images/media/team/badge/uuxtts1421612439.png",
    "rubin kazan": "https://r2.thesportsdb.com/images/media/team/badge/trvqxs1421612441.png",
    "krylya sovetov": "https://r2.thesportsdb.com/images/media/team/badge/uvwxsw1421612428.png",
    "akhmat grozny": "https://r2.thesportsdb.com/images/media/team/badge/twxqrq1421612465.png",
    "sochi": "https://r2.thesportsdb.com/images/media/team/badge/i0j7a21571477926.png",

    # --- Баскетбол (Евролига & NBA) ---
    "saski baskonia": "https://r2.thesportsdb.com/images/media/team/badge/p4x3o61767366090.png",
    "baskonia": "https://r2.thesportsdb.com/images/media/team/badge/p4x3o61767366090.png",
    "anadolu efes": "https://r2.thesportsdb.com/images/media/team/badge/uldz0d1782050729.png",
    "hapoel tel aviv": "https://r2.thesportsdb.com/images/media/team/badge/yrrsml1767366305.png",
    "paris basketball": "https://r2.thesportsdb.com/images/media/team/badge/9q0d6x1726681476.png",
    "virtus bologna": "https://r2.thesportsdb.com/images/media/team/badge/kqfwqq1659402893.png",
    "olimpia milano": "https://r2.thesportsdb.com/images/media/team/badge/aurbi61790186853.png",
    "olympiacos": "https://r2.thesportsdb.com/images/media/team/badge/j5v0e21659402919.png",
    "maccabi tel aviv": "https://r2.thesportsdb.com/images/media/team/badge/4v43z91659402909.png",
    "crvena zvezda": "https://r2.thesportsdb.com/images/media/team/badge/osgmbz1781157114.png",
    "partizan": "https://r2.thesportsdb.com/images/media/team/badge/w3i01b1660995200.png",
    "zalgiris": "https://r2.thesportsdb.com/images/media/team/badge/047f0x1659402947.png",
    "asvel": "https://r2.thesportsdb.com/images/media/team/badge/10s47o1611139483.png",
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
    "ska st petersburg": "https://r2.thesportsdb.com/images/media/team/badge/vwwtxq1421612444.png",
    "new york rangers": "https://a.espncdn.com/i/teamlogos/nhl/500/nyr.png",
    "edmonton oilers": "https://a.espncdn.com/i/teamlogos/nhl/500/edm.png",
    "florida panthers": "https://a.espncdn.com/i/teamlogos/nhl/500/fla.png",
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

def normalize_team_name(name: str) -> List[str]:
    """
    Интеллектуальная нормализация названия команды:
    - Удаляет диакритические знаки (Plzeň -> Plzen, Köln -> Koln)
    - Убирает префиксы: 1. FC, PFC, CA, CD, RC, SC, FSV, FC, FK
    - Убирает суффиксы: TC, IF, IK, HK, SK, HC, BK, CF
    - Поддерживает русскую транслитерацию
    - Возвращает упорядоченный список кандидатов поиска
    """
    if not name:
        return []

    variants: List[str] = []

    # Транслитерация с русского, если есть кириллица
    latin_name = transliterate_ru(name) if re.search(r'[а-яё]', name, re.IGNORECASE) else name

    # Нормализация диакритических знаков (Unicode NFKD)
    nfkd = unicodedata.normalize('NFKD', latin_name)
    no_accents = ''.join([c for c in nfkd if not unicodedata.combining(c)])

    # Базовая очистка знаков
    clean_str = no_accents.replace('/', ' ').replace('-', ' ').replace('_', ' ')
    clean_str = re.sub(r'[^a-zA-Z0-9\s]', ' ', clean_str)
    base_clean = ' '.join(clean_str.split()).lower()

    if base_clean and base_clean not in variants:
        variants.append(base_clean)

    # 1. Убираем ведущие префиксы (1. FC Köln -> Koln, CA Osasuna -> Osasuna, PFC Levski -> Levski)
    prefix_pattern = r'^(1\.\s*|1\s+fc\s+|pfc\s+|cf\s+|ca\s+|cd\s+|rc\s+|sc\s+|fsv\s+|ssv\s+|fk\s+|fc\s+|bc\s+|hc\s+)'
    without_prefix = re.sub(prefix_pattern, '', base_clean, flags=re.IGNORECASE).strip()
    if without_prefix and without_prefix not in variants:
        variants.append(without_prefix)

    # 2. Убираем хвостовые суффиксы (Ferencváros TC -> Ferencvaros, Nybro Vikings IF -> Nybro Vikings)
    suffix_pattern = r'\b(tc|jk|fc|cf|if|ik|hk|sk|hc|bk|fk|ac|bc|kk|sc|as|cd|ud|rb|afc|vfb|vfl|tsv|1907|1899)\b'
    without_suffix = re.sub(suffix_pattern, '', without_prefix, flags=re.IGNORECASE).strip()
    without_suffix = ' '.join(without_suffix.split()).lower()
    if without_suffix and without_suffix not in variants:
        variants.append(without_suffix)

    # 3. Первое главное слово (если > 3 символов)
    parts = without_suffix.split()
    if parts and len(parts[0]) > 3 and parts[0] not in variants:
        variants.append(parts[0])

    return variants

def get_team_logo(team_name: str, sport: str = "") -> Optional[str]:
    """
    Возвращает прямую ссылку на прозрачную эмблему команды из ESPN / TheSportsDB CDN.
    Если не найдено — возвращает None, чтобы фронтенд отобразил стильный SVG/CSS векторный бейдж.
    """
    if not team_name:
        return None

    search_variants = normalize_team_name(team_name)

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

    # 3. Запрос к TheSportsDB API v3 (официальный ключ '3')
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
                        for v in search_variants:
                            _save_to_disk_cache(v, badge)
                        return badge
        except Exception:
            continue

    return None

def get_league_country(league: str = "", sport: str = "") -> Dict[str, str]:
    """
    Определяет страну, код флага для FlagCDN и эмодзи по названию лиги.
    """
    l_lower = (league or "").lower()
    s_lower = (sport or "").lower()
    combined = f"{l_lower} {s_lower}"

    if any(x in combined for x in ["france", "ligue 1", "ligue 2", "франци"]):
        return {"name": "Франция", "code": "fr", "flag_url": "https://flagcdn.com/w40/fr.png", "emoji": "🇫🇷"}
    if any(x in combined for x in ["england", "epl", "premier", "championship", "англия"]):
        return {"name": "Англия", "code": "gb-eng", "flag_url": "https://flagcdn.com/w40/gb-eng.png", "emoji": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"}
    if any(x in combined for x in ["spain", "la liga", "laliga", "испани"]):
        return {"name": "Испания", "code": "es", "flag_url": "https://flagcdn.com/w40/es.png", "emoji": "🇪🇸"}
    if any(x in combined for x in ["italy", "serie a", "serie_a", "италия"]):
        return {"name": "Италия", "code": "it", "flag_url": "https://flagcdn.com/w40/it.png", "emoji": "🇮🇹"}
    if any(x in combined for x in ["germany", "bundesliga", "германи"]):
        return {"name": "Германия", "code": "de", "flag_url": "https://flagcdn.com/w40/de.png", "emoji": "🇩🇪"}
    if any(x in combined for x in ["sweden", "allsvensk", "shl", "швеци"]):
        return {"name": "Швеция", "code": "se", "flag_url": "https://flagcdn.com/w40/se.png", "emoji": "🇸🇪"}
    if any(x in combined for x in ["portugal", "primeira", "португал"]):
        return {"name": "Португалия", "code": "pt", "flag_url": "https://flagcdn.com/w40/pt.png", "emoji": "🇵🇹"}
    if any(x in combined for x in ["netherlands", "eredivisie", "нидерланд"]):
        return {"name": "Нидерланды", "code": "nl", "flag_url": "https://flagcdn.com/w40/nl.png", "emoji": "🇳🇱"}
    if any(x in combined for x in ["turkey", "super lig", "турци"]):
        return {"name": "Турция", "code": "tr", "flag_url": "https://flagcdn.com/w40/tr.png", "emoji": "🇹🇷"}
    if any(x in combined for x in ["nhl", "nfl", "nba", "mls", "american", "сша"]):
        return {"name": "США", "code": "us", "flag_url": "https://flagcdn.com/w40/us.png", "emoji": "🇺🇸"}
    if any(x in combined for x in ["khl", "rpl", "кхл", "рпл", "росси"]):
        return {"name": "Россия", "code": "ru", "flag_url": "https://flagcdn.com/w40/ru.png", "emoji": "🇷🇺"}
    if any(x in combined for x in ["euroleague", "champions_league", "europa_league", "uefa", "европ"]):
        return {"name": "Европа", "code": "eu", "flag_url": "https://flagcdn.com/w40/eu.png", "emoji": "🇪🇺"}
    if any(x in combined for x in ["mma", "ufc", "atp", "wta", "tennis", "турнир"]):
        return {"name": "Международный", "code": "un", "flag_url": "https://flagcdn.com/w40/un.png", "emoji": "🌍"}

    return {"name": "Спорт", "code": "un", "flag_url": "https://flagcdn.com/w40/un.png", "emoji": "🌐"}
