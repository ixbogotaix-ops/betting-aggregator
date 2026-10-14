from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone, time, timedelta
from typing import List, Dict
import re
from thefuzz import fuzz
from unidecode import unidecode

from app.models import Match, Prediction, MatchStatus
from app.schemas import TopBetResponse, TopBetPredictionDetail
from app.analytics_engine import (
    generate_source_reasoning,
    generate_match_tactical_analysis,
    generate_match_key_factors,
    generate_h2h_summary,
    generate_ai_insight,
    generate_cappers_consensus_reasoning
)
from app.logo_service import get_team_logo, get_league_country

def normalize_outcome(outcome: str, home_team: str = "", away_team: str = "") -> str:
    """
    Приводит исходы любых источников к абсолютно единому стандарту спортивного беттинга:
    - Победа [Команда] (П1)
    - Победа [Команда] (П2)
    - Ничья (Х)
    - [Команда] не проиграет (1X)
    - [Команда] не проиграет (X2)
    - Победа 1 или 2 (12)
    - Обе забьют — Да (ОЗ: Да)
    - Обе забьют — Нет (ОЗ: Нет)
    - Тотал Больше X (ТБ X)
    - Тотал Меньше X (ТМ X)
    - Фора [Команда] (X)
    - Тайм/Матч: X
    - Комбинированные ставки
    """
    if not outcome:
        return ""

    # Очищаем от суффиксов источников в скобках, например: " (Stavka TV)", " (Legalbet)", " (Vprognoze)", " (BR)"
    raw = re.sub(r'\s*\((?:stavka tv|legalbet|vprognoze|br|betting|tg|statarea|pinnacle)\b.*?\)', '', outcome, flags=re.IGNORECASE)
    raw = raw.strip().rstrip('.').strip()
    out = raw.lower()

    # Вспомогательное сопоставление с командами
    def is_team_match(query: str, target: str) -> bool:
        if not query or not target:
            return False
        q_clean = unidecode(query).lower().strip()
        t_clean = unidecode(target).lower().strip()
        if q_clean in t_clean or t_clean in q_clean:
            return True
        return fuzz.partial_ratio(q_clean, t_clean) > 80

    # 1. Тайм / Матч (КРИТИЧЕСКИ ВАЖНО: отделять от ординаров П1/П2!)
    if any(k in out for k in ["тайм / матч", "тайм/матч", "тайм-матч", "т/м:"]) or re.search(r'\b(н/п1|н/п2|п1/п1|п2/п2|п1/н|п2/н|п1/п2|п2/п1)\b', out):
        clean_tm = raw.replace('Тайм / Матч -', '').replace('Тайм/Матч -', '').replace('Тайм / Матч —', '').strip()
        return f"Тайм/Матч: {clean_tm}"

    # 2. Комбинированные ставки: Победа + Тотал / Обе забьют
    if any(k in out for k in [" и тб", " и тм", " + тб", " + тм", " и оз", " + оз", " и обе забьют"]):
        return raw.capitalize()

    # 3. Обе забьют (ОЗ)
    if "оз" in out or "обе забьют" in out:
        if any(w in out for w in ["нет", "no", "не забьют", "— нет", "- нет"]):
            return "Обе забьют — Нет (ОЗ: Нет)"
        return "Обе забьют — Да (ОЗ: Да)"

    # 4. Двойной шанс: 1X, X2, 12
    if re.search(r'\b(1x|1х)\b', out) or ("не проиграет" in out and ("1" in out or "хозя" in out or is_team_match(out, home_team))):
        return f"{home_team} не проиграет (1X)" if home_team else "1X (Хозяева не проиграют)"
    if re.search(r'\b(x2|х2)\b', out) or ("не проиграет" in out and ("2" in out or "гост" in out or is_team_match(out, away_team))):
        return f"{away_team} не проиграет (X2)" if away_team else "X2 (Гости не проиграют)"
    if re.search(r'\b(12)\b', out) or "победа 1 или 2" in out:
        return "Победа 1 или 2 (12)"

    # 5. Ничья
    if out in ["draw", "x", "х", "ничья", "х.", "x."] or out.startswith("ничья") or out == "мир":
        return "Ничья (Х)"

    # 6. Форы (ПРОВЕРЯТЬ ДО П1/П2, чтобы "Фора 2 (-1)" не стала П2!)
    f1_match = re.search(r'(?:фора\s*1|ф1)\s*\(?([\+\-]?\d+[\.,]?\d*)\)?', out)
    if f1_match:
        val = f1_match.group(1).replace(',', '.')
        return f"Фора {home_team} ({val}) (Ф1)" if home_team else f"Фора 1 ({val})"
    f2_match = re.search(r'(?:фора\s*2|ф2)\s*\(?([\+\-]?\d+[\.,]?\d*)\)?', out)
    if f2_match:
        val = f2_match.group(1).replace(',', '.')
        return f"Фора {away_team} ({val}) (Ф2)" if away_team else f"Фора 2 ({val})"

    # 7. Тоталы (ТБ / ТМ)
    tb_match = re.search(r'(?:тб|больше|over)\s*\(?(\d+[\.,]?\d*)\)?', out)
    if tb_match:
        val = tb_match.group(1).replace(',', '.')
        return f"Тотал Больше {val} (ТБ {val})"
    tm_match = re.search(r'(?:тм|меньше|under)\s*\(?(\d+[\.,]?\d*)\)?', out)
    if tm_match:
        val = tm_match.group(1).replace(',', '.')
        return f"Тотал Меньше {val} (ТМ {val})"
    tot_match = re.search(r'тотал\s*(\d+[\.,]?\d*)', out)
    if tot_match:
        val = tot_match.group(1).replace(',', '.')
        return f"Тотал Больше {val} (ТБ {val})"

    # 8. ЧИСТАЯ Победа 2 / Гости (П2)
    if (
        out in ["away_win", "п2", "w2", "2", "победа 2", "победа2", "победа гостей", "победа второй команды", "победа второй"]
        or re.search(r'\b(победа\s*2|победа\s*гостей|победа\s*второй)\b', out)
        or re.search(r'\(п2\)', out)
        or re.fullmatch(r'п2[\.\s]*', out)
        or re.fullmatch(r'w2[\.\s]*', out)
        or re.fullmatch(r'2[\.\s]*', out)
    ):
        return f"Победа {away_team} (П2)" if away_team else "Победа Гостей (П2)"

    # 9. ЧИСТАЯ Победа 1 / Хозяева (П1)
    if (
        out in ["home_win", "п1", "w1", "1", "победа 1", "победа1", "победа хозяев", "победа первой команды", "победа первой"]
        or re.search(r'\b(победа\s*1|победа\s*хозяев|победа\s*первой)\b', out)
        or re.search(r'\(п1\)', out)
        or re.fullmatch(r'п1[\.\s]*', out)
        or re.fullmatch(r'w1[\.\s]*', out)
        or re.fullmatch(r'1[\.\s]*', out)
    ):
        return f"Победа {home_team} (П1)" if home_team else "Победа Хозяев (П1)"

    # 10. Явное указание команды в исходе: "Победа: Juventus", "Победа Juventus"
    if "победа:" in out or "победа " in out or out.startswith("победа"):
        team_part = out.split(":", 1)[-1].strip() if ":" in out else out.replace("победа", "").strip()
        if not any(k in team_part for k in ["тотал", "тб", "тм", "тайм", "фора"]):
            if away_team and is_team_match(team_part, away_team):
                return f"Победа {away_team} (П2)"
            if home_team and is_team_match(team_part, home_team):
                return f"Победа {home_team} (П1)"
            if team_part:
                return f"Победа {team_part.title()}"

    # Если исход точно равен названию одной из команд
    if away_team and is_team_match(out, away_team):
        return f"Победа {away_team} (П2)"
    if home_team and is_team_match(out, home_team):
        return f"Победа {home_team} (П1)"

    return raw.capitalize()

def calculate_odds_multiplier(odds: float) -> float:
    """
    Пенализация слишком низких коэффициентов (мало пользы).
    В ставках от реальных капперов обычно играют ординары от 1.50 до 2.20.
    """
    if odds < 1.35:
        return 0.6  # Штраф за слишком мизерные кэфы
    elif odds >= 1.50 and odds <= 2.20:
        return 1.15 # Бонус за оптимальный диапазон капперов
    elif odds > 3.20:
        return 0.8  # Легкий штраф за повышенный риск
    return 1.0

def calculate_passability_multiplier(outcome: str, odds: float) -> float:
    """
    Рассчитывает множитель математической проходимости (Win Rate).
    В беттинге ставки с закрытием 2 из 3 исходов (1X, X2, Фора 0, Фора +1.5)
    и надежные тоталы (ТБ 1.5, ТБ 2, ТМ 3.5) статистически проходят в 75-88% случаев,
    в то время как чистая победа П1 / П2 на фаворита часто срывается ничьей.
    """
    if not outcome:
        return 1.0
    out_low = outcome.lower()

    # 1. Двойной шанс (1X, X2) - максимальная проходимость (78-88%)!
    if any(k in out_low for k in ["1x", "1х", "x2", "х2", "не проиграет", "двойной"]):
        return 1.35

    # 2. Мягкие надежные тоталы (ТБ 1.5, ТБ 2, ТМ 3.5, ТМ 4)
    if any(k in out_low for k in ["тб 1.5", "тб 1", "тб 2", "тм 3.5", "тм 4", "тм 4.5"]):
        return 1.25

    # 3. Форы с подстраховкой ничьей (0, +1, +1.5)
    if any(k in out_low for k in ["(0)", "(+1", "(+1.5", "(+2"]):
        return 1.25

    # 4. Обе забьют (ОЗ: Да)
    if "обе забьют — да" in out_low or "оз: да" in out_low or "обе забьют - да" in out_low:
        return 1.15

    # 5. Стандартные тоталы (ТБ 2.5, ТМ 2.5)
    if "тб 2.5" in out_low or "тм 2.5" in out_low or "тотал" in out_low:
        return 1.10

    # 6. Чистая победа (П1 / П2) - базовый множитель 1.0
    return 1.0

def get_generic_sport(s: str) -> str:
    s_low = (s or '').lower().strip()
    if any(x in s_low for x in ["mma", "ufc", "bellator", "boxing", "martial"]):
        return "MMA"
    if any(x in s_low for x in ["tennis", "atp", "wta", "itf"]):
        return "Tennis"
    if any(x in s_low for x in ["basketball", "nba", "euroleague", "vtb", "acb", "nbl"]):
        return "Basketball"
    if "veikkausliiga" not in s_low and any(x in s_low for x in ["hockey", "nhl", "khl", "ahl", "shl", "liiga", "mestis", "vhl"]):
        return "Hockey"
    if any(x in s_low for x in ["nfl", "ncaaf", "american football", "afl"]):
        return "American Football"
    if any(x in s_low for x in ["esport", "dota", "cs:go", "cs2", "counter-strike", "league of legends", "valorant"]):
        return "Esports"
    if any(x in s_low for x in ["baseball", "mlb", "kbo", "npb"]):
        return "Baseball"
    if any(x in s_low for x in ["cricket", "twenty20", "one day international", "t20", "test matches"]):
        return "Cricket"
    if any(x in s_low for x in [
        "football", "soccer", "uefa", "champions league", "europa league", "conference league",
        "la liga", "epl", "premier", "serie", "série", "bundesliga", "ligue", "eredivisie", "superliga",
        "ekstraklasa", "eliteserien", "allsvenskan", "championship", "league 1", "league 2", "3. liga",
        "copa", "sudamericana", "libertadores", "liga mx", "mls", "saudi", "primeira",
        "primera", "super league", "superleague", "superettan", "veikkausliiga", "j league", "k league",
        "division", "div", "ireland", "scotland"
    ]):
        return "Football"
    return "Other"

async def calculate_daily_top_bets(session: AsyncSession, sport_type: str = None, date_str: str = None, status_filter: str = None) -> List[TopBetResponse]:
    """
    Отбирает матчи на выбранную дату и агрегирует прогнозы реальных капперов.
    Поддерживает фильтрацию по статусу: 'upcoming', 'finished' (архив) или все.
    """
    moscow_tz = timezone(timedelta(hours=3))
    now_moscow = datetime.now(moscow_tz).replace(tzinfo=None)
    
    if status_filter == "finished":
        stmt = select(Match).options(
            selectinload(Match.predictions).selectinload(Prediction.source)
        ).where(
            (Match.status == MatchStatus.finished) | (Match.final_score_home != None)
        )
        if date_str and date_str != "ALL":
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
            stmt = stmt.where(
                Match.match_date >= datetime.combine(target_date.date(), time.min),
                Match.match_date <= datetime.combine(target_date.date(), time.max)
            )
    else:
        if date_str and date_str != "ALL":
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
            start_filter = datetime.combine(target_date.date(), time.min)
            end_of_day = datetime.combine(target_date.date(), time.max)
        else:
            target_date = now_moscow
            start_filter = datetime.combine(target_date.date(), time.min)
            end_of_day = now_moscow + timedelta(days=365) # Если ALL, берем всё будущее
            
        # Скрываем матчи, которые уже начались, если смотрим текущий день или ALL (если не запрошен архив)
        if (date_str == "ALL" or target_date.date() == now_moscow.date()) and status_filter != "finished":
            start_filter = now_moscow

        # Получаем матчи с прогнозами и источниками
        stmt = select(Match).options(
            selectinload(Match.predictions).selectinload(Prediction.source)
        ).where(
            Match.match_date >= start_filter,
            Match.match_date <= end_of_day
        )
        if status_filter == "upcoming":
            stmt = stmt.where(Match.status == MatchStatus.upcoming)

    result = await session.execute(stmt)
    matches = result.scalars().all()

    if sport_type and sport_type != 'All':
        matches = [m for m in matches if get_generic_sport(m.sport_type) == sport_type or (m.sport_type and m.sport_type.lower() == sport_type.lower())]

    top_bets = []

    for match in matches:
        if not match.predictions:
            continue

        # Группируем прогнозы по исходам с нормализацией текста
        outcomes_map: Dict[str, List[Prediction]] = {}
        for pred in match.predictions:
            norm_outcome = normalize_outcome(pred.predicted_outcome, match.home_team, match.away_team)
            outcomes_map.setdefault(norm_outcome, []).append(pred)

        best_outcome = None
        best_score = -1.0
        best_avg_odds = 0.0
        best_sources = []

        # Анализируем каждый возможный исход в этом матче
        for outcome, preds in outcomes_map.items():
            raw_score = 0.0
            total_odds = 0.0
            supporting_sources = []
            
            # Считаем суммарный вес капперов
            high_tier_cappers_count = 0

            for p in preds:
                # Вес источника базируется на его ROI (устанавливается парсером)
                source_weight = p.source.weight if p.source and p.source.weight else 1.0
                raw_score += source_weight
                total_odds += p.odds
                
                if p.source:
                    # Добавляем имя каппера и его вес (для визуала на фронте)
                    source_label = f"{p.source.name} (Рейтинг: {round(source_weight, 1)})"
                    supporting_sources.append(source_label)
                    
                if source_weight >= 3.0: # Считаем, что каппер топ-уровня
                    high_tier_cappers_count += 1

            avg_odds = total_odds / len(preds)
            
            # Применяем множитель коэффициента и бонус математической надежности (проходимости)
            final_score = raw_score * calculate_odds_multiplier(avg_odds) * calculate_passability_multiplier(outcome, avg_odds)
            
            # БОНУС ЗА КОНСЕНСУС: Если сразу несколько ТОП-капперов дали этот прогноз
            if len(preds) > 1:
                consensus_multiplier = 1.0 + (len(preds) * 0.2)
                # Если среди них есть профи, даем еще больший буст
                consensus_multiplier += (high_tier_cappers_count * 0.3)
                final_score *= consensus_multiplier

            # Переводим в 100-балльную шкалу.
            # Эталонный максимальный скор: 3 топ-каппера (вес 5.0) = 15.0 базовая + консенсус = ~30.0
            MAX_EXPECTED_SCORE = 30.0
            normalized_score = min((final_score / MAX_EXPECTED_SCORE) * 100, 100.0)

            if normalized_score > best_score:
                best_score = normalized_score
                best_outcome = outcome
                best_avg_odds = avg_odds
                best_sources = supporting_sources

        # Собираем подробный список всех мнений капперов по этому матчу
        detailed_preds = []
        for p in match.predictions:
            s_name = p.source.name if p.source else "Эксперт"
            s_type = p.source.source_type.value if (p.source and hasattr(p.source.source_type, 'value')) else (str(p.source.source_type) if p.source else "site")
            s_weight = round(p.source.weight, 1) if (p.source and p.source.weight) else 1.0
            
            # Единый стандарт исхода для всех капперов и источников
            norm_p_outcome = normalize_outcome(p.predicted_outcome, match.home_team, match.away_team)
            
            # Размышления эксперта: из БД или динамическая генерация конкретных аргументов
            p_reasoning = getattr(p, 'reasoning', None)
            if not p_reasoning or len(str(p_reasoning).strip()) < 10:
                p_reasoning = generate_source_reasoning(
                    source_name=s_name,
                    source_type=s_type,
                    sport=match.sport_type,
                    home_team=match.home_team,
                    away_team=match.away_team,
                    outcome=norm_p_outcome,
                    odds=p.odds,
                    source_weight=s_weight
                )
            
            # Исход ставки источника (если матч завершен)
            p_status_val = None
            if hasattr(p, 'status') and p.status:
                p_status_val = p.status.value if hasattr(p.status, 'value') else str(p.status)
            elif match.final_score_home is not None and match.final_score_away is not None:
                from .settlement_service import evaluate_bet_outcome
                eval_st = evaluate_bet_outcome(norm_p_outcome, match.final_score_home, match.final_score_away, match.home_team, match.away_team)
                if eval_st:
                    p_status_val = eval_st.value

            detailed_preds.append(TopBetPredictionDetail(
                source_name=s_name,
                source_type=s_type,
                predicted_outcome=norm_p_outcome,
                odds=round(p.odds, 2),
                confidence_score=p.confidence_score,
                source_weight=s_weight,
                reasoning=p_reasoning,
                status=p_status_val
            ))

        # Выводим в топ, только если скор больше 5.0 (чтобы покрывать даже одиночные уверенные прогнозы)
        if best_score >= 5.0:
            # Тактический анализ матча
            tactical = getattr(match, 'tactical_analysis', None)
            if not tactical or len(str(tactical).strip()) < 20:
                tactical = generate_match_tactical_analysis(
                    match.sport_type, match.league, match.home_team, match.away_team, best_outcome, round(best_avg_odds, 2)
                )

            # Ключевые факторы матча
            factors_raw = getattr(match, 'key_factors', None)
            factors = []
            if factors_raw:
                try:
                    import json
                    factors = json.loads(factors_raw) if isinstance(factors_raw, str) else list(factors_raw)
                except Exception:
                    factors = []
            if not factors:
                factors = generate_match_key_factors(
                    match.sport_type, match.league, match.home_team, match.away_team, best_outcome, round(best_avg_odds, 2)
                )

            # Очные встречи H2H
            h2h = generate_h2h_summary(match.home_team, match.away_team, match.sport_type)

            # Инсайт ИИ
            ai_in = match.ai_insight if (match.ai_insight and len(match.ai_insight.strip()) > 5) else generate_ai_insight(
                match.sport_type, match.home_team, match.away_team, best_outcome, round(best_avg_odds, 2), round(best_score, 1)
            )

            # Сводка капперов
            cappers_re = match.cappers_reasoning if (match.cappers_reasoning and len(match.cappers_reasoning.strip()) > 5) else generate_cappers_consensus_reasoning(
                best_sources, best_outcome, round(best_avg_odds, 2)
            )

            # Эмблемы команд и флаг страны
            h_logo = get_team_logo(match.home_team, match.sport_type)
            a_logo = get_team_logo(match.away_team, match.sport_type)
            country_info = get_league_country(match.league, match.sport_type)

            # Исход консенсуса
            bet_res_val = None
            if match.final_score_home is not None and match.final_score_away is not None:
                from .settlement_service import evaluate_bet_outcome
                eval_cons = evaluate_bet_outcome(best_outcome, match.final_score_home, match.final_score_away, match.home_team, match.away_team)
                if eval_cons:
                    bet_res_val = eval_cons.value
            
            m_status_str = match.status.value if hasattr(match.status, 'value') else str(match.status)

            top_bets.append(TopBetResponse(
                match_id=match.id,
                match_name=f"{match.home_team} vs {match.away_team}",
                match_date=match.match_date,
                league=match.league,
                sport_type=match.sport_type,
                recommended_outcome=best_outcome,
                average_odds=round(best_avg_odds, 2),
                confidence_score=round(best_score, 1),
                supporting_sources=best_sources,
                is_bet_of_the_day=match.is_bet_of_the_day or False,
                ai_insight=ai_in,
                cappers_reasoning=cappers_re,
                tactical_analysis=tactical,
                key_factors=factors,
                h2h_summary=h2h,
                home_team=match.home_team,
                away_team=match.away_team,
                home_logo=h_logo,
                away_logo=a_logo,
                country_name=country_info.get("name"),
                country_flag_url=country_info.get("flag_url"),
                country_flag_emoji=country_info.get("emoji"),
                final_score_home=match.final_score_home,
                final_score_away=match.final_score_away,
                status=m_status_str,
                bet_result=bet_res_val,
                all_predictions=detailed_preds
            ))

    # Сортируем от самых уверенных ставок к менее уверенным
    top_bets.sort(key=lambda x: x.confidence_score, reverse=True)

    # Определяем Ставку Дня: ровно 1 лучшая ставка на каждый базовый вид спорта
    seen_botd_sports = set()
    for bet in top_bets:
        gen = get_generic_sport(bet.sport_type)
        if bet.is_bet_of_the_day:
            if gen not in seen_botd_sports:
                seen_botd_sports.add(gen)
            else:
                bet.is_bet_of_the_day = False

    # Для тех видов спорта, где флага еще не было, отмечаем самую уверенную ставку
    for bet in top_bets:
        gen = get_generic_sport(bet.sport_type)
        if gen not in seen_botd_sports:
            bet.is_bet_of_the_day = True
            seen_botd_sports.add(gen)

    return top_bets
