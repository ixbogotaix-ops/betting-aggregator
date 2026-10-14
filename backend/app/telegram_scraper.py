import re
import random
import logging
import asyncio
import aiohttp
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from thefuzz import fuzz
from unidecode import unidecode

logger = logging.getLogger(__name__)

TARGET_CHANNELS = [
    # 📌 1. Официальные медиа и топ-верификаторы (Высший вес авторитета)
    {"name": "legalbet", "url": "https://t.me/s/legalbet", "roi": 12.0, "winrate": 60.0, "total_bets": 1000},
    {"name": "bookmaker_ratings", "url": "https://t.me/s/bookmaker_ratings", "roi": 10.5, "winrate": 58.0, "total_bets": 800},
    {"name": "vprognoze", "url": "https://t.me/s/vprognoze", "roi": 9.0, "winrate": 56.0, "total_bets": 1500},
    {"name": "intelbet", "url": "https://t.me/s/intelbet", "roi": 11.0, "winrate": 59.0, "total_bets": 700},
    {"name": "stavka_tv", "url": "https://t.me/s/stavka_tv", "roi": 13.5, "winrate": 62.0, "total_bets": 900},
    {"name": "bet_itors", "url": "https://t.me/s/bet_itors", "roi": 10.0, "winrate": 55.0, "total_bets": 500},
    {"name": "capper_control", "url": "https://t.me/s/capper_control", "roi": 10.0, "winrate": 55.0, "total_bets": 500},
    {"name": "odds_portal_ru", "url": "https://t.me/s/odds_portal_ru", "roi": 10.0, "winrate": 55.0, "total_bets": 500},
    {"name": "metaratings_ru", "url": "https://t.me/s/metaratings_ru", "roi": 10.0, "winrate": 55.0, "total_bets": 500},
    {"name": "championat_com", "url": "https://t.me/s/championat_com", "roi": 10.0, "winrate": 55.0, "total_bets": 500},

    # ⚽ 2. Футбол: Топ-лиги, кубки и блоги аналитиков
    {"name": "football_hub_ru", "url": "https://t.me/s/football_hub_ru", "roi": 8.0, "winrate": 55.0, "total_bets": 400},
    {"name": "capper_football", "url": "https://t.me/s/capper_football", "roi": 5.0, "winrate": 53.0, "total_bets": 300},
    {"name": "goal_forecast", "url": "https://t.me/s/goal_forecast", "roi": 6.0, "winrate": 54.0, "total_bets": 200},
    {"name": "euro_football_chat", "url": "https://t.me/s/euro_football_chat", "roi": 4.5, "winrate": 52.0, "total_bets": 250},
    {"name": "russian_premier_league", "url": "https://t.me/s/russian_premier_league", "roi": 10.0, "winrate": 55.0, "total_bets": 500},
    {"name": "champions_league_bets", "url": "https://t.me/s/champions_league_bets", "roi": 10.0, "winrate": 55.0, "total_bets": 500},
    {"name": "tactical_board", "url": "https://t.me/s/tactical_board", "roi": 10.0, "winrate": 55.0, "total_bets": 500},
    {"name": "corner_cards_bets", "url": "https://t.me/s/corner_cards_bets", "roi": 10.0, "winrate": 55.0, "total_bets": 500},
    {"name": "xG_football_analytics", "url": "https://t.me/s/xG_football_analytics", "roi": 10.0, "winrate": 55.0, "total_bets": 500},
    {"name": "foot_analytics_pro", "url": "https://t.me/s/foot_analytics_pro", "roi": 10.0, "winrate": 55.0, "total_bets": 500},

    # 🏒 3. Хоккей (КХЛ, НХЛ)
    {"name": "ice_hockey_bets", "url": "https://t.me/s/ice_hockey_bets", "roi": 9.5, "winrate": 57.0, "total_bets": 400},
    {"name": "khl_analytics_pro", "url": "https://t.me/s/khl_analytics_pro", "roi": 10.0, "winrate": 55.0, "total_bets": 500},
    {"name": "nhl_expert_tips", "url": "https://t.me/s/nhl_expert_tips", "roi": 10.0, "winrate": 55.0, "total_bets": 500},
    {"name": "puck_and_goal", "url": "https://t.me/s/puck_and_goal", "roi": 10.0, "winrate": 55.0, "total_bets": 500},

    # 🎾 4. Теннис (ATP, WTA, Турниры Большого Шлема)
    {"name": "tennis_expert_pro", "url": "https://t.me/s/tennis_expert_pro", "roi": 14.0, "winrate": 63.0, "total_bets": 600},
    {"name": "court_side_bets", "url": "https://t.me/s/court_side_bets", "roi": 10.0, "winrate": 55.0, "total_bets": 500},
    {"name": "tennis_stat_lab", "url": "https://t.me/s/tennis_stat_lab", "roi": 10.0, "winrate": 55.0, "total_bets": 500},

    # 🏀 5. Баскетбол и другие виды спорта (NBA, Единая лига ВТБ)
    {"name": "basket_analytics", "url": "https://t.me/s/basket_analytics", "roi": 10.0, "winrate": 58.0, "total_bets": 500},
    {"name": "nba_night_picks", "url": "https://t.me/s/nba_night_picks", "roi": 10.0, "winrate": 55.0, "total_bets": 500},
    {"name": "volleyball_expert_bets", "url": "https://t.me/s/volleyball_expert_bets", "roi": 10.0, "winrate": 55.0, "total_bets": 500},
    {"name": "mma_ufc_predictions", "url": "https://t.me/s/mma_ufc_predictions", "roi": 10.0, "winrate": 55.0, "total_bets": 500},

    # 📊 6. Профессиональные беттинг-лаборатории (Валуйные ставки)
    {"name": "smart_betting_lab", "url": "https://t.me/s/smart_betting_lab", "roi": 18.0, "winrate": 65.0, "total_bets": 850},
    {"name": "value_bets_channel", "url": "https://t.me/s/value_bets_channel", "roi": 20.5, "winrate": 68.0, "total_bets": 1200},
    {"name": "roi_tracker_bot", "url": "https://t.me/s/roi_tracker_bot", "roi": 15.0, "winrate": 61.0, "total_bets": 700},
    {"name": "betting_strategy_ru", "url": "https://t.me/s/betting_strategy_ru", "roi": 11.5, "winrate": 59.0, "total_bets": 500},
    {"name": "math_betting_club", "url": "https://t.me/s/math_betting_club", "roi": 10.0, "winrate": 55.0, "total_bets": 500},
    {"name": "pro_capper_union", "url": "https://t.me/s/pro_capper_union", "roi": 10.0, "winrate": 55.0, "total_bets": 500},
    {"name": "sure_bets_monitor", "url": "https://t.me/s/sure_bets_monitor", "roi": 10.0, "winrate": 55.0, "total_bets": 500}
]

class TelegramChannelParser:
    def __init__(self, channel_data):
        self.name = channel_data["name"]
        self.url = channel_data["url"]
        self.roi = channel_data["roi"]
        self.winrate = channel_data["winrate"]
        self.total_bets = channel_data["total_bets"]
        
    async def fetch_recent_posts(self, session: aiohttp.ClientSession):
        """Асинхронный парсинг публичных постов из Telegram-канала с защитой от FloodWait"""
        try:
            retry_count = 0
            html = ""
            while retry_count < 3:
                async with session.get(self.url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}) as response:
                    if response.status == 429: # FloodWait protection
                        retry_after = int(response.headers.get("Retry-After", 30))
                        logger.warning(f"Telegram Limit (429) для {self.name}. Ожидание {retry_after} сек...")
                        await asyncio.sleep(retry_after)
                        retry_count += 1
                        continue
                    
                    if response.status != 200:
                        logger.warning(f"Канал {self.name} недоступен (Код: {response.status})")
                        return []
                        
                    html = await response.text()
                    break
            
            if not html: return []

            soup = BeautifulSoup(html, "html.parser")
            posts = soup.find_all("div", class_="tgme_widget_message")
            
            today = datetime.now(timezone.utc).date()
            extracted_texts = []
            
            for post in posts:
                # Фильтрация постов (берем за последние 3 дня)
                time_tag = post.find("time")
                if time_tag and time_tag.has_attr("datetime"):
                    post_time = datetime.fromisoformat(time_tag["datetime"]).date()
                    if (today - post_time).days > 3:
                        continue # Игнорируем слишком старые посты
                
                text_div = post.find("div", class_="tgme_widget_message_text")
                if text_div:
                    text = text_div.get_text(separator="\n", strip=True)
                    extracted_texts.append(text)
                
            return extracted_texts
        except Exception as e:
            logger.error(f"Ошибка парсинга Telegram {self.name}: {e}")
            return []

    def extract_prediction(self, text, active_matches):
        """Умное извлечение ставки и Fuzzy Matching"""
        odds_match = re.search(r'\b([1-3]\.\d{2})\b', text)
        odds = float(odds_match.group(1)) if odds_match else None
        
        outcome = None
        text_clean = text.strip()

        # 1. Приоритет: Обе забьют (ОЗ)
        if re.search(r'\b(оз\s*[-—:]?\s*нет|обе\s*забьют\s*[-—:]?\s*нет|не\s*забьют)\b', text_clean, re.I):
            outcome = "Обе забьют — Нет (ОЗ: Нет)"
        elif re.search(r'\b(оз\s*[-—:]?\s*да|обе\s*забьют\s*[-—:]?\s*да|обе\s*забьют|\bоз\b)\b', text_clean, re.I):
            outcome = "Обе забьют — Да (ОЗ: Да)"

        # 2. Приоритет: Тоталы (Любые: ТБ 1.5, ТБ 2, ТБ 2.5, ТБ 3, ТМ 2.5, ТМ 3.5 и т.д.)
        elif re.search(r'(?:тб|тотал\s*больше|over)\s*\(?(\d+[\.,]?\d*)\)?', text_clean, re.I):
            m = re.search(r'(?:тб|тотал\s*больше|over)\s*\(?(\d+[\.,]?\d*)\)?', text_clean, re.I)
            v = m.group(1).replace(',', '.')
            outcome = f"Тотал Больше {v} (ТБ {v})"
        elif re.search(r'(?:тм|тотал\s*меньше|under)\s*\(?(\d+[\.,]?\d*)\)?', text_clean, re.I):
            m = re.search(r'(?:тм|тотал\s*меньше|under)\s*\(?(\d+[\.,]?\d*)\)?', text_clean, re.I)
            v = m.group(1).replace(',', '.')
            outcome = f"Тотал Меньше {v} (ТМ {v})"

        # 3. Приоритет: Двойной шанс (Максимальная надежность: 1X, X2, 12)
        elif re.search(r'\b(1x|1х)\b', text_clean, re.I) or re.search(r'\b1\s*не\s*проиграет\b', text_clean, re.I):
            outcome = "1X (Хозяева не проиграют)"
        elif re.search(r'\b(x2|х2)\b', text_clean, re.I) or re.search(r'\b2\s*не\s*проиграет\b', text_clean, re.I):
            outcome = "X2 (Гости не проиграют)"
        elif re.search(r'\b(12)\b', text_clean, re.I) or "победа 1 или 2" in text_clean.lower():
            outcome = "Победа 1 или 2 (12)"

        # 4. Приоритет: Форы
        elif re.search(r'(?:фора\s*1|ф1)\s*\(?([\+\-]?\d+[\.,]?\d*)\)?', text_clean, re.I):
            m = re.search(r'(?:фора\s*1|ф1)\s*\(?([\+\-]?\d+[\.,]?\d*)\)?', text_clean, re.I)
            outcome = f"Фора 1 ({m.group(1).replace(',', '.')})"
        elif re.search(r'(?:фора\s*2|ф2)\s*\(?([\+\-]?\d+[\.,]?\d*)\)?', text_clean, re.I):
            m = re.search(r'(?:фора\s*2|ф2)\s*\(?([\+\-]?\d+[\.,]?\d*)\)?', text_clean, re.I)
            outcome = f"Фора 2 ({m.group(1).replace(',', '.')})"

        # 5. И только затем: Ничья, П1, П2 (с четкими границами слов)
        elif re.search(r'\b(ничья|draw|мир)\b', text_clean, re.I):
            outcome = "Ничья (Х)"
        elif re.search(r'\b(п1|победа\s*1|победа\s*хозяев|победа\s*первой)\b', text_clean, re.I):
            outcome = "Победа Хозяев (П1)"
        elif re.search(r'\b(п2|победа\s*2|победа\s*гостей|победа\s*второй)\b', text_clean, re.I):
            outcome = "Победа Гостей (П2)"

        best_match = None
        highest_score = 0
        
        for match in active_matches:
            # Транслитерируем названия команд из API (на всякий случай) и русский текст поста в латиницу
            eng_home = unidecode(match["home"].lower())
            eng_away = unidecode(match["away"].lower())
            eng_text = unidecode(text.lower())
            
            score_home = fuzz.partial_ratio(eng_home, eng_text)
            score_away = fuzz.partial_ratio(eng_away, eng_text)
            
            # Если каппер упомянул хотя бы одну команду очень точно ИЛИ обе средне
            if (score_home >= 85 or score_away >= 85) or (score_home >= 65 and score_away >= 65):
                match_score = max(score_home, score_away) + (score_home + score_away) / 2
                if match_score > highest_score:
                    highest_score = match_score
                    best_match = match
                
        if best_match and outcome and odds:
            return {
                "match": best_match,
                "prediction": outcome,
                "odds": odds
            }
        return None

async def process_single_channel(parser, session, real_matches):
    """Обрабатывает один канал асинхронно"""
    posts = await parser.fetch_recent_posts(session)
    valid_preds = []
    for text in posts:
        pred_data = parser.extract_prediction(text, real_matches)
        if pred_data:
            pred_data["parser"] = parser
            valid_preds.append(pred_data)
    return valid_preds

async def process_all_channels_async(channels_data, real_matches):
    """Пакетная обработка каналов через asyncio.gather с защитой от блокировок"""
    all_predictions = []
    batch_size = 8  # Группы по 8 каналов
    
    # timeout для aiohttp чтобы не зависало
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for i in range(0, len(channels_data), batch_size):
            batch = channels_data[i:i + batch_size]
            logger.info(f"Запуск пачки каналов ({i+1}-{i+len(batch)} из {len(channels_data)})...")
            
            tasks = []
            for c_data in batch:
                parser = TelegramChannelParser(c_data)
                tasks.append(process_single_channel(parser, session, real_matches))
                
            # Запускаем пачку параллельно
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for res in results:
                if isinstance(res, Exception):
                    logger.error(f"Сбой в параллельной задаче: {res}")
                elif isinstance(res, list):
                    all_predictions.extend(res)
            
            # Задержка между пачками для безопасности (FloodWait защита)
            if i + batch_size < len(channels_data):
                delay = random.uniform(2.5, 4.5)
                logger.info(f"Ожидание {delay:.1f} сек. перед следующей пачкой...")
                await asyncio.sleep(delay)
                
    return all_predictions
