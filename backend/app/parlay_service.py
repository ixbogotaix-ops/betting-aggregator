import math
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Match, MatchStatus
from .consensus import calculate_daily_top_bets

logger = logging.getLogger(__name__)

async def generate_daily_parlays(session: AsyncSession) -> Dict:
    """
    Автоматически подбирает 2 сбалансированных экспресса на сегодня:
    1. 'safe' (Надёжный экспресс: 2-3 железобетонных исхода, кэф ~2.10 - 2.60)
    2. 'hot' (Огненный экспресс: 3-4 исхода с высоким кэфом ~4.50 - 7.50+)
    """
    # Получаем лучшие ставки на ближайшее время
    top_bets = await calculate_daily_top_bets(session, status_filter="upcoming")

    if not top_bets or len(top_bets) < 2:
        # Если предстоящих матчей меньше 2, попробуем взять свежие матчи без жесткой фильтрации
        top_bets = await calculate_daily_top_bets(session)

    if not top_bets:
        return {"safe_parlay": None, "hot_parlay": None}

    # Исключаем дубликаты команд и матчей
    valid_bets = [b for b in top_bets if b.average_odds >= 1.20]
    if len(valid_bets) < 2:
        valid_bets = top_bets

    if len(valid_bets) < 2:
        return {"safe_parlay": None, "hot_parlay": None}

    def build_parlay_item(bet):
        return {
            "match_id": bet.match_id,
            "match_name": bet.match_name,
            "match_date": bet.match_date,
            "sport_type": bet.sport_type,
            "league": bet.league,
            "outcome": bet.recommended_outcome,
            "odds": round(bet.average_odds, 2),
            "confidence_score": round(bet.confidence_score, 1),
            "home_team": bet.home_team,
            "away_team": bet.away_team,
            "home_logo": bet.home_logo,
            "away_logo": bet.away_logo
        }

    # 1. Формируем "Надёжный экспресс" (2-3 события с наивысшей уверенностью и разумным кэфом)
    safe_candidates = sorted(
        [b for b in valid_bets if 1.20 <= b.average_odds <= 1.95],
        key=lambda x: (x.confidence_score, -x.average_odds),
        reverse=True
    )
    if len(safe_candidates) < 2:
        safe_candidates = sorted(valid_bets, key=lambda x: (x.confidence_score, -x.average_odds), reverse=True)

    safe_selected = []
    seen_matches = set()
    for b in safe_candidates:
        if b.match_id not in seen_matches and len(safe_selected) < 3:
            safe_selected.append(b)
            seen_matches.add(b.match_id)
            curr_odds = 1.0
            for item in safe_selected:
                curr_odds *= item.average_odds
            if len(safe_selected) >= 2 and curr_odds >= 2.10:
                break

    safe_parlay = None
    if len(safe_selected) >= 2:
        total_odds = 1.0
        for b in safe_selected:
            total_odds *= b.average_odds
        total_odds = round(total_odds, 2)
        safe_parlay = {
            "title": "Надёжный Экспресс",
            "type": "safe",
            "tag": "ВЫСОКАЯ ПРОХОДИМОСТЬ",
            "total_odds": total_odds,
            "items_count": len(safe_selected),
            "potential_win_1000": round(1000 * total_odds),
            "items": [build_parlay_item(b) for b in safe_selected]
        }

    # 2. Формируем "Огненный экспресс" (3-4 события с коэффициентами выше)
    hot_candidates = sorted(
        [b for b in valid_bets if b.average_odds >= 1.45],
        key=lambda x: (x.average_odds, x.confidence_score),
        reverse=True
    )
    if len(hot_candidates) < 2:
        hot_candidates = sorted(valid_bets, key=lambda x: (x.average_odds, x.confidence_score), reverse=True)

    hot_selected = []
    seen_hot = set()
    for b in hot_candidates:
        if b.match_id not in seen_hot and len(hot_selected) < 4:
            hot_selected.append(b)
            seen_hot.add(b.match_id)
            curr_odds = 1.0
            for item in hot_selected:
                curr_odds *= item.average_odds
            if len(hot_selected) >= 3 and curr_odds >= 4.5:
                break

    hot_parlay = None
    if len(hot_selected) >= 2:
        total_odds = 1.0
        for b in hot_selected:
            total_odds *= b.average_odds
        total_odds = round(total_odds, 2)
        hot_parlay = {
            "title": "Огненный Экспресс",
            "type": "hot",
            "tag": "ВЫСОКИЙ КОЭФФИЦИЕНТ",
            "total_odds": total_odds,
            "items_count": len(hot_selected),
            "potential_win_1000": round(1000 * total_odds),
            "items": [build_parlay_item(b) for b in hot_selected]
        }

    return {
        "safe_parlay": safe_parlay,
        "hot_parlay": hot_parlay
    }
