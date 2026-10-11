import asyncio
import logging
import re
from datetime import datetime, timezone
import cloudscraper
from bs4 import BeautifulSoup
from thefuzz import fuzz
from unidecode import unidecode
from sqlalchemy.future import select

from .models import Source, Match, Prediction, SourceType, MatchStatus
from .database import AsyncSessionLocal

logger = logging.getLogger(__name__)

SITE_CONFIGS = [
    {
        "name": "Zulubet",
        "url": "http://www.zulubet.com/"
    }
]

def calculate_capper_weight(base_weight, roi, winrate, total_bets):
    return max(0.1, round(base_weight + (roi / 100.0), 2))

class BypassedBettingParser:
    def __init__(self, db_session):
        self.session = db_session
        self.scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "desktop": True})

    async def parse_zulubet(self):
        """Парсинг Zulubet (отличный источник без Cloudflare) за 3 дня"""
        logger.info("[Zulubet] Сбор данных...")
        extracted_data = []
        from datetime import datetime, timedelta
        
        # Парсим сегодня, завтра и послезавтра
        dates = [
            datetime.now(),
            datetime.now() + timedelta(days=1),
            datetime.now() + timedelta(days=2)
        ]
        
        for dt in dates:
            date_str = dt.strftime("%d-%m-%Y")
            url = f"http://www.zulubet.com/tips-{date_str}.html"
            logger.info(f"[Zulubet] Парсинг страницы: {url}")
            try:
                response = await asyncio.to_thread(self.scraper.get, url)
                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.content, "html.parser")
                rows = soup.find_all("tr")
                
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) >= 15:
                        try:
                            teams = cols[1].get_text(strip=True)
                            if " - " not in teams:
                                continue
                                
                            pred_code = cols[9].get_text(strip=True)
                            if pred_code == "1":
                                outcome = "Победа Хозяев (П1)"
                                odds = float(cols[12].get_text(strip=True))
                            elif pred_code == "2":
                                outcome = "Победа Гостей (П2)"
                                odds = float(cols[14].get_text(strip=True))
                            elif pred_code == "X":
                                outcome = "Ничья (Х)"
                                odds = float(cols[13].get_text(strip=True))
                            else:
                                continue

                            extracted_data.append({
                                "platform": "Zulubet",
                                "capper": "Zulubet AI",
                                "roi": 15.0,
                                "teams_text": teams,
                                "outcome": outcome,
                                "odds": odds,
                                "target_date": dt # Сохраняем дату матча
                            })
                        except Exception:
                            continue
            except Exception as e:
                logger.error(f"[Zulubet] Ошибка парсинга {date_str}: {e}")
                
        logger.info(f"[Zulubet] Найдено матчей за 3 дня: {len(extracted_data)}")
        return extracted_data

async def run_playwright_scraper():
    """Главная функция для оркестрации парсера"""
    logger.info("=== ЗАПУСК WEB ПАРСЕРА (Bypass Mode) ===")
    async with AsyncSessionLocal() as session:
        parser = BypassedBettingParser(session)
        
        all_predictions = await parser.parse_zulubet()

        # Обработка и сохранение в БД
        added_preds = 0
        
        for item in all_predictions:
            # Регистрируем источник
            c_stmt = select(Source).where(Source.name == item["capper"])
            capper_source = (await session.execute(c_stmt)).scalar_one_or_none()
            new_weight = calculate_capper_weight(3.0, item["roi"], 60.0, 1000)
            
            if not capper_source:
                capper_source = Source(
                    name=item["capper"],
                    url="http://www.zulubet.com/",
                    source_type=SourceType.prediction_site,
                    weight=new_weight,
                    is_active=True
                )
                session.add(capper_source)
            else:
                capper_source.weight = new_weight
            await session.flush()

            teams = item["teams_text"].split(" - ")
            if len(teams) == 2:
                home, away = teams[0].strip(), teams[1].strip()
            else:
                home, away = item["teams_text"], "Unknown"

            eng_home = unidecode(home.lower())
            eng_away = unidecode(away.lower())

            m_stmt = select(Match).where(Match.status == MatchStatus.upcoming)
            active_matches = (await session.execute(m_stmt)).scalars().all()
            
            best_match = None
            highest_score = 0
            for match in active_matches:
                db_home = unidecode(match.home_team.lower())
                db_away = unidecode(match.away_team.lower())
                
                score_h = fuzz.partial_ratio(eng_home, db_home)
                score_a = fuzz.partial_ratio(eng_away, db_away)
                avg = (score_h + score_a) / 2
                
                if avg > 70 and avg > highest_score:
                    highest_score = avg
                    best_match = match

            if not best_match:
                match_date = item.get("target_date", datetime.now(timezone.utc))
                best_match = Match(
                    sport_type="Football",
                    league="Zulubet Line",
                    home_team=home,
                    away_team=away,
                    match_date=match_date,
                    status=MatchStatus.upcoming
                )
                session.add(best_match)
                await session.flush()
                logger.info(f"[Web Scraper] Создан новый матч: {home} vs {away}")

            pred_stmt = select(Prediction).where(
                Prediction.match_id == best_match.id,
                Prediction.source_id == capper_source.id
            )
            existing_pred = (await session.execute(pred_stmt)).scalar_one_or_none()
            
            if not existing_pred:
                prediction = Prediction(
                    match_id=best_match.id,
                    source_id=capper_source.id,
                    predicted_outcome=item["outcome"],
                    odds=item["odds"],
                    confidence_score=100.0
                )
                session.add(prediction)
                added_preds += 1
                
        await session.commit()
        logger.info(f"Web парсер завершил работу. Интегрировано прогнозов: {added_preds}")
        return added_preds
