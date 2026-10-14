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
        # Подготавливаем JSON с матчами для ИИ
        matches_json = []
        for bet in top_bets_data:
            matches_json.append({
                "match_id": bet.match_id,
                "match": bet.match_name,
                "sport": bet.sport_type,
                "league": bet.league,
                "outcome": bet.recommended_outcome,
                "odds": bet.average_odds,
                "confidence": bet.confidence_score
            })
            
        system_prompt = """Ты главный спортивный ИИ-аналитик и эксперт по математической проходимости ставок. Я передам тебе JSON со списком топовых ставок капперов. 
Твоя задача:
1. Выбрать РОВНО ОДНУ 'Ставку Дня' ДЛЯ КАЖДОГО ВИДА СПОРТА (например, 1 для Football, 1 для Ice Hockey, 1 для Basketball) с прицелом на МАКСИМАЛЬНУЮ ПРОХОДИМОСТЬ (Win Rate / Надежность)!
Обращай особое внимание на тоталы (ТБ/ТМ), двойной шанс (1X/X2), обе забьют (ОЗ) и форы, если они выглядят надежнее чистых исходов П1/П2. Выбирай ставку с минимальным риском проигрыша!
Верни результат в виде словаря 'bet_of_the_day_match_ids', где ключ - вид спорта, а значение - match_id.
2. Написать короткий сочный инсайт (1 предложение) от себя по КАЖДОМУ матчу в поле 'insights', используя эмодзи.
3. Написать краткую причину высокой проходимости (reasoning) для каждого матча.

ОТВЕТЬ СТРОГО В ФОРМАТЕ JSON:
{
  "bet_of_the_day_match_ids": {
    "Football": 123,
    "Ice Hockey": 456
  },
  "insights": {
    "123": "🔥 Максимальная проходимость: ставка закрывает два сценария из трёх!",
    "456": "🛡️ Железобетонный тотал по статистике последних очных встреч."
  },
  "reasoning": {
    "123": "Высочайший консенсус экспертов на двойной исход или тотал, снижающий риск ничьей.",
    "456": "Команды стабильно пробивают этот тотал, эксперты ожидают открытую игру."
  }
}
"""
        import requests, json
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "model": "openrouter/free",
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
            # Пытаемся распарсить JSON
            # Иногда ИИ оборачивает в ```json
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
            return json.loads(content.strip())
    except Exception as e:
        logger.error(f"Auto-analyzer failed: {e}")
        
    return {}
