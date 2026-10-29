from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks, Header
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
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://45.84.222.76",
        "http://dthenbk.duckdns.org",
        "https://dthenbk.duckdns.org",
        "https://dthenbk.duckdns.org:8444",
        "http://dthenbk.duckdns.org:8444",
    ],
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

    # Фоновый прогрев кэша Робобета
    try:
        import asyncio
        from starlette.concurrency import run_in_threadpool
        from .robobet_scraper import get_robobet_cached
        asyncio.create_task(run_in_threadpool(get_robobet_cached))
    except Exception:
        pass

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
    result = await db.execute(
        select(models.Match)
        .options(selectinload(models.Match.predictions).selectinload(models.Prediction.source))
        .offset(skip)
        .limit(limit)
    )
    matches = result.scalars().all()

    from .logo_service import get_team_logo
    response_list = []
    for m in matches:
        m_dict = schemas.MatchResponse.model_validate(m).model_dump()
        m_dict["home_logo"] = get_team_logo(m.home_team, m.sport_type)
        m_dict["away_logo"] = get_team_logo(m.away_team, m.sport_type)
        response_list.append(schemas.MatchResponse(**m_dict))
    return response_list

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

_today_predictions_cache = {}
_today_predictions_cache_ttl = 30  # 30 seconds

@app.get("/api/predictions/today", response_model=List[schemas.MatchResponse])
async def get_today_predictions(
    sport_type: Optional[str] = Query(None, description="Фильтр по виду спорта"),
    date: Optional[str] = Query(None, description="Дата в формате YYYY-MM-DD"),
    upcoming_only: Optional[bool] = Query(False, description="Только не начавшиеся матчи"),
    db: AsyncSession = Depends(get_db)
):
    import time as _t
    cache_key = f"{sport_type}_{date}_{upcoming_only}"
    now_ts = _t.time()
    if cache_key in _today_predictions_cache:
        c_ts, c_res = _today_predictions_cache[cache_key]
        if now_ts - c_ts < _today_predictions_cache_ttl:
            return c_res

    from datetime import timezone, timedelta
    moscow_tz = timezone(timedelta(hours=3))
    now_moscow = datetime.now(moscow_tz).replace(tzinfo=None)
    
    if date:
        target_date = datetime.strptime(date, "%Y-%m-%d")
    else:
        target_date = now_moscow
        
    start_filter = datetime.combine(target_date.date(), time.min)
    end_of_day = datetime.combine(target_date.date(), time.max)
    
    if upcoming_only and target_date.date() == now_moscow.date():
        start_filter = now_moscow

    stmt = select(models.Match).options(
        selectinload(models.Match.predictions).selectinload(models.Prediction.source)
    ).where(
        models.Match.match_date >= start_filter,
        models.Match.match_date <= end_of_day
    ).order_by(models.Match.match_date.asc())

    result = await db.execute(stmt)
    matches = result.scalars().all()
    
    if sport_type and sport_type != 'All':
        from .consensus import get_generic_sport
        matches = [m for m in matches if get_generic_sport(m.sport_type) == sport_type or (m.sport_type and m.sport_type.lower() == sport_type.lower())]

    from .logo_service import get_team_logo, get_league_country, translate_team_name_to_ru
    resp_list = []
    for m in matches:
        c_info = get_league_country(m.league, m.sport_type)
        league_ru = c_info.get("league_ru") or m.league
        h_ru = translate_team_name_to_ru(m.home_team)
        a_ru = translate_team_name_to_ru(m.away_team)
        h_logo = get_team_logo(m.home_team, m.sport_type, fast_only=True)
        a_logo = get_team_logo(m.away_team, m.sport_type, fast_only=True)
        resp_list.append(schemas.MatchResponse(
            id=m.id,
            sport_type=m.sport_type,
            league=league_ru,
            home_team=h_ru,
            away_team=a_ru,
            match_date=m.match_date,
            status=m.status,
            final_score_home=m.final_score_home,
            final_score_away=m.final_score_away,
            predictions=[schemas.PredictionResponse.model_validate(p) for p in m.predictions] if m.predictions else [],
            home_logo=h_logo,
            away_logo=a_logo
        ))
    
    _today_predictions_cache[cache_key] = (now_ts, resp_list)
    return resp_list

from .consensus import calculate_daily_top_bets, get_generic_sport
from .schemas import TopBetResponse

@app.get("/api/predictions/top-daily", response_model=List[TopBetResponse])
async def get_top_daily_bets(
    sport_type: Optional[str] = Query(None, description="Фильтр по виду спорта"),
    date: Optional[str] = Query(None, description="Дата в формате YYYY-MM-DD"),
    status_filter: Optional[str] = Query(None, description="upcoming / finished"),
    only_bet_of_the_day: Optional[bool] = Query(False, description="Только 1 ставка дня на спорт"),
    db: AsyncSession = Depends(get_db)
):
    top_bets = await calculate_daily_top_bets(db, sport_type, date, status_filter)

    if only_bet_of_the_day:
        return [b for b in top_bets if b.is_bet_of_the_day]

    return top_bets

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
async def get_stats_overview(
    sport: Optional[str] = Query(None, description="Фильтр по виду спорта"),
    db: AsyncSession = Depends(get_db)
):
    """
    Возвращает статистику проходимости (Winrate, ROI) и рейтинг капперов/источников,
    в том числе с фильтрацией по конкретному виду спорта.
    """
    from .settlement_service import get_performance_stats
    stats = await get_performance_stats(db, sport_filter=sport)
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

@app.get("/api/archive/summary")
async def get_archive_summary(
    sport: Optional[str] = Query(None, description="Фильтр по виду спорта"),
    db: AsyncSession = Depends(get_db)
):
    """
    Возвращает календарную статистику архива ставок по дням (W/L/R, winrate, profit, ROI)
    и суммарную сводку за всё время.
    """
    from .settlement_service import get_archive_calendar_summary
    return await get_archive_calendar_summary(db, sport_type=sport)

@app.get("/api/stats/monthly-performance")
async def get_monthly_performance_endpoint(
    month: Optional[str] = Query(None, description="Месяц в формате YYYY-MM (например, 2026-10)"),
    mode: Optional[str] = Query("botd", description="Режим: botd (Ставка Дня) или robobet (Робобет)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Возвращает подневную статистику Ставок Дня (строго 1 ставка на каждый день месяца,
    например, на 17 октября ровно 17 ставок):
    - Список матчей по дням с исходами и статусом Прошло / Не прошло
    - Итоговый подсчет за выбранный месяц (в конце списка)
    - Подсчет за месяц на сегодняшний день (Month-To-Date)
    - Подсчет вообще за ВСЕ месяцы (All-Time)
    - Ссылки на предыдущие месяцы
    """
    from .monthly_stats_service import get_monthly_performance
    return await get_monthly_performance(db, month_str=month, mode=mode)

@app.get("/api/results/recent", response_model=List[TopBetResponse])
async def get_recent_results(
    sport_type: Optional[str] = Query(None, description="Фильтр по виду спорта"),
    date: Optional[str] = Query(None, description="Дата в формате YYYY-MM-DD"),
    category: Optional[str] = Query(None, description="Категория: all, botd, cappers, robobet"),
    outcome_filter: Optional[str] = Query(None, description="win, loss, refund"),
    db: AsyncSession = Depends(get_db)
):
    """
    Возвращает завершённые матчи с результатами ставок (Архив / Прошедшие).
    Поддерживает фильтрацию по виду спорта, конкретной дате, категории источника и исходу.
    """
    finished_bets = await calculate_daily_top_bets(db, sport_type=sport_type, date_str=date, status_filter="finished")

    # Если запрошены ставки Робобет или все ставки, дополняем завершёнными матчами Робобета
    if category in [None, "all", "robobet"] and (not sport_type or sport_type in ["All", "Football"]):
        try:
            from .robobet_scraper import get_robobet_cached
            r_data = get_robobet_cached(force_refresh=False)
            r_matches = r_data.get("matches", [])
            r_finished = [m for m in r_matches if m.get("is_finished") and m.get("score")]
            
            # Проверяем фильтрацию по дате для Робобета (по Московскому времени)
            from datetime import timezone, timedelta
            moscow_tz = timezone(timedelta(hours=3))
            now_moscow = datetime.now(moscow_tz).replace(tzinfo=None)
            now_str = now_moscow.strftime("%Y-%m-%d")
            for rm in r_finished:
                if date and date != "ALL" and date != now_str:
                    continue
                # Избегаем дубликатов по именам команд
                already_in = any(
                    (b.home_team and b.home_team.lower() in rm["team1"].lower()) or
                    (b.match_name and rm["team1"].lower() in b.match_name.lower())
                    for b in finished_bets
                )
                if not already_in:
                    finished_bets.append(TopBetResponse(
                        match_id=abs(hash(rm["id"])) % 10000000,
                        match_name=f"{rm['team1']} — {rm['team2']}",
                        match_date=datetime.now(),
                        league=rm.get("country", "Футбол"),
                        sport_type="Football",
                        recommended_outcome=rm.get("recommendation", "П1"),
                        average_odds=rm.get("rec_odd", 1.8),
                        confidence_score=rm.get("rec_prob", 65),
                        supporting_sources=["Робобет ИИ (Диксон-Коулз/Пуассон)"],
                        is_bet_of_the_day=False,
                        ai_insight=f"Математическая модель: П1 {rm.get('prob_1')}% | X {rm.get('prob_x')}% | П2 {rm.get('prob_2')}%. Ожидаемая выгода +EV: {rm.get('ev')}",
                        value_badge=f"+EV: {int(rm.get('ev', 0)*100)}%" if rm.get('is_value') else None,
                        ev_percent=rm.get('ev', 0.0),
                        home_team=rm.get("team1"),
                        away_team=rm.get("team2"),
                        home_logo=rm.get("home_logo"),
                        away_logo=rm.get("away_logo"),
                        country_name=rm.get("country"),
                        country_flag_url=rm.get("country_flag_url"),
                        country_flag_emoji=rm.get("country_emoji"),
                        final_score_home=rm.get("home_score"),
                        final_score_away=rm.get("away_score"),
                        status="finished",
                        bet_result=rm.get("result_status"),
                        all_predictions=[]
                    ))
        except Exception as e:
            logger.warning(f"Ошибка загрузки завершенных матчей Робобета: {e}")

    # Фильтр по категории
    if category == "botd":
        finished_bets = [b for b in finished_bets if b.is_bet_of_the_day]
    elif category == "cappers":
        finished_bets = [b for b in finished_bets if not any("Робобет" in s for s in b.supporting_sources)]
    elif category == "robobet":
        finished_bets = [b for b in finished_bets if any("Робобет" in s for s in b.supporting_sources)]

    # Фильтр по исходу (win, loss, refund)
    if outcome_filter and outcome_filter != "all":
        finished_bets = [b for b in finished_bets if b.bet_result == outcome_filter]

    return finished_bets


@app.get("/api/parlays/daily", response_model=schemas.DailyParlaysResponse)
async def get_daily_parlays_endpoint(db: AsyncSession = Depends(get_db)):
    """
    Генерирует два готовых экспресса дня:
    1. Надёжный (Safe) — 2-3 матча с наивысшей проходимостью
    2. Огненный (Hot) — 3-4 матча с высоким общим кэфом
    """
    from .parlay_service import generate_daily_parlays
    return await generate_daily_parlays(db)

@app.post("/api/telegram/send-parlay")
async def send_parlay_to_telegram(
    parlay_type: str = Query("ai", description="ai, safe или hot"),
    db: AsyncSession = Depends(get_db)
):
    """
    Отправляет выбранный экспресс в Telegram-канал.
    """
    from .parlay_service import generate_daily_parlays
    from .telegram_bot import send_parlay_alert
    
    parlays = await generate_daily_parlays(db)
    if parlay_type == "ai":
        selected = parlays.get("ai_parlay") or parlays.get("safe_parlay")
    elif parlay_type == "safe":
        selected = parlays.get("safe_parlay")
    else:
        selected = parlays.get("hot_parlay")
    
    if not selected:
        raise HTTPException(status_code=404, detail="Экспресс данного типа не сформирован (недостаточно матчей)")
        
    success = send_parlay_alert(selected)
    if not success:
        return {"status": "error", "message": "Не удалось отправить сообщение (проверьте токен бота и chat_id)"}
    return {"status": "ok", "message": f"Экспресс ({parlay_type}) успешно отправлен в Telegram!"}

@app.post("/api/telegram/send-super-alerts")
async def trigger_super_consensus_alerts(db: AsyncSession = Depends(get_db)):
    """
    Сканирует матчи и отправляет срочные алерты по супер-консенсусу (4+ источника / 85%+ уверенность).
    """
    from .telegram_bot import check_and_notify_super_consensus
    top_bets = await calculate_daily_top_bets(db, status_filter="upcoming")
    if not top_bets:
        top_bets = await calculate_daily_top_bets(db)
        
    sent_count = await check_and_notify_super_consensus(top_bets)
    return {"status": "ok", "sent_alerts_count": sent_count}

@app.post("/api/telegram/send-yesterday-report")
async def trigger_telegram_yesterday_report(
    target_date: Optional[str] = Query(None, description="Дата в формате YYYY-MM-DD (по умолчанию вчера)"),
    chat_id: Optional[str] = Query(None, description="Chat ID получателя (по умолчанию канал/чат из .env)")
):
    """
    Отправляет в Telegram утренний отчёт по результатам вчерашних ставок и сводную статистику за текущий месяц.
    """
    from .telegram_bot import send_yesterday_settlement_and_monthly_stats_report
    success = await send_yesterday_settlement_and_monthly_stats_report(chat_id=chat_id, target_date=target_date)
    return {"status": "ok" if success else "error", "sent": success, "target_date": target_date}

# --- АВТОРИЗАЦИЯ ЧЕРЕЗ GOOGLE ---

@app.post("/api/auth/google", response_model=schemas.AuthResponse)
async def login_with_google(req: schemas.GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    """
    Аутентификация через Google Identity Services (One Tap или Google Sign-In Button).
    Верифицирует токен с серверами Google и создает/обновляет аккаунт пользователя.
    """
    from .auth_service import verify_google_id_token, authenticate_or_register_google_user, create_access_token
    
    if req.demo:
        # Тестовый демо-вход (пока пользователь настраивает свой Client ID в Google Cloud)
        google_info = {
            "google_id": "demo_google_id_9999",
            "email": "demo.user@sports-ai.com",
            "name": "Аналитик AI (Демо)",
            "picture": "https://api.dicebear.com/7.x/bottts/svg?seed=SportsAI",
            "email_verified": True
        }
    else:
        if not req.credential:
            raise HTTPException(status_code=400, detail="Отсутствует Google токен авторизации (credential)")
            
        google_info = verify_google_id_token(req.credential)
        if not google_info:
            raise HTTPException(status_code=401, detail="Недействительный или просроченный токен Google")
            
    user = await authenticate_or_register_google_user(db, google_info)
    token = create_access_token(user.id, user.email, user.role)
    
    return schemas.AuthResponse(
        access_token=token,
        token_type="bearer",
        user=schemas.UserResponse.model_validate(user)
    )

@app.post("/api/auth/telegram", response_model=schemas.AuthResponse)
async def login_with_telegram(req: schemas.TelegramAuthRequest, db: AsyncSession = Depends(get_db)):
    """
    Аутентификация через Telegram Mini App (TMA).
    Проверяет HMAC-подпись initData от Telegram и авторизует пользователя.
    """
    from .auth_service import verify_telegram_webapp_data, authenticate_or_register_telegram_user, create_access_token
    import os
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    tg_user = None
    
    if req.init_data and bot_token:
        tg_user = verify_telegram_webapp_data(req.init_data, bot_token)
        
    if not tg_user and req.user:
        tg_user = req.user
        
    if not tg_user:
        raise HTTPException(status_code=401, detail="Недействительные данные авторизации Telegram")
        
    user = await authenticate_or_register_telegram_user(db, tg_user)
    token = create_access_token(user.id, user.email, user.role)
    
    return schemas.AuthResponse(
        access_token=token,
        token_type="bearer",
        user=schemas.UserResponse.model_validate(user)
    )

@app.get("/api/auth/me", response_model=schemas.UserResponse)
async def get_current_user_profile(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Возвращает профиль текущего авторизованного пользователя.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Требуется авторизация")
        
    token = authorization.replace("Bearer ", "").strip()
    from .auth_service import verify_access_token
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Токен авторизации недействителен или истек")
        
    user_id = int(payload["sub"])
    stmt = select(models.User).where(models.User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
        
    return schemas.UserResponse.model_validate(user)

@app.post("/api/auth/logout")
async def logout():
    return {"status": "ok", "message": "Успешный выход из системы"}

# --- ЭНДПОИНТЫ РОБОБЕТ (МАТЕМАТИЧЕСКАЯ ИИ-МОДЕЛЬ) ---

@app.get("/api/robobet")
async def get_robobet_predictions(force: bool = False):
    """
    Возвращает список математических прогнозов Робобет (Диксон-Коулз/Пуассон),
    распределение вероятностей (П1, X, П2) и вычисленный 'Матч Дня от Робобет'.
    Выполняется в threadpool, чтобы не блокировать асинхронный event loop!
    """
    from starlette.concurrency import run_in_threadpool
    from .robobet_scraper import get_robobet_cached
    return await run_in_threadpool(get_robobet_cached, force_refresh=force)

@app.post("/api/robobet/refresh")
async def refresh_robobet_predictions():
    """Принудительно обновляет базу матчей Робобета."""
    from starlette.concurrency import run_in_threadpool
    from .robobet_scraper import get_robobet_cached
    return await run_in_threadpool(get_robobet_cached, force_refresh=True)


