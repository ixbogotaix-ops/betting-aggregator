import os
import re
import logging
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from thefuzz import fuzz
from unidecode import unidecode
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from .models import Match, Prediction, Source, HistoricalResult, MatchStatus, ResultStatus
from .consensus import normalize_outcome, get_generic_sport

logger = logging.getLogger(__name__)

def evaluate_bet_outcome(outcome_str: str, home_score: int, away_score: int, home_team: str = "", away_team: str = "") -> Optional[ResultStatus]:
    """
    Математически рассчитывает исход ставки (win / loss / refund)
    на основе финального счёта матча.
    """
    if outcome_str is None or home_score is None or away_score is None:
        return None

    raw = outcome_str.lower().strip()
    total_goals = home_score + away_score
    diff_home = home_score - away_score
    diff_away = away_score - home_score

    def is_team(query: str, target: str) -> bool:
        if not query or not target:
            return False
        q = unidecode(query).lower().strip()
        t = unidecode(target).lower().strip()
        return q in t or t in q or fuzz.partial_ratio(q, t) > 75

    # 0. Комбинированные ставки: 1X/X2/П1/П2 + ТМ/ТБ
    m_combo = re.search(r'(1[xх]|x2|х2|п1|п2|победа\s*[12])\s*(?:\+|и|and|&)\s*(?:тм|тб|тотал\s*(?:меньше|больше))\s*\(?(\d+[\.,]?\d*)\)?', raw)
    if m_combo:
        side = m_combo.group(1).upper().replace('Х', 'X')
        tot_val = float(m_combo.group(2).replace(',', '.'))
        is_tm = ("тм" in raw or "меньше" in raw)
        
        side_ok = False
        if side in ["1X", "1Х"] or "1" in side:
            side_ok = (home_score >= away_score) if "X" in side else (home_score > away_score)
        elif side in ["X2", "Х2"] or "2" in side:
            side_ok = (away_score >= home_score) if "X" in side else (away_score > home_score)
            
        tot_ok = (total_goals < tot_val) if is_tm else (total_goals > tot_val)
        return ResultStatus.win if (side_ok and tot_ok) else ResultStatus.loss

    # 0.1 Индивидуальные тоталы (ИТБ / ИТМ)
    itb_match = re.search(r'(?:итб\s*([12])|индивидуальный\s*тотал\s*([12])\s*больше)\s*\(?(\d+[\.,]?\d*)\)?', raw)
    if itb_match:
        team_num = itb_match.group(1) or itb_match.group(2)
        val = float(itb_match.group(3).replace(',', '.'))
        team_goals = home_score if team_num == '1' else away_score
        if team_goals > val:
            return ResultStatus.win
        elif team_goals == val:
            return ResultStatus.refund
        else:
            return ResultStatus.loss

    itm_match = re.search(r'(?:итм\s*([12])|индивидуальный\s*тотал\s*([12])\s*меньше)\s*\(?(\d+[\.,]?\d*)\)?', raw)
    if itm_match:
        team_num = itm_match.group(1) or itm_match.group(2)
        val = float(itm_match.group(3).replace(',', '.'))
        team_goals = home_score if team_num == '1' else away_score
        if team_goals < val:
            return ResultStatus.win
        elif team_goals == val:
            return ResultStatus.refund
        else:
            return ResultStatus.loss

    # 1. Обе забьют (ОЗ)
    if "оз" in raw or "обе забьют" in raw:
        both_scored = (home_score > 0 and away_score > 0)
        if any(w in raw for w in ["нет", "no", "не забьют", "— нет", "- нет"]):
            return ResultStatus.win if not both_scored else ResultStatus.loss
        return ResultStatus.win if both_scored else ResultStatus.loss

    # 2. Двойной шанс (1X, X2, 12)
    if re.search(r'\b(1x|1х)\b', raw) or ("не проиграет" in raw and ("1" in raw or "хозя" in raw or is_team(raw, home_team))):
        return ResultStatus.win if home_score >= away_score else ResultStatus.loss
    if re.search(r'\b(x2|х2)\b', raw) or ("не проиграет" in raw and ("2" in raw or "гост" in raw or is_team(raw, away_team))):
        return ResultStatus.win if away_score >= home_score else ResultStatus.loss
    if re.search(r'\b(12)\b', raw) or "победа 1 или 2" in raw:
        return ResultStatus.win if home_score != away_score else ResultStatus.loss

    # 3. Ничья (Х)
    if raw in ["draw", "x", "х", "ничья", "х.", "x."] or raw.startswith("ничья") or raw == "мир":
        return ResultStatus.win if home_score == away_score else ResultStatus.loss

    # 4. Тоталы (ТБ / ТМ)
    tb_match = re.search(r'(?:тб|больше|over)\s*\(?(\d+[\.,]?\d*)\)?', raw)
    if tb_match:
        val = float(tb_match.group(1).replace(',', '.'))
        if total_goals > val:
            return ResultStatus.win
        elif total_goals == val:
            return ResultStatus.refund
        else:
            return ResultStatus.loss

    tm_match = re.search(r'(?:тм|меньше|under)\s*\(?(\d+[\.,]?\d*)\)?', raw)
    if tm_match:
        val = float(tm_match.group(1).replace(',', '.'))
        if total_goals < val:
            return ResultStatus.win
        elif total_goals == val:
            return ResultStatus.refund
        else:
            return ResultStatus.loss

    tot_match = re.search(r'тотал\s*(\d+[\.,]?\d*)', raw)
    if tot_match:
        val = float(tot_match.group(1).replace(',', '.'))
        if total_goals > val:
            return ResultStatus.win
        elif total_goals == val:
            return ResultStatus.refund
        else:
            return ResultStatus.loss

    # 5. Форы (Ф1 / Ф2)
    is_handicap = any(k in raw for k in ['фора', 'handicap', 'азиатская фора']) or re.search(r'\b(ф1|ф2|ah1|ah2|ах1|ах2)\b', raw) or 'с форой' in raw
    if is_handicap:
        val_m = re.search(r'\(\s*([\+\-]?\d+[\.,]?\d*)\s*\)', raw)
        if not val_m:
            val_m = re.search(r'[\+\-]\d+[\.,]?\d*', raw)
        if not val_m:
            val_m = re.search(r'(?:фора|handicap|ф[12]?)\s*(?:[12]|хозяев|гостей|[^\d\(\)]+)?\s*\(?([\+\-]?\d+[\.,]?\d*)\)?', raw)
        val = float(val_m.group(1).replace(',', '.')) if val_m else 0.0

        is_t2 = bool(
            re.search(r'(?:фора|handicap|ф|ah|ах|форой)\s*2\b', raw)
            or re.search(r'\b(ф2|ah2|ах2|гост\w*|втор\w*)\b', raw)
            or (away_team and is_team(raw, away_team))
            or '(ф2)' in raw
        )
        is_t1 = bool(
            re.search(r'(?:фора|handicap|ф|ah|ах|форой)\s*1\b', raw)
            or re.search(r'\b(ф1|ah1|ах1|хозя\w*|перв\w*)\b', raw)
            or (home_team and is_team(raw, home_team))
            or '(ф1)' in raw
        )

        if is_t2 and not is_t1:
            adjusted = diff_away + val
        elif is_t1 and not is_t2:
            adjusted = diff_home + val
        elif is_t2 and is_t1:
            if away_team and is_team(raw, away_team):
                adjusted = diff_away + val
            else:
                adjusted = diff_home + val
        else:
            adjusted = diff_home + val

        if adjusted > 0:
            return ResultStatus.win
        elif adjusted == 0:
            return ResultStatus.refund
        else:
            return ResultStatus.loss

    # 6. Победа 2 / Гости (П2)
    has_market_term = any(k in raw for k in ['фора', 'handicap', 'тб', 'тм', 'тотал', 'итб', 'итм', 'тайм', 'период', 'сет', 'гол'])
    if (
        raw in ["away_win", "п2", "w2", "2", "победа 2", "победа2", "победа гостей", "победа второй команды", "победа второй"]
        or re.search(r'\b(победа\s*2|победа\s*гостей|победа\s*второй)\b', raw)
        or re.search(r'\(п2\)', raw)
        or re.fullmatch(r'п2[\.\s]*', raw)
        or re.fullmatch(r'w2[\.\s]*', raw)
        or (away_team and not has_market_term and is_team(raw, away_team))
    ):
        return ResultStatus.win if away_score > home_score else ResultStatus.loss

    # 7. Победа 1 / Хозяева (П1)
    if (
        raw in ["home_win", "п1", "w1", "1", "победа 1", "победа1", "победа хозяев", "победа первой команды", "победа первой"]
        or re.search(r'\b(победа\s*1|победа\s*хозяев|победа\s*первой)\b', raw)
        or re.search(r'\(п1\)', raw)
        or re.fullmatch(r'п1[\.\s]*', raw)
        or re.fullmatch(r'w1[\.\s]*', raw)
        or (home_team and not has_market_term and is_team(raw, home_team))
    ):
        return ResultStatus.win if home_score > away_score else ResultStatus.loss

    return None

def teams_match(team_a: str, team_b: str) -> bool:
    """
    Интеллектуальное сопоставление названий команд (русский, английский, транслит, синонимы).
    """
    if not team_a or not team_b:
        return False
    a_clean = unidecode(team_a).lower().strip()
    b_clean = unidecode(team_b).lower().strip()
    if a_clean == b_clean:
        return True
    if fuzz.token_set_ratio(a_clean, b_clean) >= 75 or fuzz.ratio(a_clean, b_clean) >= 72:
        return True
    
    # Пробуем нормализованные варианты из logo_service
    try:
        from .logo_service import normalize_team_name
        vars_a = normalize_team_name(team_a)
        for v in vars_a:
            v_clean = unidecode(v).lower().strip()
            if v_clean == b_clean or fuzz.token_set_ratio(v_clean, b_clean) >= 75 or fuzz.ratio(v_clean, b_clean) >= 72:
                return True
                
        vars_b = normalize_team_name(team_b)
        for v in vars_b:
            v_clean = unidecode(v).lower().strip()
            if v_clean == a_clean or fuzz.token_set_ratio(a_clean, v_clean) >= 75 or fuzz.ratio(a_clean, v_clean) >= 72:
                return True
    except Exception:
        pass

    return False

class SettlementService:
    def __init__(self):
        self.api_key = os.getenv("SPORTS_API_KEY")

    def fetch_completed_scores_from_espn(self, days_back: int = 5) -> List[Dict]:
        """
        Запрашивает официальные завершённые счета из ESPN Scoreboard API.
        Не требует API-ключа, не имеет лимитов по квоте.
        """
        from concurrent.futures import ThreadPoolExecutor
        soccer_leagues = [
            'eng.1', 'esp.1', 'ita.1', 'ger.1', 'fra.1',
            'uefa.champions', 'uefa.europa', 'uefa.europa.conf',
            'rus.1', 'usa.1', 'ned.1', 'por.1', 'tur.1', 'bra.1'
        ]

        # Генерируем даты YYYYMMDD
        now = datetime.now()
        dates_list = [(now - timedelta(days=d)).strftime("%Y%m%d") for d in range(days_back + 1)]

        def fetch_espn_task(args):
            sport, league, d_str = args
            url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard?dates={d_str}"
            try:
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    events = r.json().get('events', [])
                    res = []
                    for ev in events:
                        status = ev.get('status', {}).get('type', {})
                        if status.get('completed'):
                            comps = ev.get('competitions', [{}])[0].get('competitors', [])
                            if len(comps) >= 2:
                                h = comps[0] if comps[0].get('homeAway') == 'home' else comps[1]
                                a = comps[1] if comps[0].get('homeAway') == 'home' else comps[0]
                                try:
                                    h_score = int(h.get('score', 0))
                                    a_score = int(a.get('score', 0))
                                    h_name = h.get('team', {}).get('displayName', '') or h.get('team', {}).get('name', '')
                                    a_name = a.get('team', {}).get('displayName', '') or a.get('team', {}).get('name', '')
                                    if h_name and a_name:
                                        res.append({
                                            'home_team': h_name,
                                            'away_team': a_name,
                                            'home_score': h_score,
                                            'away_score': a_score,
                                            'league': league,
                                            'sport': sport,
                                            'source': 'espn'
                                        })
                                except (ValueError, TypeError):
                                    pass
                    return res
            except Exception:
                pass
            return []

        tasks = []
        for d in dates_list:
            for l in soccer_leagues:
                tasks.append(('soccer', l, d))
            tasks.append(('hockey', 'nhl', d))
            tasks.append(('basketball', 'nba', d))

        try:
            with ThreadPoolExecutor(max_workers=10) as ex:
                results = ex.map(fetch_espn_task, tasks)
            events = [ev for sublist in results for ev in sublist]
            logger.info(f"Получено {len(events)} завершённых матчей из ESPN API")
            return events
        except Exception as e:
            logger.warning(f"Ошибка получения счетов из ESPN: {e}")
            return []

    def fetch_completed_scores_from_zulubet(self, days_back: int = 3) -> List[Dict]:
        """
        Запрашивает завершённые футбольные матчи со счетами из Zulubet (80-100 матчей/день).
        """
        import cloudscraper
        from bs4 import BeautifulSoup
        events = []
        try:
            scraper = cloudscraper.create_scraper()
            now = datetime.now()
            urls = ["http://www.zulubet.com/"]
            for d in range(1, days_back + 1):
                d_str = (now - timedelta(days=d)).strftime("%d-%m-%Y")
                urls.append(f"http://www.zulubet.com/tips-{d_str}.html")

            for url in urls:
                try:
                    r = scraper.get(url, timeout=8)
                    if r.status_code != 200:
                        continue
                    soup = BeautifulSoup(r.content, "html.parser")
                    for row in soup.find_all("tr"):
                        cols = [c.get_text(strip=True) for c in row.find_all("td")]
                        if len(cols) >= 12 and " - " in cols[1]:
                            teams = cols[1].split(" - ")
                            h_name = teams[0].strip()
                            a_name = teams[1].strip()
                            score_found = None
                            # В Zulubet счёт матча находится строго в конце строки (cols[-2] или cols[-1])
                            # Ни в коем случае НЕ смотрим cols[0], где указано время матча (например, 17:00 или 16:30)!
                            for c in cols[2:]:
                                if '%' in c or '.' in c:
                                    continue
                                m = re.fullmatch(r'(\d{1,2})\s*:\s*(\d{1,2})', c.strip())
                                if m:
                                    h_sc, a_sc = int(m.group(1)), int(m.group(2))
                                    if h_sc <= 12 and a_sc <= 12:
                                        score_found = (h_sc, a_sc)
                                        break
                            if score_found and h_name and a_name:
                                events.append({
                                    "home_team": h_name,
                                    "away_team": a_name,
                                    "home_score": score_found[0],
                                    "away_score": score_found[1],
                                    "sport": "Football",
                                    "source": "zulubet"
                                })
                except Exception:
                    continue

            logger.info(f"Получено {len(events)} завершённых матчей из Zulubet")
            return events
        except Exception as e:
            logger.warning(f"Ошибка получения счетов из Zulubet: {e}")
            return []

    def fetch_completed_scores_from_robobet(self) -> List[Dict]:
        """
        Запрашивает завершённые матчи со счетами из Robobet.
        """
        try:
            from .robobet_scraper import scrape_robobet
            matches = scrape_robobet()
            res = []
            for m in matches:
                if m.get("is_finished") and m.get("home_score") is not None and m.get("away_score") is not None:
                    res.append({
                        "home_team": m.get("team1", ""),
                        "away_team": m.get("team2", ""),
                        "home_score": m.get("home_score"),
                        "away_score": m.get("away_score"),
                        "sport": "Football",
                        "source": "robobet"
                    })
            logger.info(f"Получено {len(res)} завершённых матчей из Robobet")
            return res
        except Exception as e:
            logger.warning(f"Ошибка получения счетов из Robobet: {e}")
            return []

    def fetch_completed_scores_from_api(self, days_from: int = 3) -> List[Dict]:
        """
        Запрашивает счета из The-Odds-API (только при наличии доступной квоты).
        """
        if not self.api_key:
            return []

        sports = [
            "soccer_epl", "soccer_spain_la_liga", "soccer_italy_serie_a",
            "soccer_germany_bundesliga", "soccer_france_ligue_one",
            "soccer_uefa_champs_league", "soccer_uefa_europa_league",
            "basketball_nba", "icehockey_nhl"
        ]

        completed_events = []
        for sport in sports:
            try:
                url = f"https://api.the-odds-api.com/v4/sports/{sport}/scores/"
                params = {"apiKey": self.api_key, "daysFrom": days_from, "dateFormat": "iso"}
                r = requests.get(url, params=params, timeout=8)
                if r.status_code != 200:
                    # При 401 или исчерпании квоты сразу прерываем опрос The-Odds-API
                    if r.status_code in [401, 429]:
                        logger.warning(f"The-Odds-API недоступен или квота исчерпана ({r.status_code})")
                        break
                    continue
                data = r.json()
                for item in data:
                    if item.get("completed") and item.get("scores"):
                        scores_list = item["scores"]
                        home_name = item.get("home_team", "")
                        away_name = item.get("away_team", "")
                        home_score, away_score = None, None
                        for s in scores_list:
                            name = s.get("name", "")
                            score = s.get("score")
                            if score is not None:
                                try:
                                    sc_val = int(score)
                                    if name == home_name or fuzz.ratio(name, home_name) > 80:
                                        home_score = sc_val
                                    elif name == away_name or fuzz.ratio(name, away_name) > 80:
                                        away_score = sc_val
                                except ValueError:
                                    pass
                        if home_score is not None and away_score is not None:
                            completed_events.append({
                                "home_team": home_name,
                                "away_team": away_name,
                                "home_score": home_score,
                                "away_score": away_score,
                                "sport": item.get("sport_title", sport),
                                "source": "odds_api"
                            })
            except Exception:
                break

        return completed_events

    def fetch_all_completed_scores(self, days_back: int = 5) -> List[Dict]:
        """
        Объединяет все доступные источники счетов: ESPN (безлимит) + Zulubet + Robobet + The-Odds-API.
        """
        all_events = []
        seen = set()

        # 1. ESPN
        for ev in self.fetch_completed_scores_from_espn(days_back=days_back):
            key = (ev["home_team"].lower(), ev["away_team"].lower())
            if key not in seen:
                seen.add(key)
                all_events.append(ev)

        # 2. Zulubet
        for ev in self.fetch_completed_scores_from_zulubet(days_back=min(days_back, 3)):
            key = (ev["home_team"].lower(), ev["away_team"].lower())
            if key not in seen:
                seen.add(key)
                all_events.append(ev)

        # 3. Robobet
        for ev in self.fetch_completed_scores_from_robobet():
            key = (ev["home_team"].lower(), ev["away_team"].lower())
            if key not in seen:
                seen.add(key)
                all_events.append(ev)

        # 4. The-Odds-API (попытка при наличии квоты)
        for ev in self.fetch_completed_scores_from_api(days_from=days_back):
            key = (ev["home_team"].lower(), ev["away_team"].lower())
            if key not in seen:
                seen.add(key)
                all_events.append(ev)

        logger.info(f"Всего собрано {len(all_events)} уникальных завершённых событий со счетами")
        return all_events

    async def sync_scores_and_settle(self, session: AsyncSession) -> Dict[str, int]:
        """
        Сопоставляет счета с матчами в БД, обновляет статусы и рассчитывает исход ставок.
        """
        api_events = self.fetch_all_completed_scores(days_back=7)
        settled_matches_count = 0
        settled_preds_count = 0

        # Выбираем все матчи, которые начались более 1.5 часов назад и еще не отмечены как finished
        moscow_tz = timezone(timedelta(hours=3))
        now_moscow = datetime.now(moscow_tz).replace(tzinfo=None)
        cutoff_time = now_moscow - timedelta(hours=1, minutes=30)

        stmt = select(Match).options(
            selectinload(Match.predictions).selectinload(Prediction.source)
        ).where(
            Match.match_date <= cutoff_time,
            (Match.status == MatchStatus.upcoming) | (Match.final_score_home == None)
        )
        res = await session.execute(stmt)
        candidate_matches = res.scalars().all()

        for match in candidate_matches:
            matched_event = None
            for ev in api_events:
                if teams_match(match.home_team, ev["home_team"]) and teams_match(match.away_team, ev["away_team"]):
                    matched_event = ev
                    break

            if matched_event:
                match.final_score_home = matched_event["home_score"]
                match.final_score_away = matched_event["away_score"]
                match.status = MatchStatus.finished
                settled_matches_count += 1

                # Рассчитываем исход каждого прогноза капперов
                for pred in match.predictions:
                    pred_res = evaluate_bet_outcome(
                        pred.predicted_outcome,
                        match.final_score_home,
                        match.final_score_away,
                        match.home_team,
                        match.away_team
                    )
                    if pred_res:
                        pred.status = pred_res
                        settled_preds_count += 1

                # Рассчитываем исход общего консенсуса (HistoricalResult)
                if match.predictions:
                    from .consensus import normalize_outcome
                    counts: Dict[str, List[Prediction]] = {}
                    for p in match.predictions:
                        n = normalize_outcome(p.predicted_outcome, match.home_team, match.away_team)
                        counts.setdefault(n, []).append(p)
                    best_norm = max(counts.keys(), key=lambda k: len(counts[k]))
                    cons_res = evaluate_bet_outcome(
                        best_norm,
                        match.final_score_home,
                        match.final_score_away,
                        match.home_team,
                        match.away_team
                    )
                    if cons_res:
                        hr_stmt = select(HistoricalResult).where(HistoricalResult.match_id == match.id)
                        hr = (await session.execute(hr_stmt)).scalar_one_or_none()
                        if not hr:
                            hr = HistoricalResult(
                                match_id=match.id,
                                final_score_home=match.final_score_home,
                                final_score_away=match.final_score_away,
                                match_status=cons_res
                            )
                            session.add(hr)
                        else:
                            hr.final_score_home = match.final_score_home
                            hr.final_score_away = match.final_score_away
                            hr.match_status = cons_res

        await session.commit()
        return {
            "settled_matches": settled_matches_count,
            "settled_predictions": settled_preds_count
        }


SPORT_TRANSLATIONS_RU = {
    "Football": "футболе",
    "Hockey": "хоккее",
    "Basketball": "баскетболе",
    "Tennis": "теннисе",
    "MMA": "MMA / единоборствах",
    "Esports": "киберспорте",
    "Baseball": "бейсболе",
    "American Football": "амер. футболе",
    "Cricket": "крикете",
    "Other": "спорте",
    "All": "всех видах спорта"
}

def calculate_source_dynamic_weight(winrate: float, total_bets: int, base_weight: float = 1.0) -> Tuple[float, str]:
    """
    Превращает реальную проходимость (winrate %) источника в динамический вес влияния.
    Если источник имеет < 2 рассчитанных ставок в этом виде спорта,
    используется нейтральный базовый вес (1.0).
    При высоком винрейте (>=70%) вес взлетает до 3.0-4.0x.
    При низком винрейте (<45%) вес падает до 0.2-0.5x (слушают в последнюю очередь).
    """
    if total_bets < 2:
        return (base_weight, "untested")

    # Сглаживание малых выборок к 50% (Bayesian shrinkage)
    smoothed_wr = winrate
    if total_bets < 5:
        smoothed_wr = (winrate * total_bets + 50.0 * 2) / (total_bets + 2)

    if smoothed_wr >= 75.0:
        w = min(4.0, 3.0 + (smoothed_wr - 75.0) * 0.08)
        tier = "elite_sharp"
    elif smoothed_wr >= 65.0:
        w = 2.2 + (smoothed_wr - 65.0) * 0.08
        tier = "sharp"
    elif smoothed_wr >= 55.0:
        w = 1.4 + (smoothed_wr - 55.0) * 0.08
        tier = "profitable"
    elif smoothed_wr >= 48.0:
        w = 1.0 + (smoothed_wr - 48.0) * 0.05
        tier = "neutral"
    elif smoothed_wr >= 40.0:
        w = 0.55 + (smoothed_wr - 40.0) * 0.05
        tier = "subpar"
    else:
        w = max(0.20, 0.20 + (smoothed_wr / 40.0) * 0.25)
        tier = "poor"

    return round(w, 2), tier

_source_sport_stats_cache = None
_source_sport_stats_cache_ts = 0
_source_sport_stats_cache_ttl = 60  # 60 seconds

async def get_source_sport_stats(session: AsyncSession) -> Dict:
    """
    Собирает полную историческую статистику проходимости (winrate, ROI, W/L/R)
    в разрезе (источник, вид спорта), а также общую по каждому источнику.
    """
    global _source_sport_stats_cache, _source_sport_stats_cache_ts
    import time as _t
    now_ts = _t.time()
    if _source_sport_stats_cache and (now_ts - _source_sport_stats_cache_ts < _source_sport_stats_cache_ttl):
        return _source_sport_stats_cache

    stmt_preds = select(Prediction).options(
        selectinload(Prediction.source),
        selectinload(Prediction.match)
    ).where(
        Prediction.status != None
    )
    res_p = await session.execute(stmt_preds)
    settled_preds = res_p.scalars().all()

    sport_map: Dict[Tuple[int, str], Dict] = {}
    overall_map: Dict[int, Dict] = {}

    for p in settled_preds:
        s_id = p.source_id
        s_name = p.source.name if p.source else "Unknown"
        s_type = p.source.source_type.value if (p.source and hasattr(p.source.source_type, 'value')) else (str(p.source.source_type) if p.source else "prediction_site")
        base_w = p.source.weight if (p.source and p.source.weight) else 1.0

        raw_sport = p.match.sport_type if (p.match and p.match.sport_type) else "Other"
        gen_sport = get_generic_sport(raw_sport)

        sport_entry = sport_map.setdefault((s_id, gen_sport), {
            "source_id": s_id,
            "source_name": s_name,
            "source_type": s_type,
            "sport": gen_sport,
            "total_bets": 0,
            "wins": 0,
            "losses": 0,
            "refunds": 0,
            "profit": 0.0,
            "base_weight": base_w
        })
        sport_entry["total_bets"] += 1

        all_entry = overall_map.setdefault(s_id, {
            "source_id": s_id,
            "source_name": s_name,
            "source_type": s_type,
            "sport": "All",
            "total_bets": 0,
            "wins": 0,
            "losses": 0,
            "refunds": 0,
            "profit": 0.0,
            "base_weight": base_w
        })
        all_entry["total_bets"] += 1

        if p.status == ResultStatus.win:
            sport_entry["wins"] += 1
            sport_entry["profit"] += max(0.0, (p.odds or 1.5) - 1.0)
            all_entry["wins"] += 1
            all_entry["profit"] += max(0.0, (p.odds or 1.5) - 1.0)
        elif p.status == ResultStatus.loss:
            sport_entry["losses"] += 1
            sport_entry["profit"] -= 1.0
            all_entry["losses"] += 1
            all_entry["profit"] -= 1.0
        elif p.status == ResultStatus.refund:
            sport_entry["refunds"] += 1
            all_entry["refunds"] += 1

    by_source_sport = {}
    for (s_id, g_sport), d in sport_map.items():
        dec = d["wins"] + d["losses"]
        wr = round((d["wins"] / dec * 100), 1) if dec > 0 else 0.0
        roi = round((d["profit"] / dec * 100), 1) if dec > 0 else 0.0
        dyn_w, tier = calculate_source_dynamic_weight(wr, dec, d["base_weight"])
        item = {
            "source_id": s_id,
            "source_name": d["source_name"],
            "source_type": d["source_type"],
            "sport": g_sport,
            "total_bets": d["total_bets"],
            "wins": d["wins"],
            "losses": d["losses"],
            "refunds": d["refunds"],
            "winrate_pct": wr,
            "roi_pct": roi,
            "net_profit": round(d["profit"], 2),
            "dynamic_weight": dyn_w,
            "tier": tier
        }
        by_source_sport[(s_id, g_sport)] = item

    by_source_overall = {}
    overall_leaderboard = []
    for s_id, d in overall_map.items():
        dec = d["wins"] + d["losses"]
        wr = round((d["wins"] / dec * 100), 1) if dec > 0 else 0.0
        roi = round((d["profit"] / dec * 100), 1) if dec > 0 else 0.0
        dyn_w, tier = calculate_source_dynamic_weight(wr, dec, d["base_weight"])
        item = {
            "source_id": s_id,
            "source_name": d["source_name"],
            "source_type": d["source_type"],
            "sport": "All",
            "total_bets": d["total_bets"],
            "wins": d["wins"],
            "losses": d["losses"],
            "refunds": d["refunds"],
            "winrate_pct": wr,
            "roi_pct": roi,
            "net_profit": round(d["profit"], 2),
            "dynamic_weight": dyn_w,
            "tier": tier
        }
        by_source_overall[s_id] = item
        overall_leaderboard.append(item)

    overall_leaderboard.sort(key=lambda x: (x["winrate_pct"], x["wins"]), reverse=True)

    sports_leaderboards: Dict[str, List[Dict]] = {}
    for (s_id, g_sport), item in by_source_sport.items():
        sports_leaderboards.setdefault(g_sport, []).append(item)

    for g_sport, items in sports_leaderboards.items():
        items.sort(key=lambda x: (x["winrate_pct"], x["wins"]), reverse=True)

    available_sports = sorted(list(sports_leaderboards.keys()))

    res_data = {
        "by_source_sport": by_source_sport,
        "by_source_overall": by_source_overall,
        "sports_leaderboards": sports_leaderboards,
        "overall_leaderboard": overall_leaderboard,
        "available_sports": available_sports
    }
    _source_sport_stats_cache = res_data
    _source_sport_stats_cache_ts = _t.time()
    return res_data

async def get_performance_stats(session: AsyncSession, sport_filter: Optional[str] = None) -> Dict:
    """
    Генерирует полную аналитику проходимости и ROI для сайта и бота.
    Поддерживает фильтрацию по виду спорта (sport_filter).
    """
    # 1. Завершенные матчи с результатами консенсуса
    stmt_matches = select(Match).options(
        selectinload(Match.result)
    ).where(
        Match.status == MatchStatus.finished,
        Match.final_score_home != None
    )
    res_m = await session.execute(stmt_matches)
    all_finished_matches = res_m.scalars().all()

    # Фильтруем матчи по виду спорта, если передан
    if sport_filter and sport_filter != "All":
        finished_matches = [
            m for m in all_finished_matches 
            if get_generic_sport(m.sport_type) == sport_filter
        ]
    else:
        finished_matches = all_finished_matches

    total_settled_matches = len(finished_matches)
    cons_wins = 0
    cons_losses = 0
    cons_refunds = 0
    cons_profit = 0.0

    for m in finished_matches:
        if m.result:
            if m.result.match_status == ResultStatus.win:
                cons_wins += 1
                cons_profit += 0.75
            elif m.result.match_status == ResultStatus.loss:
                cons_losses += 1
                cons_profit -= 1.0
            elif m.result.match_status == ResultStatus.refund:
                cons_refunds += 1

    decided = cons_wins + cons_losses
    winrate_pct = round((cons_wins / decided * 100), 1) if decided > 0 else 0.0
    roi_pct = round((cons_profit / decided * 100), 1) if decided > 0 else 0.0

    # 2. Получаем статистику по источникам из общей функции
    stats_data = await get_source_sport_stats(session)

    if sport_filter and sport_filter != "All":
        leaderboard = stats_data["sports_leaderboards"].get(sport_filter, [])
    else:
        leaderboard = stats_data["overall_leaderboard"]

    return {
        "overview": {
            "total_matches": total_settled_matches,
            "wins": cons_wins,
            "losses": cons_losses,
            "refunds": cons_refunds,
            "winrate_pct": winrate_pct,
            "roi_pct": roi_pct,
            "net_profit_units": round(cons_profit, 2)
        },
        "leaderboard": leaderboard,
        "sports_breakdown": stats_data["sports_leaderboards"],
        "available_sports": stats_data["available_sports"]
    }

async def get_archive_calendar_summary(session: AsyncSession, sport_type: Optional[str] = None) -> Dict:
    """
    Генерирует структурированную сводку архива по дням (календарный трек-рекорд):
    - Список прошедших дней со статистикой (W/L/R, winrate %, profit_units, roi %)
    - Общую суммарную статистику за всё время
    """
    stmt = select(Match).options(
        selectinload(Match.result),
        selectinload(Match.predictions)
    ).where(
        (Match.status == MatchStatus.finished) | (Match.final_score_home != None)
    ).order_by(Match.match_date.desc())

    res = await session.execute(stmt)
    all_matches = res.scalars().all()

    if sport_type and sport_type != 'All':
        all_matches = [
            m for m in all_matches 
            if get_generic_sport(m.sport_type) == sport_type or (m.sport_type and m.sport_type.lower() == sport_type.lower())
        ]

    days_map: Dict[str, List[Match]] = {}
    for m in all_matches:
        if not m.match_date:
            continue
        d_str = m.match_date.strftime("%Y-%m-%d")
        days_map.setdefault(d_str, []).append(m)

    days_summary = []
    overall_total = 0
    overall_wins = 0
    overall_losses = 0
    overall_refunds = 0
    overall_profit = 0.0

    for d_str in sorted(days_map.keys(), reverse=True):
        m_list = days_map[d_str]
        w = 0
        l = 0
        r = 0
        prof = 0.0

        for m in m_list:
            res_status = None
            if m.result and m.result.match_status:
                res_status = m.result.match_status
            elif m.final_score_home is not None and m.final_score_away is not None and m.predictions:
                from .consensus import normalize_outcome
                counts: Dict[str, int] = {}
                for p in m.predictions:
                    n = normalize_outcome(p.predicted_outcome, m.home_team, m.away_team)
                    counts[n] = counts.get(n, 0) + 1
                if counts:
                    best_n = max(counts.keys(), key=lambda k: counts[k])
                    res_status = evaluate_bet_outcome(best_n, m.final_score_home, m.final_score_away, m.home_team, m.away_team)

            if res_status == ResultStatus.win:
                w += 1
                prof += 0.80
            elif res_status == ResultStatus.loss:
                l += 1
                prof -= 1.0
            elif res_status == ResultStatus.refund:
                r += 1

        decided = w + l
        wr = round((w / decided * 100), 1) if decided > 0 else 0.0
        roi = round((prof / decided * 100), 1) if decided > 0 else 0.0
        p_units = round(prof, 2)

        days_summary.append({
            "date": d_str,
            "total_matches": len(m_list),
            "decided": decided,
            "wins": w,
            "losses": l,
            "refunds": r,
            "winrate": wr,
            "profit_units": p_units,
            "roi": roi
        })

        overall_total += len(m_list)
        overall_wins += w
        overall_losses += l
        overall_refunds += r
        overall_profit += prof

    ov_decided = overall_wins + overall_losses
    ov_wr = round((overall_wins / ov_decided * 100), 1) if ov_decided > 0 else 0.0
    ov_roi = round((overall_profit / ov_decided * 100), 1) if ov_decided > 0 else 0.0

    return {
        "days": days_summary,
        "overall": {
            "total_matches": overall_total,
            "decided": ov_decided,
            "wins": overall_wins,
            "losses": overall_losses,
            "refunds": overall_refunds,
            "winrate": ov_wr,
            "profit_units": round(overall_profit, 2),
            "roi": ov_roi
        }
    }

