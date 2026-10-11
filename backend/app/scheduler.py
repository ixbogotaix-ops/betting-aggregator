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

    # Добавляем задачу на 12:00
    scheduler.add_job(
        scheduled_scraping_job,
        CronTrigger(hour=12, minute=0)
    )
    
    # Добавляем задачу на 17:00
    scheduler.add_job(
        scheduled_scraping_job,
        CronTrigger(hour=17, minute=0)
    )
    
    # Запуск каждые 2 часа для постоянной актуальности
    scheduler.add_job(
        scheduled_scraping_job,
        'interval',
        hours=2
    )

    scheduler.start()
    logger.info("Автоматическое расписание запущено! Каждые 2 часа + 12:00 и 17:00.")

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
