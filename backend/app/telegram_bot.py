import os
import logging
import asyncio
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Множество ID матчей, по которым уже отправлялись супер-алерты (защита от спама)
_NOTIFIED_SUPER_CONSENSUS_IDS = set()
_NOTIFIED_TRIPLE_AI_IDS = set()

# Основное интерактивное меню кнопок в Telegram
MAIN_KEYBOARD = {
    "keyboard": [
        [{"text": "🏆 Ставка дня"}, {"text": "🤖 Топ ИИ (3/3)"}],
        [{"text": "⚡ Экспресс дня"}, {"text": "📊 Итоги & Статистика"}],
        [{"text": "🌐 Открыть сайт"}]
    ],
    "resize_keyboard": True,
    "is_persistent": True
}

def send_telegram_message(text: str, chat_id: Optional[str] = None, reply_markup: Optional[Dict] = None) -> bool:
    load_dotenv(override=True)
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    target_chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not target_chat_id:
        logger.warning("Telegram Bot Token или Chat ID не настроены. Пропуск отправки.")
        return False
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": target_chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    try:
        response = requests.post(url, json=payload, timeout=25)
        if response.status_code == 200:
            logger.info(f"Сообщение успешно отправлено в Telegram chat {target_chat_id}!")
            return True
        else:
            logger.error(f"Ошибка отправки в Telegram: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Сбой при подключении к Telegram API: {e}")
        return False

# ==========================================
# 1. АЛЕРТЫ И ДАЙДЖЕСТЫ
# ==========================================

def send_super_consensus_alert(bet) -> bool:
    """
    Отправляет экстренный алерт в Telegram при супер-консенсусе капперов (4+ источника или уверенность >= 85%).
    """
    site_url = os.getenv("SITE_URL", "https://dthenbk.duckdns.org:8444")
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
    return send_telegram_message(text, reply_markup=MAIN_KEYBOARD)

def send_super_ai_triple_alert(m: dict) -> bool:
    """
    Отправляет экстренный алерт в Telegram, когда все 3 математических алгоритма (Робобет + Vitibet + Zulubet)
    выдали одинаковый прогноз!
    """
    site_url = os.getenv("SITE_URL", "https://dthenbk.duckdns.org:8444")
    m_id = m.get("id") or f"{m.get('team1')}_{m.get('team2')}_{m.get('time')}"
    if m_id in _NOTIFIED_TRIPLE_AI_IDS:
        return False

    team1 = m.get("team1")
    team2 = m.get("team2")
    time_str = m.get("time", "")
    country = m.get("country", "Футбол")
    rec = m.get("recommendation", "")
    odd = m.get("rec_odd", "-")
    prob = m.get("rec_prob", "-")
    v_score = m.get("vitibet_proj_score", "-")
    v_idx = m.get("vitibet_index", "-")
    z_tip = m.get("zulubet_tip", "-")

    text = (
        "🔥 *СУПЕР-КОНСЕНСУС ТРОЙНОГО ИИ (3/3)!* 🔥\n\n"
        f"⚽ *{team1} vs {team2}*\n"
        f"🏆 Турнир: _{country}_\n"
        f"⏰ Время: *{time_str} МСК*\n\n"
        f"🎯 *ВЫБОР СУПЕРКОМПЬЮТЕРА:* `{rec}` (Кэф: *{odd}*)\n"
        f"📈 *Математическая вероятность:* *{prob}%*\n\n"
        "🧠 *Показания 3-х независимых алгоритмов:*\n"
        f"▪️ *Робобет (Poisson/EV):* {rec} ({prob}%), валуйный перевес\n"
        f"▪️ *Vitibet (Index):* точный счёт `{v_score}` | индекс уверенности: `{v_idx}`\n"
        f"▪️ *Zulubet (Tips):* прогноз `{z_tip}` | расчёт исходов\n\n"
        "⚡ _Все три независимые математические системы подтвердили исход!_\n\n"
        f"👉 [Открыть матч на платформе]({site_url})"
    )

    success = send_telegram_message(text, reply_markup=MAIN_KEYBOARD)
    if success:
        _NOTIFIED_TRIPLE_AI_IDS.add(m_id)
    return success

async def check_and_notify_triple_ai_matches():
    """
    Сканирует кэш Робобета и отправляет алерты по неначавшимся матчам с супер-консенсусом 3/3.
    """
    try:
        from .robobet_scraper import get_robobet_cached
        data = get_robobet_cached()
        matches = data.get("matches", [])
        
        sent = 0
        for m in matches:
            if m.get("is_triple_consensus") and not m.get("is_time_past") and not m.get("is_finished"):
                if float(m.get("rec_odd") or 0) >= 1.40:
                    ok = send_super_ai_triple_alert(m)
                    if ok:
                        sent += 1
                        await asyncio.sleep(1) # пауза между сообщениями
        return sent
    except Exception as e:
        logger.warning(f"Ошибка проверки матчей Тройного ИИ для Telegram: {e}")
        return 0

async def notify_daily_top_bets(top_bets_data: list):
    """
    Формирует красивый пост для Telegram со ставкой дня от капперов.
    """
    if not top_bets_data:
        return
        
    bet_of_the_day = next((b for b in top_bets_data if getattr(b, 'is_bet_of_the_day', False)), None)
    
    message_lines = ["🏆 *Утренний дайджест: Лучшие ставки дня* 🏆\n"]
    
    if bet_of_the_day:
        message_lines.append("🔥 *ГЛАВНАЯ СТАВКА ДНЯ (КОНСЕНСУС)* 🔥")
        message_lines.append(f"⚽ *{bet_of_the_day.match_name}*")
        message_lines.append(f"🏆 Лига: _{bet_of_the_day.league}_")
        if hasattr(bet_of_the_day, 'match_date') and bet_of_the_day.match_date:
            message_lines.append(f"⏱ Время: *{bet_of_the_day.match_date.strftime('%H:%M МСК')}*")
        message_lines.append(f"🎯 Исход: *{bet_of_the_day.recommended_outcome}*")
        message_lines.append(f"💰 Средний кэф: *{bet_of_the_day.average_odds}*")
        message_lines.append(f"📊 Уверенность: *{bet_of_the_day.confidence_score}%*")
        if getattr(bet_of_the_day, 'cappers_reasoning', None):
            message_lines.append(f"\n🧠 _Логика капперов:_ {bet_of_the_day.cappers_reasoning[:200]}...")
        if getattr(bet_of_the_day, 'ai_insight', None):
            message_lines.append(f"🤖 _ИИ:_ {bet_of_the_day.ai_insight}\n")
    else:
        message_lines.append("ИИ пока отбирает лучшую ставку дня...\n")
        
    message_lines.append("📊 *Другие надёжные матчи сегодня:*")
    other_bets = [b for b in top_bets_data if b != bet_of_the_day]
    for bet in other_bets[:4]:
        time_str = bet.match_date.strftime('%H:%M') if hasattr(bet, 'match_date') and bet.match_date else ""
        message_lines.append(f"▪️ *{bet.match_name}* {time_str} | *{bet.recommended_outcome}* (кэф {bet.average_odds}) | Уверенность: {bet.confidence_score}%")
    
    site_url = os.getenv("SITE_URL", "https://dthenbk.duckdns.org:8444")
    message_lines.append(f"\n👉 [Все матчи и экспрессы на платформе]({site_url})")
    
    final_text = "\n".join(message_lines)
    return send_telegram_message(final_text, reply_markup=MAIN_KEYBOARD)

def send_parlay_alert(parlay: dict) -> bool:
    """
    Отправляет сгенерированный экспресс дня в Telegram.
    """
    if not parlay or not parlay.get("items"):
        return False
        
    site_url = os.getenv("SITE_URL", "https://dthenbk.duckdns.org:8444")
    p_type = parlay.get("type", "safe")
    header_icon = "🔥" if p_type == "ai" else ("🛡️" if p_type == "safe" else "🚀")
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
        
    lines.append(f"\n👉 [Собрать купон в калькуляторе на сайте]({site_url})")
    
    final_text = "\n".join(lines)
    return send_telegram_message(final_text, reply_markup=MAIN_KEYBOARD)

async def notify_daily_morning_digest():
    """
    Утренняя рассылка в 10:30 МСК: Ставка дня + Топ-3 Тройного ИИ + Надёжный экспресс.
    """
    from .database import AsyncSessionLocal
    from .consensus import calculate_daily_top_bets
    from .parlay_service import generate_daily_parlays
    from .robobet_scraper import get_robobet_cached

    try:
        async with AsyncSessionLocal() as session:
            top_bets = await calculate_daily_top_bets(session, status_filter="upcoming")
            if not top_bets:
                top_bets = await calculate_daily_top_bets(session)
            
            # 1. Отправляем утренний пост ставки дня
            if top_bets:
                await notify_daily_top_bets(top_bets)
                await asyncio.sleep(2)

            # 2. Отправляем готовый Экспресс
            parlays = await generate_daily_parlays(session)
            best_parlay = parlays.get("ai_parlay") or parlays.get("safe_parlay")
            if best_parlay:
                send_parlay_alert(best_parlay)
    except Exception as e:
        logger.error(f"Ошибка утренней рассылки: {e}")

async def notify_evening_summary():
    """
    Вечерний отчет в 23:30 МСК об итогах дня (сколько зашло / не зашло, винрейт, профит).
    """
    from .database import AsyncSessionLocal
    from .settlement_service import get_performance_stats
    from datetime import date

    try:
        today_str = date.today().isoformat()
        async with AsyncSessionLocal() as session:
            stats = await get_performance_stats(session)
            overview = stats.overview

            text = (
                f"🌙 *ВЕЧЕРНИЙ ИТОГОВЫЙ ОТЧЁТ СТАВОК* ({today_str}) 🌙\n\n"
                f"📊 Рассчитано ставок: *{overview.total_matches}*\n"
                f"✅ Выигрышей: *{overview.wins}*\n"
                f"❌ Проигрышей: *{overview.losses}*\n"
                f"🔄 Возвратов: *{overview.refunds}*\n\n"
                f"🎯 *Винрейт системы:* *{overview.winrate_pct}%*\n"
                f"💰 *Чистая прибыль:* *{'+' if overview.net_profit_units > 0 else ''}{overview.net_profit_units} u* (флэт 1u)\n"
                f"📈 *ROI системы:* *{'+' if overview.roi_pct > 0 else ''}{overview.roi_pct}%*\n\n"
                f"👉 [Открыть полный архив со счетами матчей](https://dthenbk.duckdns.org:8444)"
            )
            send_telegram_message(text, reply_markup=MAIN_KEYBOARD)
    except Exception as e:
        logger.error(f"Ошибка вечерней рассылки отчета: {e}")

async def send_yesterday_settlement_and_monthly_stats_report(chat_id: Optional[str] = None, target_date: Optional[str] = None) -> bool:
    """
    Отправляет утренний отчёт в Telegram по результатам ставок за вчерашний день
    и сводную статистику за текущий месяц (сколько прошло, сколько не прошло, винрейт, прибыль в флэтах).
    """
    from .database import AsyncSessionLocal
    from .monthly_stats_service import get_monthly_performance
    from .consensus import calculate_daily_top_bets, get_daily_top3_lock

    moscow_tz = timezone(timedelta(hours=3))
    now = datetime.now(moscow_tz)

    if not target_date:
        y_dt = now - timedelta(days=1)
        target_date = y_dt.strftime("%Y-%m-%d")
    else:
        try:
            y_dt = datetime.strptime(target_date, "%Y-%m-%d")
        except Exception:
            y_dt = now - timedelta(days=1)
            target_date = y_dt.strftime("%Y-%m-%d")

    day_num = y_dt.day
    month_names_gen = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля",
        5: "мая", 6: "июня", 7: "июля", 8: "августа",
        9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }
    month_names_nom = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
    }
    date_formatted_ru = f"{day_num} {month_names_gen.get(y_dt.month, '')}"
    site_url = os.getenv("SITE_URL", "https://dthenbk.duckdns.org:8444")

    try:
        async with AsyncSessionLocal() as session:
            # 1. Получаем статистику за текущий месяц
            perf = await get_monthly_performance(session)
            m_summary = perf.get("current_month_to_date") or perf.get("selected_month_summary") or {}

            # Находим вчерашнюю ставку дня в календаре
            days = perf.get("days", [])
            yesterday_botd = next((d for d in days if d.get("date") == target_date), None)

            # 2. Получаем Топ-3 ставки дня за вчера
            top_bets = await calculate_daily_top_bets(session, date_str=target_date, status_filter="all")
            top3 = [b for b in top_bets if getattr(b, 'daily_rank', 99) in [1, 2, 3]][:3]
            if not top3 and top_bets:
                top3 = top_bets[:3]

            lines = [
                f"📊 *ИТОГИ СТАВОК ЗА ВЧЕРА ({date_formatted_ru.upper()})* 📊\n"
            ]

            if yesterday_botd:
                st = yesterday_botd.get("result_status", "upcoming")
                if st == "win":
                    badge = "✅ *ПРОШЛО*"
                    p_txt = f"(+{yesterday_botd.get('profit', 0):.2f} флэт)"
                elif st == "loss":
                    badge = "❌ *НЕ ПРОШЛО*"
                    p_txt = "(-1.00 флэт)"
                elif st == "refund":
                    badge = "🔄 *ВОЗВРАТ*"
                    p_txt = "(0.00 флэт)"
                else:
                    badge = "⏳ *Ожидает расчета*"
                    p_txt = ""

                score_info = f" | Счёт: *{yesterday_botd.get('score')}*" if yesterday_botd.get("score") else ""
                icon = yesterday_botd.get("sport_icon", "⚽")
                league_info = f"🏆 Лига: _{yesterday_botd.get('league')}_" if yesterday_botd.get("league") else ""

                lines.append("👑 *ГЛАВНАЯ СТАВКА ДНЯ:*")
                lines.append(f"{icon} *{yesterday_botd.get('match_name')}*")
                if league_info:
                    lines.append(league_info)
                lines.append(f"🎯 Исход: *{yesterday_botd.get('outcome')}* (кэф *{yesterday_botd.get('odds')}*){score_info}")
                lines.append(f"Статус: {badge} {p_txt}\n")

            # Другие топ-ставки дня, если есть
            other_top = []
            for b in top3:
                # Пропускаем дубликат ставки дня
                if yesterday_botd and yesterday_botd.get("match_name") and (
                    yesterday_botd.get("home_team", "---") in b.match_name or 
                    b.home_team in yesterday_botd.get("match_name", "")
                ):
                    continue
                other_top.append(b)

            if other_top:
                lines.append("🥈 *ДРУГИЕ ТОП СТАВКИ ДНЯ:*")
                for b in other_top:
                    b_st = getattr(b, 'bet_result', None)
                    if b_st == "win":
                        b_badge = "✅ *ПРОШЛО*"
                        b_p = f"(+{b.average_odds - 1.0:.2f} флэт)"
                    elif b_st == "loss":
                        b_badge = "❌ *НЕ ПРОШЛО*"
                        b_p = "(-1.00 флэт)"
                    elif b_st == "refund":
                        b_badge = "🔄 *ВОЗВРАТ*"
                        b_p = "(0.00 флэт)"
                    else:
                        b_badge = "⏳ *Завершён*" if b.status == "finished" else "⏳ *В игре*"
                        b_p = ""

                    score_str = f" | Счёт: *{b.final_score_home}:{b.final_score_away}*" if b.final_score_home is not None else ""
                    lines.append(f"▪️ *{b.match_name}*")
                    lines.append(f"   🎯 *{b.recommended_outcome}* (кэф *{b.average_odds}*){score_str}")
                    lines.append(f"   Итог: {b_badge} {b_p}")
                lines.append("")

            # Блок статистики за месяц
            cur_month_title = f"{month_names_nom.get(now.month, 'Текущий месяц')} {now.year}"
            tot = m_summary.get("finished_bets", 0) + m_summary.get("upcoming_bets", 0)
            if tot == 0:
                tot = m_summary.get("total_bets", 0) or m_summary.get("total_days", 0)
            w = m_summary.get("wins", 0)
            l = m_summary.get("losses", 0)
            r = m_summary.get("refunds", 0)
            wr = m_summary.get("winrate", 0.0)
            profit = m_summary.get("profit_units", 0.0)
            roi = m_summary.get("roi", 0.0)
            profit_sign = "+" if profit > 0 else ""

            lines.append("───────────────────────")
            lines.append(f"📈 *СТАТИСТИКА ЗА {cur_month_title.upper()}:*")
            lines.append(f"▪️ Рассчитано ставок: *{w + l + r}* из {tot}")
            lines.append(f"▪️ Прошло: *{w}* ✅  |  Мимо: *{l}* ❌" + (f"  |  Возврат: *{r}* 🔄" if r > 0 else ""))
            lines.append(f"▪️ Проходимость (Winrate): *{wr}%* 🔥")
            lines.append(f"▪️ Чистая прибыль: *{profit_sign}{profit:.2f} флэт* 💰")
            lines.append(f"▪️ Доходность (ROI): *{'+' if roi > 0 else ''}{roi}%*")
            lines.append("───────────────────────\n")
            lines.append(f"👉 [Открыть детальный календарь и архив]({site_url})")

            final_text = "\n".join(lines)
            return send_telegram_message(final_text, chat_id=chat_id, reply_markup=MAIN_KEYBOARD)
    except Exception as e:
        logger.error(f"Ошибка формирования отчета о результатах: {e}", exc_info=True)
        return False

# ==========================================
# 2. ИНТЕРАКТИВНЫЙ ОБРАБОТЧИК СООБЩЕНИЙ (POLLING)
# ==========================================

async def handle_telegram_incoming_message(chat_id: int, text: str):
    """
    Обрабатывает команду пользователя или клик по кнопке клавиатуры.
    """
    text_clean = text.strip()
    site_url = os.getenv("SITE_URL", "https://dthenbk.duckdns.org:8444")

    if text_clean in ["/start", "/help", "старт", "привет"]:
        welcome_text = (
            "👋 *Добро пожаловать в AI Sports Aggregator!* 🤖\n\n"
            "Я официальный бот платформы спортивной аналитики и прогнозов. Объединяю:\n"
            "▫️ Прогнозы ведущих капперов рунета (7 источников)\n"
            "▫️ Математический Тройной ИИ (*Робобет + Vitibet + Zulubet*)\n"
            "▫️ Алгоритмические экспрессы с расчетом вероятностей\n\n"
            "🎯 *Выберите нужный раздел в меню ниже:* 👇"
        )
        send_telegram_message(welcome_text, chat_id=str(chat_id), reply_markup=MAIN_KEYBOARD)
        return

    from .database import AsyncSessionLocal

    if text_clean in ["🏆 Ставка дня", "/today", "ставка дня", "топ"]:
        from .consensus import calculate_daily_top_bets
        async with AsyncSessionLocal() as session:
            top_bets = await calculate_daily_top_bets(session, status_filter="upcoming")
            if not top_bets:
                top_bets = await calculate_daily_top_bets(session)

            if not top_bets:
                send_telegram_message("⏳ На сегодня все матчи уже завершились или аналитики ещё формируют линию на завтра.", chat_id=str(chat_id), reply_markup=MAIN_KEYBOARD)
                return

            botd = next((b for b in top_bets if getattr(b, 'is_bet_of_the_day', False)), top_bets[0])
            time_str = botd.match_date.strftime('%H:%M МСК') if botd.match_date else ""

            msg = (
                "🏆 *СТАВКА ДНЯ ОТ КАППЕРОВ & ИИ* 🏆\n\n"
                f"⚽ *{botd.match_name}*\n"
                f"🏆 Лига: _{botd.league}_\n"
                f"⏰ Время: *{time_str}*\n\n"
                f"🎯 Рекомендация: *{botd.recommended_outcome}*\n"
                f"💰 Средний кэф: *{botd.average_odds}*\n"
                f"📊 Уверенность аналитиков: *{botd.confidence_score}%*\n\n"
            )
            if getattr(botd, 'cappers_reasoning', None):
                msg += f"🧠 *Аргументы:* _{botd.cappers_reasoning[:250]}..._\n\n"
            msg += f"👉 [Смотреть подробности на сайте]({site_url})"
            send_telegram_message(msg, chat_id=str(chat_id), reply_markup=MAIN_KEYBOARD)
        return

    if text_clean in ["🤖 Топ ИИ (3/3)", "/robobet", "робобет", "ии"]:
        from .robobet_scraper import get_robobet_cached
        data = get_robobet_cached()
        matches = data.get("matches", [])
        
        upcoming = [m for m in matches if not m.get("is_time_past") and not m.get("is_finished")]
        if not upcoming:
            send_telegram_message("🤖 На сегодня все матчи Робобета завершились. Обновление линии ожидается утром!", chat_id=str(chat_id), reply_markup=MAIN_KEYBOARD)
            return

        triple_matches = [m for m in upcoming if m.get("is_triple_consensus")]
        selected = triple_matches[:3] if triple_matches else upcoming[:3]

        lines = ["🤖 *ТОП МАТЧИ ОТ ТРОЙНОГО ИИ (Робобет + Vitibet + Zulubet)* 🤖\n"]
        for idx, m in enumerate(selected, 1):
            badge = "🔥 [3/3 Консенсус]" if m.get("is_triple_consensus") else "⚡ [Матем. выбор]"
            v_score = f" (Vitibet {m.get('vitibet_proj_score')})" if m.get('vitibet_proj_score') else ""
            lines.append(
                f"{idx}️⃣ *{m.get('team1')} vs {m.get('team2')}* {badge}\n"
                f"   ⏰ {m.get('time')} МСК | _{m.get('country')}_\n"
                f"   🎯 Исход: *{m.get('recommendation')}* (кэф *{m.get('rec_odd')}*) | Вероятность: *{m.get('rec_prob')}%*{v_score}\n"
            )

        lines.append(f"👉 [Открыть полный раздел Тройного ИИ на сайте]({site_url})")
        send_telegram_message("\n".join(lines), chat_id=str(chat_id), reply_markup=MAIN_KEYBOARD)
        return

    if text_clean in ["⚡ Экспресс дня", "/express", "экспресс"]:
        from .parlay_service import generate_daily_parlays
        async with AsyncSessionLocal() as session:
            parlays = await generate_daily_parlays(session)
            target = parlays.get("ai_parlay") or parlays.get("safe_parlay") or parlays.get("hot_parlay")
            if not target:
                send_telegram_message("⚡ Экспресс дня сейчас формируется из новых матчей. Загляните чуть позже!", chat_id=str(chat_id), reply_markup=MAIN_KEYBOARD)
                return

            total_odds = target.get("total_odds", 1.0)
            items = target.get("items", [])
            win_1000 = target.get("potential_win_1000", 0)

            lines = [
                f"⚡ *{target.get('title', 'Экспресс дня').upper()}* ⚡",
                f"🏷️ _{target.get('tag', 'Высокая проходимость')}_\n",
                f"📈 Общий коэффициент: *{total_odds}*",
                f"💵 Выигрыш с 1 000 ₽: *{win_1000:,} ₽*\n".replace(",", " "),
                "📋 *События в купоне:*"
            ]
            for idx, it in enumerate(items, 1):
                lines.append(
                    f"{idx}️⃣ *{it['match_name']}*\n"
                    f"   🏆 _{it.get('league', '')}_\n"
                    f"   🎯 Выбор: *{it['outcome']}* (кэф *{it['odds']}*)"
                )
            lines.append(f"\n👉 [Собрать купон в калькуляторе на сайте]({site_url})")
            send_telegram_message("\n".join(lines), chat_id=str(chat_id), reply_markup=MAIN_KEYBOARD)
        return

    if text_clean in ["📊 Итоги & Статистика", "📊 Статистика архива", "/stats", "/results", "/yesterday", "статистика", "итоги", "архив", "вчера", "результаты"]:
        await send_yesterday_settlement_and_monthly_stats_report(chat_id=str(chat_id))
        return

    if text_clean in ["🌐 Открыть сайт", "/site", "сайт"]:
        msg = (
            "🌐 *AI Sports Betting Aggregator*\n\n"
            f"Платформа доступна 24/7 по защищенному адресу:\n"
            f"👉 {site_url}\n\n"
            "В веб-версии доступны: графики Пуассона, детальные разборы капперов, интерактивный калькулятор экспрессов и архив с фильтром по датам."
        )
        send_telegram_message(msg, chat_id=str(chat_id), reply_markup=MAIN_KEYBOARD)
        return

    # Ответ на любой неизвестный текст
    send_telegram_message(
        "Я вас понял! Воспользуйтесь кнопками внизу экрана, чтобы получить свежую ставку дня, топ ИИ или экспресс. 👇",
        chat_id=str(chat_id),
        reply_markup=MAIN_KEYBOARD
    )

async def start_telegram_polling():
    """
    Асинхронный воркер Telegram Long Polling для обработки входящих команд.
    """
    load_dotenv(override=True)
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN не задан. Фоновый polling Telegram отключен.")
        return

    logger.info("Telegram Bot Long Polling успешно запущен!")
    offset = 0

    while True:
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getUpdates?offset={offset}&timeout=20"
            resp = await asyncio.to_thread(requests.get, url, timeout=30)
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    for update in data.get("result", []):
                        update_id = update.get("update_id", 0)
                        offset = max(offset, update_id + 1)
                        
                        message = update.get("message") or update.get("channel_post")
                        if message:
                            chat = message.get("chat", {})
                            chat_id = chat.get("id")
                            text = message.get("text", "")
                            if chat_id and text:
                                asyncio.create_task(handle_telegram_incoming_message(chat_id, text))
            elif resp.status_code in [409, 401]:
                logger.warning(f"Telegram polling status {resp.status_code}. Пауза 10 сек...")
                await asyncio.sleep(10)
            else:
                await asyncio.sleep(2)
        except Exception as e:
            logger.debug(f"Ошибка в цикле telegram polling (авто-восстановление): {e}")
            await asyncio.sleep(3)
