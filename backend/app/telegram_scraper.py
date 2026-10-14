import re
import random
import logging
import asyncio
import aiohttp
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from thefuzz import fuzz
from unidecode import unidecode

logger = logging.getLogger(__name__)

def detect_sport(text: str = "", league: str = "", teams: str = "") -> str:
    s = f"{text} {league} {teams}".lower()
    if any(k in s for k in ["хоккей", "кхл", "нхл", "вхл", "мхл", "hockey", "nhl", "khl", "шайб", "буллит", "овертайм", "ска-", "нефтяник"]):
        return "Hockey"
    if any(k in s for k in ["баскетбол", "nba", "нба", "евролига", "втб", "basketball", "euroleague"]):
        return "Basketball"
    if any(k in s for k in ["теннис", "atp", "wta", "itf", "tennis", "сет", "гейм", "паолини", "картал", "джокович", "алькарас"]):
        return "Tennis"
    if any(k in s for k in ["mma", "ufc", "мма", "юфс", "бокс", "boxing", "бой"]):
        return "MMA"
    if any(k in s for k in ["esport", "киберспорт", "cs:go", "cs2", "dota", "valorant"]):
        return "Esports"
    return "Football"

def extract_teams_from_post(text: str):
    """Извлекает пару команд из текста поста каппера, если матча нет в активных API-матчах"""
    # Удаляем кавычки и лишние символы
    text_clean = re.sub(r'[«»\"\'\(\)]', ' ', text)
    # Разбиваем по строкам и предложениям (точка, точка с запятой, перенос строки)
    segments = [s.strip() for s in re.split(r'[\n\.;]+', text_clean) if s.strip()]
    stop_words = ["ставка", "прогноз", "кэф", "коэф", "кф", "рублей", "канал", "подписк", "https", "t.me", "http", "лесенка", "марафон", "банк", "vip", "время", "мск", "коэффициент", "форы", "тотал", "победа", "турнир", "кубок", "чемпионат", "премьер-лига"]
    separators = [r'\s+[—–]\s+', r'\s+vs\.?\s+', r'\s+против\s+', r'\s+-\s+']
    
    for seg in segments:
        seg_clean = re.sub(r'^[⚽🏒🏀🎾🥊🎮🔥💰🏆🎯🚀💎📌\s]+', '', seg).strip()
        if any(w in seg_clean.lower() for w in stop_words):
            continue
        if len(seg_clean) < 4 or len(seg_clean) > 70:
            continue
            
        for sep_pattern in separators:
            parts = re.split(sep_pattern, seg_clean, flags=re.IGNORECASE)
            if len(parts) == 2:
                t1 = re.sub(r'[^\w\s\.-]', '', parts[0]).strip()
                t2 = re.sub(r'[^\w\s\.-]', '', parts[1]).strip()
                t2 = re.sub(r'\s+\d{1,2}[:.]\d{2}.*$', '', t2).strip()
                t2 = re.sub(r'\s+кф.*$', '', t2, flags=re.I).strip()
                
                if 2 <= len(t1) <= 30 and 2 <= len(t2) <= 30:
                    banned_words = ["приложен", "сезон", "рекорд", "бонус", "скачат", "подпиш", "канал", "ссылк", "видео", "фото", "смотреть", "трансляци", "эфир", "конкурс", "розыгрыш", "фрибет", "рублей", "руб", "пост", "сайт"]
                    if any(b in t1.lower() for b in banned_words) or any(b in t2.lower() for b in banned_words):
                        continue
                    if not re.search(r'\b(тб|тм|фора|итб|итм|оз|1x|x2)\b', t1.lower()) and not re.search(r'\b(тб|тм|фора|итб|итм|оз|1x|x2)\b', t2.lower()):
                        return (t1, t2)
    return None

TARGET_CHANNELS = [
    # 📌 1. Официальные медиа и топ-верификаторы (Высший вес авторитета)
    {"name": "stavka_tv", "url": "https://t.me/s/stavka_tv", "roi": 13.5, "winrate": 62.0, "total_bets": 1200},
    {"name": "bookmaker_ratings", "url": "https://t.me/s/bookmaker_ratings", "roi": 10.5, "winrate": 58.0, "total_bets": 800},
    {"name": "kushvsporte", "url": "https://t.me/s/kushvsporte", "roi": 12.0, "winrate": 60.0, "total_bets": 950},
    {"name": "metaratings", "url": "https://t.me/s/metaratings", "roi": 10.0, "winrate": 56.0, "total_bets": 750},
    {"name": "sportsru", "url": "https://t.me/s/sportsru", "roi": 9.5, "winrate": 55.0, "total_bets": 1000},
    {"name": "championat", "url": "https://t.me/s/championat", "roi": 9.0, "winrate": 54.0, "total_bets": 1100},
    {"name": "matchpremier", "url": "https://t.me/s/matchpremier", "roi": 11.0, "winrate": 57.0, "total_bets": 600},

    # 📊 2. Ведущие аналитические линии букмекеров
    {"name": "ligastavok", "url": "https://t.me/s/ligastavok", "roi": 10.0, "winrate": 55.0, "total_bets": 500},
    {"name": "fonbet_official", "url": "https://t.me/s/fonbet_official", "roi": 11.5, "winrate": 58.0, "total_bets": 800},
    {"name": "betboom_ru", "url": "https://t.me/s/betboom_ru", "roi": 10.5, "winrate": 56.0, "total_bets": 700},
    {"name": "olimpbet_official", "url": "https://t.me/s/olimpbet_official", "roi": 9.0, "winrate": 54.0, "total_bets": 500},

    # 🎯 3. Лаборатории аналитики
    {"name": "smart_betting_lab", "url": "https://t.me/s/smart_betting_lab", "roi": 18.0, "winrate": 65.0, "total_bets": 850},
    {"name": "value_bets_channel", "url": "https://t.me/s/value_bets_channel", "roi": 20.5, "winrate": 68.0, "total_bets": 1200},
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
        """Умное извлечение ставки с сохранением точных композитных исходов, тоталов, двойных шансов и аргументов"""
        text_clean = text.strip()
        
        # 0. Извлечение коэффициента
        odds = None
        odds_match = re.search(r'(?:кэф|коэф|кф|odds|коэффициент|к\.)\s*[:=\-@]?\s*([1-9]\d*(?:[\.,]\d{1,2})?)', text_clean, re.I)
        if odds_match:
            try:
                odds = float(odds_match.group(1).replace(',', '.'))
            except Exception:
                pass
        if not odds:
            fallback_odds = re.search(r'\b([1-4][\.,]\d{2})\b', text_clean)
            if fallback_odds:
                try:
                    odds = float(fallback_odds.group(1).replace(',', '.'))
                except Exception:
                    pass

        outcome = None

        # Проверяем, есть ли явная строка "Ставка: ..." или "Прогноз: ..."
        explicit_bet = None
        for line in text_clean.split('\n'):
            line_s = line.strip()
            m_exp = re.match(r'^(?:ставка|прогноз|мой выбор|выбор|исход|ординар|играем|берём|беру|пик)\s*[:—\-]\s*(.+)', line_s, re.I)
            if m_exp:
                raw_bet = m_exp.group(1).strip()
                # Удаляем приписку с кэфом на конце, например: (кф 1.85)
                raw_bet = re.sub(r'\(?\s*(?:кэф|кф|коэф|odds)?\s*[:=\-]?\s*[1-9]\d*[\.,]\d+\s*\)?$', '', raw_bet, flags=re.I).strip()
                explicit_bet = raw_bet
                break

        scan_target = explicit_bet if explicit_bet else text_clean

        # 1. Приоритет: Комбинированные ставки (1X + ТМ, П1 + ТМ, ОЗ + ТБ и т.д.)
        m_combo_und = re.search(r'(1[xх]|x2|х2|п1|п2|победа\s*[12])\s*(?:\+|и|and|&)\s*(?:тм|тотал\s*меньше)\s*\(?(\d+[\.,]?\d*)\)?', scan_target, re.I)
        m_combo_ovr = re.search(r'(1[xх]|x2|х2|п1|п2|победа\s*[12])\s*(?:\+|и|and|&)\s*(?:тб|тотал\s*больше)\s*\(?(\d+[\.,]?\d*)\)?', scan_target, re.I)
        m_combo_btts = re.search(r'(1[xх]|x2|х2|п1|п2)\s*(?:\+|и|and|&)\s*(?:оз|обе\s*забьют)', scan_target, re.I)
        m_btts_tb = re.search(r'(?:оз|обе\s*забьют)\s*(?:\+|и|and|&)\s*(?:тб|тотал\s*больше)\s*\(?(\d+[\.,]?\d*)\)?', scan_target, re.I)
        m_btts_tm = re.search(r'(?:оз|обе\s*забьют)\s*(?:\+|и|and|&)\s*(?:тм|тотал\s*меньше)\s*\(?(\d+[\.,]?\d*)\)?', scan_target, re.I)

        if m_combo_und:
            side = m_combo_und.group(1).upper().replace('Х', 'X')
            v = m_combo_und.group(2).replace(',', '.')
            outcome = f"{side} + ТМ {v}"
        elif m_combo_ovr:
            side = m_combo_ovr.group(1).upper().replace('Х', 'X')
            v = m_combo_ovr.group(2).replace(',', '.')
            outcome = f"{side} + ТБ {v}"
        elif m_combo_btts:
            side = m_combo_btts.group(1).upper().replace('Х', 'X')
            outcome = f"{side} + ОЗ: Да"
        elif m_btts_tb:
            v = m_btts_tb.group(1).replace(',', '.')
            outcome = f"ОЗ + ТБ {v}"
        elif m_btts_tm:
            v = m_btts_tm.group(1).replace(',', '.')
            outcome = f"ОЗ + ТМ {v}"

        # 2. Индивидуальные тоталы (ИТБ / ИТМ)
        elif re.search(r'(?:итб\s*1|ит1б|индивидуальный\s*тотал\s*1\s*больше|индивидуальный\s*тотал\s*первой\s*больше)\s*\(?(\d+[\.,]?\d*)\)?', scan_target, re.I):
            m = re.search(r'(?:итб\s*1|ит1б|индивидуальный\s*тотал\s*1\s*больше|индивидуальный\s*тотал\s*первой\s*больше)\s*\(?(\d+[\.,]?\d*)\)?', scan_target, re.I)
            outcome = f"ИТБ1 ({m.group(1).replace(',', '.')})"
        elif re.search(r'(?:итм\s*1|ит1м|индивидуальный\s*тотал\s*1\s*меньше|индивидуальный\s*тотал\s*первой\s*меньше)\s*\(?(\d+[\.,]?\d*)\)?', scan_target, re.I):
            m = re.search(r'(?:итм\s*1|ит1м|индивидуальный\s*тотал\s*1\s*меньше|индивидуальный\s*тотал\s*первой\s*меньше)\s*\(?(\d+[\.,]?\d*)\)?', scan_target, re.I)
            outcome = f"ИТМ1 ({m.group(1).replace(',', '.')})"
        elif re.search(r'(?:итб\s*2|ит2б|индивидуальный\s*тотал\s*2\s*больше|индивидуальный\s*тотал\s*второй\s*больше)\s*\(?(\d+[\.,]?\d*)\)?', scan_target, re.I):
            m = re.search(r'(?:итб\s*2|ит2б|индивидуальный\s*тотал\s*2\s*больше|индивидуальный\s*тотал\s*второй\s*больше)\s*\(?(\d+[\.,]?\d*)\)?', scan_target, re.I)
            outcome = f"ИТБ2 ({m.group(1).replace(',', '.')})"
        elif re.search(r'(?:итм\s*2|ит2м|индивидуальный\s*тотал\s*2\s*меньше|индивидуальный\s*тотал\s*второй\s*меньше)\s*\(?(\d+[\.,]?\d*)\)?', scan_target, re.I):
            m = re.search(r'(?:итм\s*2|ит2м|индивидуальный\s*тотал\s*2\s*меньше|индивидуальный\s*тотал\s*второй\s*меньше)\s*\(?(\d+[\.,]?\d*)\)?', scan_target, re.I)
            outcome = f"ИТМ2 ({m.group(1).replace(',', '.')})"

        # 3. Приоритет: Двойной шанс (Максимальная надежность: 1X, X2, 12)
        elif re.search(r'\b(1x|1х)\b', scan_target, re.I) or re.search(r'\b1\s*не\s*проиграет\b', scan_target, re.I):
            outcome = "1X (Хозяева не проиграют)"
        elif re.search(r'\b(x2|х2)\b', scan_target, re.I) or re.search(r'\b2\s*не\s*проиграет\b', scan_target, re.I):
            outcome = "X2 (Гости не проиграют)"
        elif re.search(r'\b(12)\b', scan_target, re.I) or "победа 1 или 2" in scan_target.lower():
            outcome = "Победа 1 или 2 (12)"

        # 4. Приоритет: Тоталы (Любые: ТБ 1.5, ТБ 2, ТБ 2.5, ТМ 2.5, ТМ 3.5 и т.д.)
        elif re.search(r'(?:тб|тотал(?:\s*голов|\s*шайб|\s*очков|\s*раундов)?\s*[:—\-]?\s*больше|over)\s*\(?(\d+[\.,]?\d*)\)?', scan_target, re.I):
            m = re.search(r'(?:тб|тотал(?:\s*голов|\s*шайб|\s*очков|\s*раундов)?\s*[:—\-]?\s*больше|over)\s*\(?(\d+[\.,]?\d*)\)?', scan_target, re.I)
            v = m.group(1).replace(',', '.')
            outcome = f"Тотал Больше {v} (ТБ {v})"
        elif re.search(r'(?:тм|тотал(?:\s*голов|\s*шайб|\s*очков|\s*раундов)?\s*[:—\-]?\s*меньше|under)\s*\(?(\d+[\.,]?\d*)\)?', scan_target, re.I):
            m = re.search(r'(?:тм|тотал(?:\s*голов|\s*шайб|\s*очков|\s*раундов)?\s*[:—\-]?\s*меньше|under)\s*\(?(\d+[\.,]?\d*)\)?', scan_target, re.I)
            v = m.group(1).replace(',', '.')
            outcome = f"Тотал Меньше {v} (ТМ {v})"

        # 5. Приоритет: Обе забьют (ОЗ)
        elif re.search(r'(?:обе(?:\s*команды)?\s*забьют\s*[:—\-]?\s*нет|оз\s*[-—:]?\s*нет|не\s*забьют)', scan_target, re.I):
            outcome = "Обе забьют — Нет (ОЗ: Нет)"
        elif re.search(r'(?:обе(?:\s*команды)?\s*забьют(?:\s*[:—\-]?\s*да)?|оз\s*[-—:]?\s*да|\bоз\b)', scan_target, re.I):
            outcome = "Обе забьют — Да (ОЗ: Да)"

        # 6. Приоритет: Форы
        elif re.search(r'(?:победа\s*с\s*учетом\s*форы|фора)\s*[:—\-]?\s*([^\(\d\.\n]+)\s*\(?([\+\-]?\d+[\.,]?\d*)\)?', scan_target, re.I):
            m = re.search(r'(?:победа\s*с\s*учетом\s*форы|фора)\s*[:—\-]?\s*([^\(\d\.\n]+)\s*\(?([\+\-]?\d+[\.,]?\d*)\)?', scan_target, re.I)
            t_name = m.group(1).strip()
            v = m.group(2).replace(',', '.')
            outcome = f"Фора {t_name} ({v})"
        elif re.search(r'(?:фора\s*1|ф1)\s*\(?([\+\-]?\d+[\.,]?\d*)\)?', scan_target, re.I):
            m = re.search(r'(?:фора\s*1|ф1)\s*\(?([\+\-]?\d+[\.,]?\d*)\)?', scan_target, re.I)
            outcome = f"Фора 1 ({m.group(1).replace(',', '.')})"
        elif re.search(r'(?:фора\s*2|ф2)\s*\(?([\+\-]?\d+[\.,]?\d*)\)?', scan_target, re.I):
            m = re.search(r'(?:фора\s*2|ф2)\s*\(?([\+\-]?\d+[\.,]?\d*)\)?', scan_target, re.I)
            outcome = f"Фора 2 ({m.group(1).replace(',', '.')})"

        # 7. Ничья, П1, П2, Победа в матче
        elif re.search(r'(?:победа\s*в\s*матче|чистая\s*победа)\s*[:—\-]?\s*([^\.\n]+)', scan_target, re.I):
            m = re.search(r'(?:победа\s*в\s*матче|чистая\s*победа)\s*[:—\-]?\s*([^\.\n]+)', scan_target, re.I)
            outcome = f"Победа {m.group(1).strip()}"
        elif re.search(r'\b(ничья|draw|мир)\b', scan_target, re.I):
            outcome = "Ничья (Х)"
        elif re.search(r'\b(п1|победа\s*1|победа\s*хозяев|победа\s*первой)\b', scan_target, re.I):
            outcome = "Победа Хозяев (П1)"
        elif re.search(r'\b(п2|победа\s*2|победа\s*гостей|победа\s*второй)\b', scan_target, re.I):
            outcome = "Победа Гостей (П2)"

        # 8. Если была явная строка ставки, но не подошла ни под один шаблон — берем как есть
        elif explicit_bet and len(explicit_bet) >= 2:
            outcome = explicit_bet.capitalize()

        best_match = None
        highest_score = 0
        
        for match in active_matches:
            # Транслитерируем названия команд из API и русский текст поста в латиницу
            eng_home = unidecode(match["home"].lower())
            eng_away = unidecode(match["away"].lower())
            eng_text = unidecode(text_clean.lower())
            
            score_home = fuzz.partial_ratio(eng_home, eng_text)
            score_away = fuzz.partial_ratio(eng_away, eng_text)
            
            # Если каппер упомянул хотя бы одну команду очень точно ИЛИ обе средне
            if (score_home >= 85 or score_away >= 85) or (score_home >= 65 and score_away >= 65):
                match_score = max(score_home, score_away) + (score_home + score_away) / 2
                if match_score > highest_score:
                    highest_score = match_score
                    best_match = match
                
        if not best_match and outcome:
            team_pair = extract_teams_from_post(text_clean)
            if team_pair:
                t1, t2 = team_pair
                sp = detect_sport(text_clean, teams=f"{t1} {t2}")
                best_match = {
                    "id": f"tg_{abs(hash(t1 + t2))}",
                    "sport": sp,
                    "league": "Линия Telegram",
                    "home": t1,
                    "away": t2,
                    "time": datetime.now(timezone.utc) + timedelta(hours=3)
                }
                active_matches.append(best_match)

        if best_match and outcome:
            return {
                "match": best_match,
                "prediction": outcome,
                "odds": odds if odds else 1.80,
                "reasoning": text_clean[:700]
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
