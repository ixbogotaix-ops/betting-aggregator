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
    send_telegram_message(final_text)
