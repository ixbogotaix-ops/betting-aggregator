from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone, time, timedelta
from typing import List, Dict
import re
from thefuzz import fuzz
from unidecode import unidecode

from app.models import Match, Prediction
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
    """
    if not outcome:
        return ""

    # Очищаем от суффиксов источников в скобках, например: " (Stavka TV)", " (Legalbet)", " (Vprognoze)", " (BR)"
    raw = re.sub(r'\s*\((?:stavka tv|legalbet|vprognoze|br|betting|tg|statarea|pinnacle)\b.*?\)', '', outcome, flags=re.IGNORECASE)
    # Убираем завершающие точки, кавычки и пробелы
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

    # 1. Обе забьют (ОЗ)
    if "оз" in out or "обе забьют" in out:
        if any(w in out for w in ["нет", "no", "не забьют", "— нет", "- нет"]):
            return "Обе забьют — Нет (ОЗ: Нет)"
        return "Обе забьют — Да (ОЗ: Да)"

    # 2. Двойной шанс: 1X, X2, 12
    if re.search(r'\b(1x|1х)\b', out) or ("не проиграет" in out and ("1" in out or "хозя" in out or is_team_match(out, home_team))):
        return f"{home_team} не проиграет (1X)" if home_team else "1X (Хозяева не проиграют)"
    if re.search(r'\b(x2|х2)\b', out) or ("не проиграет" in out and ("2" in out or "гост" in out or is_team_match(out, away_team))):
        return f"{away_team} не проиграет (X2)" if away_team else "X2 (Гости не проиграют)"
    if re.search(r'\b(12)\b', out) or "победа 1 или 2" in out:
        return "Победа 1 или 2 (12)"

    # 3. Ничья
    if out in ["draw", "x", "х", "ничья", "х.", "x."] or out.startswith("ничья") or out == "мир":
        return "Ничья (Х)"

    # 4. Тоталы (ТБ / ТМ)
    tb_match = re.search(r'(?:тб|больше|over)\s*\(?(\d+[\.,]?\d*)\)?', out)
    if tb_match:
        val = tb_match.group(1).replace(',', '.')
        return f"Тотал Больше {val} (ТБ {val})"
    tm_match = re.search(r'(?:тм|меньше|under)\s*\(?(\d+[\.,]?\d*)\)?', out)
    if tm_match:
        val = tm_match.group(1).replace(',', '.')
        return f"Тотал Меньше {val} (ТМ {val})"

    # 5. Форы
    f1_match = re.search(r'(?:фора\s*1|ф1)\s*\(?([\+\-]?\d+[\.,]?\d*)\)?', out)
    if f1_match:
        val = f1_match.group(1).replace(',', '.')
        return f"Фора {home_team} ({val}) (Ф1)" if home_team else f"Фора 1 ({val})"
    f2_match = re.search(r'(?:фора\s*2|ф2)\s*\(?([\+\-]?\d+[\.,]?\d*)\)?', out)
    if f2_match:
        val = f2_match.group(1).replace(',', '.')
        return f"Фора {away_team} ({val}) (Ф2)" if away_team else f"Фора 2 ({val})"

    # 6. Победа 2 / Гости / П2 / Away
    # Примеры: "ПОБЕДА 2", "победа 2.", "п2", "победа гостей", "away_win", "победа: marseille", "победа marseille"
    if (
        out in ["away_win", "п2", "w2", "2", "победа 2", "победа2", "победа гостей", "победа второй команды"]
        or out.startswith("победа 2")
        or out.endswith("п2")
        or "победа второй" in out
        or "победа гостей" in out
    ):
        return f"Победа {away_team} (П2)" if away_team else "Победа Гостей (П2)"

    # 7. Победа 1 / Хозяева / П1 / Home
    # Примеры: "ПОБЕДА 1", "победа 1.", "п1", "победа хозяев", "home_win", "победа: troyes", "победа troyes"
    if (
        out in ["home_win", "п1", "w1", "1", "победа 1", "победа1", "победа хозяев", "победа первой команды"]
        or out.startswith("победа 1")
        or out.endswith("п1")
        or "победа первой" in out
        or "победа хозяев" in out
    ):
        return f"Победа {home_team} (П1)" if home_team else "Победа Хозяев (П1)"

    # 8. Явное указание команды в исходе: "Победа: Marseille", "Победа Marseille", "Marseille", "Troyes"
    if "победа:" in out or "победа " in out or out.startswith("победа"):
        team_part = out.split(":", 1)[-1].strip() if ":" in out else out.replace("победа", "").strip()
        if away_team and is_team_match(team_part, away_team):
            return f"Победа {away_team} (П2)"
        if home_team and is_team_match(team_part, home_team):
            return f"Победа {home_team} (П1)"
        if team_part:
            return f"Победа {team_part.title()}"

    # Если исход равен названию одной из команд
    if away_team and is_team_match(out, away_team):
        return f"Победа {away_team} (П2)"
    if home_team and is_team_match(out, home_team):
        return f"Победа {home_team} (П1)"

    return raw.capitalize()

def calculate_odds_multiplier(odds: float) -> float:
    """
    Пенализация слишком низких коэффициентов (мало пользы).
    В ставках от реальных капперов обычно играют ординары от 1.60 до 2.20.
    """
    if odds < 1.40:
        return 0.5  # Штраф за верняки
    elif odds >= 1.60 and odds <= 2.20:
        return 1.15 # Бонус за оптимальный диапазон капперов
    elif odds > 3.50:
        return 0.8  # Легкий штраф за риск
    return 1.0

async def calculate_daily_top_bets(session: AsyncSession, sport_type: str = None, date_str: str = None) -> List[TopBetResponse]:
    """
    Отбирает матчи на выбранную дату и агрегирует прогнозы реальных капперов.
    Индекс уверенности сильно зависит от веса (ROI) капперов и их консенсуса.
    """
    moscow_tz = timezone(timedelta(hours=3))
    now_moscow = datetime.now(moscow_tz).replace(tzinfo=None)
    
    if date_str and date_str != "ALL":
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        start_filter = datetime.combine(target_date.date(), time.min)
        end_of_day = datetime.combine(target_date.date(), time.max)
    else:
        target_date = now_moscow
        start_filter = datetime.combine(target_date.date(), time.min)
        end_of_day = now_moscow + timedelta(days=365) # Если ALL, берем всё будущее
        
    # Скрываем матчи, которые уже начались, если смотрим текущий день или ALL
    if date_str == "ALL" or target_date.date() == now_moscow.date():
        start_filter = now_moscow

    # Получаем матчи с прогнозами и источниками
    stmt = select(Match).options(
        selectinload(Match.predictions).selectinload(Prediction.source)
    ).where(
        Match.match_date >= start_filter,
        Match.match_date <= end_of_day
    )

    if sport_type:
        stmt = stmt.where(Match.sport_type == sport_type)

    result = await session.execute(stmt)
    matches = result.scalars().all()

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
            
            # Применяем множитель коэффициента
            final_score = raw_score * calculate_odds_multiplier(avg_odds)
            
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
            
            detailed_preds.append(TopBetPredictionDetail(
                source_name=s_name,
                source_type=s_type,
                predicted_outcome=norm_p_outcome,
                odds=round(p.odds, 2),
                confidence_score=p.confidence_score,
                source_weight=s_weight,
                reasoning=p_reasoning
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
                all_predictions=detailed_preds
            ))

    # Сортируем от самых уверенных ставок к менее уверенным
    top_bets.sort(key=lambda x: x.confidence_score, reverse=True)
    return top_bets
