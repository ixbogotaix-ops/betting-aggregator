import os
import logging
import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def send_telegram_message(text: str):
    load_dotenv(override=True)
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        logger.warning("Telegram Bot Token или Chat ID не настроены. Пропуск отправки.")
        return False
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            logger.info("Уведомление успешно отправлено в Telegram!")
            return True
        else:
            logger.error(f"Ошибка отправки в Telegram: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Сбой при подключении к Telegram API: {e}")
        return False

async def notify_daily_top_bets(top_bets_data: list):
    """
    Формирует красивый пост для Telegram со ставкой дня и отправляет его.
    """
    if not top_bets_data:
        return
        
    bet_of_the_day = next((b for b in top_bets_data if getattr(b, 'is_bet_of_the_day', False)), None)
    
    message_lines = ["🏆 *Аналитика от ИИ-Каппера* 🏆\n"]
    
    if bet_of_the_day:
        message_lines.append("🔥 *СТАВКА ДНЯ* 🔥")
        message_lines.append(f"*{bet_of_the_day.match_name}*")
        message_lines.append(f"⏱ Время: {bet_of_the_day.match_date.strftime('%H:%M')}")
        message_lines.append(f"🎯 Исход: *{bet_of_the_day.recommended_outcome}*")
        message_lines.append(f"💰 Средний кэф: *{bet_of_the_day.average_odds}*")
        if getattr(bet_of_the_day, 'cappers_reasoning', None):
            message_lines.append(f"\n🧠 _Логика капперов:_ {bet_of_the_day.cappers_reasoning}")
        if getattr(bet_of_the_day, 'ai_insight', None):
            message_lines.append(f"🤖 _ИИ:_ {bet_of_the_day.ai_insight}\n")
    else:
        message_lines.append("ИИ пока не выбрал 'Ставку дня' на сегодня.\n")
        
    message_lines.append("📊 *Остальные топ-матчи:*")
    other_bets = [b for b in top_bets_data if b != bet_of_the_day]
    for bet in other_bets[:5]:
        message_lines.append(f"▪️ *{bet.match_name}* | Кэф {bet.average_odds} | Уверенность: {bet.confidence_score}%")
    
    if len(other_bets) > 5:
        message_lines.append(f"_(И еще {len(other_bets) - 5} матчей...)_")
    
    site_url = os.getenv("SITE_URL", "http://45.84.222.76")
    message_lines.append(f"\n👉 _Все матчи и подробная аналитика:_\n🌐 [AI Sports Aggregator]({site_url}) — {site_url}")
    
    final_text = "\n".join(message_lines)
    if len(final_text) > 4000:
        final_text = final_text[:4000] + "\n...[сообщение обрезано]"
    return send_telegram_message(final_text)

# Множество ID матчей, по которым уже отправлялись супер-алерты (защита от спама)
_NOTIFIED_SUPER_CONSENSUS_IDS = set()

def send_super_consensus_alert(bet) -> bool:
    """
    Отправляет экстренный алерт в Telegram при супер-консенсусе (4+ источника или уверенность >= 85%).
    """
    site_url = os.getenv("SITE_URL", "http://45.84.222.76")
    sources_str = ", ".join(getattr(bet, 'supporting_sources', [])) or "Все ключевые аналитики"
    
    match_time = ""
    if hasattr(bet, 'match_date') and bet.match_date:
        match_time = bet.match_date.strftime('%H:%M МСК (%d.%m)')
    
    text = (
        "🚨 *СУПЕР-КОНСЕНСУС ИИ & КАППЕРОВ!* 🚨\n\n"
        f"⚽ *{bet.match_name}*\n"
        f"🏆 Лига: _{bet.league}_\n"
        f"⏰ Время: *{match_time}*\n\n"
        f"🎯 *ЕДИНОГЛАСНЫЙ ИСХОД:* `{bet.recommended_outcome}`\n"
        f"📊 *Уверенность:* *{bet.confidence_score}%* 🔥\n"
        f"💰 *Средний кэф:* *{bet.average_odds}*\n"
        f"🤝 *Поддержали:* _{sources_str}_\n\n"
    )
    
    if getattr(bet, 'cappers_reasoning', None):
        text += f"🧠 *Аргументы капперов:*\n_{bet.cappers_reasoning}_\n\n"
    elif getattr(bet, 'ai_insight', None):
        text += f"🤖 *Вывод ИИ:*\n_{bet.ai_insight}_\n\n"
        
    text += f"👉 [Смотреть детали и экспрессы на платформе]({site_url})"
    return send_telegram_message(text)

async def check_and_notify_super_consensus(top_bets_data: list):
    """
    Проверяет список ставок и отправляет супер-алерты по тем, кто набрал супер-консенсус и ещё не был отправлен.
    """
    count = 0
    for bet in top_bets_data:
        match_id = getattr(bet, 'match_id', None)
        if match_id in _NOTIFIED_SUPER_CONSENSUS_IDS:
            continue
            
        sources_count = len(getattr(bet, 'supporting_sources', []))
        confidence = getattr(bet, 'confidence_score', 0)
        
        # Условие супер-консенсуса: 4+ источника или уверенность >= 85% при среднем кэфе >= 1.35
        if (sources_count >= 4 or confidence >= 85.0) and getattr(bet, 'average_odds', 0) >= 1.35:
            success = send_super_consensus_alert(bet)
            if success:
                _NOTIFIED_SUPER_CONSENSUS_IDS.add(match_id)
                count += 1
    return count

def send_parlay_alert(parlay: dict) -> bool:
    """
    Отправляет сгенерированный экспресс дня в Telegram.
    """
    if not parlay or not parlay.get("items"):
        return False
        
    site_url = os.getenv("SITE_URL", "http://45.84.222.76")
    p_type = parlay.get("type", "safe")
    header_icon = "🛡️" if p_type == "safe" else "🚀"
    title = parlay.get("title", "Экспресс Дня")
    total_odds = parlay.get("total_odds", 1.0)
    win_1000 = parlay.get("potential_win_1000", 0)
    
    lines = [
        f"{header_icon} *{title.upper()}* {header_icon}",
        f"🏷️ _{parlay.get('tag', 'Высокая проходимость')}_\n",
        f"📈 Общий коэффициент: *{total_odds}*",
        f"💵 Выигрыш со ставки 1 000 ₽: *{win_1000:,} ₽*\n".replace(",", " "),
        "📋 *События в купоне:*"
    ]
    
    for idx, item in enumerate(parlay.get("items", []), 1):
        lines.append(
            f"{idx}️⃣ *{item['match_name']}*\n"
            f"   🏆 _{item.get('league', '')}_\n"
            f"   🎯 Выбор: *{item['outcome']}* (кэф *{item['odds']}*) | Уверенность: *{item['confidence_score']}%*"
        )
        
    lines.append(f"\n👉 [Собрать или настроить экспресс в калькуляторе]({site_url})")
    
    final_text = "\n".join(lines)
    return send_telegram_message(final_text)

