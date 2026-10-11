import asyncio
import logging
from datetime import datetime, timezone, timedelta
import requests
from bs4 import BeautifulSoup
from sqlalchemy.future import select

# Импортируем наши модели и подключение к БД
from app.database import AsyncSessionLocal
from app.models import Match, Prediction, Source, SourceType, MatchStatus

# Настраиваем красивое логирование в консоль
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def get_or_create_source(session) -> Source:
    """Проверяет наличие источника в БД, если нет - создает."""
    source_name = "MockScraper"
    stmt = select(Source).where(Source.name == source_name)
    result = await session.execute(stmt)
    source = result.scalar_one_or_none()
    
    if not source:
        source = Source(
            name=source_name,
            url="https://example-sports-site.com",
            source_type=SourceType.prediction_site,
            is_active=True
        )
        session.add(source)
        await session.commit()
        await session.refresh(source)
        logger.info(f"Создан новый источник в базе: '{source_name}'")
    return source

def parse_matches_data():
    """
    Здесь должна быть логика парсинга.
    Для примера показана структура использования requests и BeautifulSoup.
    
    ВАЖНО: Большинство реальных букмекерских сайтов используют защиту (Cloudflare/JS-рендеринг),
    поэтому обычный requests там выдаст 403 ошибку или капчу. 
    Если целевой сайт защищен, здесь нужно будет использовать Playwright.
    """
    logger.info("Запрашиваем данные с сайта...")
    
    try:
        # Пример того, как выглядел бы парсинг простого HTML-сайта
        # headers = {'User-Agent': 'Mozilla/5.0...'}
        # response = requests.get("https://example.com/today-matches", headers=headers, timeout=10)
        # soup = BeautifulSoup(response.text, 'html.parser')
        # ... поиск через soup.find_all(...)
        
        # Так как реальный парсинг зависит от конкретного сайта, 
        # возвращаем заглушку (mock-данные), имитирующую результат работы bs4
        now = datetime.now(timezone.utc)
        parsed_data = [
            {
                "sport": "Football",
                "league": "Champions League",
                "home": "Real Madrid",
                "away": "Bayern Munich",
                "time": now + timedelta(hours=3),
                "odds": 2.10,
                "prediction": "home_win"
            },
            {
                "sport": "Football",
                "league": "Premier League",
                "home": "Arsenal",
                "away": "Liverpool",
                "time": now + timedelta(hours=5),
                "odds": 3.40,
                "prediction": "draw"
            }
        ]
        logger.info(f"Успешно получены данные по {len(parsed_data)} матчам.")
        return parsed_data
        
    except Exception as e:
        logger.error(f"Ошибка при парсинге: {e}")
        return []

async def process_matches():
    async with AsyncSessionLocal() as session:
        # 1. Получаем источник
        source = await get_or_create_source(session)
        
        # 2. Получаем спарсенные данные
        matches_data = parse_matches_data()
        
        if not matches_data:
            logger.warning("Нет данных для добавления в базу.")
            return

        added_matches = 0
        added_predictions = 0

        # 3. Обрабатываем каждый матч
        for item in matches_data:
            # Проверяем, есть ли уже такой матч в БД (по командам и виду спорта)
            # В реальном проекте стоит проверять еще и дату (например, промежуток +/- 24 часа), 
            # чтобы не спутать с матчем этих же команд в следующем круге.
            stmt = select(Match).where(
                Match.home_team == item["home"],
                Match.away_team == item["away"],
                Match.sport_type == item["sport"]
            )
            result = await session.execute(stmt)
            match = result.scalar_one_or_none()

            if not match:
                match = Match(
                    sport_type=item["sport"],
                    league=item["league"],
                    home_team=item["home"],
                    away_team=item["away"],
                    match_date=item["time"],
                    status=MatchStatus.upcoming
                )
                session.add(match)
                # flush отправляет данные в БД и получает ID, но не коммитит транзакцию окончательно
                await session.flush() 
                added_matches += 1
                logger.info(f"➕ Добавлен новый матч: {item['home']} vs {item['away']}")
            else:
                logger.debug(f"Матч уже существует: {item['home']} vs {item['away']}")

            # Проверяем, есть ли уже прогноз от ЭТОГО источника на ЭТОТ матч
            pred_stmt = select(Prediction).where(
                Prediction.match_id == match.id,
                Prediction.source_id == source.id,
                Prediction.predicted_outcome == item["prediction"]
            )
            pred_result = await session.execute(pred_stmt)
            existing_pred = pred_result.scalar_one_or_none()

            if not existing_pred:
                prediction = Prediction(
                    match_id=match.id,
                    source_id=source.id,
                    predicted_outcome=item["prediction"],
                    odds=item["odds"],
                    confidence_score=80.0 # Базовое значение уверенности
                )
                session.add(prediction)
                added_predictions += 1
                logger.info(f"📈 Добавлен прогноз: {item['prediction']} (Кэф: {item['odds']}) на матч {item['home']}")
            else:
                logger.debug(f"Прогноз на этот матч от источника {source.name} уже существует.")
                
        # 4. Фиксируем изменения в базе
        await session.commit()
        
        logger.info("="*40)
        logger.info(f"ИТОГИ ПАРСИНГА:")
        logger.info(f"Новых матчей: {added_matches}")
        logger.info(f"Новых прогнозов: {added_predictions}")
        logger.info("="*40)

async def main():
    logger.info("=== Запуск скрипта агрегации ===")
    await process_matches()
    logger.info("=== Скрипт успешно завершил работу ===")

if __name__ == "__main__":
    # Для запуска асинхронной функции в обычном скрипте используем asyncio.run()
    asyncio.run(main())
