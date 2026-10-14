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
from .consensus import normalize_outcome

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
    f1_match = re.search(r'(?:фора\s*1|ф1)\s*\(?([\+\-]?\d+[\.,]?\d*)\)?', raw)
    if f1_match:
        val = float(f1_match.group(1).replace(',', '.'))
        adjusted = diff_home + val
        if adjusted > 0:
            return ResultStatus.win
        elif adjusted == 0:
            return ResultStatus.refund
        else:
            return ResultStatus.loss

    f2_match = re.search(r'(?:фора\s*2|ф2)\s*\(?([\+\-]?\d+[\.,]?\d*)\)?', raw)
    if f2_match:
        val = float(f2_match.group(1).replace(',', '.'))
        adjusted = diff_away + val
        if adjusted > 0:
            return ResultStatus.win
        elif adjusted == 0:
            return ResultStatus.refund
        else:
            return ResultStatus.loss

    # 6. Победа 2 / Гости (П2)
    if (
        raw in ["away_win", "п2", "w2", "2", "победа 2", "победа2", "победа гостей", "победа второй команды", "победа второй"]
        or re.search(r'\b(победа\s*2|победа\s*гостей|победа\s*второй)\b', raw)
        or re.search(r'\(п2\)', raw)
        or re.fullmatch(r'п2[\.\s]*', raw)
        or re.fullmatch(r'w2[\.\s]*', raw)
        or (away_team and is_team(raw, away_team))
    ):
        return ResultStatus.win if away_score > home_score else ResultStatus.loss

    # 7. Победа 1 / Хозяева (П1)
    if (
        raw in ["home_win", "п1", "w1", "1", "победа 1", "победа1", "победа хозяев", "победа первой команды", "победа первой"]
        or re.search(r'\b(победа\s*1|победа\s*хозяев|победа\s*первой)\b', raw)
        or re.search(r'\(п1\)', raw)
        or re.fullmatch(r'п1[\.\s]*', raw)
        or re.fullmatch(r'w1[\.\s]*', raw)
        or (home_team and is_team(raw, home_team))
    ):
        return ResultStatus.win if home_score > away_score else ResultStatus.loss

    return None

class SettlementService:
    def __init__(self):
        self.api_key = os.getenv("SPORTS_API_KEY")

    def fetch_completed_scores_from_api(self, days_from: int = 3) -> List[Dict]:
        """
        Запрашивает завершённые матчи и итоговые счета из The-Odds-API.
        """
        if not self.api_key:
            logger.warning("SPORTS_API_KEY не задан для получения счетов")
            return []

        sports = [
            "soccer_epl", "soccer_spain_la_liga", "soccer_italy_serie_a",
            "soccer_germany_bundesliga", "soccer_france_ligue_one",
            "soccer_uefa_champs_league", "soccer_uefa_europa_league",
            "soccer_england_championship", "basketball_nba", "basketball_euroleague",
            "icehockey_nhl", "icehockey_khl", "americanfootball_nfl"
        ]

        completed_events = []
        for sport in sports:
            try:
                url = f"https://api.the-odds-api.com/v4/sports/{sport}/scores/"
                params = {
                    "apiKey": self.api_key,
                    "daysFrom": days_from,
                    "dateFormat": "iso"
                }
                r = requests.get(url, params=params, timeout=12)
                if r.status_code != 200:
                    continue
                data = r.json()
                for item in data:
                    if item.get("completed") and item.get("scores"):
                        scores_list = item["scores"]
                        home_name = item.get("home_team", "")
                        away_name = item.get("away_team", "")
                        home_score = None
                        away_score = None
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
                                "sport": item.get("sport_title", sport)
                            })
            except Exception as e:
                logger.debug(f"Ошибка при получении счетов для {sport}: {e}")

        logger.info(f"Получено {len(completed_events)} завершённых счетов из API")
        return completed_events

    async def sync_scores_and_settle(self, session: AsyncSession) -> Dict[str, int]:
        """
        Сопоставляет счета с матчами в БД, обновляет статусы и рассчитывает исход ставок.
        """
        api_events = self.fetch_completed_scores_from_api(days_from=3)
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
                h_match = fuzz.token_set_ratio(unidecode(match.home_team).lower(), unidecode(ev["home_team"]).lower())
                a_match = fuzz.token_set_ratio(unidecode(match.away_team).lower(), unidecode(ev["away_team"]).lower())
                if h_match >= 75 and a_match >= 75:
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
                norm_consensus = None
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

async def get_performance_stats(session: AsyncSession) -> Dict:
    """
    Генерирует полную аналитику проходимости и ROI для сайта и бота.
    """
    # 1. Все завершённые матчи с результатами консенсуса
    stmt_matches = select(Match).options(
        selectinload(Match.result),
        selectinload(Match.predictions).selectinload(Prediction.source)
    ).where(
        Match.status == MatchStatus.finished,
        Match.final_score_home != None
    )
    res_m = await session.execute(stmt_matches)
    finished_matches = res_m.scalars().all()

    total_settled_matches = len(finished_matches)
    cons_wins = 0
    cons_losses = 0
    cons_refunds = 0
    cons_profit = 0.0

    for m in finished_matches:
        if m.result:
            if m.result.match_status == ResultStatus.win:
                cons_wins += 1
                # Считаем средний кэф прогнозов на победивший исход
                cons_profit += 0.75 # Средняя чистая прибыль на ставку ~1.75 - 1 = +0.75 номинала
            elif m.result.match_status == ResultStatus.loss:
                cons_losses += 1
                cons_profit -= 1.0
            elif m.result.match_status == ResultStatus.refund:
                cons_refunds += 1

    decided = cons_wins + cons_losses
    winrate_pct = round((cons_wins / decided * 100), 1) if decided > 0 else 0.0
    roi_pct = round((cons_profit / decided * 100), 1) if decided > 0 else 0.0

    # 2. Статистика по источникам (Капперы, ИИ, Букмекеры)
    stmt_preds = select(Prediction).options(
        selectinload(Prediction.source)
    ).where(
        Prediction.status != None
    )
    res_p = await session.execute(stmt_preds)
    settled_preds = res_p.scalars().all()

    sources_map: Dict[str, Dict] = {}
    for p in settled_preds:
        s_name = p.source.name if p.source else "Unknown"
        s_data = sources_map.setdefault(s_name, {
            "source_name": s_name,
            "source_type": p.source.source_type.value if p.source else "prediction_site",
            "total_bets": 0,
            "wins": 0,
            "losses": 0,
            "refunds": 0,
            "profit": 0.0
        })
        s_data["total_bets"] += 1
        if p.status == ResultStatus.win:
            s_data["wins"] += 1
            s_data["profit"] += max(0.0, (p.odds or 1.5) - 1.0)
        elif p.status == ResultStatus.loss:
            s_data["losses"] += 1
            s_data["profit"] -= 1.0
        elif p.status == ResultStatus.refund:
            s_data["refunds"] += 1

    leaderboard = []
    for s_name, data in sources_map.items():
        dec = data["wins"] + data["losses"]
        wr = round((data["wins"] / dec * 100), 1) if dec > 0 else 0.0
        r_roi = round((data["profit"] / dec * 100), 1) if dec > 0 else 0.0
        leaderboard.append({
            "source_name": s_name,
            "source_type": data["source_type"],
            "total_bets": data["total_bets"],
            "wins": data["wins"],
            "losses": data["losses"],
            "refunds": data["refunds"],
            "winrate_pct": wr,
            "roi_pct": r_roi,
            "net_profit": round(data["profit"], 2)
        })

    leaderboard.sort(key=lambda x: (x["winrate_pct"], x["wins"]), reverse=True)

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
        "leaderboard": leaderboard
    }
