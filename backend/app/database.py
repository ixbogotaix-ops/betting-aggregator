from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Замените строку подключения на ваши реальные данные
# Переключено на SQLite для того, чтобы всё работало сразу "из коробки" без настройки серверов
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./betting_db.sqlite"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()

async def init_db():
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Безопасная проверка существующих колонок через PRAGMA table_info (предотвращает откат транзакции)
        try:
            pred_cols_res = await conn.execute(text("PRAGMA table_info(predictions)"))
            pred_cols = {row[1] for row in pred_cols_res.fetchall()}
            
            match_cols_res = await conn.execute(text("PRAGMA table_info(matches)"))
            match_cols = {row[1] for row in match_cols_res.fetchall()}

            if "reasoning" not in pred_cols:
                await conn.execute(text("ALTER TABLE predictions ADD COLUMN reasoning TEXT"))
            if "status" not in pred_cols:
                await conn.execute(text("ALTER TABLE predictions ADD COLUMN status VARCHAR(20)"))

            if "tactical_analysis" not in match_cols:
                await conn.execute(text("ALTER TABLE matches ADD COLUMN tactical_analysis TEXT"))
            if "key_factors" not in match_cols:
                await conn.execute(text("ALTER TABLE matches ADD COLUMN key_factors TEXT"))
            if "final_score_home" not in match_cols:
                await conn.execute(text("ALTER TABLE matches ADD COLUMN final_score_home INTEGER"))
            if "final_score_away" not in match_cols:
                await conn.execute(text("ALTER TABLE matches ADD COLUMN final_score_away INTEGER"))
            if "chosen_outcome" not in match_cols:
                await conn.execute(text("ALTER TABLE matches ADD COLUMN chosen_outcome TEXT"))

            # Schema versioning
            await conn.execute(text("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY)"))
            
            v_res = await conn.execute(text("SELECT version FROM schema_version WHERE version = 1"))
            if not v_res.scalar_one_or_none():
                await conn.execute(text("UPDATE matches SET match_date = datetime(match_date, '+3 hours')"))
                await conn.execute(text("INSERT INTO schema_version (version) VALUES (1)"))
            
            v_res2 = await conn.execute(text("SELECT version FROM schema_version WHERE version = 2"))
            if not v_res2.scalar_one_or_none():
                for sfx in [' (Stavka TV)', ' (Legalbet)', ' (Vprognoze)', ' (BR)']:
                    await conn.execute(text(f"UPDATE predictions SET predicted_outcome = REPLACE(predicted_outcome, '{sfx}', '') WHERE predicted_outcome LIKE '%{sfx}%'"))
                await conn.execute(text("INSERT INTO schema_version (version) VALUES (2)"))

            # Удаление синтетических прогнозов Global Bookmakers и StatArea AI
            await conn.execute(text("DELETE FROM predictions WHERE source_id IN (SELECT id FROM sources WHERE name IN ('Global Bookmakers', 'StatArea AI (Trends)'))"))
            await conn.execute(text("UPDATE sources SET is_active = 0 WHERE name IN ('Global Bookmakers', 'StatArea AI (Trends)')"))
        except Exception as e:
            pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

