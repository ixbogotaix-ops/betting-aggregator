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

    # Исключаем матчи далекого будущего (более 36 часов вперед) и уже прошедшие
    now_utc = datetime.now(timezone.utc)
    max_horizon = now_utc + timedelta(hours=36)

    def is_upcoming_and_near(b):
        if not hasattr(b, 'match_date') or not b.match_date:
            return True
        md = b.match_date
        if md.tzinfo is None:
            md = md.replace(tzinfo=timezone.utc)
        return (now_utc - timedelta(minutes=15)) <= md <= max_horizon

    near_bets = [b for b in top_bets if is_upcoming_and_near(b)]
    if len(near_bets) >= 2:
        valid_bets = [b for b in near_bets if b.average_odds >= 1.20]
    else:
        valid_bets = [b for b in top_bets if b.average_odds >= 1.20]

    if len(valid_bets) < 2:
        valid_bets = top_bets

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

    # 1. Формируем "Экспресс Тройного ИИ" (на базе Робобет + Vitibet + Zulubet)
    ai_parlay = None
    try:
        from .robobet_scraper import get_robobet_cached
        robobet_data = get_robobet_cached()
        robo_matches = robobet_data.get("matches", [])
        
        # Только предстоящие матчи
        robo_upcoming = [
            m for m in robo_matches 
            if not m.get("is_time_past") 
            and not m.get("is_finished") 
            and (m.get("score") == "- : -" or not m.get("score"))
            and float(m.get("rec_odd") or 0) >= 1.25
        ]

        # Сортируем: сначала 3/3 супер-консенсус, затем 2/2, затем высокая вероятность
        robo_sorted = sorted(
            robo_upcoming,
            key=lambda m: (
                1 if m.get("is_triple_consensus") else 0,
                1 if m.get("is_math_consensus") else 0,
                float(m.get("rec_prob") or 0)
            ),
            reverse=True
        )

        ai_selected = []
        seen_teams = set()
        for m in robo_sorted:
            t1 = m.get("team1")
            t2 = m.get("team2")
            if t1 not in seen_teams and t2 not in seen_teams and len(ai_selected) < 3:
                ai_selected.append(m)
                seen_teams.add(t1)
                seen_teams.add(t2)
                curr_odds = 1.0
                for it in ai_selected:
                    curr_odds *= float(it.get("rec_odd") or 1.5)
                if len(ai_selected) >= 2 and curr_odds >= 2.10:
                    break

        if len(ai_selected) >= 2:
            total_ai_odds = 1.0
            for it in ai_selected:
                total_ai_odds *= float(it.get("rec_odd") or 1.5)
            total_ai_odds = round(total_ai_odds, 2)
            
            ai_items = []
            for m in ai_selected:
                tip_suffix = f" (Vitibet {m.get('vitibet_proj_score')})" if m.get('vitibet_proj_score') else ""
                ai_items.append({
                    "match_id": m.get("id"),
                    "match_name": f"{m.get('team1')} vs {m.get('team2')}",
                    "match_date": datetime.now(timezone.utc),
                    "sport_type": "Футбол",
                    "league": f"Тройной ИИ ({m.get('country', 'Турнир')})",
                    "outcome": f"{m.get('recommendation')} [{m.get('rec_prob')}%]{tip_suffix}",
                    "odds": round(float(m.get("rec_odd") or 1.50), 2),
                    "confidence_score": round(float(m.get("rec_prob") or 65.0), 1),
                    "home_team": m.get("team1"),
                    "away_team": m.get("team2"),
                    "home_logo": m.get("home_logo"),
                    "away_logo": m.get("away_logo")
                })

            has_triple = any(m.get("is_triple_consensus") for m in ai_selected)
            ai_parlay = {
                "title": "Экспресс Тройного ИИ",
                "type": "ai",
                "tag": "🔥 СУПЕР ИИ 3/3" if has_triple else "МАТЕМАТИЧЕСКИЙ КОНСЕНСУС",
                "total_odds": total_ai_odds,
                "items_count": len(ai_items),
                "potential_win_1000": round(1000 * total_ai_odds),
                "items": ai_items
            }
        else:
            # Fallback к событиям с наивысшим рейтингом доверия
            ai_candidates = sorted(valid_bets, key=lambda x: (x.confidence_score, -x.average_odds), reverse=True)
            ai_fallback_selected = []
            seen_fallback = set()
            for b in ai_candidates:
                if b.match_id not in seen_fallback and len(ai_fallback_selected) < 3:
                    ai_fallback_selected.append(b)
                    seen_fallback.add(b.match_id)
                    curr_odds = 1.0
                    for item in ai_fallback_selected:
                        curr_odds *= item.average_odds
                    if len(ai_fallback_selected) >= 2 and curr_odds >= 2.10:
                        break
            if len(ai_fallback_selected) >= 2:
                total_odds = 1.0
                for b in ai_fallback_selected:
                    total_odds *= b.average_odds
                total_odds = round(total_odds, 2)
                ai_parlay = {
                    "title": "Экспресс ИИ-Консенсус",
                    "type": "ai",
                    "tag": "ВЫСШИЙ РЕЙТИНГ ИИ",
                    "total_odds": total_odds,
                    "items_count": len(ai_fallback_selected),
                    "potential_win_1000": round(1000 * total_odds),
                    "items": [build_parlay_item(b) for b in ai_fallback_selected]
                }
    except Exception as e:
        logger.warning(f"Не удалось собрать экспресс Тройного ИИ: {e}")

    # 2. Формируем "Надёжный экспресс" (2-3 события с наивысшей уверенностью и разумным кэфом)
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

    # 3. Формируем "Огненный экспресс" (3-4 события с коэффициентами выше)
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
        "ai_parlay": ai_parlay,
        "safe_parlay": safe_parlay,
        "hot_parlay": hot_parlay
    }
