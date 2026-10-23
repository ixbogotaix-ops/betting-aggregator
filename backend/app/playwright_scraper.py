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

                            # Очищаем префикс текущей минуты (например, "-52'1X" -> "1X", "-38'1" -> "1")
                            pred_code_raw = cols[9].get_text(strip=True) if len(cols) > 9 else ""
                            pred_code = re.sub(r'^[-\d\']+', '', pred_code_raw).strip()

                            o1_str = cols[12].get_text(strip=True).replace(',', '.') if len(cols) > 12 else "1.0"
                            ox_str = cols[13].get_text(strip=True).replace(',', '.') if len(cols) > 13 else "1.0"
                            o2_str = cols[14].get_text(strip=True).replace(',', '.') if len(cols) > 14 else "1.0"

                            try:
                                o1 = float(o1_str)
                            except ValueError:
                                o1 = 1.0
                            try:
                                ox = float(ox_str)
                            except ValueError:
                                ox = 1.0
                            try:
                                o2 = float(o2_str)
                            except ValueError:
                                o2 = 1.0

                            if pred_code == "1":
                                outcome = "Победа Хозяев (П1)"
                                odds = o1
                            elif pred_code == "2":
                                outcome = "Победа Гостей (П2)"
                                odds = o2
                            elif pred_code == "X":
                                outcome = "Ничья (Х)"
                                odds = ox
                            elif pred_code in ["1X", "X1"]:
                                outcome = "1X (Хозяева не проиграют)"
                                odds = round(1.0 / (1.0 / o1 + 1.0 / ox), 2) if (o1 > 1.0 and ox > 1.0) else 1.25
                            elif pred_code in ["X2", "2X"]:
                                outcome = "X2 (Гости не проиграют)"
                                odds = round(1.0 / (1.0 / o2 + 1.0 / ox), 2) if (o2 > 1.0 and ox > 1.0) else 1.25
                            else:
                                continue

                            if odds < 1.05 or odds > 30.0:
                                continue

                            extracted_data.append({
                                "platform": "Zulubet",
                                "capper": "Zulubet AI",
                                "roi": 15.0,
                                "teams_text": teams,
                                "outcome": outcome,
                                "odds": odds,
                                "target_date": dt
                            })
                        except Exception:
                            continue
            except Exception as e:
                logger.error(f"[Zulubet] Ошибка парсинга {date_str}: {e}")
                
        logger.info(f"[Zulubet] Найдено матчей за 3 дня: {len(extracted_data)}")
        return extracted_data

def clean_team_name_for_match(name: str) -> str:
    s = unidecode(name).lower()
    for noise in ['fc', 'fk', 'tc', 'sc', 'cf', 'bc', 'jk', 'фк', 'бк']:
        s = re.sub(rf'\b{noise}\b', '', s)
    return ' '.join(s.split())

async def run_playwright_scraper():
    """Главная функция для оркестрации парсера Zulubet"""
    logger.info("=== ЗАПУСК WEB ПАРСЕРА (Zulubet AI Matcher) ===")
    async with AsyncSessionLocal() as session:
        parser = BypassedBettingParser(session)
        
        all_predictions = await parser.parse_zulubet()
        added_preds = 0
        
        # Получаем все актуальные футбольные матчи
        m_stmt = select(Match).where(Match.status == MatchStatus.upcoming)
        active_matches = (await session.execute(m_stmt)).scalars().all()

        for item in all_predictions:
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
                continue

            eng_home = clean_team_name_for_match(home)
            eng_away = clean_team_name_for_match(away)
            target_date = item.get("target_date")

            best_match = None
            highest_score = 0

            for match in active_matches:
                # 1. Проверка вида спорта: Zulubet парсит ИСКЛЮЧИТЕЛЬНО футбол!
                m_sport = str(match.sport_type or "").lower()
                if m_sport and not any(s in m_sport for s in ["foot", "socc", "европ", "uefa", "лига", "league", "fifa"]):
                    continue

                # 2. Проверка даты: матч не может отстоять от спарсенной даты Zulubet более чем на 36 часов!
                if match.match_date and target_date:
                    try:
                        m_dt = match.match_date.replace(tzinfo=None) if hasattr(match.match_date, 'replace') else match.match_date
                        t_dt = target_date.replace(tzinfo=None) if hasattr(target_date, 'replace') else target_date
                        diff_hours = abs((m_dt - t_dt).total_seconds()) / 3600.0
                        if diff_hours > 36.0:
                            continue
                    except Exception:
                        pass

                db_home = clean_team_name_for_match(match.home_team)
                db_away = clean_team_name_for_match(match.away_team)

                # 3. Строгое сопоставление по токенам: ОБЕ команды обязаны совпасть с порогом >= 70!
                score_h = fuzz.token_set_ratio(eng_home, db_home)
                score_a = fuzz.token_set_ratio(eng_away, db_away)

                if score_h >= 70 and score_a >= 70:
                    avg = (score_h + score_a) / 2.0
                    if avg >= 78 and avg > highest_score:
                        highest_score = avg
                        best_match = match

            if not best_match:
                # Не создаем безымянные мусорные матчи 'Zulubet Line' без турниров и логотипов!
                continue

            pred_stmt = select(Prediction).where(
                Prediction.match_id == best_match.id,
                Prediction.source_id == capper_source.id
            )
            existing_pred = (await session.execute(pred_stmt)).scalar_one_or_none()
            
            if existing_pred:
                # Обновляем старый прогноз свежими актуальными данными с сайта
                existing_pred.predicted_outcome = item["outcome"]
                existing_pred.odds = item["odds"]
                existing_pred.created_at = datetime.utcnow()
            else:
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
        logger.info(f"Zulubet парсер завершил работу. Интегрировано/обновлено прогнозов: {added_preds}")
        return added_preds
