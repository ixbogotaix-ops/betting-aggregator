path = r'd:\AI\BK\betting_aggregator\backend\app\consensus.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Exclude mock matches from candidate loops
old_mock_check = """    for match in matches:
        if not match.predictions:
            continue"""

new_mock_check = """    for match in matches:
        if not match.predictions or (match.league and 'mock' in match.league.lower()) or match.id == 274:
            continue"""

# 2. Fix match status for matches past 135 minutes
old_status_block = """            elif match.match_date:
                time_diff_sec = (now_moscow - match.match_date).total_seconds()
                if 0 <= time_diff_sec <= 135 * 60:
                    m_status_str = "live"
                else:
                    m_status_str = "upcoming"
            else:
                m_status_str = "upcoming\""""

new_status_block = """            elif match.match_date:
                time_diff_sec = (now_moscow - match.match_date).total_seconds()
                if 0 <= time_diff_sec <= 135 * 60:
                    m_status_str = "live"
                elif time_diff_sec > 135 * 60:
                    m_status_str = "finished"
                else:
                    m_status_str = "upcoming"
            else:
                m_status_str = "upcoming\""""

# 3. Upgrade locked_ids logic to purge 274 and pick the REAL best bets
old_lock_block = """    target_date_str = (target_date if (date_str and date_str != "ALL") else now_moscow).strftime("%Y-%m-%d")
    locked_ids = get_daily_top3_lock(target_date_str)
    if not locked_ids and status_filter != "finished":
        # Если для даты ещё нет фиксации, берём первые 3 ставки с кэфом >= 1.55
        qualifying = [b for b in top_bets if (b.average_odds or 0.0) >= 1.55]
        if qualifying:
            locked_ids = [b.match_id for b in qualifying[:3]]
            save_daily_top3_lock(target_date_str, locked_ids)

    # Если для даты зафиксированы ID матчей, строго выстраиваем их в Топ-3:
    if locked_ids:
        by_id = {b.match_id: b for b in top_bets}
        top3_bets = []
        for m_id in locked_ids:
            if m_id in by_id:
                top3_bets.append(by_id[m_id])"""

new_lock_block = """    target_date_str = (target_date if (date_str and date_str != "ALL") else now_moscow).strftime("%Y-%m-%d")
    locked_ids = get_daily_top3_lock(target_date_str) or []

    # Очищаем locked_ids от удаленных и фейковых матчей (id 274 и т.д.)
    valid_locked_ids = [m_id for m_id in locked_ids if m_id != 274 and any(b.match_id == m_id for b in top_bets)]
    
    # Проверяем, нужно ли обновить фиксацию:
    # 1. Если фиксации не было вообще
    # 2. Если в фиксации были удаленные/фейковые матчи
    # 3. Если текущие зафиксированные матчи слабые (score < 15 или 1 каппер), а в течение дня появились мощные матчи с консенсусом 3+ капперов
    qualifying = [b for b in top_bets if (b.average_odds or 0.0) >= 1.55 and b.match_id != 274]
    needs_reselection = False

    if not valid_locked_ids and status_filter != "finished":
        needs_reselection = True
    elif len(valid_locked_ids) < 3 and len(qualifying) >= 3 and status_filter != "finished":
        needs_reselection = True
    elif valid_locked_ids and qualifying and status_filter != "finished":
        by_id = {b.match_id: b for b in top_bets}
        current_best_score = max((by_id[m].confidence_score for m in valid_locked_ids if m in by_id), default=0)
        top_available_score = qualifying[0].confidence_score if qualifying else 0
        top_pred_count = len(qualifying[0].all_predictions or []) if qualifying else 0
        # Если появился матч с очевидным перевесом консенсуса (3+ мнений и скор на 50% выше), обновляем
        if top_available_score > current_best_score * 1.5 and top_pred_count >= 3:
            needs_reselection = True

    if needs_reselection and qualifying:
        valid_locked_ids = [b.match_id for b in qualifying[:3]]
        save_daily_top3_lock(target_date_str, valid_locked_ids)

    locked_ids = valid_locked_ids

    # Если для даты зафиксированы ID матчей, строго выстраиваем их в Топ-3:
    if locked_ids:
        by_id = {b.match_id: b for b in top_bets}
        top3_bets = []
        for m_id in locked_ids:
            if m_id in by_id:
                top3_bets.append(by_id[m_id])"""

norm_text = text.replace('\r\n', '\n')
norm_text = norm_text.replace(old_mock_check.replace('\r\n', '\n'), new_mock_check.replace('\r\n', '\n'))
norm_text = norm_text.replace(old_status_block.replace('\r\n', '\n'), new_status_block.replace('\r\n', '\n'))
norm_text = norm_text.replace(old_lock_block.replace('\r\n', '\n'), new_lock_block.replace('\r\n', '\n'))

with open(path, 'w', encoding='utf-8') as f:
    f.write(norm_text)

print("SUCCESS: Updated consensus.py!")
