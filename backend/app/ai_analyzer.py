import os
import requests
import json
import logging

logger = logging.getLogger(__name__)

async def analyze_top_bets_with_ai(top_bets_data: list) -> str:
    """
    Отправляет топ-ставки в OpenRouter для ИИ-анализа и выбора наилучших.
    """
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        return "⚠️ ВНИМАНИЕ: Для работы ИИ-анализатора добавьте OPENROUTER_API_KEY в файл .env в папке backend. Пока ключ не добавлен, ИИ отключен."

    if not top_bets_data:
        return "Нет ставок для анализа."

    # Формируем промпт для ИИ
    prompt = "Ты профессиональный спортивный аналитик. Твоя задача — проанализировать список лучших консенсус-ставок, собранных с различных платформ прогнозистов, и выбрать 1-2 самых железобетонных варианта. Объясни свой выбор коротко и по делу.\n\nСписок ставок:\n"
    
    for idx, bet in enumerate(top_bets_data, 1):
        prompt += f"{idx}. {bet.get('match_name')} | Ставка: {bet.get('recommended_outcome')} | Коэффициент: {bet.get('average_odds')} | Уверенность алгоритма: {bet.get('confidence_score')}/100\n"

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "model": "openrouter/free", # Автоматический выбор лучшей доступной бесплатной модели
                "messages": [
                    {
                        "role": "system", 
                        "content": "Ты крутой ИИ-каппер и спортивный аналитик. Твоя задача писать ярко, сочно, использовать много эмодзи (🔥, 💰, ⚽, 🏆, 🎯, 🚀, 💎) и структурировать текст красиво. Используй списки, выделяй важное жирным. Пиши так, чтобы пользователю хотелось сразу поставить ставку! Отвечай на русском языке."
                    },
                    {"role": "user", "content": prompt}
                ]
            }),
            timeout=20
        )
        if response.status_code != 200:
            logger.error(f"Ошибка OpenRouter: {response.status_code} - {response.text}")
            return f"❌ Ошибка при обращении к ИИ (Код {response.status_code}). Подробности: {response.text[:100]}"
            
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Ошибка вызова OpenRouter: {e}")
        return f"❌ Сбой сети или ошибка ИИ: {e}"

async def auto_analyze_matches_for_scraper(top_bets_data: list) -> dict:
    """
    Вызывается парсером для автоматического выбора 'Ставки дня' и генерации инсайтов по каждому матчу.
    Возвращает dict с { "bet_of_the_day_match_id": int, "insights": { "match_id": "text" } }
    """
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key or not top_bets_data:
        return {}
        
    try:
        # Подготавливаем расширенный JSON с мнением и аргументами капперов для ИИ
        matches_json = []
        for bet in top_bets_data:
            capper_options = []
            if hasattr(bet, 'all_predictions') and bet.all_predictions:
                for p in bet.all_predictions:
                    capper_options.append({
                        "capper": p.source_name,
                        "rating": p.source_weight,
                        "bet": p.predicted_outcome,
                        "odds": p.odds,
                        "capper_argument": p.reasoning[:300] if p.reasoning else ""
                    })

            matches_json.append({
                "match_id": bet.match_id,
                "match": bet.match_name,
                "sport": bet.sport_type,
                "league": bet.league,
                "stat_consensus_outcome": bet.recommended_outcome,
                "stat_odds": bet.average_odds,
                "stat_confidence": bet.confidence_score,
                "capper_predictions": capper_options
            })
            
        system_prompt = """Ты главный спортивный ИИ-аналитик и эксперт по теории вероятностей и проходимости ставок.
Я передаю тебе JSON со списком матчей, где для каждого матча собраны РЕАЛЬНЫЕ ПРОГНОЗЫ КАППЕРОВ с их аргументами и коэффициентами.

Твоя задача — внимательно изучить ВСЕ варианты ставок капперов по каждому матчу и сделать 3 ключевых действия:

1. ВЫБРАТЬ НАИЛУЧШУЮ СТАВКУ ДЛЯ КАЖДОГО МАТЧА ('best_picks_by_match'):
В словаре { "match_id": "выбранная_ставка" } укажи САМУЮ УМНУЮ И ПРОХОДИМУЮ СТАВКУ из тех, что предложили капперы, либо улучшенный безопасный вариант.
ВНИМАНИЕ: Избегай слепых чистых побед П1/П2, если есть более надежные варианты!
В футболе 25-30% матчей заканчиваются ничьей. Если капперы предлагают:
- Двойной шанс (1X, X2 — закрывает 2 из 3 исходов)
- Тоталы (ТМ 3.5, ТБ 1.5, ТБ 2, ТМ 2.5)
- Форы с нулем (0) или плюсовые форы (+1, +1.5)
- Комбинированные исходы (1X + ТМ 3.5, П1 + ТМ 4.5, ОЗ + ТБ 2.5)
- Обе забьют (ОЗ: Да / ОЗ: Нет)
- Индивидуальные тоталы (ИТБ1 1.5, ИТМ2 1.5)
ВСЕГДА ВЫБИРАЙ ИХ, ЕСЛИ ОНИ ВЫГЛЯДЯТ НАДЕЖНЕЕ ЧИСТОГО ИСХОДА!

2. ВЫБРАТЬ 'СТАВКУ ДНЯ' ДЛЯ КАЖДОГО ВИДА СПОРТА ('bet_of_the_day_match_ids'):
В словаре { "вид_спорта": match_id } выбери РОВНО ОДИН главный матч на каждый вид спорта (Football, Basketball, Ice Hockey, Tennis, etc.), в котором проходимость максимальная!

3. СГЕНЕРИРОВАТЬ ИНСАЙТ И ОБОСНОВАНИЕ:
- 'insights': { "match_id": "Короткий яркий инсайт с эмодзи (1 предложение)" }
- 'reasoning': { "match_id": "Аналитическое резюме: почему эта ставка выбрана на основе аргументов капперов и статистики" }

ОТВЕТЬ СТРОГО В JSON:
{
  "best_picks_by_match": {
    "123": "1X + ТМ 3.5",
    "124": "Тотал Больше 2 (ТБ 2)"
  },
  "bet_of_the_day_match_ids": {
    "Football": 123,
    "Ice Hockey": 456
  },
  "insights": {
    "123": "🛡️ Железобетонная страховка: 1X перекрывает ничью, а ТМ 3.5 защищает банк!",
    "456": "🚀 Высокая результативность: обе команды забивают более 3 шайб за игру."
  },
  "reasoning": {
    "123": "Капперы подчеркивают надежную оборону хозяев и проблемы в атаке гостей. Комбо 1X + ТМ 3.5 покрывает 90% вероятных счетов.",
    "456": "Анализ личных встреч показывает, что в 8 из 10 последних матчей данный тотал пробивался с запасом."
  }
}
"""
        models_to_try = ["openrouter/free", "google/gemini-2.0-flash-exp:free", "meta-llama/llama-3.3-70b-instruct:free"]
        for mod in models_to_try:
            try:
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    data=json.dumps({
                        "model": mod,
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": json.dumps(matches_json, ensure_ascii=False)}
                        ]
                    }),
                    timeout=25
                )
                if response.status_code == 200:
                    content = response.json()["choices"][0]["message"]["content"]
                    if content.startswith("```json"):
                        content = content[7:-3]
                    elif content.startswith("```"):
                        content = content[3:-3]
                    parsed = json.loads(content.strip())
                    if parsed and isinstance(parsed, dict):
                        return parsed
            except Exception as ex_m:
                logger.debug(f"Model {mod} failed: {ex_m}")
                continue
    except Exception as e:
        logger.error(f"Auto-analyzer failed: {e}")
        
    return {}
