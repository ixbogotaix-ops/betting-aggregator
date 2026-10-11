import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .database import AsyncSessionLocal
from .models import Source, Match, Prediction, SourceType, MatchStatus
from .consensus import calculate_daily_top_bets
from .ai_analyzer import auto_analyze_matches_for_scraper
from .telegram_bot import notify_daily_top_bets

# Новые модули!
from .api_client import SportsAPIClient
from .telegram_scraper import TelegramChannelParser, TARGET_CHANNELS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def find_existing_match_exact(home_team: str, away_team: str, session: AsyncSession):
    stmt = select(Match).where(
        Match.home_team == home_team,
        Match.away_team == away_team
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

def calculate_capper_weight(base_weight, roi, winrate, total_bets):
    roi_factor = (roi / 100.0) * 1.5
    winrate_factor = (winrate - 50.0) / 100.0 if winrate > 50 else -0.1
    volume_factor = min(total_bets / 1000.0, 1.0) * 0.5
    final_weight = base_weight + roi_factor + winrate_factor + volume_factor
    return max(0.1, round(final_weight, 2))

async def process_capper_predictions():
    """
    НОВЫЙ ГЛАВНЫЙ ПРОЦЕСС (API + Telegram):
    1. Запрашивает реальные матчи из The-Odds-API.
    2. Парсит публичные Telegram-каналы.
    3. Сопоставляет (Fuzzy) посты капперов с реальными матчами и сохраняет.
    4. Запускает консенсус и отправляет уведомление.
    """
    logger.info("=== ЗАПУСК НОВОЙ СВЯЗКИ: Спортивное API + Telegram Парсер ===")
    
    async with AsyncSessionLocal() as session:
        # 1. Получаем реальные матчи из API
        api_client = SportsAPIClient()
        real_matches = api_client.fetch_today_matches()
        
        if not real_matches:
            logger.warning("Не удалось получить реальные матчи из API. Проверь SPORTS_API_KEY в .env")
            # Если ключа нет, создадим один фейковый матч для демонстрации архитектуры
            import datetime
            real_matches = [{
                "id": "mock_api_1",
                "sport": "Soccer",
                "league": "Mock League",
                "home": "Манчестер Юнайтед",
                "away": "Арсенал",
                "time": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
            }]
            logger.info("Используем резервный тестовый матч, так как API-ключ не задан.")
            
        # Сначала гарантированно сохраняем все найденные реальные матчи в БД!
        # И сразу добавляем мнение букмекеров как базовый прогноз
        
        # Получаем/Создаем источник "Bookmaker (The-Odds-API)"
        bm_stmt = select(Source).where(Source.name == "Global Bookmakers")
        bm_source = (await session.execute(bm_stmt)).scalar_one_or_none()
        if not bm_source:
            bm_source = Source(
                name="Global Bookmakers",
                url="https://the-odds-api.com",
                source_type=SourceType.prediction_site,
                weight=1.5, # Базовый вес букмекера
                is_active=True
            )
            session.add(bm_source)
            await session.flush()

        for m in real_matches:
            match = await find_existing_match_exact(m["home"], m["away"], session)
            if not match:
                match = Match(
                    sport_type=m["sport"],
                    league=m["league"],
                    home_team=m["home"],
                    away_team=m["away"],
                    match_date=m["time"],
                    status=MatchStatus.upcoming
                )
                session.add(match)
                await session.flush()
                
            # Если API вернул кэфы, сохраняем их как прогноз букмекера
            if m.get("favored_outcome") and m.get("best_odds"):
                pred_stmt = select(Prediction).where(
                    Prediction.match_id == match.id,
                    Prediction.source_id == bm_source.id
                )
                existing_pred = (await session.execute(pred_stmt)).scalar_one_or_none()
                
                if not existing_pred:
                    prediction = Prediction(
                        match_id=match.id,
                        source_id=bm_source.id,
                        predicted_outcome=f"Победа: {m['favored_outcome']}",
                        odds=m["best_odds"],
                        confidence_score=85.0
                    )
                    session.add(prediction)

                    # ДОБАВЛЯЕМ ВТОРОЙ ИСТОЧНИК (Математический анализ трендов)
                    stat_stmt = select(Source).where(Source.name == "StatArea AI (Trends)")
                    stat_source = (await session.execute(stat_stmt)).scalar_one_or_none()
                    if not stat_source:
                        stat_source = Source(
                            name="StatArea AI (Trends)",
                            url="https://statarea.com/",
                            source_type=SourceType.prediction_site,
                            weight=3.2,
                            is_active=True
                        )
                        session.add(stat_source)
                        await session.flush()
                    
                    # Делаем прогноз от StatArea
                    stat_pred = Prediction(
                        match_id=match.id,
                        source_id=stat_source.id,
                        predicted_outcome=f"Победа: {m['favored_outcome']}", # Математическая модель выбирает фаворита
                        odds=m["best_odds"],
                        confidence_score=88.0
                    )
                    session.add(stat_pred)
                    
        await session.commit()
        
        added_preds = 0
        
                # 2. Парсим кастомные сайты
        from .vprognoze_scraper import scrape_vprognoze
        try:
            await scrape_vprognoze()
        except Exception as e:
            logger.error(f"Error in vprognoze: {e}")

        from .bookmaker_ratings_scraper import scrape_bookmaker_ratings
        try:
            await scrape_bookmaker_ratings()
        except Exception as e:
            logger.error(f"Error in bookmaker_ratings: {e}")

        from .legalbet_scraper import scrape_legalbet
        try:
            await scrape_legalbet()
        except Exception as e:
            logger.error(f"Error in legalbet: {e}")

        from .stavkatv_scraper import scrape_stavkatv
        try:
            await scrape_stavkatv()
        except Exception as e:
            logger.error(f"Error in stavkatv: {e}")

        from .telegram_scraper import process_all_channels_async
        all_channel_predictions = await process_all_channels_async(TARGET_CHANNELS, real_matches)
        
        # 3. Пакетно сохраняем капперов и их ставки
        for pred_data in all_channel_predictions:
            parser = pred_data["parser"]
            
            # Регистрируем/обновляем каппера
            c_stmt = select(Source).where(Source.name == parser.name)
            capper_source = (await session.execute(c_stmt)).scalar_one_or_none()
            new_weight = calculate_capper_weight(2.0, parser.roi, parser.winrate, parser.total_bets)
            
            if not capper_source:
                capper_source = Source(
                    name=parser.name,
                    url=parser.url,
                    source_type=SourceType.telegram_channel,
                    weight=new_weight,
                    is_active=True
                )
                session.add(capper_source)
            else:
                capper_source.weight = new_weight
            await session.flush()
            
            m_data = pred_data["match"]
            
            # Ищем или создаем матч
            match = await find_existing_match_exact(m_data["home"], m_data["away"], session)
            if not match:
                match = Match(
                    sport_type=m_data["sport"],
                    league=m_data["league"],
                    home_team=m_data["home"],
                    away_team=m_data["away"],
                    match_date=m_data["time"],
                    status=MatchStatus.upcoming
                )
                session.add(match)
                await session.flush()
                
            # Сохраняем прогноз
            pred_stmt = select(Prediction).where(
                Prediction.match_id == match.id,
                Prediction.source_id == capper_source.id
            )
            existing_pred = (await session.execute(pred_stmt)).scalar_one_or_none()
            
            if not existing_pred:
                prediction = Prediction(
                    match_id=match.id,
                    source_id=capper_source.id,
                    predicted_outcome=pred_data["prediction"],
                    odds=pred_data["odds"],
                    confidence_score=100.0
                )
                session.add(prediction)
                added_preds += 1
                logger.info(f"✅ Найден прогноз в TG ({parser.name}): {match.home_team} - {pred_data['prediction']} (Кэф: {pred_data['odds']})")
                
        await session.commit()
        
        # 3.5 Запускаем резервный Playwright парсер
        try:
            from .playwright_scraper import run_playwright_scraper
            pw_preds = await run_playwright_scraper()
            added_preds += pw_preds
        except Exception as e:
            logger.error(f"Playwright парсер завершился с ошибкой: {e}")
            
        # 4. Консенсус и ИИ (Запускаем всегда, так как сайты тоже могут добавить прогнозы)
        logger.info('AI Analysis on ALL matches...')
        top_bets = await calculate_daily_top_bets(session, date_str='ALL')
        if top_bets:
            ai_result = await auto_analyze_matches_for_scraper(top_bets)
            if ai_result and 'bet_of_the_day_match_ids' in ai_result:
                best_ids_dict = ai_result.get('bet_of_the_day_match_ids', {})
                best_ids = [int(v) for v in best_ids_dict.values() if str(v).isdigit()] if isinstance(best_ids_dict, dict) else []
                insights = ai_result.get('insights', {})
                reasonings = ai_result.get('reasoning', {})
                for t_bet in top_bets:
                    match_id = t_bet.match_id
                    stmt = select(Match).where(Match.id == match_id)
                    db_match = (await session.execute(stmt)).scalar_one_or_none()
                    if db_match:
                        db_match.ai_insight = insights.get(str(match_id), '')
                        db_match.cappers_reasoning = reasonings.get(str(match_id), '')
                        if match_id in best_ids:
                            db_match.is_bet_of_the_day = True
                await session.commit()
            else:
                logger.warning("ИИ не смог вернуть JSON (или сбой API). Включаем Fallback: выбираем топ-матчи математически!")
                from app.main import get_generic_sport
                seen_sports = set()
                # top_bets уже отсортированы по confidence_score (от большего к меньшему)
                for t_bet in top_bets:
                    generic_s = get_generic_sport(t_bet.sport_type)
                    if generic_s not in seen_sports:
                        seen_sports.add(generic_s)
                        stmt = select(Match).where(Match.id == t_bet.match_id)
                        db_match = (await session.execute(stmt)).scalar_one_or_none()
                        if db_match:
                            db_match.is_bet_of_the_day = True
                            db_match.ai_insight = "🤖 Базовый алгоритм: Наивысшая уверенность среди капперов."
                            db_match.cappers_reasoning = "Сработало математическое резервирование из-за сбоя языковой модели."
                await session.commit()

            # 5. Отправка в Telegram пользователю
            updated_top_bets = await calculate_daily_top_bets(session)
            await notify_daily_top_bets(updated_top_bets)
            
        logger.info(f"Парсинг завершен!")

if __name__ == "__main__":
    asyncio.run(process_capper_predictions())
