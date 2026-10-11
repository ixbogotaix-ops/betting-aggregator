from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timezone, time

from . import models, schemas
from .database import get_db, engine, Base
from .ai_analyzer import analyze_top_bets_with_ai
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Betting Aggregator API")

# Настройка CORS для фронтенда на React/Vite
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    from .database import init_db
    await init_db()
    
    # Запуск фонового планировщика
    from .scheduler import start_scheduler
    start_scheduler()

# --- Эндпоинты для матчей ---

@app.post("/api/matches/", response_model=schemas.MatchResponse, status_code=201)
async def create_match(match: schemas.MatchCreate, db: AsyncSession = Depends(get_db)):
    db_match = models.Match(**match.model_dump())
    db.add(db_match)
    await db.commit()
    await db.refresh(db_match)
    return db_match

@app.get("/api/matches/", response_model=List[schemas.MatchResponse])
async def get_matches(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Match).offset(skip).limit(limit))
    matches = result.scalars().all()
    return matches

# --- Эндпоинты для прогнозов ---

@app.post("/api/predictions/", response_model=schemas.PredictionResponse, status_code=201)
async def create_prediction(prediction: schemas.PredictionCreate, db: AsyncSession = Depends(get_db)):
    match = await db.get(models.Match, prediction.match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
        
    source = await db.get(models.Source, prediction.source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    db_prediction = models.Prediction(**prediction.model_dump())
    db.add(db_prediction)
    await db.commit()
    await db.refresh(db_prediction)
    
    stmt = select(models.Prediction).options(selectinload(models.Prediction.source)).where(models.Prediction.id == db_prediction.id)
    result = await db.execute(stmt)
    return result.scalar_one()

@app.get("/api/predictions/today", response_model=List[schemas.MatchResponse])
async def get_today_predictions(
    sport_type: Optional[str] = Query(None, description="Фильтр по виду спорта"),
    date: Optional[str] = Query(None, description="Дата в формате YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db)
):
    from datetime import timezone, timedelta
    moscow_tz = timezone(timedelta(hours=3))
    now_moscow = datetime.now(moscow_tz).replace(tzinfo=None)
    
    if date:
        target_date = datetime.strptime(date, "%Y-%m-%d")
    else:
        target_date = now_moscow
        
    start_filter = datetime.combine(target_date.date(), time.min)
    end_of_day = datetime.combine(target_date.date(), time.max)
    
    # Если мы смотрим сегодняшний день, отсекаем матчи, которые уже начались
    if target_date.date() == now_moscow.date():
        start_filter = now_moscow

    stmt = select(models.Match).options(
        selectinload(models.Match.predictions).selectinload(models.Prediction.source)
    ).where(
        models.Match.match_date >= start_filter,
        models.Match.match_date <= end_of_day
    )

    if sport_type:
        stmt = stmt.where(models.Match.sport_type == sport_type)

    result = await db.execute(stmt)
    matches = result.scalars().all()
    
    return matches

from .consensus import calculate_daily_top_bets
from .schemas import TopBetResponse

def get_generic_sport(sport_name: str) -> str:
    s = sport_name.lower()
    if any(x in s for x in ["soccer", "série", "serie", "liga", "epl", "football", "premier", "championship", "uefa", "fifa", "pro league"]):
        return "Football"
    if any(x in s for x in ["nba", "basketball"]):
        return "Basketball"
    if any(x in s for x in ["nhl", "hockey", "khl", "liiga", "shl"]):
        return "Ice Hockey"
    if any(x in s for x in ["ncaaf", "nfl"]):
        return "American Football"
    if any(x in s for x in ["tennis", "atp", "wta"]):
        return "Tennis"
    if any(x in s for x in ["cricket", "t20"]):
        return "Cricket"
    return sport_name

@app.get("/api/predictions/top-daily", response_model=List[TopBetResponse])
async def get_top_daily_bets(
    sport_type: Optional[str] = Query(None, description="Фильтр по виду спорта"),
    date: Optional[str] = Query(None, description="Дата в формате YYYY-MM-DD"),
    status_filter: Optional[str] = Query(None, description="upcoming / finished"),
    db: AsyncSession = Depends(get_db)
):
    top_bets = await calculate_daily_top_bets(db, sport_type, date, status_filter)

    # Оставляем только ОДНУ лучшую ставку на каждый БАЗОВЫЙ вид спорта!
    filtered_bets = []
    seen_sports = set()
    
    # Сначала ищем матчи, которые ИИ отметил как is_bet_of_the_day
    for bet in top_bets:
        generic = get_generic_sport(bet.sport_type)
        if bet.is_bet_of_the_day and generic not in seen_sports:
            filtered_bets.append(bet)
            seen_sports.add(generic)
            
    # Если для какого-то спорта ИИ еще не выбрал ставку, берем просто самый уверенный матч
    for bet in top_bets:
        generic = get_generic_sport(bet.sport_type)
        if generic not in seen_sports:
            filtered_bets.append(bet)
            seen_sports.add(generic)
            
    return filtered_bets

# --- Дополнительные эндпоинты ---
@app.post("/api/sources/", response_model=schemas.SourceResponse, status_code=201)
async def create_source(source: schemas.SourceCreate, db: AsyncSession = Depends(get_db)):
    db_source = models.Source(**source.model_dump())
    db.add(db_source)
    await db.commit()
    await db.refresh(db_source)
    return db_source

@app.get("/api/sources/status", response_model=List[schemas.SourceStatusResponse])
async def get_sources_status(db: AsyncSession = Depends(get_db)):
    # Вытягиваем все источники
    result = await db.execute(select(models.Source))
    sources = result.scalars().all()
    
    status_list = []
    # Берем время 24 часа назад
    from datetime import datetime, timedelta
    yesterday = datetime.utcnow() - timedelta(hours=24)
    
    for s in sources:
        # Считаем количество прогнозов за последние 24 часа
        pred_stmt = select(models.Prediction).where(
            models.Prediction.source_id == s.id,
            models.Prediction.created_at >= yesterday
        ).order_by(models.Prediction.created_at.desc())
        
        preds_result = await db.execute(pred_stmt)
        preds = preds_result.scalars().all()
        
        count = len(preds)
        last_parsed = preds[0].created_at if count > 0 else None
        
        if not s.is_active:
            status_str = "Отключен"
        elif count > 0:
            status_str = "Онлайн (работает)"
        else:
            status_str = "Ожидание / Нет матчей"
            
        status_list.append(schemas.SourceStatusResponse(
            id=s.id,
            name=s.name,
            source_type=s.source_type.value if hasattr(s.source_type, 'value') else str(s.source_type),
            is_active=s.is_active,
            recent_predictions_count=count,
            last_parsed_at=last_parsed,
            status=status_str
        ))
        
    return status_list

_last_sync_time = 0
_sync_lock = False

@app.post("/api/sources/sync")
async def sync_sources(background_tasks: BackgroundTasks):
    global _last_sync_time, _sync_lock
    import time
    now = time.time()
    
    if _sync_lock or (now - _last_sync_time < 45):
        return {
            "status": "rate_limited", 
            "message": "Сбор данных уже выполняется или запускался недавно. Подождите немного."
        }
        
    _last_sync_time = now
    _sync_lock = True
    
    async def run_sync_with_unlock():
        global _sync_lock
        from .capper_scraper import process_capper_predictions
        try:
            await process_capper_predictions()
        finally:
            _sync_lock = False

    background_tasks.add_task(run_sync_with_unlock)
    return {"status": "started", "message": "Сбор прогнозов запущен в фоновом режиме"}

@app.get("/api/ai-analyze-bets")
async def get_ai_analysis(
    date: Optional[str] = Query(None, description="Дата в формате YYYY-MM-DD"),
    sport_type: Optional[str] = Query(None, description="Фильтр по виду спорта"),
    db: AsyncSession = Depends(get_db)
):
    """
    Отправляет топ-ставки в OpenRouter для текстового анализа.
    """
    # Используем существующую функцию получения топ ставок
    top_bets_raw = await calculate_daily_top_bets(db, sport_type, date)
    
    # Форматируем для ИИ
    top_bets_data = []
    for bet in top_bets_raw:
        top_bets_data.append({
            "match_name": bet.match_name,
            "recommended_outcome": bet.recommended_outcome,
            "average_odds": round(bet.average_odds, 2),
            "confidence_score": round(bet.confidence_score, 1)
        })
        
    ai_verdict = await analyze_top_bets_with_ai(top_bets_data)
    
    return {"ai_verdict": ai_verdict}

@app.get("/api/stats/overview", response_model=schemas.PerformanceStatsResponse)
async def get_stats_overview(db: AsyncSession = Depends(get_db)):
    """
    Возвращает статистику проходимости (Winrate, ROI) и рейтинг капперов/источников.
    """
    from .settlement_service import get_performance_stats
    stats = await get_performance_stats(db)
    return stats

@app.post("/api/results/sync")
async def sync_match_results(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    Запускает проверку завершённых счетов матчей и расчёт выигрышей/проигрышей.
    """
    from .settlement_service import SettlementService
    service = SettlementService()
    
    async def run_settlement():
        from .database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            await service.sync_scores_and_settle(session)
            
    background_tasks.add_task(run_settlement)
    return {"status": "started", "message": "Проверка результатов матчей запущена в фоновом режиме"}

@app.get("/api/results/recent", response_model=List[TopBetResponse])
async def get_recent_results(
    sport_type: Optional[str] = Query(None, description="Фильтр по виду спорта"),
    db: AsyncSession = Depends(get_db)
):
    """
    Возвращает недавние завершённые матчи с результатами ставок (Архив / Прошедшие).
    """
    finished_bets = await calculate_daily_top_bets(db, sport_type=sport_type, date_str=None, status_filter="finished")
    return finished_bets
