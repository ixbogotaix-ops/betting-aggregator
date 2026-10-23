"""
Robobet Scraper and Analysis Service
Scrapes https://vprognoze.ru/robobet/ for mathematical AI probabilities and generates Match of the Day.
"""
import re
import logging
import requests
from lxml import html
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
from .vitibet_scraper import get_vitibet_cached, find_vitibet_match, check_mathematical_consensus
from .zulubet_scraper import get_zulubet_cached, find_zulubet_match, check_zulu_consensus
from .logo_service import get_team_logo, get_country_info

logger = logging.getLogger("robobet_scraper")

ROBOBET_URL = "https://vprognoze.ru/robobet/"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://vprognoze.ru/',
}

def evaluate_robobet_outcome(recommendation: str, home_score: Optional[int], away_score: Optional[int]) -> Tuple[Optional[str], Optional[bool]]:
    """
    Evaluates whether the recommendation won, lost, or pushed.
    Returns (result_status, is_win).
    result_status: 'win', 'loss', 'refund' or None
    is_win: True, False or None
    """
    if not recommendation or home_score is None or away_score is None:
        return (None, None)
    
    raw = recommendation.upper().strip().replace('Х', 'X')
    if raw in ['П1', 'P1', '1']:
        win = (home_score > away_score)
        return ("win" if win else "loss", win)
    elif raw in ['П2', 'P2', '2']:
        win = (away_score > home_score)
        return ("win" if win else "loss", win)
    elif raw in ['X', 'НИЧЬЯ']:
        win = (home_score == away_score)
        return ("win" if win else "loss", win)
    elif raw in ['1X', '1Х']:
        win = (home_score >= away_score)
        return ("win" if win else "loss", win)
    elif raw in ['X2', 'Х2']:
        win = (away_score >= home_score)
        return ("win" if win else "loss", win)
    elif raw in ['12']:
        win = (home_score != away_score)
        return ("win" if win else "loss", win)
    
    # Fallback to general evaluator
    try:
        from .settlement_service import evaluate_bet_outcome, ResultStatus
        res = evaluate_bet_outcome(recommendation, home_score, away_score)
        if res == ResultStatus.win:
            return ("win", True)
        elif res == ResultStatus.loss:
            return ("loss", False)
        elif res == ResultStatus.refund:
            return ("refund", None)
    except Exception:
        pass

    return (None, None)

def calculate_double_chance_odds(odd_a: float, odd_b: float) -> float:
    """
    Рассчитывает реальный букмекерский коэффициент двойного шанса (1X, X2, 12).
    Формула: 1 / ((1 / odd_a) + (1 / odd_b)) * (1 - маржа).
    Стандартная маржа БК на двойные исходы составляет ~4-5% (множитель 0.96).
    """
    if not odd_a or not odd_b or odd_a <= 1.0 or odd_b <= 1.0:
        return 1.25
    implied = (1.0 / odd_a) + (1.0 / odd_b)
    if implied <= 0:
        return 1.25
    k = (1.0 / implied) * 0.96
    return max(1.05, round(k, 2))

def scrape_robobet() -> List[Dict[str, Any]]:
    """Scrapes all matches and probabilities from Robobet."""
    try:
        resp = requests.get(ROBOBET_URL, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            logger.error(f"Robobet returned status {resp.status_code}")
            return []
        
        resp.encoding = 'utf-8'
        tree = html.fromstring(resp.text)
        rows = tree.xpath('//*[contains(@class, "v3-robobet__table-body-row")]')
        
        matches = []
        for idx, row in enumerate(rows):
            try:
                # 1. Time
                time_el = row.xpath('.//*[contains(@class, "v3-robobet__table-body-time")]/text()')
                match_time = time_el[0].strip() if time_el else ""
                
                # 2. Flag / Country
                country_use = row.xpath('.//*[contains(@class, "v3-robobet__table-body-country")]//use/@href')
                country_title = row.xpath('.//*[contains(@class, "v3-robobet__table-body-country")]//@title')
                country = ""
                if country_title and country_title[0].strip():
                    country = country_title[0].strip()
                elif country_use:
                    country = country_use[0].split('#')[-1].replace('flag-', '').upper()

                if country in ['EUROPEANUNION', 'EUROPEAN UNION', 'EU', 'EUROPE', 'UEFA']:
                    country = "Лига Европы"
                elif country in ['WORLD', 'INTERNATIONAL']:
                    country = "Международные"
                elif country in ['VE', 'VENEZUELA']:
                    country = "Венесуэла"

                # 3. Match Teams
                match_span = row.xpath('.//*[contains(@class, "v3-robobet__table-body-match")]//span/text()')
                match_str = match_span[0].strip() if match_span else ""
                if not match_str:
                    # fallback to any text in match container
                    all_match = row.xpath('.//*[contains(@class, "v3-robobet__table-body-match")]//text()')
                    match_str = " ".join([m.strip() for m in all_match if m.strip()])
                
                teams = match_str.split(" - ")
                team1 = teams[0].strip() if len(teams) > 0 else match_str
                team2 = teams[1].strip() if len(teams) > 1 else ""

                # 4. Probabilities
                raw_percs = row.xpath('.//*[contains(@class, "v3-robobet__table-body-percent")]//text()')
                clean_percs = [p.strip().replace('%', '') for p in raw_percs if '%' in p]
                prob_1, prob_x, prob_2 = 0, 0, 0
                if len(clean_percs) >= 3:
                    try:
                        prob_1 = int(clean_percs[0])
                        prob_x = int(clean_percs[1])
                        prob_2 = int(clean_percs[2])
                    except ValueError:
                        pass

                # 5. Recommended Bet Outcome
                bet_el = row.xpath('.//*[contains(@class, "v3-robobet__table-body-bet")]//text()')
                recommendation = "".join(bet_el).strip() if bet_el else ""

                # 6. Bookmaker Odds
                raw_kfs = row.xpath('.//*[contains(@class, "v3-robobet__table-body-kf")]//text()')
                clean_kfs = [k.strip().replace(',', '.') for k in raw_kfs if k.strip()]
                odds_1, odds_x, odds_2 = 1.0, 1.0, 1.0
                if len(clean_kfs) >= 3:
                    try:
                        odds_1 = float(clean_kfs[0])
                        odds_x = float(clean_kfs[1])
                        odds_2 = float(clean_kfs[2])
                    except ValueError:
                        pass

                # 7. Score / Status
                score_el = row.xpath('.//*[contains(@class, "v3-robobet__table-body-score")]/text()')
                score_str = score_el[0].strip() if score_el else ""
                
                # Match link
                link_el = row.xpath('.//a[contains(@class, "v3-robobet__table-body-link")]/@href')
                match_url = ("https://vprognoze.ru" + link_el[0]) if link_el and link_el[0] else ""

                # Determine recommended odd & win probability
                rec_odd = 1.0
                rec_prob = 0
                if recommendation == "П1":
                    rec_odd = odds_1
                    rec_prob = prob_1
                elif recommendation == "П2":
                    rec_odd = odds_2
                    rec_prob = prob_2
                elif recommendation == "X2":
                    rec_prob = prob_x + prob_2
                    rec_odd = calculate_double_chance_odds(odds_x, odds_2)
                elif recommendation == "1X":
                    rec_prob = prob_1 + prob_x
                    rec_odd = calculate_double_chance_odds(odds_1, odds_x)
                elif recommendation == "12":
                    rec_prob = prob_1 + prob_2
                    rec_odd = calculate_double_chance_odds(odds_1, odds_2)

                # Mathematical Expected Value (+EV): (prob * odds) - 1.0
                # e.g., 65% at 1.80 -> 0.65 * 1.80 = 1.17 -> +17% EV!
                ev = round(((rec_prob / 100.0) * rec_odd) - 1.0, 3) if rec_prob > 0 and rec_odd > 1.0 else 0.0

                home_score = None
                away_score = None
                is_finished = False
                result_status = None
                is_win = None

                if score_str == "отм":
                    is_finished = True
                    result_status = "refund"
                elif score_str and score_str != "- : -" and ":" in score_str:
                    m_sc = re.search(r'(\d+)\s*[:\-]\s*(\d+)', score_str)
                    if m_sc:
                        try:
                            home_score = int(m_sc.group(1))
                            away_score = int(m_sc.group(2))
                            is_finished = True
                            result_status, is_win = evaluate_robobet_outcome(recommendation, home_score, away_score)
                        except ValueError:
                            pass

                c_info = get_country_info(country)
                country_ru = c_info.get("name") or country

                matches.append({
                    "id": f"robobet_{idx}_{match_time}_{team1[:5]}",
                    "time": match_time,
                    "country": country_ru,
                    "country_raw": country,
                    "country_code": c_info.get("code", ""),
                    "country_flag_url": c_info.get("flag_url", ""),
                    "country_emoji": c_info.get("emoji", "🌍"),
                    "team1": team1,
                    "team2": team2,
                    "home_logo": get_team_logo(team1, "football", fast_only=True),
                    "away_logo": get_team_logo(team2, "football", fast_only=True),
                    "match_name": f"{team1} — {team2}",
                    "prob_1": prob_1,
                    "prob_x": prob_x,
                    "prob_2": prob_2,
                    "recommendation": recommendation,
                    "odds_1": odds_1,
                    "odds_x": odds_x,
                    "odds_2": odds_2,
                    "rec_odd": rec_odd,
                    "rec_prob": rec_prob,
                    "ev": ev,
                    "is_value": ev > 0.05,
                    "score": score_str,
                    "home_score": home_score,
                    "away_score": away_score,
                    "is_finished": is_finished,
                    "result_status": result_status,
                    "is_win": is_win,
                    "match_url": match_url
                })
            except Exception as e:
                logger.warning(f"Error parsing robobet row {idx}: {e}")
                continue

        logger.info(f"Successfully scraped {len(matches)} Robobet matches")
        return matches

    except Exception as e:
        logger.error(f"Error in scrape_robobet: {e}")
        return []

def enrich_matches_with_ai_models(matches: Optional[List[Dict[str, Any]]], force: bool = False) -> List[Dict[str, Any]]:
    """
    Enriches each Robobet match with:
    1. Vitibet exact score prediction, algorithm confidence index, and pick.
    2. Zulubet mathematical percentage distribution (1/X/2) and algorithmic tip.
    3. Calculates Triple AI Consensus (Robobet + Vitibet + Zulubet).
    """
    if not matches:
        return []

    viti_matches = get_vitibet_cached(force=force) or []
    zulu_matches = get_zulubet_cached(force=force) or []

    for m in matches:
        t1 = m.get("team1", "")
        t2 = m.get("team2", "")
        rec = m.get("recommendation", "")

        # 1. Vitibet Match
        vm = find_vitibet_match(t1, t2, viti_matches) if viti_matches else None
        viti_agree = False
        if vm:
            m["has_vitibet"] = True
            m["vitibet_tip"] = vm["tip"]
            m["vitibet_index"] = vm["index_str"]
            m["vitibet_index_val"] = vm["index_val"]
            m["vitibet_proj_score"] = vm["proj_score"]
            viti_agree = check_mathematical_consensus(rec, vm["tip"])
        else:
            m["has_vitibet"] = False
            m["vitibet_tip"] = None
            m["vitibet_index"] = None
            m["vitibet_index_val"] = 0.0
            m["vitibet_proj_score"] = None

        # 2. Zulubet Match
        zm = find_zulubet_match(t1, t2, zulu_matches) if zulu_matches else None
        zulu_agree = False
        if zm:
            m["has_zulubet"] = True
            m["zulubet_tip"] = zm["tip"]
            m["zulubet_prob_1"] = zm["prob_1"]
            m["zulubet_prob_x"] = zm["prob_x"]
            m["zulubet_prob_2"] = zm["prob_2"]
            zulu_agree = check_zulu_consensus(rec, zm["tip"])
        else:
            m["has_zulubet"] = False
            m["zulubet_tip"] = None
            m["zulubet_prob_1"] = 0
            m["zulubet_prob_x"] = 0
            m["zulubet_prob_2"] = 0

        # 3. Consensus Level across 3 Independent AI Engines
        agreed_engines = 1  # Robobet pick itself
        matched_engines = 1
        if m["has_vitibet"]:
            matched_engines += 1
            if viti_agree:
                agreed_engines += 1
        if m["has_zulubet"]:
            matched_engines += 1
            if zulu_agree:
                agreed_engines += 1

        m["matched_engines"] = matched_engines
        m["agreed_engines"] = agreed_engines
        m["is_math_consensus"] = (agreed_engines >= 2)
        m["is_triple_consensus"] = (agreed_engines >= 3)
        if agreed_engines >= 3:
            m["consensus_badge"] = "🔥 СУПЕР ИИ 3/3"
        elif agreed_engines == 2:
            m["consensus_badge"] = "⚡ ИИ-КОНСЕНСУС 2/2"
        else:
            m["consensus_badge"] = None

    return matches

def enrich_time_and_status(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Рассчитывает текущий статус матча на основе реального московского времени (Europe/Moscow).
    Определяет:
    - is_time_past: стартовал ли матч по времени
    - match_status_label: 'upcoming' (еще не начался), 'live' (идет прямо сейчас), 'finished' (завершен)
    """
    moscow_tz = timezone(timedelta(hours=3))
    now_msk = datetime.now(moscow_tz)
    now_minutes = now_msk.hour * 60 + now_msk.minute

    for m in matches:
        t_str = m.get("time", "").strip()
        is_time_past = False
        minutes_diff = 0
        match_status_label = "upcoming"

        if t_str and ":" in t_str:
            try:
                parts = t_str.split(":")
                h = int(parts[0])
                mn = int(parts[1])
                m_minutes = h * 60 + mn
                minutes_diff = now_minutes - m_minutes
                
                score = m.get("score", "").strip()
                is_fin = m.get("is_finished") or (score and score != "- : -" and score != "отм") or (score == "отм")

                if is_fin or m.get("result_status") is not None:
                    is_time_past = True
                    match_status_label = "finished"
                elif minutes_diff > 0:
                    is_time_past = True
                    # Если прошло менее 120 минут и нет финального счета - матч идет прямо сейчас!
                    if minutes_diff <= 120 and (not score or score == "- : -"):
                        match_status_label = "live"
                    else:
                        match_status_label = "finished"
                else:
                    match_status_label = "upcoming"
            except Exception:
                pass

        m["is_time_past"] = is_time_past
        m["minutes_diff"] = minutes_diff
        m["match_status_label"] = match_status_label

    return matches

def get_robobet_top_3_bets(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Выбирает Топ-3 лучших математических ИИ ставок дня.
    СТРОЖАЙШИЙ ПРИОРИТЕТ:
    1. Профитность: коэффициент СТРОГО НЕ МЕНЕЕ 1.55 (кэф мин 1.55, мелкие коэффициенты исключены!).
    2. Матчи, которые ЕЩЕ НЕ НАЧАЛИСЬ (время старта строго в будущем, match_time > now_msk и score == '- : -')
    3. Если на сегодня все матчи уже стартовали, берем текущие LIVE матчи или лучшие завершенные с кэфом >= 1.55.
    """
    enrich_time_and_status(matches)

    MIN_TOP_ODDS = 1.55

    # 1. Строго не начавшиеся матчи (на которые пользователь еще может поставить!)
    truly_upcoming = [
        m for m in matches 
        if not m.get("is_time_past") and not m.get("is_finished") and (not m.get("score") or m.get("score") == "- : -")
    ]

    # Сначала ищем среди неначавшихся матчей со строгим профитным коэффициентом >= 1.55
    upcoming_profitable = [m for m in truly_upcoming if (m.get("rec_odd") or 0.0) >= MIN_TOP_ODDS]

    if len(upcoming_profitable) >= 3:
        candidates = upcoming_profitable
    elif upcoming_profitable:
        # Если неначавшихся >= 1.55 меньше 3, дополняем активными LIVE матчами с кэфом >= 1.55
        live_profitable = [m for m in matches if m.get("match_status_label") == "live" and (m.get("rec_odd") or 0.0) >= MIN_TOP_ODDS]
        candidates = upcoming_profitable + [m for m in live_profitable if m not in upcoming_profitable]
        # Если всё ещё меньше 3, смотрим все матчи дня с кэфом >= 1.55
        if len(candidates) < 3:
            all_profitable = [m for m in matches if (m.get("rec_odd") or 0.0) >= MIN_TOP_ODDS]
            candidates = candidates + [m for m in all_profitable if m not in candidates]
    else:
        # Если среди неначавшихся нет кэфов >= 1.55, берем LIVE или все матчи с кэфом >= 1.55
        all_profitable = [m for m in matches if (m.get("rec_odd") or 0.0) >= MIN_TOP_ODDS]
        if all_profitable:
            candidates = all_profitable
        else:
            candidates = truly_upcoming if truly_upcoming else matches

    if not candidates:
        return []

    def calculate_math_rank(m):
        prob = m.get("rec_prob", 0)
        odd = m.get("rec_odd", 1.0)
        ev = m.get("ev", 0.0)
        is_consensus = m.get("is_math_consensus", False)
        is_triple = m.get("is_triple_consensus", False)
        viti_idx = abs(m.get("vitibet_index_val", 0.0))

        # Balanced odds weighting & Profit Priority (кэф мин 1.55)
        odd_mult = 1.0
        if odd < 1.55:
            odd_mult = 0.05   # Жесткий барьер для любого случайного кэфа ниже 1.55
        elif 1.55 <= odd < 1.65:
            odd_mult = 1.05
        elif 1.65 <= odd <= 2.45:
            odd_mult = 1.45   # 🌟 ЗОЛОТАЯ ЗОНА МАКСИМАЛЬНОГО ПРОФИТА
        elif 2.46 <= odd <= 3.20:
            odd_mult = 1.25
        elif odd > 3.20:
            odd_mult = 0.85

        score = (prob + max(0.0, min(1.0, ev)) * 35.0)
        
        # Награда за тройной консенсус моделей
        if is_triple:
            score += 70.0
        elif is_consensus:
            score += 35.0

        # Вес индекса Vitibet
        if viti_idx > 0:
            score += min(15.0, viti_idx * 2.5)

        return score * odd_mult

    ranked = sorted(candidates, key=calculate_math_rank, reverse=True)
    top_3 = []
    medals = ["🥇 ЗОЛОТО", "🥈 СЕРЕБРО", "🥉 БРОНЗА"]
    for i, m in enumerate(ranked[:3]):
        item = dict(m)
        item["rank"] = i + 1
        item["medal"] = medals[i]
        # Полное разрешение логотипов (включая поиск TheSportsDB и авто-сохранение в кэш)
        item["home_logo"] = get_team_logo(item.get("team1", ""), "football", fast_only=False)
        item["away_logo"] = get_team_logo(item.get("team2", ""), "football", fast_only=False)
        top_3.append(item)

    return top_3

_cache = {
    "matches": [],
    "botd": None,
    "top_3": [],
    "updated_at": None
}

def calculate_robobet_stats(matches: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(matches)
    finished_list = [m for m in matches if m.get("is_finished") or m.get("match_status_label") == "finished"]
    wins = sum(1 for m in finished_list if m.get("result_status") == "win")
    losses = sum(1 for m in finished_list if m.get("result_status") == "loss")
    refunds = sum(1 for m in finished_list if m.get("result_status") == "refund")
    decided = wins + losses
    winrate = round((wins / decided * 100), 1) if decided > 0 else 0.0

    upcoming_count = sum(1 for m in matches if not m.get("is_time_past") and (not m.get("score") or m.get("score") == "- : -"))
    live_count = sum(1 for m in matches if m.get("match_status_label") == "live")

    return {
        "total_matches": total,
        "finished": len(finished_list),
        "upcoming": upcoming_count,
        "live": live_count,
        "wins": wins,
        "losses": losses,
        "refunds": refunds,
        "winrate": winrate
    }

def get_robobet_cached(force_refresh: bool = False) -> Dict[str, Any]:
    """Returns cached Robobet matches, Top 3 Bets, and Bet of the Day with Triple AI cross-analysis."""
    now = datetime.now()
    if (
        not force_refresh
        and _cache["updated_at"] is not None
        and _cache["matches"]
        and (now - _cache["updated_at"]).total_seconds() < 900  # 15 min cache
    ):
        # Всегда пересчитываем динамические временные статусы (исходя из текущей секунды)
        enrich_time_and_status(_cache["matches"])
        top_3 = get_robobet_top_3_bets(_cache["matches"])
        botd = top_3[0] if top_3 else None
        return {
            "matches": _cache["matches"],
            "bet_of_the_day": botd,
            "top_3_bets": top_3,
            "total": len(_cache["matches"]),
            "stats": calculate_robobet_stats(_cache["matches"]),
            "updated_at": _cache["updated_at"].isoformat()
        }

    raw_matches = scrape_robobet()
    enriched_matches = enrich_matches_with_ai_models(raw_matches, force=force_refresh)
    enrich_time_and_status(enriched_matches)
    top_3 = get_robobet_top_3_bets(enriched_matches)
    botd = top_3[0] if top_3 else None

    # Синхронизируем полученные логотипы топ-3 обратно в общий список матчей
    for t in top_3:
        for m in enriched_matches:
            if m.get("id") == t.get("id"):
                m["home_logo"] = t.get("home_logo")
                m["away_logo"] = t.get("away_logo")

    # Прогреваем эмблемы для первых матчей ленты (только быстрый кэш, без сетевых задержек)
    for m in enriched_matches[:15]:
        if not m.get("home_logo"):
            m["home_logo"] = get_team_logo(m.get("team1", ""), "football", fast_only=True)
        if not m.get("away_logo"):
            m["away_logo"] = get_team_logo(m.get("team2", ""), "football", fast_only=True)

    _cache["matches"] = enriched_matches
    _cache["botd"] = botd
    _cache["top_3"] = top_3
    _cache["updated_at"] = now

    return {
        "matches": enriched_matches,
        "bet_of_the_day": botd,
        "top_3_bets": top_3,
        "total": len(enriched_matches),
        "stats": calculate_robobet_stats(enriched_matches),
        "updated_at": now.isoformat()
    }
