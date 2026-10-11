import asyncio
from typing import Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from rapidfuzz import fuzz, process
from datetime import timedelta, datetime

from app.database import AsyncSessionLocal
from app.models import Match

# Порог схожести. Выше 85 - считаем, что это та же самая команда.
SIMILARITY_THRESHOLD = 85.0

async def get_canonical_team_name(incoming_name: str, session: AsyncSession) -> str:
    """
    Ищет похожее название команды в базе данных.
    Использует token_sort_ratio для хорошей работы с переставленными словами 
    (например, "United Manchester" == "Manchester United").
    """
    # 1. Получаем все уникальные имена команд из БД.
    # В реальном HighLoad проекте этот список лучше держать в Redis, 
    # чтобы не дергать БД на каждый парсинг.
    stmt_home = select(Match.home_team).distinct()
    stmt_away = select(Match.away_team).distinct()
    
    home_teams = (await session.execute(stmt_home)).scalars().all()
    away_teams = (await session.execute(stmt_away)).scalars().all()
    
    # Объединяем в один уникальный список
    all_teams = list(set(home_teams).union(set(away_teams)))
    
    if not all_teams:
        return incoming_name
        
    # 2. Ищем лучшее совпадение с помощью rapidfuzz
    # process.extractOne возвращает кортеж (best_match, score, index)
    match_result = process.extractOne(
        incoming_name, 
        all_teams, 
        scorer=fuzz.token_sort_ratio
    )
    
    if match_result:
        best_match, score, index = match_result
        if score >= SIMILARITY_THRESHOLD:
            # Нашли похожее! Возвращаем то, которое уже есть в БД (каноническое)
            return best_match
            
    # Если ничего похожего нет (score < 85), значит это новая команда
    return incoming_name


async def find_existing_match_fuzzy(
    home_team: str, 
    away_team: str, 
    match_date: datetime, 
    session: AsyncSession,
    sport_type: str = "Football"
) -> Optional[Match]:
    """
    Проверяет, существует ли матч в БД, используя нечеткое сопоставление имен команд.
    """
    # Нормализуем обе команды
    canonical_home = await get_canonical_team_name(home_team, session)
    canonical_away = await get_canonical_team_name(away_team, session)
    
    # Ищем матч с каноническими именами. 
    # ОЧЕНЬ ВАЖНО: даем допуск по дате (например, +/- 24 часа), 
    # так как на разных сайтах время матча может отличаться из-за часовых поясов 
    # или сдвигов в расписании турнира.
    date_start = match_date - timedelta(hours=24)
    date_end = match_date + timedelta(hours=24)
    
    stmt = select(Match).where(
        Match.home_team == canonical_home,
        Match.away_team == canonical_away,
        Match.sport_type == sport_type,
        Match.match_date >= date_start,
        Match.match_date <= date_end
    )
    
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


# =====================================================================
# БЛОК ТЕСТИРОВАНИЯ
# =====================================================================
async def test_matcher():
    print("=== Запуск тестов Fuzzy Matching (rapidfuzz) ===\n")
    
    async with AsyncSessionLocal() as session:
        test_date = datetime.now()
        
        # 1. Добавляем эталонный матч в БД, чтобы нам было с чем сравнивать
        test_match = Match(
            sport_type="Football",
            league="Premier League",
            home_team="Manchester United",
            away_team="Manchester City",
            match_date=test_date,
            status="upcoming"
        )
        session.add(test_match)
        await session.commit()
        print("[+] Добавлен эталонный матч: Manchester United vs Manchester City")
        print("-" * 50)
        
        # 2. Тестируем поиск канонического имени (home_team)
        variations = [
            "Man United", 
            "Manchester Utd", 
            "Man Utd",
            "United Manchester", 
            "Манчестер Юнайтед", # Кириллица! Rapidfuzz не поймет транслит без подготовки
            "Arsenal" # Совсем другая команда
        ]
        
        print("Тестирование get_canonical_team_name():")
        for var in variations:
            canonical = await get_canonical_team_name(var, session)
            
            # Считаем точный score для наглядности вывода
            score = fuzz.token_sort_ratio(var, test_match.home_team)
            
            if canonical == test_match.home_team:
                print(f"  ✅ '{var}' (Скор: {score:.1f}) -> Распознано как: '{canonical}'")
            else:
                print(f"  ❌ '{var}' (Скор: {score:.1f}) -> Слишком далеко! Оставлено как новое: '{canonical}'")
                
        print("-" * 50)
        
        # 3. Тестируем поиск целого матча с искаженными именами
        print("Тестирование find_existing_match_fuzzy() ('Man Utd' vs 'Man City'):")
        found_match = await find_existing_match_fuzzy(
            "Man Utd", "Man City", test_date, session
        )
        
        if found_match:
            print(f"  ✅ Успех! Матч найден под каноничным именем: {found_match.home_team} vs {found_match.away_team} (ID: {found_match.id})")
        else:
            print("  ❌ Матч не найден.")
            
        print("\n=== Тесты завершены ===")

if __name__ == "__main__":
    asyncio.run(test_matcher())
