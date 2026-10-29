path = r'd:\AI\BK\betting_aggregator\backend\app\capper_scraper.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

old_block = """        # 1. Получаем реальные матчи из API
        api_client = SportsAPIClient()
        real_matches = api_client.fetch_today_matches()
        
        if not real_matches:
            logger.warning("Не удалось получить реальные матчи из API. Проверь SPORTS_API_KEY в .env")
            # Если ключа нет, создадим один фейковый матч для демонстрации архитектуры
            import datetime
            real_matches = [{
                "id": "mock_api_1",
                "sport": "Soccer",
                "league": "Mock League",
                "home": "Манчестер Юнайтед",
                "away": "Арсенал",
                "time": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
            }]
            logger.info("Используем резервный тестовый матч, так как API-ключ не задан.")
            
        # Гарантированно сохраняем все найденные реальные матчи в БД как официальные афиши
        for m in real_matches:
            match = await find_existing_match_exact(m["home"], m["away"], session)
            if not match:
                match = Match(
                    sport_type=m["sport"],
                    league=m["league"],
                    home_team=m["home"],
                    away_team=m["away"],
                    match_date=m["time"],
                    status=MatchStatus.upcoming
                )
                session.add(match)
                await session.flush()
            else:
                # Обновляем время матча до точного московского времени
                match.match_date = m["time"]
                
        await session.commit()"""

new_block = """        # 1. Получаем реальные матчи из API (если доступно)
        api_client = SportsAPIClient()
        real_matches = api_client.fetch_today_matches() or []
        
        if not real_matches:
            logger.info("Sports API недоступен или лимит исчерпан. Используем прямые линии парсеров (Vprognoze, Legalbet, Stavka TV).")
            real_matches = []
            
        # Гарантированно сохраняем реальные матчи (только если они действительно получены из API)
        if real_matches:
            for m in real_matches:
                match = await find_existing_match_exact(m["home"], m["away"], session)
                if not match:
                    match = Match(
                        sport_type=m["sport"],
                        league=m["league"],
                        home_team=m["home"],
                        away_team=m["away"],
                        match_date=m["time"],
                        status=MatchStatus.upcoming
                    )
                    session.add(match)
                    await session.flush()
                else:
                    match.match_date = m["time"]
            await session.commit()"""

norm_text = text.replace('\r\n', '\n')
norm_old = old_block.replace('\r\n', '\n')
norm_new = new_block.replace('\r\n', '\n')

if norm_old in norm_text:
    updated = norm_text.replace(norm_old, norm_new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(updated)
    print("SUCCESS: Mock code removed from capper_scraper.py")
else:
    print("FAILED TO FIND OLD BLOCK")
