import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio

logger = logging.getLogger(__name__)

def start_scheduler():
    scheduler = AsyncIOScheduler()

    async def scheduled_scraping_job():
        logger.info("=== НАЧАЛО ЗАПЛАНИРОВАННОГО ПАРСИНГА И ОТПРАВКИ ОТЧЕТА ===")
        from app.capper_scraper import process_capper_predictions
        try:
            await process_capper_predictions()
        except Exception as e:
            logger.error(f"Ошибка во время парсинга по расписанию: {e}")

        # Фоновый прогрев кэша Робобет, Vitibet и Zulubet (Тройной ИИ)
        try:
            from app.robobet_scraper import get_robobet_cached
            await asyncio.to_thread(get_robobet_cached, True)
            logger.info("Кэш Тройного ИИ (Робобет, Vitibet, Zulubet) успешно прогрет по расписанию.")
        except Exception as e:
            logger.warning(f"Ошибка прогрева кэша Тройного ИИ: {e}")

        # Проверка и отправка срочных алертов по Тройному ИИ и супер-консенсусу
        try:
            from app.telegram_bot import check_and_notify_triple_ai_matches, check_and_notify_super_consensus
            from app.database import AsyncSessionLocal
            from app.consensus import calculate_daily_top_bets

            triple_sent = await check_and_notify_triple_ai_matches()
            if triple_sent > 0:
                logger.info(f"Отправлено {triple_sent} Telegram алертов по Тройному ИИ.")

            async with AsyncSessionLocal() as session:
                top_bets = await calculate_daily_top_bets(session, status_filter="upcoming")
                if top_bets:
                    super_sent = await check_and_notify_super_consensus(top_bets)
                    if super_sent > 0:
                        logger.info(f"Отправлено {super_sent} Telegram алертов по супер-консенсусу.")
        except Exception as e:
            logger.warning(f"Ошибка отправки Telegram алертов: {e}")

    # Утренний дайджест в 10:30 МСК
    async def morning_digest_job():
        from app.telegram_bot import notify_daily_morning_digest
        await notify_daily_morning_digest()

    scheduler.add_job(
        morning_digest_job,
        CronTrigger(hour=10, minute=30, timezone="Europe/Moscow")
    )

    # Вечерний итоговый отчет в 23:30 МСК
    async def evening_summary_job():
        from app.telegram_bot import notify_evening_summary
        await notify_evening_summary()

    scheduler.add_job(
        evening_summary_job,
        CronTrigger(hour=23, minute=30, timezone="Europe/Moscow")
    )

    # Добавляем задачу на 12:00 МСК
    scheduler.add_job(
        scheduled_scraping_job,
        CronTrigger(hour=12, minute=0, timezone="Europe/Moscow")
    )
    
    # Добавляем задачу на 17:00 МСК
    scheduler.add_job(
        scheduled_scraping_job,
        CronTrigger(hour=17, minute=0, timezone="Europe/Moscow")
    )
    
    # Запуск каждые 2 часа для постоянной актуальности
    scheduler.add_job(
        scheduled_scraping_job,
        'interval',
        hours=2
    )

    async def scheduled_settlement_job():
        logger.info("=== ПРОВЕРКА РЕЗУЛЬТАТОВ МАТЧЕЙ И РАСЧЕТ ВЫИГРЫШЕЙ ПО РАСПИСАНИЮ ===")
        from app.settlement_service import SettlementService
        from app.database import AsyncSessionLocal
        try:
            service = SettlementService()
            async with AsyncSessionLocal() as session:
                res = await service.sync_scores_and_settle(session)
                logger.info(f"Итоги проверки счетов: {res}")
        except Exception as e:
            logger.error(f"Ошибка проверки счетов по расписанию: {e}")

    # Запуск регулярной проверки результатов завершённых матчей каждые 10 минут
    scheduler.add_job(
        scheduled_settlement_job,
        'interval',
        minutes=10
    )

    scheduler.start()
    logger.info("Автоматическое расписание запущено! Парсинг каждые 2ч, проверка результатов каждые 10 мин, утренний/вечерний дайджесты.")

    # Немедленный запуск проверки результатов завершённых матчей при старте сервера
    asyncio.create_task(scheduled_settlement_job())

    # Запуск интерактивного Telegram Bot Polling в фоне
    try:
        from app.telegram_bot import start_telegram_polling
        asyncio.create_task(start_telegram_polling())
    except Exception as e:
        logger.warning(f"Не удалось запустить Telegram polling: {e}")

    # Проверка при старте приложения: если свежих прогнозов нет, запускаем сбор
    async def initial_check():
        await asyncio.sleep(5) # Даем серверу запуститься
        from app.database import AsyncSessionLocal
        from app.models import Prediction
        from sqlalchemy import select, func
        from datetime import datetime, timezone, timedelta

        try:
            async with AsyncSessionLocal() as session:
                recent_limit = datetime.now(timezone.utc) - timedelta(hours=3)
                stmt = select(func.count(Prediction.id)).where(Prediction.created_at >= recent_limit)
                count = (await session.execute(stmt)).scalar() or 0
                if count < 5:
                    logger.info("Свежих прогнозов за последние 3 часа мало или нет. Запускаем автоматический сбор при старте...")
                    await scheduled_scraping_job()
                else:
                    logger.info(f"В базе уже есть {count} свежих прогнозов за 3 часа. Немедленный сбор не требуется.")
        except Exception as e:
            logger.error(f"Ошибка проверки свежести данных при старте: {e}")

    asyncio.create_task(initial_check())
