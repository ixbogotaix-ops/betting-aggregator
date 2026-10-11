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
                "sport": bet.sport_type, # Передаем вид спорта!
                "league": bet.league,
                "odds": bet.average_odds,
                "confidence": bet.confidence_score
            })
            
        system_prompt = """Ты спортивный ИИ-каппер. Я передам тебе JSON со списком топовых ставок. 
Твоя задача:
1. Выбрать РОВНО ОДНУ 'Ставку Дня' ДЛЯ КАЖДОГО ВИДА СПОРТА (например, 1 для Football, 1 для Ice Hockey, 1 для Basketball) и вернуть словарь в поле 'bet_of_the_day_match_ids', где ключ - вид спорта, а значение - match_id.
2. Написать короткий инсайт (1 предложение) от себя по КАЖДОМУ матчу в поле 'insights', используя эмодзи.
3. Написать краткую общую мысль/причину (reasoning) для каждого матча.

ОТВЕТЬ СТРОГО В ФОРМАТЕ JSON:
{
  "bet_of_the_day_match_ids": {
    "Football": 123,
    "Ice Hockey": 456
  },
  "insights": {
    "123": "🔥 Отличный кэф, команда на пике формы!",
    "456": "⚠️ Рискованно из-за травм, но алгоритм верит в победу."
  },
  "reasoning": {
    "123": "Эксперты уверены в победе хозяев, так как гости проиграли 5 матчей подряд на выезде и имеют проблемы в защите.",
    "456": "Большинство капперов берут победу, ожидая закрытую тактическую игру без основных нападающих."
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
