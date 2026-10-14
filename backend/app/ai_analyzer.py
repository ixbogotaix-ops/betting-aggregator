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
    prompt = "Ты профессиональный спортивный аналитик и специалист по Value Betting (+EV). Твоя задача — проанализировать список лучших консенсус-ставок, собранных с различных платформ прогнозистов, и выбрать 1-2 самых лучших и валуйных варианта с математическим перевесом над линией букмекера. Не бойся хороших кэфов (1.80 - 2.30), избегай заниженных кэфов без валуя. Объясни свой выбор коротко и по делу.\n\nСписок ставок:\n"
    
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
                        "content": "Ты элитный ИИ-каппер и спортивный аналитик по Value Betting (+EV). Твоя задача писать профессионально, ярко, сочно, использовать много эмодзи (🔥, 💰, ⚽, 🏆, 🎯, 🚀, 💎) и структурировать текст красиво. Подчеркивай перевес над линией букмекера, выгоду коэффициентов и ценность ставки. Отвечай на русском языке."
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
            
        system_prompt = """Ты — элитный профессиональный спортивный аналитик и эксперт по Sharp Value Betting (валуйные ставки, математическое ожидание и теория вероятностей).
Ты досконально знаешь внутреннюю кухню букмекерского бизнеса: маржу букмекеров, расчет истинной вероятности, формулу математического ожидания (+EV = P_true * odds - 1) и управление дисперсией.

ГЛАВНЫЙ ЗАКОН ПРОФЕССИОНАЛЬНОГО БЕТТИНГА:
Никогда не брать слепо заниженные "надежные" варианты вроде 1X за 1.18-1.25! Это типичная ловушка для новичков: букмекер закладывает в низкие кэфы огромную маржу (6-9%), и на дистанции любая одна осечка сжигает прибыль от 5-6 ставок.
И наоборот: если за П1 на команду дают коэффициент 2.10 (букмекер закладывает вероятность ~47%), а реальная проходимость по аналитике и форме составляет 55%, то это ставка с гигантским перевесом над линией (+15.5% EV)! Такая ставка П1 за 2.10 на порядок выгоднее и доходнее, чем перестраховочная Фора (0) за 1.55 или 1X за 1.25.

ТВОЯ ЗАДАЧА — проанализировать реальные прогнозы капперов и выбрать лучшие ставки по балансу ПРОХОДИМОСТИ И ВАЛУЙНОСТИ (+EV):

1. 'best_picks_by_match' { "match_id": "выбранная_ставка" }:
Выбери наилучшую ставку для каждого матча:
- Оценивай ВАЛУЙНОСТЬ (+EV) и адекватность коэффициента: золотая зона валуя 1.65 – 2.45.
- Если у хозяев отличная форма и капперы уверенно топят за них, смело бери П1 за 1.85-2.25! Не бойся чистых побед, если в них заложен математический перевес над линией.
- Если матч открытый и атакующий — бери Тотал Больше (ТБ 2.5 / ТБ 3) или Обе забьют за 1.70-2.15.
- Если фаворит играет в гостях или есть риск ничьей — сравнивай варианты: Фора (0) за 1.75 может быть идеальным балансом проходимости и возврата при ничьей.
- Двойной шанс (1X / X2) бери ТОЛЬКО ТОГДА, когда на него есть реальный валуйный кэф (от 1.55 и выше, например на дерзкого домашнего андердога)! Если кэф на 1X ниже 1.35 — НИ В КОЕМ СЛУЧАЕ НЕ БЕРИ ЕГО, это мусор по валуйности.
- Также допускаются комбинации (П1 + ТМ 4.5, 1X + ТМ 3.5, ОЗ + ТБ 2.5), если они имеют кэф 1.70 - 2.50.

2. 'bet_of_the_day_match_ids' { "вид_спорта": match_id }:
В словаре укажи РОВНО ОДИН главный матч дня на каждый вид спорта (Football, Ice Hockey, Basketball, Tennis, MMA, etc.).
В качестве "Ставки Дня" выбирай матч, где сочетание ПРОХОДИМОСТИ и ПОЛОЖИТЕЛЬНОГО МАТЕМАТИЧЕСКОГО ОЖИДАНИЯ (+EV) максимальное среди всех кандидатов!

3. 'insights' { "match_id": "Короткий острый инсайт профессионального каппера с эмодзи (1 предложение с акцентом на валуйность/кэф)" }
4. 'reasoning' { "match_id": "Глубокое экспертное обоснование: почему этот исход валуен (+EV), какова истинная вероятность против линии букмекера и почему аргументы капперов перевешивают маржу" }

ОТВЕТЬ СТРОГО В ФОРМАТЕ JSON:
{
  "best_picks_by_match": {
    "123": "Победа Хозяев (П1)",
    "124": "Тотал Больше 2.5 (ТБ 2.5)"
  },
  "bet_of_the_day_match_ids": {
    "Football": 123,
    "Ice Hockey": 456
  },
  "insights": {
    "123": "💎 Мощный валуй (+14% EV): коэффициент 2.10 на чистую победу недооценивает атакующий потенциал хозяев!",
    "456": "🔥 Идеальный баланс проходимости: ТБ 5.5 за 1.85 пробивается в 75% очных встреч этих команд."
  },
  "reasoning": {
    "123": "Букмекер оценил победу хозяев с вероятностью 47.6% (кэф 2.10). Анализ xG и капперский консенсус дают реальную вероятность не менее 56%. Чистая победа П1 дает гораздо более высокий долгосрочный ROI (+17.6%), чем перестраховочные 1X с заниженным кэфом.",
    "456": "Обе команды идут с серией результативных матчей, вратари показывают нестабильную игру. Капперы единогласно выбирают верховой тотал."
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
