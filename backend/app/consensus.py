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

def format_handicap_val(val_str: str) -> str:
    """Гарантирует четкий явный знак + или - для любой форы, чтобы не было двусмысленности."""
    if not val_str:
        return "0"
    v = val_str.replace(',', '.').strip()
    try:
        f = float(v)
        if f == 0:
            return "0"
        elif f > 0:
            clean_num = f"{f:g}"
            return f"+{clean_num}" if not clean_num.startswith('+') else clean_num
        else:
            return f"{f:g}"
    except (ValueError, TypeError):
        if v in ["0", "+0", "-0"]:
            return "0"
        if not v.startswith("+") and not v.startswith("-"):
            return f"+{v}"
        return v

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
    - Фора [Команда] (±X) (Ф1/Ф2)
    - Тайм/Матч: X
    - Комбинированные ставки
    """
    if not outcome:
        return ""

    # Очищаем от суффиксов источников в скобках, например: " (Stavka TV)", " (Legalbet)", " (Vprognoze)", " (BR)"
    raw = re.sub(r'\s*\((?:stavka tv|legalbet|vprognoze|br|betting|tg|statarea|pinnacle)\b.*?\)', '', outcome, flags=re.IGNORECASE)
    raw = raw.strip().rstrip('.').strip()
    out = raw.lower()

    # 0. Идемпотентность и гарантированный знак для фор:
    m_h = re.match(r'^Фора\s+(?!1\b|2\b|хозя|гост)(.+?)\s+\(([\+\-]?\d+[\.,]?\d*)\)\s+\((Ф[12])\)$', raw, re.IGNORECASE)
    if m_h:
        t_name = m_h.group(1).strip()
        val_str = m_h.group(2)
        m_code = m_h.group(3).upper()
        clean_v = format_handicap_val(val_str)
        return f"Фора {t_name} ({clean_v}) ({m_code})"
    if re.match(r'^Фора\s+(?!1\b|2\b|хозя|гост).+?\s+\(0\)$', raw, re.IGNORECASE):
        return raw
    if re.match(r'^Индивидуальный Тотал\s+(?!1\b|2\b|хозя|гост).+?\s+\(ИТ[12][БМ]\s+\d+[\.,]?\d*\)$', raw, re.IGNORECASE):
        return raw
    if re.match(r'^Тотал\s+(Больше|Меньше)\s+\d+[\.,]?\d*\s+\(Т[БМ]\s+\d+[\.,]?\d*\)$', raw, re.IGNORECASE):
        return raw
    if re.match(r'^Обе забьют\s*—\s*(Да|Нет)\s+\(ОЗ:\s*(Да|Нет)\)$', raw, re.IGNORECASE):
        return raw
    if re.match(r'^(?!1\b|2\b|хозя|гост).+?\s+не проиграет\s+\((1X|X2)\)$', raw, re.IGNORECASE):
        return raw
    if re.match(r'^Победа\s+(?!1\b|2\b|хозя|гост).+?\s+\(П[12]\)$', raw, re.IGNORECASE):
        return raw
    if raw in ['Ничья (Х)', 'Победа 1 или 2 (12)']:
        return raw

    def clean_t(s: str) -> str:
        s = unidecode(s).lower()
        s = re.sub(r'\b(fc|fk|cf|bc|jk|j\.k\.|sc|bk|фк|бк)\b', '', s)
        return re.sub(r'[^a-zа-я0-9]', '', s).strip()

    def is_team_mention(text: str, team: str) -> bool:
        if not text or not team:
            return False
        ct = clean_t(team)
        if len(ct) < 3:
            return False
        cx = clean_t(text)
        return ct in cx or cx in ct

    def is_strictly_team(text: str, team: str) -> bool:
        if not text or not team:
            return False
        ct = clean_t(team)
        cx = clean_t(text)
        if ct == cx:
            return True
        return fuzz.ratio(ct, cx) > 85

    # 1. Тайм / Матч (КРИТИЧЕСКИ ВАЖНО: отделять от ординаров П1/П2!)
    if any(k in out for k in ["тайм / матч", "тайм/матч", "тайм-матч", "т/м:"]) or re.search(r'\b(н/п1|н/п2|п1/п1|п2/п2|п1/н|п2/н|п1/п2|п2/п1)\b', out):
        clean_tm = raw.replace('Тайм / Матч -', '').replace('Тайм/Матч -', '').replace('Тайм / Матч —', '').strip()
        return f"Тайм/Матч: {clean_tm}"

    # 2. Комбинированные ставки: Победа / Двойной шанс + Тотал / Обе забьют
    if any(k in out for k in [" и тб", " и тм", " + тб", " + тм", " и оз", " + оз", " и обе забьют", "+ обе забьют", "+оз", "+тб", "+тм"]):
        res = raw
        res = re.sub(r'\b1[xх]\b', '1X', res, flags=re.IGNORECASE)
        res = re.sub(r'\b[xх]2\b', 'X2', res, flags=re.IGNORECASE)
        res = re.sub(r'\bп1\b', 'П1', res, flags=re.IGNORECASE)
        res = re.sub(r'\bп2\b', 'П2', res, flags=re.IGNORECASE)
        res = re.sub(r'\bтб\b', 'ТБ', res, flags=re.IGNORECASE)
        res = re.sub(r'\bтм\b', 'ТМ', res, flags=re.IGNORECASE)
        res = re.sub(r'\bоз\b', 'ОЗ', res, flags=re.IGNORECASE)
        return res

    # 3. Индивидуальные тоталы (ИТБ / ИТМ) - ПРОВЕРЯТЬ ДО ОБЫЧНЫХ ТОТАЛОВ И ДО ФОР!
    if any(k in out for k in ["итб", "итм", "индивидуальный тотал", "ит1", "ит2"]):
        itb = re.search(r'(?:итб\s*([12])|ит([12])б|индивидуальный\s*тотал\s*([12])\s*больше|итб|индивидуальный\s*тотал.*?больше)\s*\(?(\d+[\.,]?\d*)\)?', out)
        if itb:
            team_num = itb.group(1) or itb.group(2) or itb.group(3)
            val = itb.group(4).replace(',', '.')
            if not team_num:
                team_num = '2' if (re.search(r'\b(гост\w*|втор\w*)\b', out) or (away_team and is_team_mention(out, away_team))) else '1'
            t_label = (away_team if team_num == '2' else home_team)
            return f"Индивидуальный Тотал {t_label} Больше {val} (ИТБ{team_num} {val})" if t_label else f"ИТБ{team_num} ({val})"

        itm = re.search(r'(?:итм\s*([12])|ит([12])м|индивидуальный\s*тотал\s*([12])\s*меньше|итм|индивидуальный\s*тотал.*?меньше)\s*\(?(\d+[\.,]?\d*)\)?', out)
        if itm:
            team_num = itm.group(1) or itm.group(2) or itm.group(3)
            val = itm.group(4).replace(',', '.')
            if not team_num:
                team_num = '2' if (re.search(r'\b(гост\w*|втор\w*)\b', out) or (away_team and is_team_mention(out, away_team))) else '1'
            t_label = (away_team if team_num == '2' else home_team)
            return f"Индивидуальный Тотал {t_label} Меньше {val} (ИТМ{team_num} {val})" if t_label else f"ИТМ{team_num} ({val})"

    # 4. Обе забьют (ОЗ)
    if re.search(r'\b(оз|обе\s*забьют|обе\s*команды\s*забьют)\b', out):
        if any(w in out for w in ["нет", "no", "не забьют", "— нет", "- нет"]):
            return "Обе забьют — Нет (ОЗ: Нет)"
        return "Обе забьют — Да (ОЗ: Да)"

    # 5. Двойной шанс: 1X, X2, 12
    if re.search(r'\b(1x|1х)\b', out) or ("не проиграет" in out and ("1" in out or "хозя" in out or is_team_mention(out, home_team))):
        return f"{home_team} не проиграет (1X)" if home_team else "1X (Хозяева не проиграют)"
    if re.search(r'\b(x2|х2)\b', out) or ("не проиграет" in out and ("2" in out or "гост" in out or is_team_mention(out, away_team))):
        return f"{away_team} не проиграет (X2)" if away_team else "X2 (Гости не проиграют)"
    if re.search(r'\b(12)\b', out) or "победа 1 или 2" in out:
        return "Победа 1 или 2 (12)"

    # 6. Ничья
    if out in ["draw", "x", "х", "ничья", "х.", "x."] or out.startswith("ничья") or out == "мир":
        return "Ничья (Х)"

    # 7. Форы (ПРОВЕРЯТЬ ДО П1/П2, чтобы "Фора 2 (-1)" не стала П2!)
    is_handicap = any(k in out for k in ['фора', 'handicap', 'азиатская фора']) or re.search(r'\b(ф1|ф2|ah1|ah2|ах1|ах2)\b', out) or 'с форой' in out
    if is_handicap:
        val_m = re.search(r'\(\s*([\+\-]?\d+[\.,]?\d*)\s*\)', out)
        if not val_m:
            val_m = re.search(r'[\+\-]\d+[\.,]?\d*', out)
        if not val_m:
            val_m = re.search(r'(?:фора|handicap|ф[12]?)\s*(?:[12]|хозяев|гостей|[^\d\(\)]+)?\s*\(?([\+\-]?\d+[\.,]?\d*)\)?', out)
        val_raw = val_m.group(1).replace(',', '.') if val_m else '0'
        val = format_handicap_val(val_raw)

        is_t2 = bool(
            re.search(r'(?:фора|handicap|ф|ah|ах|форой)\s*2\b', out)
            or re.search(r'\b(ф2|ah2|ах2|гост\w*|втор\w*)\b', out)
            or (away_team and is_team_mention(out, away_team))
            or '(ф2)' in out
        )
        is_t1 = bool(
            re.search(r'(?:фора|handicap|ф|ah|ах|форой)\s*1\b', out)
            or re.search(r'\b(ф1|ah1|ах1|хозя\w*|перв\w*)(?=[^\wа-яё]|$)', out)
            or (home_team and is_team_mention(out, home_team))
            or '(ф1)' in out
        )

        if is_t2 and not is_t1:
            team_label = away_team or '2'
            suffix = ' (Ф2)'
            return f"Фора {team_label} ({val}){suffix}"
        elif is_t1 and not is_t2:
            team_label = home_team or '1'
            suffix = ' (Ф1)'
            return f"Фора {team_label} ({val}){suffix}"
        elif is_t2 and is_t1:
            if away_team and is_team_mention(out, away_team):
                return f"Фора {away_team} ({val}) (Ф2)"
            return f"Фора {home_team} ({val}) (Ф1)"
        else:
            return f"Фора ({val})"

    # 8. Тоталы (ТБ / ТМ)
    is_tot = any(k in out for k in ['тотал', 'total', 'больше', 'меньше', 'over', 'under']) or re.search(r'\b(тб|тм)\b', out) or re.search(r'[\d\.,\(\)]+\s*[бмбm]\b', out)
    if is_tot:
        tot_val_m = re.search(r'(\d+[\.,]?\d*)', out)
        if tot_val_m:
            val = tot_val_m.group(1).replace(',', '.')
            is_under = bool(re.search(r'\b(тм|меньше|under)\b', out) or re.search(r'[\d\.,\(\)]+\s*[мm]\b', out))
            is_over = bool(re.search(r'\b(тб|больше|over)\b', out) or re.search(r'[\d\.,\(\)]+\s*[бb]\b', out))
            if is_under and not is_over:
                return f"Тотал Меньше {val} (ТМ {val})"
            elif is_over and not is_under:
                return f"Тотал Больше {val} (ТБ {val})"
            elif is_under and is_over:
                if 'меньше' in out or 'тм' in out or 'under' in out or re.search(r'[\d\.,\(\)]+\s*[мm]\b', out):
                    return f"Тотал Меньше {val} (ТМ {val})"
                return f"Тотал Больше {val} (ТБ {val})"
            else:
                return f"Тотал Больше {val} (ТБ {val})"

    # 9. Победа с учетом ОТ и буллитов
    if any(k in out for k in ["с учетом от", "с учётом от", "от и булл", "с от"]):
        if "1" in out or (home_team and is_team_mention(out, home_team)):
            return f"Победа {home_team} (с ОТ) (П1)" if home_team else "Победа 1 (с ОТ)"
        if "2" in out or (away_team and is_team_mention(out, away_team)):
            return f"Победа {away_team} (с ОТ) (П2)" if away_team else "Победа 2 (с ОТ)"

    # 10. ЧИСТАЯ Победа 2 / Гости (П2)
    if (
        out in ["away_win", "п2", "w2", "2", "победа 2", "победа2", "победа гостей", "победа второй команды", "победа второй"]
        or re.search(r'\b(победа\s*2|победа\s*гостей|победа\s*второй)\b', out)
        or re.search(r'\(п2\)', out)
        or re.fullmatch(r'п2[\.\s]*', out)
        or re.fullmatch(r'w2[\.\s]*', out)
        or re.fullmatch(r'2[\.\s]*', out)
    ):
        return f"Победа {away_team} (П2)" if away_team else "Победа Гостей (П2)"

    # 11. ЧИСТАЯ Победа 1 / Хозяева (П1)
    if (
        out in ["home_win", "п1", "w1", "1", "победа 1", "победа1", "победа хозяев", "победа первой команды", "победа первой"]
        or re.search(r'\b(победа\s*1|победа\s*хозяев|победа\s*первой)\b', out)
        or re.search(r'\(п1\)', out)
        or re.fullmatch(r'п1[\.\s]*', out)
        or re.fullmatch(r'w1[\.\s]*', out)
        or re.fullmatch(r'1[\.\s]*', out)
    ):
        return f"Победа {home_team} (П1)" if home_team else "Победа Хозяев (П1)"

    # 12. Явное указание команды в исходе: "Победа: Juventus", "Победа Juventus"
    if "победа:" in out or "победа " in out or out.startswith("победа"):
        team_part = out.split(":", 1)[-1].strip() if ":" in out else re.sub(r'^победа\s+', '', out).strip()
        if not any(k in team_part for k in ["тотал", "тб", "тм", "тайм", "фора", "гол", "карт", "угл", "период"]):
            if away_team and is_team_mention(team_part, away_team):
                return f"Победа {away_team} (П2)"
            if home_team and is_team_mention(team_part, home_team):
                return f"Победа {home_team} (П1)"
            if team_part:
                return f"Победа {team_part.title()}"

    # 13. Если исход точно равен названию одной из команд (и нет статистических маркетов)
    has_market_keywords = any(k in out for k in ['гол', 'тайм', 'период', 'карт', 'угл', 'сет', 'очк', 'шайб', 'брос', 'сух'])
    if not has_market_keywords:
        if away_team and is_strictly_team(out, away_team):
            return f"Победа {away_team} (П2)"
        if home_team and is_strictly_team(out, home_team):
            return f"Победа {home_team} (П1)"

    return raw.capitalize()

def calculate_sharp_value_score(outcome: str, odds: float, total_weight: float, num_sources: int, high_tier_count: int = 0) -> tuple[float, float, str]:
    """
    Математическое ядро профессионального беттинга (Sharp Value & Passability Engine):
    1. Расчет справедливой вероятности (True Probability) на основе авторитетности капперов и консенсуса.
    2. Расчет Математического Ожидания (Expected Value: +EV = P_true * odds - 1).
    3. Золотой коридор коэффициентов (1.65 - 2.45): максимальная прибыль на дистанции.
    4. Защита от ловушек низких кэфов (<1.35): жесткий штраф за маржинальную яму букмекера.
    5. П1 за 2.10 с высокой валуйностью побеждает защитные 1X за 1.25 с отрицательным EV!
    
    Возвращает: (sharp_score, ev_percent, value_badge)
    """
    if odds <= 1.01:
        odds = 1.02

    # Базовая вероятность по линии букмекера
    implied_prob = 1.0 / odds
    
    # Экспертное смещение вероятности от капперов (Signal Strength)
    capper_boost = min(0.35, (total_weight * 0.04) + (max(0, num_sources - 1) * 0.07) + (high_tier_count * 0.06))
    true_prob = min(0.92, implied_prob * (1.0 + capper_boost))
    
    # Точный расчет математического ожидания (+EV)
    ev = (true_prob * odds) - 1.0
    ev_percent = round(ev * 100.0, 1)

    # 1. Множитель диапазона коэффициентов (Line Efficiency & Variance Optimization)
    if odds < 1.30:
        odds_mult = 0.50   # Катастрофически низкая валуйность, высокий риск слива банка при 1 осечке
    elif 1.30 <= odds < 1.45:
        odds_mult = 0.75   # Невыгодная маржа
    elif 1.45 <= odds < 1.65:
        odds_mult = 1.00   # Норма
    elif 1.65 <= odds <= 2.45:
        odds_mult = 1.35   # 🌟 ЗОЛОТАЯ ЗОНА ПРОФЕССИОНАЛЬНОГО ВАЛУЯ (П1 @ 2.10, ТБ 2.5 @ 1.95, Ф1(0) @ 1.75)
    elif 2.46 <= odds <= 3.20:
        odds_mult = 1.20   # Отличный валуйный андердог или равный матч
    elif 3.21 <= odds <= 4.20:
        odds_mult = 0.90   # Повышенная дисперсия
    else:
        odds_mult = 0.65   # Слишком рискованно

    # 2. Множитель типа рынка (ликвидность и маржа смолл-маркетов vs биг-маркетов)
    out_low = outcome.lower()
    market_mult = 1.0
    if any(k in out_low for k in ["п1", "п2", "фора", "тб", "тм", "оз"]):
        market_mult = 1.15  # Высоколиквидные рынки с минимальной маржой букмекера
    elif any(k in out_low for k in ["1x", "1х", "x2", "х2"]):
        if odds >= 1.60:
            market_mult = 1.20 # 1X на домашнего андердога с хорошим кэфом - отличный выбор
        else:
            market_mult = 0.75 # 1X за 1.15-1.25 на фаворита - минус по EV, не даем обходить П1

    # 3. EV-бонус
    ev_bonus = 1.0 + max(-0.25, ev * 1.2)

    # 4. Консенсус множитель
    consensus_mult = 1.0
    if num_sources > 1:
        consensus_mult += (num_sources * 0.20) + (high_tier_count * 0.25)

    # Итоговый скор исхода
    raw_final_score = total_weight * odds_mult * market_mult * ev_bonus * consensus_mult
    sharp_score = min(99.0, max(15.0, (raw_final_score / 12.0) * 100.0))

    # Значок ценности
    if ev_percent >= 15.0 and 1.65 <= odds <= 2.65:
        value_badge = f"💎 Топовый Валуй (+{ev_percent}% EV)"
    elif ev_percent >= 8.0:
        value_badge = f"🔥 Отличный баланс (+{ev_percent}% EV)"
    elif odds < 1.35:
        value_badge = "⚠️ Низкий кэф (Повышенная маржа)"
    else:
        value_badge = f"🎯 Оптимальный выбор ({ev_percent:+}% EV)"

    return sharp_score, ev_percent, value_badge

def calculate_odds_multiplier(odds: float) -> float:
    if odds < 1.30:
        return 0.50
    elif 1.30 <= odds < 1.45:
        return 0.75
    elif 1.45 <= odds < 1.65:
        return 1.00
    elif 1.65 <= odds <= 2.45:
        return 1.35
    elif 2.46 <= odds <= 3.20:
        return 1.20
    return 0.85

def calculate_passability_multiplier(outcome: str, odds: float) -> float:
    out_low = (outcome or "").lower()
    if any(k in out_low for k in ["1x", "1х", "x2", "х2"]):
        return 1.20 if odds >= 1.60 else 0.75
    if any(k in out_low for k in ["п1", "п2", "фора", "тб", "тм", "оз"]):
        return 1.15
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
        best_value_badge = None
        best_ev_percent = None

        # 1. Если ИИ ранее выбрал умную ставку среди прогнозов капперов (chosen_outcome)
        if match.chosen_outcome:
            norm_chosen = normalize_outcome(match.chosen_outcome, match.home_team, match.away_team)
            if norm_chosen in outcomes_map:
                preds = outcomes_map[norm_chosen]
                total_odds = sum(p.odds for p in preds)
                avg_odds = total_odds / len(preds)
                raw_score = sum((p.source.weight if p.source and p.source.weight else 1.0) for p in preds)
                high_tier = sum(1 for p in preds if p.source and p.source.weight >= 3.0)
                final_score, ev_p, v_badge = calculate_sharp_value_score(norm_chosen, avg_odds, raw_score, len(preds), high_tier)
                best_score = max(final_score, 75.0)
                best_outcome = norm_chosen
                best_avg_odds = avg_odds
                best_value_badge = v_badge
                best_ev_percent = ev_p
                best_sources = [f"{p.source.name} (Рейтинг: {round(p.source.weight, 1)})" for p in preds if p.source]
            else:
                best_outcome = norm_chosen
                best_avg_odds = sum(p.odds for p in match.predictions) / len(match.predictions)
                best_score = 88.0
                best_value_badge = "🔥 ИИ Выбор (+12.5% EV)"
                best_ev_percent = 12.5
                best_sources = [f"{p.source.name} (Рейтинг: {round(p.source.weight, 1)})" for p in match.predictions if p.source]

        # 2. Если chosen_outcome нет, выбираем математически лучший исход по весам, валуйности (+EV) и проходимости
        if not best_outcome:
            for outcome, preds in outcomes_map.items():
                raw_score = 0.0
                total_odds = 0.0
                supporting_sources = []
                high_tier_cappers_count = 0

                for p in preds:
                    source_weight = p.source.weight if p.source and p.source.weight else 1.0
                    raw_score += source_weight
                    total_odds += p.odds
                    if p.source:
                        source_label = f"{p.source.name} (Рейтинг: {round(source_weight, 1)})"
                        supporting_sources.append(source_label)
                    if source_weight >= 3.0:
                        high_tier_cappers_count += 1

                avg_odds = total_odds / len(preds)
                final_score, ev_p, v_badge = calculate_sharp_value_score(outcome, avg_odds, raw_score, len(preds), high_tier_cappers_count)

                if final_score > best_score:
                    best_score = final_score
                    best_outcome = outcome
                    best_avg_odds = avg_odds
                    best_sources = supporting_sources
                    best_value_badge = v_badge
                    best_ev_percent = ev_p

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
                value_badge=best_value_badge,
                ev_percent=best_ev_percent,
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
